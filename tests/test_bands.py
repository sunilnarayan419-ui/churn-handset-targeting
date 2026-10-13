import pandas as pd
import pytest

from churn_targeting import bands


@pytest.mark.parametrize(
    "days,label",
    [(100, "<=100"), (101, "101-150"), (300, "251-300"), (301, "301-350"), (350, "301-350"),
     (351, "351-400"), (400, "351-400"), (401, "401-500"), (700, "501-700"), (701, ">700")],
)
def test_handset_age_boundaries(days, label):
    assert str(bands.handset_age_band(pd.Series([days])).iloc[0]) == label


def test_tenure_bands():
    out = bands.tenure_band(pd.Series([6, 12, 13, 24, 25])).astype(str).tolist()
    assert out == ["<=12 months", "<=12 months", "13-24 months", "13-24 months", ">24 months"]


def test_300_day_rule_edges():
    flags = bands.past_300_days(pd.Series([300, 301, 400, 401])).tolist()
    assert flags == [False, True, True, False]
