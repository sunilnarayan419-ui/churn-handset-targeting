# Data validation

Validation is implemented in {repo}`src/churn_targeting/data.py` and exposed through
`churn-targeting validate`. Failures raise `DataValidationError` (a `ValueError`) or `FileNotFoundError`; they
are not logged or repaired.

## Checks performed

| Step | Function | Rule |
|---|---|---|
| Files exist | `load_raw` | Both `Client.csv` and `Record.csv` must exist in the data directory, otherwise `FileNotFoundError` naming the missing paths |
| Key present | `validate_keys` | `Customer_ID` is a column of both tables |
| Key complete | `validate_keys` | No missing `Customer_ID` values in either table |
| Key unique | `validate_keys` | No duplicated `Customer_ID` in either table |
| Same population | `validate_keys` | The two ID sets are identical; otherwise the error reports how many IDs are only in one table |
| Target present | `validate_keys` | `churn` is a column of the record table |
| One-to-one merge | `merge_customers` | `record.merge(client, on="Customer_ID", how="inner", validate="one_to_one")` |
| No row change | `merge_customers` | The merged row count equals the record table's row count |

The merge is an inner join on a validated key, so row multiplication or silent loss would be rejected.
Tests in `tests/test_data.py` cover duplicate IDs, unmatched IDs, missing IDs, a missing target, missing files
and the quality report (synthetic data).

## Quality report

`quality_report(df, top=5)` returns a `QualityReport` with the row and column counts, the mean of `churn`,
the number of columns with missing values and the top columns by percentage missing (rounded to one decimal).
`churn-targeting validate` prints it as JSON.

## What is not validated

Reading the source shows several things that are **not** checked, so they must be reviewed manually:

- Value ranges and plausibility of any feature (for example negative handset age).
- That `churn` takes only the values 0 and 1. `select_features` casts it with `.astype(int)`, which would fail
  on missing values; other numeric values would pass silently.
- Column dtypes and the presence of any column other than `Customer_ID` and `churn`. Scoring tolerates
  missing columns by design ({doc}`feature-engineering`).
- Temporal consistency, because no timestamps exist ({doc}`data-provenance`).

The training guide's phrase "target is missing/invalid" should therefore be read as "target column missing".
