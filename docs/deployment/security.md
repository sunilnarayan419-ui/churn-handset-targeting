# Security

This page lists controls present in the code and gaps that a deployer must close. It is not a security
audit.

## Present in the code

- Optional shared-secret authentication with constant-time comparison ({doc}`../api/authentication`).
- Strict input schemas with bounds; batch size capped at 5,000 rows.
- Cypher data passed as parameters; labels and relationship types only from a hard-coded whitelist
  ({doc}`../graph-analytics/neo4j-integration`).
- Non-root container user; secrets via environment variables; `.env`, `data/raw/*` and `models/*` git-ignored.
- MiroFish client: HTTP(S) only, no credentials in URL, no redirects; remote execution behind explicit flags
  and a read-only preflight ({doc}`../simulation/mirofish-integration`).
- Failure messages from the simulation runner expose only the exception type.

## Gaps and risks

| Risk | Detail |
|---|---|
| Open docs and schema | `/docs`, `/redoc` and `/openapi.json` are not protected by the key |
| No TLS | Terminate TLS in front of the service; the key is sent in a header |
| Single shared key | No rotation, per-client keys, rate limiting or audit log |
| Pickle model files | `joblib.load` executes code from the file. Load only bundles you produced; never accept uploaded models |
| Personal data | Scored customer lists and raw data are personal data; do not commit or share them; document lawful basis, consent and opt-out |
| Dependency drift | Dependabot is configured; no lockfile is committed, so builds resolve fresh versions |
| Neo4j exposure | Compose publishes 7474 and 7687; restrict network access and use a strong password |
| Model misuse | Do not use scores for credit, eligibility, pricing discrimination or denial of service |

## Hygiene checklist

Review staged files before every commit; ensure no `.env`, credentials, raw CSVs, customer-level predictions
or unnecessary model binaries are included ({doc}`../development/development-workflow`).
