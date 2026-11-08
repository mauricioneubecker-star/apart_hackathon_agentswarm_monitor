"""Issue 2: E_dir MH OR by category and category x discoverability, with config bootstrap, config sign-flip p,
and config-level heterogeneity tests (label permutation over configs; bootstrap of the log-OR difference)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, fmt, load, mh_parts, signflip_cfg, summarize  # noqa: E402

runs = load()
rows = all_rows(runs)
cat = np.array([o["cat"][:2] for o in runs])[rows["run_i"]]
disc = np.array([o["disc"] for o in runs])[rows["run_i"]]
dm = rows["dm"] == 1
groups = {"K2": cat == "K2", "K4": cat == "K4",
          "K2/exploration": (cat == "K2") & (disc == "exploration"), "K2/peers_only": (cat == "K2") & (disc == "peers_only"),
          "K4/exploration": (cat == "K4") & (disc == "exploration"), "K4/peers_only": (cat == "K4") & (disc == "peers_only"),
          "exploration": disc == "exploration", "peers_only": disc == "peers_only"}
for k in ("E_dir", "P_dir"):
    for nm, sel in (("all", np.ones(len(dm), bool)), ("dm>0", dm)):
        print(f"--- {k} {nm}")
        u, M = mh_parts(rows, rows[k], sel)
        print(f"  {'pooled':16s}", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
        for g, gs in groups.items():
            u, M = mh_parts(rows, rows[k], sel & gs)
            s = summarize(u, M)
            print(f"  {g:16s}", fmt(s), " signflip p", round(signflip_cfg(M), 4) if len(M) else None)

# heterogeneity: K2 vs K4 and 4-way, config-level permutation of the group labels (within nothing), E_dir
rng = np.random.default_rng(7)
cfgs = np.array(sorted({o["sid"] for o in runs}))
cfg_cat = {o["sid"]: o["cat"][:2] for o in runs}
cfg_disc = {o["sid"]: o["disc"] for o in runs}


def per_cfg(sel):
    u, M = mh_parts(rows, rows["E_dir"], sel)
    return dict(zip(u, M))


for nm, sel in (("all", np.ones(len(dm), bool)), ("dm>0", dm)):
    P = per_cfg(sel)
    keys = [c for c in cfgs if c in P]
    M = np.array([P[c] for c in keys])
    lab2 = np.array([cfg_cat[c] for c in keys])
    lab4 = np.array([cfg_cat[c] + "/" + cfg_disc[c] for c in keys])

    def lor(Mx):
        return np.log(Mx[:, 0].sum() / Mx[:, 1].sum()) if Mx[:, 1].sum() > 0 and Mx[:, 0].sum() > 0 else np.nan

    def stat2(lab):
        return lor(M[lab == "K4"]) - lor(M[lab == "K2"])

    def stat4(lab):
        v = [lor(M[lab == g]) for g in np.unique(lab4)]
        v = np.array([x for x in v if np.isfinite(x)])
        return np.var(v)

    o2, o4 = stat2(lab2), stat4(lab4)
    n2 = np.array([stat2(rng.permutation(lab2)) for _ in range(5000)])
    n4 = np.array([stat4(rng.permutation(lab4)) for _ in range(5000)])
    n2 = n2[np.isfinite(n2)]
    p2 = (np.sum(np.abs(n2) >= abs(o2)) + 1) / (len(n2) + 1)
    p4 = (np.sum(n4 >= o4) + 1) / (len(n4) + 1)
    # bootstrap of OR ratio K4/K2 within groups
    bs = []
    i2, i4 = np.flatnonzero(lab2 == "K2"), np.flatnonzero(lab2 == "K4")
    for _ in range(4000):
        a = M[rng.choice(i2, len(i2))]
        b = M[rng.choice(i4, len(i4))]
        if a[:, 1].sum() > 0 and b[:, 1].sum() > 0 and a[:, 0].sum() > 0:
            bs.append(np.log(b[:, 0].sum() / b[:, 1].sum()) - np.log(a[:, 0].sum() / a[:, 1].sum()))
    print(f"[{nm}] informative configs K2 {len(i2)} K4 {len(i4)}; OR ratio K4/K2 = {np.exp(o2):.2f} "
          f"boot95 [{np.exp(np.percentile(bs, 2.5)):.2f}, {np.exp(np.percentile(bs, 97.5)):.2f}], "
          f"label-perm p(K2 vs K4) = {p2:.4f}; 4-group var(logOR) perm p = {p4:.4f}")
    # share of the pooled MH numerator / denominator by group
    for g in np.unique(lab4):
        Mg = M[lab4 == g]
        print(f"   {g:28s} configs {len(Mg):3d}  num share {Mg[:,0].sum()/M[:,0].sum():.2f}  den share {Mg[:,1].sum()/M[:,1].sum():.2f}  exposed adoptions {int(Mg[:,4].sum())}")
