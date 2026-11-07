# Limitations and responsible use

This page consolidates limitations stated across the repository and clarifies what is implemented, assumed or
only proposed.

## Scientific limitations

1. **Association, not causation.** The model learns from observational labels. It cannot say whether contact
   prevents churn. The incremental save rate is an input; only a randomised pilot estimates it, and none has
   been run.
2. **Enriched sample and assumed base rate.** The sample churns at 49.6 % versus an assumed ~1 % monthly rate.
   The shift to 1 % is an assumption anchored on carrier disclosures, not a measured Company A rate, and rests
   on a prior-shift assumption ({doc}`../data-science/calibration`).
3. **No temporal validation.** There are no timestamps, so generalisation over time is untested and column
   timing (leakage) cannot be proven.
4. **Moderate discrimination.** Test ROC-AUC 0.693; performance varies by tenure (0.650-0.749) and area
   (0.640-0.734).
5. **Single split, single data set.** Reported intervals reflect test-set sampling variation only.
6. **Economics are conditional.** Margin, months credited, costs, acceptance and fixed cost are assumptions;
   annualisation ignores repeat contact. Break-even and ROI are scenario arithmetic, not forecasts
   ({doc}`../business-methodology/break-even-analysis`).
7. **Pilot sizing is approximate.** Normal approximation, independent customers, no attrition or interim
   analysis ({doc}`../business-methodology/pilot-design`).
8. **Simulation outputs are not evidence.** Scenario comparisons use illustrative assumptions and MiroFish
   activity is simulated behaviour; the two simulation economics definitions differ from `finance.py`
   ({doc}`../simulation/evaluation`).
9. **Currency assumed to be USD.**

## Fairness and responsible use

`ethnic` is excluded, but income, marital status and other fields may act as proxies; no subgroup fairness audit
is implemented. Do not use scores for credit, eligibility, pricing discrimination, denial of service or other
consequential individual decisions. Contact needs consent, opt-out handling and a lawful basis.

## Implemented versus proposed

| Implemented | Proposed or not available |
|---|---|
| Validation, training, calibration, scoring, targeting statistics, economics, pilot sizing, API, optional Neo4j, scenario comparison | A randomised pilot, uplift modelling, temporal validation, fairness audit, monitoring, hot model reload |
| MiroFish client and gated adapter (experimental) | A verified end-to-end MiroFish run; any causal simulation result |

## Engineering limitations

Dependencies for the command-line interface are spread across extras ({doc}`../getting-started/installation`);
no lockfile is committed; `/cohorts/{dimension}` returns 503 in the default app without Neo4j; no
monitoring, logging, TLS or rate limiting ({doc}`../deployment/security`).
