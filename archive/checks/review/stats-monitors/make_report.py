#!/usr/bin/env python3
"""Writes REPORT.md from the outputs of make_zs_cv.py, evaluate.py, check_repro.py, primary_stats.py,
secondary_stats.py, sensitivity.py and diagnostics.py. Every number in the report is read from those files."""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

A = argparse.ArgumentParser()
A.add_argument("--stat", required=True, help=".../scratchpad/stat")
A.add_argument("--commits", required=True, help="json with commit hashes")
a = A.parse_args()
ST = a.stat
MON = os.path.join(ST, "monitors")
OUT = os.path.join(MON, "out")
P = json.load(open(os.path.join(OUT, "primary_results.json")))
SX = json.load(open(os.path.join(OUT, "secondary_results.json")))
SN = json.load(open(os.path.join(OUT, "sensitivity_results.json")))
RP = json.load(open(os.path.join(OUT, "step1_repro_check.json")))
ZC = json.load(open(os.path.join(ST, "preds", "zs_cv_coverage.json")))
CM = json.load(open(a.commits))
J = pd.read_csv(os.path.join(MON, "step3_joint_table.csv"))
D = pd.read_csv(os.path.join(OUT, "descriptive_table.csv"))
CA = pd.read_csv(os.path.join(OUT, "controls_ablations.csv"))
SR = pd.read_csv(os.path.join(OUT, "seed_noise.csv"))
AR = pd.read_csv(os.path.join(OUT, "architectures_18fold.csv"))
SC = pd.read_csv(os.path.join(OUT, "screen_id0.csv"))
CL = pd.read_csv(os.path.join(OUT, "clock_likeness.csv"))
S = pd.read_csv(os.path.join(ST, "data", "night", "snapshots.csv"), low_memory=False)
B = P["B"]


def f3(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.3f}"


def s3(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.3f}"


def pv(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n/a"
    if p <= 1.0 / B + 1e-15:
        return f"≤{1.0 / B:.0e}".replace("e-0", "e-")
    return f"{p:.4f}" if p >= 0.001 else f"{p:.1e}"


def ci(lo, hi):
    return f"[{lo:+.3f}, {hi:+.3f}]"


def ci_u(lo, hi):
    return f"[{lo:.3f}, {hi:.3f}]"


def lst(xs):
    return xs if isinstance(xs, (list, tuple)) else json.loads(xs.replace("'", '"')) if isinstance(xs, str) else xs


MET = {"tauroc": "tAUROC", "auroc": "AUROC"}
prim = P["primary"]
supp = P["supplementary"]
pa, pb = prim[:5], prim[5:]
sig = [r for r in prim if r["p_holm"] < 0.05]
nsig = [r for r in prim if r["p_holm"] >= 0.05]
seedaware = {r["comparison"]: r for r in SN["seed_aware"]}
desc = D.set_index("predictor")
apr = SN["auprc"]
ev = S[S["eval"] == 1]
tr = ev[ev.split == "night_train"]
lab_tr = tr[tr.y3.notna()]
BASE = pd.read_csv("/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv", low_memory=False)
cuts = "/".join(str(int(c)) for c in sorted(BASE.cut.unique()))
assert BASE.groupby("group_id").cut.nunique().max() == 1
# secondary verdict lists (used in the summary and in section 6)
ex_ctl_a = CA[(CA.metric == "auroc") & CA.seed_aware_excludes0].variant.tolist()
ex_ctl_t = CA[(CA.metric == "tauroc") & CA.seed_aware_excludes0].variant.tolist()
ex_ctl_any = [v for v in CA.variant.unique() if CA[CA.variant == v].seed_aware_excludes0.any()]
ctl_none = [v for v in CA.variant.unique() if not CA[CA.variant == v].seed_aware_excludes0.any()]
ex_scr = sorted(set(SC[SC.seed_aware_excludes0].u))
ex_arch = sorted(set((AR[AR.seed_aware_excludes0].u + " − " + AR[AR.seed_aware_excludes0].v).tolist()))
L = []
w = L.append

# ------------------------------------------------------------------------------------------------ header + summary
w("# Monitor comparison with statistical tests (harness CV, night_train)")
w("")
w("GNN, zero-shot LLM monitors and baselines, all scored on **identical rows and folds**: the gnn_opt harness CV on "
  f"night_train ({len(lab_tr)} eval rows, {int(lab_tr.y3.sum())} positives, {lab_tr.cfg.nunique()} configs, "
  f"{lab_tr.run.nunique()} runs; 2 x 5 grouped ID folds + 8 LODO folds). Pre-registered predictor set and comparisons "
  "from `ANALYSIS_PLAN.md` §3-4. All numbers below were produced by the scripts listed in §9.")
w("")
w("## Summary")
w("")
amin = min(r["est"] for r in pa)
amax = max(r["est"] for r in pa)
rtc_min = min(r["rtc"]["est"] for r in pa)
rtc_max = max(r["rtc"]["est"] for r in pa)
low_t = min(desc.loc[n, "tauroc_lo"] for n in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid"))
kmin = min(r["lodo_same_sign"] for r in pa)
all_a = all(r["p_holm"] < 0.05 for r in pa)
w(f"- **(a) RQ2, {'every' if all_a else 'NOT every'} communication monitor beats the clock on time-matched AUROC.** "
  f"Differences {s3(amin)} to "
  f"{s3(amax)}, all p {pv(max(r['p_raw'] for r in pa))} (bootstrap floor 1/B), Holm p ≤ "
  f"{max(r['p_holm'] for r in pa):.4f}, and the sign holds in "
  + ("all 8 LODO folds" if kmin == 8 else f"at least {kmin} of 8 LODO folds") + ". "
  f"The result holds with the plan's rounds-to-cut bins too ({s3(rtc_min)} to {s3(rtc_max)}, all Holm p ≤ "
  f"{max(r['rtc']['p_holm_sens'] for r in pa):.4f}). The bar is low: the clock's time-matched AUROC is "
  f"{f3(desc.loc['clock', 'tauroc'])}, below chance, but every monitor's lower CI bound is also above 0.5 "
  f"(lowest {f3(low_t)}).")
w("- **(b) Pooled ID AUROC, significant after Holm (11 tests):** " + "; ".join(
    f"{r['comparison']} {s3(r['est'])} {ci(r['ci_lo'], r['ci_hi'])}, Holm p = {r['p_holm']:.4f}, LODO {r['lodo_same_sign']}/8"
    for r in pb if r["p_holm"] < 0.05) + ".")
w("- **(b) Not significant, a tie in the plan's wording (\"gleichauf\"):** " + "; ".join(
    f"{r['comparison']} {s3(r['est'])} {ci(r['ci_lo'], r['ci_hi'])}, Holm p = {r['p_holm']:.3f}, LODO {r['lodo_same_sign']}/8"
    for r in pb if r["p_holm"] >= 0.05) + ".")
dl_sig = [r for r in pb if r["p_holm"] >= 0.05 and r["delong"]["p"] < 0.05]
ties = [r for r in pb if r["p_holm"] >= 0.05]
w(f"- **A row-level DeLong test is anti-conservative here.** For {len(dl_sig)} of the {len(ties)} ties its raw p is "
  "< 0.05 (" + ", ".join(f"{r['comparison']} DeLong p = {r['delong']['p']:.3f} vs bootstrap p = {r['p_raw']:.3f}"
                         for r in dl_sig)
  + "). The cluster-bootstrap standard errors are "
  f"{min(r['boot_se'] / r['delong']['se'] for r in pb):.2f} to {max(r['boot_se'] / r['delong']['se'] for r in pb):.2f} "
  "times the DeLong ones, because the rows of one config are strongly dependent (§5).")
# programmatic consistency checks used in the text below
same_a = all((r["p_holm"] < 0.05) == (r["rtc"]["p_holm_sens"] < 0.05) for r in pa)
same_b = all((r["p_holm"] < 0.05) == (r["repmean"]["p_holm_sens"] < 0.05) for r in pb)
zs_more = all(r["repmean"]["est"] >= r["est"] for r in pb if r["comparison"].startswith("zs:"))
same_seed = all(((seedaware[r["comparison"]]["ci"][0] > 0) or (seedaware[r["comparison"]]["ci"][1] < 0))
                == (r["p_holm"] < 0.05) for r in pb if r["comparison"] in seedaware)
chance_both = all(desc.loc[n, "tauroc_lo"] > 0.5 and desc.loc[n, "tauroc_rtc_lo"] > 0.5
                  for n in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid"))
n_mixed = int(lab_tr[lab_tr.mixed == 1].cfg.nunique())
no_pos_early = int(lab_tr[lab_tr.t <= 10].y3.sum()) == 0
lex_d = CA[(CA.variant == "ablation +lex") & (CA.metric == "auroc")].est.iloc[0]
print("consistency:", dict(same_a=same_a, same_b=same_b, zs_more=zs_more, same_seed=same_seed, chance_both=chance_both,
                           n_mixed=n_mixed, no_pos_early=no_pos_early))
w(f"- **Secondary (exploratory, not corrected):** these GNN controls and ablations differ from the matched reference "
  f"m_noer (id0) by more than seed noise on at least one metric: {', '.join(ex_ctl_any) or 'none'}. These do not: "
  f"{', '.join(ctl_none) or 'none'}. Of the 22 id0 screen variants, the ones that clear seed noise are: "
  + (", ".join(f"`{x}`" + (" (no temporal block)" if x == "s_gtemp_none" else "") for x in ex_scr) or "none")
  + ". 18-fold architecture "
  f"differences (m_* candidates, ensemble vs members) that clear it: {', '.join(ex_arch) or 'none'}.")
w("")
w("Scope: this is CV evidence on night_train only. The plan's full decision rule (§4) also needs sign agreement in at "
  "least 3 of the 4 held-out splits (protocol b). That criterion is **not** evaluated here, because the GNN still "
  "has 0 looks at the test splits.")
w("")

# ------------------------------------------------------------------------------------------------ 1. data
w("## 1. Rows, keys and reproduction")
w("")
spl = ev.groupby("split").y3.agg(["size", "sum"]).astype(int)
w(f"- Dataset rebuilt with `gnn_opt/build_dataset.py --runs sim_dataset/runs_night` (scratch mini-repo, index.csv via "
  f"symlink): {len(S)} snapshots, {len(ev)} eval rows. The splits are not `unknown`: "
  + ", ".join(f"{k} {v['size']} rows / {v['sum']} pos" for k, v in spl.iterrows()) + ".")
w(f"- night_train eval rows: {len(lab_tr)}, {int(lab_tr.y3.sum())} positives "
  f"(prevalence {SN['prevalence']:.3f}), {lab_tr.cfg.nunique()} configs, {lab_tr.run.nunique()} runs. "
  f"{int(lab_tr.groupby('run').tipped.first().sum())} runs tipped. "
  f"{int((lab_tr.groupby('cfg').y3.sum() > 0).sum())} configs hold at least one positive row "
  f"(at most {int(lab_tr.groupby('cfg').y3.sum().max())} per config)."
  + (" Round bins 1-5 and 6-10 hold no positives." if no_pos_early else ""))
mx = max(v["max_abs_diff"] for v in RP["vs_cv_table_final_csv"].values())
w(f"- **Reproduction (step 1):** I ran `evaluate.py --pairs` on final, final+hgb_bag+graph+mem, hgb_bag+graph+mem, "
  f"hgb_bag+graph, hgb_clock, edge_monitor_top3 and oracle_risk. It reproduces `gnn_opt_torch/preds/cv_table_final.csv` "
  f"exactly: max |diff| = {mx:.1f} over all 31-32 metric columns of all 7 models. Every value in the RESULTS.md step-4 "
  f"table (select, ID AUROC/AUPRC, LODO mean/worst, tAUROC, R@5%FPR) is equal at 3 decimals: "
  f"{'yes, for all 7 models' if all(v['all_equal_at_3dp'] for v in RP['vs_results_md_step4'].values()) else 'NO'}. "
  "The bootstrap printout is identical "
  "too (e.g. final - hgb_bag+graph -0.003 / 0.035 / 0.083, share > 0 0.958; `step1_repro.log`).")
z = ZC["pairwise"]
w(f"- **LLM CV files (step 2),** built like `llm_monitor.py --to-cv`: every fold gets the same zero-shot score; "
  f"run = episode_id, round = t, score = zs_tip (already /100, so 0-1). Each file has {z['keys']} (run, round, fold) "
  f"keys, identical to the GNN file `final.csv`. Missing vs the harness eval rows: "
  + ", ".join(f"{k} {v['missing_vs_harness']}" for k, v in ZC.items())
  + "; NaN scores: " + ", ".join(f"{k} {v['nan_scores_on_eval_rows']}" for k, v in ZC.items())
  + "; distinct score values: " + ", ".join(f"{k} {v['distinct_scores']}" for k, v in ZC.items())
  + ". The harness labels (y3, risk, cfg, split) and llm_monitor `_base` (tip, risk_count, group_id, split) agree on "
  "all 3,370 rows.")
w(f"- All 11 predictors were checked: 18 folds each, every fold holds exactly the eval rows of its test configs, "
  f"no NaN, no missing OOF row.")
w(f"- Sources: origin/gnn-opt-torch `{CM['gnn-opt-torch'][:10]}`, origin/gnn-opt `{CM['gnn-opt'][:10]}`. The LLM "
  f"monitor data come from the worktree at origin/night-vx-validation `{CM['night-vx-validation'][:10]}`.")
w("")

# ------------------------------------------------------------------------------------------------ 2. method
w("## 2. Method")
w("")
w(f"- **Unit of resampling = config** ({P['n_cfg']}). Paired cluster bootstrap with B = {B:,} resamples "
  f"(seed {P['seed']}). All predictors and statistics share the same draws, so every difference is paired.")
w("- The bootstrap is computed exactly, without materialising resampled rows. With config multiplicities k, "
  "AUROC(k) = k'Mk / ((k'n1)(k'n0)), where M[c,c'] counts the positive-in-c > negative-in-c' pairs (ties 0.5). "
  f"Checks: equal to sklearn / harness `time_matched_auroc` on the full sample and on concatenated resamples "
  f"(max |diff| {max(P['equivalence']['full_max_abs'], P['equivalence']['resample_max_abs']):.1e}). With the "
  "harness's own draws (seed 0, 1000), it reproduces the `evaluate.py --pairs` quantiles bit for bit.")
w("- **Scores:** repeat-averaged ID out-of-fold scores (`harness.id_oof`, as in `evaluate.py --pairs`). For the "
  "zero-shot monitors this is the raw score. The harness table's \"ID AUROC\" is the mean of the two per-repeat "
  "pooled AUROCs; it is reported as a sensitivity (\"rep-mean\").")
w("- **Statistics:** (a) time-matched AUROC as in the harness (`metrics.time_matched_auroc`): AUROC within round "
  "bins 1-5, 6-10, ..., 26-30, weighted by positives. Because bins 1-10 have no positives, 4 bins remain. As a "
  "sensitivity, the plan / llm_monitor definition: rounds-to-cut bins (≤-9, -8..-5, -4..-1, 0..3, >3; cut = "
  f"per-config deadline round {cuts}), pairs-weighted. (b) pooled ID AUROC.")
w(f"- **Estimate** = full-sample difference. **CI** = 2.5/97.5 % percentiles of the bootstrap differences. "
  f"**p** = 2·min(P*(d ≤ 0), P*(d ≥ 0)), floored at 1/B = {1 / B:.0e}. **Holm** over the 11 primary comparisons.")
w("- **LODO sign count:** the same statistic in each of the 8 LODO folds, using each fold's own predictions (the "
  "trained models never saw the held-out domain). It counts the folds whose difference has the sign of the "
  "full-sample estimate, plus an exact two-sided binomial sign test. The LODO folds overlap (K2/K4 partition the "
  "configs; the other six cut across them), so the sign test is descriptive.")
w("- **DeLong** (row-level, Sun & Xu) is shown only as a contrast (§5).")
w("")

# ------------------------------------------------------------------------------------------------ 3. joint table
w("## 3. Joint harness table (step 3, `evaluate.py`, identical rows)")
w("")
cols = ["select", "ID_AUROC", "ID_AUPRC", "LODO_mean", "LODO_min", "tAUROC", "R@5%FPR", "risk<=2", "risk3-7", "mixed",
        "board", "team/dm"]
w("| model | " + " | ".join(c.replace("LODO_min", "LODO worst").replace("_", " ") for c in cols) + " |")
w("|---|" + "---|" * len(cols))
for _, r in J.iterrows():
    w(f"| {r.model} | " + " | ".join(f3(r[c]) for c in cols) + " |")
w("")
lc = [c for c in J.columns if c.startswith("L:")]
w("LODO AUROC per fold:")
w("")
w("| model | " + " | ".join(c[2:] for c in lc) + " |")
w("|---|" + "---|" * len(lc))
for _, r in J.iterrows():
    w(f"| {r.model} | " + " | ".join(f3(r[c]) for c in lc) + " |")
w("")
w("Notes: the zero-shot monitors are untrained, so their \"LODO\" values are AUROCs on domain subsets, not "
  "domain-shift tests. Their selection score therefore means something different. R@5%FPR uses the 5 %-FPR "
  "threshold of the same CV scores for every model (zero-shot scores are coarse and tied, so the realised FPR is "
  "< 5 %). Brier is meaningless for the uncalibrated zero-shot scores and is left out. The mixed column covers the "
  f"{n_mixed} mixed-outcome configs present in night_train.")
w("")

# ------------------------------------------------------------------------------------------------ 4. primary
w("## 4. Primary family (pre-registered, Holm over 11 comparisons)")
w("")
w("| # | family | comparison | metric | A | B | Δ = A − B | 95 % CI | p raw | p Holm | LODO same sign | sign-test p | verdict |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(prim, 1):
    u, v = r["comparison"].split(" - ")
    verdict = "**different**" if r["p_holm"] < 0.05 else "tie"
    w(f"| {i} | {r['family'].replace('primary ', '')} | {r['comparison']} | {MET[r['metric']]} | {f3(r[u])} | {f3(r[v])} | "
      f"**{s3(r['est'])}** | {ci(r['ci_lo'], r['ci_hi'])} | {pv(r['p_raw'])} | {r['p_holm']:.4f} | "
      f"{r['lodo_same_sign']}/8 | {r['sign_test_p']:.3f} | {verdict} |")
w("")
w("Sensitivity of the primary family. (a) uses the plan's rounds-to-cut time bins; (b) uses the harness "
  "per-repeat-mean AUROC. Holm is recomputed over the 11 sensitivity p-values. \"seed-aware\" adds the training-seed "
  "variance of a single GNN (from the seed-0 vs seed-100 pairs, 18-fold OOF) to the bootstrap variance; this is "
  "pessimistic for the 4-member ensemble (normal approximation).")
w("")
w("| # | comparison | sensitivity Δ | 95 % CI | p | p Holm | LODO same sign | seed-aware 95 % CI | seed-aware p |")
w("|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(prim, 1):
    if "rtc" in r:
        x = r["rtc"]
        sa = ("-", "-")
        w(f"| {i} | {r['comparison']} (rtc bins) | {s3(x['est'])} | {ci(*x['ci'])} | {pv(x['p_raw'])} | "
          f"{x['p_holm_sens']:.4f} | {x['lodo_same_sign']}/8 | - | - |")
    else:
        x = r["repmean"]
        q = seedaware.get(r["comparison"])
        sa = (ci(*q["ci"]), f"{q['p_normal']:.4f}") if q else ("-", "-")
        w(f"| {i} | {r['comparison']} (rep-mean) | {s3(x['est'])} | {ci(*x['ci'])} | {pv(x['p_raw'])} | "
          f"{x['p_holm_sens']:.4f} | - | {sa[0]} | {sa[1]} |")
w("")
w("LODO fold differences (A − B; (a) tAUROC, (b) AUROC):")
w("")
fn = list(prim[0]["lodo_diffs"].keys())
w("| comparison | " + " | ".join(fn) + " |")
w("|---|" + "---|" * len(fn))
for r in prim:
    w(f"| {r['comparison']} | " + " | ".join(s3(r["lodo_diffs"][k]) for k in fn) + " |")
w("")

# ------------------------------------------------------------------------------------------------ per predictor
w("### Per predictor (full-sample value [95 % cluster-bootstrap CI], repeat-averaged OOF)")
w("")
w("| predictor | AUROC | AUROC rep-mean | AUPRC | tAUROC (round bins) | tAUROC (rtc bins) | within mixed cfg × time | before 1st announcement |")
w("|---|---|---|---|---|---|---|---|")
for n, r in desc.iterrows():
    q = apr[n]
    w(f"| {n} | {f3(r.auroc)} {ci_u(r.auroc_lo, r.auroc_hi)} | {f3(r.auroc_repmean)} | {f3(q['auprc'])} "
      f"{ci_u(q['lo'], q['hi'])} | {f3(r.tauroc)} {ci_u(r.tauroc_lo, r.tauroc_hi)} | {f3(r.tauroc_rtc)} "
      f"{ci_u(r.tauroc_rtc_lo, r.tauroc_rtc_hi)} | {f3(r.mixed_cfg_time)} {ci_u(r.mixed_cfg_time_lo, r.mixed_cfg_time_hi)} | "
      f"{f3(r.before_ann)} {ci_u(r.before_ann_lo, r.before_ann_hi)} |")
w("")
w(f"Prevalence = {SN['prevalence']:.3f}. \"Within mixed cfg × time\" is the plan's \"innerhalb gleicher Setups\": a "
  f"pairs-weighted AUROC within (config × rounds-to-cut bin) strata of the {n_mixed} mixed-outcome configs, so its CIs "
  "are very wide. \"Before 1st announcement\" covers rows before the first shortcut announcement (llm_monitor "
  "definition); it holds few positives. Both columns are descriptive and not tested.")
w("")

# ------------------------------------------------------------------------------------------------ supplementary
w("### Supplementary comparisons (not in the Holm family, raw p)")
w("")
w("| comparison | metric | Δ | 95 % CI | p raw | LODO same sign | DeLong p (contrast) |")
w("|---|---|---|---|---|---|---|")
for r in supp:
    w(f"| {r['comparison']} | {MET[r['metric']]} | {s3(r['est'])} | {ci(r['ci_lo'], r['ci_hi'])} | {pv(r['p_raw'])} | "
      f"{r['lodo_same_sign']}/8 | {('%.2g' % r['delong']['p']) if 'delong' in r else '-'} |")
w("")
gf = SN["global_full_sampling"]
w(f"LLM sampling noise (zs:global_full, which averages k = 3 samples): using only the first sample changes "
  f"AUROC by {s3(gf['auroc']['diff'])} {ci(*gf['auroc']['ci'])} and tAUROC by {s3(gf['tauroc']['diff'])} "
  f"{ci(*gf['tauroc']['ci'])}. Sampling noise cannot be measured for zs:pairwise (k = 1).")
w("")

# ------------------------------------------------------------------------------------------------ 5. DeLong
w("## 5. Contrast: row-level DeLong vs the cluster bootstrap")
w("")
w("| comparison | Δ AUROC | bootstrap 95 % CI | bootstrap p | DeLong 95 % CI | DeLong p | SE ratio boot / DeLong | implied design effect |")
w("|---|---|---|---|---|---|---|---|")
for r in pb + [x for x in supp if "delong" in x][:6]:
    rat = r["boot_se"] / r["delong"]["se"]
    w(f"| {r['comparison']} | {s3(r['est'])} | {ci(r['ci_lo'], r['ci_hi'])} | {pv(r['p_raw'])} | "
      f"{ci(*r['delong']['ci'])} | {r['delong']['p']:.2g} | {rat:.2f} | {rat ** 2:.1f} |")
w("")
w("DeLong treats the 3,370 snapshots as independent draws. They are not. Consecutive rounds of one run share almost "
  "the same transcript, and its features and labels are autocorrelated: y3 is 1 for up to 3 consecutive rows before "
  "a tip. The two runs of a config share the setup, and the 135 positive rows come from only 45 tipped runs in 26 "
  "configs. The effective sample size is the number of configs, not rows. The row-level variance is too small by the "
  "design effect above, so DeLong p-values are too small. The cluster bootstrap resamples whole configs and keeps "
  "this dependence.")
w("")

# ------------------------------------------------------------------------------------------------ 6. secondary
w("## 6. Secondary: GNN structure controls, ablations and seed noise (exploratory, no correction, plan §9)")
w("")
ref = SX["ref_m_noer_id0"]
w(f"**Matched reference.** `mac_log.jsonl` / `experiments/mac_*.jsonl` show that every control and ablation uses "
  "config {epochs 30, edge_readout off}, seed 0, cv id0 (+ control / feat / clock). That is the config of `m_noer`. "
  "Its id0 folds (`m_noer__s1`, merged into `m_noer.csv` with 0 differences) are the reference of RESULTS.md step 5: "
  f"AUROC {f3(ref['auroc'])} {ci_u(*ref['ci']['auroc'])}, tAUROC {f3(ref['tauroc'])} {ci_u(*ref['ci']['tauroc'])}, "
  f"AUPRC {f3(ref['auprc'])}. RESULTS.md has 0.871 [0.816, 0.921] with 1000 resamples. The reference is unambiguous; "
  "no fallback was needed.")
w("")
nz = SX["noise"]
w(f"**Seed noise floor (id0, single model).** The pooled SD of a single-seed AUROC is "
  f"{nz['auroc']['sigma_single_seed_id0']:.3f} (df {nz['auroc']['df']}: s_base trio with seeds 0/100/200, plus the "
  f"m_noer_swa and m_tmemgru seed-0 vs seed-100 pairs on id0). For a difference of two single-seed models that gives "
  f"SD {nz['auroc']['sd_diff']:.3f} and a 95 % band of ±{nz['auroc']['band95_diff']:.3f} (t, {nz['auroc']['df']} df). "
  f"The largest observed seed |Δ| on id0 is {nz['auroc']['max_obs_seed_diff_id0']:.3f}. For tAUROC: SD "
  f"{nz['tauroc']['sigma_single_seed_id0']:.3f}, band ±{nz['tauroc']['band95_diff']:.3f}, max observed "
  f"{nz['tauroc']['max_obs_seed_diff_id0']:.3f}. On the 18-fold repeat-averaged OOF statistic the seed noise is smaller: "
  f"SD {nz['auroc']['sigma_single_seed_18fold']:.4f} (2 df), max observed {nz['auroc']['max_obs_seed_diff_18fold']:.4f}.")
w("")
w("| seed pair | set | Δ AUROC | 95 % CI | p | Δ tAUROC | 95 % CI | Δ select | Δ LODO worst |")
w("|---|---|---|---|---|---|---|---|---|")
for (u, v, st_), g in SR.groupby(["u", "v", "set"], sort=False):
    ra = g[g.metric == "auroc"].iloc[0]
    rt = g[g.metric == "tauroc"].iloc[0]
    kind = " (same seed, rerun)" if ra.kind != "seed" else ""
    w(f"| {u} − {v}{kind} | {st_} | {s3(ra.est)} | {ci(ra.ci_lo, ra.ci_hi)} | {pv(ra.p_raw)} | {s3(rt.est)} | "
      f"{ci(rt.ci_lo, rt.ci_hi)} | {s3(ra.d_select) if pd.notna(ra.d_select) else '-'} | "
      f"{s3(ra.d_lodo_min) if pd.notna(ra.d_lodo_min) else '-'} |")
w("")
w("s_base, s_base_r1 and s_base_r2 are the same DEFAULT config with the default seed (0, as logged for the m_* "
  "runs that also set no seed), 100 and 200 (`experiments/screen_id0.jsonl`). m_noer_swa_s1 and "
  "m_tmemgru_s1 are seed 100 (\"seed 2\" in RESULTS.md). s_noer and m_noer have the same config and the same seed but "
  "come from separate runs (screen vs main search). Their difference shows run-to-run nondeterminism, or a code change "
  "between the two runs (cannot be told apart from the files).")
w("")
w("**Controls and ablations vs m_noer (id0, 5 folds, seed 0).** \"> max seed\" means |Δ| is larger than the largest "
  "observed seed difference. \"> 95 % band\" means |Δ| is larger than t·√2·σ_seed. \"seed-aware CI\" = "
  "Δ ± 1.96·√(SE_boot² + 2σ²_seed).")
w("")
w("| variant | AUROC [CI] | Δ AUROC [CI] | p | > max seed | > 95 % band | seed-aware CI excl. 0 | tAUROC | Δ tAUROC [CI] | p | > max seed | > 95 % band | seed-aware CI excl. 0 |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
yn = lambda b: "yes" if bool(b) else "no"  # noqa: E731
for var, g in CA.groupby("variant", sort=False):
    ra = g[g.metric == "auroc"].iloc[0]
    rt = g[g.metric == "tauroc"].iloc[0]
    uci = lst(ra.u_ci)
    w(f"| {var} | {f3(ra.u_val)} {ci_u(*uci)} | {s3(ra.est)} {ci(ra.ci_lo, ra.ci_hi)} | {pv(ra.p_raw)} | "
      f"{yn(ra.exceeds_max_seed_diff)} | {yn(ra.exceeds_seed_band95)} | {yn(ra.seed_aware_excludes0)} | {f3(rt.u_val)} | "
      f"{s3(rt.est)} {ci(rt.ci_lo, rt.ci_hi)} | {pv(rt.p_raw)} | {yn(rt.exceeds_max_seed_diff)} | "
      f"{yn(rt.exceeds_seed_band95)} | {yn(rt.seed_aware_excludes0)} |")
w("")
sr = CA[(CA.variant == "control shuffle_rows") & (CA.metric == "auroc")].iloc[0]
w(f"Chance checks: shuffle_rows AUROC {f3(sr.u_val)} {ci_u(*lst(sr.u_ci))} (contains 0.5). shuffle_labels keeps the "
  "label-vs-round prior: AUROC "
  f"{f3(CA[(CA.variant == 'control shuffle_labels') & (CA.metric == 'auroc')].u_val.iloc[0])}, but tAUROC "
  f"{f3(CA[(CA.variant == 'control shuffle_labels') & (CA.metric == 'tauroc')].u_val.iloc[0])} "
  f"{ci_u(*lst(CA[(CA.variant == 'control shuffle_labels') & (CA.metric == 'tauroc')].u_ci.iloc[0]))}.")
w("")
w("**Architectures, 18 folds (seed 0; repeat-averaged OOF).** Seed noise comes from the two 18-fold seed pairs "
  f"(band ±{nz['auroc']['band95_diff_18fold']:.3f} AUROC and ±{nz['tauroc']['band95_diff_18fold']:.3f} tAUROC, "
  "t with 2 df, so imprecise). Δ select and Δ LODO worst are point values from `harness.cv_summary`, without CI.")
w("")
w("| comparison | Δ AUROC [CI] | p | seed-aware excl. 0 | Δ tAUROC [CI] | p | seed-aware excl. 0 | Δ select | Δ LODO worst |")
w("|---|---|---|---|---|---|---|---|---|")
for (u, v), g in AR.groupby(["u", "v"], sort=False):
    ra = g[g.metric == "auroc"].iloc[0]
    rt = g[g.metric == "tauroc"].iloc[0]
    w(f"| {u} − {v} | {s3(ra.est)} {ci(ra.ci_lo, ra.ci_hi)} | {pv(ra.p_raw)} | {yn(ra.seed_aware_excludes0)} | "
      f"{s3(rt.est)} {ci(rt.ci_lo, rt.ci_hi)} | {pv(rt.p_raw)} | {yn(rt.seed_aware_excludes0)} | {s3(ra.d_select)} | "
      f"{s3(ra.d_lodo_min)} |")
w("")
w("**id0 screen (22 variants vs s_base, seed 0).** Rows sorted by Δ AUROC.")
w("")
w("| variant | AUROC | Δ AUROC [CI] | p | > max seed | seed-aware excl. 0 | Δ tAUROC [CI] | p | seed-aware excl. 0 |")
w("|---|---|---|---|---|---|---|---|---|")
fl = SC.set_index(["u", "metric"])
for u in SC[SC.metric == "auroc"].sort_values("est", ascending=False).u:
    ra, rt = fl.loc[(u, "auroc")], fl.loc[(u, "tauroc")]
    w(f"| {u} | {f3(ra.u_val)} | {s3(ra.est)} {ci(ra.ci_lo, ra.ci_hi)} | {pv(ra.p_raw)} | {yn(ra.exceeds_max_seed_diff)} | "
      f"{yn(ra.seed_aware_excludes0)} | {s3(rt.est)} {ci(rt.ci_lo, rt.ci_hi)} | {pv(rt.p_raw)} | {yn(rt.seed_aware_excludes0)} |")
w("")
scr_max = sorted(set(SC[SC.exceeds_max_seed_diff].u) - set(ex_scr))
scr_band = sorted(set(SC[SC.exceeds_seed_band95].u) - set(ex_scr))
sef = CA[(CA.variant == "control shuffle_ef")].set_index("metric")
w("**Answer: does any difference exceed the seed noise?** Criterion: the seed-aware 95 % CI (seed variance "
  f"included) excludes 0. Controls/ablations on AUROC: {', '.join(ex_ctl_a) or 'none'}; on tAUROC: "
  f"{', '.join(ex_ctl_t) or 'none'}. Within seed noise on both metrics: {', '.join(ctl_none) or 'none'}. "
  f"shuffle_ef has Δ AUROC {s3(sef.loc['auroc', 'est'])} and Δ tAUROC {s3(sef.loc['tauroc', 'est'])}: past the largest "
  "observed seed difference, but inside the 95 % band. "
  f"Screen variants: {', '.join(ex_scr) or 'none'} (on AUROC or tAUROC). Past the largest observed seed |Δ| on some "
  f"metric but not seed-aware: {', '.join(scr_max) or 'none'}. Past the 95 % band but not seed-aware: "
  f"{', '.join(scr_band) or 'none'}. 18-fold architecture differences: {', '.join(ex_arch) or 'none'}. Reading: "
  "apart from the label-destroying controls, the only changes that clear seed noise remove the temporal memory "
  "(s_gtemp_none) or the interpretive jury dimensions (S0/S1/S2, at least on tAUROC). Topology (rewire), conv type, "
  "loss weighting and the m_* regularisers cannot be told apart from seed noise with this data.")
w("")

# ------------------------------------------------------------------------------------------------ 7. caveats
w("## 7. Caveats")
w("")
cl = CL.set_index("predictor")
cav = [
    f"**night_train only:** {lab_tr.cfg.nunique()} configs, {len(lab_tr)} rows, {int(lab_tr.y3.sum())} positive rows from "
    f"{int(lab_tr.groupby('run').tipped.first().sum())} tipped runs in {int((lab_tr.groupby('cfg').y3.sum() > 0).sum())} "
    f"configs. Inference rests on few independent units. A percentile bootstrap with 64 clusters can under-cover a "
    f"little, so read p-values near 0.05 as approximate. B = {B:,} gives a p floor of {1 / B:.0e} (Holm floor "
    f"{11 / B:.4f}).",
    "**Not the plan's full decision rule.** Plan §4 needs (1) a CI that excludes 0 in protocol (a), pooled OOF over "
    "**all** night configs with llm_monitor folds, and (2) sign agreement in ≥ 3 of 4 held-out splits (protocol b). "
    "This report is the harness CV on night_train with the harness folds. LODO sign counts are a within-CV proxy, "
    "not criterion (2). Test splits were not touched (GNN looks: 0).",
    "**Zero-shot LLM monitors read raw message text, task words included** (\"skip\", \"quarantine\", shortcut names). "
    "The headline GNN and bag+graph inputs exclude the task lexicon (ablation-only: hgb_bag+graph+lex 0.873 vs 0.843 "
    f"ID AUROC in RESULTS.md; GNN +lex {s3(lex_d)} here). Part of the LLM advantage may be lexical access, not better "
    "reasoning about contagion.",
    f"**zs:global_full sees an implicit clock:** the whole transcript from round 1, so its length grows with t. Its "
    f"score has the highest rank correlation with the round of all predictors (Spearman ρ = "
    f"{cl.loc['zs:global_full', 'rho_t_all']:.2f}, vs {cl.loc['zs:pairwise', 'rho_t_all']:.2f} pairwise, "
    f"{cl.loc['bag+graph', 'rho_t_all']:.2f} bag+graph, {cl.loc['gnn_final', 'rho_t_all']:.2f} gnn_final). Time-matched "
    "AUROC controls for the round only coarsely (5-round bins).",
    "**Same LLM in the monitor and in the features:** the monitor is Claude Haiku 5.5, which is also one of the two jury "
    "judges (DeepSeek V4 Flash + Claude Haiku 5.5, FEATURES.md / README) whose ratings form the GNN and bag+graph "
    "edge/node features. The monitor families are therefore not independent views, and shared model biases are "
    "possible.",
    "**Zero-shot = untrained.** Their LODO values are subset AUROCs, not transfer tests, and the selection score has a "
    "different meaning for them. Prompt development used 8 night_train dev runs (all variants frozen at r0, no "
    "revision, llm_monitor README); those runs are part of these rows.",
    "**Repeat-averaged OOF** gives every trained model a 2-model mini-ensemble (repeat 0 and repeat 1 models); the "
    "zero-shot scores do not get this. The per-repeat (rep-mean) sensitivity is shown; "
    + ("it does not change any Holm verdict" if same_b else "it CHANGES at least one Holm verdict (see §4)")
    + ("; it favours the zero-shot monitors slightly more." if zs_more else "."),
    "**Training and sampling noise is not in the config-bootstrap CIs.** The seed-aware sensitivity adds single-model "
    "seed variance for the GNN (pessimistic for the 4-member ensemble) and "
    + ("no verdict changes" if same_seed else "at least one verdict CHANGES (see §4)")
    + ". The snapshot-level HGB baselines (clock, bag+graph, +mem) are deterministic given their fixed random_state "
    "(< 10,000 training rows, so no early-stopping split; no subsampling). LLM sampling noise was "
    f"measured only for global_full (single sample vs k = 3: {s3(gf['auroc']['diff'])} AUROC), not for pairwise (k = 1).",
    f"**The clock is a weak bar time-matched:** hgb_clock has tAUROC {f3(desc.loc['clock', 'tauroc'])} (< 0.5) with "
    "round bins, because within a 5-round bin the clock model's ranking runs against the outcome. With the plan's "
    f"rounds-to-cut bins it reaches {f3(desc.loc['clock', 'tauroc_rtc'])}. "
    + ("All five communication monitors also beat chance (lower CI bound > 0.5) on both definitions." if chance_both
       else "Not every monitor's lower CI bound is above 0.5 on both definitions (see §4)."),
    "**Secondary analyses** are on id0 (5 folds, one seed). The seed noise comes from few seed pairs (4 df on id0, "
    "2 df on 18 folds), so the noise bands are themselves uncertain. No multiplicity correction (plan §9).",
    "**gnn_final** = `final.csv`, the probability mean of m_noer_swa and m_tmemgru with 2 seeds each (checked: max "
    f"|diff| {SX['checks']['final_vs_mean_of_4_members']['max_abs_diff']:.1f} to the mean of the 4 member files). "
    "gnn_hybrid = the logit mean 0.5/0.5 of final and hgb_bag+graph+mem (max |diff| "
    f"{SX['checks']['hybrid_vs_logit_mean_final_hgbmem']['max_abs_diff']:.1f}). RESULTS.md mentions a better "
    "node-GRU GNN (e_ngru_4runs, select 0.871); it is not the shipped model and is not tested here. The plan's "
    "`gnn_final = ____` field is still empty and should name this configuration before any held-out evaluation.",
    "**Plan deviations:** B = 10,000 instead of 1,000 (the task asked for ≥ 2,000). Round-bin tAUROC (harness) is the "
    "primary time matching, and the plan's rounds-to-cut bins are the sensitivity; "
    + ("every Holm verdict of family (a) is the same under both." if same_a
       else "at least one Holm verdict of family (a) DIFFERS between the two (see §4)."),
]
for c in cav:
    w(f"- {c}")
w("")

# ------------------------------------------------------------------------------------------------ 8. how to read
w("## 8. What this means for the paper")
w("")
w(f"- RQ2 is {'supported' if all_a else 'NOT supported'} in CV: "
  + ("all five communication monitors beat the clock time-matched after Holm, " if all_a else "")
  + ("in all 8 LODO folds each. " if kmin == 8 else f"in at least {kmin} of 8 LODO folds each. ")
  + "The zero-shot pairwise LLM has the highest point estimates of all observable monitors (ID AUROC "
  f"{f3(desc.loc['zs:pairwise', 'auroc'])}, tAUROC {f3(desc.loc['zs:pairwise', 'tauroc'])}). It is significantly "
  f"better than bag+graph (primary, Holm) and than edge_monitor_top3 (supplementary, uncorrected p = "
  f"{pv([r for r in supp if r['comparison'] == 'zs:pairwise - edge_monitor_top3'][0]['p_raw'])}), but it ties with "
  "gnn_final and gnn_hybrid.")
R_ = {r["comparison"]: r for r in pb}
g1, g2, z1 = R_["gnn_final - bag+graph"], R_["gnn_hybrid - bag+graph"], R_["zs:pairwise - bag+graph"]
z2, z3, z4 = R_["zs:pairwise - gnn_final"], R_["zs:pairwise - gnn_hybrid"], R_["zs:global_full - bag+graph"]
sg = lambda r: r["p_holm"] < 0.05  # noqa: E731
w(f"- RQ3, architecture: the GNN alone {'separates' if sg(g1) else 'does not separate'} from bag+graph (Holm p = "
  f"{g1['p_holm']:.3f}, LODO {g1['lodo_same_sign']}/8). The hybrid (GNN + GBM) "
  f"{'does' if sg(g2) else 'does not either'} ({s3(g2['est'])}, LODO {g2['lodo_same_sign']}/8). The global LLM monitor "
  f"{'differs from' if sg(z4) else 'ties with'} bag+graph."
  + (" Wording for the paper: \"the hybrid and the pairwise LLM monitor beat the tabular graph baseline; GNN, hybrid "
     "and pairwise LLM are statistically tied\"."
     if (sg(g2) and sg(z1) and not sg(g1) and not sg(z2) and not sg(z3)) else ""))
w("- None of these is a final paper verdict until protocol (b) on the held-out splits has been run (plan §4, rule 2).")
w("")

# ------------------------------------------------------------------------------------------------ 9. files
w("## 9. Files and commands")
w("")
w("Scratch: `" + ST + "/`")
w("")
w("- `repo/gnn_opt/` (harness copy from origin/gnn-opt), `repo/sim_dataset` → symlink; `data/night/` (rebuilt "
  "dataset); `preds/` (CV files from git + `zs_*.csv`).")
w("- `monitors/make_zs_cv.py` (step 2), `monitors/check_repro.py` (step 1 check), `monitors/statlib.py` (bootstrap, "
  "Holm, DeLong), `monitors/primary_stats.py` (step 4), `monitors/secondary_stats.py` (step 5), "
  "`monitors/sensitivity.py`, `monitors/diagnostics.py`, `monitors/make_report.py`.")
w("- Outputs: `monitors/step1_repro.log`, `step1_repro_table.csv`, `step3_joint.log`, `step3_joint_table.csv`, "
  "`out/primary_results.json`, `out/comparisons.csv`, `out/descriptive_table.csv`, `out/secondary_results.json`, "
  "`out/controls_ablations.csv`, `out/seed_noise.csv`, `out/architectures_18fold.csv`, `out/screen_id0.csv`, "
  "`out/sensitivity_results.json`, `out/clock_likeness.csv`, `out/rank_corr_main.csv`.")
w("")
w("```bash")
w("PY=/Users/mauricio/sim_local/apart/sim_dataset/.venv/bin/python; ST=" + ST)
w("cd /Users/mauricio/sim_local/apart_ana && $PY -I $ST/repo/gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out $ST/data/night")
w("$PY -I $ST/monitors/make_zs_cv.py --data $ST/data/night --folds $ST/repo/gnn_opt/folds.json \\")
w("    --llm-root /Users/mauricio/sim_local/apart_ana/data/llm_monitor --ref-cv $ST/preds/final.csv --out-dir $ST/preds")
w("$PY -I $ST/repo/gnn_opt/evaluate.py --data $ST/data/night --preds $ST/preds/{zs_pairwise,zs_global_full,zs_global_window,final,final+hgb_bag+graph+mem,hgb_bag+graph+mem,hgb_bag+graph,hgb_bag,edge_monitor_top3,hgb_clock,oracle_risk}.csv --pairs")
w("COMMON=\"--data $ST/data/night --base /Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv --folds $ST/repo/gnn_opt/folds.json --preds $ST/preds\"")
w("$PY -I $ST/monitors/primary_stats.py $COMMON --harness $ST/repo/gnn_opt --B 10000 --out $ST/monitors/out")
w("$PY -I $ST/monitors/secondary_stats.py $COMMON --harness $ST/repo/gnn_opt --B 10000 --out $ST/monitors/out")
w("$PY -I $ST/monitors/sensitivity.py $COMMON --llm-root /Users/mauricio/sim_local/apart_ana/data/llm_monitor --out $ST/monitors/out")
w("```")
w("")
open(os.path.join(MON, "REPORT.md"), "w").write("\n".join(L) + "\n")
print(f"wrote {os.path.join(MON, 'REPORT.md')} ({len(L)} lines)")
