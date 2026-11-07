# Retention economics

Every input of the economics is an explicit argument; nothing is hidden in the code
({repo}`src/churn_targeting/finance.py`). Assumed values are labelled as assumptions, never measurements.

## Definitions (per monthly campaign wave)

| Symbol | Code name | Meaning | Unit |
|---|---|---|---|
| $N$ | `n_treated` | Customers contacted | customers |
| $p$ | `churn_prob` | Real-world monthly churn probability of the contacted group | probability |
| $s$ | `save_rate` | **Incremental** share of would-be churners the contact retains | probability |
| $r$ | `avg_monthly_rev` | Average monthly revenue per customer | currency/month |
| $m$ | `margin` | Contribution margin | fraction |
| $T$ | `months` | Months of margin credited to a save | months |
| $c$ | `contact_cost` | Cost of one contact | currency |
| $a$ | `accept_rate` | Share of contacted customers who accept the incentive | probability |
| $I$ | `incentive` | Incentive paid per acceptor | currency |

## Equations

$$
C = Np,\qquad S = C\,s,\qquad V = r\,m\,T
$$

$$
\text{gross benefit}=S\,V,\qquad
\text{variable cost}=N\,(c+aI),\qquad
\text{net variable benefit}=SV-N(c+aI)
$$

`cost_per_contact(c, a, I)` $=c+aI$ and `value_per_save(r, m, T)` $=rmT$. The break-even save rate is derived
in {doc}`break-even-analysis`.

## Input validation and boundaries

`economics()` raises `ValueError` unless `churn_prob`, `save_rate`, `margin` and `accept_rate` lie in $[0,1]$,
`n_treated`, `avg_monthly_rev`, `contact_cost` and `incentive` are non-negative, and `months > 0`. The API
tightens some bounds (`n_treated > 0`, `0 < churn_prob < 1`) ({doc}`../api/schemas`). If $pV\le 0$ the
break-even is `inf` (JSON `null`).

## Annualisation

`annualize(wave, fixed_cost, waves=12, book=None)` multiplies gross benefit and variable cost by the number of
waves and subtracts a fixed programme cost $F$:

$$
\text{net}=12\,(SV-\text{var. cost})-F,\qquad
\text{ROI}=100\cdot\frac{\text{net}}{12\cdot\text{var. cost}+F}\ \%
$$

ROI is `nan` if total cost is zero. If `book` is given and the annual variable net benefit $B>0$, it adds
`breakeven_book_size` $=F/(B/\text{book})$, the book size at which the fixed cost is covered. The docstring
states the simplification: it ignores repeat contact with the same customer.

## Assumptions object

`finance.Assumptions` stores the labelled defaults used for the reported results:

| Field | Default | Note |
|---|---:|---|
| `base_rate` | 0.0099 | Assumed monthly churn; not Company A's measured rate |
| `margin` | 0.40 | Assumption |
| `months` | 12 | Months credited per save |
| `contact_cost` | 0.75 | Per contact |
| `accept_rate` | 0.15 | Share accepting the incentive |
| `incentive` | 20.0 | Per acceptor |
| `fixed_cost_per_year` | 60,000 | Programme cost |
| `book` | 100,000 | Subscriber book used for scaling |

The currency is assumed to be US dollars ({doc}`../data-science/data-provenance`). These values must be
replaced by the operator's own figures before any decision.

## Sensitivity analysis

`sensitivity_grid(churn_prob, avg_monthly_rev, n_treated, margin, months, save_rates, contact_costs)` returns
the net variable benefit per wave for every (contact cost, save rate) pair; rows are contact costs and columns
are save rates. It is monotone increasing in $s$ and decreasing in $c$ (checked in `tests/test_finance.py`).

```{figure} ../../content/images/fig_sensitivity.png
:width: 70%
:alt: Net variable benefit per wave for the top 5 percent slice by save rate and contact cost.

Net variable benefit per wave (US dollars) for the top-5 % slice, by incremental save rate and cost per
contact (manuscript Figure 3).
```

```{warning}
The save rate $s$ is an *input*. The churn model cannot estimate it; only a randomised pilot can
({doc}`pilot-design`).
```
