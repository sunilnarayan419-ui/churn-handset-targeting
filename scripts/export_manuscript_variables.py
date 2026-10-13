"""Format reports/results.json (+ the notebook's model comparison) into template variables for Manubot.

    python scripts/export_manuscript_variables.py   # writes build/variables.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def build(results: dict, notebook: dict) -> dict:
    e, m, t, f = results["eda"], results["model"]["metrics_test"], results["targeting"], results["finance"]
    strata = e["tenure_strata"]
    rng = lambda r: f"{pct(r[0])} to {pct(r[1])}"  # noqa: E731
    models = {}
    for key, name in (("dummy", "Dummy (prior)"), ("logistic", "Logistic regression"),
                      ("forest", "Random forest"), ("boosting", "Gradient boosting")):
        r = notebook["models"][name]
        models[key] = {"cv_auc": f"{r['CV ROC-AUC']:.3f}", "test_auc": f"{r['Test ROC-AUC']:.3f}",
                       "pr_auc": f"{r['Test PR-AUC']:.3f}", "accuracy": f"{r['Accuracy']:.3f}"}
    dec = {d["decile"]: d for d in results["deciles"]}
    tg = {k: {"file_churn": pct(v["churn_rate_in_file"]), "recall": pct(v["recall"], 0),
              "prec": pct(v["precision_at_base_rate"]), "lift": f"{v['lift_at_base_rate']:.1f}x"}
          for k, v in t.items()}
    scen = {}
    for k, v in f["scenarios"].items():
        scen[k] = {"save_rate": pct(v["save_rate"], 0), "saved": f"{v['saved_per_year']:.0f}", "gross": money(v["gross_benefit"]),
                   "var_cost": money(v["variable_cost"]), "net": money(v["net_benefit"]), "roi": f"{v['roi_pct']:.0f}%"}
    ue, ps, A = f["unit_economics"], f["pilot_sizing"], f["assumptions"]
    be_book = f["scenarios"]["top5_upside"].get("breakeven_book_size")
    return {
        "n_customers": f"{results['n_customers']:,}", "n_features": str(results["model"]["n_features"]),
        "sample_churn": pct(results["sample_churn_rate"]),
        "eda": {
            "churn_le300": pct(e["churn_le300"]), "n_le300": f"{e['n_le300']:,}",
            "churn_301_400": pct(e["churn_301_400"]), "n_301_400": f"{e['n_301_400']:,}",
            "cohort_share_base": pct(e["cohort_share_of_base"]), "cohort_share_churners": pct(e["cohort_share_of_churners"]),
            "strata_t1": f"{pct(strata['<=12 months']['le300'])} to {pct(strata['<=12 months']['301_400'])}",
            "strata_t2": f"{pct(strata['13-24 months']['le300'])} to {pct(strata['13-24 months']['301_400'])}",
            "strata_t3": f"{pct(strata['>24 months']['le300'])} to {pct(strata['>24 months']['301_400'])}",
            "range_revenue": rng(e["range_revenue"]), "range_usage": rng(e["range_usage_change"]),
            "range_care": rng(e["range_care_calls"]), "range_price": rng(e["range_handset_price"]),
            "nyc_customers": f"{e['nyc_customers']:,}", "nyc_share": pct(e["nyc_share"]), "nyc_churn": pct(e["nyc_churn"]),
            "cols_missing": str(e["columns_with_missing"]), "max_missing": pct(e["max_missing_pct"] / 100),
            "max_missing_col": e["max_missing_column"],
        },
        "models": models,
        "gb": {"test_auc": f"{m['roc_auc']:.3f}", "auc_lo": f"{results['model']['auc_ci'][0]:.3f}",
               "auc_hi": f"{results['model']['auc_ci'][1]:.3f}", "pr_auc": f"{m['pr_auc']:.3f}",
               "accuracy": f"{m['accuracy']:.3f}", "precision": f"{m['precision']:.3f}", "recall": f"{m['recall']:.3f}",
               "f1": f"{m['f1']:.3f}", "brier_raw": f"{m['brier_raw']:.4f}", "brier_cal": f"{m['brier_calibrated']:.4f}"},
        "dec": {"top": pct(dec[1]["churn_rate"]), "bottom": pct(dec[10]["churn_rate"]),
                "ratio": f"{dec[1]['churn_rate'] / dec[10]['churn_rate']:.1f}"},
        "tgt": tg,
        "sub": {"auc_t1": f"{results['subgroups']['auc_by_tenure']['<=12 months']:.3f}",
                "auc_t2": f"{results['subgroups']['auc_by_tenure']['13-24 months']:.3f}",
                "auc_t3": f"{results['subgroups']['auc_by_tenure']['>24 months']:.3f}",
                "area_min": f"{results['subgroups']['auc_by_area_min']:.3f}", "area_max": f"{results['subgroups']['auc_by_area_max']:.3f}"},
        "fin": {
            "base_rate": pct(A["base_rate"], 2), "margin": pct(A["margin"], 0), "months": str(A["months"]),
            "contact_cost": f"${A['contact_cost']:.2f}", "incentive": f"${A['incentive']:.0f}",
            "accept_rate": pct(A["accept_rate"], 0), "fixed_cost": f"${A['fixed_cost_per_year']:,.0f}", "book": f"{A['book']:,}",
            "break_nudge": pct(ue["top5"]["breakeven_nudge"]), "break_incent": pct(ue["top5"]["breakeven_incentive"], 0),
            "value_per_save": f"${ue['top5']['value_per_save']:.0f}", "rev_top5": f"${ue['top5']['avg_monthly_rev']:.0f}",
            "churn_prob_top5": pct(ue["top5"]["churn_prob"]), "would_churn_top5": f"{ue['top5']['would_be_churners']:.0f}",
            "scen": scen, "breakeven_book_top5_upside": f"{be_book:,.0f}" if be_book else "n/a",
            "n10": f"{ps['top5']['n_10']:,}", "n20": f"{ps['top5']['n_20']:,}", "n30": f"{ps['top5']['n_30']:,}",
            "pilot_cost": money(ps["top5"]["n_20"] * A["contact_cost"]),
        },
    }


def main() -> None:
    results = json.loads((ROOT / "reports/results.json").read_text())
    notebook = json.loads((ROOT / "reports/notebook_results.json").read_text())
    out = ROOT / "build/variables.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(build(results, notebook), indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
