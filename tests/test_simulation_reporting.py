
"""Tests for auditable retention scenario reports."""

import pytest

from churn_targeting.simulation.reporting import (
    build_scenario_report,
    compare_scenario_reports,
)
from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


def make_scenario(
    scenario_id: str = "nudge-v1",
    *,
    cost: float = 0.75,
    rate: float = 0.05,
) -> ScenarioConfig:
    return ScenarioConfig(
        scenario_id=scenario_id,
        name="Personalized nudge",
        objective="Explore a hypothetical retention intervention.",
        intervention_type="personalized_nudge",
        cost_per_target=cost,
        target_population=1000,
        assumptions={
            "assumed_incremental_save_rate": rate,
            "currency": "USD",
        },
    )


def test_report_calculates_economics_from_explicit_assumptions():
    report = build_scenario_report(
        make_scenario(),
        value_per_incremental_save=30.0,
    )

    assert report.economics["expected_value_per_target"] == pytest.approx(1.5)
    assert report.economics["expected_net_value_per_target"] == pytest.approx(
        0.75
    )
    assert report.assumptions["evidence_type"] == "explicit_assumptions"
    assert report.simulation is None


def test_report_can_include_successful_simulation_findings():
    scenario = make_scenario()

    simulation = SimulationResult(
        run_id="run-001",
        scenario_id=scenario.scenario_id,
        status="succeeded",
        summary="Hypothetical reactions varied by persona.",
        findings=["Some simulated personas objected to promotional messages."],
        limitations=["Persona reactions are not observed customer behavior."],
    )

    report = build_scenario_report(
        scenario,
        value_per_incremental_save=30.0,
        simulation_result=simulation,
    )

    assert report.simulation is not None
    assert report.simulation["evidence_type"] == "simulation_generated"
    assert report.simulation["metrics"] == {}
    assert "Causal campaign effectiveness requires controlled real-world evaluation." in (
        report.evidence_boundaries
    )


def test_report_rejects_mismatched_simulation():
    scenario = make_scenario()

    simulation = SimulationResult(
        run_id="run-002",
        scenario_id="another-scenario",
        status="succeeded",
    )

    with pytest.raises(ValueError, match="does not match"):
        build_scenario_report(
            scenario,
            value_per_incremental_save=30.0,
            simulation_result=simulation,
        )


def test_report_rejects_failed_simulation():
    scenario = make_scenario()

    simulation = SimulationResult(
        run_id="run-003",
        scenario_id=scenario.scenario_id,
        status="failed",
    )

    with pytest.raises(ValueError, match="successful"):
        build_scenario_report(
            scenario,
            value_per_incremental_save=30.0,
            simulation_result=simulation,
        )


def test_report_requires_explicit_save_rate_assumption():
    scenario = ScenarioConfig(
        scenario_id="missing-rate",
        name="Missing rate",
        objective="Test missing assumptions.",
        intervention_type="none",
        cost_per_target=0,
        target_population=100,
    )

    with pytest.raises(ValueError, match="assumed_incremental_save_rate"):
        build_scenario_report(
            scenario,
            value_per_incremental_save=30.0,
        )


def test_comparison_rejects_duplicate_scenario_ids():
    scenario = make_scenario()
    first = build_scenario_report(
        scenario,
        value_per_incremental_save=30.0,
    )
    second = build_scenario_report(
        scenario,
        value_per_incremental_save=30.0,
    )

    with pytest.raises(ValueError, match="unique"):
        compare_scenario_reports([first, second])


def test_comparison_does_not_claim_a_winning_strategy():
    first = build_scenario_report(
        make_scenario("nudge-v1"),
        value_per_incremental_save=30.0,
    )
    second = build_scenario_report(
        make_scenario("credit-v1", cost=20.0, rate=0.15),
        value_per_incremental_save=30.0,
    )

    comparison = compare_scenario_reports([first, second])

    assert comparison["scenario_count"] == 2
    assert "not interpret the ordering as proof" in comparison["interpretation"]
