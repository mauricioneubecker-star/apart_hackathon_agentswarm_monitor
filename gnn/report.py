"""Summarize <out>/results.jsonl: mean ± std over seeds per arm, plus bootstrap CIs over groups (configurations /
games) for seed-averaged test predictions.

Usage: python -m gnn.report results/amx_phase1 [--splits val,test_id] [--level graph,node] [--boot 1000]
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .metrics import get


def load_results(out):
    rows = [json.loads(l) for l in open(os.path.join(out, "results.jsonl")) if l.strip()]
    seen, uniq = set(), []
    for r in rows[::-1]:   # keep the last result per run_id
        if r["run_id"] not in seen:
            seen.add(r["run_id"]), uniq.append(r)
    return uniq[::-1]


def table(rows, splits, levels, metrics=("auprc", "auroc", "recall_at_5fpr")):
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    out = []
    for arm, rs in by_arm.items():
        line = {"arm": arm, "n_seeds": len(rs), "secs": np.mean([r["secs"] for r in rs])}
        for s in splits:
            for lv in levels:
                for m in metrics:
                    v = [get(r["metrics"], s, f"{lv}.{m}") for r in rs]
                    v = [x for x in v if x == x]
                    if v:
                        line[f"{s}/{lv}/{m}"] = f"{np.mean(v):.3f} ± {np.std(v):.3f}"
                prev = [get(r["metrics"], s, f"{lv}.prevalence") for r in rs]
                prev = [x for x in prev if x == x]
                if prev:
                    line[f"{s}/{lv}/prev"] = f"{prev[0]:.3f}"
            mae = [get(r["metrics"], s, "count.mae") for r in rs]
            mae = [x for x in mae if x == x]
            if mae:
                line[f"{s}/count/mae"] = f"{np.mean(mae):.3f} ± {np.std(mae):.3f}"
        out.append(line)
    return pd.DataFrame(out)


def bootstrap(out, rows, split, level, n_boot=1000, seed=0):
    """Seed-averaged predictions per arm; resample groups with replacement."""
    rng = np.random.default_rng(seed)
    by_arm = defaultdict(list)
    for r in rows:
        f = os.path.join(out, "preds", f"{r['run_id']}_{level}.csv.gz")
        if os.path.exists(f):
            by_arm[r["arm"]].append(f)
    res = []
    for arm, files in by_arm.items():
        dfs = [pd.read_csv(f) for f in files]
        key = ["episode_id", "t"] + (["sid"] if level == "node" else [])
        ycol, pcol = ("y_graph", "p_graph") if level == "graph" else ("y", "p")
        if pcol not in dfs[0]:
            continue
        df = dfs[0][dfs[0].split == split].copy()
        if level == "node":
            df["_k"] = np.arange(len(df))
            ps = [d[d.split == split][pcol].values for d in dfs]
        else:
            ps = [d[d.split == split].set_index(["episode_id", "t"]).loc[
                df.set_index(["episode_id", "t"]).index][pcol].values for d in dfs]
        df["p_avg"] = np.mean(ps, 0)
        df = df[df[ycol].notna()]
        if df[ycol].nunique() < 2:
            continue
        groups = df.group_id.unique()
        idx = df.groupby("group_id").indices
        ap, au = [], []
        for _ in range(n_boot):
            g = rng.choice(groups, len(groups), replace=True)
            ii = np.concatenate([idx[x] for x in g])
            y, p = df[ycol].values[ii], df.p_avg.values[ii]
            if 0 < y.sum() < len(y):
                ap.append(average_precision_score(y, p)), au.append(roc_auc_score(y, p))
        res.append({"arm": arm, "split": split, "level": level, "n_seeds": len(files),
                    "auprc": average_precision_score(df[ycol], df.p_avg),
                    "auprc_ci": f"[{np.percentile(ap, 2.5):.3f}, {np.percentile(ap, 97.5):.3f}]",
                    "auroc": roc_auc_score(df[ycol], df.p_avg),
                    "auroc_ci": f"[{np.percentile(au, 2.5):.3f}, {np.percentile(au, 97.5):.3f}]",
                    "n_groups": len(groups)})
    return pd.DataFrame(res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--splits", default="val,test_id")
    ap.add_argument("--level", default="graph,node")
    ap.add_argument("--boot", type=int, default=0, help="bootstrap reps on the last split (0 = off)")
    ap.add_argument("--md", help="write markdown to this file")
    a = ap.parse_args()
    rows = load_results(a.out)
    splits, levels = a.splits.split(","), a.level.split(",")
    T = table(rows, splits, levels)
    txt = T.to_markdown(index=False) if hasattr(T, "to_markdown") else T.to_string(index=False)
    try:
        txt = T.to_markdown(index=False)
    except ImportError:
        txt = T.to_string(index=False)
    print(txt)
    if a.boot:
        for lv in levels:
            B = bootstrap(a.out, rows, splits[-1], lv, a.boot)
            if len(B):
                print(f"\nBootstrap over groups, {splits[-1]}, {lv}:")
                print(B.round(3).to_string(index=False))
    if a.md:
        open(a.md, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
