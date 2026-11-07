# Problem statement

## Decision context

A telecom operator (anonymised as *Company A*) wants to reduce customer churn by targeting customers whose
handsets are ageing. Retention contact is cheap per customer but not free, and the operator can only contact a
limited number of customers per campaign wave. Two things must therefore be decided:

1. **Ranking.** Which customers should be contacted first?
2. **Worth.** What share of would-be churners must a contact retain for the campaign to pay for itself?

## Prediction target

The binary label `churn` equals 1 when the customer left 31 to 60 days after the observation date
({doc}`../data-science/data-provenance`). The task is binary classification with a risk score as output.

## Why the problem is not just "train a classifier"

Three separate questions are easy to conflate; this project keeps them apart.

| Question | Quantity | Answered by | Evidence in this repository |
|---|---|---|---|
| Can customers be ranked by risk? | Discrimination (ROC-AUC, PR-AUC, lift) | The model | Reported hold-out metrics ({doc}`../data-science/evaluation`) |
| Are the predicted probabilities numerically right? | Calibration | Platt scaling, base-rate shift | Brier score; base rate is an assumption ({doc}`../data-science/calibration`) |
| Does contact *cause* customers to stay? | Incremental (causal) effect | A randomised pilot | **None.** Sample size is computed; no pilot was run ({doc}`../business-methodology/pilot-design`) |

The assignment sample is enriched with churners (about 49.6 % positive) while the business scenario assumes a
monthly churn rate of about 1 %. Rank quality and relative lift transfer to a realistic population; raw
precision, accuracy and counts do not. The base-rate shift in {doc}`../data-science/calibration` addresses the
probability scale, but the 1 % figure is an assumption anchored on published carrier disclosures, not a
measured Company A rate.

## Scope of the stated recommendation

The repository's manuscript and README recommend using the model to design a capped, randomised retention
experiment with a stop rule, not to justify an immediate roll-out. This documentation preserves that framing.
