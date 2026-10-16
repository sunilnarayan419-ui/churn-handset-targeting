
"""Orchestration for controlled retention simulation runs."""

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Literal
from uuid import uuid4

from churn_targeting.simulation.adapter import SimulationAdapter
from churn_targeting.simulation.schemas import (
    ScenarioConfig,
    SimulationResult,
)


@dataclass(frozen=True)
class RunOutcome:
    """Outcome and timing information for one simulation attempt."""

    result: SimulationResult
    elapsed_seconds: float


class SimulationRunner:
    """Execute scenarios through an injected simulation adapter."""

    def __init__(
        self,
        adapter: SimulationAdapter,
        timeout_seconds: float = 30.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.adapter = adapter
        self.timeout_seconds = timeout_seconds
        self.clock = clock

    def run(self, scenario: ScenarioConfig) -> RunOutcome:
        """Submit a scenario, retrieve its result, and validate the contract."""

        started = self.clock()
        local_run_id = f"local-{uuid4().hex}"

        try:
            external_run_id = self.adapter.submit(scenario)

            if not external_run_id:
                raise ValueError("Adapter returned an empty run ID")

            if self.clock() - started > self.timeout_seconds:
                return self._failure(
                    local_run_id,
                    scenario.scenario_id,
                    "timed_out",
                    "Scenario submission exceeded the configured time budget.",
                    started,
                )

            result = self.adapter.get_result(external_run_id)

            if self.clock() - started > self.timeout_seconds:
                return self._failure(
                    external_run_id,
                    scenario.scenario_id,
                    "timed_out",
                    "Scenario execution exceeded the configured time budget.",
                    started,
                )

            if result.scenario_id != scenario.scenario_id:
                raise ValueError(
                    "Adapter result scenario_id does not match the request"
                )

            return RunOutcome(
                result=result,
                elapsed_seconds=max(0.0, self.clock() - started),
            )

        except TimeoutError:
            return self._failure(
                local_run_id,
                scenario.scenario_id,
                "timed_out",
                "The adapter reported a timeout.",
                started,
            )

        except Exception as exc:
            return self._failure(
                local_run_id,
                scenario.scenario_id,
                "failed",
                f"Simulation failed: {type(exc).__name__}",
                started,
            )

    def _failure(
        self,
        run_id: str,
        scenario_id: str,
        status: Literal["failed", "timed_out"],
        message: str,
        started: float,
    ) -> RunOutcome:
        """Return a normalized failure without leaking exception details."""

        result = SimulationResult(
            run_id=run_id,
            scenario_id=scenario_id,
            status=status,
            summary=message,
            limitations=[
                "No successful simulation result was produced.",
                "Failure details are intentionally limited to the exception type.",
            ],
        )

        return RunOutcome(
            result=result,
            elapsed_seconds=max(0.0, self.clock() - started),
        )
