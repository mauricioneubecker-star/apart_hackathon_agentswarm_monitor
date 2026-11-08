"""Baseline predictions for the night_vx evaluation (ANALYSIS_PLAN.md §6 step 2 and Nachtrag 2).

Refits the harness baselines on night_train exactly like gnn_opt/baselines.py (same specs, same train rows
`H.train_rows`, same HGB settings, single thread) and predicts
  (a) every non-train snapshot of the night batch (Part B needs the night runs of its 8 source configs), and
  (b) every snapshot of runs_vx.
Nothing is evaluated. Labels of runs_vx are not used, except `risk` (true violator count) as the input of the oracle
reference, which is what the oracle is by definition. baselines.py --apply skips the edge monitor, so the night-fitted
per-edge model is applied to the vx edge features here (same code path as EdgeMonitor.predict, checked on night).

Built-in checks (written to <out>/make_baselines.json):
  * edge apply on the night dataset == EdgeMonitor.predict (exact);
  * night non-train predictions == the held-out refits (analysis/heldout, scratch regen dir) after %.5g rounding;
  * night_val predictions vs the committed gnn_opt/preds/eval/<name>.csv (exact for clock, oracle and edge; models on
    table.csv aggregates carry float32 table noise, see analysis/results/heldout_full.md §1.2).

  python analysis/vx_preds/make_baselines.py --harness <gnn-opt-torch checkout>/gnn_opt --night <dataset dir> \
      --vx <dataset dir> --out <dir> [--regen <dir>]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NAMES = ["hgb_clock", "hgb_struct", "hgb_pairwise", "hgb_bag", "hgb_bag+graph", "hgb_bag+graph+mem",
         "oracle_risk+clock", "edge_monitor_top3"]


def edge_apply(fitted, G, snaps, ecols_ref, pool="top3"):
    """EdgeMonitor.predict with the edge arrays of another dataset G (fitted model from the night dataset)."""
    ec = list(G["ecols"])
    assert list(ecols_ref) == ec, "edge feature columns differ between datasets"
    ci = [ec.index(c) for c in BL.E_GEN]
    esnap = G["node_snap"][G["ES"]]
    m = np.isin(esnap, snaps)
    X = np.nan_to_num(G["EF"][m][:, ci], nan=-1.0)
    es = esnap[m]
    p = fitted.m.predict_proba(X)[:, 1]
    s = pd.Series(p).groupby(es)
    agg = s.max() if pool == "max" else s.apply(lambda v: np.sort(v.values)[-3:].mean())
    return pd.Series(snaps).map(agg).fillna(fitted.empty).values


def g5(x):
    return np.array([float(f"{v:.5g}") for v in x])


def main():
    global BL, H
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harness", required=True)
    ap.add_argument("--night", required=True)
    ap.add_argument("--vx", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--regen", default=None)
    a = ap.parse_args()
    sys.path.insert(0, a.harness)
    import baselines as BL  # noqa: E402
    import harness as H  # noqa: E402

    os.makedirs(a.out, exist_ok=True)
    D = H.load(a.night, graphs=True)
    S, T = D["S"], D["T"].assign(risk=D["S"].risk.values)
    E = H.load(a.vx, graphs=True)
    SV, TV = E["S"], E["T"].assign(risk=E["S"].risk.values)
    sp = BL.specs(T)
    sp["edge_monitor_top3"] = lambda: BL.EdgeMonitor(D, "top3")
    y, snaps = S["y3"].values, S.snap.values
    tr = H.train_rows(S, "y3").values
    te = (S.split != H.TRAIN_SPLIT).values
    assert not SV.split.eq(H.TRAIN_SPLIT).any(), "vx dataset contains night_train rows"
    rep = {"train_rows": int(tr.sum()), "train_positives": int(np.nansum(y[tr])), "night_predicted": int(te.sum()),
           "vx_predicted": int(len(SV)), "models": {}}
    print(rep, flush=True)
    for n in NAMES:
        is_edge = n.startswith("edge_monitor")
        m = sp[n]()
        m = m.fit(snaps[tr], y[tr]) if is_edge else m.fit(T[tr], y[tr])
        if is_edge:
            p_night = m.predict(snaps[te])
            chk = edge_apply(m, D, snaps[te], D["ecols"])
            assert np.array_equal(p_night, chk), "edge_apply differs from EdgeMonitor.predict on night"
            p_vx = edge_apply(m, E, SV.snap.values, D["ecols"])
        else:
            missing = [c for c in m.cols if c not in TV.columns]
            assert not missing, f"{n}: vx table lacks {missing[:5]}"
            p_night, p_vx = m.predict(T[te]), m.predict(TV)
        P = pd.concat([pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": p_night}),
                       pd.DataFrame({"run": SV.run.values, "round": SV["round"].values, "score": p_vx})],
                      ignore_index=True)
        assert not P.duplicated(["run", "round"]).any() and P.score.notna().all()
        P.to_csv(os.path.join(a.out, f"{n}.csv"), index=False)
        r = {"rows": int(len(P)), "vx_rows": int(len(p_vx)), "vx_distinct": int(pd.Series(p_vx).nunique())}
        night = P.iloc[:int(te.sum())]
        if a.regen and os.path.exists(os.path.join(a.regen, f"{n}.csv")):
            R = pd.read_csv(os.path.join(a.regen, f"{n}.csv"))
            j = R.merge(night, on=["run", "round"], how="left", suffixes=("_ref", "_new"))
            d = np.abs(j.score_ref.values - g5(j.score_new.values))
            r["vs_heldout_regen"] = {"rows": int(len(j)), "matched": int(j.score_new.notna().sum()),
                                     "max_abs_diff_after_g5": float(np.nanmax(d)), "exact_share": float(np.mean(d == 0))}
        cf = os.path.join(a.harness, "preds", "eval", f"{n}.csv")
        if os.path.exists(cf):
            C = pd.read_csv(cf)
            j = C.merge(night, on=["run", "round"], how="left", suffixes=("_ref", "_new"))
            d = np.abs(j.score_ref.values - g5(j.score_new.values))
            r["vs_committed_eval"] = {"rows": int(len(j)), "matched": int(j.score_new.notna().sum()),
                                      "max_abs_diff_after_g5": float(np.nanmax(d)), "exact_share": float(np.mean(d == 0)),
                                      "spearman": float(j[["score_ref", "score_new"]].corr("spearman").iloc[0, 1])}
        rep["models"][n] = r
        print(n, json.dumps(r), flush=True)
    json.dump(rep, open(os.path.join(a.out, "make_baselines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
