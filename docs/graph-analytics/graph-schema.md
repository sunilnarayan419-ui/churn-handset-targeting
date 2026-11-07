# Graph schema

A star schema around each customer. Labels and relationship types come from the fixed mapping
`graph.GRAPH_SCHEMA`; the same dimension keys are defined in `analytics.DIMENSIONS` (an `assert` enforces that
the two sets match).

```text
(:Customer {id, churn, months, eqpdays, rev_mean, hnd_price})
   -[:HAS_HANDSET_AGE]->   (:HandsetAgeBand {name, ord})
   -[:HAS_TENURE]->        (:TenureBand {name, ord})
   -[:HAS_PRICE_TIER]->    (:PriceTier {name, ord})
   -[:IN_AREA]->           (:Area {name})
   -[:HAS_CREDIT_CLASS]->  (:CreditClass {name})
```

| Dimension | Node label | Relationship | Source column | `ord` |
|---|---|---|---|---|
| `handset_age` | `HandsetAgeBand` | `HAS_HANDSET_AGE` | `eqpdays` | band order |
| `tenure` | `TenureBand` | `HAS_TENURE` | `months` | band order |
| `price_tier` | `PriceTier` | `HAS_PRICE_TIER` | `hnd_price` | band order |
| `area` | `Area` | `IN_AREA` | `area` | 0 |
| `credit_class` | `CreditClass` | `HAS_CREDIT_CLASS` | `crclscod` | 0 |

`Customer` properties come from `CUSTOMER_PROPS`: `churn`, `months`, `eqpdays`, `rev_mean` (from column
`rev_Mean`) and `hnd_price`; a property is loaded only if its source column exists. Missing values become
`null`.

## Constraints

`ensure_schema()` issues `CREATE CONSTRAINT ... IF NOT EXISTS`:

- `customer_id`: `Customer.id` is unique.
- `<label lowercased>_name`: each segment label's `name` is unique (for example `handsetageband_name`).

## Example query

Churn by handset-age band and tenure; also available as `GraphStore.churn_by_pair`.

```cypher
MATCH (c:Customer)-[:HAS_HANDSET_AGE]->(a:HandsetAgeBand), (c)-[:HAS_TENURE]->(t:TenureBand)
RETURN a.name AS handset_age, t.name AS tenure, count(c) AS customers, avg(c.churn) AS churn_rate
ORDER BY a.ord, t.ord
```

Segment labels (for example `<=100`, `101-150`, `<=12 months`) are produced by `bands.py`, so Neo4j and
pandas agree by construction ({doc}`../business-methodology/customer-targeting`).
