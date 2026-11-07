# Docker

Container assets: {repo}`Dockerfile` and {repo}`docker-compose.yml`. A Docker build does not prove a model is
mounted at runtime.

## Image

| Aspect | Setting |
|---|---|
| Base | `python:3.12-slim` |
| Install | `pip install ".[api,graph]"` from `pyproject.toml` and `src/` |
| User | Non-root user `app`; `/app/models` created and owned by it |
| Port | 8000 |
| Health check | Every 30 s (5 s timeout): fetches `http://127.0.0.1:8000/health` |
| Command | `uvicorn churn_targeting.api.main:create_app --factory --host 0.0.0.0 --port 8000` |

The image contains no data and no model. Static reading of the Dockerfile shows only the `api` and `graph`
extras are installed; the `churn-targeting` command-line interface also imports `pyyaml` and `httpx`
({doc}`../getting-started/installation`), so use the image for the API (its `CMD`), not for the CLI, unless
you add those packages.

```bash
docker build -t churn-targeting .
docker run --rm -p 8000:8000 \
  -v "$(pwd)/models:/app/models:ro" -e MODEL_PATH=/app/models/churn_model.joblib \
  churn-targeting
```

## Compose stack

```bash
# .env must define NEO4J_PASSWORD (at least 8 characters); API_KEY is optional
docker compose up -d neo4j        # graph database only
docker compose up -d              # database and API
```

| Service | Details |
|---|---|
| `neo4j` | Image `neo4j:5`; `NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}` (required); ports 7474 (browser) and 7687 (bolt); volume `neo4j_data`; `cypher-shell` health check |
| `api` | Built from the Dockerfile; waits for a healthy `neo4j`; env `NEO4J_URI=bolt://neo4j:7687`, `NEO4J_USER`, `NEO4J_PASSWORD`, `MODEL_PATH=/app/models/churn_model.joblib`, `API_KEY` (default empty); mounts `./models` read-only; port 8000 |

The API container does not load customer data into Neo4j. Load it from the host, where port 7687 is
published:

```bash
export NEO4J_URI=bolt://localhost:7687 NEO4J_PASSWORD=<same password>
churn-targeting graph-load --reset
```

Train the model on the host first so `./models/churn_model.joblib` exists, and restart the `api` service after
retraining.

## Cautions

- Neo4j ports are published to the host; do not expose them publicly.
- `NEO4J_AUTH` is derived from an environment variable; keep `.env` out of version control.
- CI verifies only that `docker build` succeeds.
