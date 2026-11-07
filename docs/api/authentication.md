# Authentication

Authentication is a single optional shared secret implemented by the `require_key` dependency in
{repo}`src/churn_targeting/api/main.py`.

| Condition | Behaviour |
|---|---|
| `API_KEY` unset or empty | `require_key` does nothing; every route is open |
| `API_KEY` set, header absent or different | HTTP 401, `detail: "invalid or missing X-API-Key"` |
| `API_KEY` set, header equal | Request proceeds |

- The header is `X-API-Key`. The comparison uses `secrets.compare_digest` (constant time).
- `GET /health` is never protected, so container and orchestrator probes work.
- All other application routes are protected by `dependencies=[Depends(require_key)]`.

```bash
curl -H "X-API-Key: $API_KEY" http://127.0.0.1:8000/model
```

## What this is not

Reading the code shows the following are **not implemented**; do not assume them:

- Per-user identity, roles, key rotation or revocation (one shared key).
- Protection of the framework documentation routes `/docs`, `/redoc` and `/openapi.json`.
- Transport security: the service speaks plain HTTP; TLS must be terminated in front of it.
- Rate limiting, request-size limits beyond the 5,000-row batch cap, CORS configuration or audit logging.

Operational guidance is in {doc}`../deployment/security`. Never put a real key in source code, examples,
screenshots or committed environment files.
