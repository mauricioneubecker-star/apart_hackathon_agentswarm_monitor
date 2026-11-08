#!/usr/bin/env python3
"""Multivariable logistic regression of run-level `tipped` (theta = 8) on all night-batch factors jointly.

* One-hot main effects of the 14 design factors + design-block (split) dummies; references in REFS.
* ML fit: Newton-Raphson on the L2-penalised log-likelihood with lambda = 1/C, C = 1e6 (intercept unpenalised),
  i.e. sklearn LogisticRegression(C=1e6); checked against sklearn.
* Separation check: refit with C = 1e8 and 1e10 (coefficients must not drift), max |beta|, all-0/all-1 columns, and
  the share of cluster-bootstrap refits with |beta| > 10 (quasi-separation inside resamples).
* Config-cluster bootstrap stratified by block (B_BOOT resamples of configs with replacement within block; all runs
  of a drawn config enter); percentile 95% CIs of the ORs, for the ML fit and for a Firth (Jeffreys-prior,
  bias-reduced) fit, which stays finite under separation.
* Adjusted randomization test per factor (factors were assigned independently and balanced within block): permute
  that factor's labels across configs within block, keep every other factor fixed, refit ML; statistic =
  likelihood-ratio (deviance drop) of the factor's columns. Exact under the sharp null of no effect. Holm over 14.
* Sensitivities (Firth): no block dummies; + extra design factors (seed placement, cut, push offset, family);
  ML with mild ridge C = 5. Exploratory interaction terms (Firth).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 20261109
B_BOOT = 2000
B_ADJ = 10_000
B_SENS = 1000
C_MAIN = 1e6

REFS = {"category": "K2", "release_freeze": False, "manager_push": False, "discoverability": "peers_only",
        "channels": "team_channels", "self_merge": False, "persistent_share": 0.0, "prohibition_form": "soft",
        "n_impossible": 9, "persona_mix": "uniform", "sanctions": "off", "model_mix": "duo", "seed_type": "none",
        "seed_tech_lead": False, "split": "night_train"}
LEVELS = {"category": ["K2", "K4"], "release_freeze": [False, True], "manager_push": [False, True],
          "discoverability": ["peers_only", "exploration"], "channels": ["team_channels", "board", "dm_only"],
          "self_merge": [False, True], "persistent_share": [0.0, 0.5],
          "prohibition_form": ["soft", "ambiguous", "implicit"], "n_impossible": [9, 12, 16],
          "persona_mix": ["uniform", "skewed_pragmatic"], "sanctions": ["off", "drawn"], "model_mix": ["duo", "majority"],
          "seed_type": ["none", "knower", "pioneer", "side_task", "external"], "seed_tech_lead": [False, True],
          "split": ["night_train", "night_val", "night_test_id", "night_test_ood_family", "night_test_ood_seed",
                    "night_branch"]}
FACTORS = ["category", "release_freeze", "manager_push", "discoverability", "channels", "self_merge",
           "persistent_share", "prohibition_form", "n_impossible", "persona_mix", "sanctions", "model_mix",
           "seed_type", "seed_tech_lead"]
EXTRA_LEVELS = {"seed_placement": ["hub", "periphery"], "cut": [17, 20, 23, 26],
                # push offset only acts with a push: dummies for 6 and 8 (ref 4), both 0 without push (no collinearity)
                "push_offset_on": [4, 6, 8],
                "family": ["ledgerlib", "routekit", "slotplan", "stockflow", "textkit", "metricore"]}


def onehot(df, factors, levels):
    cols, names, owner = [], [], []
    for f in factors:
        for lv in levels[f][1:]:
            cols.append((df[f] == lv).to_numpy(float))
            names.append(f"{f}={lv}")
            owner.append(f)
    return np.column_stack(cols), names, owner


def design(df, factors, levels, extra=None):
    X, names, owner = onehot(df, factors, levels)
    if extra:
        Xe, ne, oe = onehot(df, extra, EXTRA_LEVELS)
        X, names, owner = np.column_stack([X, Xe]), names + ne, owner + oe
    X = np.column_stack([np.ones(len(df)), X])
    return X, ["(intercept)"] + names, ["(intercept)"] + owner


def expit(x):
    return 0.5 * (1 + np.tanh(0.5 * x))


def fit_ml(X, y, lam, beta0=None, max_iter=100):
    """Newton-Raphson, penalty (lam/2)*||beta[1:]||^2 (sklearn C = 1/lam). Returns beta, deviance, converged."""
    n, p = X.shape
    beta = np.zeros(p) if beta0 is None else beta0.copy()
    pen = np.full(p, lam)
    pen[0] = 0.0

    def obj(b):
        eta = X @ b
        return -(y * eta - np.logaddexp(0, eta)).sum() + 0.5 * (pen * b * b).sum()

    f_old = obj(beta)
    converged = False
    for _ in range(max_iter):
        mu = expit(X @ beta)
        g = X.T @ (mu - y) + pen * beta
        H = (X * (mu * (1 - mu))[:, None]).T @ X + np.diag(pen) + 1e-12 * np.eye(p)
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(H, g, rcond=None)[0]
        t = 1.0
        while True:
            nb = beta - t * step
            f_new = obj(nb)
            if f_new <= f_old + 1e-12 or t < 1e-8:
                break
            t /= 2
        beta = nb
        done = abs(f_old - f_new) < 1e-10 * (1 + abs(f_new)) and np.max(np.abs(t * step)) < 1e-7
        f_old = f_new
        if done:
            converged = True
            break
    eta = X @ beta
    return beta, float(-2 * (y * eta - np.logaddexp(0, eta)).sum()), converged


def fit_firth(X, y, beta0=None, max_iter=200):
    """Firth bias-reduced logistic regression (penalised log-lik l + 0.5 log|X'WX|), modified-score Newton steps
    with step halving. Finite under (quasi-)separation."""
    n, p = X.shape
    beta = np.zeros(p) if beta0 is None else beta0.copy()

    def pll(b):
        eta = X @ b
        mu = expit(eta)
        M = (X * (mu * (1 - mu))[:, None]).T @ X
        sign, logdet = np.linalg.slogdet(M)
        return (y * eta - np.logaddexp(0, eta)).sum() + 0.5 * logdet if sign > 0 else -np.inf

    f = pll(beta)
    converged = False
    for _ in range(max_iter):
        mu = expit(X @ beta)
        W = mu * (1 - mu)
        M = (X * W[:, None]).T @ X
        try:
            Minv = np.linalg.inv(M)
        except np.linalg.LinAlgError:
            Minv = np.linalg.pinv(M)
        h = W * np.einsum("ij,jk,ik->i", X, Minv, X)
        U = X.T @ (y - mu + h * (0.5 - mu))
        step = Minv @ U
        t = 1.0
        while True:
            nb = beta + t * step
            fn = pll(nb)
            if fn >= f - 1e-10 or t < 1e-8:
                break
            t /= 2
        beta = nb
        f = fn
        if np.max(np.abs(t * step)) < 1e-8:
            converged = True
            break
    return beta, converged


def boot_cfg_idx(cfg, rng):
    parts = []
    for _, g in cfg.groupby("split"):
        ids = g.index.to_numpy()
        parts.append(ids[rng.integers(0, len(ids), len(ids))])
    return np.concatenate(parts)


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * p[i]))
        adj[i] = run
    return adj


def pct(x):
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    rng = np.random.default_rng(SEED)
    cfg = pd.read_csv(HERE / "configs.csv")
    runs = pd.read_csv(HERE / "runs.csv")
    for d in (cfg, runs):
        for c in ["release_freeze", "manager_push", "self_merge", "seed_tech_lead", "tl_eligible"]:
            d[c] = d[c].astype(bool)
        d["push_offset_on"] = np.where(d.manager_push, d.push_offset, 0)
    cfg = cfg.reset_index(drop=True)
    cfg_pos = {s: i for i, s in enumerate(cfg.scenario_id)}
    runs["cfg_i"] = runs.scenario_id.map(cfg_pos)
    cfg_i = runs.cfg_i.to_numpy()
    rows_by_cfg = {i: np.flatnonzero(cfg_i == i) for i in range(len(cfg))}
    rows_of = lambda idx: np.concatenate([rows_by_cfg[i] for i in idx])
    y = runs.tipped.to_numpy(float)
    allf = FACTORS + ["split"]
    X, names, owner = design(runs, allf, LEVELS)
    lam = 1 / C_MAIN
    beta, dev, conv = fit_ml(X, y, lam)
    bF, convF = fit_firth(X, y, beta0=beta * 0.8)
    res = dict(n_runs=int(len(y)), n_tipped=int(y.sum()), n_configs=int(len(cfg)), n_params=int(X.shape[1]),
               C=C_MAIN, refs={k: str(v) for k, v in REFS.items()}, converged_ml=bool(conv), converged_firth=bool(convF),
               deviance=dev)
    # ---------------- separation / stability checks on the full data
    sep = {}
    for C in [1e8, 1e10]:
        b2, _, _ = fit_ml(X, y, 1 / C, beta0=beta)
        sep[f"max_abs_change_C{C:.0e}"] = float(np.max(np.abs(b2 - beta)))
    sep["max_abs_beta"] = float(np.max(np.abs(beta[1:])))
    mu = expit(X @ beta)
    sep["hessian_condition_number"] = float(np.linalg.cond((X * (mu * (1 - mu))[:, None]).T @ X))
    sep["min_fitted_p"], sep["max_fitted_p"] = float(mu.min()), float(mu.max())
    sep["columns_with_all0_or_all1"] = [names[j] for j in range(1, X.shape[1])
                                        if y[X[:, j] == 1].sum() in (0, (X[:, j] == 1).sum())]
    try:
        from sklearn.linear_model import LogisticRegression
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sk = LogisticRegression(C=C_MAIN, max_iter=100000, tol=1e-12, solver="lbfgs").fit(X[:, 1:], y)
        sep["sklearn_max_abs_diff"] = float(np.max(np.abs(np.r_[sk.intercept_, sk.coef_[0]] - beta)))
    except Exception as e:  # noqa: BLE001
        sep["sklearn_error"] = repr(e)
    res["separation_checks"] = sep

    # ---------------- cluster bootstrap: ML and Firth on the same resamples
    BM = np.full((B_BOOT, X.shape[1]), np.nan)
    BF = np.full((B_BOOT, X.shape[1]), np.nan)
    nc_ml = nc_f = 0
    for b in range(B_BOOT):
        rows = rows_of(boot_cfg_idx(cfg, rng))
        bm, _, cm = fit_ml(X[rows], y[rows], lam, beta0=beta, max_iter=60)
        bf, cf = fit_firth(X[rows], y[rows], beta0=bF)
        BM[b], BF[b] = bm, bf
        nc_ml += (not cm)
        nc_f += (not cf)
    degenerate = np.any(np.abs(BM[:, 1:]) > 10, axis=1)
    res["bootstrap"] = dict(B=B_BOOT, nonconverged_ml=int(nc_ml), nonconverged_firth=int(nc_f),
                            share_resamples_any_ml_abs_beta_gt10=float(degenerate.mean()),
                            share_resamples_any_firth_abs_beta_gt10=float(np.any(np.abs(BF[:, 1:]) > 10, axis=1).mean()))
    coef = []
    contrasts = [(names[j], {j: 1.0}) for j in range(1, X.shape[1])]
    jb, jd = names.index("channels=board"), names.index("channels=dm_only")
    contrasts.append(("channels: board vs dm_only (derived)", {jb: 1.0, jd: -1.0}))
    for term, wts in contrasts:
        lin = lambda B_: sum(w * (B_[..., j] if B_.ndim > 1 else B_[j]) for j, w in wts.items())
        bm_obs, bf_obs = lin(beta), lin(bF)
        bm_bs, bf_bs = lin(BM), lin(BF)
        lo_m, hi_m = pct(bm_bs)
        lo_f, hi_f = pct(bf_bs)
        j0 = next(iter(wts))
        coef.append(dict(term=term, factor=owner[j0], beta_ml=float(bm_obs), OR_ml=float(np.exp(bm_obs)),
                         OR_ml_ci=[float(np.exp(lo_m)), float(np.exp(hi_m))],
                         share_boot_ml_abs_gt10=float(np.mean(np.abs(bm_bs) > 10)),
                         beta_firth=float(bf_obs), OR_firth=float(np.exp(bf_obs)),
                         OR_firth_ci=[float(np.exp(lo_f)), float(np.exp(hi_f))],
                         firth_boot_share_gt0=float(np.mean(bf_bs > 0)),
                         firth_ci_excludes_1=bool(lo_f > 0 or hi_f < 0),
                         ml_ci_excludes_1=bool(lo_m > 0 or hi_m < 0)))
    res["coefficients"] = coef

    # ---------------- adjusted randomization tests (conditional on all other factors)
    adj = []
    seed_blocks = ~cfg.split.isin(["night_branch", "night_test_ood_seed"]).to_numpy()
    split_c = cfg.split.to_numpy()
    for f in FACTORS:
        cols = [j for j, o in enumerate(owner) if o == f]
        test_cols = cols + ([j for j, o in enumerate(owner) if o == "seed_tech_lead"] if f == "seed_type" else [])
        keep = [j for j in range(X.shape[1]) if j not in test_cols]
        _, dev0, _ = fit_ml(X[:, keep], y, lam)
        lr_obs = dev0 - dev
        if f == "seed_type":   # permute (seed type, tech-lead status) jointly -> joint null of the seed design
            unit = (cfg.seed_type + "|" + cfg.seed_tech_lead.astype(str)).to_numpy()
            strata = np.where(seed_blocks, split_c, np.char.add("fixed_", split_c.astype(str)))
        elif f == "seed_tech_lead":   # Bernoulli(0.5) among eligible configs -> permute within block x seed type
            unit = cfg.seed_tech_lead.to_numpy()
            strata = np.where(cfg.tl_eligible, (cfg.split + "|" + cfg.seed_type).to_numpy(), "fixed")
        else:
            unit = cfg[f].to_numpy()
            strata = split_c
        strata = strata.astype(str)
        groups = [np.flatnonzero(strata == s) for s in np.unique(strata)]
        # level indicator per config for each tested column
        col_specs = []
        for j in test_cols:
            fo, lv = names[j].split("=", 1)
            lvv = [l for l in LEVELS[fo] if str(l) == lv][0]
            col_specs.append((j, fo, lvv))
        lr_perm = np.empty(B_ADJ)
        Xp = X.copy()
        for b in range(B_ADJ):
            pv = unit.copy()
            for g in groups:
                pv[g] = unit[g][rng.permutation(len(g))]
            if f == "seed_type":
                st = np.array([u.split("|")[0] for u in pv])
                tl = np.array([u.split("|")[1] == "True" for u in pv])
                vals = {"seed_type": st, "seed_tech_lead": tl}
            else:
                vals = {f: pv}
            for j, fo, lvv in col_specs:
                Xp[:, j] = (vals[fo] == lvv).astype(float)[cfg_i]
            _, devp, _ = fit_ml(Xp, y, lam, beta0=beta, max_iter=60)
            lr_perm[b] = dev0 - devp
        p = (1 + np.sum(lr_perm >= lr_obs - 1e-9)) / (B_ADJ + 1)
        from scipy import stats
        adj.append(dict(factor=f if f != "seed_type" else "seed_type (+ tech-lead status, joint)", lr_obs=float(lr_obs),
                        df=len(test_cols), p_adj_perm=float(p), B=B_ADJ,
                        p_chi2_asymptotic=float(stats.chi2.sf(lr_obs, len(test_cols))),
                        perm_null_mean_lr=float(lr_perm.mean())))
        print(f"adjusted perm {f:17s} LR {lr_obs:7.3f} df {len(test_cols)} p {p:.4f} "
              f"(chi2 {adj[-1]['p_chi2_asymptotic']:.4f}, null mean LR {lr_perm.mean():.2f})", flush=True)
    for a, h in zip(adj, holm([a["p_adj_perm"] for a in adj])):
        a["p_holm"] = float(h)
    res["adjusted_randomization"] = adj

    # ---------------- sensitivity fits (Firth unless stated), bootstrap CIs for key terms
    key = ["category=K4", "release_freeze=True", "manager_push=True", "discoverability=exploration",
           "channels=board", "channels=dm_only", "sanctions=drawn", "n_impossible=12", "n_impossible=16",
           "prohibition_form=implicit", "prohibition_form=ambiguous", "seed_tech_lead=True", "seed_type=pioneer",
           "persistent_share=0.5", "self_merge=True"]

    def sens(label, Xs, names_s, method):
        if method == "firth":
            bs, cs = fit_firth(Xs, y)
            refit = lambda Xr, yr: fit_firth(Xr, yr, beta0=bs)[0]
        else:
            bs, _, cs = fit_ml(Xs, y, method)
            refit = lambda Xr, yr: fit_ml(Xr, yr, method, beta0=bs, max_iter=60)[0]
        BBs = np.full((B_SENS, Xs.shape[1]), np.nan)
        for b in range(B_SENS):
            rows = rows_of(boot_cfg_idx(cfg, rng))
            BBs[b] = refit(Xs[rows], y[rows])
        outk = {}
        for k in key:
            if k in names_s:
                j = names_s.index(k)
                lo, hi = pct(BBs[:, j])
                outk[k] = dict(OR=float(np.exp(bs[j])), OR_ci=[float(np.exp(lo)), float(np.exp(hi))])
        return dict(label=label, n_params=int(Xs.shape[1]), converged=bool(cs), terms=outk, B=B_SENS)

    sres = []
    Xn, nn, _ = design(runs, FACTORS, LEVELS)
    sres.append(sens("Firth, no block dummies", Xn, nn, "firth"))
    Xe, ne, _ = design(runs, allf, LEVELS, extra=["seed_placement", "cut", "push_offset_on", "family"])
    jm = ne.index("family=metricore")    # metricore == night_test_ood_family block -> collinear, drop
    Xe = np.delete(Xe, jm, axis=1)
    ne = [n for i, n in enumerate(ne) if i != jm]
    sres.append(sens("Firth, + seed placement, cut, push offset, family", Xe, ne, "firth"))
    sres.append(sens("ML with ridge C = 5", X, names, 1 / 5.0))
    res["sensitivity"] = sres

    # ---------------- exploratory interactions (Firth, one product term at a time)
    inter = []
    for a, b, la, lb in [("release_freeze=True", "manager_push=True", "freeze", "push"),
                         ("discoverability=exploration", "category=K4", "exploration", "K4"),
                         ("release_freeze=True", "discoverability=exploration", "freeze", "exploration"),
                         ("channels=board", "discoverability=exploration", "board", "exploration")]:
        ja, jb2 = names.index(a), names.index(b)
        Xi = np.column_stack([X, X[:, ja] * X[:, jb2]])
        bi, ci_ = fit_firth(Xi, y)
        _, devi, _ = fit_ml(Xi, y, lam)
        Bi = np.full((B_SENS, Xi.shape[1]), np.nan)
        for t in range(B_SENS):
            rows = rows_of(boot_cfg_idx(cfg, rng))
            Bi[t] = fit_firth(Xi[rows], y[rows], beta0=bi)[0]
        lo, hi = pct(Bi[:, -1])
        loa0, hia0 = pct(Bi[:, ja])
        loa1, hia1 = pct(Bi[:, ja] + Bi[:, -1])
        inter.append(dict(term=f"{la} x {lb}", ratio_of_ORs=float(np.exp(bi[-1])), ci=[float(np.exp(lo)), float(np.exp(hi))],
                          OR_a_when_b0=float(np.exp(bi[ja])), OR_a_when_b0_ci=[float(np.exp(loa0)), float(np.exp(hia0))],
                          OR_a_when_b1=float(np.exp(bi[ja] + bi[-1])), OR_a_when_b1_ci=[float(np.exp(loa1)), float(np.exp(hia1))],
                          lr_ml_vs_main=float(dev - devi)))
    res["interactions_exploratory"] = inter
    (HERE / "results_logit.json").write_text(json.dumps(res, indent=1, default=str))

    print(json.dumps({k: res[k] for k in ["n_runs", "n_tipped", "n_configs", "n_params", "converged_ml",
                                          "converged_firth", "deviance", "separation_checks", "bootstrap"]},
                     indent=1, default=str))
    print(f"\n{'term':38s} {'OR_ML':>8s} {'ML 95% CI':>24s} {'|b|>10':>7s} {'OR_Firth':>9s} {'Firth 95% CI':>20s}")
    for c in coef:
        print(f"{c['term']:38s} {c['OR_ml']:8.3f} [{c['OR_ml_ci'][0]:9.3g}, {c['OR_ml_ci'][1]:9.3g}] "
              f"{c['share_boot_ml_abs_gt10']:7.3f} {c['OR_firth']:9.3f} [{c['OR_firth_ci'][0]:7.3f}, "
              f"{c['OR_firth_ci'][1]:8.3f}] {'*' if c['firth_ci_excludes_1'] else ''}")
    print("\nadjusted randomization tests")
    for a in adj:
        print(f"  {a['factor']:40s} LR {a['lr_obs']:7.3f} df {a['df']} p {a['p_adj_perm']:.4f} holm {a['p_holm']:.4f} "
              f"chi2-p {a['p_chi2_asymptotic']:.4f}")
    print("\nsensitivity")
    for s in sres:
        print(" ", s["label"], s["n_params"], s["converged"])
        for k, v in s["terms"].items():
            print(f"     {k:30s} OR {v['OR']:7.3f} [{v['OR_ci'][0]:.3f}, {v['OR_ci'][1]:.3f}]")
    print("\ninteractions (exploratory, Firth)")
    for i in inter:
        print(" ", json.dumps(i))


if __name__ == "__main__":
    main()
