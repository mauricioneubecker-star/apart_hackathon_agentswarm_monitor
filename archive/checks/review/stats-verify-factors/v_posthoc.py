"""Post-hoc channel contrasts, discoverability x category interaction, ICC, freeze statistic sensitivity."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v_tests_lib import perm_test, boot_diff, holm, perm_labels  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = pd.read_csv(os.path.join(HERE, "v_configs.csv"))
runs = pd.read_csv(os.path.join(HERE, "v_runs.csv"))
B = 50000
BB = 10000
res = {}

# ---- post-hoc pairwise channel contrasts (subset to the 2 levels, permute within block)
pc = {}
for i, (a, b) in enumerate([("board", "dm_only"), ("board", "team_channels"), ("team_channels", "dm_only")]):
    d = cfg[cfg["channels"].isin([a, b])]
    y = d["rate"].to_numpy(float)
    bl = d["split"].to_numpy()
    codes = (d["channels"] == a).astype(np.int16).to_numpy()   # 1 = a
    t0, p = perm_test(y, codes, bl, 2, B, seed=300 + i)
    ci, _ = boot_diff(y, codes, bl, 1, 0, BB, seed=400 + i)
    pc[f"{a}-vs-{b}"] = dict(n=int(len(d)), diff=t0, p=p, ci=list(map(float, ci)))
h = holm({k: v["p"] for k, v in pc.items()})
for k, v in pc.items():
    v["holm"] = h[k]
    print(f"{k:28s} n={v['n']:3d} diff={100*v['diff']:+.1f} [{100*v['ci'][0]:+.1f}, {100*v['ci'][1]:+.1f}] p={v['p']:.5f} holm={v['holm']:.4f}")
res["channels_posthoc"] = pc

# board - dm_only CI on the full 112 (as in their main table)
y = cfg["rate"].to_numpy(float)
bl = cfg["split"].to_numpy()
codes = np.array([["board", "team_channels", "dm_only"].index(v) for v in cfg["channels"]], dtype=np.int16)
ci, _ = boot_diff(y, codes, bl, 0, 2, BB, seed=499)
print(f"board - dm_only on 112 configs bootstrap: [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]")

# ---- discoverability x category cells and DiD
cfg["expl"] = (cfg["discoverability"] == "exploration").astype(int)
cfg["k4"] = (cfg["cat"] == "K4").astype(int)
cells = cfg.groupby(["expl", "k4"])["rate"].agg(["mean", "size"])
print(cells)
# run-level rate in the K4 x exploration cell
rc = runs[runs["is_control"]].copy()
rc["expl"] = (rc["discoverability"] == "exploration").astype(int)
rc["k4"] = (rc["category"].str[:2] == "K4").astype(int)
print("run-level K4+expl:", rc[(rc.expl == 1) & (rc.k4 == 1)]["tipped"].mean())
# subgroup tests
for name, mask, fac in [("disc | K2", cfg.k4 == 0, "expl"), ("disc | K4", cfg.k4 == 1, "expl"),
                        ("cat | peers", cfg.expl == 0, "k4"), ("cat | expl", cfg.expl == 1, "k4")]:
    d = cfg[mask]
    yy = d["rate"].to_numpy(float)
    bb = d["split"].to_numpy()
    cc = d[fac].to_numpy().astype(np.int16)
    t0, p = perm_test(yy, cc, bb, 2, B, seed=hash(name) % 10000)
    ci, _ = boot_diff(yy, cc, bb, 1, 0, BB, seed=hash(name) % 10000 + 1)
    print(f"{name:12s} n={len(d)} diff={100*t0:+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}] p={p:.5f}")
    res[name] = dict(n=int(len(d)), diff=t0, p=p, ci=list(map(float, ci)))

# DiD bootstrap (stratified by block)
rng = np.random.default_rng(555)
ub = cfg["split"].unique()
idx_by = [np.where(cfg["split"].to_numpy() == b)[0] for b in ub]
Y = cfg["rate"].to_numpy(float)
E = cfg["expl"].to_numpy()
K = cfg["k4"].to_numpy()


def did(ii):
    y, e, k = Y[ii], E[ii], K[ii]
    m = lambda a, b: y[(e == a) & (k == b)].mean()
    return (m(1, 1) - m(0, 1)) - (m(1, 0) - m(0, 0))


d0 = did(np.arange(len(Y)))
bs = np.array([did(np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])) for _ in range(BB)])
bs = bs[~np.isnan(bs)]
print(f"DiD expl x K4 = {100*d0:+.1f} [{100*np.percentile(bs,2.5):+.1f}, {100*np.percentile(bs,97.5):+.1f}]")
res["did_expl_k4"] = dict(est=d0, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])

# ---- ICC (one-way ANOVA estimator) of tipped among configs with >= 2 control runs
g = rc.groupby("scenario_id")["tipped"]
sizes = g.size()
keep = sizes[sizes >= 2].index
r2 = rc[rc["scenario_id"].isin(keep)]
gg = r2.groupby("scenario_id")["tipped"]
k = gg.ngroups
N = len(r2)
ni = gg.size().to_numpy()
mi = gg.mean().to_numpy()
ybar = r2["tipped"].mean()
ssb = np.sum(ni * (mi - ybar) ** 2)
ssw = np.sum([np.sum((v.to_numpy(float) - v.mean()) ** 2) for _, v in gg])
msb = ssb / (k - 1)
msw = ssw / (N - k)
n0 = (N - np.sum(ni ** 2) / N) / (k - 1)
icc = (msb - msw) / (msb + (n0 - 1) * msw)
print(f"ICC: configs={k} runs={N} n0={n0:.3f} ICC={icc:.3f} mean size={N/k:.3f}")
res["icc"] = dict(k=int(k), N=int(N), n0=float(n0), icc=float(icc))

# ---- freeze: sensitivity of the marginal test to the statistic / weighting
y = cfg["rate"].to_numpy(float)
bl = cfg["split"].to_numpy()
codes = cfg["release_freeze"].astype(int).to_numpy().astype(np.int16)
# (a) block-stratified difference (weights = n_b * share1 * share0 ~ CMH weights)
ubl = np.unique(bl)


def strat_stat(L):
    L = np.atleast_2d(L).astype(float)
    num = 0.0
    den = 0.0
    for b in ubl:
        ib = bl == b
        Lb = L[:, ib]
        yb = y[ib]
        n1 = Lb.sum(axis=1)
        n0_ = ib.sum() - n1
        w = n1 * n0_ / ib.sum()
        dlt = (Lb @ yb) / n1 - (yb.sum() - Lb @ yb) / n0_
        dlt = np.where((n1 > 0) & (n0_ > 0), dlt, 0.0)
        num = num + w * dlt
        den = den + w
    return num / den


rngs = np.random.default_rng(91)
t0 = strat_stat(codes)[0]
cnt = 0
BS = 200000
for _ in range(BS // 20000):
    P = perm_labels(codes, bl, 20000, rngs)
    cnt += int(np.sum(np.abs(strat_stat(P)) >= abs(t0) - 1e-12))
ps = (1 + cnt) / (BS + 1)
print(f"freeze block-stratified (CMH-weighted) diff = {100*t0:+.1f} pp, perm p = {ps:.5f} (B={BS}), Holm x11 = {11*ps:.4f}")
res["freeze_strat"] = dict(diff=float(t0), p=ps)
# (b) run-weighted: pool runs (config label permuted, statistic = run-level difference of tip rates)
nr = cfg["n_runs"].to_numpy(float)
nt = cfg["n_tip"].to_numpy(float)


def runw(L):
    L = np.atleast_2d(L).astype(float)
    return (L @ nt) / (L @ nr) - ((nt.sum() - L @ nt) / (nr.sum() - L @ nr))


t0 = runw(codes)[0]
cnt = 0
for _ in range(BS // 20000):
    P = perm_labels(codes, bl, 20000, rngs)
    cnt += int(np.sum(np.abs(runw(P)) >= abs(t0) - 1e-12))
pr_ = (1 + cnt) / (BS + 1)
print(f"freeze run-weighted diff = {100*t0:+.1f} pp, config-level perm p = {pr_:.5f}, Holm x11 = {11*pr_:.4f}")
res["freeze_runweighted"] = dict(diff=float(t0), p=pr_)

with open(os.path.join(HERE, "v_posthoc.json"), "w") as f:
    json.dump(res, f, indent=1, default=float)
