import pytest

from churn_targeting.finance import (
    annualize,
    breakeven_save_rate,
    cost_per_contact,
    economics,
    sensitivity_grid,
    value_per_save,
)

BASE = dict(n_treated=1000, churn_prob=0.05, avg_monthly_rev=50, save_rate=0.10, margin=0.4, months=12,
            contact_cost=0.5)


def test_hand_calculated_wave():
    e = economics(**BASE)
    assert e["would_be_churners"] == pytest.approx(50)
    assert e["saved"] == pytest.approx(5)
    assert e["value_per_save"] == pytest.approx(240)
    assert e["gross_benefit"] == pytest.approx(1200)
    assert e["variable_cost"] == pytest.approx(500)
    assert e["net_variable_benefit"] == pytest.approx(700)


def test_break_even_save_rate_gives_zero_net():
    be = breakeven_save_rate(0.05, 50, 0.4, 12, 0.5)
    e = economics(**{**BASE, "save_rate": be})
    assert e["net_variable_benefit"] == pytest.approx(0, abs=1e-9)


def test_incentive_cost_per_contact():
    assert cost_per_contact(0.75, 0.15, 20.0) == pytest.approx(3.75)


def test_matches_analysis_break_even_rates():
    # top-5% slice from the analysis: churn prob 5.24%, revenue $46.64, 40% margin, 12 months
    assert breakeven_save_rate(0.0524, 46.64, 0.4, 12, 0.75) == pytest.approx(0.0639, abs=5e-4)
    assert breakeven_save_rate(0.0524, 46.64, 0.4, 12, 0.75, 0.15, 20.0) == pytest.approx(0.32, abs=2e-3)


def test_value_per_save():
    assert value_per_save(46.64, 0.4, 12) == pytest.approx(223.872)


@pytest.mark.parametrize("field,bad", [("churn_prob", 1.5), ("save_rate", -0.1), ("margin", 2), ("months", 0)])
def test_invalid_inputs_rejected(field, bad):
    with pytest.raises(ValueError):
        economics(**{**BASE, field: bad})


def test_annualize_rolls_up_and_computes_roi():
    wave = {"gross_benefit": 1000.0, "variable_cost": 400.0}
    a = annualize(wave, fixed_cost=5000, waves=12, book=100_000)
    assert a["gross_benefit"] == 12000 and a["variable_cost"] == 4800
    assert a["net_benefit"] == pytest.approx(7200 - 5000)
    assert a["roi_pct"] == pytest.approx(100 * 2200 / 9800)
    assert a["breakeven_book_size"] == pytest.approx(5000 / (7200 / 100_000))


def test_no_breakeven_book_when_variable_benefit_is_negative():
    a = annualize({"gross_benefit": 100.0, "variable_cost": 400.0}, fixed_cost=5000, book=100_000)
    assert "breakeven_book_size" not in a and a["net_benefit"] < 0


def test_sensitivity_grid_increases_with_save_rate_and_decreases_with_cost():
    g = sensitivity_grid(0.05, 50, 1000, 0.4, 12, [0.02, 0.05, 0.1], [0.25, 0.5, 1.0])
    assert all(row[0] < row[1] < row[2] for row in g)
    assert all(g[0][j] > g[1][j] > g[2][j] for j in range(3))


def test_break_even_is_infinite_when_a_save_has_no_value():
    assert breakeven_save_rate(0.05, 0.0, 0.4, 12, 0.5) == float("inf")
