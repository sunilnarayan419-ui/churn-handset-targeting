"""Recompute every number used in the manuscript from the raw data, using only the package.

    python scripts/export_results.py --data-dir data/raw --out reports/results.json

Requires scipy (notebook extra) for the chi-square test. Takes about 1-2 minutes on one CPU core.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from churn_targeting import bands
from churn_targeting.calibration import to_real_world
from churn_targeting.data import load_customers
from churn_targeting.finance import Assumptions, annualize, economics
from churn_targeting.modeling import train
from churn_targeting.pilot import n_per_arm
from churn_targeting.targeting import decile_table, mask_stats, top_fraction_stats

SCENARIOS = {
    "Conservative": dict(pi=0.0086, s=0.03, margin=0.30, months=6, contact=1.00),
    "Base": dict(pi=0.0099, s=0.06, margin=0.40, months=12, contact=0.75),
    "Upside": dict(pi=0.0104, s=0.10, margin=0.50, months=12, contact=0.50),
}


def eda_stats(df: pd.DataFrame) -> dict:
    from scipy import stats

    le300 = df[df.eqpdays <= 300].churn
    mid = df[(df.eqpdays > 300) & (df.eqpdays <= 400)].churn
    table = np.array([[le300.sum(), len(le300) - le300.sum()], [mid.sum(), len(mid) - mid.sum()]])
    p = float(stats.chi2_contingency(table)[1])
    cohort = bands.past_300_days(df.eqpdays)
    tenure = bands.tenure_band(df.months)
    eq3 = pd.cut(df.eqpdays, [-np.inf, 300, 400, np.inf], labels=["le300", "301_400", "gt400"])
    strata = (df.assign(t=tenure, e=eq3).pivot_table(index="t", columns="e", values="churn",
                                                     aggfunc="mean", observed=True))
    def spread(col, q=None, bins=None):
        s = pd.qcut(df[col], q, duplicates="drop") if q else pd.cut(df[col], bins)
        m = df.groupby(s, observed=True).churn.mean()
        return [float(m.min()), float(m.max())]
    nyc = df[df.area == "NEW YORK CITY AREA"]
    miss = (df.isna().mean() * 100).sort_values(ascending=False)
    return {
        "churn_le300": float(le300.mean()), "n_le300": int(len(le300)),
        "churn_301_400": float(mid.mean()), "n_301_400": int(len(mid)), "chi2_p": p,
        "cohort_share_of_base": float(cohort.mean()),
        "cohort_share_of_churners": float(cohort[df.churn == 1].mean()),
        "tenure_strata": {str(i): {k: float(v) for k, v in r.items()} for i, r in strata.iterrows()},
        "range_revenue": spread("rev_Mean", q=5), "range_usage_change": spread("change_mou", q=5),
        "range_care_calls": spread("custcare_Mean", bins=[-1, 0, 2, 5, 10_000]),
        "range_handset_price": spread("hnd_price", bins=[0, 30, 100, 150, 1000]),
        "nyc_customers": int(len(nyc)), "nyc_share": float(len(nyc) / len(df)), "nyc_churn": float(nyc.churn.mean()),
        "columns_with_missing": int((miss > 0).sum()), "max_missing_pct": float(miss.iloc[0]),
        "max_missing_column": str(miss.index[0]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/raw")
    ap.add_argument("--out", default="reports/results.json")
    args = ap.parse_args()

    df = load_customers(args.data_dir)
    out: dict = {"n_customers": len(df), "sample_churn_rate": float(df.churn.mean()), "eda": eda_stats(df)}

    res = train(df)
    b, X_test, y_test, raw = res.bundle, res.X_test, res.y_test.values, res.raw_test_scores
    out["model"] = {"name": b.metadata["model_name"], "n_features": b.metadata["n_features"],
                    "params": b.metadata["params"], "metrics_test": res.metrics}
    rng = np.random.default_rng(42)
    boot = [roc_auc_score(y_test[i], raw[i]) for i in (rng.integers(0, len(y_test), len(y_test)) for _ in range(300))]
    out["model"]["auc_ci"] = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

    out["targeting"] = {f"top{int(f * 100)}": top_fraction_stats(y_test, raw, f, 0.01) for f in (0.05, 0.10, 0.20)}
    out["targeting"]["rule_301_400"] = mask_stats(y_test, bands.past_300_days(X_test.eqpdays).values, 0.01)
    out["deciles"] = decile_table(y_test, raw).round(4).reset_index().to_dict("records")

    tt = pd.DataFrame({"y": y_test, "p": raw, "months": X_test.months.values, "area": X_test.area.values})
    tt["tenure"] = bands.tenure_band(tt.months).astype(str)
    auc = lambda g: float(roc_auc_score(g.y, g.p))  # noqa: E731
    out["subgroups"] = {"auc_by_tenure": {k: auc(g) for k, g in tt.groupby("tenure")},
                        "auc_by_area_min": min(auc(g) for _, g in tt.groupby("area")),
                        "auc_by_area_max": max(auc(g) for _, g in tt.groupby("area"))}

    # --- finance (same definitions as the notebook; see churn_targeting.finance) ---
    A = Assumptions()
    train_idx = df.index.difference(X_test.index)
    rev_fill = float(df.loc[train_idx, "rev_Mean"].median())
    rev = df.loc[X_test.index, "rev_Mean"].clip(lower=0).fillna(rev_fill).to_numpy()
    p_cal = b.calibrator.predict(raw)
    order = np.argsort(-raw)

    def slice_inputs(frac, pi):
        top = order[: int(round(frac * len(raw)))]
        return float(to_real_world(p_cal, pi, b.pi_sample)[top].mean()), float(rev[top].mean())

    unit = {}
    for frac in (0.05, 0.10, 0.20):
        p, r = slice_inputs(frac, A.base_rate)
        nudge = economics(frac * A.book, p, r, 0, A.margin, A.months, A.contact_cost)
        incent = economics(frac * A.book, p, r, 0, A.margin, A.months, A.contact_cost, A.accept_rate, A.incentive)
        unit[f"top{int(frac * 100)}"] = {"churn_prob": p, "avg_monthly_rev": r, "value_per_save": nudge["value_per_save"],
                                         "would_be_churners": nudge["would_be_churners"],
                                         "breakeven_nudge": nudge["breakeven_save_rate"],
                                         "breakeven_incentive": incent["breakeven_save_rate"]}
    scen = {}
    for frac in (0.05, 0.10):
        for name, sc in SCENARIOS.items():
            p, r = slice_inputs(frac, sc["pi"])
            wave = economics(frac * A.book, p, r, sc["s"], sc["margin"], sc["months"], sc["contact"])
            scen[f"top{int(frac * 100)}_{name.lower()}"] = {**annualize(wave, A.fixed_cost_per_year, book=A.book),
                                                             "saved_per_year": 12 * wave["saved"], "save_rate": sc["s"]}
    pilot = {}
    for key, u in unit.items():
        pilot[key] = {f"n_{int(e * 100)}": n_per_arm(u["churn_prob"], e) for e in (0.10, 0.20, 0.30)}
    out["finance"] = {"assumptions": A.__dict__, "unit_economics": unit, "scenarios": scen, "pilot_sizing": pilot}

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=float))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
