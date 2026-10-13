# Data card

| Item | Detail |
|---|---|
| Source | Supplied with the GCI World 2026 final assignment (anonymised operator "Company A"); not redistributed |
| Files | `Client.csv` (100,000 x 50), `Record.csv` (100,000 x 51); join key `Customer_ID` (unique, non-null, 1:1) |
| Target | `churn`: 1 = left 31-60 days after the observation date (49.6% positive) |
| Missing data | 43 of 100 columns; up to 49.4% (`numbcars`); household-demographic fields most affected |
| Excluded from models | `Customer_ID`; `ethnic` (protected characteristic) |
| Known gaps | No timestamps; currency not stated (USD assumed); regions anonymised and US-style; sample enriched with churners |

**Handling.** Keep raw files in `data/raw/` (git-ignored). Do not commit extracts, trained models or scored customer lists. Contacting customers on the basis of a score needs consent, opt-out handling and a documented lawful basis.
