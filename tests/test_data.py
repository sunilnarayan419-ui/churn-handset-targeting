import pandas as pd
import pytest

from churn_targeting.data import (
    DataValidationError,
    load_raw,
    merge_customers,
    quality_report,
)


def test_merge_is_one_to_one(client_record):
    client, record = client_record
    merged = merge_customers(client, record)
    assert len(merged) == len(record) == len(client)
    assert merged["Customer_ID"].is_unique
    assert {"churn", "area", "eqpdays"} <= set(merged.columns)


def test_duplicate_ids_rejected(client_record):
    client, record = client_record
    dup = pd.concat([record, record.iloc[[0]]])
    with pytest.raises(DataValidationError, match="duplicate"):
        merge_customers(client, dup)


def test_unmatched_ids_rejected(client_record):
    client, record = client_record
    with pytest.raises(DataValidationError, match="differ"):
        merge_customers(client.iloc[:-5], record)


def test_missing_ids_rejected(client_record):
    client, record = client_record
    bad = client.copy()
    bad.loc[bad.index[0], "Customer_ID"] = None
    with pytest.raises(DataValidationError, match="missing"):
        merge_customers(bad, record)


def test_missing_target_rejected(client_record):
    client, record = client_record
    with pytest.raises(DataValidationError, match="churn"):
        merge_customers(client, record.drop(columns="churn"))


def test_load_raw_reports_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="Client.csv"):
        load_raw(tmp_path)


def test_quality_report(customers):
    rep = quality_report(customers)
    assert rep.rows == len(customers)
    assert rep.columns_with_missing == 1
    assert "rev_Mean" in rep.top_missing_pct
    assert 0 < rep.churn_rate < 1
