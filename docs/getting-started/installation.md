# Installation

The package is `churn-targeting` (version in {repo}`pyproject.toml`), built with setuptools from a `src/`
layout. It requires **Python 3.10 or newer**; the CI workflow tests Python 3.10, 3.11 and 3.12 and the Docker
image uses 3.12.

## Install with uv

[uv](https://docs.astral.sh/uv/) is the recommended installer. From the repository root:

```bash
uv venv --python 3.12
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
uv pip install -e ".[api,graph,dev,docs,notebook]"
```

The repository does not contain a `uv.lock` file, so uv resolves dependencies at install time. If you prefer
uv's project workflow, `uv sync --extra api --extra graph --extra dev --extra docs --extra notebook` creates
the environment and writes a local `uv.lock`; commit it only if you intend to maintain it.

`pip` works equally well: `python -m pip install -e ".[api,graph,dev,docs,notebook]"`.

## Dependency groups

Dependencies are declared in {repo}`pyproject.toml`.

| Name | Kind | Contents | Needed for |
|---|---|---|---|
| (core) | `dependencies` | numpy, pandas, scikit-learn, joblib | Data loading, modelling, finance, pilot sizing |
| `api` | extra | fastapi, uvicorn[standard], pydantic | The REST service; also imported by the simulation schemas |
| `graph` | extra | neo4j (Python driver) | Neo4j cohort layer |
| `notebook` | extra | matplotlib, seaborn, scipy, jupyter | Notebook; `scripts/export_results.py` (uses scipy) |
| `docs` | extra | manubot, jinja2, pyyaml | **Manubot manuscript build** (not this website) |
| `dev` | extra | pytest, pytest-cov, httpx, ruff, pre-commit | Tests, linting, hooks |
| `sphinx-docs` | dependency group | sphinx, furo, myst-parser, sphinx-autodoc-typehints, sphinxcontrib-mermaid, httpx, pyyaml | **This documentation website** |

```{important}
Static inspection of the source shows that `churn_targeting.cli` (the `churn-targeting` entry point) imports
the simulation package at module level. That pulls in `pydantic` (extra `api`), `pyyaml` (extra `docs`) and
`httpx` (extra `dev`). Installing only the core dependencies is therefore unlikely to be sufficient to run the
command-line interface; use the full install command above. This observation comes from reading the code and
has not been confirmed by running it.
```

## Build this documentation locally

```bash
uv sync --extra api --group sphinx-docs
uv run sphinx-build -b html docs docs/_build/html
```

The `api` extra is installed so that `autodoc` can import the package; `neo4j` is mocked in
{repo}`docs/conf.py`. Mermaid diagrams are rendered in the browser and need network access to the mermaid
CDN. Output goes to `docs/_build/` (git-ignored). The Read the Docs configuration is in
{repo}`.readthedocs.yaml`.

## Verify the installation

```bash
python -c "import churn_targeting; print(churn_targeting.__version__)"
churn-targeting --help
```
