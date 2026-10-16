
"""Tests for the simulation adapter contract."""

from churn_targeting.simulation.adapter import SimulationAdapter
from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


class FakeSimulationAdapter:
    """Deterministic fake backend for unit tests."""

    def submit(self, scenario: ScenarioConfig) -> str:
        return f"fake-{scenario.scenario_id}"

    def get_result(self, run_id: str) -> SimulationResult:
        scenario_id = run_id.removeprefix("fake-")

        return SimulationResult(
            run_id=run_id,
            scenario_id=scenario_id,
            status="succeeded",
            summary="Synthetic test result; not empirical evidence.",
            findings=["Hypothesis generated for testing."],
            limitations=["Fake backend; no real simulation was executed."],
        )


def test_fake_adapter_obeys_contract():
    adapter: SimulationAdapter = FakeSimulationAdapter()

    scenario = ScenarioConfig(
        scenario_id="baseline-v1",
        name="No intervention",
        objective="Establish a baseline.",
        intervention_type="none",
        cost_per_target=0,
        target_population=100,
    )

    run_id = adapter.submit(scenario)
    result = adapter.get_result(run_id)

    assert run_id == "fake-baseline-v1"
    assert result.scenario_id == scenario.scenario_id
    assert result.status == "succeeded"
    assert "not empirical evidence" in result.summary


def test_fake_adapter_does_not_claim_real_measurements():
    adapter = FakeSimulationAdapter()

    result = adapter.get_result("fake-baseline-v1")

    assert result.metrics == {}
    assert any("no real simulation" in item for item in result.limitations)
