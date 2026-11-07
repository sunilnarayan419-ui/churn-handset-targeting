# Customer targeting

Targeting turns a risk ranking into a contact list under a capacity limit. The logic is in
{repo}`src/churn_targeting/targeting.py` and {repo}`src/churn_targeting/bands.py`.

## Ranking and top-k selection

`top_fraction_stats(y_true, score, frac, pi_real)` sorts customers by descending score (stable sort), contacts
the top $k=\max(1,\lfloor \text{frac}\cdot n\rfloor)$ and reports:

| Key | Definition |
|---|---|
| `contacted` | $k$ |
| `churn_rate_in_file` | share of the $k$ who churned in the sample |
| `recall` | TPR = churners in the slice / all churners |
| `false_positive_rate` | FPR = stayers in the slice / all stayers |
| `lift_in_file` | `churn_rate_in_file` divided by the sample churn rate |
| `precision_at_base_rate` | Bayes-adjusted precision at base rate $\pi$ (below) |
| `lift_at_base_rate` | `precision_at_base_rate` / $\pi$ |

$$
\text{precision}_\pi=\frac{\mathrm{TPR}\,\pi}{\mathrm{TPR}\,\pi+\mathrm{FPR}\,(1-\pi)}
$$

`realworld_precision` returns `nan` when the denominator is not positive. The adjustment answers "what share of
contacted customers would really churn at base rate $\pi$", and is only as valid as $\pi$
({doc}`../data-science/calibration`).

`decile_table(y_true, score)` ranks customers, assigns decile $=\min(\lfloor 10i/n\rfloor,9)+1$ and returns
customers, churn rate, lift versus average and cumulative recall per decile.

## Rule-based comparison

`mask_stats(y_true, mask, pi_real)` evaluates any boolean selection with the same metrics. The repository uses
it for a simple rule, handset age of 301-400 days (`bands.past_300_days`), as a baseline for the model
({doc}`../data-science/evaluation` reports both).

## Segmentation

`bands.py` is the single definition of cohorts, shared by pandas analytics and Neo4j. Intervals are right-closed
(`pandas.cut`); values outside the edges become missing and are dropped from tables.

| Dimension | Source column | Bands |
|---|---|---|
| `handset_age` | `eqpdays` | ≤100, 101-150, 151-200, 201-250, 251-300, 301-350, 351-400, 401-500, 501-700, >700 |
| `tenure` | `months` | ≤12, 13-24, >24 months (edges 0, 12, 24, 100) |
| `price_tier` | `hnd_price` | ≤$30, $30-100, $100-150, >$150 (edges 0, 30, 100, 150, 1000) |
| `area` | `area` | raw labels, no banding |
| `credit_class` | `crclscod` | raw labels, no banding |

Bands are for exploration and cohort reporting; they are not model inputs ({doc}`../data-science/feature-engineering`).

## Operational interpretation

- The list size is a business constraint (budget, call capacity), not something the model chooses.
- A high rank means "high predicted churn probability", not "will respond to an offer". Some high-risk
  customers cannot be saved and some low-risk customers might be; ranking by risk is not ranking by uplift.
- Excluding `ethnic` does not make a list fair; proxies remain.
- Scores must not drive credit, eligibility, pricing discrimination or denial of service.

## Limitations of predictive targeting

Predictive targeting optimises *who will leave*, whereas the decision needs *whose departure contact will
prevent*. Estimating the latter needs experimental data ({doc}`pilot-design`); uplift modelling (Radcliffe,
2007) is the established approach once such data exist, and is not implemented here.
