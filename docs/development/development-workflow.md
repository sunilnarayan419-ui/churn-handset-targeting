# Development workflow

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

After successful training, restart the API before checking `model_loaded` (see {doc}`troubleshooting`). The script does not fabricate input data, start/stop a server, or claim that metrics meet a production threshold.




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

## Build the documentation site

Install with uv and build; this is the intended procedure and has not been run by the authors of this page.

```bash
uv sync --extra api --group sphinx-docs
uv run sphinx-build -b html docs docs/_build/html
```

Pages are Markdown (MyST) or reStructuredText; every page must appear in a `toctree` in `docs/index.rst` or
`docs/api/index.rst`. Mermaid diagrams use the `{mermaid}` directive. Link to files outside `docs/` with the
`{repo}` role (for example ``{repo}`src/churn_targeting/finance.py` ``). Keep claims tied to the code, and mark
anything unverified as such.
