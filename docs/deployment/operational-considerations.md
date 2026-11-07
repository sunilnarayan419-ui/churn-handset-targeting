# Operational considerations

The repository provides a service and an analysis pipeline; it does not provide a production operations
setup. This page lists what exists and what a deployment would still need.

## Lifecycle

1. Train on authorised data, verify the two artefacts, and keep the metadata JSON with the bundle.
2. Start (or restart) the API; confirm `/health` shows `model_loaded: true`, then `/model`.
3. Retrain and restart on a schedule you define; the service does not reload models.

## Health and readiness

`/health` is liveness-oriented: it reports whether a bundle object exists and whether a graph store object
exists, but does not exercise scoring or the database. The container health check only fetches `/health`.

## Monitoring (recommended, not implemented)

The model card recommends monthly tracking of ROC-AUC and calibration by tenure group, retraining on drift and
recalibration on the operator's real base rate. The repository contains no monitoring code, metrics endpoint,
structured logging or alerting.

## Performance

No latency or throughput measurements exist in the repository. Batch scoring builds one DataFrame per request
(at most 5,000 rows). Training a 100,000-row data set is described as feasible on one CPU core; the results
export takes about 1-2 minutes per its docstring.

## Rollback and change control

Keep previous bundles and their metadata. Any change of data, scikit-learn version or base-rate assumption can
change outputs. Define retraining triggers, a stop rule for the pilot and a rollback plan before any
operational use ({doc}`../scientific-reproducibility/limitations`).
