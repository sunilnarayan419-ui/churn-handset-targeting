
"""Tests for simulation request and result validation."""

from typing import Any, cast

import pytest
from pydantic import ValidationError

from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


@pytest.fixture
def valid_scenario() -> dict:
    return {
        "scenario_id": "retention-baseline-v1",
        "name": "No intervention",
        "objective": "Establish a baseline for retention strategy analysis.",
        "intervention_type": "none",
        "cost_per_target": 0.0,
        "target_population": 1000,
        "assumptions": {
            "baseline_churn_rate": 0.25,
            "currency": "USD",
        },
        "questions": ["What happens without a retention offer?"],
    }


def test_valid_scenario_is_accepted(valid_scenario):
    scenario = ScenarioConfig(**valid_scenario)

    assert scenario.scenario_id == "retention-baseline-v1"
    assert scenario.cost_per_target == 0.0
    assert scenario.target_population == 1000


def test_negative_campaign_cost_is_rejected(valid_scenario):
    valid_scenario["cost_per_target"] = -1.0

    with pytest.raises(ValidationError):
        ScenarioConfig(**valid_scenario)


def test_zero_target_population_is_rejected(valid_scenario):
    valid_scenario["target_population"] = 0

    with pytest.raises(ValidationError):
        ScenarioConfig(**valid_scenario)


def test_invalid_intervention_type_is_rejected(valid_scenario):
    valid_scenario["intervention_type"] = "guaranteed_retention"

    with pytest.raises(ValidationError):
        ScenarioConfig(**valid_scenario)


def test_unknown_fields_are_rejected(valid_scenario):
    valid_scenario["secret_api_key"] = "must-not-be-accepted"

    with pytest.raises(ValidationError):
        ScenarioConfig(**valid_scenario)


def test_simulation_result_is_accepted():
    result = SimulationResult(
        run_id="run-001",
        scenario_id="retention-baseline-v1",
        status="succeeded",
        summary="Exploratory simulation completed.",
        metrics={},
        findings=["Customer reactions varied across hypothetical personas."],
        limitations=["Persona reactions are simulated, not observed."],
    )

    assert result.status == "succeeded"
    assert result.metrics == {}
    assert len(result.limitations) == 1



def test_invalid_result_status_is_rejected():
    invalid_status = cast(Any, "proven")

    with pytest.raises(ValidationError):
        SimulationResult(
            run_id="run-002",
            scenario_id="retention-baseline-v1",
            status=invalid_status,
        )
