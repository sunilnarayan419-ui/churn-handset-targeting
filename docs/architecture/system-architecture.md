# System architecture

The system is a small, layered Python package. A **pure core** (data validation, modelling, targeting
statistics, economics, pilot sizing) is wrapped by thin edges: a command-line interface, a FastAPI service and
an optional Neo4j store. A separate, **experimental** simulation package is reachable from the command line
only; it is not wired into the API.

```{mermaid}
flowchart LR
    C["Client.csv"] --> D
    R["Record.csv"] --> D
    D["data.py<br/>validated one-to-one merge"] --> M["features.py + modeling.py<br/>split, pipeline, Platt calibration"]
    M --> B[("models/churn_model.joblib<br/>+ .json metadata")]
    D --> A["analytics.py + bands.py<br/>pandas cohorts"]
    D --> G["graph.py<br/>Neo4j loader and Cypher"]
    B --> API["FastAPI service<br/>api/main.py"]
    A -.->|"injected frame only"| API
    G -.->|"when NEO4J_URI is set"| API
    FIN["finance.py<br/>economics"] --> API
    PIL["pilot.py<br/>sample size"] --> API
    M --> X["scripts/export_results.py<br/>also uses targeting.py, finance.py, pilot.py"]
    X --> RJ["reports/results.json"]
    RJ --> MS["Manubot manuscript<br/>content/ + build/"]
    SIM["simulation/ (experimental)<br/>scenario comparison, MiroFish adapter"] --> CLI["Command line only<br/>python -m ...simulation.cli<br/>churn-targeting mirofish-*"]
```

## Module responsibilities

| Layer | Modules | Responsibility |
|---|---|---|
| Configuration | `config.py` | Environment-backed `Settings`; `SEED = 42`; `DEFAULT_BASE_RATE = 0.0099` |
| Data | `data.py` | Load both CSVs, validate keys, validated one-to-one merge, `QualityReport` |
| Modelling | `features.py`, `modeling.py`, `calibration.py` | Feature selection, scikit-learn pipeline, training, Platt calibration, base-rate shift, scoring, persistence |
| Decision logic | `targeting.py`, `finance.py`, `pilot.py` | Ranking statistics, retention economics, pilot sample size (plain functions) |
| Cohorts | `bands.py`, `analytics.py`, `graph.py` | One definition of each segment, used by pandas and Neo4j alike |
| Interfaces | `cli.py`, `api/main.py`, `api/schemas.py` | Commands `validate`, `train`, `graph-load`, `serve`, `mirofish-*`; seven HTTP routes |
| Experimental | `simulation/*` | Scenario schemas, assumption-based economics, provenance, MiroFish integration |

Details: {doc}`application-architecture`, {doc}`data-flow`, {doc}`model-pipeline`,
{doc}`technology-stack`, {doc}`../development/repository-guide`.

## Design decisions

These are visible in the source and are the reasons the code is structured as it is.

- **Pure core, thin edges.** Targeting, finance and pilot sizing are plain functions with explicit arguments,
  testable without a model, a database or a web server. The API validates input and calls them.
- **One definition of a segment.** `bands.py` defines every cohort once; both the pandas analytics and the
  Neo4j loader use it, and an integration test asserts that they agree.
- **Split before fitting.** All encoding and imputation lives inside the scikit-learn pipeline. The
  calibrator is fitted on out-of-fold *training* predictions only; the test partition is used once for
  reporting.
- **Numbers are not typed into the paper.** The manuscript pulls figures from `reports/results.json`, which
  `scripts/export_results.py` recomputes from the raw data; `scripts/check_manuscript.py` fails on any
  undefined variable ({doc}`../scientific-reproducibility/manuscript-pipeline`).
- **Optional heavy dependencies.** FastAPI and Neo4j are extras. `GraphStore` accepts an injected driver so
  its logic is unit-tested with a fake.
- **Defensive defaults.** Cypher labels and relationship types come from a fixed whitelist, data is passed as
  query parameters, the API key comparison is constant-time, the container runs as a non-root user, and
  secrets come from the environment ({doc}`../deployment/security`).
