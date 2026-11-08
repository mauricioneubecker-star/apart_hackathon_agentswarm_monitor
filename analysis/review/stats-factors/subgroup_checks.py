#!/usr/bin/env python3
"""Exploratory subgroup randomization tests (interactions) + checks of the test machinery.

1. Subgroup tests: effect of factor A within each level of factor B (permutation of A within block among the configs
   of that subgroup; exact under the sharp null of no A effect in that subgroup). Exploratory, no multiplicity
   correction.
2. Null calibration: 2,000 placebo factors drawn like a 50/50 night factor (balanced within block, independent of the
   outcome) -> share of p < 0.05 and p < 0.01 must be ~ nominal.
3. Monte Carlo precision: release_freeze marginal test with 100,000 permutations (borderline after Holm).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from factor_tests import analyse, perm_codes, stat, pval, holm  # noqa: E402

SEED = 20261111


def main():
    rng = np.random.default_rng(SEED)
    cfg = pd.read_csv(HERE / "configs.csv")
    runs = pd.read_csv(HERE / "runs.csv")
    for d in (cfg, runs):
        for c in ["release_freeze", "manager_push", "self_merge", "seed_tech_lead", "tl_eligible", "enforced"]:
            d[c] = d[c].astype(bool)
    out = {"subgroups": []}
    specs = [("discoverability", ["peers_only", "exploration"], "category", ["K2", "K4"]),
             ("category", ["K2", "K4"], "discoverability", ["peers_only", "exploration"]),
             ("release_freeze", [False, True], "manager_push", [False, True]),
             ("manager_push", [False, True], "release_freeze", [False, True]),
             ("release_freeze", [False, True], "category", ["K2", "K4"]),
             ("release_freeze", [False, True], "discoverability", ["peers_only", "exploration"])]
    for a, alev, b, blev in specs:
        for bl in blev:
            c = cfg[cfg[b] == bl].reset_index(drop=True)
            r = runs[runs[b] == bl]
            res = analyse(c, r, f"{a} | {b}={bl}", a, alev, None, "subgroup", rng)
            out["subgroups"].append(dict(effect_of=a, within=f"{b}={bl}", n_configs=res["n_configs"],
                                         levels=[(l["level"], l["n_configs"], round(l["config_mean"], 4)) for l in res["levels"]],
                                         diff=res["diff"], diff_ci=res["diff_ci"], p_perm=res["p_perm"]))
    # seed none x peers_only: structural check (only the forced knower can spread the shortcut)
    sub = cfg[~cfg.split.isin(["night_branch", "night_test_ood_seed"])]
    tab = sub.groupby(["seed_type", "discoverability"]).agg(n_cfg=("tip_rate", "size"), mean=("tip_rate", "mean"),
                                                            runs=("n_runs", "sum"), tipped=("n_tipped", "sum"))
    out["seed_x_discoverability"] = tab.reset_index().to_dict(orient="records")
    br = cfg[cfg.split == "night_branch"].groupby("discoverability").agg(n_cfg=("tip_rate", "size"),
                                                                          tipped=("n_tipped", "sum"))
    out["branch_block_none_by_discoverability"] = br.reset_index().to_dict(orient="records")

    # null calibration with placebo factors
    y = cfg.tip_rate.to_numpy(float)
    blocks = cfg.split.to_numpy()
    n_plac, B = 2000, 2000
    base = np.zeros(len(cfg), int)
    for bl in np.unique(blocks):           # 50/50 within block, like weighted_balanced
        idx = np.flatnonzero(blocks == bl)
        base[idx[: len(idx) // 2]] = 1
    ps = np.empty(n_plac)
    for k in range(n_plac):
        lab = perm_codes(base, blocks, 1, rng)[0]
        T0 = stat(y, lab, 2)
        Tp = stat(y, perm_codes(lab, blocks, B, rng), 2)
        ps[k] = pval(T0, Tp, True)
    out["null_calibration"] = dict(n_placebo=n_plac, B=B, share_p_lt_05=float(np.mean(ps < 0.05)),
                                   share_p_lt_01=float(np.mean(ps < 0.01)), mean_p=float(ps.mean()),
                                   deciles=[float(np.mean(ps < q)) for q in np.arange(0.1, 1.0, 0.1)])
    # MC precision for release_freeze
    codes = cfg.release_freeze.astype(int).to_numpy()
    T0 = float(stat(y, codes, 2))
    big = 100_000
    cnt = 0
    for _ in range(10):
        Tp = stat(y, perm_codes(codes, blocks, big // 10, rng), 2)
        cnt += int(np.sum(np.abs(Tp) >= abs(T0) - 1e-12))
    p_big = (1 + cnt) / (big + 1)
    se = float(np.sqrt(p_big * (1 - p_big) / big))
    # Holm with the other 13 main p-values from results_factors.json
    rf = json.loads((HERE / "results_factors.json").read_text())
    pm = {r["factor"]: r["p_perm"] for r in rf["main"]}
    pm["release_freeze"] = p_big
    names = list(pm)
    h = holm([pm[n] for n in names])
    out["freeze_precision"] = dict(B=big, T_obs=T0, p=p_big, mc_se=se, p_holm_with_this_p=float(h[names.index("release_freeze")]))
    (HERE / "results_subgroups.json").write_text(json.dumps(out, indent=1, default=str))
    for s in out["subgroups"]:
        print(f"{s['effect_of']:16s} within {s['within']:28s} n {s['n_configs']:3d} {s['levels']} diff {s['diff']:+.3f} "
              f"[{s['diff_ci'][0]:+.3f}, {s['diff_ci'][1]:+.3f}] p {s['p_perm']:.4f}")
    print("\nseed type x discoverability (randomized-seed blocks):")
    for r in out["seed_x_discoverability"]:
        print("  ", r)
    print("branch block (seed none):", out["branch_block_none_by_discoverability"])
    print("\nnull calibration:", out["null_calibration"])
    print("freeze precision:", out["freeze_precision"])


if __name__ == "__main__":
    main()
