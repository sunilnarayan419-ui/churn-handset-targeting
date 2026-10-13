"""Cohort analytics in pandas. Same output schema as the Neo4j queries (graph.py), so either can serve the API."""

from __future__ import annotations

import pandas as pd

from . import bands

# dimension -> (source column, band function or None, ordered labels or None)
DIMENSIONS: dict[str, tuple[str, object, list[str] | None]] = {
    "handset_age": ("eqpdays", bands.handset_age_band, bands.HANDSET_AGE_LABELS),
    "tenure": ("months", bands.tenure_band, bands.TENURE_LABELS),
    "price_tier": ("hnd_price", bands.price_tier, bands.PRICE_LABELS),
    "area": ("area", None, None),
    "credit_class": ("crclscod", None, None),
}


def segment_labels(df: pd.DataFrame, dimension: str) -> pd.Series:
    if dimension not in DIMENSIONS:
        raise KeyError(f"unknown dimension {dimension!r}; choose from {sorted(DIMENSIONS)}")
    col, fn, _ = DIMENSIONS[dimension]
    if col not in df.columns:
        raise KeyError(f"column {col!r} needed for dimension {dimension!r} is missing")
    return fn(df[col]) if fn else df[col]


def churn_by_segment(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Customers and churn rate per segment, in natural band order (or alphabetical)."""
    seg = segment_labels(df, dimension)
    t = (df.assign(segment=seg.astype("object")).dropna(subset=["segment"])
         .groupby("segment", observed=True)["churn"].agg(customers="size", churn_rate="mean").reset_index())
    order = DIMENSIONS[dimension][2]
    if order:
        t["segment"] = pd.Categorical(t["segment"], categories=order, ordered=True)
        t = t.sort_values("segment")
        t["segment"] = t["segment"].astype(str)
    else:
        t = t.sort_values("segment")
    return t.reset_index(drop=True)
