"""Probability calibration and base-rate (prior-shift) correction."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def expit(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


class PlattCalibrator:
    """Logistic calibration of a score, fitted on out-of-fold training predictions only."""

    def __init__(self, coef: float = 1.0, intercept: float = 0.0):
        self.coef, self.intercept = coef, intercept

    def fit(self, p_oof, y) -> PlattCalibrator:
        lr = LogisticRegression(C=1e6).fit(logit(p_oof).reshape(-1, 1), np.asarray(y))
        self.coef, self.intercept = float(lr.coef_[0, 0]), float(lr.intercept_[0])
        return self

    def predict(self, p):
        return expit(self.coef * logit(p) + self.intercept)


def to_real_world(p_cal, pi_real: float, pi_sample: float):
    """Shift probabilities from the (enriched) sample base rate to a realistic one (Bayes' rule on odds)."""
    if not 0 < pi_real < 1 or not 0 < pi_sample < 1:
        raise ValueError("base rates must be strictly between 0 and 1")
    z = logit(p_cal) + np.log(pi_real / (1 - pi_real)) - np.log(pi_sample / (1 - pi_sample))
    return expit(z)
