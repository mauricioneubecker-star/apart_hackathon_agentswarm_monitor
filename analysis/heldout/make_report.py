"""Compose heldout/REPORT.md from out/results.json, out/diagnostics.json, out/harness_repro_y3.csv and
out/regen_baselines.log. No numbers are typed in by hand except the GNN team's published values (quoted for the
reproduction check, also hard-coded in analysis.py)."""
from __future__ import annotations

import json
import os
import re

import numpy as np
import pandas as pd

HO_DIR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/heldout"
OUT = f"{HO_DIR}/out"
r = json.load(open(f"{OUT}/results.json"))
dg = json.load(open(f"{OUT}/diagnostics.json"))
crg = json.load(open(f"{OUT}/check_regen.json"))
ctb = json.load(open(f"{OUT}/check_table.json"))
regen = open(f"{OUT}/regen_baselines.log").read()
refs = open(f"{HO_DIR}/refs.txt").read().split("\n")
T = r["table"]
SPL = ["test_id", "ood_family", "ood_seed", "branch"]


def f3(x):
    return "n/a" if x is None else f"{x:.3f}"


def s3(x):
    return f"{x:+.3f}"


def ci(c, sign=False):
    fmt = s3 if sign else f3
    return f"[{fmt(c[0])}, {fmt(c[1])}]"


def pfmt(p):
    return "<= 1e-4" if p <= 1.00001e-4 else (f"{p:.4f}" if p < 0.1 else f"{p:.3f}")


def name(a):
    return f"`{a}`"


L = []
w = L.append
meta = r["meta"]
rows = r["rows"]
prim = r["primary"]
n_sig = sum(c["p_holm"] < 0.05 for c in prim)
best = min(prim, key=lambda c: c["p_holm"])
sens = [c["sens_tm_harness"] for c in prim if c["metric"] == "tm_plan"]
mx = r["mixed"]

w("# Held-out comparison on identical rows (primary analysis, ANALYSIS_PLAN.md §4 / §4b)")
w("")
w(f"All monitors scored on the same {meta['n_rows']} held-out harness rows ({meta['n_pos']} positives, "
  f"{meta['n_cfgs']} configs, {meta['n_runs']} runs): night_test_id, night_test_ood_family, night_test_ood_seed and "
  "night_branch, `eval == 1` (y3 defined, branch prefixes counted once). Inference unit = config. Every number below "
  "was produced by the scripts in §9; the GNN team's published values appear only in the reproduction check (§2).")
w("")
w("## Summary")
w("")
rep = r["reproduction"]
w(f"- **Reproduction of the GNN team's test look: exact.** Rows ({meta['n_rows']} / {meta['n_pos']}), pooled and per-split "
  "AUROC of hybrid / gnn5 / tab_mem / edge (0.832 / 0.817 / 0.811 / 0.800), their bootstrap CIs (with their draws), "
  "AUPRC, tAUROC, R@5%FPR, lead time and the pair differences all match at 3 decimals. The harness `evaluate.py`, run "
  f"here on the same files, agrees with my implementation exactly (max |diff| {rep['max_abs_diff_vs_harness_evaluate_py']:g}).")
w(f"- **Primary family (11 tests, Holm): {n_sig} of 11 significant.** The smallest Holm p is {best['p_holm']:.3f} "
  f"({best['a']} - {best['b']}, time-matched, {s3(best['est'])} {ci(best['ci'], True)}, raw p {pfmt(best['p'])}). Under "
  "the plan's rule (§4) every comparison is a **tie (\"gleichauf\")** on the held-out splits. The result does not depend "
  f"on the bootstrap seed: seeds 1-3 give smallest Holm p "
  + ", ".join(f"{min(dg['seed_sensitivity'][s]['holm']):.3f}" for s in ('1', '2', '3')) + ".")
tmc = T["clock"]["tm_plan"]["est"]
fails = [c for c in prim if c["metric"] == "tm_plan" and c["n_agree"] < 3]
_pairs = {b: v["pairs"] for b, v in dg["clock_within_rtc_bins"].items()}
early_share = (_pairs["<=-9"] + _pairs["-8..-5"]) / sum(_pairs.values())
w(f"- **RQ2 (monitors beat the clock, time-matched) is not supported on held-out data under the plan's definition.** "
  f"Within rounds-to-cut bins the clock itself reaches {tmc:.3f} (night_train CV: "
  f"{dg['clock_cv_night_train']['tm_plan']:.3f}). At equal rounds-to-cut, a config with a later deadline is at a later "
  f"absolute round, and in the two earliest bins, which hold {early_share:.0%} of the comparison pairs, positives "
  "occur almost only in the late-deadline configs (cut 23/26). Absolute time therefore still separates the classes "
  "inside the bins. The five "
  "monitor - clock differences are "
  + ", ".join(f"{s3(c['est'])}" for c in prim if c["metric"] == "tm_plan")
  + " (bag+graph, zs:pairwise, zs:global_full, gnn5, hybrid). "
  + " and ".join(c["a"] for c in fails) + f" also fail the sign criterion ("
  + "; ".join(f"{c['a']} {c['n_agree']}/4, below the clock on "
              + " and ".join(k for k, v in c["split_diffs"].items() if np.sign(v) != np.sign(c["est"])) for c in fails)
  + ").")
w(f"- **Sensitivity, harness tAUROC (round bins, where the clock is {T['clock']['tm_harness']['est']:.3f}):** all five "
  f"monitors beat the clock by {min(s['est'] for s in sens):+.3f} to {max(s['est'] for s in sens):+.3f}, every p "
  f"<= {max(s['p'] for s in sens):.4f}, sign in 4/4 splits. The RQ2 verdict therefore hinges on the time-matching "
  "definition; the plan's definition is the pre-registered one.")
MON = ["clock", "bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid", "tab_mem", "edge", "zs:global_window",
       "zs:agent"]
by_auc = sorted(MON, key=lambda k: -T[k]["pooled"]["est"])
by_ap = sorted(MON, key=lambda k: -T[k]["auprc"]["est"])
w(f"- **Point estimates, pooled AUROC (monitors + clock, descending):** "
  + ", ".join(f"{k} {T[k]['pooled']['est']:.3f}" for k in by_auc)
  + f" (oracle reference {T['oracle']['pooled']['est']:.3f}). **AUPRC, descending:** "
  + ", ".join(f"{k} {T[k]['auprc']['est']:.3f}" for k in by_ap[:4]) + f", ... (prevalence {T['clock']['auprc']['prev']:.3f}).")
S = {(c["a"], c["b"], c["metric"], c["label"].split(":")[0]): c for c in r["secondary"]}
ood = [c for c in r["secondary"] if c["label"].startswith("secondary: primary difference on the OOD")]
tid = [c for c in r["secondary"] if c["label"].startswith("secondary: primary difference on test_id")]
g = lambda lst, a, b: next(c for c in lst if c["a"] == a and c["b"] == b)  # noqa: E731
w(f"- **Where the rankings split (secondary, uncorrected):** in test_id the trained GNN models lead (hybrid "
  f"{T['hybrid']['test_id']['auroc']:.3f}, gnn5 {T['gnn5']['test_id']['auroc']:.3f} vs zs:pairwise "
  f"{T['zs:pairwise']['test_id']['auroc']:.3f}; zs:pairwise - hybrid {s3(g(tid, 'zs:pairwise', 'hybrid')['est'])} "
  f"{ci(g(tid, 'zs:pairwise', 'hybrid')['ci'], True)}). On the three OOD splits pooled zs:pairwise leads: vs bag+graph "
  f"{s3(g(ood, 'zs:pairwise', 'bag+graph')['est'])} (p {pfmt(g(ood, 'zs:pairwise', 'bag+graph')['p'])}), vs gnn5 "
  f"{s3(g(ood, 'zs:pairwise', 'gnn5')['est'])} (p {pfmt(g(ood, 'zs:pairwise', 'gnn5')['p'])}), vs hybrid "
  f"{s3(g(ood, 'zs:pairwise', 'hybrid')['est'])} (p {pfmt(g(ood, 'zs:pairwise', 'hybrid')['p'])}). Not corrected, "
  "and the OOD/ID split was not a pre-registered test.")
lead = {k: T[k]["lead"] for k in ["clock", "bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid"]}
w(f"- **Lead time (alarm = score above the training 5 %-FPR threshold):** hybrid alarms "
  f"{lead['hybrid']['n_alarmed_before_tip']}/{lead['hybrid']['tipped_runs']} tipped runs before the tip (median lead "
  f"{lead['hybrid']['median_lead']:g} rounds) with false alarms on {lead['hybrid']['n_untipped_false_alarm']}/"
  f"{lead['hybrid']['untipped_runs']} untipped runs; zs:pairwise {lead['zs:pairwise']['n_alarmed_before_tip']}/"
  f"{lead['zs:pairwise']['tipped_runs']} (median {lead['zs:pairwise']['median_lead']:g}) with "
  f"{lead['zs:pairwise']['n_untipped_false_alarm']}/{lead['zs:pairwise']['untipped_runs']} false-alarm runs. The clock "
  f"alarms {lead['clock']['n_alarmed_before_tip']}/{lead['clock']['tipped_runs']} tipped runs but also "
  f"{lead['clock']['n_untipped_false_alarm']}/{lead['clock']['untipped_runs']} untipped runs.")
cb = g(r["secondary"], "comb:pairwise+hybrid", "hybrid")
w(f"- **Exploratory:** the label-free mean-of-ranks combination zs:pairwise + hybrid reaches "
  f"{T['comb:pairwise+hybrid']['pooled']['est']:.3f} pooled ({s3(cb['est'])} {ci(cb['ci'], True)} over hybrid, "
  f"{s3(g(r['secondary'], 'comb:pairwise+hybrid', 'zs:pairwise')['est'])} over zs:pairwise).")
w("- **Deviation from the task's file list:** the committed `gnn_opt/preds/eval/hgb_bag+graph.csv`, `hgb_clock.csv` "
  "and `oracle_risk+clock.csv` contain night_val only (720 rows, 0 held-out rows). I refit these three harness "
  "baselines on night_train with the harness's own `baselines.py` specs (§1.2). clock and oracle reproduce the "
  f"committed night_val predictions bit for bit; bag+graph does not (val AUROC {crg['bag+graph_refit']['val_auroc']:.4f} vs committed {crg['bag+graph_committed']['val_auroc']:.4f}), so its "
  "held-out values carry a small refit uncertainty.")
w("")

# ------------------------------------------------------------------------------------------------ 1. rows
w("## 1. Rows, predictors, coverage")
w("")
w("### 1.1 Rows")
w("")
w("| split | rows | positives | prevalence | configs | configs with a positive | runs | tipped runs |")
w("|---|---|---|---|---|---|---|---|")
for k in SPL + ["pooled"]:
    v = rows[k]
    w(f"| {k} | {v['rows']} | {v['pos']} | {v['prev']:.3f} | {v['cfgs']} | {v['cfgs_with_pos']} | {v['runs']} | {v['tipped_runs']} |")
w("")
w(f"- Source: harness `snapshots.csv` (scratch `stat/data/night`), rows with `eval == 1` in the four held-out splits. "
  f"{rows['pooled']['excluded_branch_prefix_rows_eval0_labelled']} labelled branch-prefix duplicates (`eval == 0`, "
  "all in night_branch) are excluded, so each prefix counts once.")
w("- Labels, configs, splits, `tipped` and `tip_round` agree with `llm_monitor/_base/snapshots.csv` on all rows. "
  "`rounds_to_cut = t - cut` (cut = 17/20/23/26 per config) comes from `_base`.")
w(f"- **Mixed configs** (held-out runs include tipped and untipped ones): **{mx['n_mixed_cfgs']}** "
  f"({', '.join(f'{k} {v}' for k, v in mx['per_split'].items())}), {mx['n_rows']} rows, {mx['n_pos']} positives. The "
  f"harness schema list (control arms only) has {len(mx['harness_schema_mixed_in_heldout'])} of them; the "
  f"{mx['per_split']['branch']} branch configs (one control run each) are mixed only across arms. The llm_monitor `_base` flag gives the same "
  f"{len(mx['llm_base_mixed_in_heldout'])}.")
w("")
w("### 1.2 Predictors and coverage of the held-out rows")
w("")
w("| predictor | held-out predictions | trained on | missing rows | NaN | distinct values |")
w("|---|---|---|---|---|---|")
desc = {"clock": ("hgb_clock, **refit here** (committed eval file is night_val only)", "night_train"),
        "bag+graph": ("hgb_bag+graph, **refit here** (committed eval file is night_val only)", "night_train"),
        "tab_mem": ("origin/gnn-opt-torch `gnn_opt_torch/preds/eval/hgb_bag+graph+mem__allsplits.csv`", "night_train"),
        "edge": ("origin/gnn-opt-torch `gnn_opt_torch/preds/eval/edge_monitor_top3__allsplits.csv`", "night_train"),
        "gnn5": ("origin/gnn-opt-torch `gnn_opt_torch/preds/eval/cloud_final_gnn.csv`", "night_train"),
        "hybrid": ("origin/gnn-opt-torch `gnn_opt_torch/preds/eval/cloud_final.csv`", "night_train"),
        "zs:pairwise": ("`apart_ana/data/llm_monitor/pairwise/snapshots.csv` zs_tip", "none (zero-shot)"),
        "zs:global_full": ("`.../global_full/snapshots.csv` zs_tip", "none (zero-shot)"),
        "zs:global_window": ("`.../global_window/snapshots.csv` zs_tip", "none (zero-shot)"),
        "zs:agent": ("`.../agent/snapshots.csv` zs_tip", "none (zero-shot)"),
        "oracle": ("oracle_risk+clock, **refit here** (reference only, not a monitor)", "night_train"),
        "tab_mem(refit here)": ("hgb_bag+graph+mem refit here (sensitivity only)", "night_train")}
for k, v in r["coverage"].items():
    w(f"| {name(k)} | {desc[k][0]} | {desc[k][1]} | {v['missing']} | {v['nan']} | {v['distinct_values']} |")
w("| `comb:pairwise+hybrid` | mean of the ranks of zs:pairwise and hybrid over the held-out rows (exploratory) | none | 0 | 0 | - |")
w("")
w(f"Every predictor covers every held-out row; no row was dropped. Git refs: origin/gnn-opt-torch `{refs[0][:10]}`, "
  f"origin/gnn-opt `{refs[1][:10]}`. `zs:*` = zero-shot Claude Haiku 5.5 monitors (no training; prompt frozen on 8 "
  "night_train dev runs), score `zs_tip` in [0, 1], keys `episode_id` = run, `t` = round. gnn5 = node-GRU GNN, 5 "
  "seeds; hybrid = logit blend 0.5 of gnn5 with hgb_bag+graph+mem; both frozen by the GNN team on CV only.")
w("")
w("**Refit of the three baselines** (`scripts/regen_baselines.py`; `baselines.py` specs, train rows = night_train "
  "`eval == 1`, HGB depth 3 / 250 iterations / lr 0.05 / seed 0, single thread). Check against the committed files:")
w("")
w("```")
for line in regen.strip().split("\n"):
    w(re.sub(r"\s+\|", " |", line))
w("```")
w("")
tm_ref = g(r["secondary"], "tab_mem(refit here)", "tab_mem")
w(f"clock, oracle and edge monitor (the same HGB on raw edge features) reproduce bit for bit, so data, splits and "
  f"sklearn behave the same. Models on `table.csv` aggregates do not: bag+graph changes the val AUROC from "
  f"{crg['bag+graph_committed']['val_auroc']:.4f} (committed) to {crg['bag+graph_refit']['val_auroc']:.4f}, and the same refit of tab_mem moves its held-out AUROC by {s3(tm_ref['est'])} "
  f"{ci(tm_ref['ci'], True)} (per split "
  + ", ".join(f"{k} {s3(v)}" for k, v in tm_ref["split_diffs"].items())
  + "). A rebuild of `table.csv` from `graphs.npz` here differs from the stored table only at float32 rounding level "
  f"(max |diff| {ctb['max_abs_diff']:.1e} in {ctb['n_cols_differing']} of {ctb['n_cols']} columns), so the "
  "tabular features sit on HGB bin edges at that precision. The bag+graph numbers below carry refit noise of the "
  "same order as the tab_mem refit difference above.")
w("")
w("### 1.3 5 %-FPR thresholds (training data only; alarm iff score > thr, harness `metrics.thr_at_fpr`)")
w("")
w("| predictor | threshold | from | rows | FPR on that data |")
w("|---|---|---|---|---|")
for k, v in r["thresholds"].items():
    w(f"| {name(k)} | {v['thr']:.4g} | {v['src']} | {v['n_rows']} | {v['train_fpr']:.4f} |")
w("")
w("For gnn5 and hybrid the CV files are the GNN team's proxies (`preds/cv/cloud_final*.csv`, the 4-run node-GRU "
  "ensemble); the 5-seed final model was not cross-validated.")
w("")

# ------------------------------------------------------------------------------------------------ 2. repro
w("## 2. Reproduction of the GNN team's test look (RESULTS.md step 9)")
w("")
w("| model | pooled AUROC mine / published | test_id | ood_family | ood_seed | branch | CI (their draws: seed 0, B = 1000) mine / published | AUPRC, tAUROC, R@5%FPR mine | lead: alarmed, median, false-alarm runs mine / published |")
w("|---|---|---|---|---|---|---|---|---|")
for k in ["hybrid", "gnn5", "tab_mem", "edge"]:
    v = rep[k]
    m, p = v["pooled_and_splits_mine"], v["published"]
    w(f"| {name(k)} | {m[0]:.3f} / {p[0]:.3f} | " + " | ".join(f"{a:.3f} / {b:.3f}" for a, b in zip(m[1:], p[1:]))
      + f" | {ci(v['ci_seed0_B1000'])} / [{v['ci_published'][0]:.3f}, {v['ci_published'][1]:.3f}] | "
      + ", ".join(f"{x:.3f}" for x in v["auprc_tauroc_r5_mine"])
      + f" | {v['lead_mine'][0]:.2f}, {v['lead_mine'][1]:g}, {v['lead_mine'][2]:.2f} / "
      + f"{v['lead_published'][0]:.2f}, {v['lead_published'][1]:g}, {v['lead_published'][2]:.2f} |")
w("")
w("Pair differences with their draws (2.5 / 50 / 97.5 %, share > 0): "
  + "; ".join(f"hybrid - {o} " + " / ".join(f"{x:+.3f}" for x in rep[f'hybrid-{o}']['mine_q'])
              + f", {rep[f'hybrid-{o}']['share_gt0']:.3f} (published " + " / ".join(f"{x:+.3f}" for x in rep[f'hybrid-{o}']['published']) + ")"
              for o in ["gnn5", "tab_mem", "edge"]) + ".")
w("")
w("The harness's own `evaluate.py` (their `test_look.sh` command, run here on the same files, output "
  "`out/harness_repro_y3.txt`) gives the same table, and AUROC, AUPRC, tAUROC and R@5%FPR from my code match it "
  f"exactly (max |diff| {rep['max_abs_diff_vs_harness_evaluate_py']:.1e} over pooled + 4 splits x 4 models).")
w("")

# ------------------------------------------------------------------------------------------------ 3. method
w("## 3. Method")
w("")
w(f"- **Statistics.** (i) pooled AUROC; (ii) **time-matched AUROC, plan definition** (§4): AUROC within rounds-to-cut "
  "bins <= -9, -8..-5, -4..-1, 0..3, > 3, pairs-weighted mean (= `llm_monitor.evaluate.stratified_auroc`; the bins "
  "are `pd.cut(rounds_to_cut, [-99, -9, -5, -1, 3, 99])`); (iii) **harness tAUROC** (sensitivity): AUROC within round "
  "bins 1-5, ..., 26-30, weighted by positives (`metrics.time_matched_auroc`); (iv) **within mixed configs x "
  "rounds-to-cut bin**: pairs-weighted AUROC over strata config x bin, rows of the mixed configs only; (v) AUPRC "
  "(sklearn average precision) next to the prevalence; (vi) AUROC before the first announcement of the shortcut "
  "(`before_announce == 1`, plan §4 main-table column); (vii) recall at the training 5 %-FPR threshold and the "
  "realised held-out FPR; (viii) lead time with the harness definition (`evaluate.lead_time`: first labelled row with "
  "score > thr; lead = tip round - alarm round; share of tipped runs with lead > 0, median lead over them; share of "
  "untipped runs with any alarm).")
w(f"- **Inference unit = config** ({meta['n_cfgs']} held-out configs). **Paired cluster bootstrap**, B = {meta['B']:,}, "
  f"seed {meta['seed']}: configs drawn with replacement, the same draws for every predictor and statistic. Computed "
  "exactly from per-config pair-count matrices: with multiplicities k, AUROC(k) = k'Mk / ((k'n1)(k'n0)), and the "
  "stratified versions sum the per-bin terms. Checked against sklearn / harness / llm_monitor on the full sample and "
  f"on materialised resamples (max |diff| {max(r['engine_checks'].values()):.1e}).")
w("- **Estimate** = full-sample difference; **CI** = 2.5 / 97.5 % percentiles of the bootstrap differences; "
  "**p** = 2 min(P*(d <= 0), P*(d >= 0)), floored at 1/B, capped at 1. **Holm** over the 11 primary tests.")
w("- **Split signs** (plan §4 criterion 2): the same statistic computed on each held-out split alone; a difference "
  "counts as real only if Holm p < 0.05 **and** the sign agrees with the pooled sign in >= 3 of 4 splits, otherwise "
  "\"tie\". Plan criterion 1 is defined on protocol (a), the CV CI, which is not part of this held-out analysis; "
  "here the Holm-corrected held-out bootstrap takes its place.")
w("- **Sensitivities:** split-stratified bootstrap (configs resampled within each split), bootstrap seeds 1-3, harness "
  "tAUROC instead of the plan bins for family (a). **Row-level DeLong** (fast DeLong; for (a) a pairs-weighted "
  "combination of per-bin DeLong estimates, bins with >= 2 positives and negatives) is shown only as an "
  "**anti-conservative contrast**: it treats the rows of one config as independent.")
w("- **Secondary analyses** are uncorrected. OOD-pooled and test_id-only analyses resample only the configs of "
  "those splits (24 and 12). The combination is the mean of the two ranks over the held-out rows (label-free, no "
  "fitting, transductive in the ranks).")
w("")

# ------------------------------------------------------------------------------------------------ 4. table
w("## 4. AUROC table (held-out, identical rows)")
w("")
w(f"Prevalence {T['clock']['auprc']['prev']:.3f} pooled; per split "
  + ", ".join(f"{k} {rows[k]['prev']:.3f}" for k in SPL) + ". 95 % CIs: cluster bootstrap over configs.")
w("")
order = ["clock", "bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid", "tab_mem", "edge", "zs:global_window",
         "zs:agent", "oracle", "comb:pairwise+hybrid"]
role = {"clock": "primary", "bag+graph": "primary", "zs:pairwise": "primary", "zs:global_full": "primary",
        "gnn5": "primary (ext:gnn_final)", "hybrid": "primary (ext:gnn_hybrid)", "tab_mem": "secondary",
        "edge": "secondary", "zs:global_window": "secondary", "zs:agent": "secondary", "oracle": "reference only",
        "comb:pairwise+hybrid": "exploratory"}
w("| predictor | set | AUROC [95% CI] | AUPRC [95% CI] | time-matched, plan bins [95% CI] | harness tAUROC [95% CI] | within mixed cfg x bin [95% CI] | before announcement |")
w("|---|---|---|---|---|---|---|---|")
for k in order:
    v = T[k]
    w(f"| {name(k)} | {role[k]} | {f3(v['pooled']['est'])} {ci(v['pooled']['ci'])} | {f3(v['auprc']['est'])} {ci(v['auprc']['ci'])} | "
      f"{f3(v['tm_plan']['est'])} {ci(v['tm_plan']['ci'])} | {f3(v['tm_harness']['est'])} {ci(v['tm_harness']['ci'])} | "
      f"{f3(v['mixed']['est'])} {ci(v['mixed']['ci'])} | {f3(v['preann']['est'])} |")
w("")
w(f"Within mixed configs: {mx['n_mixed_cfgs']} configs, {mx['n_rows']} rows, {mx['n_pos']} positives. Before "
  f"announcement: {dg['before_announce']['rows']} rows, {dg['before_announce']['pos']} positives.")
w("")
w("| predictor | test_id | ood_family | ood_seed | branch | OOD pooled | time-matched (plan) test_id / ood_family / ood_seed / branch | R@5%FPR (held-out FPR) | R@5%FPR per split | Brier (raw score) |")
w("|---|---|---|---|---|---|---|---|---|---|")
for k in order:
    v = T[k]
    r5 = v.get("r5")
    w(f"| {name(k)} | " + " | ".join(f3(v[s]["auroc"]) for s in SPL) + f" | {f3(v['ood_pooled']['auroc'])} | "
      + " / ".join(f3(v[s]["tm_plan"]) for s in SPL) + " | "
      + (f"{r5['recall']:.3f} ({r5['fpr_heldout']:.3f})" if r5 else "-") + " | "
      + (" / ".join(f"{r5['per_split_recall'][s]:.2f}" for s in SPL) if r5 else "-") + " | "
      + (f"{v['brier_raw']:.3f}" if v["brier_raw"] is not None else "-") + " |")
w("")
w("Brier is on raw scores. The zero-shot scores are not calibrated, so their Brier is not comparable.")
w("")

# ------------------------------------------------------------------------------------------------ 5. primary
w("## 5. Primary family (ANALYSIS_PLAN.md §4b, 11 tests, Holm)")
w("")
w("| # | comparison | statistic | estimate [95% CI] | p raw | p Holm | split differences test_id / ood_family / ood_seed / branch | same sign as pooled | verdict | split-stratified bootstrap p | row-level DeLong p (anti-conservative) |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
ids = []
for c in prim:
    fam = "a" if c["metric"] == "tm_plan" else "b"
    ids.append(f"{fam}{sum(x.startswith(fam) for x in ids) + 1}")
for i, c in zip(ids, prim):
    st = "time-matched (plan)" if c["metric"] == "tm_plan" else "pooled AUROC"
    w(f"| {i} | {c['a']} - {c['b']} | {st} | {s3(c['est'])} {ci(c['ci'], True)} | "
      f"{pfmt(c['p'])} | {c['p_holm']:.3f} | " + " / ".join(s3(c["split_diffs"][s]) for s in SPL)
      + f" | {c['n_agree']}/4 | {c['verdict']} | {pfmt(c['p_split_stratified'])} | {c['delong_p']:.2g} |")
w("")
strat_holm = np.array([c["p_split_stratified"] for c in prim])


def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for rr, i in enumerate(o):
        run = max(run, min(1.0, (m - rr) * ps[i])); adj[i] = run
    return adj


sh = holm(strat_holm)
w(f"- Holm on the split-stratified p-values: smallest {sh.min():.3f}; no test significant either.")
bg = prim[0]["split_diffs"]["branch"]
w(f"- a1 (bag+graph - clock) reaches {prim[0]['n_agree']}/4 only through branch {bg:+.4f}, i.e. a zero difference there.")
w("- Seed sensitivity (B = 10,000 each), raw p per test in the order above:")
for sd, v in dg["seed_sensitivity"].items():
    w(f"  - seed {sd}: " + ", ".join(f"{p:.4f}" for p in v["p"]) + f"; smallest Holm {min(v['holm']):.3f}")
w("- Cluster bootstrap SE / row-level DeLong SE for the pooled differences: "
  + ", ".join(f"{k} {v['ratio']:.2f}" for k, v in r["se_ratio"].items())
  + f". Treating rows as independent understates the uncertainty (SE ratio {min(v['ratio'] for v in r['se_ratio'].values()):.1f}"
  f"-{max(v['ratio'] for v in r['se_ratio'].values()):.1f}); row-level DeLong p < 0.05 for "
  f"{sum(c['delong_p'] < 0.05 for c in prim)} of the 11 primary tests, all of which are ties here.")
w("")
w("**Sensitivity for family (a): harness tAUROC (round bins, positive-weighted) instead of the plan bins** (not part of the family):")
w("")
w("| comparison | estimate [95% CI] | p raw | split differences test_id / ood_family / ood_seed / branch | same sign |")
w("|---|---|---|---|---|")
for c in prim:
    if c["metric"] != "tm_plan":
        continue
    s = c["sens_tm_harness"]
    w(f"| {c['a']} - {c['b']} | {s3(s['est'])} {ci(s['ci'], True)} | {pfmt(s['p'])} | "
      + " / ".join(s3(s["split_diffs"][k]) for k in SPL) + f" | {s['n_agree']}/4 |")
w("")
w("**Why the two time-matchings disagree** (`scripts/diagnostics.py`): clock AUROC inside each rounds-to-cut bin, and "
  "the positive rate by deadline (cut) in that bin:")
w("")
w("| rounds-to-cut bin | rows | positives | clock AUROC in bin | positive rate for cut 17 / 20 / 23 / 26 |")
w("|---|---|---|---|---|")
for b in ["<=-9", "-8..-5", "-4..-1", "0..3", ">3"]:
    v = dg["clock_within_rtc_bins"][b]
    pr = v["pos_rate_by_cut"]
    w(f"| {b} | {dg['rtc_bins'][b]['rows']} | {dg['rtc_bins'][b]['pos']} | {f3(v['clock_auroc'])} | "
      + " / ".join(f"{pr.get(str(c), pr.get(c, float('nan'))):.3f}" for c in (17, 20, 23, 26)) + " |")
w("")
w(f"Inside the round bins the clock is near chance ("
  + ", ".join(f"rounds {1 + 5 * int(k)}-{5 + 5 * int(k)}: {f3(v['clock_auroc'])}" for k, v in dg["clock_within_round_bins"].items()
              if v["clock_auroc"] is not None)
  + f"; the last bin holds only {dg['clock_within_round_bins']['5']['pos']} positives). With rounds-to-cut bins, "
  "absolute time is still informative, and the plan's (a) test becomes a test against a clock of about "
  f"{T['clock']['tm_plan']['est']:.2f} rather than 0.5. On night_train CV the clock's plan-binned AUROC is "
  f"{dg['clock_cv_night_train']['tm_plan']:.3f} (harness {dg['clock_cv_night_train']['tm_harness']:.3f}), and the "
  "monitors' CV values are " + ", ".join(f"{k} {v['tm_plan']:.3f}" for k, v in dg["cv_tm_plan_context"].items())
  + " (computed here from the CV / zero-shot files). The margin shrinks on held-out data from both sides: the clock "
  f"rises ({dg['clock_cv_night_train']['tm_plan']:.3f} -> {T['clock']['tm_plan']['est']:.3f}) and every monitor falls ("
  + ", ".join(f"{k} {T[k]['tm_plan']['est'] - v['tm_plan']:+.3f}" for k, v in dg["cv_tm_plan_context"].items())
  + "), the zero-shot ones included.")
w("")

# ------------------------------------------------------------------------------------------------ 6. secondary
w("## 6. Secondary analyses (uncorrected; raw p)")
w("")
w("| label | comparison | statistic | estimate [95% CI] | p raw | split differences test_id / ood_family / ood_seed / branch | same sign |")
w("|---|---|---|---|---|---|---|")
for c in r["secondary"]:
    st = {"tm_plan": "time-matched (plan)", "pooled": "pooled AUROC"}[c["metric"]]
    sd = (" / ".join(s3(c["split_diffs"][s]) for s in SPL) + f" | {c['n_agree']}/4") if "split_diffs" in c else "- | -"
    w(f"| {c['label']} | {c['a']} - {c['b']} | {st} | {s3(c['est'])} {ci(c['ci'], True)} | {pfmt(c['p'])} | {sd} |")
w("")
w("AUPRC differences for the (b) pairs (descriptive, same draws): "
  + "; ".join(f"{k} {s3(v['est'])} {ci(v['ci'], True)}" for k, v in r["auprc_diffs"].items()) + ".")
w("")

# ------------------------------------------------------------------------------------------------ 7. lead time
w("## 7. Lead time and false alarms (held-out runs; thresholds from training data only)")
w("")
w("| predictor | tipped runs alarmed before the tip | median lead [IQR] (rounds) | untipped runs with a false alarm | R@5%FPR (rows) | held-out row FPR |")
w("|---|---|---|---|---|---|")
for k in ["clock", "bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid", "tab_mem", "edge", "zs:global_window",
          "zs:agent", "oracle"]:
    v = T[k]["lead"]
    iq = v["lead_iqr"]
    w(f"| {name(k)} | {v['n_alarmed_before_tip']}/{v['tipped_runs']} ({v['alarmed_before_tip']:.2f}) | {v['median_lead']:g} "
      f"[{iq[0]:g}, {iq[1]:g}] | {v['n_untipped_false_alarm']}/{v['untipped_runs']} ({v['false_alarm_runs']:.2f}) | "
      f"{T[k]['r5']['recall']:.3f} | {T[k]['r5']['fpr_heldout']:.3f} |")
w("")
w("The first six rows are the primary predictors. A run-level false alarm is any alarm on a labelled row of an "
  "untipped run, so even a ~5 % row FPR alarms a large share of 30-round runs; the clock alarms every untipped run.")
w("")

# ------------------------------------------------------------------------------------------------ 8. caveats
ic = dg["implicit_clock"]
w("## 8. Caveats")
w("")
w("- **One GNN test look was already used.** The GNN team looked once at these held-out splits with these exact "
  "prediction files (LOOKS.md: test 1 of 2) and published the AUROCs. This analysis makes no new model choice, and the "
  "frozen predictions are only re-scored, but the GNN's held-out performance was known before it ran. Plan §0 also "
  "records that protocol (b) of the LLM monitors on the held-out splits was evaluated and committed earlier "
  "(68744e2).")
w("- **The LLM monitors read raw message text, including task words.** The headline GNN / tabular models exclude the "
  "task lexicon (`mech_ref`, `pressure_lex`, ...) by rule (ablation only), so the information sets differ.")
w(f"- **zs:global_full sees an implicit clock** (the whole transcript up to t). Its score has the highest rank "
  f"correlation with the round of all predictors (Spearman {ic['zs:global_full']['spearman_round_all']:.2f} on held-out "
  f"rows, vs clock {ic['clock']['spearman_round_all']:.2f}, zs:pairwise {ic['zs:pairwise']['spearman_round_all']:.2f}, "
  f"hybrid {ic['hybrid']['spearman_round_all']:.2f}). Its pooled AUROC partly reflects time; the time-matched values "
  "are the fairer comparison.")
w("- **Haiku is also one of the two jury judges** (DeepSeek + Haiku) whose edge / node scores are the GNN and tabular "
  "features. Its errors can reach both sides, so the GNN-vs-LLM comparison is not between independent information "
  "sources (the GNN team's judge-swap table in RESULTS.md step 9 shows the trained models depend on which judge "
  "produced the features).")
w(f"- **ood_seed: the trigger is not in the communication** (injection via tool output), so a communication "
  "monitor sees only its consequences. Within round bins the trained monitors are near chance there (harness tAUROC "
  "on ood_seed: " + ", ".join(f"{k} {T[k]['ood_seed']['tm_harness']:.3f}" for k in ["bag+graph", "tab_mem", "edge", "gnn5", "hybrid"])
  + "); the zero-shot monitors are higher (" + ", ".join(f"{k} {T[k]['ood_seed']['tm_harness']:.3f}"
                                                         for k in ["zs:pairwise", "zs:global_full", "zs:global_window", "zs:agent"]) + ").")
w(f"- **Few configs per split** (12 / 8 / 8 / 8; positives in only {rows['test_id']['cfgs_with_pos']} / "
  f"{rows['ood_family']['cfgs_with_pos']} / {rows['ood_seed']['cfgs_with_pos']} / {rows['branch']['cfgs_with_pos']} "
  "of them). Per-split signs, and so the >= 3/4 rule, rest on a few configs each. The within-mixed statistic rests on "
  f"{mx['n_mixed_cfgs']} configs and {mx['n_pos']} positives (CI widths "
  f"{min(T[k]['mixed']['ci'][1] - T[k]['mixed']['ci'][0] for k in MON):.2f}-"
  f"{max(T[k]['mixed']['ci'][1] - T[k]['mixed']['ci'][0] for k in MON):.2f}). A percentile cluster bootstrap "
  f"with {meta['n_cfgs']} clusters tends to give intervals that are somewhat too narrow, i.e. p-values that are too "
  "small; since no primary test is significant, this cannot overturn a verdict, but it argues against reading the "
  "uncorrected secondary p-values strictly.")
w("- **bag+graph, clock and oracle were refit here** (§1.2): clock and oracle are bit-identical to the committed "
  f"night_val predictions; bag+graph is not, and carries refit noise of the order of the tab_mem refit check "
  f"({s3(tm_ref['est'])} {ci(tm_ref['ci'], True)} pooled).")
w("- **Thresholds come from different pools by design:** trained models from night_train ID-OOF CV predictions (for "
  "gnn5 / hybrid the GNN team's 4-run CV proxy, not the 5-seed final model), zero-shot monitors from night_train + "
  "night_val raw scores. Realised held-out row FPRs range "
  f"{min(T[k]['r5']['fpr_heldout'] for k in order if 'r5' in T[k]):.3f}-"
  f"{max(T[k]['r5']['fpr_heldout'] for k in order if 'r5' in T[k]):.3f}, so the recalls are not at an identical FPR.")
w("- **Zero-shot prompt.** It was frozen on 8 night_train dev runs: untrained, but not developed blind to the training "
  "split. Nothing was tuned on held-out data.")
w("- **Deviations from plan §5** (by instruction): rows are the GNN harness rows (branch prefixes once) rather than "
  "`llm_monitor.evaluate` (prefixes three times). The GNN models are the GNN team's frozen night_train-only models, "
  "not a train + val refit.")
w("- **Time-matching definition matters** (§5): the pre-registered rounds-to-cut bins leave absolute time "
  f"informative (clock {T['clock']['tm_plan']['est']:.3f}). The harness round bins neutralise it "
  f"({T['clock']['tm_harness']['est']:.3f}), and the RQ2 verdict flips between the two.")
w("- **Exploratory combination:** ranks are taken over the held-out rows. That is label-free, but it uses the test "
  "score distribution. It was defined after the primary results were known to the requester.")
w("")

# ------------------------------------------------------------------------------------------------ 9. files
w("## 9. Files and commands")
w("")
w("Python: `/Users/mauricio/sim_local/apart/sim_dataset/.venv/bin/python -I -B` (numpy, pandas, scipy, scikit-learn).")
w("")
w("1. `git show <ref>:<path> > heldout/preds/{eval,cv}/<name>.csv`: prediction files (refs above).")
w("2. `scripts/regen_baselines.py`: refits hgb_clock, hgb_bag+graph, oracle_risk+clock (+ checks) into `preds/regen/` "
  "(log `out/regen_baselines.log`); `scripts/check_table.py`: table rebuild check (`out/check_table.log`).")
w("3. `stat/repo/gnn_opt/evaluate.py` with the GNN team's `test_look.sh` arguments: `out/harness_repro_y3.{txt,csv}`.")
w("4. `scripts/analysis.py` (+ `scripts/hlib.py`): `out/results.json`, `out/analysis.log`, `out/table_predictors.csv`, "
  "`out/table_primary.csv`, `out/table_secondary.csv`.")
w("5. `scripts/diagnostics.py`: `out/diagnostics.{json,log}`.")
w("6. `scripts/make_report.py`: this file.")
w("")
open(f"{HO_DIR}/REPORT.md", "w").write("\n".join(L) + "\n")
print(f"wrote {HO_DIR}/REPORT.md ({len(L)} lines)")
