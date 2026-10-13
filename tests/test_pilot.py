import pytest

from churn_targeting.pilot import n_per_arm


def test_textbook_example():
    # 10% baseline, 20% relative drop (10% -> 8%): about 3,200 per arm at 80% power, 5% alpha
    assert 3100 <= n_per_arm(0.10, 0.20) <= 3300


def test_matches_analysis_top5_slice():
    assert n_per_arm(0.0524, 0.20) == pytest.approx(6420, rel=0.01)
    assert n_per_arm(0.0524, 0.10) == pytest.approx(27033, rel=0.01)


def test_larger_effect_needs_fewer_customers():
    assert n_per_arm(0.05, 0.3) < n_per_arm(0.05, 0.2) < n_per_arm(0.05, 0.1)


def test_rarer_event_needs_more_customers():
    assert n_per_arm(0.01, 0.2) > n_per_arm(0.05, 0.2)


@pytest.mark.parametrize("p0,rel", [(0, 0.2), (1, 0.2), (0.05, 0), (0.05, 1)])
def test_invalid_inputs(p0, rel):
    with pytest.raises(ValueError):
        n_per_arm(p0, rel)
