"""Sensitivity promised in ANALYSIS_PLAN.md Nachtrag 2 item 3 (run once, after the night_vx evaluation).

The stored GNN file models/cloud_final_gnn.pt keeps 15 of the 40 states the GNN team averaged for its held-out
numbers. This reports, on the held-out rows of analysis/results/heldout.md (night_test_id, test_ood_family,
test_ood_seed, night_branch; eval == 1), the AUROC and time-matched AUROC of the stored 15-state GNN and hybrid next
to the 40-state versions, with a paired cluster bootstrap over configs. Exploratory; changes no rule.

  python analysis/vx_gnn15_heldout.py --snap analysis/vx_preds/snap/night_snapshots.csv \
      --index sim_dataset/dataset/index.csv --gnn40 <cloud_final_gnn.csv> --hybrid40 <cloud_final.csv> \
      --gnn15 analysis/vx_preds/preds/gnn.csv --hybrid15 analysis/vx_preds/preds/hybrid.csv \
      --out analysis/results/vx_gnn15_heldout
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HO = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]
BINS = [-99, -9, -5, -1, 3, 99]


def tm(y, p, b):
    num = den = 0.0
    for v in np.unique(b):
        m = b == v
        n1 = int(y[m].sum())
        n0 = int(m.sum()) - n1
        if n1 and n0:
            num += n1 * n0 * roc_auc_score(y[m], p[m])
            den += n1 * n0
    return num / den if den else np.nan


def main():
    ap = argparse.ArgumentParser()
    for k in ("snap", "index", "gnn40", "hybrid40", "gnn15", "hybrid15", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261108)
    a = ap.parse_args()
    I = pd.read_csv(a.index, low_memory=False).set_index("scenario_id")
    S = pd.read_csv(a.snap, low_memory=False)
    S = S[(S["eval"] == 1) & S.y3.notna() & S.split.isin(HO)][["run", "round", "cfg", "split", "y3"]].copy()
    S["rtc"] = S["round"] - S.cfg.map(I["deadline_round"]).astype(float)
    S["bin"] = np.asarray(pd.Series(pd.cut(S.rtc.values, BINS)).astype(str))
    names = {"gnn40": a.gnn40, "gnn15": a.gnn15, "hybrid40": a.hybrid40, "hybrid15": a.hybrid15}
    for n, p in names.items():
        P = pd.read_csv(p)[["run", "round", "score"]].rename(columns={"score": n})
        S = S.merge(P, on=["run", "round"], how="left")
        assert S[n].notna().all(), f"{n}: missing rows"
    y, b = S.y3.values.astype(int), S["bin"].values
    cfgs = np.array(sorted(S.cfg.unique()))
    idx = {c: np.where(S.cfg.values == c)[0] for c in cfgs}
    rng = np.random.default_rng(a.seed)

    def metr(rows):
        return {n: (roc_auc_score(y[rows], S[n].values[rows]), tm(y[rows], S[n].values[rows], b[rows])) for n in names}

    full = metr(np.arange(len(S)))
    draws = []
    for _ in range(a.boot):
        rows = np.concatenate([idx[c] for c in rng.choice(cfgs, len(cfgs), replace=True)])
        if 0 < y[rows].sum() < len(rows):
            draws.append(metr(rows))
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    res = {"rows": int(len(S)), "positives": int(y.sum()), "configs": int(len(cfgs)), "valid_draws": len(draws),
           "spearman_15_vs_40": {k: float(S[[k + "40", k + "15"]].corr("spearman").iloc[0, 1]) for k in ("gnn", "hybrid")},
           "metrics": {}}
    for n in names:
        res["metrics"][n] = {"auroc": float(full[n][0]), "tm_auroc": float(full[n][1])}
    for k in ("gnn", "hybrid"):
        for j, m in enumerate(("auroc", "tm_auroc")):
            d = [dr[k + "15"][j] - dr[k + "40"][j] for dr in draws]
            res["metrics"][f"{k}15_minus_{k}40_{m}"] = {"diff": float(full[k + "15"][j] - full[k + "40"][j]), "ci": ci(d)}
    json.dump(res, open(a.out + ".json", "w"), indent=1)
    L = ["# Stored 15-state GNN vs reported 40-state GNN on the held-out rows (exploratory)", "",
         f"Rows {res['rows']}, positives {res['positives']}, configs {res['configs']}, valid draws {res['valid_draws']}.", "",
         "| predictor | AUROC | time-matched AUROC |", "|---|---|---|"]
    for n in names:
        L.append(f"| {n} | {res['metrics'][n]['auroc']:.3f} | {res['metrics'][n]['tm_auroc']:.3f} |")
    L += ["", "| difference (15 − 40) | AUROC [CI] | time-matched [CI] |", "|---|---|---|"]
    for k in ("gnn", "hybrid"):
        x, z = res["metrics"][f"{k}15_minus_{k}40_auroc"], res["metrics"][f"{k}15_minus_{k}40_tm_auroc"]
        L.append(f"| {k} | {x['diff']:+.3f} [{x['ci'][0]:+.3f}, {x['ci'][1]:+.3f}] | {z['diff']:+.3f} [{z['ci'][0]:+.3f}, {z['ci'][1]:+.3f}] |")
    L += ["", f"Spearman 15 vs 40 on these rows: {res['spearman_15_vs_40']}", "",
          "gnn15 = the stored models/cloud_final_gnn.pt (15 states). hybrid15 = the vx hybrid, i.e. gnn15 blended with the",
          "locally refit tab_mem; hybrid40 = the team's cloud_final.csv (40-state GNN + the team's own tab_mem), so the",
          "hybrid row differs in both components, not only in the stored states."]
    open(a.out + ".md", "w").write("\n".join(L) + "\n")
    print("wrote", a.out + ".json", a.out + ".md")


if __name__ == "__main__":
    main()
