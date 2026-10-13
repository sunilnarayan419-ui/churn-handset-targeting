"""Training, evaluation, scoring and persistence of the churn model bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_predict,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from .calibration import PlattCalibrator, to_real_world
from .config import DEFAULT_BASE_RATE, SEED
from .features import DEFAULT_HGB_PARAMS, build_pipeline, column_types, select_features

SEARCH_SPACE = {
    "model__learning_rate": [0.03, 0.05, 0.1],
    "model__max_leaf_nodes": [15, 31, 63],
    "model__min_samples_leaf": [50, 100, 200],
    "model__l2_regularization": [0.0, 1.0, 10.0],
}


@dataclass
class ModelBundle:
    pipeline: Pipeline
    calibrator: PlattCalibrator
    feature_columns: list[str]
    pi_sample: float
    metadata: dict = field(default_factory=dict)
    cat_columns: list[str] = field(default_factory=list)
    num_columns: list[str] = field(default_factory=list)


@dataclass
class TrainResult:
    bundle: ModelBundle
    metrics: dict
    X_test: pd.DataFrame
    y_test: pd.Series
    raw_test_scores: np.ndarray


def evaluate_scores(y_true, p_raw, p_cal) -> dict:
    y_true = np.asarray(y_true)
    pred = (np.asarray(p_raw) >= 0.5).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, p_raw)),
        "pr_auc": float(average_precision_score(y_true, p_raw)),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "brier_raw": float(brier_score_loss(y_true, p_raw)),
        "brier_calibrated": float(brier_score_loss(y_true, p_cal)),
    }


def train(
    df: pd.DataFrame,
    seed: int = SEED,
    params: dict | None = None,
    search: bool = False,
    test_size: float = 0.20,
    n_splits: int = 3,
) -> TrainResult:
    """Split first, then fit everything on the training part; the test part is used once for reporting."""
    X, y = select_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )
    cat_cols, num_cols = column_types(X)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    base = build_pipeline(cat_cols, num_cols, params=params, seed=seed)
    if search:
        rs = RandomizedSearchCV(base, SEARCH_SPACE, n_iter=6, scoring="roc_auc", cv=cv,
                                random_state=seed, n_jobs=1).fit(X_train, y_train)
        pipeline = rs.best_estimator_
        used = {k.replace("model__", ""): v for k, v in rs.best_params_.items()}
    else:
        pipeline = base.fit(X_train, y_train)
        used = dict(params or DEFAULT_HGB_PARAMS)

    oof = cross_val_predict(clone(pipeline), X_train, y_train, cv=cv, method="predict_proba")[:, 1]
    calibrator = PlattCalibrator().fit(oof, y_train)

    p_raw = pipeline.predict_proba(X_test)[:, 1]
    p_cal = calibrator.predict(p_raw)
    metrics = evaluate_scores(y_test, p_raw, p_cal)
    pi_sample = float(y_train.mean())

    metadata = {
        "model_name": "Gradient boosting (HistGradientBoostingClassifier)",
        "target": "churn (left 31-60 days after observation date)",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "seed": seed,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "pi_sample": pi_sample,
        "params": used,
        "metrics_test": metrics,
        "excluded_features": ["Customer_ID", "ethnic"],
        "n_features": int(X.shape[1]),
    }
    bundle = ModelBundle(pipeline, calibrator, X.columns.tolist(), pi_sample, metadata, cat_cols, num_cols)
    return TrainResult(bundle, metrics, X_test, y_test, p_raw)


def score_frame(bundle: ModelBundle, frame: pd.DataFrame, base_rate: float = DEFAULT_BASE_RATE) -> pd.DataFrame:
    """Score customers. Unknown columns are ignored; missing model columns become NaN (handled natively)."""
    X = _prepare(bundle, frame)
    raw = bundle.pipeline.predict_proba(X)[:, 1]
    cal = bundle.calibrator.predict(raw)
    real = to_real_world(cal, base_rate, bundle.pi_sample)
    return pd.DataFrame(
        {"score_raw": raw, "churn_prob_calibrated": cal, "churn_prob_at_base_rate": real},
        index=frame.index,
    )


def _prepare(bundle: ModelBundle, frame: pd.DataFrame) -> pd.DataFrame:
    """Align a raw frame to the training columns and dtypes (an all-missing column arrives as float)."""
    X = frame.reindex(columns=bundle.feature_columns).copy()
    for c in bundle.cat_columns:
        X[c] = X[c].astype(object)
    for c in bundle.num_columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    return X


def missing_feature_count(bundle: ModelBundle, frame: pd.DataFrame) -> pd.Series:
    cols = [c for c in bundle.feature_columns if c in frame.columns]
    return pd.Series(len(bundle.feature_columns) - len(cols), index=frame.index)


def save_bundle(bundle: ModelBundle, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, p)
    p.with_suffix(".json").write_text(json.dumps(bundle.metadata, indent=2))


def load_bundle(path: str | Path) -> ModelBundle:
    """Load a bundle. Only load artifacts you trained yourself: joblib files are pickles."""
    return joblib.load(path)
