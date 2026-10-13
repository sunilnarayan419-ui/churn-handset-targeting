# Neo4j graph model

```
(:Customer {id, churn, months, eqpdays, rev_mean, hnd_price})
   -[:HAS_HANDSET_AGE]->  (:HandsetAgeBand {name, ord})
   -[:HAS_TENURE]->       (:TenureBand {name, ord})
   -[:HAS_PRICE_TIER]->   (:PriceTier {name, ord})
   -[:IN_AREA]->          (:Area {name})
   -[:HAS_CREDIT_CLASS]-> (:CreditClass {name})
```

Constraints: `Customer.id` and each segment node's `name` are unique. Loading uses `UNWIND` batches with `MERGE`, so it is idempotent.

Example: churn by handset-age band and tenure (also available as `GraphStore.churn_by_pair`).

```cypher
MATCH (c:Customer)-[:HAS_HANDSET_AGE]->(a:HandsetAgeBand), (c)-[:HAS_TENURE]->(t:TenureBand)
RETURN a.name AS handset_age, t.name AS tenure, count(c) AS customers, avg(c.churn) AS churn_rate
ORDER BY a.ord, t.ord
```

**Why a graph here, honestly.** The data are tabular and contain no customer-to-customer links, so a relational table is equally capable and pandas gives identical answers (the integration tests assert this). The graph layer is justified as a cohort-exploration and extensibility layer: if household, referral or number-porting relationships become available they can be added as relationships and used for community and contagion analyses without changing this schema.
