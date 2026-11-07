# MiroFish integration

```{admonition} Status: experimental and optional
MiroFish is an external multi-agent simulation service. The integration code is gated by explicit flags and a
read-only preflight. The repository contains no recorded end-to-end run against a telecom-appropriate
project, and the README states that the existing MiroFish test project is fictional and agricultural and must
not be used. Treat every output as simulated activity, not observed customer behaviour.
```

## Architecture and adapter boundary

The experiment layer depends only on the `SimulationAdapter` protocol (`submit(scenario) -> run_id`,
`get_result(run_id) -> SimulationResult`). `MiroFishAdapter` implements it on top of `MiroFishClient`, an
`httpx` wrapper; `MiroFishHealthClient` is a separate read-only client.

```{mermaid}
sequenceDiagram
    participant CLI as churn-targeting mirofish-run
    participant PF as preflight
    participant R as SimulationRunner
    participant A as MiroFishAdapter
    participant M as MiroFish backend
    CLI->>PF: GET /api/graph/project/list (read-only)
    PF-->>CLI: candidate_requires_manual_review or blocked
    CLI->>R: run(scenario) only if preflight passed
    R->>A: submit(scenario)
    A->>M: POST /api/simulation/create
    A->>M: POST /api/simulation/prepare
    A->>M: POST /api/simulation/prepare/status (poll)
    A->>M: POST /api/simulation/start
    R->>A: get_result(simulation_id)
    A->>M: GET /api/simulation/{id}/run-status (poll)
    A-->>R: SimulationResult with activity metrics
```

## Safety gates

1. `mirofish-run` requires both `--allow-remote-execution` and `--confirm-project-requirement-matches-scenario`
   (argparse `required=True`), plus `--scenario` and `--project-id`.
2. Before any mutation it runs the **preflight**: `GET /api/graph/project/list`. The project is
   `blocked_incompatible_or_unverified` if its requirement text contains agricultural markers (`agricultural`,
   `agriculture`, `farmer`, `compost`, `nandipur`) or none of the telecom markers (`telecom`, `churn`,
   `retention`, `handset`, `subscriber`); otherwise it is `candidate_requires_manual_review`. The output always
   states `execution_authorized: false` and that keyword matching is only a heuristic needing human review.
3. `MiroFishAdapter.submit` re-checks `allow_remote_execution` and the confirmation flag. The MiroFish API
   used does not accept the scenario objective, so the human must confirm that the existing project's
   requirement matches the scenario.
4. `MiroFishClient` rejects non-HTTP(S) URLs, URLs with credentials, queries or fragments, and does not follow
   redirects.

## Behaviour and configuration

- The adapter creates a simulation for the project with Twitter and Reddit disabled in the create payload,
  prepares it with `use_llm_for_profiles=False`, `parallel_profile_count=1`, `force_regenerate=False`, polls
  preparation, then starts with `platform="parallel"`, `max_rounds` (default 3) and
  `enable_graph_memory_update=False`.
- Polling uses `poll_interval_seconds=2.0` and `max_wait_seconds` (default 300; CLI flag). The runner timeout
  defaults to 360 s on the CLI. Success states: `completed`, `succeeded`, `finished`; failure states:
  `failed`, `error`, `stopped`, `cancelled`.
- Configuration: `MIROFISH_BASE_URL`, `MIROFISH_TIMEOUT_SECONDS`; `--base-url` overrides the URL.
- Health: `MiroFishHealthClient.check_health()` GETs `/health` and requires `status == "ok"` and
  `service == "MiroFish Backend"`; `mirofish_cli` defaults to `http://localhost:5001` and exits 1 on failure.

## What the result contains

Only numeric activity fields reported by MiroFish (current and total rounds, progress, simulated hours, and
Twitter, Reddit and total action counts) are copied into `metrics`. The summary and limitations state that
these do not establish churn reduction, retention lift or revenue impact. **No business KPI is invented.**

## Known limits

- The client contract reflects the MiroFish endpoints coded in `mirofish_client.py`; the repository does not
  pin or test against a MiroFish version, and unit tests use mocked transports.
- `httpx` is declared only in the `dev` extra and `pyyaml` only in the `docs` extra
  ({doc}`../getting-started/installation`).
- Keep remote execution disabled until a dedicated, verified telecom or churn project and its data have been
  prepared and reviewed.
