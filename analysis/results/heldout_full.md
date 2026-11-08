# Held-out comparison on identical rows (primary analysis, ANALYSIS_PLAN.md §4 / §4b)

All monitors scored on the same 2338 held-out harness rows (156 positives, 36 configs, 100 runs): night_test_id, night_test_ood_family, night_test_ood_seed and night_branch, `eval == 1` (y3 defined, branch prefixes counted once). Inference unit = config. Every number below was produced by the scripts in §9; the GNN team's published values appear only in the reproduction check (§2).

## Summary

- **Reproduction of the GNN team's test look: exact.** Rows (2338 / 156), pooled and per-split AUROC of hybrid / gnn5 / tab_mem / edge (0.832 / 0.817 / 0.811 / 0.800), their bootstrap CIs (with their draws), AUPRC, tAUROC, R@5%FPR, lead time and the pair differences all match at 3 decimals. The harness `evaluate.py`, run here on the same files, agrees with my implementation exactly (max |diff| 0).
- **Primary family (11 tests, Holm): 0 of 11 significant.** The smallest Holm p is 0.090 (zs:pairwise - clock, time-matched, +0.121 [+0.032, +0.213], raw p 0.0082). Under the plan's rule (§4) every comparison is a **tie ("gleichauf")** on the held-out splits. The result does not depend on the bootstrap seed: seeds 1-3 give smallest Holm p 0.092, 0.081, 0.092.
- **RQ2 (monitors beat the clock, time-matched) is not supported on held-out data under the plan's definition.** Within rounds-to-cut bins the clock itself reaches 0.716 (night_train CV: 0.635). At equal rounds-to-cut, a config with a later deadline is at a later absolute round, and in the two earliest bins, which hold 66% of the comparison pairs, positives occur almost only in the late-deadline configs (cut 23/26). Absolute time therefore still separates the classes inside the bins. The five monitor - clock differences are +0.080, +0.121, +0.103, +0.053, +0.101 (bag+graph, zs:pairwise, zs:global_full, gnn5, hybrid). gnn5 and hybrid also fail the sign criterion (gnn5 2/4, below the clock on ood_seed and branch; hybrid 2/4, below the clock on ood_seed and branch).
- **Sensitivity, harness tAUROC (round bins, where the clock is 0.530):** all five monitors beat the clock by +0.191 to +0.257, every p <= 0.0002, sign in 4/4 splits. The RQ2 verdict therefore hinges on the time-matching definition; the plan's definition is the pre-registered one.
- **Point estimates, pooled AUROC (monitors + clock, descending):** zs:pairwise 0.855, zs:agent 0.849, hybrid 0.832, zs:global_window 0.829, gnn5 0.817, zs:global_full 0.816, bag+graph 0.812, tab_mem 0.811, edge 0.800, clock 0.781 (oracle reference 0.908). **AUPRC, descending:** gnn5 0.309, hybrid 0.301, zs:pairwise 0.273, zs:global_window 0.261, ... (prevalence 0.067).
- **Where the rankings split (secondary, uncorrected):** in test_id the trained GNN models lead (hybrid 0.922, gnn5 0.921 vs zs:pairwise 0.872; zs:pairwise - hybrid -0.050 [-0.115, +0.004]). On the three OOD splits pooled zs:pairwise leads: vs bag+graph +0.088 (p 0.0026), vs gnn5 +0.097 (p 0.0198), vs hybrid +0.073 (p 0.0292). Not corrected, and the OOD/ID split was not a pre-registered test.
- **Lead time (alarm = score above the training 5 %-FPR threshold):** hybrid alarms 28/52 tipped runs before the tip (median lead 5.5 rounds) with false alarms on 15/48 untipped runs; zs:pairwise 25/52 (median 2) with 10/48 false-alarm runs. The clock alarms 36/52 tipped runs but also 48/48 untipped runs.
- **Exploratory:** the label-free mean-of-ranks combination zs:pairwise + hybrid reaches 0.861 pooled (+0.029 [+0.004, +0.056] over hybrid, +0.006 over zs:pairwise).
- **Deviation from the task's file list:** the committed `gnn_opt/preds/eval/hgb_bag+graph.csv`, `hgb_clock.csv` and `oracle_risk+clock.csv` contain night_val only (720 rows, 0 held-out rows). I refit these three harness baselines on night_train with the harness's own `baselines.py` specs (§1.2). clock and oracle reproduce the committed night_val predictions bit for bit; bag+graph does not (val AUROC 0.9009 vs committed 0.9022), so its held-out values carry a small refit uncertainty.

## 1. Rows, predictors, coverage

### 1.1 Rows

| split | rows | positives | prevalence | configs | configs with a positive | runs | tipped runs |
|---|---|---|---|---|---|---|---|
| test_id | 896 | 54 | 0.060 | 12 | 7 | 36 | 18 |
| ood_family | 569 | 33 | 0.058 | 8 | 4 | 24 | 11 |
| ood_seed | 349 | 36 | 0.103 | 8 | 7 | 16 | 12 |
| branch | 524 | 33 | 0.063 | 8 | 5 | 24 | 11 |
| pooled | 2338 | 156 | 0.067 | 36 | 23 | 100 | 52 |

- Source: harness `snapshots.csv` (scratch `stat/data/night`), rows with `eval == 1` in the four held-out splits. 80 labelled branch-prefix duplicates (`eval == 0`, all in night_branch) are excluded, so each prefix counts once.
- Labels, configs, splits, `tipped` and `tip_round` agree with `llm_monitor/_base/snapshots.csv` on all rows. `rounds_to_cut = t - cut` (cut = 17/20/23/26 per config) comes from `_base`.
- **Mixed configs** (held-out runs include tipped and untipped ones): **9** (test_id 3, ood_family 1, ood_seed 2, branch 3), 591 rows, 45 positives. The harness schema list (control arms only) has 6 of them; the 3 branch configs (one control run each) are mixed only across arms. The llm_monitor `_base` flag gives the same 9.

### 1.2 Predictors and coverage of the held-out rows

| predictor | held-out predictions | trained on | missing rows | NaN | distinct values |
|---|---|---|---|---|---|
| `clock` | hgb_clock, **refit here** (committed eval file is night_val only) | night_train | 0 | 0 | 20 |
| `bag+graph` | hgb_bag+graph, **refit here** (committed eval file is night_val only) | night_train | 0 | 0 | 2036 |
| `tab_mem` | origin/gnn-opt-torch `gnn_opt_torch/preds/eval/hgb_bag+graph+mem__allsplits.csv` | night_train | 0 | 0 | 2051 |
| `edge` | origin/gnn-opt-torch `gnn_opt_torch/preds/eval/edge_monitor_top3__allsplits.csv` | night_train | 0 | 0 | 1619 |
| `gnn5` | origin/gnn-opt-torch `gnn_opt_torch/preds/eval/cloud_final_gnn.csv` | night_train | 0 | 0 | 2149 |
| `hybrid` | origin/gnn-opt-torch `gnn_opt_torch/preds/eval/cloud_final.csv` | night_train | 0 | 0 | 2149 |
| `zs:pairwise` | `apart_ana/data/llm_monitor/pairwise/snapshots.csv` zs_tip | none (zero-shot) | 0 | 0 | 32 |
| `zs:global_full` | `.../global_full/snapshots.csv` zs_tip | none (zero-shot) | 0 | 0 | 150 |
| `zs:global_window` | `.../global_window/snapshots.csv` zs_tip | none (zero-shot) | 0 | 0 | 27 |
| `zs:agent` | `.../agent/snapshots.csv` zs_tip | none (zero-shot) | 0 | 0 | 39 |
| `oracle` | oracle_risk+clock, **refit here** (reference only, not a monitor) | night_train | 0 | 0 | 157 |
| `tab_mem(refit here)` | hgb_bag+graph+mem refit here (sensitivity only) | night_train | 0 | 0 | 2041 |
| `comb:pairwise+hybrid` | mean of the ranks of zs:pairwise and hybrid over the held-out rows (exploratory) | none | 0 | 0 | - |

Every predictor covers every held-out row; no row was dropped. Git refs: origin/gnn-opt-torch `aebf0e1f7e`, origin/gnn-opt `38d1f5274e`. `zs:*` = zero-shot Claude Haiku 5.5 monitors (no training; prompt frozen on 8 night_train dev runs), score `zs_tip` in [0, 1], keys `episode_id` = run, `t` = round. gnn5 = node-GRU GNN, 5 seeds; hybrid = logit blend 0.5 of gnn5 with hgb_bag+graph+mem; both frozen by the GNN team on CV only.

**Refit of the three baselines** (`scripts/regen_baselines.py`; `baselines.py` specs, train rows = night_train `eval == 1`, HGB depth 3 / 250 iterations / lr 0.05 / seed 0, single thread). Check against the committed files:

```
train rows 3370 positives 135 | predicting 3720 snapshots
hgb_bag+graph          ref=hgb_bag+graph.csv ref rows 720 matched 720 | max|diff| 0.104  max rel 0.986  exact-equal share 0.0014
hgb_clock              ref=hgb_clock.csv ref rows 720 matched 720 | max|diff| 0  max rel 0  exact-equal share 1.0000
oracle_risk+clock      ref=oracle_risk+clock.csv ref rows 720 matched 720 | max|diff| 0  max rel 0  exact-equal share 1.0000
hgb_bag+graph+mem      ref=hgb_bag+graph+mem__allsplits.csv ref rows 3720 matched 3720 | max|diff| 0.236  max rel 1.44  exact-equal share 0.0000
edge_monitor_top3      ref=edge_monitor_top3__allsplits.csv ref rows 3720 matched 3720 | max|diff| 0  max rel 0  exact-equal share 1.0000
```

clock, oracle and edge monitor (the same HGB on raw edge features) reproduce bit for bit, so data, splits and sklearn behave the same. Models on `table.csv` aggregates do not: bag+graph changes the val AUROC from 0.9022 (committed) to 0.9009, and the same refit of tab_mem moves its held-out AUROC by +0.002 [-0.003, +0.007] (per split test_id +0.001, ood_family -0.006, ood_seed +0.008, branch +0.005). A rebuild of `table.csv` from `graphs.npz` here differs from the stored table only at float32 rounding level (max |diff| 2.0e-05 in 47 of 227 columns), so the tabular features sit on HGB bin edges at that precision. The bag+graph numbers below carry refit noise of the same order as the tab_mem refit difference above.

### 1.3 5 %-FPR thresholds (training data only; alarm iff score > thr, harness `metrics.thr_at_fpr`)

| predictor | threshold | from | rows | FPR on that data |
|---|---|---|---|---|
| `clock` | 0.1207 | night_train ID-OOF (hgb_clock.csv, repeat mean) | 3370 | 0.0488 |
| `bag+graph` | 0.1363 | night_train ID-OOF (hgb_bag+graph.csv, repeat mean) | 3370 | 0.0498 |
| `tab_mem` | 0.1363 | night_train ID-OOF (hgb_bag+graph+mem.csv, repeat mean) | 3370 | 0.0498 |
| `edge` | 0.3263 | night_train ID-OOF (edge_monitor_top3.csv, repeat mean) | 3370 | 0.0498 |
| `gnn5` | 0.314 | night_train ID-OOF (cloud_final_gnn.csv, repeat mean) | 3370 | 0.0498 |
| `hybrid` | 0.1431 | night_train ID-OOF (cloud_final.csv, repeat mean) | 3370 | 0.0498 |
| `zs:pairwise` | 0.88 | night_train + night_val eval rows (raw zero-shot score) | 4050 | 0.0469 |
| `zs:global_full` | 0.65 | night_train + night_val eval rows (raw zero-shot score) | 4050 | 0.0474 |
| `zs:global_window` | 0.55 | night_train + night_val eval rows (raw zero-shot score) | 4050 | 0.0471 |
| `zs:agent` | 0.92 | night_train + night_val eval rows (raw zero-shot score) | 4050 | 0.0395 |
| `oracle` | 0.1162 | night_train ID-OOF (oracle_risk+clock.csv, repeat mean) | 3370 | 0.0498 |
| `tab_mem(refit here)` | 0.1363 | night_train ID-OOF (hgb_bag+graph+mem.csv, repeat mean) | 3370 | 0.0498 |

For gnn5 and hybrid the CV files are the GNN team's proxies (`preds/cv/cloud_final*.csv`, the 4-run node-GRU ensemble); the 5-seed final model was not cross-validated.

## 2. Reproduction of the GNN team's test look (RESULTS.md step 9)

| model | pooled AUROC mine / published | test_id | ood_family | ood_seed | branch | CI (their draws: seed 0, B = 1000) mine / published | AUPRC, tAUROC, R@5%FPR mine | lead: alarmed, median, false-alarm runs mine / published |
|---|---|---|---|---|---|---|---|---|
| `hybrid` | 0.832 / 0.832 | 0.922 / 0.922 | 0.823 / 0.823 | 0.785 / 0.785 | 0.728 / 0.728 | [0.782, 0.885] / [0.782, 0.885] | 0.301, 0.752, 0.372 | 0.54, 5.5, 0.31 / 0.54, 5.5, 0.31 |
| `gnn5` | 0.817 / 0.817 | 0.921 / 0.921 | 0.794 / 0.794 | 0.744 / 0.744 | 0.731 / 0.731 | [0.756, 0.877] / [0.756, 0.877] | 0.309, 0.739, 0.417 | 0.54, 5, 0.29 / 0.54, 5, 0.29 |
| `tab_mem` | 0.811 / 0.811 | 0.895 / 0.895 | 0.807 / 0.807 | 0.780 / 0.780 | 0.699 / 0.699 | [0.760, 0.861] / [0.760, 0.861] | 0.252, 0.718, 0.250 | 0.52, 5, 0.29 / 0.52, 5, 0.29 |
| `edge` | 0.800 / 0.800 | 0.837 / 0.837 | 0.812 / 0.812 | 0.780 / 0.780 | 0.728 / 0.728 | [0.757, 0.847] / [0.757, 0.847] | 0.211, 0.682, 0.288 | 0.56, 4, 0.29 / 0.56, 4, 0.29 |

Pair differences with their draws (2.5 / 50 / 97.5 %, share > 0): hybrid - gnn5 -0.007 / +0.016 / +0.041, 0.905 (published -0.007 / +0.016 / +0.041); hybrid - tab_mem -0.006 / +0.021 / +0.051, 0.932 (published -0.006 / +0.021 / +0.051); hybrid - edge -0.011 / +0.032 / +0.078, 0.934 (published -0.011 / +0.032 / +0.078).

The harness's own `evaluate.py` (their `test_look.sh` command, run here on the same files, output `out/harness_repro_y3.txt`) gives the same table, and AUROC, AUPRC, tAUROC and R@5%FPR from my code match it exactly (max |diff| 0.0e+00 over pooled + 4 splits x 4 models).

## 3. Method

- **Statistics.** (i) pooled AUROC; (ii) **time-matched AUROC, plan definition** (§4): AUROC within rounds-to-cut bins <= -9, -8..-5, -4..-1, 0..3, > 3, pairs-weighted mean (= `llm_monitor.evaluate.stratified_auroc`; the bins are `pd.cut(rounds_to_cut, [-99, -9, -5, -1, 3, 99])`); (iii) **harness tAUROC** (sensitivity): AUROC within round bins 1-5, ..., 26-30, weighted by positives (`metrics.time_matched_auroc`); (iv) **within mixed configs x rounds-to-cut bin**: pairs-weighted AUROC over strata config x bin, rows of the mixed configs only; (v) AUPRC (sklearn average precision) next to the prevalence; (vi) AUROC before the first announcement of the shortcut (`before_announce == 1`, plan §4 main-table column); (vii) recall at the training 5 %-FPR threshold and the realised held-out FPR; (viii) lead time with the harness definition (`evaluate.lead_time`: first labelled row with score > thr; lead = tip round - alarm round; share of tipped runs with lead > 0, median lead over them; share of untipped runs with any alarm).
- **Inference unit = config** (36 held-out configs). **Paired cluster bootstrap**, B = 10,000, seed 20261108: configs drawn with replacement, the same draws for every predictor and statistic. Computed exactly from per-config pair-count matrices: with multiplicities k, AUROC(k) = k'Mk / ((k'n1)(k'n0)), and the stratified versions sum the per-bin terms. Checked against sklearn / harness / llm_monitor on the full sample and on materialised resamples (max |diff| 1.1e-16).
- **Estimate** = full-sample difference; **CI** = 2.5 / 97.5 % percentiles of the bootstrap differences; **p** = 2 min(P*(d <= 0), P*(d >= 0)), floored at 1/B, capped at 1. **Holm** over the 11 primary tests.
- **Split signs** (plan §4 criterion 2): the same statistic computed on each held-out split alone; a difference counts as real only if Holm p < 0.05 **and** the sign agrees with the pooled sign in >= 3 of 4 splits, otherwise "tie". Plan criterion 1 is defined on protocol (a), the CV CI, which is not part of this held-out analysis; here the Holm-corrected held-out bootstrap takes its place.
- **Sensitivities:** split-stratified bootstrap (configs resampled within each split), bootstrap seeds 1-3, harness tAUROC instead of the plan bins for family (a). **Row-level DeLong** (fast DeLong; for (a) a pairs-weighted combination of per-bin DeLong estimates, bins with >= 2 positives and negatives) is shown only as an **anti-conservative contrast**: it treats the rows of one config as independent.
- **Secondary analyses** are uncorrected. OOD-pooled and test_id-only analyses resample only the configs of those splits (24 and 12). The combination is the mean of the two ranks over the held-out rows (label-free, no fitting, transductive in the ranks).

## 4. AUROC table (held-out, identical rows)

Prevalence 0.067 pooled; per split test_id 0.060, ood_family 0.058, ood_seed 0.103, branch 0.063. 95 % CIs: cluster bootstrap over configs.

| predictor | set | AUROC [95% CI] | AUPRC [95% CI] | time-matched, plan bins [95% CI] | harness tAUROC [95% CI] | within mixed cfg x bin [95% CI] | before announcement |
|---|---|---|---|---|---|---|---|
| `clock` | primary | 0.781 [0.714, 0.841] | 0.176 [0.106, 0.272] | 0.716 [0.632, 0.789] | 0.530 [0.481, 0.578] | 0.682 [0.484, 0.891] | 0.725 |
| `bag+graph` | primary | 0.812 [0.759, 0.861] | 0.260 [0.154, 0.392] | 0.797 [0.723, 0.854] | 0.721 [0.646, 0.790] | 0.647 [0.442, 0.789] | 0.775 |
| `zs:pairwise` | primary | 0.855 [0.808, 0.899] | 0.273 [0.181, 0.394] | 0.838 [0.755, 0.900] | 0.787 [0.722, 0.849] | 0.820 [0.660, 0.900] | 0.766 |
| `zs:global_full` | primary | 0.816 [0.759, 0.869] | 0.245 [0.158, 0.367] | 0.819 [0.727, 0.883] | 0.734 [0.650, 0.813] | 0.747 [0.356, 0.916] | 0.736 |
| `gnn5` | primary (ext:gnn_final) | 0.817 [0.756, 0.873] | 0.309 [0.194, 0.460] | 0.769 [0.676, 0.846] | 0.739 [0.659, 0.812] | 0.639 [0.430, 0.792] | 0.734 |
| `hybrid` | primary (ext:gnn_hybrid) | 0.832 [0.782, 0.881] | 0.301 [0.179, 0.452] | 0.818 [0.748, 0.870] | 0.752 [0.674, 0.822] | 0.647 [0.429, 0.815] | 0.779 |
| `tab_mem` | secondary | 0.811 [0.756, 0.860] | 0.252 [0.143, 0.396] | 0.804 [0.725, 0.864] | 0.718 [0.640, 0.790] | 0.642 [0.380, 0.811] | 0.773 |
| `edge` | secondary | 0.800 [0.753, 0.841] | 0.211 [0.134, 0.324] | 0.792 [0.696, 0.853] | 0.682 [0.604, 0.752] | 0.591 [0.337, 0.811] | 0.758 |
| `zs:global_window` | secondary | 0.829 [0.780, 0.875] | 0.261 [0.169, 0.374] | 0.816 [0.727, 0.879] | 0.735 [0.661, 0.806] | 0.733 [0.447, 0.891] | 0.744 |
| `zs:agent` | secondary | 0.849 [0.803, 0.893] | 0.234 [0.153, 0.363] | 0.836 [0.749, 0.897] | 0.771 [0.704, 0.836] | 0.834 [0.651, 0.926] | 0.780 |
| `oracle` | reference only | 0.908 [0.872, 0.945] | 0.590 [0.462, 0.714] | 0.872 [0.817, 0.921] | 0.870 [0.815, 0.922] | 0.876 [0.708, 0.972] | 0.812 |
| `comb:pairwise+hybrid` | exploratory | 0.861 [0.817, 0.904] | 0.328 [0.209, 0.489] | 0.849 [0.781, 0.901] | 0.798 [0.735, 0.856] | 0.770 [0.611, 0.867] | 0.781 |

Within mixed configs: 9 configs, 591 rows, 45 positives. Before announcement: 1786 rows, 42 positives.

| predictor | test_id | ood_family | ood_seed | branch | OOD pooled | time-matched (plan) test_id / ood_family / ood_seed / branch | R@5%FPR (held-out FPR) | R@5%FPR per split | Brier (raw score) |
|---|---|---|---|---|---|---|---|---|---|
| `clock` | 0.847 | 0.659 | 0.816 | 0.776 | 0.745 | 0.649 / 0.796 / 0.767 / 0.695 | 0.128 (0.029) | 0.13 / 0.06 / 0.17 / 0.15 | 0.059 |
| `bag+graph` | 0.902 | 0.786 | 0.759 | 0.737 | 0.758 | 0.798 / 0.886 / 0.730 / 0.695 | 0.276 (0.048) | 0.46 / 0.18 / 0.17 / 0.18 | 0.059 |
| `zs:pairwise` | 0.872 | 0.867 | 0.842 | 0.797 | 0.846 | 0.764 / 0.953 / 0.818 / 0.728 | 0.333 (0.045) | 0.31 / 0.52 / 0.25 / 0.27 | 0.259 |
| `zs:global_full` | 0.875 | 0.782 | 0.825 | 0.734 | 0.783 | 0.780 / 0.920 / 0.764 / 0.703 | 0.212 (0.032) | 0.22 / 0.18 / 0.25 / 0.18 | 0.084 |
| `gnn5` | 0.921 | 0.794 | 0.744 | 0.731 | 0.749 | 0.832 / 0.867 / 0.550 / 0.675 | 0.417 (0.054) | 0.72 / 0.18 / 0.33 / 0.24 | 0.062 |
| `hybrid` | 0.922 | 0.823 | 0.785 | 0.728 | 0.774 | 0.825 / 0.912 / 0.736 / 0.688 | 0.372 (0.063) | 0.63 / 0.27 / 0.28 / 0.15 | 0.057 |
| `tab_mem` | 0.895 | 0.807 | 0.780 | 0.699 | 0.759 | 0.796 / 0.905 / 0.756 / 0.663 | 0.250 (0.044) | 0.41 / 0.27 / 0.17 / 0.06 | 0.059 |
| `edge` | 0.837 | 0.812 | 0.780 | 0.728 | 0.777 | 0.689 / 0.890 / 0.772 / 0.671 | 0.288 (0.048) | 0.35 / 0.27 / 0.25 / 0.24 | 0.061 |
| `zs:global_window` | 0.868 | 0.829 | 0.829 | 0.751 | 0.807 | 0.744 / 0.937 / 0.739 / 0.721 | 0.173 (0.031) | 0.15 / 0.18 / 0.19 / 0.18 | 0.070 |
| `zs:agent` | 0.870 | 0.848 | 0.829 | 0.801 | 0.835 | 0.730 / 0.944 / 0.786 / 0.744 | 0.263 (0.054) | 0.31 / 0.27 / 0.17 / 0.27 | 0.282 |
| `oracle` | 0.925 | 0.896 | 0.922 | 0.875 | 0.898 | 0.831 / 0.926 / 0.887 / 0.819 | 0.788 (0.094) | 0.78 / 0.67 / 0.94 / 0.76 | 0.039 |
| `comb:pairwise+hybrid` | 0.911 | 0.862 | 0.824 | 0.788 | 0.830 | 0.816 / 0.944 / 0.797 / 0.750 | - | - | - |

Brier is on raw scores. The zero-shot scores are not calibrated, so their Brier is not comparable.

## 5. Primary family (ANALYSIS_PLAN.md §4b, 11 tests, Holm)

| # | comparison | statistic | estimate [95% CI] | p raw | p Holm | split differences test_id / ood_family / ood_seed / branch | same sign as pooled | verdict | split-stratified bootstrap p | row-level DeLong p (anti-conservative) |
|---|---|---|---|---|---|---|---|---|---|---|
| a1 | bag+graph - clock | time-matched (plan) | +0.080 [-0.012, +0.178] | 0.0998 | 0.781 | +0.149 / +0.090 / -0.038 / +0.000 | 3/4 | tie (gleichauf): Holm p = 0.781 >= 0.05; sign in 3/4 splits | 0.0840 | 0.0035 |
| a2 | zs:pairwise - clock | time-matched (plan) | +0.121 [+0.032, +0.213] | 0.0082 | 0.090 | +0.115 / +0.157 / +0.050 / +0.034 | 4/4 | tie (gleichauf): Holm p = 0.090 >= 0.05; sign in 4/4 splits | 0.0054 | 6.4e-07 |
| a3 | zs:global_full - clock | time-matched (plan) | +0.103 [+0.017, +0.188] | 0.0216 | 0.200 | +0.131 / +0.124 / -0.003 / +0.008 | 3/4 | tie (gleichauf): Holm p = 0.200 >= 0.05; sign in 3/4 splits | 0.0192 | 9.5e-06 |
| a4 | gnn5 - clock | time-matched (plan) | +0.053 [-0.048, +0.155] | 0.299 | 1.000 | +0.183 / +0.071 / -0.218 / -0.020 | 2/4 | tie (gleichauf): Holm p = 1.000 >= 0.05; sign in 2/4 splits | 0.241 | 0.082 |
| a5 | hybrid - clock | time-matched (plan) | +0.101 [+0.015, +0.193] | 0.0200 | 0.200 | +0.175 / +0.116 / -0.031 / -0.007 | 2/4 | tie (gleichauf): Holm p = 0.200 >= 0.05; sign in 2/4 splits | 0.0084 | 4e-05 |
| b1 | gnn5 - bag+graph | pooled AUROC | +0.004 [-0.036, +0.046] | 0.834 | 1.000 | +0.019 / +0.008 / -0.016 / -0.007 | 2/4 | tie (gleichauf): Holm p = 1.000 >= 0.05; sign in 2/4 splits | 0.833 | 0.76 |
| b2 | hybrid - bag+graph | pooled AUROC | +0.020 [-0.005, +0.045] | 0.112 | 0.781 | +0.020 / +0.037 / +0.026 / -0.009 | 3/4 | tie (gleichauf): Holm p = 0.781 >= 0.05; sign in 3/4 splits | 0.107 | 0.039 |
| b3 | zs:pairwise - bag+graph | pooled AUROC | +0.042 [-0.008, +0.096] | 0.0976 | 0.781 | -0.030 / +0.081 / +0.083 / +0.060 | 3/4 | tie (gleichauf): Holm p = 0.781 >= 0.05; sign in 3/4 splits | 0.0778 | 0.0061 |
| b4 | zs:pairwise - gnn5 | pooled AUROC | +0.038 [-0.025, +0.105] | 0.227 | 1.000 | -0.049 / +0.073 / +0.099 / +0.066 | 3/4 | tie (gleichauf): Holm p = 1.000 >= 0.05; sign in 3/4 splits | 0.205 | 0.015 |
| b5 | zs:pairwise - hybrid | pooled AUROC | +0.022 [-0.030, +0.075] | 0.379 | 1.000 | -0.050 / +0.044 / +0.057 / +0.069 | 3/4 | tie (gleichauf): Holm p = 1.000 >= 0.05; sign in 3/4 splits | 0.338 | 0.092 |
| b6 | zs:global_full - bag+graph | pooled AUROC | +0.003 [-0.050, +0.058] | 0.852 | 1.000 | -0.028 / -0.004 / +0.066 / -0.003 | 1/4 | tie (gleichauf): Holm p = 1.000 >= 0.05; sign in 1/4 splits | 0.848 | 0.83 |

- Holm on the split-stratified p-values: smallest 0.059; no test significant either.
- a1 (bag+graph - clock) reaches 3/4 only through branch +0.0005, i.e. a zero difference there.
- Seed sensitivity (B = 10,000 each), raw p per test in the order above:
  - seed 20261108: 0.0998, 0.0082, 0.0216, 0.2992, 0.0200, 0.8336, 0.1116, 0.0976, 0.2270, 0.3794, 0.8516; smallest Holm 0.090
  - seed 1: 0.0992, 0.0084, 0.0204, 0.3006, 0.0238, 0.8412, 0.1138, 0.0990, 0.2216, 0.3668, 0.8596; smallest Holm 0.092
  - seed 2: 0.0910, 0.0074, 0.0246, 0.3020, 0.0172, 0.8320, 0.1060, 0.1004, 0.2348, 0.3760, 0.8610; smallest Holm 0.081
  - seed 3: 0.0918, 0.0084, 0.0266, 0.2856, 0.0170, 0.8228, 0.1128, 0.1104, 0.2370, 0.3836, 0.8562; smallest Holm 0.092
- Cluster bootstrap SE / row-level DeLong SE for the pooled differences: gnn5 - bag+graph 1.50, hybrid - bag+graph 1.31, zs:pairwise - bag+graph 1.69, zs:pairwise - gnn5 2.08, zs:pairwise - hybrid 2.00, zs:global_full - bag+graph 1.78. Treating rows as independent understates the uncertainty (SE ratio 1.3-2.1); row-level DeLong p < 0.05 for 7 of the 11 primary tests, all of which are ties here.

**Sensitivity for family (a): harness tAUROC (round bins, positive-weighted) instead of the plan bins** (not part of the family):

| comparison | estimate [95% CI] | p raw | split differences test_id / ood_family / ood_seed / branch | same sign |
|---|---|---|---|---|
| bag+graph - clock | +0.191 [+0.105, +0.270] | <= 1e-4 | +0.274 / +0.272 / +0.013 / +0.097 | 4/4 |
| zs:pairwise - clock | +0.257 [+0.165, +0.349] | <= 1e-4 | +0.232 / +0.417 / +0.176 / +0.167 | 4/4 |
| zs:global_full - clock | +0.204 [+0.096, +0.307] | 0.0002 | +0.239 / +0.318 / +0.116 / +0.088 | 4/4 |
| gnn5 - clock | +0.209 [+0.121, +0.288] | <= 1e-4 | +0.310 / +0.298 / +0.020 / +0.077 | 4/4 |
| hybrid - clock | +0.222 [+0.132, +0.305] | <= 1e-4 | +0.304 / +0.334 / +0.037 / +0.083 | 4/4 |

**Why the two time-matchings disagree** (`scripts/diagnostics.py`): clock AUROC inside each rounds-to-cut bin, and the positive rate by deadline (cut) in that bin:

| rounds-to-cut bin | rows | positives | clock AUROC in bin | positive rate for cut 17 / 20 / 23 / 26 |
|---|---|---|---|---|
| <=-9 | 1144 | 33 | 0.754 | 0.000 / 0.000 / 0.057 / 0.038 |
| -8..-5 | 350 | 26 | 0.847 | 0.000 / 0.010 / 0.120 / 0.213 |
| -4..-1 | 312 | 62 | 0.609 | 0.111 / 0.250 / 0.367 / 0.088 |
| 0..3 | 235 | 26 | 0.581 | 0.143 / 0.138 / 0.147 / 0.000 |
| >3 | 297 | 9 | 0.690 | 0.024 / 0.022 / 0.111 / 0.000 |

Inside the round bins the clock is near chance (rounds 6-10: 0.500, rounds 11-15: 0.544, rounds 16-20: 0.526, rounds 21-25: 0.503, rounds 26-30: 0.740; the last bin holds only 5 positives). With rounds-to-cut bins, absolute time is still informative, and the plan's (a) test becomes a test against a clock of about 0.72 rather than 0.5. On night_train CV the clock's plan-binned AUROC is 0.635 (harness 0.401), and the monitors' CV values are bag+graph 0.813, hybrid 0.876, gnn5 0.872, zs:pairwise 0.894, zs:global_full 0.835 (computed here from the CV / zero-shot files). The margin shrinks on held-out data from both sides: the clock rises (0.635 -> 0.716) and every monitor falls (bag+graph -0.017, hybrid -0.058, gnn5 -0.103, zs:pairwise -0.056, zs:global_full -0.016), the zero-shot ones included.

## 6. Secondary analyses (uncorrected; raw p)

| label | comparison | statistic | estimate [95% CI] | p raw | split differences test_id / ood_family / ood_seed / branch | same sign |
|---|---|---|---|---|---|---|
| post hoc: tab_mem (hgb_bag+graph+mem) in place of bag+graph | gnn5 - tab_mem | pooled AUROC | +0.005 [-0.043, +0.055] | 0.817 | +0.026 / -0.014 / -0.036 / +0.032 | 2/4 |
| post hoc: tab_mem (hgb_bag+graph+mem) in place of bag+graph | hybrid - tab_mem | pooled AUROC | +0.021 [-0.005, +0.049] | 0.121 | +0.027 / +0.016 / +0.006 / +0.029 | 4/4 |
| post hoc: tab_mem (hgb_bag+graph+mem) in place of bag+graph | zs:pairwise - tab_mem | pooled AUROC | +0.043 [-0.006, +0.096] | 0.0812 | -0.023 / +0.060 / +0.063 / +0.098 | 3/4 |
| post hoc: tab_mem vs clock, time-matched (not in the family) | tab_mem - clock | time-matched (plan) | +0.088 [-0.012, +0.187] | 0.0904 | +0.146 / +0.109 / -0.012 / -0.032 | 2/4 |
| post hoc: zs:agent (agent-level LLM variant, not in the main set) | zs:agent - zs:pairwise | pooled AUROC | -0.006 [-0.021, +0.009] | 0.483 | -0.002 / -0.019 / -0.013 / +0.004 | 3/4 |
| post hoc: zs:agent, time-matched | zs:agent - zs:pairwise | time-matched (plan) | -0.002 [-0.024, +0.016] | 0.774 | -0.035 / -0.009 / -0.032 / +0.015 | 3/4 |
| post hoc: zs:agent (agent-level LLM variant, not in the main set) | zs:agent - hybrid | pooled AUROC | +0.017 [-0.033, +0.066] | 0.471 | -0.052 / +0.025 / +0.044 / +0.073 | 3/4 |
| post hoc: zs:agent, time-matched | zs:agent - hybrid | time-matched (plan) | +0.018 [-0.044, +0.069] | 0.505 | -0.095 / +0.032 / +0.050 / +0.056 | 3/4 |
| secondary (RQ3, not in the Holm family) | zs:pairwise - zs:global_full | pooled AUROC | +0.039 [-0.004, +0.082] | 0.0710 | -0.003 / +0.084 / +0.017 / +0.063 | 3/4 |
| secondary (RQ3), time-matched | zs:pairwise - zs:global_full | time-matched (plan) | +0.019 [-0.025, +0.070] | 0.416 | -0.016 / +0.033 / +0.054 / +0.026 | 3/4 |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | bag+graph - clock | time-matched (plan) | +0.043 [-0.067, +0.149] | 0.471 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:pairwise - clock | time-matched (plan) | +0.115 [+0.014, +0.216] | 0.0206 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:global_full - clock | time-matched (plan) | +0.081 [-0.010, +0.172] | 0.0854 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | gnn5 - clock | time-matched (plan) | -0.006 [-0.128, +0.102] | 0.941 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | hybrid - clock | time-matched (plan) | +0.057 [-0.048, +0.154] | 0.285 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | gnn5 - bag+graph | pooled AUROC | -0.009 [-0.067, +0.050] | 0.761 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | hybrid - bag+graph | pooled AUROC | +0.016 [-0.020, +0.051] | 0.368 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:pairwise - bag+graph | pooled AUROC | +0.088 [+0.029, +0.149] | 0.0026 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:pairwise - gnn5 | pooled AUROC | +0.097 [+0.016, +0.182] | 0.0198 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:pairwise - hybrid | pooled AUROC | +0.073 [+0.008, +0.137] | 0.0292 | - | - |
| secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs) | zs:global_full - bag+graph | pooled AUROC | +0.025 [-0.037, +0.091] | 0.441 | - | - |
| secondary: primary difference on test_id alone (12 configs) | bag+graph - clock | time-matched (plan) | +0.149 [-0.049, +0.354] | 0.146 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:pairwise - clock | time-matched (plan) | +0.115 [-0.123, +0.349] | 0.351 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:global_full - clock | time-matched (plan) | +0.131 [-0.114, +0.380] | 0.290 | - | - |
| secondary: primary difference on test_id alone (12 configs) | gnn5 - clock | time-matched (plan) | +0.183 [-0.010, +0.377] | 0.0636 | - | - |
| secondary: primary difference on test_id alone (12 configs) | hybrid - clock | time-matched (plan) | +0.175 [-0.020, +0.369] | 0.0764 | - | - |
| secondary: primary difference on test_id alone (12 configs) | gnn5 - bag+graph | pooled AUROC | +0.019 [-0.029, +0.067] | 0.398 | - | - |
| secondary: primary difference on test_id alone (12 configs) | hybrid - bag+graph | pooled AUROC | +0.020 [-0.007, +0.050] | 0.142 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:pairwise - bag+graph | pooled AUROC | -0.030 [-0.099, +0.038] | 0.453 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:pairwise - gnn5 | pooled AUROC | -0.049 [-0.118, +0.006] | 0.107 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:pairwise - hybrid | pooled AUROC | -0.050 [-0.115, +0.004] | 0.0828 | - | - |
| secondary: primary difference on test_id alone (12 configs) | zs:global_full - bag+graph | pooled AUROC | -0.028 [-0.120, +0.057] | 0.668 | - | - |
| exploratory, post hoc: mean-of-ranks combination, no fitting | comb:pairwise+hybrid - zs:pairwise | pooled AUROC | +0.006 [-0.021, +0.035] | 0.667 | +0.038 / -0.005 / -0.018 / -0.009 | 1/4 |
| exploratory, post hoc: combination, time-matched | comb:pairwise+hybrid - zs:pairwise | time-matched (plan) | +0.011 [-0.015, +0.043] | 0.445 | +0.052 / -0.009 / -0.021 / +0.021 | 2/4 |
| exploratory, post hoc: mean-of-ranks combination, no fitting | comb:pairwise+hybrid - hybrid | pooled AUROC | +0.029 [+0.004, +0.056] | 0.0238 | -0.012 / +0.039 / +0.039 / +0.060 | 3/4 |
| exploratory, post hoc: combination, time-matched | comb:pairwise+hybrid - hybrid | time-matched (plan) | +0.031 [+0.004, +0.064] | 0.0244 | -0.009 / +0.032 / +0.061 / +0.062 | 3/4 |
| extra: other predictors vs clock, time-matched (not in the family) | edge - clock | time-matched (plan) | +0.076 [-0.012, +0.150] | 0.0918 | +0.040 / +0.094 / +0.005 / -0.024 | 3/4 |
| extra: other predictors vs clock, time-matched (not in the family) | zs:global_window - clock | time-matched (plan) | +0.099 [+0.012, +0.186] | 0.0250 | +0.095 / +0.141 / -0.029 / +0.026 | 3/4 |
| extra: other predictors vs clock, time-matched (not in the family) | zs:agent - clock | time-matched (plan) | +0.119 [+0.028, +0.209] | 0.0144 | +0.080 / +0.148 / +0.018 / +0.049 | 4/4 |
| extra: other predictors vs clock, time-matched (not in the family) | oracle - clock | time-matched (plan) | +0.156 [+0.095, +0.233] | <= 1e-4 | +0.182 / +0.130 / +0.120 / +0.125 | 4/4 |
| check: refit noise (same tab_mem model refit in this environment) | tab_mem(refit here) - tab_mem | pooled AUROC | +0.002 [-0.003, +0.007] | 0.365 | +0.001 / -0.006 / +0.008 / +0.005 | 3/4 |
| context: bag+graph vs tab_mem (memory features) | bag+graph - tab_mem | pooled AUROC | +0.001 [-0.021, +0.023] | 0.916 | +0.007 / -0.021 / -0.020 / +0.039 | 2/4 |

AUPRC differences for the (b) pairs (descriptive, same draws): gnn5 - bag+graph +0.048 [-0.003, +0.122]; hybrid - bag+graph +0.041 [-0.004, +0.096]; zs:pairwise - bag+graph +0.013 [-0.096, +0.118]; zs:pairwise - gnn5 -0.035 [-0.175, +0.086]; zs:pairwise - hybrid -0.027 [-0.153, +0.087]; zs:global_full - bag+graph -0.015 [-0.135, +0.102].

## 7. Lead time and false alarms (held-out runs; thresholds from training data only)

| predictor | tipped runs alarmed before the tip | median lead [IQR] (rounds) | untipped runs with a false alarm | R@5%FPR (rows) | held-out row FPR |
|---|---|---|---|---|---|
| `clock` | 36/52 (0.69) | 3 [2, 5] | 48/48 (1.00) | 0.128 | 0.029 |
| `bag+graph` | 28/52 (0.54) | 4.5 [2, 6.25] | 20/48 (0.42) | 0.276 | 0.048 |
| `zs:pairwise` | 25/52 (0.48) | 2 [1, 5] | 10/48 (0.21) | 0.333 | 0.045 |
| `zs:global_full` | 17/52 (0.33) | 3 [1, 4] | 11/48 (0.23) | 0.212 | 0.032 |
| `gnn5` | 28/52 (0.54) | 5 [2.75, 7] | 14/48 (0.29) | 0.417 | 0.054 |
| `hybrid` | 28/52 (0.54) | 5.5 [3, 6.25] | 15/48 (0.31) | 0.372 | 0.063 |
| `tab_mem` | 27/52 (0.52) | 5 [2.5, 6] | 14/48 (0.29) | 0.250 | 0.044 |
| `edge` | 29/52 (0.56) | 4 [2, 6] | 14/48 (0.29) | 0.288 | 0.048 |
| `zs:global_window` | 19/52 (0.37) | 5 [2.5, 7] | 9/48 (0.19) | 0.173 | 0.031 |
| `zs:agent` | 22/52 (0.42) | 5 [2, 7] | 14/48 (0.29) | 0.263 | 0.054 |
| `oracle` | 48/52 (0.92) | 5 [3, 6] | 14/48 (0.29) | 0.788 | 0.094 |

The first six rows are the primary predictors. A run-level false alarm is any alarm on a labelled row of an untipped run, so even a ~5 % row FPR alarms a large share of 30-round runs; the clock alarms every untipped run.

## 8. Caveats

- **One GNN test look was already used.** The GNN team looked once at these held-out splits with these exact prediction files (LOOKS.md: test 1 of 2) and published the AUROCs. This analysis makes no new model choice, and the frozen predictions are only re-scored, but the GNN's held-out performance was known before it ran. Plan §0 also records that protocol (b) of the LLM monitors on the held-out splits was evaluated and committed earlier (68744e2).
- **The LLM monitors read raw message text, including task words.** The headline GNN / tabular models exclude the task lexicon (`mech_ref`, `pressure_lex`, ...) by rule (ablation only), so the information sets differ.
- **zs:global_full sees an implicit clock** (the whole transcript up to t). Its score has the highest rank correlation with the round of all predictors (Spearman 0.83 on held-out rows, vs clock 0.73, zs:pairwise 0.72, hybrid 0.69). Its pooled AUROC partly reflects time; the time-matched values are the fairer comparison.
- **Haiku is also one of the two jury judges** (DeepSeek + Haiku) whose edge / node scores are the GNN and tabular features. Its errors can reach both sides, so the GNN-vs-LLM comparison is not between independent information sources (the GNN team's judge-swap table in RESULTS.md step 9 shows the trained models depend on which judge produced the features).
- **ood_seed: the trigger is not in the communication** (injection via tool output), so a communication monitor sees only its consequences. Within round bins the trained monitors are near chance there (harness tAUROC on ood_seed: bag+graph 0.535, tab_mem 0.564, edge 0.541, gnn5 0.543, hybrid 0.560); the zero-shot monitors are higher (zs:pairwise 0.698, zs:global_full 0.638, zs:global_window 0.650, zs:agent 0.695).
- **Few configs per split** (12 / 8 / 8 / 8; positives in only 7 / 4 / 7 / 5 of them). Per-split signs, and so the >= 3/4 rule, rest on a few configs each. The within-mixed statistic rests on 9 configs and 45 positives (CI widths 0.24-0.56). A percentile cluster bootstrap with 36 clusters tends to give intervals that are somewhat too narrow, i.e. p-values that are too small; since no primary test is significant, this cannot overturn a verdict, but it argues against reading the uncorrected secondary p-values strictly.
- **bag+graph, clock and oracle were refit here** (§1.2): clock and oracle are bit-identical to the committed night_val predictions; bag+graph is not, and carries refit noise of the order of the tab_mem refit check (+0.002 [-0.003, +0.007] pooled).
- **Thresholds come from different pools by design:** trained models from night_train ID-OOF CV predictions (for gnn5 / hybrid the GNN team's 4-run CV proxy, not the 5-seed final model), zero-shot monitors from night_train + night_val raw scores. Realised held-out row FPRs range 0.029-0.094, so the recalls are not at an identical FPR.
- **Zero-shot prompt.** It was frozen on 8 night_train dev runs: untrained, but not developed blind to the training split. Nothing was tuned on held-out data.
- **Deviations from plan §5** (by instruction): rows are the GNN harness rows (branch prefixes once) rather than `llm_monitor.evaluate` (prefixes three times). The GNN models are the GNN team's frozen night_train-only models, not a train + val refit.
- **Time-matching definition matters** (§5): the pre-registered rounds-to-cut bins leave absolute time informative (clock 0.716). The harness round bins neutralise it (0.530), and the RQ2 verdict flips between the two.
- **Exploratory combination:** ranks are taken over the held-out rows. That is label-free, but it uses the test score distribution. It was defined after the primary results were known to the requester.

## 9. Files and commands

Python: `/Users/mauricio/sim_local/apart/sim_dataset/.venv/bin/python -I -B` (numpy, pandas, scipy, scikit-learn).

1. `git show <ref>:<path> > heldout/preds/{eval,cv}/<name>.csv`: prediction files (refs above).
2. `scripts/regen_baselines.py`: refits hgb_clock, hgb_bag+graph, oracle_risk+clock (+ checks) into `preds/regen/` (log `out/regen_baselines.log`); `scripts/check_table.py`: table rebuild check (`out/check_table.log`).
3. `stat/repo/gnn_opt/evaluate.py` with the GNN team's `test_look.sh` arguments: `out/harness_repro_y3.{txt,csv}`.
4. `scripts/analysis.py` (+ `scripts/hlib.py`): `out/results.json`, `out/analysis.log`, `out/table_predictors.csv`, `out/table_primary.csv`, `out/table_secondary.csv`.
5. `scripts/diagnostics.py`: `out/diagnostics.{json,log}`.
6. `scripts/make_report.py`: this file.

