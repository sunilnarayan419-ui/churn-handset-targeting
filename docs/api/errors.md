# Errors

The application raises `fastapi.HTTPException` with a string `detail`; request validation errors are produced
by FastAPI itself. There are no custom exception handlers.

| Status | When | Body |
|---|---|---|
| 200 | Success | Response model |
| 401 | `API_KEY` is set and `X-API-Key` is missing or wrong | `{"detail": "invalid or missing X-API-Key"}` |
| 404 | `/cohorts/{dimension}` with an unknown dimension | `{"detail": "unknown dimension; choose from ['area', 'credit_class', 'handset_age', 'price_tier', 'tenure']"}` |
| 422 | Request body, path or query parameter violates the schema; or `economics()` raises `ValueError` | FastAPI validation body (`detail` is a list of `loc`/`msg`/`type` items), or `{"detail": "<message>"}` for `ValueError` |
| 503 | No model loaded (`/model`, `/score`, `/score/batch`) | ``{"detail": "model not loaded; run `churn-targeting train`"}`` |
| 503 | `/cohorts/{dimension}` with neither a graph store nor an in-memory frame | `{"detail": "no graph store or customer data configured"}` |

Always read the response body: `detail` carries the application-level reason.

## Common diagnoses

| Symptom | Interpretation |
|---|---|
| `/health` is 200 but `model_loaded` is false | The process is alive but no bundle was loaded at startup. Train, check `MODEL_PATH`, restart |
| `/score` returns 503 | Expected without a loaded model |
| An invalid batch returns 503, not 422 | The model dependency can fail before the body is validated; load a model before testing validation |
| A valid cohort dimension returns 503 | Neo4j is not configured and no frame is injected; the default app loads no frame |
| 401 on every call | `API_KEY` is set; send the header |

## Failures that are not translated

Exceptions other than `HTTPException` are not caught by the routes. In particular, `ValueError` from the
base-rate shift (an invalid configured `BASE_RATE`) and errors raised by the Neo4j driver during a cohort query
would propagate as unhandled server errors (HTTP 500). This is inferred from the source and has not been
exercised.
