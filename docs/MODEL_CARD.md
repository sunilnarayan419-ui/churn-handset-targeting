# Model card: handset-age churn model

**Model.** `HistGradientBoostingClassifier` (scikit-learn) with ordinal-encoded categoricals and native missing-value handling; Platt calibration; optional base-rate shift. Settings: learning rate 0.03, 31 leaf nodes, min 100 samples per leaf, L2 = 1.0 (chosen by 3-fold CV, randomised search of 6 settings).

**Intended use.** Rank customers by risk of leaving within 31-60 days so that a capacity-limited, low-cost retention contact reaches the highest-risk slice, with a randomised hold-out to measure the effect. **Not** for individual decisions about service, pricing or credit, and not a causal estimate of what contact or a handset upgrade does.

**Data.** 100,000 anonymised customers, 97 usage, billing, handset and demographic features; 49.6% churned (enriched; real monthly churn is about 1%). `Customer_ID` and `ethnic` are excluded. No timestamps.

**Evaluation** (stratified 80/20 split, seed 42, test set used once): ROC-AUC 0.693 (95% bootstrap 0.687-0.701), PR-AUC 0.681, accuracy 0.636, precision 0.630, recall 0.645, F1 0.638, Brier 0.2211 calibrated. Baseline (no skill) ROC-AUC 0.500. Logistic regression 0.644, random forest 0.675. Top 5% by risk: 5.3x lift at an assumed 1% base rate.

**Subgroups.** ROC-AUC about 0.75 for customers in their first year, 0.65 for 13-24 months, 0.68 beyond; 0.64-0.73 across the 19 areas.

**Limitations.** Association only; no time-based validation; column timing unverified; moderate discrimination; base-rate-adjusted numbers depend on an assumed rate; remaining demographic fields (income, marital status, etc.) may act as proxies and need a fairness review before deployment.

**Monitoring.** Track ROC-AUC and calibration monthly by tenure group; retrain on drift; recalibrate on the operator's real base rate.
