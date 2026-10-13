.PHONY: install lint test test-all train serve graph-up graph-load results docs clean

install:            ## editable install with every extra
	pip install -e ".[api,graph,dev,docs,notebook]"

lint:
	ruff check .

test:               ## fast tests (no database)
	pytest -m "not integration"

test-all:           ## needs NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD
	pytest

train:              ## needs data/raw/Client.csv and Record.csv
	churn-targeting train

serve:
	churn-targeting serve

graph-up:
	docker compose up -d neo4j

graph-load:
	churn-targeting graph-load --reset

results:            ## recompute reports/results.json from the raw data
	python scripts/export_results.py

docs:               ## build the Manubot manuscript into output/
	bash build/build.sh

clean:
	rm -rf output build/variables.json ci/cache .pytest_cache .ruff_cache
