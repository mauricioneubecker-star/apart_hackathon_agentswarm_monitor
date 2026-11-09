#!/usr/bin/env python3
"""Step 4: primary inference (ANALYSIS_PLAN.md sections 3-4) on the harness CV rows of night_train.

Unit of resampling = config (64). Paired cluster bootstrap, B resamples, same draws for every predictor and
statistic. Statistic for (b) = pooled AUROC of the repeat-averaged ID out-of-fold scores (harness.id_oof, as in
evaluate.py --pairs); for (a) = harness time-matched AUROC (round bins 1-5, 6-10, ..., positive-weighted) on the
same OOF scores. Estimate = full-sample difference; CI = 2.5/97.5 % percentiles of the bootstrap differences;
p = 2 min(P*(d <= 0), P*(d >= 0)), floored at 1/B. Holm over the 11 primary comparisons.
LODO: per comparison, sign of the difference of the same statistic in each of the 8 LODO folds (fold-specific
predictions), exact two-sided binomial sign test.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statlib as L  # noqa: E402

PRIMARY = {"clock": "hgb_clock.csv", "bag+graph": "hgb_bag+graph.csv", "zs:pairwise": "zs_pairwise.csv",
           "zs:global_full": "zs_global_full.csv", "gnn_final": "final.csv",
           "gnn_hybrid": "final+hgb_bag+graph+mem.csv"}
EXTRA = {"bag+graph+mem": "hgb_bag+graph+mem.csv", "zs:global_window": "zs_global_window.csv",
         "edge_monitor_top3": "edge_monitor_top3.csv", "bag": "hgb_bag.csv", "oracle_risk": "oracle_risk.csv"}
FAM_A = [(m, "clock") for m in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid")]
FAM_B = [("gnn_final", "bag+graph"), ("gnn_hybrid", "bag+graph"), ("zs:pairwise", "bag+graph"),
         ("zs:pairwise", "gnn_final"), ("zs:pairwise", "gnn_hybrid"), ("zs:global_full", "bag+graph")]
SUPP_A = [("bag+graph+mem", "clock"), ("zs:global_window", "clock")]
SUPP_B = [("gnn_final", "bag+graph+mem"), ("gnn_hybrid", "bag+graph+mem"), ("zs:pairwise", "bag+graph+mem"),
          ("zs:global_full", "bag+graph+mem"), ("bag+graph+mem", "bag+graph"), ("zs:global_window", "bag+graph"),
          ("zs:pairwise", "zs:global_full"), ("zs:pairwise", "zs:global_window"), ("gnn_hybrid", "gnn_final"),
          ("zs:pairwise", "edge_monitor_top3"), ("zs:pairwise", "oracle_risk")] + \
    [(m, "clock") for m in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", required=True, help="data/llm_monitor/_base/snapshots.csv")
    ap.add_argument("--folds", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--harness", required=True, help="gnn_opt dir (for the equivalence checks)")
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    S, lab, cfgs = L.load_rows(a.data, a.base)
    folds = json.load(open(a.folds))
    nC = len(cfgs)
    y, t = lab.y.values, lab.t.values
    print(f"rows {len(lab)}, positives {int(y.sum())}, configs {nC}, runs {lab.run.nunique()}, "
          f"tipped runs {int(lab.groupby('run').tipped.first().sum())}, configs with a positive row "
          f"{int((lab.groupby('cfg').y.sum() > 0).sum())}")

    preds, checks = {}, {}
    for name, f in {**PRIMARY, **EXTRA}.items():
        d, chk = L.load_cv(os.path.join(a.preds, f), lab, folds)
        assert chk["fold_mismatch"] == 0 and chk["oof_missing"] == 0 and chk["folds_present"] == 18, (name, chk)
        assert chk["nan_scores"] == 0
        preds[name], checks[name] = d, chk
    print("key checks (all 18 folds, identical rows, no NaN):", {k: (v["rows_on_eval"], v["nan_scores"])
                                                                   for k, v in checks.items()})

    # ------------------------------------------------------------------ statistics objects (full sample + boot)
    st = {n: L.Stat(d["oof"], lab, nC) for n, d in preds.items()}
    st_rep = {n: {r: L.Stat(s, lab, nC) for r, s in d["rep"].items()} for n, d in preds.items()}
    one = np.ones((1, nC))

    # ------------------------------------------------------------------ equivalence checks
    sys.path.insert(0, a.harness)
    import harness as H  # noqa: E402
    import metrics as M  # noqa: E402
    eq = {}
    for n, d in preds.items():
        s = d["oof"]
        eq[n] = {"auroc_qf_minus_sklearn": float(st[n].auroc(one)[0] - roc_auc_score(y, s)),
                 "tauroc_qf_minus_harness": float(st[n].tauroc(one)[0] - M.time_matched_auroc(y, s, t)),
                 "tauroc_rtc_qf_minus_rows": float(st[n].tauroc_rtc(one)[0] - L.tauroc_rtc_rows(y, s, lab.rtc_bin.values))}
    mx = max(abs(v) for e in eq.values() for v in e.values())
    print(f"full-sample equivalence, max |diff| = {mx:.2e}")
    assert mx < 1e-10
    # random resamples: quadratic form == sklearn / harness on the concatenated resample
    rng = np.random.default_rng(1)
    idx_by = [np.where(lab.ci.values == c)[0] for c in range(nC)]
    mxr = 0.0
    for _ in range(5):
        pick = rng.integers(0, nC, nC)
        rows = np.concatenate([idx_by[c] for c in pick])
        K = np.bincount(pick, minlength=nC)[None, :].astype(float)
        for n in ("zs:pairwise", "gnn_final", "clock"):
            s = preds[n]["oof"]
            mxr = max(mxr, abs(st[n].auroc(K)[0] - roc_auc_score(y[rows], s[rows])),
                      abs(st[n].tauroc(K)[0] - M.time_matched_auroc(y[rows], s[rows], t[rows])),
                      abs(st[n].tauroc_rtc(K)[0] - L.tauroc_rtc_rows(y[rows], s[rows], lab.rtc_bin.values[rows])))
    print(f"resample equivalence (5 draws x 3 predictors), max |diff| = {mxr:.2e}")
    assert mxr < 1e-10
    # replicate evaluate.py --pairs (metrics.boot_ci, seed 0, n 1000) with the same draws
    Sh = S.copy()
    labh = Sh[Sh["eval"] == 1].copy()
    labh["y"] = labh["y3"]
    labh = labh[labh.y.notna()]
    P0 = pd.read_csv(os.path.join(a.preds, PRIMARY["zs:pairwise"]))
    base = H.id_oof(P0).merge(labh, on=["run", "round"])[["run", "round", "cfg", "y", "risk"]]
    pr = {}
    for n in ("zs:pairwise", "bag+graph", "gnn_final"):
        o = H.id_oof(pd.read_csv(os.path.join(a.preds, PRIMARY[n]))).merge(labh, on=["run", "round"])
        pr[n] = base.merge(o[["run", "round", "score"]], on=["run", "round"], how="left").score.values
    hb = M.boot_ci(base, pr, n=1000, pairs=[("zs:pairwise", "bag+graph"), ("gnn_final", "bag+graph")])
    rng0 = np.random.default_rng(0)
    cf_h = base.cfg.unique()
    code = {c: i for i, c in enumerate(cfgs)}
    K0 = np.zeros((1000, nC))
    for b in range(1000):
        pick = rng0.choice(cf_h, len(cf_h))
        for c in pick:
            K0[b, code[c]] += 1
    rep = {}
    for (u, v) in [("zs:pairwise", "bag+graph"), ("gnn_final", "bag+graph")]:
        dd = st[u].auroc(K0) - st[v].auroc(K0)
        mine = tuple(np.quantile(dd, [0.025, 0.5, 0.975])) + (float(np.mean(dd > 0)),)
        rep[f"{u}-{v}"] = {"harness_boot_ci": [float(x) for x in hb[f"{u}-{v}"]], "this_code": [float(x) for x in mine]}
    print("replication of evaluate.py --pairs bootstrap (same draws):", json.dumps(rep))
    for r in rep.values():
        assert np.allclose(r["harness_boot_ci"], r["this_code"], atol=1e-12)

    # ------------------------------------------------------------------ bootstrap
    K = L.draws(nC, a.B, a.seed)
    print(f"bootstrap: B = {a.B}, seed {a.seed}; resamples with < 2 classes: "
          f"{int(((K @ np.bincount(lab.ci, weights=y, minlength=nC)) == 0).sum())}")
    stats = {}
    full = {}
    for n in preds:
        stats[n] = {"auroc": st[n].auroc(K), "tauroc": st[n].tauroc(K), "tauroc_rtc": st[n].tauroc_rtc(K),
                    "before_ann": st[n].before_ann(K), "mixed_cfg_time": st[n].mixed_cfg_time(K),
                    "auroc_repmean": np.mean([s.auroc(K) for s in st_rep[n].values()], 0)}
        full[n] = {"auroc": float(st[n].auroc(one)[0]), "tauroc": float(st[n].tauroc(one)[0]),
                   "tauroc_rtc": float(st[n].tauroc_rtc(one)[0]), "before_ann": float(st[n].before_ann(one)[0]),
                   "mixed_cfg_time": float(st[n].mixed_cfg_time(one)[0]),
                   "auroc_repmean": float(np.mean([s.auroc(one)[0] for s in st_rep[n].values()]))}

    # ------------------------------------------------------------------ LODO per-fold statistics
    lodo_names = list(folds["lodo"].keys())

    def lodo_stat(n, f, metric):
        rows, sc = preds[n]["lodo"][f]
        yy, tt = y[rows], t[rows]
        if metric == "auroc":
            return roc_auc_score(yy, sc)
        if metric == "tauroc":
            return M.time_matched_auroc(yy, sc, tt)
        if metric == "tauroc_rtc":
            return L.tauroc_rtc_rows(yy, sc, lab.rtc_bin.values[rows])
        raise ValueError(metric)

    def compare(u, v, metric, family):
        d = stats[u][metric] - stats[v][metric]
        est = full[u][metric] - full[v][metric]
        p, nb = L.boot_p(d)
        lo, hi = np.nanquantile(d, [0.025, 0.975])
        lod = {f: lodo_stat(u, f, metric) - lodo_stat(v, f, metric) for f in lodo_names}
        sg = np.sign(est)
        same = int(sum(np.sign(x) == sg for x in lod.values()))
        npos = int(sum(x > 0 for x in lod.values()))
        nnz = int(sum(x != 0 for x in lod.values()))
        sp = binomtest(npos, nnz, 0.5).pvalue if nnz else np.nan
        r = {"comparison": f"{u} - {v}", "metric": metric, "family": family, "est": est, "ci_lo": float(lo),
             "ci_hi": float(hi), "boot_se": float(np.nanstd(d)), "share_gt0": float(np.nanmean(d > 0)),
             "p_raw": p, "B_valid": nb, f"{u}": full[u][metric], f"{v}": full[v][metric],
             "lodo_same_sign": same, "lodo_n": len(lod), "lodo_pos": npos, "sign_test_p": float(sp),
             "lodo_diffs": {k.replace("hold_", ""): float(x) for k, x in lod.items()}}
        if metric == "auroc":
            r["delong"] = L.delong_paired(y, preds[u]["oof"], preds[v]["oof"])
            dr = stats[u]["auroc_repmean"] - stats[v]["auroc_repmean"]
            pr_, _ = L.boot_p(dr)
            r["repmean"] = {"est": full[u]["auroc_repmean"] - full[v]["auroc_repmean"],
                            "ci": [float(x) for x in np.nanquantile(dr, [0.025, 0.975])], "p_raw": pr_}
        if metric == "tauroc":
            dr = stats[u]["tauroc_rtc"] - stats[v]["tauroc_rtc"]
            pr_, _ = L.boot_p(dr)
            lod2 = {f: lodo_stat(u, f, "tauroc_rtc") - lodo_stat(v, f, "tauroc_rtc") for f in lodo_names}
            r["rtc"] = {"est": full[u]["tauroc_rtc"] - full[v]["tauroc_rtc"],
                        "ci": [float(x) for x in np.nanquantile(dr, [0.025, 0.975])], "p_raw": pr_,
                        "lodo_same_sign": int(sum(np.sign(x) == np.sign(full[u]["tauroc_rtc"] - full[v]["tauroc_rtc"])
                                                  for x in lod2.values())),
                        "lodo_pos": int(sum(x > 0 for x in lod2.values())),
                        "sign_test_p": float(binomtest(int(sum(x > 0 for x in lod2.values())),
                                                       int(sum(x != 0 for x in lod2.values())), 0.5).pvalue)}
        return r

    prim = [compare(u, v, "tauroc", "primary (a)") for u, v in FAM_A] + \
           [compare(u, v, "auroc", "primary (b)") for u, v in FAM_B]
    adj = L.holm([r["p_raw"] for r in prim])
    for r, h in zip(prim, adj):
        r["p_holm"] = float(h)
    # sensitivity Holm: (a) with rounds-to-cut bins, (b) with per-repeat-mean AUROC
    sens_p = [r["rtc"]["p_raw"] for r in prim[:5]] + [r["repmean"]["p_raw"] for r in prim[5:]]
    for r, h in zip(prim, L.holm(sens_p)):
        (r["rtc"] if "rtc" in r else r["repmean"])["p_holm_sens"] = float(h)
    supp = [compare(u, v, "tauroc", "supplementary (a)") for u, v in SUPP_A] + \
           [compare(u, v, "auroc", "supplementary (b)") for u, v in SUPP_B]

    # ------------------------------------------------------------------ per-predictor descriptive table
    desc = []
    for n in preds:
        row = {"predictor": n}
        for m in ("auroc", "auroc_repmean", "tauroc", "tauroc_rtc", "mixed_cfg_time", "before_ann"):
            v = stats[n][m]
            lo, hi = np.nanquantile(v, [0.025, 0.975])
            row[m] = full[n][m]
            row[m + "_lo"], row[m + "_hi"] = float(lo), float(hi)
        for f in lodo_names:
            row["lodo_auroc:" + f.replace("hold_", "")] = float(lodo_stat(n, f, "auroc"))
            row["lodo_tauroc:" + f.replace("hold_", "")] = float(lodo_stat(n, f, "tauroc"))
        desc.append(row)
    D = pd.DataFrame(desc)
    D.to_csv(os.path.join(a.out, "descriptive_table.csv"), index=False)

    out = {"n_rows": int(len(lab)), "n_pos": int(y.sum()), "n_cfg": nC, "B": a.B, "seed": a.seed,
           "key_checks": checks, "equivalence": {"full_max_abs": mx, "resample_max_abs": mxr,
                                                "harness_boot_replication": rep},
           "primary": prim, "supplementary": supp}
    L.dump(out, os.path.join(a.out, "primary_results.json"))
    flat = []
    for r in prim + supp:
        f = {k: v for k, v in r.items() if k not in ("lodo_diffs", "delong", "repmean", "rtc")}
        f = {k: v for k, v in f.items() if k not in (r["comparison"].split(" - ")[0], r["comparison"].split(" - ")[1])}
        if "delong" in r:
            f.update({"delong_ci_lo": r["delong"]["ci"][0], "delong_ci_hi": r["delong"]["ci"][1],
                      "delong_p": r["delong"]["p"], "delong_se": r["delong"]["se"]})
        if "repmean" in r:
            f.update({"repmean_est": r["repmean"]["est"], "repmean_ci_lo": r["repmean"]["ci"][0],
                      "repmean_ci_hi": r["repmean"]["ci"][1], "repmean_p": r["repmean"]["p_raw"],
                      "repmean_p_holm": r["repmean"].get("p_holm_sens")})
        if "rtc" in r:
            f.update({"rtc_est": r["rtc"]["est"], "rtc_ci_lo": r["rtc"]["ci"][0], "rtc_ci_hi": r["rtc"]["ci"][1],
                      "rtc_p": r["rtc"]["p_raw"], "rtc_p_holm": r["rtc"].get("p_holm_sens"),
                      "rtc_lodo_same_sign": r["rtc"]["lodo_same_sign"], "rtc_sign_test_p": r["rtc"]["sign_test_p"]})
        f.update({"lodo:" + k: v for k, v in r["lodo_diffs"].items()})
        flat.append(f)
    pd.DataFrame(flat).to_csv(os.path.join(a.out, "comparisons.csv"), index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print("\n== per-predictor (full-sample estimate [95% cluster-bootstrap percentile CI]) ==")
    for _, r in D.iterrows():
        print(f"{r.predictor:18s} AUROC(oof) {r.auroc:.3f} [{r.auroc_lo:.3f},{r.auroc_hi:.3f}]  "
              f"AUROC(rep-mean) {r.auroc_repmean:.3f}  tAUROC {r.tauroc:.3f} [{r.tauroc_lo:.3f},{r.tauroc_hi:.3f}]  "
              f"tAUROC_rtc {r.tauroc_rtc:.3f} [{r.tauroc_rtc_lo:.3f},{r.tauroc_rtc_hi:.3f}]  "
              f"mixed cfg x time {r.mixed_cfg_time:.3f} [{r.mixed_cfg_time_lo:.3f},{r.mixed_cfg_time_hi:.3f}]  "
              f"before-ann {r.before_ann:.3f} [{r.before_ann_lo:.3f},{r.before_ann_hi:.3f}]")
    print("\n== primary family (Holm over 11) ==")
    for r in prim:
        print(f"{r['family']:13s} {r['comparison']:30s} {r['metric']:7s} d={r['est']:+.4f} "
              f"[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}] p={r['p_raw']:.4f} holm={r['p_holm']:.4f} "
              f"LODO same sign {r['lodo_same_sign']}/8 (pos {r['lodo_pos']}, sign p={r['sign_test_p']:.3f})"
              + (f" | DeLong [{r['delong']['ci'][0]:+.4f},{r['delong']['ci'][1]:+.4f}] p={r['delong']['p']:.2g}"
                 f" | rep-mean d={r['repmean']['est']:+.4f} [{r['repmean']['ci'][0]:+.4f},{r['repmean']['ci'][1]:+.4f}]"
                 f" p={r['repmean']['p_raw']:.4f} holm_s={r['repmean']['p_holm_sens']:.4f}" if 'delong' in r else "")
              + (f" | rtc d={r['rtc']['est']:+.4f} [{r['rtc']['ci'][0]:+.4f},{r['rtc']['ci'][1]:+.4f}] "
                 f"p={r['rtc']['p_raw']:.4f} holm_s={r['rtc']['p_holm_sens']:.4f} LODO {r['rtc']['lodo_same_sign']}/8"
                 if 'rtc' in r else ""))
    print("\n== supplementary (no multiplicity correction) ==")
    for r in supp:
        print(f"{r['family']:18s} {r['comparison']:34s} {r['metric']:7s} d={r['est']:+.4f} "
              f"[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}] p={r['p_raw']:.4f} LODO same sign {r['lodo_same_sign']}/8 "
              f"(sign p={r['sign_test_p']:.3f})"
              + (f" | DeLong [{r['delong']['ci'][0]:+.4f},{r['delong']['ci'][1]:+.4f}] p={r['delong']['p']:.2g}"
                 if 'delong' in r else ""))


if __name__ == "__main__":
    main()
