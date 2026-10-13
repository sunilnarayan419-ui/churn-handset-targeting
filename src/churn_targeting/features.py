"""Feature selection and the scikit-learn pipeline (all data-dependent steps live inside it)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from .config import SEED
from .data import ID, TARGET

# Protected characteristic: never used for targeting customers (fairness and compliance).
FAIRNESS_EXCLUDED = ("ethnic",)

# Settings selected by randomised search with 3-fold CV on the training data (notebook section 8).
DEFAULT_HGB_PARAMS = {
    "learning_rate": 0.03,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 100,
    "l2_regularization": 1.0,
}


def select_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return model inputs X and the churn label y; drops the id, the target and excluded columns."""
    drop = [c for c in (ID, TARGET, *FAIRNESS_EXCLUDED) if c in df.columns]
    return df.drop(columns=drop), df[TARGET].astype(int)


def column_types(X: pd.DataFrame) -> tuple[list[str], list[str]]:
    cat = X.select_dtypes(exclude="number").columns.tolist()
    num = X.select_dtypes("number").columns.tolist()
    return cat, num


def build_pipeline(
    cat_cols: list[str], num_cols: list[str], params: dict | None = None, seed: int = SEED
) -> Pipeline:
    """Ordinal-encode categories, pass numerics through (missing handled natively), gradient boosting."""
    pre = ColumnTransformer(
        [
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan,
                                   encoded_missing_value=np.nan), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )
    model = HistGradientBoostingClassifier(
        max_iter=400,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        categorical_features=[True] * len(cat_cols) + [False] * len(num_cols),
        random_state=seed,
        **(params or DEFAULT_HGB_PARAMS),
    )
    return Pipeline([("pre", pre), ("model", model)])
