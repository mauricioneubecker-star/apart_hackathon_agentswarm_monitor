#!/usr/bin/env python3
"""Random search with successive halving over the STGNN space, scored with the harness selection score.

  python3 gnn_opt_torch/search.py --n 14 --keep 6 --keep2 3 --tag rs1 --space local \
      --base '{"conv": "rgine", "gtemp": "gru", "edge_readout": false}' --extra experiments/search_extra.jsonl
Stage 1: every candidate on ID repeat 0 + the 8 LODO folds (13 of the 18 harness folds): selection score with the ID
         term from repeat 0 only. LODO is in stage 1 on purpose: the id0 screen cannot see the domain-shift failures
         (e.g. hold_K4), which dominate the selection score.
Stage 2: the best `keep` configs also on ID repeat 1 (the 5 missing folds); the stage-1 predictions are reused, so
         the result is the full 18-fold CV file -> exact harness selection score (AUPRC breaks ties).
Stage 3 (keep2 > 0): the best `keep2` again on all 18 folds with another seed; ranked by the mean selection score of
         both seeds (single-seed differences of ~0.02 are within seed noise here).
Every stage runs as one job queue over all workers (queue_cv.run_queue). Summaries append to preds/search_log.jsonl;
full CV files land in preds/cv/<tag>_<i>.csv (seed 2: <tag>_<i>_s1.csv; stage-1 partial files: <name>__s1.csv).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

import pandas as pd

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
    # optimisation / capacity / regularisation (incl. domain-transfer regularisers) around a fixed architecture
    "local": {
        "hid": [32, 48, 64, 96],
        "layers": [2, 3, 4],
        "drop": [0.0, 0.1, 0.2, 0.3],
        "epochs": [20, 30, 40],
        "lr": [5e-4, 1e-3, 2e-3, 4e-3],
        "wd": [1e-5, 1e-4, 1e-3, 1e-2, 5e-2],
        "batch_runs": [4, 8, 16],
        "edge_drop": [0.0, 0.1, 0.2],
        "feat_noise": [0.0, 0.05, 0.1],
        "w_risk": [0.2, 0.5],
        "crop": [0, 0, 5, 10],
        "swa": [0, 1],
    },
}


def sample(rng, space, base=None):
    c = {k: rng.choice(v) for k, v in space.items()}
    if base:
        c.update(base)
    return c


def stage1_score(s):
    """Selection score on id0 + LODO (ID term from repeat 0 only)."""
    return s["select"] if s.get("select") == s.get("select") else -1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(T.REPO, "gnn_opt_data", "night"))
    ap.add_argument("--n", type=int, default=14)
    ap.add_argument("--keep", type=int, default=6)
    ap.add_argument("--keep2", type=int, default=3)
    ap.add_argument("--tag", default="rs")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--mps", type=int, default=0)
    ap.add_argument("--space", default="local", choices=sorted(SPACES))
    ap.add_argument("--base", default="{}", help="fixed keys (JSON), override sampled ones")
    ap.add_argument("--extra", default=None, help="JSONL of extra candidates ({name?, cfg}); --base not applied")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    base = json.loads(a.base)
    log = os.path.join(HERE, "preds", "search_log.jsonl")
    cvd = os.path.join(HERE, "preds", "cv")
    cands = [{"name": f"{a.tag}_{i}", "cfg": sample(rng, SPACES[a.space], base)} for i in range(a.n)]
    if a.extra:
        for j, l in enumerate(x for x in open(a.extra) if x.strip()):
            e = json.loads(l)
            cands.append({"name": e.get("name", f"{a.tag}_x{j}"), "cfg": e["cfg"]})
    kw = dict(workers=a.workers, data=a.data, log=log, mps=a.mps)
    # stage 1: id0 + LODO
    r1 = run_queue([{**c, "name": c["name"] + "__s1"} for c in cands], "id0+lodo", **kw)
    for c in cands:   # resumed runs: summary from the existing partial file
        if c["name"] + "__s1" not in r1 and os.path.exists(os.path.join(cvd, c["name"] + "__s1.csv")):
            r1[c["name"] + "__s1"] = T.summarize(a.data, pd.read_csv(os.path.join(cvd, c["name"] + "__s1.csv")))
    ranked1 = sorted([c for c in cands if c["name"] + "__s1" in r1],
                     key=lambda c: -stage1_score(r1[c["name"] + "__s1"]))
    top = ranked1[:a.keep]
    print("stage 2:", [c["name"] for c in top], flush=True)
    # stage 2: ID repeat 1, merged with the stage-1 folds -> full 18-fold CV file
    run_queue([{**c, "name": c["name"] + "__id1"} for c in top], "id1", **kw)
    r2 = {}
    for c in top:
        P = pd.concat([pd.read_csv(os.path.join(cvd, c["name"] + s + ".csv")) for s in ("__s1", "__id1")])
        P.to_csv(os.path.join(cvd, c["name"] + ".csv"), index=False)
        r2[c["name"]] = s = T.summarize(a.data, P)
        rec = {"tag": a.tag, "stage": 2, "name": c["name"], "cv": "all", **s, "cfg": c["cfg"]}
        print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items()}), flush=True)
        open(log, "a").write(json.dumps(rec) + "\n")
    ranked = sorted(top, key=lambda c: (round(r2[c["name"]]["select"], 3), r2[c["name"]]["id_auprc"]), reverse=True)
    if a.keep2 > 0:
        top2 = ranked[:a.keep2]
        r3 = run_queue([{**c, "name": c["name"] + "_s1", "seed": 100} for c in top2], "all", **kw)
        for c in top2:
            n2 = c["name"] + "_s1"
            if n2 not in r3:
                r3[n2] = T.summarize(a.data, pd.read_csv(os.path.join(cvd, n2 + ".csv")))
        mean_sel = {c["name"]: (r2[c["name"]]["select"] + r3[c["name"] + "_s1"]["select"]) / 2 for c in top2}
        ranked = sorted(top2, key=lambda c: -mean_sel[c["name"]])
        for c in ranked:
            rec = {"tag": a.tag, "stage": 3, "name": c["name"], "mean_select_2seeds": mean_sel[c["name"]],
                   "cfg": c["cfg"]}
            print(json.dumps(rec), flush=True)
            open(log, "a").write(json.dumps(rec) + "\n")
    print("best:", json.dumps(ranked[0]), flush=True)


if __name__ == "__main__":
    main()
