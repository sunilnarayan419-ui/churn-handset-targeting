import pandas as pd
import pytest

from churn_targeting import bands
from churn_targeting.analytics import churn_by_segment


def test_handset_age_segments_in_band_order_and_complete(customers):
    t = churn_by_segment(customers, "handset_age")
    assert t["segment"].tolist() == [s for s in bands.HANDSET_AGE_LABELS if s in set(t["segment"])]
    assert t["customers"].sum() == len(customers)
    assert t["churn_rate"].between(0, 1).all()


def test_planted_step_visible_in_cohort_table(customers):
    t = churn_by_segment(customers, "handset_age").set_index("segment")
    assert t.loc["301-350", "churn_rate"] > t.loc["251-300", "churn_rate"]


def test_small_exact_example():
    df = pd.DataFrame({"eqpdays": [50, 60, 320, 330, 340], "churn": [0, 1, 1, 1, 0]})
    t = churn_by_segment(df, "handset_age").set_index("segment")
    assert t.loc["<=100", "customers"] == 2 and t.loc["<=100", "churn_rate"] == 0.5
    assert t.loc["301-350", "customers"] == 3 and t.loc["301-350", "churn_rate"] == pytest.approx(2 / 3)


def test_unknown_dimension_rejected(customers):
    with pytest.raises(KeyError):
        churn_by_segment(customers, "not_a_dimension")


def test_area_segments_alphabetical(customers):
    t = churn_by_segment(customers, "area")
    assert t["segment"].tolist() == sorted(t["segment"].tolist())
