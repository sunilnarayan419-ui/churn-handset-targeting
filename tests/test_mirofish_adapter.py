"""Mock-only tests for the explicitly gated MiroFish adapter."""

import pytest

from churn_targeting.simulation.mirofish_adapter import MiroFishAdapter
from churn_targeting.simulation.schemas import ScenarioConfig


def make_scenario():
    return ScenarioConfig(
        scenario_id="retention-test-v1",
        name="Retention test",
        objective="Test a hypothetical retention intervention.",
        intervention_type="personalized_nudge",
        cost_per_target=0.5,
        target_population=100,
    )


class FakeMiroFishClient:
    def __init__(self):
        self.calls = []
        self.preparation_states = [
            {"status": "ready", "already_prepared": True}
        ]
        self.run_states = [
            {
                "runner_status": "completed",
                "current_round": 3,
                "total_rounds": 3,
                "total_actions_count": 42,
                "progress_percent": 100,
            }
        ]

    def create_simulation(self, project_id):
        self.calls.append(("create", project_id))
        return {"simulation_id": "sim-mock-1", "status": "created"}

    def prepare_simulation(self, simulation_id, **kwargs):
        self.calls.append(("prepare", simulation_id, kwargs))
        return {
            "simulation_id": simulation_id,
            "task_id": "task-mock-1",
            "status": "preparing",
            "already_prepared": False,
        }

    def get_preparation_status(self, **kwargs):
        self.calls.append(("preparation_status", kwargs))
        if not self.preparation_states:
            return {"status": "ready", "already_prepared": True}
        return self.preparation_states.pop(0)

    def start_simulation(self, simulation_id, **kwargs):
        self.calls.append(("start", simulation_id, kwargs))
        return {"simulation_id": simulation_id, "runner_status": "running"}

    def get_run_status(self, simulation_id):
        self.calls.append(("run_status", simulation_id))
        if len(self.run_states) > 1:
            return self.run_states.pop(0)
        return self.run_states[0]


def make_adapter(client, **overrides):
    options = {
        "project_id": "proj-mock-1",
        "allow_remote_execution": True,
        "confirm_project_requirement_matches_scenario": True,
        "poll_interval_seconds": 0,
        "max_wait_seconds": 2,
    }
    options.update(overrides)
    return MiroFishAdapter(client, **options)


def test_remote_execution_disabled_by_default():
    client = FakeMiroFishClient()
    adapter = MiroFishAdapter(client, project_id="proj-mock-1")

    with pytest.raises(RuntimeError, match="disabled"):
        adapter.submit(make_scenario())

    assert client.calls == []


def test_project_requirement_confirmation_is_required():
    client = FakeMiroFishClient()
    adapter = make_adapter(
        client,
        confirm_project_requirement_matches_scenario=False,
    )

    with pytest.raises(RuntimeError, match="project requirement"):
        adapter.submit(make_scenario())

    assert client.calls == []


def test_submit_prepares_and_starts_with_mocked_client():
    client = FakeMiroFishClient()
    adapter = make_adapter(client)

    run_id = adapter.submit(make_scenario())

    assert run_id == "sim-mock-1"
    assert [call[0] for call in client.calls] == [
        "create",
        "prepare",
        "preparation_status",
        "start",
    ]

    prepare_call = next(call for call in client.calls if call[0] == "prepare")
    assert prepare_call[2]["use_llm_for_profiles"] is False

    start_call = next(call for call in client.calls if call[0] == "start")
    assert start_call[2]["force"] is False
    assert start_call[2]["enable_graph_memory_update"] is False


def test_completed_run_reports_activity_not_retention_impact():
    client = FakeMiroFishClient()
    adapter = make_adapter(client)

    run_id = adapter.submit(make_scenario())
    result = adapter.get_result(run_id)

    assert result.status == "succeeded"
    assert result.scenario_id == "retention-test-v1"
    assert result.metrics["total_actions_count"] == 42.0
    assert "retention lift" in result.summary
    assert any("not observed customer behavior" in item for item in result.limitations)


def test_running_simulation_times_out():
    client = FakeMiroFishClient()
    client.run_states = [{"runner_status": "running"}]

    adapter = make_adapter(client, max_wait_seconds=0.001)
    run_id = adapter.submit(make_scenario())

    with pytest.raises(TimeoutError, match="execution"):
        adapter.get_result(run_id)


def test_failed_simulation_is_not_reported_as_success():
    client = FakeMiroFishClient()
    client.run_states = [{"runner_status": "failed"}]

    adapter = make_adapter(client)
    run_id = adapter.submit(make_scenario())
    result = adapter.get_result(run_id)

    assert result.status == "failed"
    assert "No successful business outcome" in result.summary


def test_unknown_run_id_is_rejected():
    adapter = make_adapter(FakeMiroFishClient())

    with pytest.raises(ValueError, match="Unknown simulation ID"):
        adapter.get_result("sim-not-submitted")
