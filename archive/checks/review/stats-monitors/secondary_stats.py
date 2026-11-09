#!/usr/bin/env python3
"""Step 5 (secondary, exploratory, no multiplicity correction per ANALYSIS_PLAN.md section 9).

A. GNN structure controls and feature ablations (id0 folds, seed 0) vs the matched reference m_noer (same config
   {epochs 30, edge_readout off}, seed 0; its id0 folds = m_noer__s1, the reference of RESULTS.md step 5).
B. Seed noise floor: s_base / s_base_r1 / s_base_r2 (DEFAULT config, seeds 0 / 100 / 200, id0) and
   m_noer_swa vs m_noer_swa_s1, m_tmemgru vs m_tmemgru_s1 (seed 0 vs seed 100 = "seed 2" in RESULTS.md, 18 folds);
   rerun pair s_noer vs m_noer id0 (same config and seed, separate runs).
C. Architecture differences: m_* candidates on 18 folds (seed 0) and the id0 screen (s_* vs s_base, seed 0).
Same cluster bootstrap as the primary analysis (configs, B draws, same seed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import t as tdist
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statlib as L  # noqa: E402

CTRL = {"control rewire": "m_ctl_rewire__id0", "control shuffle_ef": "m_ctl_shuffle_ef__id0",
        "control shuffle_labels": "m_ctl_shuffle_labels__id0", "control shuffle_rows": "m_ctl_shuffle_rows__id0",
        "ablation +clock": "m_abl_clock__id0", "ablation +lex": "m_abl_lex__id0", "ablation S2": "m_abl_S2__id0",
        "ablation S1": "m_abl_S1__id0", "ablation S0": "m_abl_S0__id0"}
SCREEN = ["s_noer", "s_novn", "s_gtemp_none_tmem_gru", "s_gine", "s_noer_noap", "s_pw6", "s_wnode1_wrisk05",
          "s_wnode0", "s_focal2", "s_focal1_pw3", "s_tf", "s_noap", "s_gatv2", "s_norev", "s_pw1", "s_tmem_conv5",
          "s_waux0", "s_tmem_gru", "s_gtemp_conv5", "s_noauxloss", "s_wrisk0", "s_gtemp_none"]
SEED_ID0 = [("s_base", "s_base_r1"), ("s_base", "s_base_r2"), ("s_base_r1", "s_base_r2")]
SEED_18 = [("m_noer_swa", "m_noer_swa_s1"), ("m_tmemgru", "m_tmemgru_s1")]
ARCH18 = [("m_noer_swa", "m_noer"), ("m_tmemgru", "m_noer"), ("m_noer_crop10", "m_noer"),
          ("m_tmemgru", "m_noer_swa"), ("gnn_final", "m_noer_swa"), ("gnn_final", "m_tmemgru")]


def id0_vec(path, lab):
    P = pd.read_csv(path)
    P = P[P.fold.str.startswith("id0_")]
    k = lab[["run", "round"]].assign(row=np.arange(len(lab)))
    m = P.merge(k, on=["run", "round"], how="inner")
    assert not m.row.duplicated().any() and len(m) == len(lab) and m.score.notna().all(), path
    v = np.full(len(lab), np.nan)
    v[m.row.values] = m.score.values
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--harness", required=True)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.harness)
    import harness as H  # noqa: E402
    S, lab, cfgs = L.load_rows(a.data, a.base)
    folds = json.load(open(a.folds))
    nC = len(cfgs)
    y, t = lab.y.values, lab.t.values
    K = L.draws(nC, a.B, a.seed)
    one = np.ones((1, nC))
    pth = lambda n: os.path.join(a.preds, ("final" if n == "gnn_final" else n) + ".csv")  # noqa: E731

    # ---------------------------------------------------------------- consistency checks of the GNN files
    chk = {}
    for base in ("m_noer", "m_noer_swa", "m_tmemgru", "m_noer_crop10"):
        full = pd.read_csv(pth(base))
        s1 = pd.read_csv(pth(base + "__s1"))
        i1 = pd.read_csv(pth(base + "__id1"))
        part = pd.concat([s1, i1])
        mm = full.merge(part, on=["run", "round", "fold"], how="outer", suffixes=("", "_p"), indicator=True)
        chk[base] = {"rows_full": len(full), "rows_parts": len(part), "unmatched": int((mm._merge != "both").sum()),
                     "max_abs_score_diff": float((mm.score - mm.score_p).abs().max())}
    # final = probability mean of the 4 members?
    mem = ["m_noer_swa", "m_noer_swa_s1", "m_tmemgru", "m_tmemgru_s1"]
    F = pd.read_csv(pth("gnn_final"))
    acc = F[["run", "round", "fold", "score"]].rename(columns={"score": "final"})
    for n in mem:
        acc = acc.merge(pd.read_csv(pth(n))[["run", "round", "fold", "score"]].rename(columns={"score": n}),
                        on=["run", "round", "fold"], how="left")
    chk["final_vs_mean_of_4_members"] = {"rows": len(acc), "missing": int(acc[mem].isna().any(axis=1).sum()),
                                         "max_abs_diff": float((acc.final - acc[mem].mean(1)).abs().max())}
    Hy = pd.read_csv(os.path.join(a.preds, "final+hgb_bag+graph+mem.csv"))
    G = pd.read_csv(os.path.join(a.preds, "hgb_bag+graph+mem.csv"))
    hh = Hy.merge(F, on=["run", "round", "fold"], suffixes=("", "_f")).merge(G, on=["run", "round", "fold"],
                                                                              suffixes=("", "_g"))
    lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731
    bl = 1 / (1 + np.exp(-(0.5 * lg(hh.score_f) + 0.5 * lg(hh.score_g))))
    chk["hybrid_vs_logit_mean_final_hgbmem"] = {"rows": len(hh), "max_abs_diff": float((hh.score - bl).abs().max())}
    print("file checks:", json.dumps(chk, indent=None))

    # ---------------------------------------------------------------- id0 vectors
    names_id0 = ["m_noer", "s_base", "s_base_r1", "s_base_r2", "m_noer_swa", "m_noer_swa_s1", "m_tmemgru",
                 "m_tmemgru_s1", "m_noer_crop10", "gnn_final"] + list(CTRL.values()) + SCREEN
    V = {n: id0_vec(pth(n), lab) for n in names_id0}
    st = {n: L.Stat(v, lab, nC) for n, v in V.items()}
    bo = {n: {"auroc": s.auroc(K), "tauroc": s.tauroc(K)} for n, s in st.items()}
    fu = {n: {"auroc": float(s.auroc(one)[0]), "tauroc": float(s.tauroc(one)[0]),
              "auprc": float(average_precision_score(y, V[n]))} for n, s in st.items()}
    # check m_noer id0 against RESULTS.md step 5 (0.871) and mac_log (0.8710905)
    print(f"m_noer id0 AUROC {fu['m_noer']['auroc']:.4f}  AUPRC {fu['m_noer']['auprc']:.4f}  "
          f"tAUROC {fu['m_noer']['tauroc']:.4f}")

    def cmp(u, v, src_b, src_f, metric="auroc"):
        d = src_b[u][metric] - src_b[v][metric]
        est = src_f[u][metric] - src_f[v][metric]
        p, _ = L.boot_p(d)
        lo, hi = np.nanquantile(d, [0.025, 0.975])
        return {"u": u, "v": v, "metric": metric, "u_val": src_f[u][metric], "v_val": src_f[v][metric],
                "est": est, "ci_lo": float(lo), "ci_hi": float(hi), "se": float(np.nanstd(d)), "p_raw": p}

    # ---------------------------------------------------------------- B. seed noise
    seed_rows = []
    for u, v in SEED_ID0 + [(x, y_) for x, y_ in SEED_18] + [("s_noer", "m_noer")]:
        for m in ("auroc", "tauroc"):
            r = cmp(u, v, bo, fu, m)
            r["set"] = "id0"
            r["kind"] = "rerun same seed" if (u, v) == ("s_noer", "m_noer") else "seed"
            seed_rows.append(r)
    # 18-fold repeat-averaged OOF for the seed pairs / architectures
    names18 = ["m_noer", "m_noer_swa", "m_noer_swa_s1", "m_tmemgru", "m_tmemgru_s1", "m_noer_crop10", "gnn_final"]
    O, cs = {}, {}
    for n in names18:
        d, ck = L.load_cv(pth(n), lab, folds)
        assert ck["fold_mismatch"] == 0 and ck["folds_present"] == 18 and ck["oof_missing"] == 0, (n, ck)
        O[n] = d["oof"]
        c = H.cv_summary(S, pd.read_csv(pth(n)))
        cs[n] = {"select": c["select"], "id_auroc_repmean": c["id_auroc"], "lodo_mean": c["lodo_mean"],
                 "lodo_min": c["lodo_min"]}
    st18 = {n: L.Stat(v, lab, nC) for n, v in O.items()}
    bo18 = {n: {"auroc": s.auroc(K), "tauroc": s.tauroc(K)} for n, s in st18.items()}
    fu18 = {n: {"auroc": float(s.auroc(one)[0]), "tauroc": float(s.tauroc(one)[0])} for n, s in st18.items()}
    for u, v in SEED_18:
        for m in ("auroc", "tauroc"):
            r = cmp(u, v, bo18, fu18, m)
            r["set"] = "18-fold OOF"
            r["kind"] = "seed"
            r["d_select"] = cs[u]["select"] - cs[v]["select"]
            r["d_lodo_mean"] = cs[u]["lodo_mean"] - cs[v]["lodo_mean"]
            r["d_lodo_min"] = cs[u]["lodo_min"] - cs[v]["lodo_min"]
            seed_rows.append(r)
    SR = pd.DataFrame(seed_rows)

    # pooled seed SD of a single-seed statistic on id0 (s_base trio: 2 df; swa pair 1 df; tmemgru pair 1 df)
    def pooled_sigma(metric, src):
        trio = np.array([src[n][metric] for n in ("s_base", "s_base_r1", "s_base_r2")])
        ss = 2 * trio.var(ddof=1)
        dfs = 2
        for u, v in SEED_18:
            ss += (src[u][metric] - src[v][metric]) ** 2 / 2
            dfs += 1
        return float(np.sqrt(ss / dfs)), dfs
    noise = {}
    for m in ("auroc", "tauroc"):
        sg, dfs = pooled_sigma(m, fu)
        obs = SR[(SR.metric == m) & (SR.set == "id0") & (SR.kind == "seed")].est.abs().max()
        noise[m] = {"sigma_single_seed_id0": sg, "df": dfs, "sd_diff": float(np.sqrt(2) * sg),
                    "band95_diff": float(tdist.ppf(0.975, dfs) * np.sqrt(2) * sg), "max_obs_seed_diff_id0": float(obs)}
        # 18-fold: two seed pairs, 1 df each
        ss18 = sum((fu18[u][m] - fu18[v][m]) ** 2 / 2 for u, v in SEED_18)
        sg18 = float(np.sqrt(ss18 / 2))
        noise[m].update({"sigma_single_seed_18fold": sg18, "df_18fold": 2,
                         "band95_diff_18fold": float(tdist.ppf(0.975, 2) * np.sqrt(2) * sg18),
                         "max_obs_seed_diff_18fold": float(max(abs(fu18[u][m] - fu18[v][m]) for u, v in SEED_18))})
    print("seed noise:", json.dumps(noise, indent=None))

    def verdict(r, nz, key_band, key_max, sig2):
        tot = np.sqrt(r["se"] ** 2 + sig2)
        r["seed_aware_ci"] = [r["est"] - 1.959964 * tot, r["est"] + 1.959964 * tot]
        r["exceeds_max_seed_diff"] = bool(abs(r["est"]) > nz[key_max])
        r["exceeds_seed_band95"] = bool(abs(r["est"]) > nz[key_band])
        r["seed_aware_excludes0"] = bool(r["seed_aware_ci"][0] > 0 or r["seed_aware_ci"][1] < 0)
        return r

    # ---------------------------------------------------------------- A. controls / ablations vs m_noer (id0)
    ctl_rows = []
    for lab_, f in CTRL.items():
        for m in ("auroc", "tauroc"):
            r = cmp(f, "m_noer", bo, fu, m)
            r["variant"] = lab_
            r["u_ci"] = [float(x) for x in np.nanquantile(bo[f][m], [0.025, 0.975])]
            r["u_auprc"] = fu[f]["auprc"]
            ctl_rows.append(verdict(r, noise[m], "band95_diff", "max_obs_seed_diff_id0",
                                    2 * noise[m]["sigma_single_seed_id0"] ** 2))
    # reference itself
    ref_ci = {m: [float(x) for x in np.nanquantile(bo["m_noer"][m], [0.025, 0.975])] for m in ("auroc", "tauroc")}
    CR = pd.DataFrame(ctl_rows)

    # ---------------------------------------------------------------- C. architectures
    arch_rows = []
    for u, v in ARCH18:
        for m in ("auroc", "tauroc"):
            r = cmp(u, v, bo18, fu18, m)
            r["set"] = "18-fold OOF"
            r["d_select"] = cs[u]["select"] - cs[v]["select"]
            r["d_lodo_min"] = cs[u]["lodo_min"] - cs[v]["lodo_min"]
            arch_rows.append(verdict(r, noise[m], "band95_diff_18fold", "max_obs_seed_diff_18fold",
                                     2 * noise[m]["sigma_single_seed_18fold"] ** 2))
    scr_rows = []
    for n in SCREEN:
        for m in ("auroc", "tauroc"):
            r = cmp(n, "s_base", bo, fu, m)
            r["set"] = "id0 screen"
            scr_rows.append(verdict(r, noise[m], "band95_diff", "max_obs_seed_diff_id0",
                                    2 * noise[m]["sigma_single_seed_id0"] ** 2))
    AR, SCR = pd.DataFrame(arch_rows), pd.DataFrame(scr_rows)

    out = {"checks": chk, "noise": noise, "ref_m_noer_id0": {**fu["m_noer"], "ci": ref_ci},
           "cv_summary_18fold": cs, "fu_18fold": fu18}
    L.dump(out, os.path.join(a.out, "secondary_results.json"))
    SR.to_csv(os.path.join(a.out, "seed_noise.csv"), index=False)
    CR.to_csv(os.path.join(a.out, "controls_ablations.csv"), index=False)
    AR.to_csv(os.path.join(a.out, "architectures_18fold.csv"), index=False)
    SCR.to_csv(os.path.join(a.out, "screen_id0.csv"), index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.max_colwidth", 30)
    print(f"\nreference m_noer id0: AUROC {fu['m_noer']['auroc']:.3f} {ref_ci['auroc']}, "
          f"tAUROC {fu['m_noer']['tauroc']:.3f} {ref_ci['tauroc']}")
    print("\n== seed noise ==")
    print(SR.drop(columns=["u_val", "v_val"]).round(4).to_string(index=False))
    print("\n== controls / ablations vs m_noer (id0) ==")
    print(CR[["variant", "metric", "u_val", "u_ci", "u_auprc", "est", "ci_lo", "ci_hi", "p_raw",
              "exceeds_max_seed_diff", "exceeds_seed_band95", "seed_aware_ci", "seed_aware_excludes0"]]
          .round(4).to_string(index=False))
    print("\n== architectures (18 folds) ==")
    print(AR[["u", "v", "metric", "u_val", "v_val", "est", "ci_lo", "ci_hi", "p_raw", "d_select", "d_lodo_min",
              "exceeds_max_seed_diff", "exceeds_seed_band95", "seed_aware_excludes0"]].round(4).to_string(index=False))
    print("\n== id0 screen vs s_base ==")
    print(SCR[["u", "metric", "u_val", "est", "ci_lo", "ci_hi", "p_raw", "exceeds_max_seed_diff",
               "exceeds_seed_band95", "seed_aware_excludes0"]].round(4).to_string(index=False))
    print("\n18-fold cv summaries:", json.dumps({k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in cs.items()}))


if __name__ == "__main__":
    main()
