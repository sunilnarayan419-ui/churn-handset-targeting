# Environment setup

Runtime settings are read from **environment variables** by
{py:class}`churn_targeting.config.Settings` (`Settings.from_env()`), and by
`churn_targeting.simulation.config.SimulationSettings` for the optional simulation service. The template
{repo}`.env.example` documents the names; the application **does not parse `.env` files itself**. Export the
variables in your shell, or use a tool that loads `.env` (Docker Compose reads `.env` for variable
substitution).

## Variables

| Variable | Default | Used by | Meaning |
|---|---|---|---|
| `DATA_DIR` | `data/raw` | CLI (`validate`, `train`, `graph-load`) | Directory holding `Client.csv` and `Record.csv` |
| `MODEL_PATH` | `models/churn_model.joblib` | CLI `train` output, API startup | Model bundle path; a JSON sidecar is written next to it |
| `BASE_RATE` | `0.0099` | API `/score` default | Assumed monthly churn rate for the base-rate shift |
| `API_KEY` | unset | API | If non-empty, `X-API-Key` is required on every route except `/health` |
| `NEO4J_URI` | unset | API startup, CLI `graph-load` | Enables the Neo4j store, e.g. `bolt://localhost:7687` |
| `NEO4J_USER` | `neo4j` | same | Database user |
| `NEO4J_PASSWORD` | unset | same | Database password (secret) |
| `NEO4J_DATABASE` | `neo4j` | same | Database name |
| `MIROFISH_BASE_URL` | empty | simulation CLIs | Base URL of an optional MiroFish backend; must start with `http://` or `https://` |
| `MIROFISH_TIMEOUT_SECONDS` | `30` (`5` for the health CLI) | simulation CLIs | HTTP timeout, must be positive |
| `MIROFISH_MAX_SCENARIO_BYTES` | `100000` | `SimulationSettings` | Validated to be positive |

```{note}
`.env.example` places `#` comments after some values (for example `BASE_RATE=0.0099   # ...`). Loaders differ
in how they treat inline comments; if a value fails to parse, move the comment to its own line.
```

## Behaviour worth knowing

- `main()` in `cli.py` calls `Settings.from_env()` before parsing arguments, so a malformed `BASE_RATE`
  (not a float) raises `ValueError` for every CLI command.
- `BASE_RATE` is not range-checked when read. `POST /score` validates a `base_rate` *query parameter* to lie
  strictly between 0 and 1, but a misconfigured default would only fail when the probability shift is
  computed (`ValueError: base rates must be strictly between 0 and 1`).
- `DEFAULT_BASE_RATE = 0.0099` is documented in the source as an assumption, "not Company A's measured rate".
- The API only connects to Neo4j when `NEO4J_URI` is set. `NEO4J_PASSWORD` is mandatory for
  `churn-targeting graph-load` (the command exits with a message if either is missing).

## Secrets

Never commit `.env`, API keys or database passwords. `.gitignore` excludes `.env`, `data/raw/*` and
`models/*`. See {doc}`../deployment/security`.
