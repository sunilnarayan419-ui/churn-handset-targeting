import numpy as np
import pytest

from churn_targeting.calibration import PlattCalibrator, expit, logit, to_real_world


def test_logit_expit_roundtrip():
    p = np.array([0.01, 0.2, 0.5, 0.9])
    assert np.allclose(expit(logit(p)), p, atol=1e-6)


def test_prior_shift_is_identity_at_same_base_rate():
    p = np.array([0.05, 0.3, 0.7])
    assert np.allclose(to_real_world(p, 0.5, 0.5), p)


def test_lower_base_rate_lowers_probability_and_keeps_order():
    p = np.linspace(0.05, 0.95, 19)
    q = to_real_world(p, 0.0099, 0.496)
    assert np.all(q < p) and np.all(np.diff(q) > 0)


@pytest.mark.parametrize("pi_real,pi_sample", [(0, 0.5), (1, 0.5), (0.1, 0), (0.1, 1.2)])
def test_invalid_base_rates_rejected(pi_real, pi_sample):
    with pytest.raises(ValueError):
        to_real_world(np.array([0.3]), pi_real, pi_sample)


def test_platt_recovers_identity_on_calibrated_scores():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.random(20000) < p).astype(int)
    cal = PlattCalibrator().fit(p, y)
    assert abs(cal.coef - 1) < 0.15 and abs(cal.intercept) < 0.1
    assert np.all((cal.predict(p) > 0) & (cal.predict(p) < 1))
