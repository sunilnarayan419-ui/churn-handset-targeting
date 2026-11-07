# Experimental design

## Scenario schema

`ScenarioConfig` ({repo}`src/churn_targeting/simulation/schemas.py`) forbids unknown fields
(`extra="forbid"`):

| Field | Type | Constraint |
|---|---|---|
| `scenario_id` | str | 1-100 characters |
| `name` | str | 1-200 characters |
| `objective` | str | 1-2000 characters |
| `intervention_type` | literal | `none`, `personalized_nudge`, `retention_credit`, `custom` |
| `cost_per_target` | float | ≥ 0, finite |
| `target_population` | int | ≥ 1 |
| `assumptions` | dict of str, int, float or bool | default empty |
| `questions` | list of str | default empty |

`SimulationResult` carries `run_id`, `scenario_id`, `status` (`pending`, `running`, `succeeded`, `failed`,
`timed_out`), `summary`, `metrics` (floats), `findings` and `limitations`.

## Provided scenarios

`configs/simulation/` holds three illustrative scenarios. Their values are configuration assumptions, labelled
`evidence_type: illustrative_assumptions`, not evidence of any effect.

| Scenario file | `scenario_id` | Cost per target | Assumed incremental save rate | Value per save | Population |
|---|---|---:|---:|---:|---:|
| `retention_baseline.yaml` | `retention-baseline-v1` | $0 | 0 % | $30 | 1,000 |
| `personalized_nudge.yaml` | `personalized-nudge-v1` | $0.75 | 5 % | $30 | 1,000 |
| `retention_credit.yaml` | `retention-credit-v1` | $20 | 15 % | $30 | 1,000 |

The save rate must be supplied as the numeric assumption `assumed_incremental_save_rate`; the report builder
raises `ValueError` otherwise, and it is "never inferred from a simulated narrative".

## Experiment execution

`run_scenario_comparison(paths, value_per_incremental_save, output_dir, model_version="not-used",
simulator_version="not-connected")`:

1. Requires at least one path; rejects duplicate paths and duplicate `scenario_id`s.
2. Loads and validates each YAML file (`yaml.safe_load`; the file must contain a mapping).
3. Builds one report per scenario and a comparison document.
4. Writes `scenario_comparison.json` and `experiment_manifest.json` (`allow_nan=False`) to `output_dir`
   (default `reports/simulation`).

## Provenance

`scenario_fingerprint` is the SHA-256 of the canonical JSON of the validated scenario (sorted keys, compact
separators). `RunProvenance` records `run_id`, `scenario_id`, `scenario_sha256`, UTC creation time,
`model_version` and `simulator_version` (non-empty). The manifest also records the Python version, the
scenario count, `execution_mode` (`assumption_only_no_simulator`), a SHA-256 of the comparison document and
these limitations: no MiroFish simulation was executed, outputs depend on supplied assumptions, assumed save
rates are not measured causal effects. The committed manifest in `reports/simulation/` was produced in this
mode.

## Runner

`SimulationRunner(adapter, timeout_seconds=30.0, clock=monotonic)` submits a scenario, fetches the result and
validates that `result.scenario_id` matches. Exceeding the time budget after submit or after result retrieval
returns a `timed_out` result; `TimeoutError` from the adapter is also `timed_out`; any other exception becomes
`failed` with only the exception type in the message (details are deliberately not leaked). Time is checked
between adapter calls, so it is not a hard interruption of a blocking call.
