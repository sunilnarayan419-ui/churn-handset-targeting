# Configuration

All runtime configuration is by environment variable ({doc}`../getting-started/environment-setup` lists every
variable and default). This page covers deployment-time considerations.

| Concern | Guidance (from the source) |
|---|---|
| Model location | `MODEL_PATH` is read once at startup. A missing file is tolerated (`model_loaded: false`); there is no hot reload |
| Base rate | `BASE_RATE` sets the default for `/score`; clients can override per request. It must refer to the same outcome window and population as the label |
| API key | `API_KEY` enables `X-API-Key` on all routes except `/health` |
| Graph | `NEO4J_URI` enables the graph store; credentials from `NEO4J_USER`/`NEO4J_PASSWORD`; `NEO4J_DATABASE` selects the database |
| Simulation | `MIROFISH_*` variables are used only by the simulation command-line tools |
| `.env` | Not parsed by the application; supply variables through the process environment, Compose or your orchestrator |

## Serving options

`churn-targeting serve [--host 127.0.0.1] [--port 8000]` runs Uvicorn with the app factory and defaults to
loopback. The container binds `0.0.0.0`. The code sets no worker count, log configuration, proxy headers or
timeouts; use Uvicorn/Gunicorn options or a process manager if required.

## Artefacts

The model bundle is a pickle: deploy only bundles you trained, from a trusted build, and mount the models
directory read-only (as Compose does).
