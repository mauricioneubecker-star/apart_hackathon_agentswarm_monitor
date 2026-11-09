"""Heterogeneity checks on rows from build_rows.py.

1. Per-config MH contributions (same estimator as contagion.py). Group ORs are ratios of summed contributions, so a
   joint bootstrap over all configs gives the ratio of two group ORs, and permuting the group label across configs
   (optionally within channel or within category) gives a permutation null for that ratio.
2. Board: private DM (channel == dm) vs public addressing (@mention / reply in a board post) from violators.

  python contrasts.py rows_w3.npz
"""
import sys
from collections import defaultdict

import numpy as np

Z = np.load(sys.argv[1])
cfg, run, cat, chan = Z["cfg"], Z["run"], Z["cat"], Z["chan"]
T, STUCK, Y = Z["t"].astype(float), Z["stuck"].astype(float), Z["Y"].astype(float)
DM = Z["dm_any"]


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


ucfg = np.array(sorted(set(cfg)))
cfg_cat = {c: cat[cfg == c][0] for c in ucfg}
cfg_chan = {c: chan[cfg == c][0] for c in ucfg}


def table(acc):
    """112 x 2 array of (OR numerator, OR denominator) per config, zeros for uninformative configs."""
    return np.array([acc[c][:2] if c in acc else [0.0, 0.0] for c in ucfg])


def orr(M, g):
    d = M[g, 1].sum()
    return M[g, 0].sum() / d if d > 0 else np.nan


def contrast(M, gA, gB, label, nboot=4000, nperm=10000, perm_within=None):
    rng = np.random.default_rng(1)
    oa, ob = orr(M, gA), orr(M, gB)
    rat = oa / ob
    bs = []
    for _ in range(nboot):
        idx = rng.integers(0, len(ucfg), len(ucfg))
        Mb, ga, gb = M[idx], gA[idx], gB[idx]
        ra, rb = orr(Mb, ga), orr(Mb, gb)
        if np.isfinite(ra) and np.isfinite(rb) and rb > 0 and ra > 0:
            bs.append(ra / rb)
    bs = np.array(bs)
    # permutation: shuffle membership of A vs B among the configs that are in A or B (within blocks if given)
    inAB = gA | gB
    blocks = np.array([perm_within(c) for c in ucfg]) if perm_within else np.zeros(len(ucfg))
    lr_obs = abs(np.log(rat))
    ge = 0; tot = 0
    for _ in range(nperm):
        pa = gA.copy()
        for b in np.unique(blocks[inAB]):
            sel = np.flatnonzero(inAB & (blocks == b))
            pa[sel] = rng.permutation(gA[sel])
        pb = inAB & ~pa
        ra, rb = orr(M, pa), orr(M, pb)
        if not (np.isfinite(ra) and np.isfinite(rb) and ra > 0 and rb > 0):
            continue
        tot += 1
        ge += abs(np.log(ra / rb)) >= lr_obs - 1e-12
    print(f"  {label:58s} OR_A {oa:5.2f}  OR_B {ob:5.2f}  ratio {rat:5.2f} [{np.percentile(bs, 2.5):.2f}; "
          f"{np.percentile(bs, 97.5):.2f}]  perm p {(ge + 1) / (tot + 1):.4f} ({tot} valid perms)")


isK4 = np.array([cfg_cat[c] == "K4" for c in ucfg])
isBoard = np.array([cfg_chan[c] == "board" for c in ucfg])
ALL = np.ones(len(Y), bool)
for spec, mask in (("all at-risk rows", ALL), ("dm>0 (primary in ANALYSIS_PLAN)", DM == 1)):
    print(f"\n### {spec}")
    for k in ("E_dir", "E_mech", "P_dir"):
        M = table(mh(mask, Z[k]))
        contrast(M, isK4, ~isK4, f"{k}: K4 / K2 (perm unrestricted)")
        contrast(M, isK4, ~isK4, f"{k}: K4 / K2 (perm within channel)", perm_within=lambda c: cfg_chan[c])
        contrast(M, ~isBoard, isBoard, f"{k}: non-board / board (perm unrestricted)")
        contrast(M, ~isBoard, isBoard, f"{k}: non-board / board (perm within category)",
                 perm_within=lambda c: cfg_cat[c])
        contrast(M, isK4 & isBoard, ~isK4 & isBoard, f"{k}: K4-board / K2-board")
    # E_dir vs placebo on the same configs: joint bootstrap of the two ORs within a group
    Me, Mp = table(mh(mask, Z["E_dir"])), table(mh(mask, Z["P_dir"]))
    rng = np.random.default_rng(2)
    for gname, g in (("pooled", np.ones(len(ucfg), bool)), ("board", isBoard), ("K4-board", isK4 & isBoard),
                     ("K2-board", ~isK4 & isBoard), ("non-board", ~isBoard), ("K4", isK4), ("K2", ~isK4)):
        idx_g = np.flatnonzero(g)
        bs = []
        for _ in range(4000):
            idx = rng.choice(idx_g, len(idx_g))
            re_, rp = orr(Me, idx), orr(Mp, idx)
            if np.isfinite(re_) and np.isfinite(rp) and rp > 0 and re_ > 0:
                bs.append(re_ / rp)
        print(f"  E_dir / P_dir within {gname:9s}: {orr(Me, idx_g):5.2f} / {orr(Mp, idx_g):5.2f} = "
              f"{orr(Me, idx_g) / orr(Mp, idx_g):5.2f} [{np.percentile(bs, 2.5):.2f}; {np.percentile(bs, 97.5):.2f}]")
