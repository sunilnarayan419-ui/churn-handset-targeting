# Break-even analysis

## Derivation

A wave pays for its variable cost when $N p\,s\,V \ge N(c+aI)$. Solving for the incremental save rate gives

$$
s^{*}=\frac{c+aI}{p\,V}=\frac{c+aI}{p\,r\,m\,T}
$$

implemented by `finance.breakeven_save_rate`. It is the share of would-be churners a contact must retain for the
wave to break even. It is independent of $N$. For $pV\le 0$ the function returns `inf`.

Hand-checkable example (also the API example): $p=0.05$, $r=50$, $m=0.40$, $T=12$, $c=0.50$, $a=I=0$ gives
$V=240$ and $s^*=0.50/(0.05\cdot 240)\approx 0.0417$.

## Reported break-even rates

From `reports/results.json` (`finance.unit_economics`), with the default `Assumptions`. $p$ and $r$ are the
average base-rate-adjusted churn probability and revenue of each model-ranked slice of the test set.

| Slice | $p$ | Value per save | Break-even, $0.75 contact | Break-even, contact plus 15 % × $20 incentive |
|---|---:|---:|---:|---:|
| Top 5 % | 5.2 % | $223.87 | 6.4 % | 32.0 % |
| Top 10 % | 4.0 % | $251.88 | 7.4 % | 37.1 % |
| Top 20 % | 3.0 % | $265.31 | 9.3 % | 46.5 % |

Broader slices have lower average risk and so need a higher save rate. The "$20 credit" case in the README
means a $0.75 contact plus an incentive of $20 accepted by 15 % of contacts (expected $3.75 per contact).

## Annual scenarios

`annualize` applied to 12 waves, a 100,000-customer book and $60,000 fixed cost. Scenario inputs are set in
`scripts/export_results.py`:

| Scenario | Base rate | Save rate | Margin | Months | Contact cost |
|---|---:|---:|---:|---:|---:|
| Conservative | 0.86 % | 3 % | 0.30 | 6 | $1.00 |
| Base | 0.99 % | 6 % | 0.40 | 12 | $0.75 |
| Upside | 1.04 % | 10 % | 0.50 | 12 | $0.50 |

| Slice and scenario | Gross benefit | Variable cost | Net benefit | ROI |
|---|---:|---:|---:|---:|
| Top 5 %, conservative | $6,931 | $60,000 | -$113,069 | -94 % |
| Top 5 %, base | $42,246 | $45,000 | -$62,754 | -60 % |
| Top 5 %, upside | $92,203 | $30,000 | $2,203 | 2.4 % |
| Top 10 %, conservative | $11,919 | $120,000 | -$168,081 | -93 % |
| Top 10 %, base | $72,770 | $90,000 | -$77,230 | -51 % |
| Top 10 %, upside | $158,925 | $60,000 | $38,925 | 32 % |

Only the upside scenarios are net positive, and they depend on a 10 % incremental save rate that has not been
measured. The fixed cost dominates the base case. These are conditional calculations, not forecasts.

## Boundary conditions and caveats

- A $0 revenue or $0 margin gives zero value per save and an undefined (infinite) break-even.
- $p$ depends on the assumed base rate; changing $\pi$ changes every break-even.
- Churn probability is a model estimate on an enriched sample shifted to an assumed rate.
- `annualize` ignores repeated contact, discounting and saved customers churning later.

The simulation package uses a *different*, simpler per-target definition; see
{doc}`../simulation/evaluation` before comparing the two.
