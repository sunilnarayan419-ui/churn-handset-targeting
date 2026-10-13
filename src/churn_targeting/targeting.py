"""Ranking quality and base-rate-adjusted precision for a capacity-limited campaign."""

from __future__ import annotations

import numpy as np
import pandas as pd


def realworld_precision(tpr: float, fpr: float, pi: float) -> float:
    """Share of contacted customers who would really churn at base rate ``pi`` (Bayes' rule)."""
    denom = tpr * pi + fpr * (1 - pi)
    return float(tpr * pi / denom) if denom > 0 else float("nan")


def top_fraction_stats(y_true, score, frac: float, pi_real: float) -> dict:
    """Metrics when contacting the top ``frac`` of customers by score."""
    y = np.asarray(y_true)
    order = np.argsort(-np.asarray(score), kind="stable")
    k = max(1, int(frac * len(y)))
    sel = y[order[:k]]
    pos, neg = y.sum(), len(y) - y.sum()
    tp = sel.sum()
    tpr, fpr = tp / pos, (k - tp) / neg
    prec_real = realworld_precision(tpr, fpr, pi_real)
    return {
        "contacted": k,
        "churn_rate_in_file": float(tp / k),
        "recall": float(tpr),
        "false_positive_rate": float(fpr),
        "lift_in_file": float((tp / k) / y.mean()),
        "precision_at_base_rate": prec_real,
        "lift_at_base_rate": prec_real / pi_real,
    }


def mask_stats(y_true, mask, pi_real: float) -> dict:
    """Same metrics for a rule-based selection (e.g. handset 301-400 days)."""
    y, m = np.asarray(y_true), np.asarray(mask, dtype=bool)
    tpr, fpr = m[y == 1].mean(), m[y == 0].mean()
    prec_real = realworld_precision(tpr, fpr, pi_real)
    return {"share_of_base": float(m.mean()), "churn_rate_in_file": float(y[m].mean()),
            "recall": float(tpr), "precision_at_base_rate": prec_real,
            "lift_at_base_rate": prec_real / pi_real}


def decile_table(y_true, score) -> pd.DataFrame:
    y = np.asarray(y_true)
    order = np.argsort(-np.asarray(score), kind="stable")
    ys = y[order]
    n = len(ys)
    dec = np.minimum((np.arange(n) * 10) // n, 9) + 1
    t = pd.DataFrame({"decile": dec, "churn": ys}).groupby("decile").churn.agg(["size", "mean"])
    t.columns = ["customers", "churn_rate"]
    t["lift_vs_avg"] = t.churn_rate / y.mean()
    t["cum_recall"] = (t.churn_rate * t.customers).cumsum() / y.sum()
    return t
