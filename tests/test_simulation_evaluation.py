
"""Tests for deterministic retention economics and sensitivity analysis."""

import pytest

from churn_targeting.simulation.evaluation import (
    assess_economics,
    run_sensitivity_analysis,
)


def test_economic_assessment_calculates_net_value():
    result = assess_economics(
        cost_per_target=2.0,
        assumed_incremental_save_rate=0.10,
        value_per_incremental_save=30.0,
    )

    assert result.expected_value_per_target == pytest.approx(3.0)
    assert result.expected_net_value_per_target == pytest.approx(1.0)
    assert result.break_even_save_rate == pytest.approx(2 / 30)
    assert result.assumptions_only is True


def test_campaign_cost_exceeding_expected_value_is_unprofitable():
    result = assess_economics(
        cost_per_target=10.0,
        assumed_incremental_save_rate=0.10,
        value_per_incremental_save=30.0,
    )

    assert result.expected_net_value_per_target == pytest.approx(-7.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "cost_per_target": -1,
            "assumed_incremental_save_rate": 0.1,
            "value_per_incremental_save": 30,
        },
        {
            "cost_per_target": 1,
            "assumed_incremental_save_rate": 1.1,
            "value_per_incremental_save": 30,
        },
        {
            "cost_per_target": float("nan"),
            "assumed_incremental_save_rate": 0.1,
            "value_per_incremental_save": 30,
        },
    ],
)
def test_invalid_economic_inputs_are_rejected(kwargs):
    with pytest.raises(ValueError):
        assess_economics(**kwargs)


def test_sensitivity_analysis_returns_all_combinations():
    rows = run_sensitivity_analysis(
        costs=[1.0, 2.0],
        save_rates=[0.05, 0.10],
        values_per_save=[20.0, 30.0],
    )

    assert len(rows) == 8
    assert all(row["assumptions_only"] for row in rows)


def test_sensitivity_analysis_rejects_empty_dimensions():
    with pytest.raises(ValueError):
        run_sensitivity_analysis(
            costs=[],
            save_rates=[0.1],
            values_per_save=[30.0],
        )
