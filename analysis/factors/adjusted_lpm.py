#!/usr/bin/env python3
"""Regression-adjusted risk differences at the config level (linear probability model), randomization inference.

Rows = 112 configs, outcome = config tip rate (mean of run-level tipped over its control runs), equal weight per config
(as in the marginal tests). X = intercept + one-hot of the 14 factors + block dummies (same references as the logistic
model). Because the factors were assigned independently and balanced within block, each OLS coefficient is a
regression-adjusted estimate of the average effect on the tipping probability (no separation problems).
* Randomization test per factor: permute the factor's labels across configs within block (seed type jointly with
  tech-lead status; tech-lead within block x seed type), refit; statistic = extra sum of squares of the factor's
  columns (= partial F); B_PERM permutations. Holm over 14.
* 95% CIs: config bootstrap stratified by block (B_BOOT), percentile.
Sensitivity: run-count weights (WLS with weight = n_runs).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 20261110
B_PERM = 10_000
B_BOOT = 2_000
LEVELS = {"category": ["K2", "K4"], "release_freeze": [False, True], "manager_push": [False, True],
          "discoverability": ["peers_only", "exploration"], "channels": ["team_channels", "board", "dm_only"],
          "self_merge": [False, True], "persistent_share": [0.0, 0.5],
          "prohibition_form": ["soft", "ambiguous", "implicit"], "n_impossible": [9, 12, 16],
          "persona_mix": ["uniform", "skewed_pragmatic"], "sanctions": ["off", "drawn"], "model_mix": ["duo", "majority"],
          "seed_type": ["none", "knower", "pioneer", "side_task", "external"], "seed_tech_lead": [False, True],
          "split": ["night_train", "night_val", "night_test_id", "night_test_ood_family", "night_test_ood_seed",
                    "night_branch"]}
FACTORS = list(LEVELS)[:-1]


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


def build(cfg):
    cols, names, owner = [np.ones(len(cfg))], ["(intercept)"], ["(intercept)"]
    for f in FACTORS + ["split"]:
        for lv in LEVELS[f][1:]:
            cols.append((cfg[f] == lv).to_numpy(float))
            names.append(f"{f}={lv}")
            owner.append(f)
    return np.column_stack(cols), names, owner


def ols(X, y, w=None):
    if w is None:
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ b
        return b, float(r @ r)
    sw = np.sqrt(w)
    b, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    r = (y - X @ b) * sw
    return b, float(r @ r)


def main():
    rng = np.random.default_rng(SEED)
    cfg = pd.read_csv(HERE / "configs.csv")
    for c in ["release_freeze", "manager_push", "self_merge", "seed_tech_lead", "tl_eligible"]:
        cfg[c] = cfg[c].astype(bool)
    X, names, owner = build(cfg)
    y = cfg.tip_rate.to_numpy(float)
    split = cfg.split.to_numpy().astype(str)
    out = {}
    for wlabel, w in [("equal", None), ("n_runs", cfg.n_runs.to_numpy(float))]:
        beta, rss = ols(X, y, w)
        # bootstrap (stratified by block)
        groups = [np.flatnonzero(split == s) for s in np.unique(split)]
        BB = np.empty((B_BOOT, X.shape[1]))
        for b in range(B_BOOT):
            idx = np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups])
            BB[b] = ols(X[idx], y[idx], None if w is None else w[idx])[0]
        coefs = []
        terms = [(names[j], {j: 1.0}) for j in range(1, X.shape[1])]
        jb, jd = names.index("channels=board"), names.index("channels=dm_only")
        terms.append(("channels: board vs dm_only (derived)", {jb: 1.0, jd: -1.0}))
        for t, wts in terms:
            est = sum(v * beta[j] for j, v in wts.items())
            bs = sum(v * BB[:, j] for j, v in wts.items())
            lo, hi = np.percentile(bs, [2.5, 97.5])
            coefs.append(dict(term=t, rd=float(est), ci=[float(lo), float(hi)], excludes_0=bool(lo > 0 or hi < 0)))
        res = dict(weights=wlabel, coefficients=coefs, rss=rss)
        if wlabel == "equal":
            tests = []
            seed_blocks = ~cfg.split.isin(["night_branch", "night_test_ood_seed"]).to_numpy()
            for f in FACTORS:
                tcols = [j for j, o in enumerate(owner) if o == f]
                if f == "seed_type":
                    tcols += [j for j, o in enumerate(owner) if o == "seed_tech_lead"]
                    unit = (cfg.seed_type + "|" + cfg.seed_tech_lead.astype(str)).to_numpy()
                    strata = np.where(seed_blocks, split, np.char.add("fixed_", split))
                elif f == "seed_tech_lead":
                    unit = cfg.seed_tech_lead.to_numpy()
                    strata = np.where(cfg.tl_eligible, (cfg.split + "|" + cfg.seed_type).to_numpy(), "fixed")
                else:
                    unit = cfg[f].to_numpy()
                    strata = split
                strata = strata.astype(str)
                sg = [np.flatnonzero(strata == s) for s in np.unique(strata)]
                keep = [j for j in range(X.shape[1]) if j not in tcols]
                _, rss0 = ols(X[:, keep], y)
                ess_obs = rss0 - rss
                specs = []
                for j in tcols:
                    fo, lv = names[j].split("=", 1)
                    specs.append((j, fo, [l for l in LEVELS[fo] if str(l) == lv][0]))
                Xp = X.copy()
                ess = np.empty(B_PERM)
                for b in range(B_PERM):
                    pv = unit.copy()
                    for g in sg:
                        pv[g] = unit[g][rng.permutation(len(g))]
                    if f == "seed_type":
                        vals = {"seed_type": np.array([u.split("|")[0] for u in pv]),
                                "seed_tech_lead": np.array([u.split("|")[1] == "True" for u in pv])}
                    else:
                        vals = {f: pv}
                    for j, fo, lvv in specs:
                        Xp[:, j] = (vals[fo] == lvv).astype(float)
                    ess[b] = rss0 - ols(Xp, y)[1]
                p = (1 + np.sum(ess >= ess_obs - 1e-12)) / (B_PERM + 1)
                tests.append(dict(factor=f if f != "seed_type" else "seed_type (+ tech-lead status, joint)",
                                  df=len(tcols), extra_ss=float(ess_obs), p_perm=float(p), B=B_PERM))
            for t, h in zip(tests, holm([t["p_perm"] for t in tests])):
                t["p_holm"] = float(h)
            res["randomization_tests"] = tests
        out[wlabel] = res
    (HERE / "results_lpm.json").write_text(json.dumps(out, indent=1))
    for wl, r in out.items():
        print(f"\n=== weights: {wl}")
        for c in r["coefficients"]:
            print(f"  {c['term']:38s} RD {c['rd']:+.3f} [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}] {'*' if c['excludes_0'] else ''}")
        for t in r.get("randomization_tests", []):
            print(f"  test {t['factor']:40s} df {t['df']} p {t['p_perm']:.4f} holm {t['p_holm']:.4f}")


if __name__ == "__main__":
    main()
