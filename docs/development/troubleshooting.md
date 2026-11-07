# Troubleshooting

## Port 8000 already in use

`WinError 10048` means another process already owns the local port. Inspect it:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

Then inspect the process using the reported PID:

```powershell
Get-Process -Id <PID>
```

If it is the existing API, reuse it rather than starting another server. To run a second instance, use a different port:

```powershell
churn-targeting serve --port 8001
```

Use the same port in the smoke-test command:

```powershell
.\scripts\smoke_test_api.ps1 -BaseUrl http://127.0.0.1:8001
```

## Model reports as not loaded

1. Run `Test-Path .\models\churn_model.joblib`.
2. If false, restore authorised CSVs to `data/raw/` and run `churn-targeting validate` then `churn-targeting train`.
3. Confirm the output path printed by training matches `MODEL_PATH` (default `models/churn_model.joblib`).
4. Restart the API after training.
5. Query `/health`; `model_loaded` should be true.
6. Query `/model`; if still 503, check the server's working directory, `MODEL_PATH`, startup log and whether the artifact can be loaded in the same environment.

Do not silence the status flag or create an empty placeholder model to make the health check appear green.

## Environment files and Neo4j

`.env.example` documents settings; the application reads environment variables and does not automatically parse `.env` unless another tool loads it. For PowerShell, set variables in the current session, for example:

```powershell
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "<your-local-password>"
$env:NEO4J_DATABASE = "neo4j"
```

Use a password of at least 8 characters for the Compose configuration. Do not commit `.env`. The Compose API service mounts `./models` read-only and expects the trained model to exist there; Docker image build success alone does not imply scoring readiness.

## `ModuleNotFoundError: yaml` or `httpx` when running `churn-targeting`

From reading the source: `cli.py` imports the simulation package at import time, which needs `pyyaml` (extra
`docs`) and `httpx` (extra `dev`) in addition to `pydantic` (extra `api`). Install the full set
(`uv pip install -e ".[api,graph,dev,docs,notebook]"`). This explanation is inferred from the code, not
reproduced.

## Documentation build problems

| Symptom | Check |
|---|---|
| Autodoc import errors | The `api` extra and the `sphinx-docs` group must both be installed; `neo4j` is mocked |
| Mermaid diagrams blank | They render in the browser from a CDN; check network access and the `mermaid_version` in `docs/conf.py` |
| "document isn't included in any toctree" | Add the page to a `toctree` in `docs/index.rst` or `docs/api/index.rst` |
| Broken link to a repo file | Use the `{repo}` role instead of a relative file link |
