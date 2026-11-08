"""Issue 7: influence of single configs, attempt-inclusive outcome, CMH / within-stratum permutation vs cluster test."""
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, fmt, load, mh_parts, signflip_cfg, summarize  # noqa: E402

runs = load()
rows = all_rows(runs)
dm = rows["dm"] == 1
u, M = mh_parts(rows, rows["E_dir"], dm)
OR = M[:, 0].sum() / M[:, 1].sum()
print(f"dm>0 E_dir: OR {OR:.3f}, informative configs {len(u)}, strata {int(M[:,5].sum())}, exposed adoptions {int(M[:,4].sum())}")
loo = np.array([np.delete(M, i, 0)[:, 0].sum() / np.delete(M, i, 0)[:, 1].sum() for i in range(len(M))])
print(f"leave-one-config-out OR range {loo.min():.3f} .. {loo.max():.3f}")
contrib = M[:, 0] - OR * M[:, 1]
order = np.argsort(-contrib)
print("top-5 by contribution num - OR*den:", [(u[i], round(contrib[i], 2)) for i in order[:5]])
for k in range(1, 8):
    keep = np.ones(len(M), bool); keep[order[:k]] = False
    s = summarize(u[keep], M[keep])
    print(f"  drop top {k}: {fmt(s)}  signflip p {signflip_cfg(M[keep]):.4f}")
# same exercise from the other side: drop the k most NEGATIVE contributors
for k in (1, 3, 5):
    keep = np.ones(len(M), bool); keep[order[::-1][:k]] = False
    print(f"  drop bottom {k}: OR {M[keep,0].sum()/M[keep,1].sum():.2f}")
# how often does dropping 5 random configs reduce OR to <= value obtained above?
rng = np.random.default_rng(3)
keep5 = np.ones(len(M), bool); keep5[order[:5]] = False
v5 = M[keep5, 0].sum() / M[keep5, 1].sum()
rnd = []
for _ in range(5000):
    kk = np.ones(len(M), bool); kk[rng.choice(len(M), 5, replace=False)] = False
    rnd.append(M[kk, 0].sum() / M[kk, 1].sum())
print(f"  drop 5 random configs: median OR {np.median(rnd):.2f}, 2.5% {np.percentile(rnd,2.5):.2f}")
# share of the excess carried by K4 configs
k4 = np.array(["-K4-" in c for c in u])
print(f"  K4 share of positive excess: {contrib[k4 & (contrib>0)].sum()/contrib[contrib>0].sum():.2f}; top-5 all K4: {all(k4[order[:5]])}")

# CMH test (no clustering) and within-stratum exposure permutation (no clustering) vs config sign-flip
for nm, sel in (("all", None), ("dm>0", dm)):
    u2, M2 = mh_parts(rows, rows["E_dir"], sel)
    O_E, V = M2[:, 6].sum(), M2[:, 7].sum()
    chi = O_E ** 2 / V
    chi_cc = (abs(O_E) - 0.5) ** 2 / V
    print(f"[{nm}] CMH chi2 {chi:.2f} p {stats.chi2.sf(chi,1):.2e} (cc p {stats.chi2.sf(chi_cc,1):.2e}); config sign-flip p {signflip_cfg(M2, 50000):.4f}")

# within-stratum permutation of exposure (keeps per-stratum exposure count), dm>0 only, 2000x
sel = dm
run_i, t, st, y, e = rows["run_i"][sel], rows["t"][sel], rows["stuck"][sel], rows["Y"][sel], rows["E_dir"][sel]
key = (run_i.astype(np.int64) * 100 + t) * 2 + st
o_ = np.argsort(key, kind="stable")
key, y, e = key[o_], y[o_], e[o_]
bounds = np.flatnonzero(np.r_[True, key[1:] != key[:-1], True])


def mh_from(y, e):
    num = den = 0.0
    for i in range(len(bounds) - 1):
        s = slice(bounds[i], bounds[i + 1])
        ys, es = y[s], e[s]
        n = len(ys)
        a = np.sum((es == 1) & (ys == 1)); b = np.sum((es == 1) & (ys == 0)); c = np.sum((es == 0) & (ys == 1)); d = n - a - b - c
        if a + b == 0 or c + d == 0 or a + c == 0:
            continue
        num += a * d / n; den += b * c / n
    return num / den


# only strata with both exposed and adopters matter; restrict for speed
inf = []
for i in range(len(bounds) - 1):
    s = slice(bounds[i], bounds[i + 1])
    if e[s].sum() > 0 and e[s].sum() < len(e[s]) and y[s].sum() > 0:
        inf.append(s)
obs = mh_from(y, e)
cnt = 0
NPERM = 2000
for _ in range(NPERM):
    e2 = e.copy()
    for s in inf:
        e2[s] = rng.permutation(e2[s])
    if mh_from(y, e2) >= obs - 1e-12:
        cnt += 1
print(f"[dm>0] within-stratum exposure permutation: observed {obs:.3f}, one-sided p {(cnt+1)/(NPERM+1):.4f}")

# attempt-inclusive outcome: Y' = first round with violation OR blocked/failed attempt (labels.json first_attempt_round)
fy = [np.minimum(o["f"], o["fatt"]) for o in runs]
n_v = sum(int(((~o["instructed"]) & (o["f"] <= o["R"])).sum()) for o in runs)
n_e = sum(int(((~o["instructed"]) & (f <= o["R"])).sum()) for o, f in zip(runs, fy))
n_att_first = sum(int(((~o["instructed"]) & (o["fatt"] < o["f"])).sum()) for o in runs)
print(f"uninstructed adopters: violation {n_v}; violation-or-attempt {n_e}; attempt strictly before first violation (or without one) {n_att_first}")
from core import run_rows  # noqa: E402
for sender_def in ("violators", "violators_or_attempters"):
    parts = []
    for i, o in enumerate(runs):
        fs = o["f"] if sender_def == "violators" else fy[i]
        r = run_rows(o, f=fs, outcome_f=fy[i])
        r["run_i"] = np.full(len(r["t"]), i); r["cfg"] = np.full(len(r["t"]), o["sid"], dtype=object)
        parts.append(r)
    R2 = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    cat = np.array([o["cat"][:2] for o in runs])[R2["run_i"]]
    print(f"--- outcome = violation-or-attempt; exposure senders = {sender_def}; rows {len(R2['Y'])} adoptions {int(R2['Y'].sum())}")
    for nm, sel in (("all", np.ones(len(R2["Y"]), bool)), ("dm>0", R2["dm"] == 1)):
        for g, gs in (("pooled", np.ones(len(R2["Y"]), bool)), ("K2", cat == "K2"), ("K4", cat == "K4")):
            u3, M3 = mh_parts(R2, R2["E_dir"], sel & gs)
            print(f"   {nm:5s} {g:6s} E_dir", fmt(summarize(u3, M3)), " signflip p", round(signflip_cfg(M3), 4))
        u3, M3 = mh_parts(R2, R2["P_dir"], sel)
        print(f"   {nm:5s} pooled P_dir", fmt(summarize(u3, M3)))
