
"""Tests for scenario loading and report generation."""

import json

import pytest
import yaml

from churn_targeting.simulation.experiment import (
    load_scenario,
    run_scenario_comparison,
)


def write_scenario(path, scenario_id="baseline-v1", rate=0.0):
    data = {
        "scenario_id": scenario_id,
        "name": "Baseline",
        "objective": "Test the assumption-only reporting pipeline.",
        "intervention_type": "none",
        "cost_per_target": 0.0,
        "target_population": 100,
        "assumptions": {
            "assumed_incremental_save_rate": rate,
            "currency": "USD",
        },
        "questions": [],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_scenario_validates_yaml(tmp_path):
    path = write_scenario(tmp_path / "baseline.yaml")

    scenario = load_scenario(path)

    assert scenario.scenario_id == "baseline-v1"


def test_pipeline_creates_comparison_and_manifest(tmp_path):
    scenario_path = write_scenario(tmp_path / "baseline.yaml")
    output_dir = tmp_path / "reports"

    result = run_scenario_comparison(
        [scenario_path],
        value_per_incremental_save=30.0,
        output_dir=output_dir,
    )

    comparison_path = output_dir / "scenario_comparison.json"
    manifest_path = output_dir / "experiment_manifest.json"

    assert comparison_path.exists()
    assert manifest_path.exists()
    assert result["scenario_count"] == 1

    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert comparison["scenario_count"] == 1
    assert manifest["execution_mode"] == "assumption_only_no_simulator"
    assert len(manifest["comparison_sha256"]) == 64


def test_pipeline_rejects_duplicate_scenario_ids(tmp_path):
    first = write_scenario(tmp_path / "first.yaml", "same-id")
    second = write_scenario(tmp_path / "second.yaml", "same-id")

    with pytest.raises(ValueError, match="Scenario IDs must be unique"):
        run_scenario_comparison(
            [first, second],
            value_per_incremental_save=30.0,
            output_dir=tmp_path / "reports",
        )


def test_pipeline_rejects_empty_scenario_list(tmp_path):
    with pytest.raises(ValueError, match="At least one"):
        run_scenario_comparison(
            [],
            value_per_incremental_save=30.0,
            output_dir=tmp_path / "reports",
        )


def test_identical_inputs_produce_identical_comparison_hashes(tmp_path):
    scenario_path = write_scenario(
        tmp_path / "baseline.yaml",
        scenario_id="baseline-v1",
        rate=0.0,
    )

    first = run_scenario_comparison(
        [scenario_path],
        value_per_incremental_save=30.0,
        output_dir=tmp_path / "first",
    )

    second = run_scenario_comparison(
        [scenario_path],
        value_per_incremental_save=30.0,
        output_dir=tmp_path / "second",
    )

    assert first["comparison_sha256"] == second["comparison_sha256"]
