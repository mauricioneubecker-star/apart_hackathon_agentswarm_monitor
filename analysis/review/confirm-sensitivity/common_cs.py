"""Shared loader for the sensitivity re-checks (read-only on all inputs)."""
import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

SENS = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/sens"
TAGS = ["t8d3", "t6d3", "t10d3", "t8d2", "t8d5"]


def load(tag):
    B = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    P = pd.read_csv(os.path.join(SENS, "results", tag, "oof", "preds.csv"))
    R = json.load(open(os.path.join(SENS, "results", tag, "oof", "results.json")))
    night = B.split.str.startswith("night_") & ~B.split.str.startswith("night_vx")
    yok = B.tip.notna()
    rows_a = (night & yok).values
    Ba = B[rows_a].reset_index(drop=True)
    assert len(Ba) == len(P), (len(Ba), len(P))
    assert (Ba.episode_id.values == P.episode_id.values).all() and (Ba.t.values == P.t.values).all()
    names = [c for c in P.columns if c not in ("episode_id", "t")]
    common = np.all([P[n].notna().values for n in names], 0)
    D = pd.concat([Ba, P[names]], axis=1)[common].reset_index(drop=True)
    return D, names, R


def stratified_auroc(y, p, strata):
    df = pd.DataFrame({"y": y, "p": p, "s": strata}).dropna()
    num = den = 0.0
    for _, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            w = npos * nneg
            num += w * roc_auc_score(g.y, g.p)
            den += w
    return float(num / den) if den else float("nan")


def rtc_bin(rtc):
    return pd.cut(rtc, [-99, -9, -5, -1, 3, 99], labels=["<=-9", "-8..-5", "-4..-1", "0..3", ">3"]).astype(str)


def bootstrap(D, names, n_boot, seed=0, unit="group_id", diffs=(), extra_rows=None):
    """Clone of llm_monitor.evaluate.bootstrap on the rows of D."""
    g = D[unit].values
    ug = np.unique(g)
    members = {u: np.where(g == u)[0] for u in ug}
    rng = np.random.default_rng(seed)
    y = D.tip.values.astype(float)
    res = {n: [] for n in names}
    for _ in range(n_boot):
        pick = rng.choice(ug, len(ug), replace=True)
        b = np.concatenate([members[u] for u in pick])
        yb = y[b]
        if not (0 < yb.sum() < len(yb)):
            continue
        for n in names:
            res[n].append(roc_auc_score(yb, D[n].values[b]))
    out = {}
    for a, r in diffs:
        d = np.array(res[a]) - np.array(res[r])
        out[f"{a} - {r}"] = (float(d.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)),
                             float((d <= 0).mean()))
    ci = {n: (float(np.percentile(res[n], 2.5)), float(np.percentile(res[n], 97.5))) for n in names}
    return out, ci
