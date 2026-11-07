# Application architecture

## Application factory and lifecycle

`create_app(settings=None, bundle=None, frame=None, store=None)` in {repo}`src/churn_targeting/api/main.py`
builds the FastAPI application. All four collaborators can be injected, which is how the tests run the API
without files or a database.

```{list-table}
:header-rows: 1
:widths: 22 78

* - Phase
  - Behaviour (from the source)
* - Construction
  - `settings` defaults to `Settings.from_env()`. `app.state` receives `bundle`, `frame` and `store`.
    The app is titled "Churn targeting API" and versioned with `churn_targeting.__version__`.
* - Startup (lifespan)
  - If no bundle was injected and `MODEL_PATH` exists, `load_bundle` loads it. If no store was injected and
    `NEO4J_URI` is set, a `GraphStore` is created and flagged as owned by the app.
    A missing model file is **not** an error; the service starts with `model_loaded: false`.
* - Shutdown
  - An app-owned `GraphStore` is closed. Injected stores are left to the caller.
* - Reloading
  - The bundle is read once. Retraining while the service runs does not update the in-memory model;
    restart the service.
```

Served with `uvicorn churn_targeting.api.main:create_app --factory` (the `churn-targeting serve` command and
the Docker `CMD` both use this form).

## Dependencies

| Dependency | Purpose | Raises |
|---|---|---|
| `require_key` | Compares the `X-API-Key` header to `settings.api_key` with `secrets.compare_digest`; does nothing when `API_KEY` is unset | HTTP 401 |
| `get_bundle` | Returns `app.state.bundle` | HTTP 503 `model not loaded; run churn-targeting train` |

`require_key` is attached to every route except `GET /health` through `dependencies=secured`. `get_bundle` is a
parameter dependency of `/model`, `/score` and `/score/batch` only.

## Request lifecycle: `POST /score`

```{mermaid}
sequenceDiagram
    participant Client
    participant App as FastAPI app
    participant Key as require_key
    participant Bundle as get_bundle
    participant Core as score_frame
    Client->>App: POST /score with JSON body and optional base_rate
    App->>Key: Depends(require_key)
    alt API_KEY set and header missing or wrong
        Key-->>Client: 401 invalid or missing X-API-Key
    end
    App->>Bundle: Depends(get_bundle)
    alt no model loaded
        Bundle-->>Client: 503 model not loaded
    end
    Note over App: Pydantic validates the body and base_rate; invalid input returns 422
    App->>Core: _score_many(bundle, customers, base_rate)
    Note over Core: reindex to training columns, coerce dtypes, predict_proba, Platt calibrate, base-rate shift
    Core-->>App: probabilities and missing-feature count
    App-->>Client: 200 ScoreResponse
```

The relative order in which FastAPI reports a 422 and a 503 for the same request is decided by its dependency
resolution. The repository's testing guide records that an invalid batch sent while no model is loaded can
return 503 before the intended 422 is observed ({doc}`../development/testing`).

## Scoring path inside the service

`_score_many` builds a `pandas.DataFrame` from the request dictionaries, calls
`modeling.score_frame(bundle, frame, base_rate)` and `modeling.missing_feature_count`, and returns one
`ScoreResponse` per row, preserving order ({doc}`data-flow`).

## Error handling

Errors are raised as `HTTPException` with a `detail` string (401, 404, 422, 503) or produced by FastAPI's
request validation (422). The code has no custom exception handlers and no logging configuration. Exceptions
that are not `HTTPException` (for example a failing Neo4j driver call inside `/cohorts/{dimension}`) are not
caught by the route and would surface as server errors; this is a source-level observation, not an observed
behaviour. See {doc}`../api/errors`.

## Why a factory

Passing collaborators into `create_app` keeps the application free of module-level state, which makes the
route logic testable and lets the same code serve the CLI, tests and Docker.
