
"""Unit tests for simulation orchestration."""

from churn_targeting.simulation.runner import SimulationRunner
from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


class FakeAdapter:
    def __init__(self):
        self.submitted = []

    def submit(self, scenario):
        self.submitted.append(scenario.scenario_id)
        return f"fake-{scenario.scenario_id}"

    def get_result(self, run_id):
        scenario_id = run_id.removeprefix("fake-")
        return SimulationResult(
            run_id=run_id,
            scenario_id=scenario_id,
            status="succeeded",
            summary="Synthetic test output.",
            limitations=["Fake adapter; not empirical evidence."],
        )


def make_scenario():
    return ScenarioConfig(
        scenario_id="baseline-v1",
        name="Baseline",
        objective="Test the no-intervention scenario.",
        intervention_type="none",
        cost_per_target=0,
        target_population=100,
    )


def test_runner_executes_scenario():
    adapter = FakeAdapter()
    outcome = SimulationRunner(adapter).run(make_scenario())

    assert outcome.result.status == "succeeded"
    assert outcome.result.scenario_id == "baseline-v1"
    assert outcome.elapsed_seconds >= 0
    assert adapter.submitted == ["baseline-v1"]


def test_runner_rejects_nonpositive_timeout():
    adapter = FakeAdapter()

    try:
        SimulationRunner(adapter, timeout_seconds=0)
    except ValueError as exc:
        assert "timeout_seconds" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_runner_handles_adapter_failure():
    class BrokenAdapter:
        def submit(self, scenario):
            raise ConnectionError("Private endpoint details")

        def get_result(self, run_id):
            raise AssertionError("Must not be called")

    outcome = SimulationRunner(BrokenAdapter()).run(make_scenario())

    assert outcome.result.status == "failed"
    assert "ConnectionError" in outcome.result.summary
    assert "Private endpoint details" not in outcome.result.summary


def test_runner_detects_wrong_scenario_result():
    class MismatchedAdapter:
        def submit(self, scenario):
            return "external-run-1"

        def get_result(self, run_id):
            return SimulationResult(
                run_id=run_id,
                scenario_id="different-scenario",
                status="succeeded",
            )

    outcome = SimulationRunner(MismatchedAdapter()).run(make_scenario())

    assert outcome.result.status == "failed"
    assert "ValueError" in outcome.result.summary


def test_runner_handles_adapter_timeout():
    class TimeoutAdapter:
        def submit(self, scenario):
            raise TimeoutError("Request timed out")

        def get_result(self, run_id):
            raise AssertionError("Must not be called")

    outcome = SimulationRunner(TimeoutAdapter()).run(make_scenario())

    assert outcome.result.status == "timed_out"
