#!/usr/bin/env python3
"""Random search with successive halving over the STGNN space, scored with the harness selection score.

  python3 gnn_opt_torch/search.py --n 24 --stage1 id0 --keep 8 --stage2 all --tag rs1
Stage 1: each sampled config on the 5 folds of ID repeat 0 (pooled AUROC + AUPRC/4 as score).
Stage 2: the best `keep` configs on all 18 folds (selection score = mean(ID, LODO mean, LODO worst)).
Results append to gnn_opt_torch/preds/cv_log.jsonl; prediction files land in preds/cv/<tag>_<i>.csv.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import train as T  # noqa: E402

SPACE = {
    "conv": ["rgine", "rgine", "gine", "gatv2", "transformer"],
    "hid": [32, 64, 64, 96],
    "layers": [2, 3, 3, 4],
    "reverse": [True, True, False],
    "vn": [True, False],
    "tmem": ["none", "none", "gru", "conv3", "conv5"],
    "gtemp": ["none", "gru", "gru", "conv3", "conv5", "attn8"],
    "drop": [0.0, 0.1, 0.2, 0.3],
    "epochs": [30, 40, 60],
    "lr": [1e-3, 2e-3, 4e-3],
    "wd": [1e-5, 1e-4, 1e-3, 1e-2],
    "batch_runs": [4, 8, 16],
    "pos_weight": [1.0, 3.0, 6.0],
    "focal_gamma": [0.0, 0.0, 1.0, 2.0],
    "w_aux": [0.0, 0.5, 1.0],
    "w_risk": [0.0, 0.2, 0.5],
    "w_node": [0.0, 0.5, 1.0],
    "edge_drop": [0.0, 0.1, 0.2],
    "feat_noise": [0.0, 0.05, 0.1],
    "edge_readout": [True, True, False],
    "att_pool": [True, False],
    "aggr": [["sum", "mean", "max"], ["sum", "max"], ["mean", "max"], ["sum"]],
}


def sample(rng, base=None):
    c = {k: rng.choice(v) for k, v in SPACE.items()}
    if base:
        c.update(base)
    return c


def stage1_score(P, data):
    import pandas as pd
    from sklearn.metrics import average_precision_score, roc_auc_score
    S = pd.read_csv(os.path.join(data, "snapshots.csv"), low_memory=False)[["run", "round", "y3"]]
    Q = P.groupby(["run", "round"], as_index=False).score.mean().merge(S, on=["run", "round"])
    au, pr = roc_auc_score(Q.y3, Q.score), average_precision_score(Q.y3, Q.score)
    return au + pr / 4, au, pr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(T.REPO, "gnn_opt_data", "night"))
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--keep", type=int, default=6)
    ap.add_argument("--stage1", default="id0")
    ap.add_argument("--stage2", default="all")
    ap.add_argument("--tag", default="rs")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--base", default="{}", help="fixed keys (JSON)")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    base = json.loads(a.base)
    log = os.path.join(HERE, "preds", "search_log.jsonl")
    os.makedirs(os.path.join(HERE, "preds", "cv"), exist_ok=True)
    res = []
    for i in range(a.n):
        c = sample(rng, base)
        P, cpu = T.run_cv(a.data, c, a.stage1, a.workers)
        sc, au, pr = stage1_score(P, a.data)
        r = {"tag": a.tag, "i": i, "stage": 1, "score": sc, "auroc": au, "auprc": pr, "cpu_s": round(cpu), "cfg": c}
        print(json.dumps(r), flush=True)
        open(log, "a").write(json.dumps(r) + "\n")
        res.append(r)
    res.sort(key=lambda r: -r["score"])
    for r in res[:a.keep]:
        P, cpu = T.run_cv(a.data, r["cfg"], a.stage2, a.workers)
        name = f"{a.tag}_{r['i']}"
        P.to_csv(os.path.join(HERE, "preds", "cv", f"{name}.csv"), index=False)
        s = T.summarize(a.data, P)
        r2 = {"tag": a.tag, "i": r["i"], "stage": 2, **s, "cpu_s": round(cpu), "cfg": r["cfg"]}
        print(json.dumps(r2), flush=True)
        open(log, "a").write(json.dumps(r2) + "\n")


if __name__ == "__main__":
    main()
