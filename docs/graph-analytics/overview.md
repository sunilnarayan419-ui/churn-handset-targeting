# Graph analytics overview

The optional Neo4j layer ({repo}`src/churn_targeting/graph.py`) stores each customer as a node linked to its
cohort segments and answers cohort questions in Cypher. It is **a cohort-exploration and extensibility layer,
not a predictive one.** The supplied data has no customer-to-customer links (households, referrals, number
porting), so the graph cannot improve model accuracy and pandas gives identical answers; integration tests
assert that parity.

## Workflow

```{mermaid}
flowchart TD
    D["load_customers<br/>validated merged table"] --> L["churn-targeting graph-load"]
    L --> S["GraphStore.ensure_schema<br/>uniqueness constraints"]
    S --> R{"--reset?"}
    R -->|"yes"| C["GraphStore.clear<br/>delete Customer and band nodes"]
    R -->|"no"| LD
    C --> LD["GraphStore.load<br/>UNWIND + MERGE in batches of 5000"]
    LD --> N[("Neo4j<br/>Customer and segment nodes")]
    N --> Q["churn_by / churn_by_pair<br/>parameter-free Cypher with whitelisted labels"]
    Q --> API["GET /cohorts/dimension<br/>source: neo4j"]
    D --> PD["analytics.churn_by_segment<br/>same bands, pandas"]
    PD -.->|"parity asserted by integration test"| Q
```

## Why a graph, honestly

A relational table is equally capable for the current data. The graph is justified as a place to add
relationships later (households, referrals, porting) for community or contagion analyses without changing the
schema. Until such data exist, treat it as optional infrastructure.

## Requirements

- The `graph` extra (`neo4j>=5.20`) and a Neo4j 5 database ({doc}`neo4j-integration`).
- Settings `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` ({doc}`../getting-started/environment-setup`).
- The API uses the graph only when `NEO4J_URI` is set; otherwise `/cohorts/{dimension}` needs an injected
  pandas frame (not available in the default app).
