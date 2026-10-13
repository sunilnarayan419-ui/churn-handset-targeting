# Changelog

## Unreleased
- Expanded the README with setup paths for Windows PowerShell and Unix-like shells, endpoint examples, testing gates, repository structure, data-safety policy and responsible-use limitations.
- Added detailed repository/module mapping, API reference, training/evaluation guide, test guide and development/troubleshooting workflow.
- Added PowerShell training preflight/artifact verification and live API smoke-test scripts.
- Documented the distinction between a live API process, a loaded model artifact and optional Neo4j availability.

## 0.1.0
- Packaged the assignment analysis: data validation, calibrated gradient-boosting model, base-rate-adjusted targeting, break-even economics, pilot sizing.
- FastAPI service, optional Neo4j cohort layer (parity-tested against pandas), pytest suite, GitHub Actions, Docker, Manubot manuscript.
- Fix found by tests: scoring requests with all categorical fields missing no longer fail.
