"""Independent re-computation of the marginal factor tests (config level).
Own implementation: vectorised within-block permutations, own seeds, own Holm, own stratified bootstrap."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = pd.read_csv(os.path.join(HERE, "v_configs.csv"))
EPS = 1e-12
B_PERM = int(os.environ.get("B_PERM", 50000))
B_BOOT = int(os.environ.get("B_BOOT", 10000))


def perm_labels(codes, blocks, B, rng):
    """(B, n) matrix of codes permuted independently within each block."""
    n = len(codes)
    out = np.empty((B, n), dtype=np.int16)
    for b in np.unique(blocks):
        ib = np.where(blocks == b)[0]
        pr = np.argsort(rng.random((B, len(ib))), axis=1)
        out[:, ib] = codes[ib][pr]
    return out


def stat_binary(y, L):
    """L: (..., n) 0/1 codes; returns mean(y|1) - mean(y|0)."""
    L = np.asarray(L, dtype=float)
    n1 = L.sum(axis=-1)
    s1 = L @ y
    return s1 / n1 - (y.sum() - s1) / (len(y) - n1)


def stat_between(y, L, k):
    """n-weighted between-level sum of squares; L codes 0..k-1."""
    L = np.asarray(L)
    tot = 0.0
    S = y.sum()
    N = len(y)
    for g in range(k):
        ind = (L == g).astype(float)
        ng = ind.sum(axis=-1)
        sg = ind @ y
        tot = tot + sg ** 2 / ng
    return tot - S ** 2 / N


def perm_test(y, codes, blocks, k, B, seed, chunk=20000):
    rng = np.random.default_rng(seed)
    if k == 2:
        t0 = stat_binary(y, codes)
    else:
        t0 = stat_between(y, codes, k)
    cnt = 0
    done = 0
    while done < B:
        b = min(chunk, B - done)
        P = perm_labels(codes, blocks, b, rng)
        if k == 2:
            t = stat_binary(y, P)
            cnt += int(np.sum(np.abs(t) >= abs(t0) - EPS))
        else:
            t = stat_between(y, P, k)
            cnt += int(np.sum(t >= t0 - EPS))
        done += b
    return float(t0), (1 + cnt) / (B + 1)


def boot_diff(y, codes, blocks, lv, ref, B, seed):
    """stratified (by block) config bootstrap of mean(y|lv) - mean(y|ref); percentile CI."""
    rng = np.random.default_rng(seed)
    ub = np.unique(blocks)
    idx_by = [np.where(blocks == b)[0] for b in ub]
    res = np.empty(B)
    for r in range(B):
        ii = np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])
        c = codes[ii]
        yy = y[ii]
        a = yy[c == lv]
        bb = yy[c == ref]
        res[r] = (a.mean() - bb.mean()) if (len(a) and len(bb)) else np.nan
    res = res[~np.isnan(res)]
    return np.percentile(res, [2.5, 97.5]), len(res)


def boot_rate(y, codes, blocks, lv, B, seed):
    rng = np.random.default_rng(seed)
    ub = np.unique(blocks)
    idx_by = [np.where(blocks == b)[0] for b in ub]
    res = np.empty(B)
    for r in range(B):
        ii = np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])
        a = y[ii][codes[ii] == lv]
        res[r] = a.mean() if len(a) else np.nan
    res = res[~np.isnan(res)]
    return np.percentile(res, [2.5, 97.5])


def holm(pd_):
    names = list(pd_)
    ps = np.array([pd_[k] for k in names])
    order = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(1.0, run)
    return dict(zip(names, adj))


# factor specs: name -> (column, levels in code order [ref first], subset mask)
seeded = cfg["seed_type"].isin(["knower", "pioneer", "side_task"])
seed_blocks = cfg["split"].isin(["night_train", "night_val", "night_test_id", "night_test_ood_family"])
SPECS = {
    "category": ("cat", ["K2", "K4"], None),
    "release_freeze": ("release_freeze", [False, True], None),
    "manager_push": ("manager_push", [False, True], None),
    "discoverability": ("discoverability", ["peers_only", "exploration"], None),
    "channels": ("channels", ["board", "team_channels", "dm_only"], None),
    "self_merge": ("self_merge", [False, True], None),
    "persistent_share": ("persistent_share", [0.0, 0.5], None),
    "prohibition_form": ("prohibition_form", ["implicit", "ambiguous", "soft"], None),
    "n_impossible": ("n_impossible", [9, 12, 16], None),
    "persona_mix": ("persona_mix", ["uniform", "skewed_pragmatic"], None),
    "sanctions": ("sanctions", ["off", "drawn"], None),
    "model_mix": ("model_mix", ["duo", "majority"], None),
    "seed_type": ("seed_type", ["none", "knower", "pioneer", "side_task", "external"], seed_blocks.values),
    "seed_tech_lead": ("seed_tl", [False, True], seeded.values),
}

out = {"B_perm": B_PERM, "B_boot": B_BOOT, "factors": {}}
pvals = {}
for i, (name, (col, levels, mask)) in enumerate(SPECS.items()):
    d = cfg if mask is None else cfg[mask]
    y = d["rate"].to_numpy(float)
    blocks = d["split"].to_numpy()
    codes = np.array([levels.index(v) for v in d[col].tolist()], dtype=np.int16)
    k = len(levels)
    t0, p = perm_test(y, codes, blocks, k, B_PERM, seed=1000 + i)
    rates = {str(lv): float(y[codes == j].mean()) for j, lv in enumerate(levels)}
    ns = {str(lv): int((codes == j).sum()) for j, lv in enumerate(levels)}
    rec = dict(n_configs=int(len(d)), stat=t0, p=p, rates=rates, n=ns)
    if k == 2:
        ci, nb = boot_diff(y, codes, blocks, 1, 0, B_BOOT, seed=2000 + i)
        rec["diff"] = float(rates[str(levels[1])] - rates[str(levels[0])])
        rec["diff_ci"] = [float(ci[0]), float(ci[1])]
    pvals[name] = p
    out["factors"][name] = rec
    print(f"{name:18s} n={len(d):3d} stat={t0:+.4f} p={p:.5f} rates=" +
          ", ".join(f"{a}:{100*b:.1f}%({ns[a]})" for a, b in rates.items()) +
          (f" diff={100*rec['diff']:+.1f} [{100*rec['diff_ci'][0]:+.1f}, {100*rec['diff_ci'][1]:+.1f}]" if k == 2 else ""))
    sys.stdout.flush()

hp = holm(pvals)
out["holm14"] = hp
print("\nHolm over 14:")
for k_, v in sorted(hp.items(), key=lambda kv: pvals[kv[0]]):
    print(f"  {k_:18s} p={pvals[k_]:.5f} holm={v:.4f}")

# release_freeze with many permutations (MC precision)
d = cfg
y = d["rate"].to_numpy(float)
blocks = d["split"].to_numpy()
codes = d["release_freeze"].astype(int).to_numpy().astype(np.int16)
BF = int(os.environ.get("B_FREEZE", 400000))
t0, pf = perm_test(y, codes, blocks, 2, BF, seed=77)
se = np.sqrt(pf * (1 - pf) / BF)
out["freeze_big"] = dict(B=BF, p=pf, se=float(se))
print(f"\nrelease_freeze B={BF}: p={pf:.5f} (MC SE {se:.5f}); Holm (x11) = {11*pf:.4f}")
pv2 = dict(pvals)
pv2["release_freeze"] = pf
out["holm14_freeze_big"] = holm(pv2)
print("  Holm14 with big-B freeze p:", round(out["holm14_freeze_big"]["release_freeze"], 4))

# Holm family sensitivity: only the 4 positive FINDINGS sentences / the 5 FINDINGS factors
fam5 = {k_: pv2[k_] for k_ in ["release_freeze", "discoverability", "channels", "category", "sanctions"]}
fam4 = {k_: pv2[k_] for k_ in ["release_freeze", "discoverability", "channels", "category"]}
out["holm5"] = holm(fam5)
out["holm4"] = holm(fam4)
print("Holm over the 5 FINDINGS factors:", {k_: round(v, 4) for k_, v in out["holm5"].items()})
print("Holm over the 4 positive FINDINGS factors:", {k_: round(v, 4) for k_, v in out["holm4"].items()})

with open(os.path.join(HERE, "v_tests.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
