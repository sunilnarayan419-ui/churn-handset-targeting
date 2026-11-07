# Model card: handset-age churn model

Format after Mitchell et al. (2019); see {doc}`references`. Numbers are existing reported results and were not
regenerated.

## Model details

`HistGradientBoostingClassifier` (scikit-learn) with ordinal-encoded categoricals and native missing-value
handling, Platt calibration and an optional base-rate shift. Settings: learning rate 0.03, 31 leaf nodes,
minimum 100 samples per leaf, L2 = 1.0, early stopping, seed 42 (selected by 3-fold cross-validation in the
notebook; the packaged `--search` option reruns a smaller randomised search). Details:
{doc}`../data-science/model-development`.

## Intended use

Rank customers by risk of leaving within 31-60 days so that a capacity-limited, low-cost retention contact
reaches the highest-risk slice, with a randomised hold-out to measure the effect.

**Out of scope:** individual decisions about service, pricing or credit; any causal estimate of what contact or
a handset upgrade does.

## Data

100,000 anonymised customers; 97 usage, billing, handset and demographic features; 49.6 % churned (enriched;
the assumed real monthly churn is about 1 %). `Customer_ID` and `ethnic` are excluded; no timestamps
({doc}`data-card`).

## Evaluation (stratified 80/20 split, seed 42, test set used once)

ROC-AUC 0.693 (95 % bootstrap 0.687-0.701), PR-AUC 0.681, accuracy 0.636, precision 0.630, recall 0.645,
F1 0.638, Brier 0.2211 calibrated (0.2212 raw). No-skill ROC-AUC 0.500; logistic regression 0.644; random
forest 0.675. Top 5 % by risk: 5.3× lift at an assumed 1 % base rate. Full tables:
{doc}`../data-science/evaluation`.

## Subgroups

ROC-AUC about 0.75 in the first year of tenure, 0.65 for 13-24 months, 0.68 beyond; 0.64-0.73 across the 19
areas.

## Limitations

Association only; no time-based validation; column timing unverified; moderate discrimination;
base-rate-adjusted numbers depend on an assumed rate; remaining demographic fields (income, marital status,
etc.) may act as proxies and need a fairness review before deployment ({doc}`limitations`).

## Monitoring

Track ROC-AUC and calibration monthly by tenure group; retrain on drift; recalibrate on the operator's real
base rate. (Recommended; not implemented in the repository.)
