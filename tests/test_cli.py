from churn_targeting.cli import main


def _write_inputs(customers, folder):
    folder.mkdir(parents=True, exist_ok=True)
    customers[["Customer_ID", "area", "crclscod", "ethnic", "hnd_price"]].to_csv(folder / "Client.csv", index=False)
    customers[["Customer_ID", "churn", "eqpdays", "months", "rev_Mean", "mou_Mean", "change_mou"]].to_csv(
        folder / "Record.csv", index=False)


def test_validate_command(customers, tmp_path):
    _write_inputs(customers, tmp_path / "raw")
    assert main(["validate", "--data-dir", str(tmp_path / "raw")]) == 0


def test_train_command_writes_model_and_metadata(customers, tmp_path):
    _write_inputs(customers, tmp_path / "raw")
    out = tmp_path / "models" / "m.joblib"
    assert main(["train", "--data-dir", str(tmp_path / "raw"), "--out", str(out)]) == 0
    assert out.exists() and out.with_suffix(".json").exists()
