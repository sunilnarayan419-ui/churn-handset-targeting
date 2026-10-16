
"""Configuration for the optional simulation service."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SimulationSettings:
    """Runtime settings; the simulation service is optional."""

    base_url: str = ""
    timeout_seconds: float = 30.0
    max_scenario_bytes: int = 100_000

    @classmethod
    def from_env(cls) -> "SimulationSettings":
        return cls(
            base_url=os.getenv("MIROFISH_BASE_URL", "").rstrip("/"),
            timeout_seconds=float(
                os.getenv("MIROFISH_TIMEOUT_SECONDS", "30")
            ),
            max_scenario_bytes=int(
                os.getenv("MIROFISH_MAX_SCENARIO_BYTES", "100000")
            ),
        )

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if self.max_scenario_bytes <= 0:
            raise ValueError("max_scenario_bytes must be positive")

        if self.base_url and not self.base_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("base_url must use HTTP or HTTPS")
