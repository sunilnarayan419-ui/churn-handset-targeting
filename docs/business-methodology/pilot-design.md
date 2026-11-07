# Pilot design

The model ranks customers; only an experiment can show whether contact retains them. The package computes the
sample size for a two-arm randomised hold-out pilot ({repo}`src/churn_targeting/pilot.py`). **No pilot has been
run**; this page documents the calculation and the design assumptions it needs.

## Design

- Two arms of equal size: *treatment* (contact) and *control* (no contact, the hold-out).
- Eligible customers are randomised, ideally within the model-ranked slice that would be contacted.
- Outcome: churn within the same window as the label; compare churn proportions between arms.
- Test: two-sided comparison of two proportions at significance level $\alpha$ with power $1-\beta$.

## Sample size

With baseline churn probability $p_0$ and relative effect $r$ (the share of would-be churners the offer keeps,
i.e. the save rate), $p_1=p_0(1-r)$ and $\bar p=(p_0+p_1)/2$, `n_per_arm` returns

$$
n=\left\lceil\frac{\left(z_{1-\alpha/2}\sqrt{2\bar p(1-\bar p)}+z_{1-\beta}\sqrt{p_0(1-p_0)+p_1(1-p_1)}\right)^{2}}{(p_0-p_1)^{2}}\right\rceil
$$

per arm, where $z$ are standard normal quantiles (`statistics.NormalDist`). Total sample $=2n$. This is the
standard normal-approximation formula for two independent proportions (Fleiss et al., 2003; see
{doc}`../scientific-reproducibility/references`).

| Parameter | Code | Constraint | Default |
|---|---|---|---|
| Baseline churn $p_0$ | `baseline_churn_prob` | $0<p_0<1$ | required |
| Relative effect $r$ | `relative_effect` | $0<r<1$ | required |
| Significance $\alpha$ | `alpha` | | 0.05 |
| Power $1-\beta$ | `power` | | 0.80 |

Out-of-range inputs raise `ValueError`. The API route `POST /pilot/size` wraps it and returns `n_per_arm` and
`total_customers`.

## Reported sizes

From `reports/results.json` (`finance.pilot_sizing`): $p_0$ is the average base-rate-adjusted churn
probability of the slice, $\alpha=0.05$, power 0.80.

| Slice | $r=10\%$ | $r=20\%$ | $r=30\%$ |
|---|---:|---:|---:|
| Top 5 % | 27,033 | 6,420 | 2,702 |
| Top 10 % | 35,748 | 8,484 | 3,568 |
| Top 20 % | 47,607 | 11,293 | 4,747 |

These are customers **per arm**. Rarer events and smaller effects need many more customers. For
$p_0=0.10$, $r=0.20$ the unit tests expect between 3,100 and 3,300 per arm.

## Assumptions and limitations of the sizing

- Normal approximation; very small $p_0$ or very small $n$ may need exact methods.
- Customers are independent and individually randomised; clustering, households or repeat contact are not
  modelled.
- No allowance for attrition, non-compliance, multiple outcomes or interim looks (the README mentions a stop
  rule, which is not implemented in code).
- The effect size is a planning assumption. Sizing for a smaller true effect needs a larger pilot.
- The final design must define the outcome window, randomisation unit, eligibility, operational constraints
  and analysis plan in advance.
