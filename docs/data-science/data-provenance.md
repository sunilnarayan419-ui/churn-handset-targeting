# Data provenance

```{admonition} Data are not distributed
`Client.csv` and `Record.csv` were supplied with a university assignment, are not redistributable and are
excluded from version control (`data/raw/*` is git-ignored; only `data/raw/.gitkeep` and `data/README.md` are
committed). The MIT license of the code does not grant rights to the data.
```

## Source and description

| Item | Detail |
|---|---|
| Origin | Supplied with the GCI World 2026 final assignment for an anonymised operator, "Company A" |
| Files | `Client.csv` (100,000 rows × 50 columns), `Record.csv` (100,000 rows × 51 columns) |
| Join key | `Customer_ID`: present, non-null and unique in both files; the two ID sets are identical |
| Merged table | 100,000 rows and 100 columns (the key is shared); 97 model features remain after exclusions |
| Content | `Client.csv`: account and equipment characteristics. `Record.csv`: usage, billing and call-quality fields and the churn label |
| Target | `churn` = 1 if the customer left 31 to 60 days after the observation date; 49.6 % positive in the file |
| Missing data | 43 of 100 columns contain missing values, concentrated in household demographics; the maximum is 49.4 % (`numbcars`) |
| Excluded from models | `Customer_ID` and `ethnic` (a protected characteristic) |
| Timestamps | None; time-based validation is therefore impossible |
| Currency | Not stated; US dollars are assumed (consistent with handset prices and US-style regional labels). This is an assumption, not a finding |
| Regions | Anonymised, US-style labels (19 areas appear in the subgroup analysis) |

Sources of these facts: the existing data card, the manuscript data section and `reports/results.json`
(`n_customers`, `sample_churn_rate`, `eda.columns_with_missing`, `eda.max_missing_pct`).

## Sample enrichment

The file is enriched with churners (49.6 % positive), whereas the business scenario assumes a monthly churn
rate of about 1 %. Rankings and relative lift are expected to transfer to a realistic population; raw
precision, accuracy and counts do not. The probability scale is corrected, under stated assumptions, in
{doc}`calibration`.

## Handling rules

- Keep the raw files in `data/raw/` only. Do not commit extracts, trained models or scored customer lists.
- Contacting customers on the basis of a score needs consent, opt-out handling and a documented lawful basis;
  this repository does not implement or verify any of these.
- Reported results in `reports/` cannot be regenerated without the original files.

## Known gaps

No timestamps, no statement of currency, no data dictionary in the repository that proves every column was
recorded before the outcome window, and an unknown sampling procedure for the enrichment. These limit leakage
checks and any claim about production performance ({doc}`../scientific-reproducibility/limitations`).
