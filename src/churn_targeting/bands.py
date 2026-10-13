"""Customer segments shared by the pandas analytics and the Neo4j loader (single source of truth)."""

from __future__ import annotations

import numpy as np
import pandas as pd

HANDSET_AGE_EDGES = [-np.inf, 100, 150, 200, 250, 300, 350, 400, 500, 700, np.inf]
HANDSET_AGE_LABELS = ["<=100", "101-150", "151-200", "201-250", "251-300",
                      "301-350", "351-400", "401-500", "501-700", ">700"]
TENURE_EDGES = [0, 12, 24, 100]
TENURE_LABELS = ["<=12 months", "13-24 months", ">24 months"]
PRICE_EDGES = [0, 30, 100, 150, 1000]
PRICE_LABELS = ["<=$30", "$30-100", "$100-150", ">$150"]


def handset_age_band(eqpdays: pd.Series) -> pd.Series:
    return pd.cut(eqpdays, HANDSET_AGE_EDGES, labels=HANDSET_AGE_LABELS)


def tenure_band(months: pd.Series) -> pd.Series:
    return pd.cut(months, TENURE_EDGES, labels=TENURE_LABELS)


def price_tier(hnd_price: pd.Series) -> pd.Series:
    return pd.cut(hnd_price, PRICE_EDGES, labels=PRICE_LABELS)


def past_300_days(eqpdays: pd.Series) -> pd.Series:
    """Boolean flag for the 301-400 day cohort used as the simple rule in the analysis."""
    return (eqpdays > 300) & (eqpdays <= 400)
