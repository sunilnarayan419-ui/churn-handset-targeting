"""Unit tests for the Neo4j layer using an in-memory fake driver (no database needed)."""

import numpy as np
import pytest

from churn_targeting.graph import GRAPH_SCHEMA, GraphStore


class FakeRecord:
    def __init__(self, d):
        self._d = d

    def data(self):
        return self._d


class FakeSession:
    def __init__(self, log, results):
        self.log, self.results = log, results

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run(self, query, params=None):
        self.log.append((query, params))
        return [FakeRecord(r) for r in self.results]


class FakeDriver:
    def __init__(self, results=None):
        self.log, self.results, self.closed = [], results or [], False

    def session(self, database=None):
        return FakeSession(self.log, self.results)

    def close(self):
        self.closed = True


def test_schema_creates_unique_constraints_for_every_label():
    d = FakeDriver()
    GraphStore(driver=d).ensure_schema()
    text = " ".join(q for q, _ in d.log)
    assert "customer_id" in text
    assert all(label in text for label, _ in GRAPH_SCHEMA.values())
    assert all("IF NOT EXISTS" in q for q, _ in d.log)


def test_load_merges_customers_and_every_dimension(customers):
    d = FakeDriver()
    counts = GraphStore(driver=d).load(customers, batch_size=1000)
    assert counts["customers"] == len(customers)
    assert {"handset_age", "tenure", "price_tier", "area", "credit_class"} <= set(counts)
    queries = [q for q, _ in d.log]
    assert any("MERGE (c:Customer" in q for q in queries)
    assert any("HAS_HANDSET_AGE" in q for q in queries)
    assert all("UNWIND $rows" in q for q in queries)       # parameterised, never string-built from data


def test_load_converts_nan_to_none_and_batches(customers):
    d = FakeDriver()
    GraphStore(driver=d).load(customers, batch_size=1000)
    first_batches = [p["rows"] for q, p in d.log if "SET c.churn" in q]
    assert len(first_batches) == 3 and all(len(b) <= 1000 for b in first_batches)
    flat = [r for b in first_batches for r in b]
    assert any(r["rev_mean"] is None for r in flat)
    assert not any(isinstance(r["rev_mean"], float) and np.isnan(r["rev_mean"]) for r in flat)


def test_unknown_dimension_is_rejected_before_any_query():
    d = FakeDriver()
    with pytest.raises(KeyError):
        GraphStore(driver=d).churn_by("x) DETACH DELETE (n")
    assert d.log == []


def test_churn_by_returns_dataframe_and_uses_whitelisted_relationship():
    rows = [{"segment": "<=100", "customers": 10, "churn_rate": 0.4, "ord": 0},
            {"segment": "101-150", "customers": 20, "churn_rate": 0.5, "ord": 1}]
    d = FakeDriver(rows)
    t = GraphStore(driver=d).churn_by("handset_age")
    assert list(t.columns) == ["segment", "customers", "churn_rate"] and len(t) == 2
    assert "HAS_HANDSET_AGE" in d.log[0][0] and "HandsetAgeBand" in d.log[0][0]


def test_context_manager_closes_driver():
    d = FakeDriver()
    with GraphStore(driver=d):
        pass
    assert d.closed
