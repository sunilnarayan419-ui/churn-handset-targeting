
"""Reproducibility metadata for simulation experiments."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from churn_targeting.simulation.schemas import ScenarioConfig


def scenario_fingerprint(scenario: ScenarioConfig) -> str:
    """Return a stable SHA-256 fingerprint of the validated scenario."""

    payload = scenario.model_dump(mode="json")
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RunProvenance:
    """Metadata identifying a simulation run and its inputs."""

    run_id: str
    scenario_id: str
    scenario_sha256: str
    created_at_utc: str
    model_version: str
    simulator_version: str

    @classmethod
    def create(
        cls,
        run_id: str,
        scenario: ScenarioConfig,
        model_version: str,
        simulator_version: str,
    ) -> "RunProvenance":
        if not run_id.strip():
            raise ValueError("run_id must not be empty")
        if not model_version.strip():
            raise ValueError("model_version must not be empty")
        if not simulator_version.strip():
            raise ValueError("simulator_version must not be empty")

        return cls(
            run_id=run_id,
            scenario_id=scenario.scenario_id,
            scenario_sha256=scenario_fingerprint(scenario),
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            model_version=model_version,
            simulator_version=simulator_version,
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
