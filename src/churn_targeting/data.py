"""Loading, key validation and merging of the two customer tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ID = "Customer_ID"
TARGET = "churn"


class DataValidationError(ValueError):
    """Raised when the input tables violate the expected structure."""


def load_raw(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read Client.csv and Record.csv from ``data_dir``."""
    d = Path(data_dir)
    paths = {"client": d / "Client.csv", "record": d / "Record.csv"}
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing input file(s): {missing}. Place Client.csv and Record.csv in {d} (see data/README.md)."
        )
    return pd.read_csv(paths["client"]), pd.read_csv(paths["record"])


def validate_keys(client: pd.DataFrame, record: pd.DataFrame) -> None:
    """Fail loudly unless Customer_ID is present, non-null, unique and identical in both tables."""
    for name, table in (("client", client), ("record", record)):
        if ID not in table.columns:
            raise DataValidationError(f"{name} table has no {ID} column")
        if table[ID].isna().any():
            raise DataValidationError(f"{name} table has missing {ID} values")
        if table[ID].duplicated().any():
            raise DataValidationError(f"{name} table has duplicate {ID} values")
    only_client = set(client[ID]) - set(record[ID])
    only_record = set(record[ID]) - set(client[ID])
    if only_client or only_record:
        raise DataValidationError(
            f"{ID} sets differ: {len(only_client)} only in client, {len(only_record)} only in record"
        )
    if TARGET not in record.columns:
        raise DataValidationError(f"record table has no {TARGET} column")


def merge_customers(client: pd.DataFrame, record: pd.DataFrame) -> pd.DataFrame:
    """Validated one-to-one merge (one row per customer, no row multiplication)."""
    validate_keys(client, record)
    merged = record.merge(client, on=ID, how="inner", validate="one_to_one")
    if len(merged) != len(record):
        raise DataValidationError("merge changed the row count")
    return merged


def load_customers(data_dir: str | Path) -> pd.DataFrame:
    return merge_customers(*load_raw(data_dir))


@dataclass(frozen=True)
class QualityReport:
    rows: int
    columns: int
    churn_rate: float
    columns_with_missing: int
    top_missing_pct: dict[str, float]


def quality_report(df: pd.DataFrame, top: int = 5) -> QualityReport:
    miss = (df.isna().mean() * 100).sort_values(ascending=False)
    miss = miss[miss > 0]
    return QualityReport(
        rows=len(df),
        columns=df.shape[1],
        churn_rate=float(df[TARGET].mean()),
        columns_with_missing=int(len(miss)),
        top_missing_pct={k: round(float(v), 1) for k, v in miss.head(top).items()},
    )
