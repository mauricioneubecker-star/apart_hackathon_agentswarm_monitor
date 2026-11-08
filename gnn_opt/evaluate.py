#!/usr/bin/env python3
"""Metrics table for one or more prediction files on the same rows.

  # CV predictions (column 'fold'): ID pooled + LODO table + strata on ID out-of-fold predictions
  python3 gnn_opt/evaluate.py --data gnn_opt_data/night --preds gnn_opt/preds/cv/hgb_bag_graph.csv ...

  # held-out predictions (no 'fold' column), threshold for R@5%FPR from the matching CV file
  python3 gnn_opt/evaluate.py --data gnn_opt_data/night --preds A_eval.csv B_eval.csv \
      --thr-from A_cv.csv B_cv.csv --splits night_val --boot 1000

  # any new batch: build it, then predict, then evaluate (split 'all' = every row with a label)
  python3 gnn_opt/evaluate.py --data gnn_opt_data/new --preds new_preds.csv --splits all

Prediction file columns: run, round, score [, count] [, fold]. Rows are matched on (run, round) to snapshots.csv;
only rows with eval == 1 (label defined, not a duplicated branch prefix) are scored, except for the branch analysis.
Options: --target y3|y5|yrel3|yrel5 ; --pairs (bootstrap differences first file vs the others).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H  # noqa: E402
import metrics as M  # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 40)


def lead_time(df, score, thr):
    """Per tipped run: first round with score > thr before the tip (rows with a defined label); lead = tip - alarm.
    Also false-alarm rate on runs that never tip."""
    d = df.assign(s=score)
    leads, fa = [], []
    for run, g in d.groupby("run"):
        g = g.sort_values("round")
        al = g[g.s > thr]["round"]
        if g.tipped.iloc[0] == 1 and g.tip_round.notna().iloc[0]:
            tr = g.tip_round.iloc[0]
            pre = al[al < tr]
            leads.append(tr - pre.min() if len(pre) else 0)
        else:
            fa.append(int(len(al) > 0))
    leads = np.array(leads)
    return {"tipped_runs": len(leads), "alarmed_before_tip": float((leads > 0).mean()) if len(leads) else np.nan,
            "median_lead": float(np.median(leads[leads > 0])) if (leads > 0).any() else np.nan,
            "untipped_runs": len(fa), "false_alarm_runs": float(np.mean(fa)) if fa else np.nan}


def branch_analysis(S, P):
    """Counterfactual arms: per branch config, compare predicted risk after the branch point between arms with
    different outcomes. Returns per-pair rows and summary."""
    rows = []
    B = S[S.split == "night_branch"]
    d = B.merge(P[["run", "round", "score"]], on=["run", "round"], how="inner")
    for cfg, g in d.groupby("cfg"):
        b0 = g.branch_round.max()
        arms = {r: x for r, x in g.groupby("run")}
        outc = {r: x.tipped.iloc[0] for r, x in arms.items()}
        # post-branch window: rounds b0+1 .. min(first tip among arms, b0+10)
        for a in arms:
            for b in arms:
                if outc[a] == 1 and outc[b] == 0:
                    xa, xb = arms[a], arms[b]
                    tips = [x.tip_round.iloc[0] for x in (xa,) if x.tip_round.notna().iloc[0]]
                    hi = min([b0 + 10] + [t - 1 for t in tips])
                    pa = xa[(xa["round"] > b0) & (xa["round"] <= hi)].set_index("round").score
                    pb = xb[(xb["round"] > b0) & (xb["round"] <= hi)].set_index("round").score
                    common = pa.index.intersection(pb.index)
                    pre_a = xa[xa["round"] <= b0].set_index("round").score
                    pre_b = xb[xb["round"] <= b0].set_index("round").score
                    pc = pre_a.index.intersection(pre_b.index)
                    rows.append({"cfg": cfg, "tipped_arm": a.split("/")[-1], "untipped_arm": b.split("/")[-1],
                                 "rounds": len(common),
                                 "pre_diff": float((pre_a[pc] - pre_b[pc]).mean()) if len(pc) else np.nan,
                                 "post_diff": float((pa[common] - pb[common]).mean()) if len(common) else np.nan,
                                 "post_frac_higher": float((pa[common] > pb[common]).mean()) if len(common) else np.nan})
    R = pd.DataFrame(rows)
    if len(R):
        summ = {"pairs": len(R), "mean_post_diff": R.post_diff.mean(), "share_pairs_tipped_arm_higher":
                float((R.post_diff > 0).mean()), "mean_pre_diff": R.pre_diff.mean()}
    else:
        summ = {"pairs": 0}
    return R, summ


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--preds", nargs="+", required=True)
    ap.add_argument("--names", default=None, help="comma-separated display names")
    ap.add_argument("--thr-from", nargs="*", default=None, help="CV prediction files (same order) for the 5%%-FPR threshold")
    ap.add_argument("--thr", default=None, help="comma list of explicit thresholds (same order as --preds)")
    ap.add_argument("--splits", default="night_val", help="comma list, or 'all'")
    ap.add_argument("--target", default="y3")
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--pairs", action="store_true", help="bootstrap AUROC differences: first file minus each other")
    ap.add_argument("--out", default=None, help="write the metrics table as CSV")
    a = ap.parse_args()
    D = H.load(a.data, table=False)
    S = D["S"]
    mixed = set(D["schema"]["mixed_cfgs"])
    names = a.names.split(",") if a.names else [os.path.basename(p).replace(".csv", "") for p in a.preds]
    lab = S[S["eval"] == 1].copy()
    lab["y"] = lab[a.target]
    lab = lab[lab.y.notna()]
    preds = [pd.read_csv(p) for p in a.preds]

    # ---------------------------------------------------------------- CV mode
    if all("fold" in P for P in preds):
        rows = []
        for n, P in zip(names, preds):
            cs = H.cv_summary(S, P, a.target)
            oof = H.id_oof(P).merge(lab, on=["run", "round"])
            thr = M.thr_at_fpr(oof.y.values, oof.score.values)
            r = {"model": n, "select": cs.get("select"), "ID_AUROC": cs["id_auroc"], "ID_AUPRC": cs["id_auprc"],
                 "LODO_mean": cs.get("lodo_mean"), "LODO_min": cs.get("lodo_min")}
            r.update({f"L:{k.replace('hold_', '')}": v for k, v in cs["lodo"].items()})
            rep = M.full_report(oof, oof.score.values, thr, mixed, oof["count"].values if "count" in oof else None)
            r.update({k: v for k, v in rep.items() if k not in ("AUROC", "AUPRC")})
            rows.append(r)
        T = pd.DataFrame(rows)
        print(f"== CV on {H.TRAIN_SPLIT} (target {a.target}); ID = pooled out-of-fold, mean over repeats ==")
        print(T.round(3).to_string(index=False))
        if a.out:
            T.to_csv(a.out, index=False)
        if a.pairs and len(preds) > 1:
            oofs = [H.id_oof(P).merge(lab, on=["run", "round"]) for P in preds]
            base = oofs[0][["run", "round", "cfg", "y", "risk"]]
            pr = {n: base.merge(o[["run", "round", "score"]], on=["run", "round"], how="left").score.values
                  for n, o in zip(names, oofs)}
            for reg, mk in [("all", None), ("risk3-7", base.risk.between(3, 7).values),
                            ("mixed", base.cfg.isin(mixed).values)]:
                ci = M.boot_ci(base, pr, n=a.boot, mask=mk, pairs=[(names[0], n) for n in names[1:]])
                print(f"-- bootstrap over configs ({reg}):")
                for k, v in ci.items():
                    print(f"   {k:40s} " + " ".join(f"{x:.3f}" for x in v))
        return

    # ---------------------------------------------------------------- held-out mode
    sp = None if a.splits == "all" else a.splits.split(",")
    L = lab if sp is None else lab[lab.split.isin(sp)]
    thrs = [None] * len(preds)
    if a.thr_from:
        for i, f in enumerate(a.thr_from):
            oof = H.id_oof(pd.read_csv(f)).merge(lab, on=["run", "round"])
            thrs[i] = M.thr_at_fpr(oof.y.values, oof.score.values)
    if a.thr:
        thrs = [float(x) if x not in ("", "none") else None for x in a.thr.split(",")]
    rows, aligned = [], {}
    for n, P, thr in zip(names, preds, thrs):
        d = L.merge(P, on=["run", "round"], how="inner")
        aligned[n] = d
        groups = [("pooled", d)] + ([(s, g) for s, g in d.groupby("split")] if d.split.nunique() > 1 else [])
        for gname, g in groups:
            r = {"model": n, "split": gname}
            r.update(M.full_report(g, g.score.values, thr, mixed, g["count"].values if "count" in g else None))
            ci = M.boot_ci(g, {"m": g.score.values}, n=a.boot)["m"]
            r["AUROC_lo"], r["AUROC_hi"] = ci[0], ci[2]
            ci = M.boot_ci(g, {"m": g.score.values}, metric="AUPRC", n=a.boot)["m"]
            r["AUPRC_lo"], r["AUPRC_hi"] = ci[0], ci[2]
            if thr is not None:
                r.update({f"lead:{k}": v for k, v in lead_time(g, g.score.values, thr).items()})
            rows.append(r)
    T = pd.DataFrame(rows)
    print(f"== held-out ({a.splits}, target {a.target}) ==")
    print(T.round(3).to_string(index=False))
    if a.out:
        T.to_csv(a.out, index=False)
    if a.pairs and len(preds) > 1:
        base = aligned[names[0]][["run", "round", "cfg", "y", "risk", "score"]]
        pr = {n: base[["run", "round"]].merge(aligned[n][["run", "round", "score"]], on=["run", "round"],
                                              how="left").score.values for n in names}
        ci = M.boot_ci(base, pr, n=a.boot, pairs=[(names[0], n) for n in names[1:]])
        print("-- bootstrap over configs, AUROC differences:")
        for k, v in ci.items():
            if "-" in k:
                print(f"   {k:40s} " + " ".join(f"{x:.3f}" for x in v))
    if sp is None or "night_branch" in sp:
        for n, P in zip(names, preds):
            R, summ = branch_analysis(S, P)
            print(f"-- branch arms ({n}):", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in summ.items()})


if __name__ == "__main__":
    main()
