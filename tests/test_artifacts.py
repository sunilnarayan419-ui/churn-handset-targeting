"""Guards the committed result files: the packaged code and the notebook must agree."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS, NOTEBOOK = ROOT / "reports/results.json", ROOT / "reports/notebook_results.json"

pytestmark = pytest.mark.skipif(not (RESULTS.exists() and NOTEBOOK.exists()), reason="reports not present")


def _load():
    return json.loads(RESULTS.read_text()), json.loads(NOTEBOOK.read_text())


def test_model_scores_match_notebook():
    pkg, nb = _load()
    m = nb["models"]["Gradient boosting"]
    assert pkg["model"]["metrics_test"]["roc_auc"] == pytest.approx(m["Test ROC-AUC"], abs=1e-3)
    assert pkg["model"]["metrics_test"]["accuracy"] == pytest.approx(m["Accuracy"], abs=1e-3)


def test_break_even_and_pilot_sizes_match_notebook():
    pkg, nb = _load()
    unit = {u["Contacted share"]: u for u in nb["finance"]["unit_economics"]}["top 5%"]
    assert pkg["finance"]["unit_economics"]["top5"]["breakeven_nudge"] == pytest.approx(
        unit["Break-even save rate, Arm A nudge ($0.75)"], abs=1e-3)
    pilot = {p["Contacted slice"]: p for p in nb["finance"]["pilot_sizing"]}["top 5%"]
    assert pkg["finance"]["pilot_sizing"]["top5"]["n_20"] == pilot["n per arm for 20% effect"]


def test_scenario_net_benefits_match_notebook():
    pkg, nb = _load()
    for s in nb["finance"]["scenarios"]:
        key = f"top{s['Contacted'].split('%')[0].split()[-1]}_{s['Scenario'].lower()}"
        assert pkg["finance"]["scenarios"][key]["net_benefit"] == pytest.approx(s["Net benefit / yr ($)"], abs=1.0)
