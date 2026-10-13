import numpy as np
import pytest

from churn_targeting.modeling import (
    load_bundle,
    missing_feature_count,
    save_bundle,
    score_frame,
    train,
)
from conftest import FAST_PARAMS, make_customers


def test_model_beats_chance_on_planted_signal(trained):
    assert trained.metrics["roc_auc"] > 0.62
    assert trained.metrics["brier_calibrated"] <= trained.metrics["brier_raw"] + 0.01


def test_test_split_is_twenty_percent(trained, customers):
    assert len(trained.X_test) == pytest.approx(0.2 * len(customers), abs=2)
    assert trained.bundle.metadata["n_train"] + trained.bundle.metadata["n_test"] == len(customers)


def test_protected_and_id_columns_not_used(trained):
    cols = trained.bundle.feature_columns
    assert "ethnic" not in cols and "Customer_ID" not in cols and "churn" not in cols


def test_scores_are_probabilities_and_base_rate_lowers_them(trained, customers):
    s = score_frame(trained.bundle, customers.head(50), base_rate=0.0099)
    assert len(s) == 50
    assert ((s > 0) & (s < 1)).all().all()
    assert (s["churn_prob_at_base_rate"] < s["churn_prob_calibrated"]).all()


def test_scoring_tolerates_missing_and_extra_columns(trained, customers):
    partial = customers[["eqpdays", "months"]].head(5).assign(unrelated=1)
    s = score_frame(trained.bundle, partial)
    assert len(s) == 5 and s["churn_prob_calibrated"].between(0, 1).all()
    assert missing_feature_count(trained.bundle, partial).iloc[0] == len(trained.bundle.feature_columns) - 2


def test_handset_age_step_is_learned(trained, customers):
    base = customers.head(200).copy()
    young = score_frame(trained.bundle, base.assign(eqpdays=150))["score_raw"].mean()
    old = score_frame(trained.bundle, base.assign(eqpdays=350))["score_raw"].mean()
    assert old > young


def test_save_and_load_roundtrip(trained, customers, tmp_path):
    path = tmp_path / "m.joblib"
    save_bundle(trained.bundle, path)
    assert path.with_suffix(".json").exists()
    again = load_bundle(path)
    a = score_frame(trained.bundle, customers.head(20))["score_raw"].to_numpy()
    b = score_frame(again, customers.head(20))["score_raw"].to_numpy()
    assert np.allclose(a, b)


def test_training_is_deterministic():
    df = make_customers(1500, seed=3)
    a, b = train(df, params=FAST_PARAMS), train(df, params=FAST_PARAMS)
    assert a.metrics == b.metrics


def test_scoring_with_only_categorical_fields_missing(trained, customers):
    row = customers.head(3).drop(columns=["area", "crclscod"])
    assert score_frame(trained.bundle, row)["churn_prob_calibrated"].between(0, 1).all()


def test_scoring_accepts_none_in_numeric_fields(trained):
    rows = [{"eqpdays": None, "months": 12, "area": "DALLAS AREA"}, {"eqpdays": 350, "months": None}]
    import pandas as pd

    assert len(score_frame(trained.bundle, pd.DataFrame(rows))) == 2
