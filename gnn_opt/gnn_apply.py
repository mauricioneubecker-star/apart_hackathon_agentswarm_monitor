"""Apply saved numpy-GNN weights (weights/<name>.npz from run_gnn.py --final) to any dataset directory."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import train as TR
from model import Monitor, sigmoid


def apply(npz_path, data_dir):
    z = np.load(npz_path, allow_pickle=False)
    cfg = json.loads(str(z["cfg"]))
    D = TR.Data(data_dir, cfg.get("feats", "gen"))
    D.mu_n, D.sd_n, D.mu_e, D.sd_e = z["mu_n"], z["sd_n"], z["mu_e"], z["sd_e"]
    D._cache = {}
    keys = sorted({k.split("/")[0] for k in z.files if "/" in k})
    runs = D.runs
    scores, counts = [], []
    mcfg = {k: v for k, v in cfg.items() if k not in ("seeds", "feats", "target")}
    for key in keys:
        m = Monitor(D.fn, D.fe, mcfg)
        m.load_state_dict({k.split("/", 1)[1]: z[k] for k in z.files if k.startswith(key + "/")})
        m.snapshots = []
        P = TR.predict(D, m, runs)
        scores.append(P.score.values)
        counts.append(P["count"].values)
    P = P[["snap"]].copy()
    P["score"] = np.mean(scores, 0)
    P["count"] = np.mean(counts, 0)
    P = P.merge(D.S[["snap", "run", "round"]], on="snap")
    return P[["run", "round", "score", "count"]]
