# Simulation evaluation

`evaluation.py` and `reporting.py` compute economics **only from explicit assumptions**. The module docstring
states: it "does not estimate causal retention uplift from simulated agent conversations."

## Per-target economics

`assess_economics(cost_per_target, assumed_incremental_save_rate, value_per_incremental_save)` returns an
`EconomicAssessment` (with `assumptions_only=True`):

$$
\text{expected value per target}=s\,V,\qquad
\text{expected net value per target}=sV-c,\qquad
s^{*}=\frac{c}{V}\ (V>0)
$$

All inputs must be finite and non-negative and $s\le 1$, otherwise `ValueError`. `break_even_save_rate` is
`None` if $V=0$. `run_sensitivity_analysis(costs, save_rates, values_per_save)` evaluates the Cartesian
product of the three lists (all must be non-empty).

For the shipped scenarios (value per save $30): the nudge has $s^*=0.025$ and expected net value $+0.75$ per
target; the retention credit has $s^*\approx 0.667$ and expected net value $-15.50$ per target. These values are
in `reports/simulation/scenario_comparison.json`.

```{warning}
**This is not the same $s$ as in {doc}`../business-methodology/retention-economics`.** In `finance.py`, $s$ is
the share of *would-be churners* retained, and break-even depends on the churn probability $p$:
$s^*=(c+aI)/(pV)$. Here $s$ is applied *per contacted target* with no churn probability, so $s^*=c/V$. The
two cannot be compared numerically unless the simulation's $s$ is defined as $p\cdot s_{\text{finance}}$.
The simulation module is a scenario-comparison scaffold with illustrative numbers.
```

## Scenario report

`build_scenario_report` produces a `ScenarioReport`: scenario identifiers, SHA-256 fingerprint, assumptions
(augmented with `value_per_incremental_save` and `evidence_type: explicit_assumptions`), economics, an optional
`simulation` block (only for a `succeeded` result whose `scenario_id` matches; marked
`evidence_type: simulation_generated`) and the fixed `evidence_boundaries`:

- Economic results are conditional on the supplied assumptions.
- Assumed incremental save rates are not measured treatment effects.
- Simulation-generated findings are not observed customer behaviour.
- Causal campaign effectiveness requires controlled real-world evaluation.

`compare_scenario_reports` returns `report_type: exploratory_retention_scenario_comparison`, the scenarios and
an interpretation note. It **does not rank or declare a winner**, and scenario IDs must be unique.

## How to read the outputs

Treat the comparison as arithmetic on stated assumptions. Ordering of scenarios is not evidence that one
intervention works. Replace the illustrative values with measured pilot results before drawing business
conclusions ({doc}`../business-methodology/pilot-design`).
