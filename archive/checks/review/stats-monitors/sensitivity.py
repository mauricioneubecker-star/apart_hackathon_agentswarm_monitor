#!/usr/bin/env python3
"""Sensitivity add-ons (exploratory):
 1. AUPRC of the repeat-averaged OOF scores with cluster-bootstrap CIs (same draws as the primary analysis).
 2. Seed-aware version of the primary (b) comparisons that involve the GNN: add the single-model training-seed
    variance of the 18-fold OOF AUROC (estimated from the two seed-0 / seed-100 pairs, secondary_results.json) to the
    config-bootstrap variance. Pessimistic for the 4-member ensemble (no variance reduction from ensembling assumed).
    LLM sampling noise of the zero-shot monitors is NOT included (not measurable for pairwise, k = 1).
 3. LLM sampling noise of zs:global_full: first sample only (p_tip_3_s0) vs mean of k = 3 samples (p_tip_3).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import average_precision_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statlib as L  # noqa: E402
from primary_stats import EXTRA, PRIMARY  # noqa: E402


def weighted_ap(s, y, W):
    """Average precision (sklearn definition, distinct thresholds) for each row of the weight matrix W (B x n)."""
    o = np.argsort(-s, kind="mergesort")
    ss, yy = s[o], y[o]
    starts = np.r_[0, np.where(np.diff(ss) != 0)[0] + 1]
    Wo = W[:, o]
    tp = np.add.reduceat(Wo * yy, starts, axis=1).cumsum(1)
    fp = np.add.reduceat(Wo * (1 - yy), starts, axis=1).cumsum(1)
    P = tp[:, -1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        prec = tp / (tp + fp)
        rec = tp / P
    drec = np.diff(np.c_[np.zeros(len(W)), rec], axis=1)
    return np.nansum(drec * np.nan_to_num(prec), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--llm-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261108)
    a = ap.parse_args()
    S, lab, cfgs = L.load_rows(a.data, a.base)
    folds = json.load(open(a.folds))
    nC = len(cfgs)
    y = lab.y.values.astype(float)
    K = L.draws(nC, a.B, a.seed)
    one = np.ones((1, nC))
    ci = lab.ci.values
    res = {"prevalence": float(y.mean())}

    # 1. AUPRC with CIs
    preds = {n: L.load_cv(os.path.join(a.preds, f), lab, folds)[0]["oof"] for n, f in {**PRIMARY, **EXTRA}.items()}
    rng = np.random.default_rng(3)
    idx_by = [np.where(ci == c)[0] for c in range(nC)]
    mx = 0.0
    for _ in range(5):                                       # check vs sklearn on concatenated resamples
        pick = rng.integers(0, nC, nC)
        rows = np.concatenate([idx_by[c] for c in pick])
        Kc = np.bincount(pick, minlength=nC)[None, :].astype(float)
        for n in ("zs:pairwise", "gnn_final"):
            mx = max(mx, abs(weighted_ap(preds[n], y, Kc[:, ci])[0] - average_precision_score(y[rows], preds[n][rows])))
    print(f"weighted AP vs sklearn on resamples: max |diff| {mx:.2e}")
    assert mx < 1e-10
    ap_tab = {}
    for n, s in preds.items():
        full = float(weighted_ap(s, y, one[:, ci])[0])
        assert abs(full - average_precision_score(y, s)) < 1e-12
        vals = np.concatenate([weighted_ap(s, y, K[i:i + 1000][:, ci]) for i in range(0, a.B, 1000)])
        lo, hi = np.quantile(vals, [0.025, 0.975])
        ap_tab[n] = {"auprc": full, "lo": float(lo), "hi": float(hi)}
        print(f"AUPRC {n:18s} {full:.3f} [{lo:.3f}, {hi:.3f}]")
    res["auprc"] = ap_tab

    # 2. seed-aware primary (b)
    P = json.load(open(os.path.join(a.out, "primary_results.json")))
    Sx = json.load(open(os.path.join(a.out, "secondary_results.json")))
    sig = Sx["noise"]["auroc"]["sigma_single_seed_18fold"]
    sens = []
    for r in P["primary"] + P["supplementary"]:
        if r["metric"] != "auroc":
            continue
        u, v = r["comparison"].split(" - ")
        g = sum(x.startswith("gnn") for x in (u, v))
        if not g:
            continue
        tot = float(np.sqrt(r["boot_se"] ** 2 + g * sig ** 2))
        z = r["est"] / tot
        sens.append({"comparison": r["comparison"], "family": r["family"], "est": r["est"], "boot_se": r["boot_se"],
                     "seed_sd_added": float(np.sqrt(g) * sig), "total_se": tot,
                     "ci": [r["est"] - 1.959964 * tot, r["est"] + 1.959964 * tot], "p_normal": float(2 * norm.sf(abs(z)))})
        print(f"seed-aware {r['comparison']:32s} d={r['est']:+.4f} se_boot={r['boot_se']:.4f} total={tot:.4f} "
              f"CI [{sens[-1]['ci'][0]:+.4f}, {sens[-1]['ci'][1]:+.4f}] p={sens[-1]['p_normal']:.4f}")
    res["seed_aware"] = sens
    res["seed_sigma_18fold"] = sig

    # 3. LLM sampling noise of global_full
    G = pd.read_csv(os.path.join(a.llm_root, "global_full", "snapshots.csv"), low_memory=False).rename(
        columns={"episode_id": "run", "t": "round"})
    m = lab[["run", "round"]].merge(G[["run", "round", "p_tip_3", "p_tip_3_s0", "p_tip_3_sd", "n_samples", "zs_tip"]],
                                    on=["run", "round"], how="left")
    assert len(m) == len(lab) and m.p_tip_3.notna().all()
    assert np.allclose(m.zs_tip.values, m.p_tip_3.values / 100)
    st_mean = L.Stat(m.p_tip_3.values / 100, lab, nC)
    st_s0 = L.Stat(m.p_tip_3_s0.values / 100, lab, nC)
    out3 = {"n_samples": m.n_samples.value_counts().to_dict(), "mean_sd_across_samples": float(m.p_tip_3_sd.mean()),
            "share_rows_sd_gt0": float((m.p_tip_3_sd > 0).mean())}
    for met in ("auroc", "tauroc"):
        b0, b1 = getattr(st_s0, met)(K), getattr(st_mean, met)(K)
        f0, f1 = float(getattr(st_s0, met)(one)[0]), float(getattr(st_mean, met)(one)[0])
        d = b0 - b1
        p, _ = L.boot_p(d)
        out3[met] = {"single_sample": f0, "mean_k3": f1, "diff": f0 - f1,
                     "ci": [float(x) for x in np.quantile(d, [0.025, 0.975])], "p": p}
    print("global_full single sample vs k=3 mean:", json.dumps(out3))
    res["global_full_sampling"] = out3
    L.dump(res, os.path.join(a.out, "sensitivity_results.json"))


if __name__ == "__main__":
    main()
