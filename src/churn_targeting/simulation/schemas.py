
"""Validated input and output contracts for churn-retention simulations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioConfig(BaseModel):
    """Configuration for one hypothetical retention scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=2000)

    intervention_type: Literal[
        "none",
        "personalized_nudge",
        "retention_credit",
        "custom",
    ]

    cost_per_target: float = Field(ge=0, allow_inf_nan=False)
    target_population: int = Field(ge=1)

    assumptions: dict[str, str | int | float | bool] = Field(
        default_factory=dict
    )
    questions: list[str] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Normalized result returned by a simulation adapter."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1, max_length=200)
    scenario_id: str = Field(min_length=1, max_length=100)

    status: Literal[
        "pending",
        "running",
        "succeeded",
        "failed",
        "timed_out",
    ]

    summary: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
