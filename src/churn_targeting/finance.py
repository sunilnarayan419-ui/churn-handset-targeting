"""Transparent retention economics. Every input is an explicit argument; none is hidden in the code.

Definitions (per monthly campaign wave):
  N  customers contacted             C  would-be churners among them = N * churn_prob
  S  customers retained = C * s      V  value per retained customer = monthly revenue * margin * months
  gross benefit = S * V              variable cost = N * (contact_cost + accept_rate * incentive)
The save rate ``s`` is the INCREMENTAL effect of contact; the churn model cannot estimate it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assumptions:
    """Labelled assumptions (not measurements). Replace with Company A's figures."""

    base_rate: float = 0.0099
    margin: float = 0.40
    months: int = 12
    contact_cost: float = 0.75
    accept_rate: float = 0.15
    incentive: float = 20.0
    fixed_cost_per_year: float = 60_000.0
    book: int = 100_000


def _check_prob(name: str, v: float) -> None:
    if not 0 <= v <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {v}")


def cost_per_contact(contact_cost: float, accept_rate: float = 0.0, incentive: float = 0.0) -> float:
    return contact_cost + accept_rate * incentive


def value_per_save(avg_monthly_rev: float, margin: float, months: int) -> float:
    return avg_monthly_rev * margin * months


def economics(
    n_treated: float,
    churn_prob: float,
    avg_monthly_rev: float,
    save_rate: float,
    margin: float,
    months: int,
    contact_cost: float,
    accept_rate: float = 0.0,
    incentive: float = 0.0,
) -> dict:
    """Economics of one campaign wave."""
    for name, v in (("churn_prob", churn_prob), ("save_rate", save_rate), ("margin", margin),
                    ("accept_rate", accept_rate)):
        _check_prob(name, v)
    if n_treated < 0 or avg_monthly_rev < 0 or contact_cost < 0 or incentive < 0 or months <= 0:
        raise ValueError("n_treated, revenue, costs must be >= 0 and months > 0")
    would_churn = n_treated * churn_prob
    saved = would_churn * save_rate
    v = value_per_save(avg_monthly_rev, margin, months)
    gross = saved * v
    var_cost = n_treated * cost_per_contact(contact_cost, accept_rate, incentive)
    return {
        "treated": n_treated,
        "would_be_churners": would_churn,
        "saved": saved,
        "value_per_save": v,
        "gross_benefit": gross,
        "variable_cost": var_cost,
        "net_variable_benefit": gross - var_cost,
        "breakeven_save_rate": breakeven_save_rate(churn_prob, avg_monthly_rev, margin, months,
                                                   contact_cost, accept_rate, incentive),
    }


def breakeven_save_rate(
    churn_prob: float, avg_monthly_rev: float, margin: float, months: int,
    contact_cost: float, accept_rate: float = 0.0, incentive: float = 0.0,
) -> float:
    """Share of would-be churners the contact must keep for the wave to pay for itself."""
    denom = churn_prob * value_per_save(avg_monthly_rev, margin, months)
    return float("inf") if denom <= 0 else cost_per_contact(contact_cost, accept_rate, incentive) / denom


def annualize(wave: dict, fixed_cost: float, waves: int = 12, book: int | None = None) -> dict:
    """Roll one wave up to a year (simplification: ignores repeat contact with the same customer)."""
    gross, var_cost = wave["gross_benefit"] * waves, wave["variable_cost"] * waves
    net_var = gross - var_cost
    total_cost = var_cost + fixed_cost
    out = {
        "gross_benefit": gross,
        "variable_cost": var_cost,
        "fixed_cost": fixed_cost,
        "net_benefit": net_var - fixed_cost,
        "roi_pct": 100 * (net_var - fixed_cost) / total_cost if total_cost > 0 else float("nan"),
    }
    if book and net_var > 0:
        out["breakeven_book_size"] = fixed_cost / (net_var / book)
    return out


def sensitivity_grid(churn_prob: float, avg_monthly_rev: float, n_treated: float, margin: float,
                     months: int, save_rates: list[float], contact_costs: list[float]) -> list[list[float]]:
    """Net variable benefit per wave for each (contact cost, save rate) pair."""
    return [
        [economics(n_treated, churn_prob, avg_monthly_rev, s, margin, months, c)["net_variable_benefit"]
         for s in save_rates]
        for c in contact_costs
    ]
