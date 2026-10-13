# Testing guide

## Test layers

| Layer | Command | What it checks | Requirement |
|---|---|---|---|
| Lint | `python -m ruff check .` | Selected Ruff rules (`E`, `F`, `B`) | None |
| Syntax | `python -m compileall -q src tests` | Python syntax compilation | None |
| Unit/API | `python -m pytest -m "not integration" -v` | Data helpers, features, model, calibration, finance, pilot sizing and API contracts | Development/API extras |
| Coverage | `python -m pytest -m "not integration" --cov=churn_targeting --cov-report=term-missing` | Line coverage report | `pytest-cov` |
| Neo4j integration | `python -m pytest -m integration -v` | Neo4j cohort results agree with pandas results | Running/configured Neo4j |
| Live API | `./scripts/smoke_test_api.ps1` | HTTP endpoints, scoring and validation | Trained model, running API, PowerShell |
| Docker | `docker build -t churn-targeting:local .` | Container image builds | Docker engine |
| Manuscript | `python scripts/check_manuscript.py` | Undefined manuscript variables | `build/variables.json` and docs extra |

## Windows PowerShell: recommended sequence

Run from the repository root with `.venv` activated:

```powershell
python -m pip check
python -m ruff check .
python -m compileall -q src tests
python -m pytest -m "not integration" -v --cov=churn_targeting --cov-report=term-missing
```

If Neo4j is available and configured, run `python -m pytest -m integration -v` separately.

If pytest is unavailable, confirm the active interpreter with `python -c "import sys; print(sys.executable)"` and install the development dependencies with `python -m pip install -e ".[api,graph,dev]"`.

## Live API smoke test

1. Confirm `Test-Path .\models\churn_model.joblib` returns `True`.
2. Start the API in Terminal 1 with `churn-targeting serve`.
3. In Terminal 2, check `Invoke-RestMethod http://127.0.0.1:8000/health`; `model_loaded` should be `true`.
4. Run `.\scripts\smoke_test_api.ps1` from the repository root.

The smoke script checks health/model metadata, single and batch scoring, economics, pilot sizing, and selected invalid requests. It stops if the model is not loaded, because model-dependent routes may return 503 before the intended request validation is reached.

## Status-code diagnosis

| Result | Interpretation / next step |
|---|---|
| Health is 200 but `model_loaded` is false | Server is alive, but no bundle was loaded. Train, then restart the API. |
| `/model` or `/score` returns 503 | Expected without a loaded model. Check `MODEL_PATH`, file existence, working directory and server restart. |
| Empty `/score/batch` returns 503 | Model dependency may fail before endpoint validation. Load a model before expecting 422. |
| Invalid schema returns 422 | Expected Pydantic/FastAPI validation response. |
| Unknown cohort dimension returns 404 | Expected; dimension validation happens before checking graph/data availability. |
| Valid cohort dimension returns 503 | No graph store or in-memory customer frame is configured. |
| `WinError 10048` | Port is already in use. Reuse/stop that server or run another on a different port. |
| Neo4j connection failure | Check service health, URI, credentials and port; connection failure alone does not prove a code defect. |

## Important limitations

- Synthetic fixtures validate implementation behavior; they do not reproduce the assignment results.
- Passing tests does not establish production model quality, fairness, security or business impact.
- A Docker build does not prove a model is mounted at runtime.
- Coverage is a diagnostic, not proof of correctness.

## Pre-push checklist

- [ ] Ruff and compilation pass.
- [ ] Non-integration tests pass.
- [ ] Neo4j integration passes, or the reason it was not run is recorded.
- [ ] Live API smoke test passes after training.
- [ ] Docker build succeeds if Docker is available.
- [ ] `git diff --check` passes.
- [ ] No `.env`, credentials, raw assignment data, customer-level predictions or unnecessary model binaries are staged.
- [ ] GitHub Actions results are reviewed after pushing.
