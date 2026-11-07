# Technology stack

Versions are the constraints declared in {repo}`pyproject.toml`, not the versions that were installed when the
reported results were produced (the model metadata records the scikit-learn version of each trained bundle).

| Concern | Technology | Constraint / notes |
|---|---|---|
| Language | Python | `requires-python >= 3.10`; CI matrix 3.10, 3.11, 3.12; Docker image `python:3.12-slim` |
| Data handling | pandas, numpy | `pandas>=2.1`, `numpy>=1.26` |
| Machine learning | scikit-learn, joblib | `scikit-learn>=1.4`; `HistGradientBoostingClassifier`, `LogisticRegression` (Platt), `OrdinalEncoder`, `RandomizedSearchCV` |
| Service | FastAPI, Uvicorn, Pydantic v2 | `fastapi>=0.110`, `uvicorn[standard]>=0.29`, `pydantic>=2.5`; extra `api` |
| Graph (optional) | Neo4j 5, Python driver | `neo4j>=5.20`; extra `graph`; Compose and CI use image `neo4j:5` |
| Simulation (experimental) | YAML scenarios, Pydantic, httpx | `httpx` (HTTP client for MiroFish) is declared only in extra `dev`; `pyyaml` only in extra `docs` |
| Research output | Manubot, pandoc, Jinja2 | Extra `docs`; the workflow installs pandoc and runs `build/build.sh` |
| Notebook | matplotlib, seaborn, scipy, Jupyter | Extra `notebook` |
| Tests | pytest, pytest-cov, httpx | Marker `integration` needs Neo4j; synthetic fixtures in `tests/conftest.py` |
| Lint and hooks | Ruff, pre-commit | Rules `E`, `F`, `B`; line length 100; hooks for Ruff and basic file hygiene |
| CI | GitHub Actions | Jobs: lint, test (3.10-3.12), Neo4j integration, Docker build; separate manuscript workflow |
| Container | Docker, Docker Compose | Non-root user, health check on `/health`; optional Neo4j service |
| Documentation site | Sphinx, Furo, MyST Parser, autodoc, sphinx-autodoc-typehints, sphinxcontrib-mermaid, MathJax | Dependency group `sphinx-docs`; Read the Docs configuration in `.readthedocs.yaml`; uv for installation |
| Packaging | setuptools | `src/` layout; console script `churn-targeting` |
