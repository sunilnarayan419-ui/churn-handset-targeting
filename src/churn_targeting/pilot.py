"""Sample size for a randomised hold-out pilot (two-proportion test)."""

from __future__ import annotations

import math
from statistics import NormalDist


def n_per_arm(baseline_churn_prob: float, relative_effect: float, alpha: float = 0.05,
              power: float = 0.80) -> int:
    """Customers needed in EACH arm to detect a relative drop in churn probability.

    ``relative_effect`` = share of would-be churners the offer keeps (the save rate).
    """
    if not 0 < baseline_churn_prob < 1:
        raise ValueError("baseline_churn_prob must be in (0, 1)")
    if not 0 < relative_effect < 1:
        raise ValueError("relative_effect must be in (0, 1)")
    p0, p1 = baseline_churn_prob, baseline_churn_prob * (1 - relative_effect)
    pbar = (p0 + p1) / 2
    nd = NormalDist()
    za, zb = nd.inv_cdf(1 - alpha / 2), nd.inv_cdf(power)
    num = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
    return int(math.ceil(num / (p0 - p1) ** 2))
