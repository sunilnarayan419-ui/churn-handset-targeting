# Schemas

Request and response models are Pydantic v2 classes in {repo}`src/churn_targeting/api/schemas.py`. Generated
signatures are in {doc}`python-modules`; this page records the validation rules.

`FeatureValue = float | int | str | None` is the type of a single customer field.

## Scoring

| Model | Field | Type | Constraint | Description |
|---|---|---|---|---|
| `ScoreRequest` | `customer` | `dict[str, FeatureValue]` | required | Raw customer fields by column name; missing fields are unknown, unknown fields ignored |
| `BatchScoreRequest` | `customers` | `list[dict[str, FeatureValue]]` | 1 ≤ length ≤ 5000 | One object per customer |
| `ScoreResponse` | `churn_probability_calibrated` | float | | Probability on the (enriched) training-sample scale |
| | `churn_probability_at_base_rate` | float | | Probability rescaled to the requested monthly base rate |
| | `base_rate` | float | | Base rate used for this response |
| | `missing_features` | int | | Model inputs not supplied in the request |
| `BatchScoreResponse` | `results` | `list[ScoreResponse]` | | Same order as the input |

## Economics

| Model | Field | Type | Constraint |
|---|---|---|---|
| `EconomicsRequest` | `n_treated` | int | > 0 (customers contacted per wave) |
| | `churn_prob` | float | 0 < x < 1 (real-world monthly churn probability of the contacted group) |
| | `avg_monthly_rev` | float | ≥ 0 |
| | `save_rate` | float | 0 ≤ x ≤ 1 (incremental share of would-be churners the contact keeps) |
| | `margin` | float | 0 ≤ x ≤ 1 |
| | `months` | int | > 0 |
| | `contact_cost` | float | ≥ 0 |
| | `accept_rate` | float | 0 ≤ x ≤ 1, default 0.0 |
| | `incentive` | float | ≥ 0, default 0.0 |
| `EconomicsResponse` | `treated`, `would_be_churners`, `saved`, `value_per_save`, `gross_benefit`, `variable_cost`, `net_variable_benefit` | float | |
| | `breakeven_save_rate` | float or null | null when a contact can never pay back (zero value per save) |

## Pilot sizing

| Model | Field | Type | Constraint |
|---|---|---|---|
| `PilotRequest` | `baseline_churn_prob` | float | 0 < x < 1 |
| | `relative_effect` | float | 0 < x < 1 |
| | `alpha` | float | 0 < x < 1, default 0.05 |
| | `power` | float | 0 < x < 1, default 0.80 |
| `PilotResponse` | `n_per_arm`, `total_customers` | int | |

## Cohorts

| Model | Field | Type |
|---|---|---|
| `Segment` | `segment` (str), `customers` (int), `churn_rate` (float) | |
| `CohortResponse` | `dimension` (str), `source` (str: `neo4j` or `pandas`), `segments` (`list[Segment]`) | |

`GET /health` and `GET /model` return plain dictionaries without a Pydantic model.
