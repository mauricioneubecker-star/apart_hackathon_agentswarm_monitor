"""Issue 1 follow-up: is the observed placebo (dm>0) below its null only because its reference group contains
E_dir-exposed rows (which adopt more)? Compare P_dir among E_dir=0 rows against the same nulls."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, fmt, load, mh_or, mh_parts, summarize  # noqa: E402

runs = load()
rng = np.random.default_rng(2024)


def draw_shuffle():
    out = []
    for o in runs:
        f = o["f"].copy()
        for s in (0, 1):
            idx = np.flatnonzero((~o["instructed"]) & (o["stuck"] == s) & (o["f"] < 99))
            if len(idx) > 1:
                f[idx] = f[rng.permutation(idx)]
        out.append(f)
    return out


haz = []
for o in runs:
    R, f, ins, st = o["R"], o["f"], o["instructed"], o["stuck"]
    h = np.zeros((2, R + 2))
    for s in (0, 1):
        m = (~ins) & (st == s)
        for t in range(1, R + 1):
            atr = m & (f >= t)
            if atr.sum():
                h[s, t] = ((f == t) & m).sum() / atr.sum()
    haz.append(h)


def draw_iid():
    out = []
    for o, h in zip(runs, haz):
        f = o["f"].copy()
        for a in np.flatnonzero(~o["instructed"]):
            s = int(o["stuck"][a])
            u = rng.random(o["R"] + 1)
            hit = [t for t in range(1, o["R"] + 1) if u[t] < h[s, t]]
            f[a] = hit[0] if hit else 99
        out.append(f)
    return out


def st(rows):
    dm = rows["dm"] == 1
    e0 = rows["E_dir"] == 0
    return [mh_or(rows, rows["P_dir"], dm), mh_or(rows, rows["P_dir"], dm & e0), mh_or(rows, rows["P_dir"], e0)]


rows = all_rows(runs)
obs = st(rows)
u, M = mh_parts(rows, rows["P_dir"], (rows["dm"] == 1) & (rows["E_dir"] == 0))
print("observed P_dir dm>0:", round(obs[0], 3), "| P_dir dm>0 & E_dir=0:", fmt(summarize(u, M)), "| P_dir all & E_dir=0:", round(obs[2], 3))
for name, gen, n in (("shuffle", draw_shuffle, 400), ("iid", draw_iid, 200)):
    S = np.array([st(all_rows(runs, f_over=gen())) for _ in range(n)])
    for j, lab in enumerate(("P dm>0", "P dm>0 & E=0", "P all & E=0")):
        v = S[:, j][np.isfinite(S[:, j])]
        print(f"  {name:8s} {lab:13s} obs {obs[j]:.3f} null median {np.median(v):.3f} [{np.percentile(v,2.5):.3f}, {np.percentile(v,97.5):.3f}] p(<=obs) {(np.sum(v<=obs[j])+1)/(len(v)+1):.4f}")
