# Evaluation

This page defines the metrics the code computes, reports the existing results and states what they do and do
not support. Numbers are taken from `reports/results.json` and the model card; **they were not regenerated for
this documentation** and cannot be reproduced without the original data.

## Three different questions

```{list-table}
:header-rows: 1
:widths: 22 28 50

* - Question
  - Metrics
  - What it does *not* tell you
* - **Discrimination**: does the score rank churners above stayers?
  - ROC-AUC, PR-AUC, lift, recall at top-k, deciles
  - Whether probabilities are numerically right, or whether contact changes behaviour
* - **Calibration**: do predicted probabilities match observed frequencies?
  - Brier score, reliability diagram
  - Ranking quality; validity at a different base rate; any causal effect
* - **Causal effectiveness**: does contacting a customer reduce churn?
  - Difference in churn between randomised treatment and control arms
  - Not estimable from this data; no randomised pilot has been run
```

## Metrics computed by the code

`modeling.evaluate_scores(y_true, p_raw, p_cal)` returns:

| Key | Definition | Note |
|---|---|---|
| `roc_auc` | Area under the ROC curve of the **raw** score | 0.5 is chance ranking; the probability that a random churner outscores a random stayer (Hanley and McNeil, 1982) |
| `pr_auc` | Average precision of the raw score | Its no-skill baseline equals the positive rate (about 0.496 here) |
| `accuracy`, `precision`, `recall`, `f1` | At the threshold 0.5 on the raw score | Threshold-dependent; on a near-balanced file, accuracy is not a useful headline |
| `brier_raw`, `brier_calibrated` | $\frac1n\sum_i (p_i-y_i)^2$ (Brier, 1950) | Lower is better; compare with a baseline and a reliability plot |

`targeting.top_fraction_stats` and `targeting.decile_table` add ranking statistics at a contact capacity
({doc}`../business-methodology/customer-targeting`).

## Reported results

Setting: 100,000 customers, stratified 80/20 split with seed 42, test set of 20,000 customers used once,
default hyper-parameters.

| Metric | Value |
|---|---|
| ROC-AUC | 0.693 (95 % bootstrap interval 0.687-0.701) |
| PR-AUC | 0.681 |
| Accuracy / precision / recall / F1 (threshold 0.5) | 0.636 / 0.630 / 0.645 / 0.638 |
| Brier score | 0.2212 raw, 0.2211 calibrated |
| Comparison models, test ROC-AUC | dummy 0.500, logistic regression 0.644, random forest 0.675 |
| ROC-AUC by tenure | ≤ 12 months 0.749; 13-24 months 0.650; > 24 months 0.682 |
| ROC-AUC across 19 areas | 0.640 to 0.734 |

The bootstrap interval is computed by `scripts/export_results.py`: 300 resamples of the test set with
`numpy.random.default_rng(42)` and the 2.5th and 97.5th percentiles of ROC-AUC. It reflects test-set sampling
variation only, not data drift or model re-fitting. `train` itself reports no interval.

### Ranking performance on the test set

Contacting the top fraction of the 20,000 test customers by raw score (precision and lift re-scaled to an
assumed 1 % base rate with Bayes' rule):

| Slice | Contacted | Churn rate in file | Recall | Precision at 1 % base rate | Lift at 1 % base rate |
|---|---:|---:|---:|---:|---:|
| Top 5 % | 1,000 | 84.6 % | 8.5 % | 5.3 % | 5.3× |
| Top 10 % | 2,000 | 78.4 % | 15.8 % | 3.6 % | 3.6× |
| Top 20 % | 4,000 | 73.3 % | 29.6 % | 2.7 % | 2.7× |
| Rule: handset age 301-400 days | 20.9 % of customers | 59.8 % | 25.3 % | 1.5 % | 1.5× |

At a realistic base rate the large majority of contacted customers would have stayed anyway; the value of a
campaign therefore rests on the incremental effect of contact, not on the score ({doc}`../business-methodology/break-even-analysis`).

```{figure} ../../content/images/fig_eqpdays.png
:width: 80%
:alt: Churn rate by days using the current handset with 95 percent confidence intervals.

Churn rate by days using the current handset, with 95 % confidence intervals (manuscript Figure 1). This is an
association in the sample, not a causal effect of handset age.
```

## Interpretation limits

- All metrics describe one random split of one enriched sample. There is no temporal validation.
- ROC-AUC 0.693 is moderate discrimination; the top-5 % lift is large relative to the assumed base rate but
  inherits the uncertainty of that assumption.
- Subgroup AUC varies (0.650 to 0.749 by tenure), so a single global figure hides heterogeneity.
- Excluding `ethnic` does not prove fairness; no subgroup error-rate audit across protected or proxy groups is
  implemented.

## Gaps before any operational use

1. A time-stamped, representative validation cohort and a test of temporal generalisation.
2. Calibration and threshold utility at the operator's true prevalence and outcome window.
3. Comparison with simpler baselines on that cohort, with confidence intervals and subgroup results.
4. A fairness and proxy audit, and legal basis, consent and opt-out handling for contact.
5. Tests of stability, missing-feature behaviour, drift, latency and batch sizes in the deployment environment.
6. A capped randomised hold-out pilot to estimate the incremental effect ({doc}`../business-methodology/pilot-design`).

## Reproducing the numbers

```bash
python scripts/export_results.py --data-dir data/raw --out reports/results.json
```

requires the raw data and the `notebook` extra (scipy). `tests/test_artifacts.py` checks that
`reports/results.json` and `reports/notebook_results.json` agree. A reported result is an output, not proof
that a new run used the same data, package versions or environment.
