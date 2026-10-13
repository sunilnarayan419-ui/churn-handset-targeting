# API reference

The live OpenAPI contract is served at `/openapi.json`; interactive Swagger UI is at `/docs` while the service is running. This page explains expected behavior in operational terms.

## Runtime configuration

The application reads environment variables in `src/churn_targeting/config.py`:

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `data/raw` | Directory containing source assignment CSVs for CLI workflows |
| `MODEL_PATH` | `models/churn_model.joblib` | Trusted trained model bundle loaded at API startup |
| `BASE_RATE` | `0.0099` | Assumed deployment churn base rate used for odds adjustment |
| `API_KEY` | unset | When non-empty, requires `X-API-Key` on all endpoints except `/health` |
| `NEO4J_URI` | unset | When set, API attempts to create a Neo4j graph store at startup |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | unset | Neo4j password; provide through a local environment/secret, not source control |
| `NEO4J_DATABASE` | `neo4j` | Neo4j database name |

The API loads the model during application startup if the configured file exists. Training while the server is running does not automatically reload the in-memory bundle; restart the service after retraining.

## Endpoints

### `GET /health`

Liveness response with `status`, `version`, `model_loaded` and `graph_enabled`. It remains open for health probes even when `API_KEY` is configured. It does not guarantee model scoring is available.

### `GET /model`

Returns trained-bundle metadata, including model name, training timestamp, feature count, exclusions, parameters and test metrics. Returns 503 if the model is not loaded.

### `POST /score`

Request:

```json
{
  "customer": {
    "eqpdays": 350,
    "months": 14,
    "area": "NEW YORK CITY AREA"
  }
}
```

Response fields:

- `churn_probability_calibrated`: probability on the enriched training-sample scale;
- `churn_probability_at_base_rate`: probability after odds adjustment to the requested `base_rate`;
- `base_rate`: base rate used for that request;
- `missing_features`: count of model feature columns not supplied by the request.

Query parameter `base_rate` is optional and must be strictly between 0 and 1. Missing model features are handled by the pipeline; the returned count helps callers identify incomplete inputs. This does not mean missingness is harmless or that the score is equally reliable for sparse records.

### `POST /score/batch`

Request:

```json
{
  "customers": [
    {"eqpdays": 350, "months": 14},
    {"eqpdays": 100, "months": 36},
    {"eqpdays": 400, "months": 8}
  ]
}
```

`customers` must contain 1–5,000 customer objects. The response contains a `results` array with one score per input row, preserving input order. Test empty/oversized lists with a model loaded; model dependency failure can result in 503 before the endpoint's intended validation path is observed.

### `POST /finance/economics`

Required fields: `n_treated`, `churn_prob`, `avg_monthly_rev`, `save_rate`, `margin`, `months`, and `contact_cost`. Optional fields: `accept_rate` (default 0) and `incentive` (default 0). Invalid ranges return 422. Response reports estimated would-be churners, saves, value per save, gross benefit, variable cost, net variable benefit and break-even save rate. Break-even is `null` if value per save is zero.

This is a deterministic scenario calculator. Its output is only as credible as the supplied churn probability, incremental save rate, margin, time horizon and costs.

### `POST /pilot/size`

Required `baseline_churn_prob` and `relative_effect` must be strictly between 0 and 1. Optional `alpha` and `power` default to 0.05 and 0.80 and must also be strictly between 0 and 1. Response includes `n_per_arm` and `total_customers` for a two-arm test. Final study design should specify outcome window, randomisation unit, attrition, multiple testing and operational constraints.

### `GET /cohorts/{dimension}`

Supported dimensions are the fixed set defined in `churn_targeting.analytics.DIMENSIONS`; see `bands.py` and `analytics.py` for current values. Unknown dimensions return 404. A valid dimension returns `source` (`neo4j` or `pandas`) and segment summaries when a graph store or customer frame is available. The default standalone app does not automatically load a customer frame, so valid cohort queries can return 503 unless Neo4j is configured.

## Authentication

If `API_KEY` is non-empty, send it in `X-API-Key` for every route except `/health`. Example PowerShell:

```powershell
$headers = @{ "X-API-Key" = $env:API_KEY }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/model" -Headers $headers
```

Never place a real key in source code, documentation examples, screenshots or committed environment files.

## Common errors

| HTTP status | Typical meaning |
|---|---|
| 200 | Request completed successfully |
| 401 | Missing or invalid `X-API-Key` when auth is enabled |
| 404 | Unknown cohort dimension |
| 422 | Invalid request body or query parameter |
| 503 | Model not loaded for a model-dependent endpoint, or no cohort data/store available |

Always inspect the response body; the `detail` field gives the application-level reason for many 4xx/5xx responses.
