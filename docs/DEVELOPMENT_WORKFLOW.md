# Development workflow and troubleshooting

## Local setup (Windows PowerShell)

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[api,graph,dev,docs,notebook]"
python -m pip check
```

Select `.venv` with **Ctrl+Shift+P → Python: Select Interpreter** in VS Code. Confirm the interpreter path with `python -c "import sys; print(sys.executable)"`.

## Repeatable local loop

1. Make a focused code change.
2. Run `python -m ruff check .`.
3. Run `python -m compileall -q src tests`.
4. Run `python -m pytest -m "not integration" -v`.
5. For API changes, start the service and run `scripts/smoke_test_api.ps1` after training.
6. Run Neo4j integration tests if graph behavior changed.
7. Update relevant docs and tests in the same change.
8. Inspect `git diff` and `git status`; stage only intended files.

## Train and verify (PowerShell)

The helper script `scripts/train_and_verify.ps1` checks for both original CSVs, runs validation and training, and confirms the expected bundle and metadata JSON exist. It fails fast when source files are missing or a command returns a non-zero exit code.

```powershell
.\scripts\train_and_verify.ps1
```

After successful training, restart the API before checking `model_loaded`. The script does not fabricate input data, start/stop a server, or claim that metrics meet a production threshold.

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

## Manuscript and result generation

```powershell
python scripts/export_results.py --data-dir data/raw --out reports/results.json
python scripts/export_manuscript_variables.py
python scripts/check_manuscript.py
```

Regenerating analysis outputs requires the original assignment files and can take several minutes. The manuscript build uses source files under `content/` and `build/`; generated files under `output/` are not the manuscript source.

## Pre-push safety review

```powershell
git diff --check
git status --short
git ls-files data models .env
git check-ignore data/raw/Client.csv
git check-ignore data/raw/Record.csv
```

Review every file listed by `git status --short` and the staged diff. Ensure raw assignment data, customer-level predictions, local `.env`, secrets, `.venv`, caches and unnecessary binaries are excluded. A directory showing as untracked may contain legitimate files (e.g. `data/README.md`, `docs/`, or `build/build.sh`); inspect file-level paths rather than ignoring the entire directory blindly.
