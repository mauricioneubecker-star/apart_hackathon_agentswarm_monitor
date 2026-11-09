"""Reproduce contagion.json Part A exactly (incl. the shared-rng bootstrap order of contagion.py)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, load, mh_parts  # noqa: E402

w = int(sys.argv[1]) if len(sys.argv) > 1 else None
runs = load()
rows = all_rows(runs, w=w)
print("rows", len(rows["Y"]), "adoptions", int(rows["Y"].sum()), "runs", len(runs), "configs", len({o['sid'] for o in runs}))
rng = np.random.default_rng(0)


def summ(M, nboot=2000):
    if len(M) == 0 or M[:, 1].sum() == 0:
        return None
    o = M[:, 0].sum() / M[:, 1].sum()
    bo = []
    for _ in range(nboot):
        W = M[rng.integers(0, len(M), len(M))]
        if W[:, 1].sum() > 0 and W[:, 3].sum() > 0:
            bo.append(W[:, 0].sum() / W[:, 1].sum())
    return round(float(o), 4), [round(float(np.percentile(bo, 2.5)), 3), round(float(np.percentile(bo, 97.5)), 3)], len(M), int(M[:, 5].sum()), int(M[:, 4].sum())


ref = json.load(open("/Users/mauricio/sim_local/apart_vx/analysis/results/contagion.json")) if w is None else None
for k in ["E_dir", "E_any", "E_mech", "E_feed", "P_dir"]:
    x = rows[k]
    u, M = mh_parts(rows, x)
    s = summ(M)
    print(k, "all ", s, "| ref", None if ref is None or ref["mh"][k] is None else (round(ref["mh"][k]["OR"], 4), [round(v, 3) for v in ref["mh"][k]["OR_ci"]]))
    if k in ("E_dir", "E_mech", "P_dir"):
        u, M = mh_parts(rows, x, rows["dm"] == 1)
        s = summ(M)
        print(k, "dm>0", s, "| ref", None if ref is None else (round(ref["mh_dm>0"][k]["OR"], 4), [round(v, 3) for v in ref["mh_dm>0"][k]["OR_ci"]]))
