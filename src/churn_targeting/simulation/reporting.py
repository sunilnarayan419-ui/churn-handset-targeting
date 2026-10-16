
"""Build auditable comparison reports for retention scenarios.

Economic outputs are conditional on explicit assumptions.
Simulation findings are qualitative and are not empirical evidence.
"""

from dataclasses import asdict, dataclass
from typing import Any

from churn_targeting.simulation.evaluation import assess_economics
from churn_targeting.simulation.provenance import (
    scenario_fingerprint,
)
from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


@dataclass(frozen=True)
class ScenarioReport:
    """Comparison-ready record for one retention scenario."""

    scenario_id: str
    scenario_name: str
    intervention_type: str
    scenario_sha256: str
    assumptions: dict[str, Any]
    economics: dict[str, Any]
    simulation: dict[str, Any] | None
    evidence_boundaries: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


def build_scenario_report(
    scenario: ScenarioConfig,
    *,
    value_per_incremental_save: float,
    simulation_result: SimulationResult | None = None,
) -> ScenarioReport:
    """Build one report using explicit economics and optional simulation output.

    The assumed incremental save rate must be provided in the scenario's
    assumptions. It is never inferred from a simulated narrative.
    """

    if simulation_result is not None:
        if simulation_result.scenario_id != scenario.scenario_id:
            raise ValueError(
                "Simulation result scenario_id does not match the scenario"
            )

        if simulation_result.status != "succeeded":
            raise ValueError(
                "Only successful simulation results can be included"
            )

    raw_rate = scenario.assumptions.get("assumed_incremental_save_rate")

    if isinstance(raw_rate, bool) or not isinstance(raw_rate, (int, float)):
        raise ValueError(
            "assumptions must include a numeric "
            "assumed_incremental_save_rate"
        )

    economics = assess_economics(
        cost_per_target=scenario.cost_per_target,
        assumed_incremental_save_rate=float(raw_rate),
        value_per_incremental_save=value_per_incremental_save,
    )

    assumptions = dict(scenario.assumptions)
    assumptions["value_per_incremental_save"] = value_per_incremental_save
    assumptions["evidence_type"] = "explicit_assumptions"

    simulation = None
    if simulation_result is not None:
        simulation = {
            "run_id": simulation_result.run_id,
            "status": simulation_result.status,
            "summary": simulation_result.summary,
            "findings": list(simulation_result.findings),
            "limitations": list(simulation_result.limitations),
            "metrics": dict(simulation_result.metrics),
            "evidence_type": "simulation_generated",
        }

    return ScenarioReport(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        intervention_type=scenario.intervention_type,
        scenario_sha256=scenario_fingerprint(scenario),
        assumptions=assumptions,
        economics=economics.to_dict(),
        simulation=simulation,
        evidence_boundaries=[
            "Economic results are conditional on the supplied assumptions.",
            "Assumed incremental save rates are not measured treatment effects.",
            "Simulation-generated findings are not observed customer behavior.",
            "Causal campaign effectiveness requires controlled real-world evaluation.",
        ],
    )


def compare_scenario_reports(
    reports: list[ScenarioReport],
) -> dict[str, Any]:
    """Create a comparison document without asserting a winning strategy."""

    scenario_ids = [report.scenario_id for report in reports]

    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("Scenario IDs must be unique in a comparison")

    return {
        "report_type": "exploratory_retention_scenario_comparison",
        "scenario_count": len(reports),
        "scenarios": [report.to_dict() for report in reports],
        "interpretation": (
            "Compare conditional economic calculations and qualitative "
            "simulation findings. Do not interpret the ordering as proof "
            "of causal retention effectiveness."
        ),
    }

