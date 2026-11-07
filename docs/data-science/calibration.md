# Calibration and base-rate adjustment

Two separate corrections are applied to the model's raw score. They answer different questions and neither
changes how customers are *ranked*.

1. **Platt calibration** makes scores behave like probabilities **on the training-sample scale**.
2. **Base-rate (prior-shift) adjustment** rescales those probabilities to an **assumed real-world churn rate**.

Both are implemented in {repo}`src/churn_targeting/calibration.py`.

## Platt scaling

`PlattCalibrator.fit(p_oof, y)` fits a logistic regression with a single input, the logit of the score:

$$
\hat p_{\text{cal}} = \sigma\!\left(a\,\operatorname{logit}(p_{\text{raw}}) + b\right),
\qquad \operatorname{logit}(p)=\ln\frac{p}{1-p},\quad \sigma(z)=\frac{1}{1+e^{-z}}
$$

| Detail | Implementation |
|---|---|
| Fitting data | Out-of-fold predictions on the **training** partition (3-fold `cross_val_predict`) |
| Fit | `LogisticRegression(C=1e6)`, i.e. effectively unregularised; coefficient `a` and intercept `b` are stored |
| Clipping | Scores are clipped to $[10^{-6}, 1-10^{-6}]$ before the logit to avoid infinities |
| Identity | A fresh `PlattCalibrator()` has $a=1$, $b=0$ |

Platt (1999) introduced this sigmoid mapping for classifier scores; see
{doc}`../scientific-reproducibility/references`. With positive $a$ the mapping is monotonic, so ROC-AUC and
the ordering of customers are unchanged by calibration.

## Base-rate adjustment

The sample is enriched with churners (training prevalence $\pi_s$, about 0.496), while the scenario assumes a
monthly churn rate $\pi$ (default 0.0099). Under the assumption that only the class prior differs and the
class-conditional feature distributions are unchanged, Bayes' rule on the odds gives

$$
\operatorname{logit}(p_\pi) = \operatorname{logit}(p_{\text{cal}})
  + \ln\frac{\pi}{1-\pi} - \ln\frac{\pi_s}{1-\pi_s}
$$

implemented by `to_real_world(p_cal, pi_real, pi_sample)`; both base rates must lie strictly between 0 and 1,
otherwise `ValueError`. This is the standard prior-shift correction (Elkan, 2001; Saerens et al., 2002).

```{figure} ../../content/images/fig_calibration.png
:width: 70%
:alt: Reliability diagram on the test set for the raw score and the calibrated probability.

Reliability diagram on the held-out test set, raw score versus calibrated probability (existing manuscript
figure). It is on the enriched-sample scale, so it says nothing about calibration at a 1 % base rate.
```

## What the base-rate adjustment does and does not establish

| Statement | Status |
|---|---|
| Ranking and relative lift are preserved | Follows from monotonicity |
| Probabilities are valid at the stated base rate | **Only if** the 1 % figure is right and the shift assumption holds; both are assumptions |
| The 1 % rate is Company A's measured churn | **No.** It is anchored on published carrier disclosures cited in the manuscript |
| Calibration was validated at 1 % | **No.** No real-world data at that prevalence exist in the repository |
| The outcome window matches | Unverified. The label is "left 31-60 days after observation"; the base rate must refer to the same window and population |

## Where it appears in the API

`POST /score` returns both `churn_probability_calibrated` (sample scale) and
`churn_probability_at_base_rate` (shifted). The `base_rate` query parameter overrides the configured default
and must satisfy $0 < \pi < 1$ ({doc}`../api/endpoints`).

## Evaluation of calibration

The reported Brier scores on the test split are 0.2212 (raw) and 0.2211 (calibrated); the improvement from
calibration is very small, consistent with a raw score that is already close to calibrated on the enriched
scale (see the figure). Brier score and reliability diagrams assess probability quality; neither says
anything about whether contacting a customer changes the outcome ({doc}`evaluation`).
