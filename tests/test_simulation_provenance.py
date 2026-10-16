
"""Tests for scenario fingerprints and run provenance."""

from churn_targeting.simulation.provenance import (
    RunProvenance,
    scenario_fingerprint,
)
from churn_targeting.simulation.schemas import ScenarioConfig


def make_scenario(cost=0.0):
    return ScenarioConfig(
        scenario_id="baseline-v1",
        name="Baseline",
        objective="Test reproducibility.",
        intervention_type="none",
        cost_per_target=cost,
        target_population=100,
    )


def test_fingerprint_is_stable():
    scenario = make_scenario()

    assert scenario_fingerprint(scenario) == scenario_fingerprint(scenario)


def test_fingerprint_changes_when_scenario_changes():
    assert scenario_fingerprint(make_scenario(0.0)) != (
        scenario_fingerprint(make_scenario(1.0))
    )


def test_provenance_contains_expected_metadata():
    scenario = make_scenario()

    provenance = RunProvenance.create(
        run_id="run-001",
        scenario=scenario,
        model_version="churn-model-v1",
        simulator_version="mirofish-unverified",
    )

    data = provenance.to_dict()

    assert data["run_id"] == "run-001"
    assert data["scenario_id"] == "baseline-v1"
    assert len(data["scenario_sha256"]) == 64
    assert data["model_version"] == "churn-model-v1"
    assert data["simulator_version"] == "mirofish-unverified"


def test_provenance_rejects_empty_run_id():
    try:
        RunProvenance.create(
            run_id=" ",
            scenario=make_scenario(),
            model_version="model-v1",
            simulator_version="simulator-v1",
        )
    except ValueError as exc:
        assert "run_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
