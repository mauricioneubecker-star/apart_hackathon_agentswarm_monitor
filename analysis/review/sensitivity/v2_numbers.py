"""(4) Every cell of analysis/results/sensitivity.md vs results.json + base, and (independently) vs preds.csv:
main AUROC, time-matched / mixed stratified AUROC, and an exact replication of the paired bootstrap (seed 0)."""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

SENS = sys.argv[1]
MD = "/Users/mauricio/sim_local/apart_vx/analysis/results/sensitivity.md"
TAGS = ["t8d3", "t6d3", "t10d3", "t8d2", "t8d5"]
HDR = {"t8d3": "θ=8, Δ=3", "t6d3": "θ=6, Δ=3", "t10d3": "θ=10, Δ=3", "t8d2": "θ=8, Δ=2", "t8d5": "θ=8, Δ=5"}
PRED = {"nur Uhr": "clock", "bag + graph": "bag+graph", "LLM ganzes Protokoll": "zs:global_full",
        "LLM letzte 6 Runden": "zs:global_window", "LLM Gespräch für Gespräch": "zs:pairwise",
        "LLM Gespräch für Gespräch, gestackt": "hgb:pairwise", "Verstoßzähler + Uhr (Referenz)": "oracle"}
DIFF = {"LLM paarweise − bag+graph": ("zs:pairwise", "bag+graph"), "LLM ganzes Protokoll − bag+graph": ("zs:global_full", "bag+graph"),
        "Uhr − bag+graph": ("clock", "bag+graph")}

# ---------------------------------------------------------------- parse markdown table
lines = [l for l in open(MD).read().splitlines() if l.startswith("|")]
head = [c.strip() for c in lines[0].strip("|").split("|")]
cells = {}
for l in lines[2:]:
    c = [x.strip() for x in l.strip("|").split("|")]
    for h, v in zip(head[1:], c[1:]):
        cells[(c[0], h)] = v
print("parsed cells:", len(cells), "columns:", head[1:])


def strat_auc(y, p, s):
    df = pd.DataFrame({"y": y, "p": p, "s": s}).dropna()
    num = den = 0.0
    nstrata = 0
    for _, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            num += npos * nneg * roc_auc_score(g.y, g.p)
            den += npos * nneg
            nstrata += 1
    return (num / den if den else np.nan), nstrata


def boot(y, P, g, n_boot, pairs, seed=0):
    ug = np.unique(g)
    members = {u: np.where(g == u)[0] for u in ug}
    rng = np.random.default_rng(seed)
    res = {n: [] for n in P}
    for _ in range(n_boot):
        pick = rng.choice(ug, len(ug), replace=True)
        b = np.concatenate([members[u] for u in pick])
        yb = y[b]
        if not (0 < yb.sum() < len(yb)):
            continue
        for n in P:
            res[n].append(roc_auc_score(yb, P[n][b]))
    out = {}
    for a, r in pairs:
        d = np.array(res[a]) - np.array(res[r])
        out[(a, r)] = (d.mean(), np.percentile(d, 2.5), np.percentile(d, 97.5))
    return out


mism, checked = [], 0
indep = []
for tag in TAGS:
    col = HDR[tag]
    r = json.load(open(os.path.join(SENS, "results", tag, "oof", "results.json")))
    B = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    m, sl, pdf = r["main"], r["slices"], r["paired_diffs_common_rows"]
    # run / row counts
    runs = B.groupby("episode_id").tipped.first()
    exp = {"gekippte Läufe": f"{int(runs.sum())}/{len(runs)}"}
    night = B.split.str.startswith("night_") & ~B.split.str.startswith("night_vx")
    rows_a = night & B.tip.notna()
    exp["positive Zeilen"] = f"{int(B.tip[rows_a].sum())}/{int(rows_a.sum())}"
    assert m["clock"]["n_pos"] == int(B.tip[rows_a].sum()) and m["clock"]["n"] == int(rows_a.sum())
    for lab, k in PRED.items():
        exp[lab] = f"{m[k]['auroc']:.3f}"
        exp[lab + " (zeitgematcht)"] = f"{sl['time_matched_auroc'][k]:.3f}"
        exp[lab + " (gleiches Setup)"] = f"{sl['mixed_cfg_x_time_auroc'][k]:.3f}"
    for lab, (a, b) in DIFF.items():
        d = pdf[f"{a} - {b}|auroc"]
        exp[lab] = f"{d['mean']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]"
    for k, v in exp.items():
        checked += 1
        got = cells.get((k, col))
        if got != v:
            mism.append((tag, k, got, v))
    # ---------------- independent recomputation from preds.csv
    Pd = pd.read_csv(os.path.join(SENS, "results", tag, "oof", "preds.csv"))
    X = Pd.merge(B[["episode_id", "t", "tip", "group_id", "rounds_to_cut", "mixed"]], on=["episode_id", "t"], how="left")
    assert len(X) == int(rows_a.sum())
    y = X.tip.values.astype(float)
    pcols = [c for c in Pd.columns if c not in ("episode_id", "t")]
    common = np.all([X[c].notna().values for c in pcols], 0)
    assert common.sum() == r["rows_common"], (common.sum(), r["rows_common"])
    rtc = pd.cut(X.rounds_to_cut, [-99, -9, -5, -1, 3, 99], labels=["<=-9", "-8..-5", "-4..-1", "0..3", ">3"]).astype(str).values
    strata = (X.group_id + "|" + rtc).values
    mixed = common & (X.mixed == 1).values
    for lab, k in PRED.items():
        p = X[k].values
        ok = ~np.isnan(p)
        a_main = roc_auc_score(y[ok], p[ok])
        a_tm, _ = strat_auc(y[common], p[common], rtc[common])
        a_mx, ns = strat_auc(y[mixed], p[mixed], strata[mixed])
        indep.append({"tag": tag, "pred": k, "main_json": m[k]["auroc"], "main_re": a_main,
                      "tm_json": sl["time_matched_auroc"][k], "tm_re": a_tm,
                      "mx_json": sl["mixed_cfg_x_time_auroc"][k], "mx_re": a_mx, "mx_strata": ns})
    P = {k: X[k].values[common] for k in ("zs:pairwise", "zs:global_full", "clock", "bag+graph")}
    pairs = list(DIFF.values())
    for nb in (200, 1000):
        bo = boot(y[common], P, X.group_id.values[common], nb, pairs)
        for (a, b), (mu, lo, hi) in bo.items():
            d = pdf[f"{a} - {b}|auroc"]
            print(f"{tag} boot{nb:5d} {a:>15s} - {b}: re {mu:+.4f} [{lo:+.4f}, {hi:+.4f}]   json {d['mean']:+.4f} "
                  f"[{d['ci'][0]:+.4f}, {d['ci'][1]:+.4f}]")
print(f"\ncells checked against results.json/base: {checked}; mismatches: {len(mism)}")
for x in mism:
    print("MISMATCH", x)
I = pd.DataFrame(indep)
for c in ("main", "tm", "mx"):
    I[c + "_absdiff"] = (I[c + "_json"] - I[c + "_re"]).abs()
pd.set_option("display.width", 250)
print(I.round(4).to_string())
print("max abs diff main/tm/mx:", I.main_absdiff.max(), I.tm_absdiff.max(), I.mx_absdiff.max())
