"""Subgroup Mantel-Haenszel on rows from build_rows.py, same estimator as contagion.py (strata run|t|stuck,
per-config accumulation, bootstrap over configs). Each summary uses its own rng(0) so numbers are reproducible.

  python mh_sub.py rows_w3.npz
"""
import sys
from collections import defaultdict

import numpy as np

Z = np.load(sys.argv[1])
cfg, run, cat, chan = Z["cfg"], Z["run"], Z["cat"], Z["chan"]
T, STUCK, Y = Z["t"].astype(float), Z["stuck"].astype(float), Z["Y"].astype(float)
X = {k: Z[k].astype(float) for k in ("E_dir", "E_any", "E_mech", "P_dir", "E_dir_priv", "E_dir_pub", "P_dir_priv",
                                      "E_bc")}
DM = Z["dm_any"]
DMP = Z["dm_priv_any"]
NB = 2000


def mh(mask, x):
    keys = np.array([f"{a}|{int(b)}|{int(c)}" for a, b, c in zip(run[mask], T[mask], STUCK[mask])])
    y, e, cg = Y[mask], x[mask], cfg[mask]
    order = np.argsort(keys, kind="stable")
    keys, y, e, cg = keys[order], y[order], e[order], cg[order]
    bounds = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1], True])
    acc = defaultdict(lambda: np.zeros(6))
    for i in range(len(bounds) - 1):
        s = slice(bounds[i], bounds[i + 1])
        ys, es = y[s], e[s]
        n = len(ys)
        a_ = np.sum((es == 1) & (ys == 1)); b_ = np.sum((es == 1) & (ys == 0))
        c_ = np.sum((es == 0) & (ys == 1)); d_ = np.sum((es == 0) & (ys == 0))
        if (a_ + b_) == 0 or (c_ + d_) == 0 or (a_ + c_) == 0:
            continue
        v = acc[cg[s][0]]
        v += [a_ * d_ / n, b_ * c_ / n, a_ * (c_ + d_) / n, c_ * (a_ + b_) / n, a_, 1]
    return acc


def summarize(acc, nboot=NB, seed=0):
    rng = np.random.default_rng(seed)
    cf = list(acc)
    M = np.array([acc[c] for c in cf])
    if len(M) == 0 or M[:, 1].sum() == 0:
        return None
    o = M[:, 0].sum() / M[:, 1].sum()
    bo = []
    for _ in range(nboot):
        Wm = M[rng.integers(0, len(M), len(M))]
        if Wm[:, 1].sum() > 0:
            bo.append(Wm[:, 0].sum() / Wm[:, 1].sum())
    bo = np.array(bo)
    return {"OR": o, "lo": np.percentile(bo, 2.5), "hi": np.percentile(bo, 97.5), "cf": len(cf),
            "strata": int(M[:, 5].sum()), "exp_adopt": int(M[:, 4].sum()), "inf_boot": int(np.isinf(bo).sum())}


def fmt(s):
    if s is None:
        return "n/a"
    return (f"{s['OR']:.2f} [{s['lo']:.2f}; {s['hi']:.2f}]  configs {s['cf']}, strata {s['strata']}, "
            f"exposed adoptions {s['exp_adopt']}" + (f", inf-boot {s['inf_boot']}" if s['inf_boot'] else ""))


ALL = np.ones(len(Y), bool)
K4 = cat == "K4"
K2 = cat == "K2"
BOARD = chan == "board"
TEAM = chan == "team_channels"
DMO = chan == "dm_only"
groups = [("pooled", ALL), ("K2", K2), ("K4", K4), ("board", BOARD), ("team_channels", TEAM), ("dm_only", DMO),
          ("non-board", ~BOARD), ("K2&board", K2 & BOARD), ("K4&board", K4 & BOARD), ("K2&non-board", K2 & ~BOARD),
          ("K4&non-board", K4 & ~BOARD), ("K2&team", K2 & TEAM), ("K4&team", K4 & TEAM), ("K2&dm_only", K2 & DMO),
          ("K4&dm_only", K4 & DMO)]
print(f"rows {len(Y)} adoptions {int(Y.sum())}")
for g, m in groups:
    print(f"\n== {g}: rows {int(m.sum())}, adoptions {int(Y[m].sum())}, configs {len(set(cfg[m]))}, "
          f"runs {len(set(run[m]))}")
    for k in ("E_dir", "E_mech", "P_dir", "E_any"):
        print(f"  {k:7s} all    : {fmt(summarize(mh(m, X[k])))}")
        if k != "E_any":
            print(f"  {k:7s} dm>0   : {fmt(summarize(mh(m & (DM == 1), X[k])))}")
