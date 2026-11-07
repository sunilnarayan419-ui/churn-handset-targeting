# Simulation overview

```{admonition} Status: experimental
The `churn_targeting.simulation` package is an **experimental, optional decision-support layer**. Its
default mode is a deterministic, assumption-based scenario comparison that runs no simulator. Its MiroFish
integration is gated code that has not been shown, in this repository, to run end to end against a
telecom-appropriate project. Nothing here estimates a causal retention effect.
```

## Components

| Module | Role | Status |
|---|---|---|
| `schemas.py` | `ScenarioConfig` (validated input) and `SimulationResult` (normalised output) | Implemented |
| `config.py` | `SimulationSettings` from `MIROFISH_*` environment variables | Implemented |
| `adapter.py` | `SimulationAdapter` protocol: `submit`, `get_result` | Implemented (interface) |
| `runner.py` | `SimulationRunner`: time-budgeted execution through an injected adapter | Implemented |
| `evaluation.py` | Per-target economics and sensitivity grid from explicit assumptions | Implemented |
| `provenance.py` | SHA-256 scenario fingerprints and run metadata | Implemented |
| `reporting.py` | Scenario reports and comparison document | Implemented |
| `experiment.py` | YAML loading and `run_scenario_comparison` | Implemented |
| `cli.py` | `python -m churn_targeting.simulation.cli` | Implemented |
| `mirofish_client.py`, `mirofish_adapter.py`, `mirofish_health.py`, `mirofish_cli.py` | HTTP client, gated adapter, health check, health CLI | Experimental |

## Workflow

```{mermaid}
flowchart TD
    Y["configs/simulation/*.yaml"] --> LS["load_scenario<br/>yaml.safe_load + ScenarioConfig validation"]
    LS --> RP["build_scenario_report<br/>assess_economics from assumed save rate"]
    RP --> CMP["compare_scenario_reports<br/>no winner declared"]
    LS --> PV["RunProvenance.create<br/>scenario SHA-256"]
    CMP --> OUT1["scenario_comparison.json"]
    PV --> OUT2["experiment_manifest.json<br/>execution_mode: assumption_only_no_simulator"]
    LS -.->|"mirofish-run only, with explicit flags"| PF["read-only preflight<br/>project list screening"]
    PF -.-> AD["MiroFishAdapter.submit and get_result<br/>via SimulationRunner"]
    AD -.-> SR["SimulationResult<br/>activity metrics only"]
```

Solid arrows run by default; dotted arrows apply only to the gated MiroFish path. The API does not import the
simulation package.

## Entry points

| Command | Purpose |
|---|---|
| `python -m churn_targeting.simulation.cli --scenarios ... --value-per-save V` | Assumption-only comparison; writes two JSON files |
| `python -m churn_targeting.simulation.mirofish_cli [--base-url URL]` | Read-only health check of a MiroFish backend |
| `churn-targeting mirofish-preflight --scenario F --project-id ID` | Read-only project screening |
| `churn-targeting mirofish-run ...` | Gated remote run ({doc}`mirofish-integration`) |

The simulation modules are not registered as separate console scripts in `pyproject.toml`.
Design and semantics: {doc}`experimental-design`, {doc}`evaluation`.
