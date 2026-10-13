# Training and evaluation guide

## Scope

This guide describes the implemented training flow and the checks required before treating a saved bundle as usable. It does not replace the model card or the data card.

## Prerequisites

- Python 3.10–3.12; Python 3.12 is recommended for local parity with the primary CI jobs.
- Project installed in an active virtual environment with the development/API extras.
- Authorised assignment files `Client.csv` and `Record.csv` in `data/raw/`, unless a different path is passed explicitly.
- Sufficient memory for a 100,000-row tabular dataset and scikit-learn model training.

## Training sequence

### 1. Verify source files and environment

PowerShell:

```powershell
python --version
python -m pip check
Test-Path .\data\raw\Client.csv
Test-Path .\data\raw\Record.csv
```

Both file checks should be `True`. The files are intentionally ignored by Git and must not be redistributed.

### 2. Validate the input data

```powershell
churn-targeting validate
```

The loader checks the required files and performs the expected join on `Customer_ID`. Review the quality summary and stop if the join is not one-to-one, the target is missing/invalid, or unexpected schema/data-quality conditions are reported.

### 3. Train the bundle

```powershell
churn-targeting train
```

The default seed is `42`. The training implementation:

1. selects the target and excludes `Customer_ID` and `ethnic` from the feature matrix;
2. makes a stratified train/test split (default 80/20);
3. fits preprocessing and the `HistGradientBoostingClassifier` pipeline on the training partition;
4. optionally runs a small randomized search when `--search` is supplied;
5. creates out-of-fold training predictions and fits the Platt calibrator on those predictions;
6. evaluates on the held-out test set and prints the metrics;
7. saves a `ModelBundle` to `models/churn_model.joblib` and metadata to `models/churn_model.json`.

To change the input directory, output path, seed, or run the optional search:

```powershell
churn-targeting train --data-dir .\data\raw --out .\models\churn_model.joblib --seed 42
churn-targeting train --search
```

Do not run a search merely to improve the headline metric after inspecting the test set. Any model-selection work should remain within the training/validation data; reserve the test set for final evaluation.

### 4. Verify artifacts

```powershell
Test-Path .\models\churn_model.joblib
Test-Path .\models\churn_model.json
Get-Content .\models\churn_model.json
```

The `.joblib` file contains a Python object and should only be loaded from a trusted source. The JSON sidecar is for readable metadata. Neither file is required to be committed to the public repository; reproduce it from authorised data instead.

### 5. Restart the API after training

The API loads `MODEL_PATH` during application startup. If the API was already running while training occurred, it may retain `model_loaded: false` until restarted.

1. In the terminal running the API, press `Ctrl+C`.
2. Start `churn-targeting serve` again.
3. Check `GET /health`; `model_loaded` should be `true`.
4. Check `GET /model` and then `POST /score`.

If port 8000 is occupied, do not start a second server on the same port. Stop the existing server or use `churn-targeting serve --port 8001` and test against port 8001.

## Metrics and interpretation

The CLI reports ROC-AUC, PR-AUC, accuracy, precision, recall, F1, and raw/calibrated Brier scores. They answer different questions:

- **ROC-AUC:** pairwise ranking discrimination across thresholds; 0.5 is chance ranking.
- **PR-AUC / average precision:** precision–recall performance; its baseline depends on positive-class prevalence.
- **Accuracy, precision, recall and F1:** threshold-dependent metrics; do not interpret them without the chosen threshold and class balance.
- **Brier score:** mean squared probability error; lower is better, but it should be compared against appropriate baselines and reliability plots.
- **Calibration:** Platt calibration is fitted to out-of-fold predictions on the enriched training sample. It does not by itself make probabilities valid for a different deployment prevalence.
- **Base-rate adjustment:** the API applies an odds adjustment using a configured assumed base rate (default `0.0099`). Validate the actual churn definition and observation horizon before using it in a live setting.

The assignment sample is enriched (roughly 49.6% positive), while the business scenario assumes about 1% monthly churn. The base rate must match the deployment outcome window and population. A prevalence shift changes the precision and positive predictive value of a target list, even if rank discrimination stays similar.

## Evaluation gaps before production

- Obtain a time-stamped, representative validation cohort and test temporal generalisation; the supplied assignment has no timestamps.
- Validate calibration and threshold utility on the operator's true deployment prevalence.
- Compare against a trivial baseline and simpler models; report confidence intervals and subgroup results.
- Audit performance and error rates across relevant groups. Excluding `ethnic` does not remove proxy effects from other variables.
- Test stability, missing-feature behavior, drift, latency, and batch sizes in the deployment environment.
- Run a capped randomised holdout pilot to estimate incremental treatment effect; risk prediction alone cannot establish intervention benefit.

## Reproducibility and provenance

- The seed, split sizes, selected parameters, training prevalence, feature count, scikit-learn version, timestamp and test metrics are recorded in bundle metadata.
- `scripts/export_results.py` independently rebuilds analysis/manuscript variables from the raw data; it can take 1–2 minutes on one CPU core.
- Reported results in `reports/` are outputs, not proof that a new run used the same data, package versions or environment.
- Do not commit raw assignment data, model pickles, customer-level predictions or secret configuration.
