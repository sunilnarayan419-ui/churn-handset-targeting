# Quickstart

Two paths: the **calculator path** needs no data, and the **full path** needs your authorised copy of the two
input tables.

## Calculator path (no data, no model)

Start the API; the economics and pilot-sizing routes do not need a trained model.

```bash
churn-targeting serve            # http://127.0.0.1:8000 ; interactive docs at /docs
```

```bash
curl -s -X POST http://127.0.0.1:8000/finance/economics \
  -H "Content-Type: application/json" \
  -d '{"n_treated":1000,"churn_prob":0.05,"avg_monthly_rev":50,"save_rate":0.10,
       "margin":0.40,"months":12,"contact_cost":0.50}'
```

Worked by hand from the formulas in {doc}`../business-methodology/retention-economics`: 50 would-be
churners, 5 saved, value per save 50 × 0.40 × 12 = 240, gross benefit 1 200, variable cost 500, so
`net_variable_benefit` ≈ 700 and `breakeven_save_rate` = 0.50 / (0.05 × 240) ≈ 0.0417. (The arithmetic is
verified by a unit test in `tests/test_api.py`; it checks the calculator, not the business assumptions.)

```bash
curl -s -X POST http://127.0.0.1:8000/pilot/size \
  -H "Content-Type: application/json" \
  -d '{"baseline_churn_prob":0.10,"relative_effect":0.20}'
```

The response contains `n_per_arm` and `total_customers` (twice `n_per_arm`). For these inputs the unit test in `tests/test_api.py` asserts that `n_per_arm` lies between 3,100 and 3,300; the exact integer is not reproduced here because it was not computed during this documentation pass.

## Full path (needs `Client.csv` and `Record.csv`)

1. Place the files in `data/raw/` (see {doc}`../data-science/data-provenance`). They are git-ignored; do not
   redistribute them.
2. Validate keys, the one-to-one join and data quality:

   ```bash
   churn-targeting validate
   ```

3. Train, calibrate, evaluate and save the bundle (`models/churn_model.joblib` and `.json`):

   ```bash
   churn-targeting train            # add --search to re-run the randomised hyper-parameter search
   ```

4. (Re)start the API so it loads the bundle, then check `GET /health` reports `"model_loaded": true`.
5. Score customers with `POST /score` or `POST /score/batch` ({doc}`../api/endpoints`).

Model files are Python pickles: **only load bundles you trained yourself.**

## Optional: scenario comparison without a simulator

```bash
python -m churn_targeting.simulation.cli \
  --scenarios configs/simulation/retention_baseline.yaml \
              configs/simulation/personalized_nudge.yaml \
              configs/simulation/retention_credit.yaml \
  --value-per-save 30
```

This writes `scenario_comparison.json` and `experiment_manifest.json` under `reports/simulation/`. It runs no
simulator ({doc}`../simulation/overview`).

## Next steps

- Interpret metrics responsibly: {doc}`../data-science/evaluation`.
- Understand the economics: {doc}`../business-methodology/break-even-analysis`.
- Containerised run: {doc}`../deployment/docker`.
