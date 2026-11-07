# Model pipeline

The training procedure is implemented in {py:func}`churn_targeting.modeling.train`. Everything that depends on
the data is fitted after the split.

```{mermaid}
flowchart TD
    DF["merged customers"] --> XY["select_features<br/>X without Customer_ID, churn, ethnic; y = churn"]
    XY --> SP["train_test_split<br/>test_size 0.20, stratify y, random_state 42"]
    SP -->|"X_train, y_train"| BP["build_pipeline<br/>OrdinalEncoder + HistGradientBoostingClassifier"]
    SP -->|"X_test, y_test (held out)"| EV
    BP --> Q{"--search?"}
    Q -->|"no"| FIT["fit on training data<br/>default parameters"]
    Q -->|"yes"| RS["RandomizedSearchCV<br/>6 draws, 3-fold, scoring roc_auc"]
    FIT --> OOF
    RS --> OOF["cross_val_predict(clone(pipeline))<br/>3-fold out-of-fold probabilities"]
    OOF --> PL["PlattCalibrator.fit<br/>logistic regression on logit of OOF scores"]
    PL --> EV["evaluate_scores on the test split<br/>raw score and calibrated probability"]
    EV --> PI["pi_sample = mean of y_train"]
    PI --> SV["ModelBundle -> joblib + JSON metadata"]
```

## Stages

| Stage | Implementation | Value |
|---|---|---|
| Seed | `config.SEED` | 42 |
| Split | `train_test_split(..., test_size=0.20, stratify=y, random_state=seed)` | 80 % / 20 %, stratified on churn |
| Cross-validation | `StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)` | 3 folds, used for the optional search and for out-of-fold predictions |
| Encoder | `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=nan, encoded_missing_value=nan)` | Categorical columns only; numerics pass through |
| Estimator | `HistGradientBoostingClassifier` | `max_iter=400`, early stopping with `validation_fraction=0.1`, `n_iter_no_change=20`, categorical features declared to the estimator |
| Default hyper-parameters | `features.DEFAULT_HGB_PARAMS` | `learning_rate=0.03`, `max_leaf_nodes=31`, `min_samples_leaf=100`, `l2_regularization=1.0` |
| Optional search | `modeling.SEARCH_SPACE` | 3 × 3 × 3 × 3 = 81 combinations; `n_iter=6`; 3-fold CV; `scoring="roc_auc"`; `n_jobs=1` |
| Calibration | `PlattCalibrator` | Fitted on out-of-fold training predictions only |
| Held-out evaluation | `evaluate_scores` | ROC-AUC, PR-AUC, accuracy, precision, recall, F1 at threshold 0.5 on raw scores, Brier score raw and calibrated |
| Persistence | `save_bundle` | `joblib.dump` of a `ModelBundle`; metadata JSON next to it |

The source records that the default parameters were chosen by a randomised search with 3-fold cross-validation
on the training data in the analysis notebook (section 8). Running `--search` repeats a smaller search (six
draws of 81 combinations); it is not guaranteed to reproduce the defaults.

## Bundle contents

`ModelBundle` holds the fitted pipeline, the calibrator, the ordered feature columns, `pi_sample` (training
churn rate), metadata, and the categorical and numeric column lists used to align incoming frames. The
metadata JSON contains the model name, target description, UTC training time, scikit-learn version, seed,
train and test sizes, `pi_sample`, parameters, test metrics, excluded features and feature count. See
{doc}`../data-science/model-development`.
