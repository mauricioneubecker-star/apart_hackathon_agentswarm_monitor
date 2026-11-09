"""Window robustness by subgroup + private/public split of E_dir. Same MH estimator as contagion.py.

  python extra.py rows_wN.npz [privpub]
"""
import sys
from collections import defaultdict

import numpy as np

Z = np.load(sys.argv[1])
cfg, run, cat, chan = Z["cfg"], Z["run"], Z["cat"], Z["chan"]
T, STUCK, Y = Z["t"].astype(float), Z["stuck"].astype(float), Z["Y"].astype(float)
DM, DMP = Z["dm_any"], Z["dm_priv_any"]


def mh(mask, x):
    keys = np.array([f"{a}|{int(b)}|{int(c)}" for a, b, c in zip(run[mask], T[mask], STUCK[mask])])
    y, e, cg = Y[mask], x[mask].astype(float), cfg[mask]
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


def summ(acc, nboot=2000):
    rng = np.random.default_rng(0)
    M = np.array([acc[c] for c in acc])
    if len(M) == 0 or M[:, 1].sum() == 0:
        return "n/a"
    o = M[:, 0].sum() / M[:, 1].sum()
    bo = []
    for _ in range(nboot):
        Wm = M[rng.integers(0, len(M), len(M))]
        if Wm[:, 1].sum() > 0:
            bo.append(Wm[:, 0].sum() / Wm[:, 1].sum())
    return (f"{o:6.2f} [{np.percentile(bo, 2.5):.2f}; {np.percentile(bo, 97.5):.2f}] cfg {len(M)}, "
            f"exp.adopt {int(M[:, 4].sum())}")


ALL = np.ones(len(Y), bool)
K4, K2, B = cat == "K4", cat == "K2", chan == "board"
G = [("pooled", ALL), ("K2", K2), ("K4", K4), ("board", B), ("non-board", ~B), ("K2&board", K2 & B),
     ("K4&board", K4 & B), ("K2&non-board", K2 & ~B), ("K4&non-board", K4 & ~B)]
if len(sys.argv) > 2 and sys.argv[2] == "privpub":
    # share of E_dir rows that are private-DM vs public addressing, board only
    for g, m in G:
        e = Z["E_dir"][m] == 1
        print(f"{g:13s} E_dir rows {int(e.sum()):5d}: private-only {int((e & (Z['E_dir_priv'][m] == 1) & (Z['E_dir_pub'][m] == 0)).sum()):5d}"
              f"  public-only {int((e & (Z['E_dir_priv'][m] == 0) & (Z['E_dir_pub'][m] == 1)).sum()):5d}"
              f"  both {int((e & (Z['E_dir_priv'][m] == 1) & (Z['E_dir_pub'][m] == 1)).sum()):5d}")
    for g, m in G[3:]:
        print(f"\n== {g}")
        print(f"  E_dir_priv  all : {summ(mh(m, Z['E_dir_priv']))}")
        print(f"  E_dir_pub   all : {summ(mh(m, Z['E_dir_pub']))}")
        print(f"  P_dir_priv  all : {summ(mh(m, Z['P_dir_priv']))}")
        print(f"  E_dir_priv  among agents with >=1 private DM : {summ(mh(m & (DMP == 1), Z['E_dir_priv']))}")
        print(f"  P_dir_priv  among agents with >=1 private DM : {summ(mh(m & (DMP == 1), Z['P_dir_priv']))}")
        print(f"  E_dir_pub   among agents with no private DM from a violator: "
              f"{summ(mh(m & (Z['E_dir_priv'] == 0), Z['E_dir_pub']))}")
else:
    for g, m in G:
        print(f"{g:13s} E_dir all {summ(mh(m, Z['E_dir']))} | dm>0 {summ(mh(m & (DM == 1), Z['E_dir']))} | "
              f"P_dir dm>0 {summ(mh(m & (DM == 1), Z['P_dir']))}")
