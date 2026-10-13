import numpy as np
import pytest

from churn_targeting.targeting import decile_table, mask_stats, realworld_precision, top_fraction_stats


def test_no_skill_precision_equals_base_rate():
    assert realworld_precision(0.3, 0.3, 0.01) == pytest.approx(0.01)


def test_perfect_classifier_precision_is_one():
    assert realworld_precision(0.4, 0.0, 0.01) == pytest.approx(1.0)


def test_matches_analysis_example():
    # top-10% slice in the analysis: TPR ~0.158, FPR ~0.043 -> ~3.6% at a 1% base rate
    assert realworld_precision(0.158, 0.043, 0.01) == pytest.approx(0.0357, abs=1e-3)


def test_top_fraction_stats_hand_example():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 1, 0])
    score = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
    s = top_fraction_stats(y, score, 0.2, 0.01)
    assert s["contacted"] == 2 and s["churn_rate_in_file"] == 1.0
    assert s["recall"] == pytest.approx(2 / 3) and s["false_positive_rate"] == 0.0
    assert s["precision_at_base_rate"] == pytest.approx(1.0)


def test_decile_table_on_sorted_data():
    y = np.array([1] * 50 + [0] * 50)
    score = np.linspace(1, 0, 100)
    t = decile_table(y, score)
    assert t["customers"].sum() == 100 and len(t) == 10
    assert t["churn_rate"].is_monotonic_decreasing
    assert t["cum_recall"].iloc[-1] == pytest.approx(1.0)


def test_mask_stats():
    y = np.array([1, 1, 0, 0])
    m = np.array([True, False, True, False])
    s = mask_stats(y, m, 0.01)
    assert s["share_of_base"] == 0.5 and s["recall"] == 0.5 and s["churn_rate_in_file"] == 0.5
    assert s["precision_at_base_rate"] == pytest.approx(0.01)
