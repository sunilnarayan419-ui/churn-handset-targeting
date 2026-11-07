# Neo4j integration

## `GraphStore`

| Method | Behaviour |
|---|---|
| `GraphStore(uri, user, password, database="neo4j", driver=None)` | Creates a driver with `GraphDatabase.driver(uri, auth=(user, password))`, or uses an injected `driver` (used in unit tests). Raises `ImportError` with an install hint if the `neo4j` package is missing. The constructor does not verify connectivity |
| `ensure_schema()` | Creates the uniqueness constraints ({doc}`graph-schema`) |
| `load(df, batch_size=5000)` | Idempotent load; returns the number of rows written per step (`customers` plus each dimension present) |
| `clear()` | Deletes all `Customer` nodes in transactions of 10,000 rows, then all segment-label nodes |
| `churn_by(dimension)` | `segment`, `customers`, `churn_rate` ordered by `ord`, `segment` |
| `churn_by_pair(dim_a, dim_b)` | Cross-tabulated churn for two dimensions |
| `customer_count()` | Number of `Customer` nodes |
| `close()` / context manager | Closes the driver |

Unknown dimensions raise `KeyError` listing the valid ones.

## Loading

`load` writes customers with

```cypher
UNWIND $rows AS r MERGE (c:Customer {id: r.id}) SET c.churn = r.churn, ...
```

then, for each dimension whose source column exists, creates segment nodes with `MERGE ... ON CREATE SET
d.ord = r.ord` and the relationship with `MERGE (c)-[:REL]->(d)`. `MERGE` makes re-running safe. Rows with a
missing segment value are skipped for that dimension.

## Injection safety

- **Data** is always passed as query parameters (`$rows`).
- **Labels and relationship types** cannot be parameters in Cypher, so they are interpolated into the query
  text, but only from the hard-coded `GRAPH_SCHEMA` after a lookup that raises `KeyError` for anything else.
  User input never selects a label.
- The API validates `dimension` against `DIMENSIONS` before touching the store.

## Command line

```bash
docker compose up -d neo4j                      # needs NEO4J_PASSWORD (at least 8 characters)
export NEO4J_URI=bolt://localhost:7687 NEO4J_PASSWORD=<your-password>
churn-targeting graph-load --reset              # --reset deletes existing graph data first
```

`graph-load` exits with a message unless both `NEO4J_URI` and `NEO4J_PASSWORD` are set. Use `--reset` only if
you intend to clear the graph; note that `clear()` removes all nodes with the project's segment labels.

## Cohort analytics in the API

When `NEO4J_URI` is set, startup creates a store and `/cohorts/{dimension}` returns `"source": "neo4j"`.
`/health` reports `graph_enabled: true` as soon as the store object exists, even if the database is
unreachable.

## Testing

`tests/test_graph_unit.py` uses an injected fake driver. `tests/test_graph_integration.py` (marker
`integration`) needs a live database and asserts that Neo4j results equal pandas results; CI runs it against a
`neo4j:5` service container ({doc}`../development/testing`).
