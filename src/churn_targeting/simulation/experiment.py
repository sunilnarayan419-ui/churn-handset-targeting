
"""Execute reproducible, assumption-based retention scenario comparisons."""

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from churn_targeting.simulation.provenance import (
    RunProvenance,
)
from churn_targeting.simulation.reporting import (
    build_scenario_report,
    compare_scenario_reports,
)
from churn_targeting.simulation.schemas import ScenarioConfig


def load_scenario(path: Path) -> ScenarioConfig:
    """Load and validate one YAML scenario configuration."""

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError(f"Scenario file must contain a YAML mapping: {path}")

    return ScenarioConfig.model_validate(raw)


def _sha256_json(data: dict[str, Any]) -> str:
    """Hash a JSON-compatible object using canonical serialization."""

    canonical = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_scenario_comparison(
    scenario_paths: list[Path],
    *,
    value_per_incremental_save: float,
    output_dir: Path,
    model_version: str = "not-used",
    simulator_version: str = "not-connected",
) -> dict[str, Any]:
    """Generate reports from explicit assumptions without running MiroFish."""

    if not scenario_paths:
        raise ValueError("At least one scenario file is required")

    if len({path.resolve() for path in scenario_paths}) != len(scenario_paths):
        raise ValueError("Duplicate scenario file paths are not allowed")

    scenarios = [load_scenario(path) for path in scenario_paths]

    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("Scenario IDs must be unique")

    reports = [
        build_scenario_report(
            scenario,
            value_per_incremental_save=value_per_incremental_save,
        )
        for scenario in scenarios
    ]

    comparison = compare_scenario_reports(reports)
    created_at = datetime.now(timezone.utc).isoformat()

    manifest_runs = [
        RunProvenance.create(
            run_id=f"assumption-run-{index + 1:03d}",
            scenario=scenario,
            model_version=model_version,
            simulator_version=simulator_version,
        ).to_dict()
        for index, scenario in enumerate(scenarios)
    ]

    manifest = {
        "created_at_utc": created_at,
        "python_version": platform.python_version(),
        "model_version": model_version,
        "simulator_version": simulator_version,
        "execution_mode": "assumption_only_no_simulator",
        "scenario_count": len(scenarios),
        "scenario_runs": manifest_runs,
        "comparison_sha256": _sha256_json(comparison),
        "limitations": [
            "No MiroFish simulation was executed.",
            "Economic outputs depend on explicitly supplied assumptions.",
            "Assumed save rates are not measured causal effects.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_path = output_dir / "scenario_comparison.json"
    manifest_path = output_dir / "experiment_manifest.json"

    comparison_path.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    return {
        "comparison_path": str(comparison_path),
        "manifest_path": str(manifest_path),
        "scenario_count": len(scenarios),
        "comparison_sha256": manifest["comparison_sha256"],
    }
