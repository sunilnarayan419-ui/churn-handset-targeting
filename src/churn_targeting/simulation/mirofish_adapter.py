"""Explicitly gated adapter for the MiroFish agent-based simulation service."""

from __future__ import annotations

from math import isfinite
from time import monotonic, sleep
from typing import Callable

from churn_targeting.simulation.mirofish_client import MiroFishClient
from churn_targeting.simulation.schemas import ScenarioConfig, SimulationResult


class MiroFishAdapter:
    """Adapt MiroFish to SimulationAdapter with explicit remote-execution gates.

    Important:
    MiroFish uses an existing project's simulation requirement. Its verified
    create/prepare API does not accept ScenarioConfig.objective. The caller
    must explicitly confirm that the project's requirement matches the
    submitted scenario before any remote mutation is allowed.
    """

    _SUCCESS_STATES = {"completed", "succeeded", "finished"}
    _FAILURE_STATES = {"failed", "error", "stopped", "cancelled"}
    _ACTIVE_STATES = {"idle", "pending", "running"}

    def __init__(
        self,
        client: MiroFishClient,
        *,
        project_id: str,
        allow_remote_execution: bool = False,
        confirm_project_requirement_matches_scenario: bool = False,
        max_rounds: int = 3,
        poll_interval_seconds: float = 2.0,
        max_wait_seconds: float = 300.0,
        clock: Callable[[], float] = monotonic,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        if max_rounds < 1:
            raise ValueError("max_rounds must be positive")
        if poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be non-negative")
        if max_wait_seconds <= 0:
            raise ValueError("max_wait_seconds must be positive")

        self.client = client
        self.project_id = project_id
        self.allow_remote_execution = allow_remote_execution
        self.confirm_project_requirement_matches_scenario = (
            confirm_project_requirement_matches_scenario
        )
        self.max_rounds = max_rounds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_wait_seconds = max_wait_seconds
        self._clock = clock
        self._sleep = sleep_fn
        self._scenario_ids: dict[str, str] = {}

    def submit(self, scenario: ScenarioConfig) -> str:
        """Create, prepare, and start a simulation only after explicit opt-in."""
        self._require_remote_permission()

        if not self.project_id.strip():
            raise ValueError("A configured MiroFish project_id is required")

        if not self.confirm_project_requirement_matches_scenario:
            raise RuntimeError(
                "Confirm that the existing MiroFish project requirement "
                "matches this scenario before enabling remote execution."
            )

        created = self.client.create_simulation(self.project_id)
        simulation_id = created.get("simulation_id")

        if not isinstance(simulation_id, str) or not simulation_id.strip():
            raise RuntimeError("MiroFish did not return a valid simulation ID")

        self._scenario_ids[simulation_id] = scenario.scenario_id

        preparation = self.client.prepare_simulation(
            simulation_id,
            use_llm_for_profiles=False,
            parallel_profile_count=1,
            force_regenerate=False,
        )

        status = str(preparation.get("status", "")).lower()
        ready = status == "ready" or preparation.get("already_prepared") is True

        if not ready:
            task_id = preparation.get("task_id")
            if not isinstance(task_id, str) or not task_id.strip():
                raise RuntimeError(
                    "MiroFish preparation did not return a task ID or ready state"
                )

            deadline = self._clock() + self.max_wait_seconds

            while True:
                progress = self.client.get_preparation_status(
                    task_id=task_id,
                    simulation_id=simulation_id,
                )
                status = str(progress.get("status", "")).lower()

                if (
                    status == "ready"
                    or progress.get("already_prepared") is True
                ):
                    break

                if status in self._FAILURE_STATES:
                    raise RuntimeError(
                        f"MiroFish preparation ended with status: {status}"
                    )

                if status == "completed":
                    raise RuntimeError(
                        "Preparation task completed without confirming readiness"
                    )

                if status not in self._ACTIVE_STATES | {"processing", "preparing"}:
                    raise RuntimeError(
                        f"Unexpected MiroFish preparation status: {status or 'missing'}"
                    )

                self._wait(deadline, "preparation")

        self.client.start_simulation(
            simulation_id,
            platform="parallel",
            max_rounds=self.max_rounds,
            enable_graph_memory_update=False,
            force=False,
        )

        return simulation_id

    def get_result(self, run_id: str) -> SimulationResult:
        """Poll execution and normalize activity data without inventing business KPIs."""
        scenario_id = self._scenario_ids.get(run_id)
        if scenario_id is None:
            raise ValueError(
                "Unknown simulation ID for this adapter instance; submit it first"
            )

        deadline = self._clock() + self.max_wait_seconds

        while True:
            data = self.client.get_run_status(run_id)
            status = str(data.get("runner_status", "")).lower()

            if status in self._SUCCESS_STATES:
                return self._result(run_id, scenario_id, "succeeded", data)

            if status in self._FAILURE_STATES:
                return self._result(run_id, scenario_id, "failed", data)

            if status not in self._ACTIVE_STATES:
                raise RuntimeError(
                    f"Unexpected MiroFish run status: {status or 'missing'}"
                )

            self._wait(deadline, "simulation execution")

    def _require_remote_permission(self) -> None:
        if not self.allow_remote_execution:
            raise RuntimeError(
                "Remote MiroFish execution is disabled. "
                "Enable it explicitly before submitting a simulation."
            )

    def _wait(self, deadline: float, phase: str) -> None:
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise TimeoutError(f"MiroFish {phase} exceeded its time budget")

        if self.poll_interval_seconds > 0:
            self._sleep(min(self.poll_interval_seconds, remaining))

    @staticmethod
    def _result(
        run_id: str,
        scenario_id: str,
        status: str,
        data: dict,
    ) -> SimulationResult:
        activity_fields = (
            "current_round",
            "total_rounds",
            "progress_percent",
            "simulated_hours",
            "total_simulation_hours",
            "twitter_actions_count",
            "reddit_actions_count",
            "total_actions_count",
        )

        metrics: dict[str, float] = {}
        for field in activity_fields:
            value = data.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric = float(value)
                if isfinite(numeric):
                    metrics[field] = numeric

        runner_status = str(data.get("runner_status", status)).lower()

        summary = (
            "MiroFish agent-based simulation completed. Activity metrics describe "
            "simulated behavior; they do not establish measured churn reduction, "
            "retention lift, or revenue impact."
            if status == "succeeded"
            else f"MiroFish simulation ended with status '{runner_status}'. "
            "No successful business outcome is inferred."
        )

        findings = [f"MiroFish runner status: {runner_status}."]

        if "total_actions_count" in metrics:
            findings.append(
                "Reported simulated actions: "
                f"{metrics['total_actions_count']:g}."
            )

        return SimulationResult(
            run_id=run_id,
            scenario_id=scenario_id,
            status=status,
            summary=summary,
            metrics=metrics,
            findings=findings,
            limitations=[
                "MiroFish agent activity is simulated output, not observed customer behavior.",
                "Churn reduction, retention lift, and revenue impact were not measured.",
                "The existing MiroFish project requirement must match the submitted scenario.",
            ],
        )
