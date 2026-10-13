"""Neo4j graph layer for cohort analytics.

Graph model (a star schema around each customer):

    (:Customer {id, churn, months, eqpdays, rev_mean, hnd_price})
        -[:HAS_HANDSET_AGE]-> (:HandsetAgeBand {name, ord})
        -[:HAS_TENURE]->      (:TenureBand {name, ord})
        -[:HAS_PRICE_TIER]->  (:PriceTier {name, ord})
        -[:IN_AREA]->         (:Area {name})
        -[:HAS_CREDIT_CLASS]->(:CreditClass {name})

Scope note: the supplied data has no customer-to-customer links (households, referrals, porting), so
this graph supports cohort exploration and intersection queries; it does not improve model accuracy.
If such links become available they can be added as relationships without changing this schema.

Segment labels come from ``analytics``/``bands`` so Neo4j and pandas give identical answers.
Labels and relationship types are taken from a fixed whitelist, never from user input.
"""

from __future__ import annotations

import math

import pandas as pd

from .analytics import DIMENSIONS, segment_labels

GRAPH_SCHEMA: dict[str, tuple[str, str]] = {
    "handset_age": ("HandsetAgeBand", "HAS_HANDSET_AGE"),
    "tenure": ("TenureBand", "HAS_TENURE"),
    "price_tier": ("PriceTier", "HAS_PRICE_TIER"),
    "area": ("Area", "IN_AREA"),
    "credit_class": ("CreditClass", "HAS_CREDIT_CLASS"),
}
assert set(GRAPH_SCHEMA) == set(DIMENSIONS)

CUSTOMER_PROPS = {"churn": "churn", "months": "months", "eqpdays": "eqpdays",
                  "rev_mean": "rev_Mean", "hnd_price": "hnd_price"}


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v.item() if hasattr(v, "item") else v


def _chunks(rows: list, size: int):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def _schema(dimension: str) -> tuple[str, str]:
    if dimension not in GRAPH_SCHEMA:
        raise KeyError(f"unknown dimension {dimension!r}; choose from {sorted(GRAPH_SCHEMA)}")
    return GRAPH_SCHEMA[dimension]


class GraphStore:
    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None,
                 database: str = "neo4j", driver=None):
        if driver is None:
            try:
                from neo4j import GraphDatabase
            except ImportError as exc:  # pragma: no cover - depends on optional extra
                raise ImportError("Install the graph extra: pip install 'churn-targeting[graph]'") from exc
            driver = GraphDatabase.driver(uri, auth=(user, password))
        self._driver, self._database = driver, database

    # -- plumbing -----------------------------------------------------------------------------
    def _run(self, query: str, params: dict | None = None) -> list[dict]:
        with self._driver.session(database=self._database) as session:
            return [record.data() for record in session.run(query, params or {})]

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> GraphStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- schema and load ----------------------------------------------------------------------
    def ensure_schema(self) -> None:
        self._run("CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE")
        for label, _ in GRAPH_SCHEMA.values():
            self._run(f"CREATE CONSTRAINT {label.lower()}_name IF NOT EXISTS "
                      f"FOR (d:{label}) REQUIRE d.name IS UNIQUE")

    def load(self, df: pd.DataFrame, batch_size: int = 5000) -> dict[str, int]:
        """Idempotent load (MERGE): safe to re-run. Returns rows written per step."""
        counts: dict[str, int] = {}
        props = {k: v for k, v in CUSTOMER_PROPS.items() if v in df.columns}
        sub = df[["Customer_ID", *props.values()]].rename(columns={v: k for k, v in props.items()})
        rows = [{"id": int(r.pop("Customer_ID")), **{k: _clean(v) for k, v in r.items()}}
                for r in sub.to_dict("records")]
        sets = ", ".join(f"c.{k} = r.{k}" for k in props)
        q = f"UNWIND $rows AS r MERGE (c:Customer {{id: r.id}}) SET {sets}"
        for chunk in _chunks(rows, batch_size):
            self._run(q, {"rows": chunk})
        counts["customers"] = len(rows)

        for dim, (label, rel) in GRAPH_SCHEMA.items():
            col = DIMENSIONS[dim][0]
            if col not in df.columns:
                continue
            seg = segment_labels(df, dim).astype("object")
            order = DIMENSIONS[dim][2] or []
            drows = [{"id": int(i), "value": str(v), "ord": order.index(v) if v in order else 0}
                     for i, v in zip(df["Customer_ID"].tolist(), seg.tolist(), strict=True) if pd.notna(v)]
            dq = (f"UNWIND $rows AS r MATCH (c:Customer {{id: r.id}}) "
                  f"MERGE (d:{label} {{name: r.value}}) ON CREATE SET d.ord = r.ord "
                  f"MERGE (c)-[:{rel}]->(d)")
            for chunk in _chunks(drows, batch_size):
                self._run(dq, {"rows": chunk})
            counts[dim] = len(drows)
        return counts

    def clear(self) -> None:
        self._run("MATCH (n:Customer) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS")
        for label, _ in GRAPH_SCHEMA.values():
            self._run(f"MATCH (d:{label}) DETACH DELETE d")

    # -- analytics ----------------------------------------------------------------------------
    def churn_by(self, dimension: str) -> pd.DataFrame:
        label, rel = _schema(dimension)
        q = (f"MATCH (c:Customer)-[:{rel}]->(d:{label}) "
             "RETURN d.name AS segment, count(c) AS customers, avg(c.churn) AS churn_rate, d.ord AS ord "
             "ORDER BY ord, segment")
        rows = self._run(q)
        return pd.DataFrame(rows, columns=["segment", "customers", "churn_rate", "ord"]).drop(columns="ord")

    def churn_by_pair(self, dim_a: str, dim_b: str) -> pd.DataFrame:
        la, ra = _schema(dim_a)
        lb, rb = _schema(dim_b)
        q = (f"MATCH (c:Customer)-[:{ra}]->(a:{la}), (c)-[:{rb}]->(b:{lb}) "
             "RETURN a.name AS a, b.name AS b, count(c) AS customers, avg(c.churn) AS churn_rate "
             "ORDER BY a.ord, a.name, b.ord, b.name")
        return pd.DataFrame(self._run(q), columns=["a", "b", "customers", "churn_rate"])

    def customer_count(self) -> int:
        return int(self._run("MATCH (c:Customer) RETURN count(c) AS n")[0]["n"])
