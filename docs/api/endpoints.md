# Endpoints

The application defines **seven routes** in {repo}`src/churn_targeting/api/main.py`. FastAPI additionally
serves its generated documentation (`/docs`, `/redoc`) and the OpenAPI document (`/openapi.json`); these are
framework defaults and are **not** protected by the API key ({doc}`authentication`).

| Method | URL | Purpose | Auth | Needs model | Success model |
|---|---|---|:-:|:-:|---|
| GET | `/health` | Liveness, model and graph status | open | no | `dict` |
| GET | `/model` | Bundle metadata and test metrics | key | yes | `dict` |
| POST | `/score` | Score one customer | key | yes | `ScoreResponse` |
| POST | `/score/batch` | Score 1-5,000 customers | key | yes | `BatchScoreResponse` |
| POST | `/finance/economics` | Economics of one campaign wave | key | no | `EconomicsResponse` |
| POST | `/pilot/size` | Two-arm randomised pilot sample size | key | no | `PilotResponse` |
| GET | `/cohorts/{dimension}` | Churn by cohort segment | key | no | `CohortResponse` |

"key" means the route requires `X-API-Key` **when** `API_KEY` is configured; with no key configured every
route is open. Field-level contracts are in {doc}`schemas`; status codes in {doc}`errors`.

```{note}
Examples marked *shape* use placeholders in angle brackets for values that depend on your trained model or
data; they were not produced by running the service. Examples marked *hand-computed* are derived from the
formulas in {doc}`../business-methodology/retention-economics`; trailing floating-point digits may differ.
```

## `GET /health`

**Purpose.** Liveness probe. Returns `status` (`"ok"`), `version` (package version), `model_loaded` and
`graph_enabled` (whether a graph store object exists; it does not test the database connection). Always open,
including when `API_KEY` is set. It does not guarantee that scoring works.

```json
{"status": "ok", "version": "0.1.0", "model_loaded": true, "graph_enabled": false}
```

**Errors.** None defined by the application.

## `GET /model`

**Purpose.** Returns `ModelBundle.metadata`: model name, target description, training timestamp,
scikit-learn version, seed, `n_train`, `n_test`, `pi_sample`, parameters, test metrics, excluded features
(`["Customer_ID", "ethnic"]`) and `n_features`. The response type is an untyped `dict`.

*Shape:*

```json
{
  "model_name": "Gradient boosting (HistGradientBoostingClassifier)",
  "target": "churn (left 31-60 days after observation date)",
  "trained_at_utc": "<ISO-8601 UTC timestamp>",
  "sklearn_version": "<version>",
  "seed": 42,
  "n_train": "<int>", "n_test": "<int>", "pi_sample": "<float>",
  "params": {"learning_rate": 0.03, "max_leaf_nodes": 31, "min_samples_leaf": 100, "l2_regularization": 1.0},
  "metrics_test": {"roc_auc": "<float>", "pr_auc": "<float>", "accuracy": "<float>", "precision": "<float>",
                   "recall": "<float>", "f1": "<float>", "brier_raw": "<float>", "brier_calibrated": "<float>"},
  "excluded_features": ["Customer_ID", "ethnic"],
  "n_features": 97
}
```

**Errors.** 401 (key), 503 (no model loaded).

## `POST /score`

**Purpose.** Score one customer.

- **Query parameter.** `base_rate` (float, optional): strictly between 0 and 1; default is the configured
  `BASE_RATE` (0.0099).
- **Body** (`ScoreRequest`): `customer`, an object mapping raw column names to `float | int | str | null`.
  Missing fields are treated as unknown and unknown fields are ignored. An empty object is accepted (all
  features missing).
- **Response** (`ScoreResponse`): `churn_probability_calibrated` (sample scale),
  `churn_probability_at_base_rate` (shifted to `base_rate`), `base_rate`, `missing_features` (number of model
  columns not supplied).

```json
{"customer": {"eqpdays": 350, "months": 14, "area": "NEW YORK CITY AREA"}}
```

*Shape of the response:*

```json
{"churn_probability_calibrated": "<float in (0,1)>", "churn_probability_at_base_rate": "<float in (0,1)>",
 "base_rate": 0.0099, "missing_features": "<int>"}
```

**Errors.** 401, 422 (body or `base_rate` invalid, e.g. `base_rate=1.5`), 503 (no model loaded).

## `POST /score/batch`

**Purpose.** Score many customers in one call.

- **Query parameter.** `base_rate`, as above (one value applies to all rows).
- **Body** (`BatchScoreRequest`): `customers`, a list of 1 to 5,000 customer objects.
- **Response** (`BatchScoreResponse`): `results`, a list of `ScoreResponse` in input order.

```json
{"customers": [{"eqpdays": 350, "months": 14}, {"eqpdays": 100, "months": 36}, {"eqpdays": 400, "months": 8}]}
```

**Errors.** 401, 422 (empty list, more than 5,000 customers, wrong types), 503 (no model loaded; this can
precede the 422 for an invalid body, see {doc}`../architecture/application-architecture`).

## `POST /finance/economics`

**Purpose.** Deterministic economics of one monthly campaign wave via `finance.economics` (formulas in
{doc}`../business-methodology/retention-economics`). The output is only as credible as the supplied inputs.
Does not need a model.

- **Body** (`EconomicsRequest`): required `n_treated` (int > 0), `churn_prob` (0 < x < 1), `avg_monthly_rev`
  (≥ 0), `save_rate` (0 ≤ x ≤ 1), `margin` (0 ≤ x ≤ 1), `months` (int > 0), `contact_cost` (≥ 0); optional
  `accept_rate` (0 ≤ x ≤ 1, default 0) and `incentive` (≥ 0, default 0).
- **Response** (`EconomicsResponse`): `treated`, `would_be_churners`, `saved`, `value_per_save`,
  `gross_benefit`, `variable_cost`, `net_variable_benefit`, `breakeven_save_rate`. The break-even is `null`
  when a save has no value (infinity cannot be encoded in JSON).

*Hand-computed example:*

```json
{"n_treated": 1000, "churn_prob": 0.05, "avg_monthly_rev": 50, "save_rate": 0.10,
 "margin": 0.40, "months": 12, "contact_cost": 0.50}
```

```json
{"treated": 1000.0, "would_be_churners": 50.0, "saved": 5.0, "value_per_save": 240.0,
 "gross_benefit": 1200.0, "variable_cost": 500.0, "net_variable_benefit": 700.0,
 "breakeven_save_rate": 0.0417}
```

With `avg_monthly_rev: 0` the same request yields `"breakeven_save_rate": null` (asserted in
`tests/test_api.py`).

**Errors.** 401, 422 (field out of range, or a `ValueError` raised by `economics`, returned with its message
as `detail`).

## `POST /pilot/size`

**Purpose.** Sample size for a two-arm randomised pilot via `pilot.n_per_arm` (equation in
{doc}`../business-methodology/pilot-design`). Does not need a model.

- **Body** (`PilotRequest`): `baseline_churn_prob` (0 < x < 1), `relative_effect` (0 < x < 1), `alpha`
  (default 0.05, 0 < x < 1), `power` (default 0.80, 0 < x < 1).
- **Response** (`PilotResponse`): `n_per_arm` (int) and `total_customers` (= 2 × `n_per_arm`).

```json
{"baseline_churn_prob": 0.10, "relative_effect": 0.20}
```

*Shape of the response:* `{"n_per_arm": <int>, "total_customers": <2 x n_per_arm>}`. For this request the
unit test asserts `n_per_arm` between 3,100 and 3,300.

**Errors.** 401, 422.

## `GET /cohorts/{dimension}`

**Purpose.** Customers and churn rate per segment for one dimension.

- **Path parameter.** `dimension` must be one of `handset_age`, `tenure`, `price_tier`, `area`,
  `credit_class` ({doc}`../graph-analytics/overview`).
- **Behaviour.** An unknown dimension returns 404 *before* any data check. If a graph store exists, the result
  comes from Neo4j (`"source": "neo4j"`); otherwise if an in-memory customer frame was injected, from pandas
  (`"source": "pandas"`); otherwise 503. The default application never loads a frame, so without Neo4j a
  valid dimension returns 503.
- **Response** (`CohortResponse`): `dimension`, `source`, `segments` (list of `{segment, customers, churn_rate}`).

*Shape:*

```json
{"dimension": "tenure", "source": "neo4j",
 "segments": [{"segment": "<=12 months", "customers": "<int>", "churn_rate": "<float>"}]}
```

**Errors.** 401, 404 (unknown dimension), 503 (no graph store or customer data configured).
