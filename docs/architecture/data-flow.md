# Data flow

## From raw files to model inputs

```{mermaid}
flowchart TD
    A["data/raw/Client.csv"] --> L["load_raw<br/>FileNotFoundError if a file is missing"]
    B["data/raw/Record.csv"] --> L
    L --> V["validate_keys<br/>Customer_ID present, non-null, unique, identical sets; churn present"]
    V -->|"DataValidationError on any violation"| X["stop"]
    V --> M["merge_customers<br/>record.merge(client, how=inner, validate=one_to_one)"]
    M --> N["row count must equal record rows"]
    N --> Q["quality_report<br/>rows, columns, churn rate, missing-value summary"]
    N --> S["select_features<br/>drop Customer_ID, churn, ethnic"]
    S --> T["train_test_split<br/>80/20, stratified, seed 42"]
    T --> P["scikit-learn pipeline<br/>encode categoricals, native missing handling"]
```

Each box maps to a function in {repo}`src/churn_targeting/data.py` and {repo}`src/churn_targeting/features.py`.
Rules and rationale: {doc}`../data-science/data-validation` and {doc}`../data-science/feature-engineering`.

## From a request to a probability

```{mermaid}
flowchart LR
    J["JSON customer fields<br/>float, int, str or null"] --> F["pandas DataFrame"]
    F --> R["reindex to training feature columns<br/>missing columns become NaN"]
    R --> C["categoricals to object;<br/>numerics via to_numeric(errors=coerce)"]
    C --> PL["pipeline.predict_proba<br/>raw score"]
    PL --> PC["PlattCalibrator.predict<br/>calibrated probability"]
    PC --> BR["to_real_world<br/>probability at requested base rate"]
```

Unknown fields are ignored; model columns that are not supplied are counted in `missing_features` (a column
supplied with a `null` value counts as supplied). Details: {doc}`../data-science/calibration`.

## Derived and generated artefacts

| Artefact | Produced by | Consumed by | Committed? |
|---|---|---|---|
| `models/churn_model.joblib` + `.json` | `churn-targeting train` | API startup | No (git-ignored) |
| `reports/results.json` | `scripts/export_results.py` | `scripts/export_manuscript_variables.py`, `tests/test_artifacts.py` | Yes |
| `build/variables.json` | `scripts/export_manuscript_variables.py` | Manubot build | No (regenerated) |
| `reports/simulation/*.json` | `python -m churn_targeting.simulation.cli` | Readers | Yes (assumption-only examples) |
| Neo4j graph | `churn-targeting graph-load` | API `/cohorts/{dimension}` | Database volume |
