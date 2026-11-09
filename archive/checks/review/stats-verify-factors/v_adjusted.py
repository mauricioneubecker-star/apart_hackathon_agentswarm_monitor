"""Independent adjusted analyses:
(1) config-level OLS (linear probability) on all 14 factors + block dummies: coefficients, stratified bootstrap CIs,
    partial-F randomization tests (factor permuted within block, others fixed), Holm over 14.
(2) run-level logistic regression (own Newton-Raphson, tiny ridge) with LR randomization test for selected factors."""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = pd.read_csv(os.path.join(HERE, "v_configs.csv"))
runs = pd.read_csv(os.path.join(HERE, "v_runs.csv"))
runs = runs[runs["is_control"]].copy()
BLOCKS = ["night_train", "night_val", "night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]

# factor -> (column, reference, other levels in order)
FAC = {
    "category": ("cat", "K2", ["K4"]),
    "release_freeze": ("release_freeze", False, [True]),
    "manager_push": ("manager_push", False, [True]),
    "discoverability": ("discoverability", "peers_only", ["exploration"]),
    "channels": ("channels", "team_channels", ["board", "dm_only"]),
    "self_merge": ("self_merge", False, [True]),
    "persistent_share": ("persistent_share", 0.0, [0.5]),
    "prohibition_form": ("prohibition_form", "soft", ["ambiguous", "implicit"]),
    "n_impossible": ("n_impossible", 9, [12, 16]),
    "persona_mix": ("persona_mix", "uniform", ["skewed_pragmatic"]),
    "sanctions": ("sanctions", "off", ["drawn"]),
    "model_mix": ("model_mix", "duo", ["majority"]),
    "seed_type": ("seed_type", "none", ["knower", "pioneer", "side_task", "external"]),
    "seed_tech_lead": ("seed_tl", False, [True]),
}


def design(df):
    cols = {"(intercept)": np.ones(len(df))}
    groups = {}
    for f, (c, ref, lv) in FAC.items():
        groups[f] = []
        for l in lv:
            nm = f"{f}={l}"
            cols[nm] = (df[c] == l).astype(float).to_numpy()
            groups[f].append(nm)
    for b in BLOCKS[1:]:
        cols[f"block={b}"] = (df["split"] == b).astype(float).to_numpy()
    X = pd.DataFrame(cols)
    return X, groups


X, groups = design(cfg)
names = list(X.columns)
Xn = X.to_numpy()
y = cfg["rate"].to_numpy(float)
blk = cfg["split"].to_numpy()
print("params:", Xn.shape[1], "rank:", np.linalg.matrix_rank(Xn))
beta = np.linalg.lstsq(Xn, y, rcond=None)[0]
coef = dict(zip(names, beta))


def ols_beta(Xm, yv):
    return np.linalg.lstsq(Xm, yv, rcond=None)[0]


# ---- stratified config bootstrap of OLS coefficients
rng = np.random.default_rng(2024)
idx_by = [np.where(blk == b)[0] for b in BLOCKS]
BB = 5000
bs = []
for _ in range(BB):
    ii = np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])
    bs.append(ols_beta(Xn[ii], y[ii]))
bs = np.array(bs)
ci = {n: np.percentile(bs[:, j], [2.5, 97.5]) for j, n in enumerate(names)}
jb, jd = names.index("channels=board"), names.index("channels=dm_only")
bd = bs[:, jb] - bs[:, jd]
print(f"OLS board - dm_only (derived) = {100*(coef['channels=board']-coef['channels=dm_only']):+.1f} "
      f"[{100*np.percentile(bd,2.5):+.1f}, {100*np.percentile(bd,97.5):+.1f}]")


# ---- partial-F randomization tests
def perm_cols(df, f, B, rng):
    """returns list of permuted config-level label arrays (for the factor's column(s))"""
    c = FAC[f][0]
    if f == "seed_type":
        lab = list(zip(df["seed_type"], df["seed_tl"]))
        strata = df["split"].to_numpy()
    elif f == "seed_tech_lead":
        lab = list(df["seed_tl"])
        strata = (df["split"] + "|" + df["seed_type"]).to_numpy()
    else:
        lab = list(df[c])
        strata = df["split"].to_numpy()
    lab = np.array(lab, dtype=object)
    out = []
    for _ in range(B):
        L = lab.copy()
        for s in np.unique(strata):
            ii = np.where(strata == s)[0]
            L[ii] = lab[ii][rng.permutation(len(ii))]
        out.append(L)
    return out


def partial_F(Xo, Z, yv):
    """extra SS of Z given Xo (columns of Xo span the reduced model)"""
    Q, _ = np.linalg.qr(Xo)
    ey = yv - Q @ (Q.T @ yv)
    EZ = Z - Q @ (Q.T @ Z)
    # projection of ey on EZ
    g = np.linalg.lstsq(EZ, ey, rcond=None)[0]
    ess = float(ey @ (EZ @ g))
    rss_full = float(ey @ ey) - ess
    return ess, rss_full


def rand_test_ols(f, B, seed):
    rng = np.random.default_rng(seed)
    cols = groups[f] + (groups["seed_tech_lead"] if f == "seed_type" else [])
    other = [n for n in names if n not in cols]
    Xo = X[other].to_numpy()
    Z = X[cols].to_numpy()
    ess0, rss0 = partial_F(Xo, Z, y)
    df1 = Z.shape[1]
    df2 = len(y) - Xn.shape[1]
    F0 = (ess0 / df1) / (rss0 / df2)
    Q, _ = np.linalg.qr(Xo)
    ey = y - Q @ (Q.T @ y)
    cnt = 0
    for L in perm_cols(cfg, f, B, rng):
        d = cfg.copy()
        if f == "seed_type":
            d["seed_type"] = [a for a, b in L]
            d["seed_tl"] = [b for a, b in L]
        else:
            d[FAC[f][0]] = L
        Xp, _ = design(d)
        Zp = Xp[cols].to_numpy()
        EZ = Zp - Q @ (Q.T @ Zp)
        g = np.linalg.lstsq(EZ, ey, rcond=None)[0]
        ess = float(ey @ (EZ @ g))
        F = (ess / df1) / ((float(ey @ ey) - ess) / df2)
        cnt += F >= F0 - 1e-9
    return F0, (1 + cnt) / (B + 1)


B_OLS = int(os.environ.get("B_OLS", 10000))
pols = {}
t = time.time()
for i, f in enumerate(FAC):
    F0, p = rand_test_ols(f, B_OLS, 5000 + i)
    pols[f] = p
    show = ", ".join(f"{n.split('=')[1]} {100*coef[n]:+.1f} [{100*ci[n][0]:+.1f}, {100*ci[n][1]:+.1f}]" for n in groups[f])
    print(f"OLS {f:18s} F={F0:7.3f} p={p:.5f}  {show}   ({time.time()-t:.0f}s)")
    sys.stdout.flush()


def holm(pd_):
    ks = list(pd_)
    ps = np.array([pd_[k] for k in ks])
    o = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(1.0, run)
    return dict(zip(ks, adj))


hols = holm(pols)
print("OLS Holm:", {k: round(v, 4) for k, v in sorted(hols.items(), key=lambda kv: pols[kv[0]])})

# ---- run-level logistic regression with LR randomization test
cfg_index = {s: i for i, s in enumerate(cfg["scenario_id"])}
ridx = runs["scenario_id"].map(cfg_index).to_numpy()
yr = runs["tipped"].astype(float).to_numpy()
Xr = Xn[ridx]
LAM = 1e-6


def fit_logit(Xm, yv, b0=None, maxit=200):
    p = Xm.shape[1]
    b = np.zeros(p) if b0 is None else b0.copy()
    pen = np.full(p, LAM)
    pen[0] = 0.0

    def obj(bb):
        eta = Xm @ bb
        ll = np.sum(yv * eta - np.logaddexp(0, eta))
        return ll - 0.5 * np.sum(pen * bb * bb)

    cur = obj(b)
    for it in range(maxit):
        eta = Xm @ b
        mu = 1 / (1 + np.exp(-eta))
        W = mu * (1 - mu)
        g = Xm.T @ (yv - mu) - pen * b
        H = Xm.T @ (Xm * W[:, None]) + np.diag(pen) + 1e-12 * np.eye(p)
        step = np.linalg.solve(H, g)
        s = 1.0
        while True:
            nb = b + s * step
            new = obj(nb)
            if new >= cur - 1e-12 or s < 1e-8:
                break
            s /= 2
        b = nb
        if abs(new - cur) < 1e-10:
            cur = new
            break
        cur = new
    eta = Xm @ b
    dev = -2 * np.sum(yv * eta - np.logaddexp(0, eta))
    return b, dev, it


bfull, dev_full, it = fit_logit(Xr, yr)
print(f"\nlogit full: dev={dev_full:.3f} iters={it} max|beta|={np.max(np.abs(bfull)):.3f}")
for n in ["category=K4", "release_freeze=True", "discoverability=exploration", "channels=board", "channels=dm_only"]:
    print(f"  OR {n}: {np.exp(bfull[names.index(n)]):.2f}")
print(f"  OR board vs dm_only: {np.exp(bfull[jb]-bfull[jd]):.2f}")

B_LR = int(os.environ.get("B_LR", 20000))
lr_res = {}
for f in os.environ.get("LR_FACTORS", "category,discoverability,release_freeze,channels").split(","):
    rng = np.random.default_rng(hash(f) % 100000)
    cols = groups[f]
    keep = [j for j, n in enumerate(names) if n not in cols]
    _, dev_red, _ = fit_logit(Xr[:, keep], yr)
    LR0 = dev_red - dev_full
    jcols = [names.index(n) for n in cols]
    cnt = 0
    t = time.time()
    lab = cfg[FAC[f][0]].to_numpy(dtype=object)
    strata = cfg["split"].to_numpy()
    sidx = [np.where(strata == s)[0] for s in np.unique(strata)]
    Xp = Xr.copy()
    for r in range(B_LR):
        L = lab.copy()
        for ii in sidx:
            L[ii] = lab[ii][rng.permutation(len(ii))]
        for jj, n in zip(jcols, cols):
            lv = FAC[f][2][FAC[f][2].index(type(FAC[f][2][0])(n.split("=")[1]) if not isinstance(FAC[f][2][0], (bool, np.bool_)) else (n.split("=")[1] == "True"))]
            Xp[:, jj] = (L == lv).astype(float)[ridx]
        _, dv, _ = fit_logit(Xp, yr, b0=bfull)
        cnt += (dev_red - dv) >= LR0 - 1e-7
    p = (1 + cnt) / (B_LR + 1)
    lr_res[f] = dict(LR=float(LR0), p=float(p), B=B_LR)
    print(f"logit LR randomization {f:16s} LR={LR0:6.2f} p={p:.5f} (B={B_LR}, {time.time()-t:.0f}s)")
    sys.stdout.flush()

with open(os.path.join(HERE, "v_adjusted.json"), "w") as fh:
    json.dump(dict(ols_coef={k: float(v) for k, v in coef.items()},
                   ols_ci={k: list(map(float, v)) for k, v in ci.items()},
                   ols_p=pols, ols_holm=hols, logit_LR=lr_res,
                   logit_OR={n: float(np.exp(b)) for n, b in zip(names, bfull)}), fh, indent=1)
