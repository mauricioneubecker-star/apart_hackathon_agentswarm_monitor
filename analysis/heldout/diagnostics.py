"""Diagnostics for the held-out comparison (writes out/diagnostics.json + out/diagnostics.log).

1. rounds-to-cut bins: rows / positives per bin and split; clock AUROC within each bin; positive rate by cut.
2. the clock's plan-time-matched AUROC on night_train CV (ID-OOF), for context (same code path as held-out).
3. bootstrap-seed sensitivity of the 11 primary p-values (seeds 1, 2, 3) and Holm on them.
4. implicit clock: Spearman correlation of each score with the round on held-out rows (all, and negatives only).
5. Monte-Carlo SE of the bootstrap p-values.
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

import hlib as L  # noqa: E402

OUT = f"{L.HO_DIR}/out"
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


S, lab = L.load_snapshots()
R = lab[lab.split.isin(L.HO)].reset_index(drop=True)
y = R.y.values.astype(int)
n = len(R)
cfgs = np.array(sorted(R.cfg.unique()))
C = len(cfgs)
cix = {c: i for i, c in enumerate(cfgs)}
g = R.cfg.map(cix).values
scores = {}
for name, (src, _) in L.PREDICTORS.items():
    scores[name], miss, nan = L.attach(R, L.read_pred(src))
    assert miss == 0 and nan == 0
out = {}

# 1. bins
tab = R.assign(split=R.split.map(L.SHORT)).pivot_table(index="rtc_bin", columns="split", values="y", aggfunc=["size", "sum"])
log("rows / positives per rounds-to-cut bin and split:\n" + tab.to_string())
out["rtc_bins"] = {b: {"rows": int((R.rtc_bin == b).sum()), "pos": int(R.y[R.rtc_bin == b].sum())} for b in L.RTC_LABELS}
cl = scores["clock"]
within = {}
for b in L.RTC_LABELS:
    m = (R.rtc_bin == b).values
    pr = R[m].groupby("cut").y.agg(["size", "mean"])
    within[b] = {"clock_auroc": float(roc_auc_score(y[m], cl[m])) if 0 < y[m].sum() < m.sum() else None,
                 "pos_rate_by_cut": {int(k): float(v) for k, v in pr["mean"].items()},
                 "rows_by_cut": {int(k): int(v) for k, v in pr["size"].items()},
                 "pairs": int(y[m].sum() * (m.sum() - y[m].sum()))}
    log(f"  bin {b:7s} clock AUROC {within[b]['clock_auroc']}  pos rate by cut {within[b]['pos_rate_by_cut']}  "
        f"rows by cut {within[b]['rows_by_cut']}  pairs {within[b]['pairs']}")
out["clock_within_rtc_bins"] = within
rb = {}
for b in sorted(R.round_bin.unique()):
    m = (R.round_bin == b).values
    rb[int(b)] = {"rows": int(m.sum()), "pos": int(y[m].sum()),
                  "clock_auroc": float(roc_auc_score(y[m], cl[m])) if 0 < y[m].sum() < m.sum() else None}
log("harness round bins (0 = rounds 1-5, ..., 5 = 26-30):", rb)
out["clock_within_round_bins"] = rb

# 2. clock time-matched on night_train CV (ID-OOF, repeat mean), same definitions
oof = L.H.id_oof(pd.read_csv(f"{L.CV}/hgb_clock.csv")).merge(lab, on=["run", "round"])
cv_tm = L.stratified_auroc(oof.y.values, oof.score.values, oof.rtc_bin.values)
cv_th = L.MH.time_matched_auroc(oof.y.values, oof.score.values, oof["round"].values)
out["clock_cv_night_train"] = {"rows": int(len(oof)), "pos": int(oof.y.sum()), "auroc": float(roc_auc_score(oof.y, oof.score)),
                               "tm_plan": cv_tm, "tm_harness": float(cv_th)}
log(f"clock on night_train CV (ID-OOF): AUROC {out['clock_cv_night_train']['auroc']:.3f}, plan time-matched {cv_tm:.3f}, "
    f"harness tAUROC {cv_th:.3f}")
for name in ["bag+graph", "hybrid", "gnn5", "zs:pairwise", "zs:global_full"]:
    if name.startswith("zs:"):
        tr = lab[lab.split == "night_train"]
        s, _, _ = L.attach(tr, L.read_pred(L.PREDICTORS[name][0]))
        yy, rr, rd = tr.y.values, tr.rtc_bin.values, tr["round"].values
    else:
        o = L.H.id_oof(pd.read_csv(L.PREDICTORS[name][1][1])).merge(lab, on=["run", "round"])
        s, yy, rr, rd = o.score.values, o.y.values, o.rtc_bin.values, o["round"].values
    out.setdefault("cv_tm_plan_context", {})[name] = {"tm_plan": L.stratified_auroc(yy, s, rr),
                                                      "tm_harness": float(L.MH.time_matched_auroc(yy, s, rd))}
log("night_train (CV OOF / zero-shot) time-matched, for context:", {k: {a: round(b, 3) for a, b in v.items()}
                                                                    for k, v in out["cv_tm_plan_context"].items()})

# 3. seed sensitivity of the primary p-values
PRIMARY = [("bag+graph", "clock", "tm_plan"), ("zs:pairwise", "clock", "tm_plan"), ("zs:global_full", "clock", "tm_plan"),
           ("gnn5", "clock", "tm_plan"), ("hybrid", "clock", "tm_plan"),
           ("gnn5", "bag+graph", "pooled"), ("hybrid", "bag+graph", "pooled"), ("zs:pairwise", "bag+graph", "pooled"),
           ("zs:pairwise", "gnn5", "pooled"), ("zs:pairwise", "hybrid", "pooled"), ("zs:global_full", "bag+graph", "pooled")]
rtc = R.rtc_bin.values
mats = {nm: {"pooled": L.pair_mats(y, scores[nm], g, np.zeros(n, int), C), "tm_plan": L.pair_mats(y, scores[nm], g, rtc, C)}
        for nm in {a for a, _, _ in PRIMARY} | {b for _, b, _ in PRIMARY}}
F = {"pooled": L.stat_pooled, "tm_plan": L.stat_pairs}
seeds = {}
for sd in (20261108, 1, 2, 3):
    K = L.draws(C, 10_000, sd)
    ps = [L.pval(F[k](K, mats[a][k]) - F[k](K, mats[b][k])) for a, b, k in PRIMARY]
    seeds[sd] = {"p": ps, "holm": L.holm(ps).tolist()}
    log(f"seed {sd}: p " + " ".join(f"{p:.4f}" for p in ps) + " | min Holm " + f"{min(seeds[sd]['holm']):.3f}")
out["seed_sensitivity"] = {str(k): v for k, v in seeds.items()}
out["mc_se_of_p"] = {f"{a} - {b}": float(2 * np.sqrt(max(min(p / 2, 1 - p / 2), 1e-4) * (1 - min(p / 2, 1 - p / 2)) / 10_000))
                     for (a, b, _), p in zip(PRIMARY, seeds[20261108]["p"])}

# 4. implicit clock
rd = R["round"].values
ic = {}
for nm, s in scores.items():
    ic[nm] = {"spearman_round_all": float(stats.spearmanr(s, rd)[0]),
              "spearman_round_negatives": float(stats.spearmanr(s[y == 0], rd[y == 0])[0]),
              "spearman_rtc_negatives": float(stats.spearmanr(s[y == 0], R.rounds_to_cut.values[y == 0])[0])}
log("Spearman(score, round) on held-out rows [all / negatives only]:",
    {k: (round(v["spearman_round_all"], 2), round(v["spearman_round_negatives"], 2)) for k, v in ic.items()})
out["implicit_clock"] = ic

# before-announcement subset size
m = (R.before_announce == 1).values
out["before_announce"] = {"rows": int(m.sum()), "pos": int(y[m].sum()), "cfgs": int(R.cfg[m].nunique())}
log("before-announcement rows:", out["before_announce"])
json.dump(out, open(f"{OUT}/diagnostics.json", "w"), indent=1, default=float)
open(f"{OUT}/diagnostics.log", "w").write("\n".join(LOG) + "\n")
