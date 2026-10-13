# Contributing

1. `pip install -e ".[api,graph,dev,docs,notebook]"` and `pre-commit install`.
2. Run `make lint test` before pushing; `make test-all` if you touch `graph.py` (needs a Neo4j instance).
3. Never commit data, models, `.env` or scored customer lists. Every number in the manuscript must come from `reports/results.json`; change the code, rerun `make results`, then `make docs`.
4. Keep assumptions labelled as assumptions (see `finance.Assumptions`) and never present a model score as a causal effect.
