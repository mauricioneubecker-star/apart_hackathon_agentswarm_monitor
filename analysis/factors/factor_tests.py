#!/usr/bin/env python3
"""Marginal randomization tests of the night-batch design factors on the tipping probability.

Unit of inference = config (scenario_id). Outcome per config = mean of run-level `tipped` (theta = 8) over its
control runs (1-3 replicates). For every factor:
  * permutation test: factor labels permuted ACROSS CONFIGS WITHIN DESIGN BLOCK (split), B_PERM permutations;
    binary factor: T = mean(config means | level 1) - mean(config means | level 0), two-sided p;
    multi-level factor: T = n-weighted between-level variance of config means (= permutation one-way ANOVA F);
    p = (1 + #{T* >= T_obs}) / (B + 1)  (binary: |T*| >= |T_obs|).
  * effect: tip-rate difference (or per-level rates, pairwise differences) with 95% percentile CI from a
    config-cluster bootstrap stratified by block (B_BOOT resamples of configs with replacement within each block).
  * Holm over the 14 main factors; extra design factors and post-hoc contrasts are reported separately.
Also: run-level Fisher / chi-square tests as an (anti-conservative) contrast, within-config ICC, negative controls,
exploratory 2x2 interactions, and the effective-sanction subset (detection probability > 0).
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
B_PERM = 10_000
B_BOOT = 2_000
SEED = 20261108
SPLIT_ORDER = ["night_train", "night_val", "night_test_id", "night_test_ood_family", "night_test_ood_seed",
               "night_branch"]

# name, column, levels (binary: [reference, contrast]; diff = contrast - reference), subset, note
MAIN = [
    ("category", "category", ["K2", "K4"], None, "K4 check bypass vs K2 scorer tamper"),
    ("release_freeze", "release_freeze", [False, True], None, "release freeze (time pressure)"),
    ("manager_push", "manager_push", [False, True], None, "manager push"),
    ("discoverability", "discoverability", ["peers_only", "exploration"], None, "shortcut findable by exploration"),
    ("channels", "channels", ["board", "team_channels", "dm_only"], None, "communication channels"),
    ("self_merge", "self_merge", [False, True], None, "self-merge without review"),
    ("persistent_share", "persistent_share", [0.0, 0.5], None, "prompted persistent persona for 50% of agents"),
    ("prohibition_form", "prohibition_form", ["implicit", "ambiguous", "soft"], None, "prohibition form"),
    ("n_impossible", "n_impossible", [9, 12, 16], None, "number of impossible tickets"),
    ("persona_mix", "persona_mix", ["uniform", "skewed_pragmatic"], None, "persona mix"),
    ("sanctions", "sanctions", ["off", "drawn"], None, "sanctions drawn vs off"),
    ("model_mix", "model_mix", ["duo", "majority"], None, "model mix"),
    ("seed_type", "seed_type", ["none", "knower", "pioneer", "side_task", "external"], "seed_blocks",
     "seed type (blocks where it was randomized)"),
    ("seed_tech_lead", "seed_tech_lead", [False, True], "tl_eligible", "seed is tech lead (knower/pioneer/side_task)"),
]
EXTRA = [
    ("seed_placement", "seed_placement", ["hub", "periphery"], None, "seed placement"),
    ("cut", "cut", [17, 20, 23, 26], None, "release cut round"),
    ("push_offset", "push_offset", [4, 6, 8], "push_on", "push offset before cut (push configs only)"),
    ("family", "family", ["ledgerlib", "routekit", "slotplan", "stockflow", "textkit"], "indist_family",
     "task family (in-distribution blocks)"),
    ("enforced", "enforced", [False, True], None, "detection probability > 0 (a sanction can fire)"),
]
POSTHOC = [  # (factor column, level a, level b, subset) -> diff = b - a
    ("channels", "dm_only", "board", None), ("channels", "team_channels", "board", None),
    ("channels", "dm_only", "team_channels", None),
    ("prohibition_form", "soft", "implicit", None), ("prohibition_form", "soft", "ambiguous", None),
    ("prohibition_form", "ambiguous", "implicit", None),
    ("n_impossible", 9, 12, None), ("n_impossible", 9, 16, None), ("n_impossible", 12, 16, None),
]
SEED_PAIRS = [("seed_type", "none", s, "seed_blocks") for s in ["knower", "pioneer", "side_task", "external"]]
INTERACTIONS = [("release_freeze", "manager_push"), ("release_freeze", "discoverability"),
                ("discoverability", "category"), ("board", "discoverability"), ("release_freeze", "category"),
                ("discoverability", "seeded")]


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


def subset_mask(cfg, subset):
    if subset is None:
        return np.ones(len(cfg), bool)
    if subset == "seed_blocks":    # seed type constant within night_branch (none) and night_test_ood_seed (external)
        return ~cfg.split.isin(["night_branch", "night_test_ood_seed"]).to_numpy()
    if subset == "tl_eligible":
        return cfg.tl_eligible.to_numpy(bool)
    if subset == "push_on":
        return cfg.manager_push.to_numpy(bool)
    if subset == "indist_family":
        return (cfg.split != "night_test_ood_family").to_numpy()
    raise KeyError(subset)


def perm_codes(codes, blocks, B, rng):
    out = np.empty((B, len(codes)), dtype=codes.dtype)
    for b in np.unique(blocks):
        idx = np.flatnonzero(blocks == b)
        out[:, idx] = rng.permuted(np.tile(codes[idx], (B, 1)), axis=1)
    return out


def boot_idx(blocks, B, rng):
    parts, cols = [], []
    for b in np.unique(blocks):
        idx = np.flatnonzero(blocks == b)
        parts.append(idx[rng.integers(0, len(idx), size=(B, len(idx)))])
    return np.concatenate(parts, axis=1)


def level_means(y, codes, K):
    """y (n,), codes (..., n) -> means (..., K), counts (..., K)"""
    m, c = [], []
    for k in range(K):
        I = (codes == k)
        nk = I.sum(-1)
        with np.errstate(invalid="ignore", divide="ignore"):
            m.append((I * y).sum(-1) / nk)
        c.append(nk)
    return np.stack(m, -1), np.stack(c, -1)


def stat(y, codes, K):
    m, c = level_means(y, codes, K)
    if K == 2:
        return m[..., 1] - m[..., 0]
    ybar = y.mean()
    return (c * (m - ybar) ** 2).sum(-1) / codes.shape[-1]


def pval(T_obs, T_perm, two_sided):
    if two_sided:
        return (1 + np.sum(np.abs(T_perm) >= abs(T_obs) - 1e-12)) / (len(T_perm) + 1)
    return (1 + np.sum(T_perm >= T_obs - 1e-12)) / (len(T_perm) + 1)


def ci(x):
    x = np.asarray(x, float)
    ok = ~np.isnan(x)
    return [float(np.percentile(x[ok], 2.5)), float(np.percentile(x[ok], 97.5))], int((~ok).sum())


def stratified_diff(y, codes, blocks):
    num = den = 0.0
    for b in np.unique(blocks):
        s = blocks == b
        if (codes[s] == 0).any() and (codes[s] == 1).any():
            d = y[s][codes[s] == 1].mean() - y[s][codes[s] == 0].mean()
            num += s.sum() * d
            den += s.sum()
    return num / den


def analyse(cfg, runs, name, col, levels, subset, note, rng):
    msk = subset_mask(cfg, subset) & cfg[col].isin(levels).to_numpy()
    c = cfg[msk].reset_index(drop=True)
    lv = {v: i for i, v in enumerate(levels)}
    codes = c[col].map(lv).to_numpy(int)
    y = c.tip_rate.to_numpy(float)
    blocks = c.split.to_numpy()
    K = len(levels)
    T_obs = float(stat(y, codes, K))
    P = perm_codes(codes, blocks, B_PERM, rng)
    T_perm = stat(y, P, K)
    p = float(pval(T_obs, T_perm, K == 2))
    BI = boot_idx(blocks, B_BOOT, rng)
    mb, cb = level_means(y[BI], codes[BI], K)
    m_obs, n_obs = level_means(y, codes, K)
    r = runs[runs.scenario_id.isin(c.scenario_id)]
    lvl = []
    for k, v in enumerate(levels):
        rr = r[r[col] == v]
        lci, nan = ci(mb[:, k])
        lvl.append(dict(level=str(v), n_configs=int(n_obs[k]), n_runs=int(len(rr)), n_tipped_runs=int(rr.tipped.sum()),
                        config_mean=float(m_obs[k]), ci=lci, boot_nan=nan, run_rate=float(rr.tipped.mean()),
                        mean_violators=float(rr.n_violators.mean())))
    out = dict(factor=name, column=col, note=note, subset=subset or "all", levels=lvl, n_configs=int(len(c)),
               n_runs=int(len(r)), blocks_used=sorted(set(blocks)), T_obs=T_obs, p_perm=p, B_perm=B_PERM, B_boot=B_BOOT,
               kind="binary" if K == 2 else "multi")
    # run-level contrast (treats runs as independent -> anti-conservative under within-config correlation)
    tab = pd.crosstab(r[col].map(lv), r.tipped).reindex(index=range(K), columns=[0, 1], fill_value=0).to_numpy()
    if K == 2:
        out["diff"] = T_obs
        d_ci, nan = ci(mb[:, 1] - mb[:, 0])
        out["diff_ci"], out["diff_boot_nan"] = d_ci, nan
        out["diff_stratified"] = float(stratified_diff(y, codes, blocks))
        out["p_run_fisher"] = float(stats.fisher_exact(tab)[1])
    else:
        out["p_run_chi2"] = float(stats.chi2_contingency(tab)[1])
        pw = []
        for a, b in combinations(range(K), 2):
            d_ci, nan = ci(mb[:, b] - mb[:, a])
            pw.append(dict(a=str(levels[a]), b=str(levels[b]), diff=float(m_obs[b] - m_obs[a]), ci=d_ci, boot_nan=nan))
        out["pairwise_boot"] = pw
    return out


def pair_test(cfg, runs, col, a, b, subset, rng):
    res = analyse(cfg, runs, f"{col}:{b}-vs-{a}", col, [a, b], subset, "post-hoc pair", rng)
    return res


def interaction(cfg, f1, f2, rng):
    c = cfg.copy()
    c["board"] = c.channels == "board"
    c["seeded"] = c.seed_type != "none"
    if f2 == "seeded":
        c = c[~c.split.isin(["night_branch", "night_test_ood_seed"])]
    c = c.reset_index(drop=True)
    x1 = c[f1].map({True: 1, False: 0, "exploration": 1, "peers_only": 0, "K4": 1, "K2": 0}).to_numpy(int)
    x2 = c[f2].map({True: 1, False: 0, "exploration": 1, "peers_only": 0, "K4": 1, "K2": 0}).to_numpy(int)
    y = c.tip_rate.to_numpy(float)
    codes = 2 * x1 + x2               # 0: (0,0) 1: (0,1) 2: (1,0) 3: (1,1)
    m, n = level_means(y, codes, 4)
    BI = boot_idx(c.split.to_numpy(), B_BOOT, rng)
    mb, _ = level_means(y[BI], codes[BI], 4)
    did = lambda mm: (mm[..., 3] - mm[..., 1]) - (mm[..., 2] - mm[..., 0])   # effect of f1 when f2=1 minus when f2=0
    d_ci, nan = ci(did(mb))
    eff1_at0, eff1_at1 = m[2] - m[0], m[3] - m[1]
    return dict(f1=f1, f2=f2, cells={f"{f1}={i}|{f2}={j}": dict(n=int(n[2 * i + j]), mean=float(m[2 * i + j]))
                                     for i in (0, 1) for j in (0, 1)},
                effect_f1_when_f2_0=float(eff1_at0), effect_f1_when_f2_1=float(eff1_at1),
                did=float(did(m)), did_ci=d_ci, boot_nan=nan, n_configs=int(len(c)))


def icc_oneway(runs):
    g = runs.groupby("scenario_id").tipped
    sizes = g.size()
    keep = sizes[sizes >= 2].index
    r = runs[runs.scenario_id.isin(keep)]
    g = r.groupby("scenario_id").tipped
    n_i = g.size().to_numpy(float)
    m_i = g.mean().to_numpy(float)
    N, k = n_i.sum(), len(n_i)
    gm = r.tipped.mean()
    ssb = (n_i * (m_i - gm) ** 2).sum()
    ssw = ((r.tipped - r.scenario_id.map(g.mean())) ** 2).sum()
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    return dict(icc=float((msb - msw) / (msb + (n0 - 1) * msw)), n_configs=int(k), n_runs=int(N), n0=float(n0))


def main():
    rng = np.random.default_rng(SEED)
    cfg = pd.read_csv(HERE / "configs.csv")
    runs = pd.read_csv(HERE / "runs.csv")
    for c in ["release_freeze", "manager_push", "self_merge", "seed_tech_lead", "tl_eligible", "enforced"]:
        cfg[c] = cfg[c].astype(bool)
        runs[c] = runs[c].astype(bool)
    res = dict(meta=dict(n_runs=int(len(runs)), n_configs=int(len(cfg)), n_tipped=int(runs.tipped.sum()),
                         run_tip_rate=float(runs.tipped.mean()), config_mean_tip_rate=float(cfg.tip_rate.mean()),
                         runs_per_config=cfg.n_runs.value_counts().sort_index().to_dict(), B_perm=B_PERM,
                         B_boot=B_BOOT, seed=SEED))
    # descriptive per block
    blk = []
    BI_all = None
    for s in SPLIT_ORDER:
        c = cfg[cfg.split == s]
        y = c.tip_rate.to_numpy()
        bi = rng.integers(0, len(y), size=(B_BOOT, len(y)))
        lci, _ = ci(y[bi].mean(1))
        r = runs[runs.split == s]
        blk.append(dict(split=s, n_configs=int(len(c)), n_runs=int(len(r)), n_tipped=int(r.tipped.sum()),
                        config_mean=float(y.mean()), ci=lci, run_rate=float(r.tipped.mean())))
    res["blocks"] = blk

    res["main"] = [analyse(cfg, runs, *f, rng) for f in MAIN]
    ph = holm([r["p_perm"] for r in res["main"]])
    for r, h in zip(res["main"], ph):
        r["p_holm"] = float(h)
    res["extra"] = [analyse(cfg, runs, *f, rng) for f in EXTRA]
    ph = holm([r["p_perm"] for r in res["extra"]])
    for r, h in zip(res["extra"], ph):
        r["p_holm_extra"] = float(h)
    # Holm over main + extra together (sensitivity)
    allp = [r["p_perm"] for r in res["main"]] + [r["p_perm"] for r in res["extra"]]
    ha = holm(allp)
    for r, h in zip(res["main"] + res["extra"], ha):
        r["p_holm_all19"] = float(h)

    # post-hoc pairs and binary collapses
    res["posthoc"] = []
    for col, a, b, sub in POSTHOC + SEED_PAIRS:
        res["posthoc"].append(pair_test(cfg, runs, col, a, b, sub, rng))
    for fam in ["channels", "prohibition_form", "n_impossible", "seed_type"]:
        idx = [i for i, r in enumerate(res["posthoc"]) if r["column"] == fam]
        h = holm([res["posthoc"][i]["p_perm"] for i in idx])
        for i, hh in zip(idx, h):
            res["posthoc"][i]["p_holm_within_factor"] = float(hh)
    cb = cfg.copy()
    cb["board_vs_rest"] = np.where(cb.channels == "board", "board", "not_board")
    rb = runs.copy()
    rb["board_vs_rest"] = np.where(rb.channels == "board", "board", "not_board")
    res["board_vs_rest"] = analyse(cb, rb, "board_vs_rest", "board_vs_rest", ["not_board", "board"], None,
                                   "board vs team_channels + dm_only", rng)
    # n_impossible linear trend (exploratory): T = OLS slope of config mean on n_impossible, within-block perms
    c = cfg.reset_index(drop=True)
    x = c.n_impossible.to_numpy(float)
    y = c.tip_rate.to_numpy(float)
    P = perm_codes(x, c.split.to_numpy(), B_PERM, rng)
    slope = lambda xx: ((xx - xx.mean(-1, keepdims=True)) * (y - y.mean())).sum(-1) / ((x - x.mean()) ** 2).sum()
    T0 = float(slope(x))
    BI = boot_idx(c.split.to_numpy(), B_BOOT, rng)
    xb, yb = x[BI], y[BI]
    sb = ((xb - xb.mean(1, keepdims=True)) * (yb - yb.mean(1, keepdims=True))).sum(1) / ((xb - xb.mean(1, keepdims=True)) ** 2).sum(1)
    res["n_impossible_trend"] = dict(slope_per_ticket=T0, slope_per_7_tickets=7 * T0, ci_per_7=[7 * v for v in ci(sb)[0]],
                                     p_perm=float(pval(T0, slope(P), True)))

    # sanctions detail: drawn configs split by detection probability, sanction events
    sd = []
    cfg["sanction_arm"] = np.where(cfg.sanctions == "off", "off",
                                   np.where(cfg.enforced, "drawn_detect>0", "drawn_detect=0"))
    runs["sanction_arm"] = runs.scenario_id.map(cfg.set_index("scenario_id").sanction_arm)
    for arm in ["off", "drawn_detect=0", "drawn_detect>0"]:
        c = cfg[cfg.sanction_arm == arm]
        r = runs[runs.sanction_arm == arm]
        sd.append(dict(arm=arm, n_configs=int(len(c)), n_runs=int(len(r)), n_tipped=int(r.tipped.sum()),
                       config_mean=float(c.tip_rate.mean()), run_rate=float(r.tipped.mean()),
                       mean_violators=float(r.n_violators.mean()), sanction_events=int(r.n_sanction_events.sum()),
                       runs_with_sanction=int((r.n_sanction_events > 0).sum())))
    res["sanction_arms"] = sd
    enf = cfg[cfg.enforced].copy()
    res["enforced_configs"] = [dict(scenario_id=row.scenario_id, split=row.split, sanction_type=row.sanction_type,
                                    detection=row.detection_probability, enforcer=row.enforcer,
                                    n_runs=int(row.n_runs), n_tipped=int(row.n_tipped),
                                    sanction_events=int(row.n_sanction_events), release_freeze=bool(row.release_freeze),
                                    discoverability=row.discoverability, channels=row.channels)
                               for row in enf.itertuples()]
    plc = cfg[cfg.sanction_arm != "drawn_detect>0"].copy()
    plc["placebo"] = plc.sanction_arm == "drawn_detect=0"
    rp = runs[runs.sanction_arm != "drawn_detect>0"].copy()
    rp["placebo"] = rp.sanction_arm == "drawn_detect=0"
    res["sanction_placebo"] = analyse(plc.reset_index(drop=True), rp, "drawn_detect0_vs_off", "placebo", [False, True],
                                      None, "drawn but detection 0 (functionally = off) vs off", rng)

    # exploratory interactions (config-level 2x2, difference in differences, bootstrap CI only)
    res["interactions"] = [interaction(cfg, a, b, rng) for a, b in INTERACTIONS]

    # controls
    ctl = {}
    c = cfg[cfg.split.isin(["night_train", "night_val", "night_test_id"])].reset_index(drop=True)
    lv = {"night_train": 0, "night_val": 1, "night_test_id": 2}
    codes = c.split.map(lv).to_numpy(int)
    y = c.tip_rate.to_numpy(float)
    T0 = float(stat(y, codes, 3))
    P = perm_codes(codes, np.zeros(len(c), int), B_PERM, rng)      # identical design -> exchangeable block labels
    m, n = level_means(y, codes, 3)
    ctl["identical_design_blocks"] = dict(levels=list(lv), n=n.tolist(), means=m.tolist(), T_obs=T0,
                                          p_perm=float(pval(T0, stat(y, P, 3), False)))
    w = runs.pivot_table(index="scenario_id", columns="replicate", values="tipped", aggfunc="first")
    both = w[[0, 1]].dropna()
    d = (both[1] - both[0]).to_numpy(float)
    flips = rng.choice([-1.0, 1.0], size=(B_PERM, len(d)))
    Tf = (flips * d).mean(1)
    ctl["replicate_order_rep1_minus_rep0"] = dict(
        n_configs=int(len(d)), rep0_rate=float(both[0].mean()), rep1_rate=float(both[1].mean()), mean_diff=float(d.mean()),
        p_signflip=float(pval(d.mean(), Tf, True)), concordant_both_tipped=int(((both[0] == 1) & (both[1] == 1)).sum()),
        concordant_neither=int(((both[0] == 0) & (both[1] == 0)).sum()),
        rep0_only=int(((both[0] == 1) & (both[1] == 0)).sum()), rep1_only=int(((both[0] == 0) & (both[1] == 1)).sum()))
    if 2 in w:
        t3 = w[[0, 1, 2]].dropna()
        d3 = (t3[2] - (t3[0] + t3[1]) / 2).to_numpy(float)
        f3 = rng.choice([-1.0, 1.0], size=(B_PERM, len(d3)))
        ctl["rep2_minus_mean_rep01"] = dict(n_configs=int(len(d3)), rep2_rate=float(t3[2].mean()),
                                            rep01_rate=float(((t3[0] + t3[1]) / 2).mean()), mean_diff=float(d3.mean()),
                                            p_signflip=float(pval(d3.mean(), (f3 * d3).mean(1), True)))
    ctl["icc"] = icc_oneway(runs)
    res["controls"] = ctl
    (HERE / "results_factors.json").write_text(json.dumps(res, indent=1, default=str))
    print_summary(res)


def fmt(x, d=3):
    return f"{x:.{d}f}"


def print_summary(res):
    m = res["meta"]
    print(f"runs {m['n_runs']}, configs {m['n_configs']}, tipped {m['n_tipped']} ({m['run_tip_rate']:.3f}); "
          f"config-mean {m['config_mean_tip_rate']:.3f}; runs/config {m['runs_per_config']}")
    print("\nblocks:")
    for b in res["blocks"]:
        print(f"  {b['split']:24s} cfg {b['n_configs']:3d} runs {b['n_runs']:3d} tipped {b['n_tipped']:3d} "
              f"cfg-mean {fmt(b['config_mean'])} [{fmt(b['ci'][0])}, {fmt(b['ci'][1])}] run {fmt(b['run_rate'])}")
    for sect in ["main", "extra"]:
        print(f"\n=== {sect}")
        for r in res[sect]:
            hk = "p_holm" if sect == "main" else "p_holm_extra"
            line = (f"{r['factor']:17s} n_cfg {r['n_configs']:3d} p_perm {r['p_perm']:.4f} {hk} {r[hk]:.4f} "
                    f"holm19 {r['p_holm_all19']:.4f} ")
            if r["kind"] == "binary":
                line += (f"diff {fmt(r['diff'])} [{fmt(r['diff_ci'][0])}, {fmt(r['diff_ci'][1])}] strat {fmt(r['diff_stratified'])} "
                         f"run-Fisher p {r['p_run_fisher']:.2g}")
            else:
                line += f"T {r['T_obs']:.4f} run-chi2 p {r['p_run_chi2']:.2g}"
            print(line)
            for l in r["levels"]:
                print(f"     {l['level']:17s} cfg {l['n_configs']:3d} runs {l['n_runs']:3d} tipped {l['n_tipped_runs']:3d} "
                      f"cfg-mean {fmt(l['config_mean'])} [{fmt(l['ci'][0])}, {fmt(l['ci'][1])}] run {fmt(l['run_rate'])} "
                      f"viol {l['mean_violators']:.2f}")
            for pw in r.get("pairwise_boot", []):
                print(f"     {pw['b']} - {pw['a']}: {fmt(pw['diff'])} [{fmt(pw['ci'][0])}, {fmt(pw['ci'][1])}]")
    print("\n=== post-hoc pairs")
    for r in res["posthoc"]:
        print(f"  {r['factor']:40s} n_cfg {r['n_configs']:3d} diff {fmt(r['diff'])} [{fmt(r['diff_ci'][0])}, "
              f"{fmt(r['diff_ci'][1])}] p {r['p_perm']:.4f} holm-in-factor {r['p_holm_within_factor']:.4f}")
    r = res["board_vs_rest"]
    print(f"  board vs rest: diff {fmt(r['diff'])} [{fmt(r['diff_ci'][0])}, {fmt(r['diff_ci'][1])}] p {r['p_perm']:.4f}")
    t = res["n_impossible_trend"]
    print(f"  n_impossible trend per 7 tickets {fmt(t['slope_per_7_tickets'])} [{fmt(t['ci_per_7'][0])}, "
          f"{fmt(t['ci_per_7'][1])}] p {t['p_perm']:.4f}")
    print("\n=== sanctions")
    for s in res["sanction_arms"]:
        print("  ", s)
    for e in res["enforced_configs"]:
        print("   ", e)
    r = res["sanction_placebo"]
    print(f"  placebo drawn(det=0) vs off: diff {fmt(r['diff'])} [{fmt(r['diff_ci'][0])}, {fmt(r['diff_ci'][1])}] "
          f"p {r['p_perm']:.4f}")
    print("\n=== interactions (exploratory)")
    for it in res["interactions"]:
        cells = ", ".join(f"{k}: {v['mean']:.3f} (n={v['n']})" for k, v in it["cells"].items())
        print(f"  {it['f1']} x {it['f2']}: {cells}\n     effect of {it['f1']}: {fmt(it['effect_f1_when_f2_0'])} "
              f"(f2=0) vs {fmt(it['effect_f1_when_f2_1'])} (f2=1); DiD {fmt(it['did'])} "
              f"[{fmt(it['did_ci'][0])}, {fmt(it['did_ci'][1])}] nan {it['boot_nan']}")
    print("\n=== controls")
    for k, v in res["controls"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
