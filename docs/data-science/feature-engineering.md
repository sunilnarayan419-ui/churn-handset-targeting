# Feature engineering and preprocessing

The feature logic is intentionally small and lives in {repo}`src/churn_targeting/features.py`. There is no
hand-crafted feature construction: the model uses the raw columns of the merged table.

## Feature selection

`select_features(df)` returns `X` and `y`:

- `y = df["churn"].astype(int)`.
- `X` drops `Customer_ID`, `churn` and every column in `FAIRNESS_EXCLUDED = ("ethnic",)` that is present.

After these exclusions the reported model has **97 features** (100 merged columns minus the three dropped).

| Excluded column | Reason |
|---|---|
| `Customer_ID` | Identifier, not a predictor |
| `churn` | The target |
| `ethnic` | Protected characteristic: it must not be used to decide whom to contact |

```{warning}
Excluding `ethnic` does not establish fairness. Other demographic and socioeconomic fields (for example
income or marital status) remain and may act as proxies. A fairness review is required before any deployment
({doc}`../scientific-reproducibility/limitations`).
```

## Preprocessing inside the pipeline

`column_types(X)` treats every non-numeric column as categorical and every numeric column as numeric. The
`ColumnTransformer` built by `build_pipeline` then applies:

| Columns | Transformation |
|---|---|
| Categorical | `OrdinalEncoder` with `handle_unknown="use_encoded_value"`, `unknown_value=nan`, `encoded_missing_value=nan` |
| Numeric | Passed through unchanged |

Categorical columns are declared to `HistGradientBoostingClassifier` via `categorical_features`, so the
ordinal codes are treated as categories, not as ordered magnitudes. There is no scaling, imputation or
dummy-coding step.

## Missing values

`HistGradientBoostingClassifier` handles `NaN` natively by learning, for each split, which side missing values
should follow. Consequences:

- Training and scoring do not need an imputer, and nothing is imputed from test data.
- At scoring time, columns absent from the input become `NaN`, non-numeric text in a numeric column becomes
  `NaN` (`pd.to_numeric(errors="coerce")`), and unseen category labels encode to `NaN`.
- Native handling does **not** make sparse records equally reliable. The API reports how many model columns
  were not supplied (`missing_features`) so callers can judge input completeness.

## Leakage controls

| Risk | Control in the code |
|---|---|
| Test information used in fitting | The split happens first; the pipeline and calibrator are fitted on the training partition only |
| Calibration on the data it is evaluated on | The Platt calibrator is fitted on **out-of-fold** training predictions |
| Model selection on the test set | Hyper-parameter search (when used) cross-validates on training data; the test set is used once for reporting |
| Target leakage through columns | The manuscript's review found no single variable that separates churners well (strongest stand-alone ROC-AUC 0.574) and no cancellation, port-out or retention-offer field in the data dictionary |

The residual risk is that, without timestamps, it cannot be proven that every feature was recorded before the
outcome window. This is documented as a limitation, not resolved.

## Cohort bands are analytics, not features

`bands.py` defines handset-age, tenure and price bands. They are used for cohort tables, the Neo4j graph and
the simple 301-400 day rule baseline; they are **not** inputs to the model ({doc}`../business-methodology/customer-targeting`).
