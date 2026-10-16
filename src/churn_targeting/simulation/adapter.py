
"""Service boundary for optional multi-agent simulation integrations."""

from typing import Protocol

from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


class SimulationAdapter(Protocol):
    """Interface that any simulation backend must implement."""

    def submit(self, scenario: ScenarioConfig) -> str:
        """Submit a scenario and return its external run identifier."""
        ...

    def get_result(self, run_id: str) -> SimulationResult:
        """Retrieve and validate a completed simulation result."""
        ...
