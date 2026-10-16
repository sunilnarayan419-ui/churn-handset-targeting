
"""Deterministic economic and sensitivity analysis for retention scenarios.

This module evaluates explicit assumptions. It does not estimate causal
retention uplift from simulated agent conversations.
"""

from dataclasses import asdict, dataclass
from itertools import product
from math import isfinite


@dataclass(frozen=True)
class EconomicAssessment:
    """Economic result under explicitly supplied assumptions."""

    cost_per_target: float
    assumed_incremental_save_rate: float
    value_per_incremental_save: float
    expected_value_per_target: float
    expected_net_value_per_target: float
    break_even_save_rate: float | None
    assumptions_only: bool = True

    def to_dict(self) -> dict[str, float | bool | None]:
        return asdict(self)


def _validate_nonnegative_finite(name: str, value: float) -> None:
    """Reject negative, infinite, or NaN economic inputs."""

    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


def assess_economics(
    *,
    cost_per_target: float,
    assumed_incremental_save_rate: float,
    value_per_incremental_save: float,
) -> EconomicAssessment:
    """Calculate scenario economics from explicit assumptions."""

    _validate_nonnegative_finite("cost_per_target", cost_per_target)
    _validate_nonnegative_finite(
        "assumed_incremental_save_rate",
        assumed_incremental_save_rate,
    )
    _validate_nonnegative_finite(
        "value_per_incremental_save",
        value_per_incremental_save,
    )

    if assumed_incremental_save_rate > 1:
        raise ValueError("assumed_incremental_save_rate must be <= 1")

    break_even_rate = (
        cost_per_target / value_per_incremental_save
        if value_per_incremental_save > 0
        else None
    )

    expected_value = (
        assumed_incremental_save_rate * value_per_incremental_save
    )
    net_value = expected_value - cost_per_target

    return EconomicAssessment(
        cost_per_target=cost_per_target,
        assumed_incremental_save_rate=assumed_incremental_save_rate,
        value_per_incremental_save=value_per_incremental_save,
        expected_value_per_target=expected_value,
        expected_net_value_per_target=net_value,
        break_even_save_rate=break_even_rate,
    )


def run_sensitivity_analysis(
    *,
    costs: list[float],
    save_rates: list[float],
    values_per_save: list[float],
) -> list[dict[str, float | bool | None]]:
    """Evaluate every combination of explicit economic assumptions."""

    if not costs or not save_rates or not values_per_save:
        raise ValueError("All sensitivity dimensions must be non-empty")

    rows: list[dict[str, float | bool | None]] = []

    for cost, rate, value in product(costs, save_rates, values_per_save):
        assessment = assess_economics(
            cost_per_target=cost,
            assumed_incremental_save_rate=rate,
            value_per_incremental_save=value,
        )
        rows.append(assessment.to_dict())

    return rows
