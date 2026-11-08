#!/usr/bin/env python3
"""Random search with successive halving over the STGNN space, scored with the harness selection score.

  python3 gnn_opt_torch/search.py --n 36 --keep 12 --keep2 4 --tag rs1 --base '{"conv": "rgine"}' --space local
Stage 1: each sampled config on the 5 folds of ID repeat 0 (pooled AUROC + AUPRC/4 as score).
Stage 2: the best `keep` configs on all 18 folds (selection score = mean(ID, LODO mean, LODO worst); AUPRC breaks
         ties).
Stage 3 (keep2 > 0): the best `keep2` stage-2 configs again on all 18 folds with another seed; ranked by the mean
         selection score of both seeds (the stage-2 differences are within seed noise otherwise).
Every stage runs as one job queue over all workers (queue_cv.run_queue). Summaries append to
preds/search_log.jsonl; prediction files land in preds/cv/<tag>_<i>[_s<seed>].csv.
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
from queue_cv import run_queue  # noqa: E402

SPACES = {
    # broad architecture + training space
    "wide": {
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
    },
    # optimisation / capacity / regularisation around a fixed architecture (--base)
    "local": {
        "hid": [32, 48, 64, 96],
        "layers": [2, 3, 4],
        "drop": [0.0, 0.1, 0.2, 0.3],
        "epochs": [20, 30, 40, 60],
        "lr": [5e-4, 1e-3, 2e-3, 4e-3],
        "wd": [1e-5, 1e-4, 1e-3, 1e-2, 5e-2],
        "batch_runs": [4, 8, 16],
        "edge_drop": [0.0, 0.1, 0.2],
        "feat_noise": [0.0, 0.05, 0.1],
    },
}


def sample(rng, space, base=None):
    c = {k: rng.choice(v) for k, v in space.items()}
    if base:
        c.update(base)
    return c


def rank_key(s):
    return (round(s.get("select", s.get("id_auroc", 0)), 3), s.get("id_auprc", 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(T.REPO, "gnn_opt_data", "night"))
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--keep", type=int, default=8)
    ap.add_argument("--keep2", type=int, default=0)
    ap.add_argument("--stage1", default="id0")
    ap.add_argument("--stage2", default="all")
    ap.add_argument("--tag", default="rs")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--space", default="wide", choices=sorted(SPACES))
    ap.add_argument("--base", default="{}", help="fixed keys (JSON), override sampled ones")
    ap.add_argument("--extra", default=None, help="JSONL of extra stage-1 candidates ({name?, cfg})")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    base = json.loads(a.base)
    log = os.path.join(HERE, "preds", "search_log.jsonl")
    cands = [{"name": f"{a.tag}_{i}", "cfg": sample(rng, SPACES[a.space], base)} for i in range(a.n)]
    if a.extra:
        for j, l in enumerate(x for x in open(a.extra) if x.strip()):
            e = json.loads(l)
            cands.append({"name": e.get("name", f"{a.tag}_x{j}"), "cfg": {**e["cfg"], **base}})
    # stage 1
    r1 = run_queue([{**c, "name": c["name"] + "__s1"} for c in cands], a.stage1, a.workers, a.data, log=log)
    sc1 = []
    for c in cands:
        s = r1.get(c["name"] + "__s1")
        if s:
            sc1.append((s["id_auroc"] + s["id_auprc"] / 4, c))
    sc1.sort(key=lambda x: -x[0])
    top = [c for _, c in sc1[:a.keep]]
    print("stage 2:", [c["name"] for c in top], flush=True)
    r2 = run_queue(top, a.stage2, a.workers, a.data, log=log)
    ranked = sorted(top, key=lambda c: rank_key(r2.get(c["name"], {})), reverse=True)
    if a.keep2 > 0:
        top2 = ranked[:a.keep2]
        r3 = run_queue([{**c, "name": c["name"] + "_s1", "seed": 100} for c in top2], a.stage2, a.workers, a.data,
                       log=log)
        mean_sel = {c["name"]: (r2[c["name"]]["select"] + r3[c["name"] + "_s1"]["select"]) / 2 for c in top2}
        ranked = sorted(top2, key=lambda c: -mean_sel[c["name"]])
        for c in ranked:
            print(json.dumps({"name": c["name"], "mean_select_2seeds": round(mean_sel[c["name"]], 4),
                              "cfg": c["cfg"]}), flush=True)
    print("best:", json.dumps(ranked[0]), flush=True)


if __name__ == "__main__":
    main()
