# Overview

Churn Handset Targeting answers one business question in the order a careful analyst would: *given a
limited retention budget, whom should an operator contact, what would the contact have to achieve to pay for
itself, and how can that be measured?*

The repository packages the analysis of a telecom data set (anonymised as "Company A"; supplied with the
GCI World 2026 final assignment) as tested, reusable software:

| Question | Implemented answer | Where |
|---|---|---|
| Who is at risk? | Gradient-boosting classifier ranks customers by churn risk | {doc}`../data-science/model-development` |
| Can the probabilities be used on a realistic population? | Platt calibration, then an odds shift to an assumed base rate | {doc}`../data-science/calibration` |
| What must a retention contact achieve to pay off? | Break-even incremental save rate | {doc}`../business-methodology/break-even-analysis` |
| How is the effect measured? | Two-arm randomised pilot sample-size calculation | {doc}`../business-methodology/pilot-design` |
| How is it served? | FastAPI service, command-line interface, optional Neo4j cohort layer | {doc}`../api/index`, {doc}`../graph-analytics/overview` |
| Can results be reproduced? | Scripted results export and a Manubot manuscript | {doc}`../scientific-reproducibility/manuscript-pipeline` |

## What the software does not do

- It does not estimate the causal effect of a retention offer. The classifier is trained on observational
  labels; the save rate used in the economics is an input, not an output.
- It does not ship data or trained models. `Client.csv` and `Record.csv` must be supplied locally and are
  git-ignored ({doc}`../data-science/data-provenance`).
- It does not claim production readiness. See {doc}`../scientific-reproducibility/limitations`.

## Reading order

1. {doc}`problem-statement` for the decision context.
2. {doc}`installation` and {doc}`quickstart` to run the pipeline on your own copy of the data.
3. {doc}`../architecture/system-architecture` for how the modules fit together.
4. {doc}`../data-science/evaluation` and {doc}`../scientific-reproducibility/model-card` before interpreting any number.
