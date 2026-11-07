# Model development

## Prediction objective

Estimate, for each customer, the probability of leaving 31 to 60 days after the observation date and use the
**ranking** of those probabilities to choose whom to contact. The model is a supervised binary classifier; its
output is an association, not a treatment effect.

## Model choice

The notebook and manuscript compared four models on the same split: a dummy baseline, regularised logistic
regression, a random forest and a histogram-based gradient-boosting classifier. Hyper-parameters were tuned
with three-fold cross-validation on the training data and the model was chosen by cross-validated ROC-AUC
before the test set was examined. Reported test ROC-AUC values (from the model card): dummy 0.500, logistic
regression 0.644, random forest 0.675, gradient boosting 0.693. ROC-AUC is the principal metric because a
capacity-limited campaign depends on how well customers are ranked.

## Estimator

The packaged model is scikit-learn's `HistGradientBoostingClassifier`, a histogram-based implementation of
gradient-boosted decision trees (Friedman, 2001; the scikit-learn implementation is described in its user
guide as inspired by LightGBM, Ke et al., 2017; see {doc}`../scientific-reproducibility/references`). Settings
that the code fixes or defaults:

| Setting | Value |
|---|---|
| `max_iter` | 400 (upper bound; early stopping applies) |
| Early stopping | `early_stopping=True`, `validation_fraction=0.1`, `n_iter_no_change=20` |
| `learning_rate` | 0.03 |
| `max_leaf_nodes` | 31 |
| `min_samples_leaf` | 100 |
| `l2_regularization` | 1.0 |
| `random_state` | 42 |

The last four are `DEFAULT_HGB_PARAMS`. Early stopping holds out 10 % of the *training* partition internally;
it is separate from the final test split.

## Training procedure and artefacts

The sequence is shown in {doc}`../architecture/model-pipeline`. In practice:

```bash
churn-targeting validate
churn-targeting train                          # default parameters
churn-targeting train --search                 # optional randomised search (6 draws, 3-fold, ROC-AUC)
churn-targeting train --data-dir data/raw --out models/churn_model.joblib --seed 42
```

`train` prints the saved path and the test metrics as JSON and writes two files:

- `models/churn_model.joblib`: a pickled `ModelBundle`. **Load only bundles you trained or trust.**
- `models/churn_model.json`: readable metadata (model name, target, UTC timestamp, scikit-learn version, seed,
  `n_train`, `n_test`, `pi_sample`, parameters, test metrics, excluded features, feature count).

Do not run `--search` to improve a headline number after looking at the test set; model-selection work
belongs inside the training data.

## Prediction workflow

`modeling.score_frame(bundle, frame, base_rate)` aligns a frame to the training columns, predicts the raw
score, applies the Platt calibrator and the base-rate shift, and returns three columns: `score_raw`,
`churn_prob_calibrated` and `churn_prob_at_base_rate`. The API wraps this ({doc}`../api/endpoints`).
After retraining, restart the API; it loads the bundle only at startup.

## Reproducibility

The seed, split sizes, selected parameters, training prevalence, feature count, scikit-learn version and
metrics are stored in the bundle metadata. `scripts/export_results.py` rebuilds the reported numbers from the
raw data (about 1-2 minutes on one CPU core, per its docstring). A new run is not guaranteed to match earlier
reports if the data, scikit-learn version or environment differ; `tests/test_modeling.py` checks that two runs
on the same synthetic data are deterministic.

## Monitoring considerations

The model card recommends tracking ROC-AUC and calibration monthly by tenure group, retraining on drift and
recalibrating on the operator's real base rate. None of this monitoring is implemented in the repository.
