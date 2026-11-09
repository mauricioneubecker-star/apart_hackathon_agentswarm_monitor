# Monitor comparison with statistical tests (harness CV, night_train)

GNN, zero-shot LLM monitors and baselines, all scored on **identical rows and folds**: the gnn_opt harness CV on night_train (3370 eval rows, 135 positives, 64 configs, 128 runs; 2 x 5 grouped ID folds + 8 LODO folds). Pre-registered predictor set and comparisons from `ANALYSIS_PLAN.md` §3-4. All numbers below were produced by the scripts listed in §9.

## Summary

- **(a) RQ2, every communication monitor beats the clock on time-matched AUROC.** Differences +0.378 to +0.484, all p ≤1e-4 (bootstrap floor 1/B), Holm p ≤ 0.0011, and the sign holds in all 8 LODO folds. The result holds with the plan's rounds-to-cut bins too (+0.179 to +0.259, all Holm p ≤ 0.0011). The bar is low: the clock's time-matched AUROC is 0.401, below chance, but every monitor's lower CI bound is also above 0.5 (lowest 0.709).
- **(b) Pooled ID AUROC, significant after Holm (11 tests):** gnn_hybrid - bag+graph +0.048 [+0.024, +0.078], Holm p = 0.0011, LODO 8/8; zs:pairwise - bag+graph +0.068 [+0.029, +0.112], Holm p = 0.0011, LODO 8/8.
- **(b) Not significant, a tie in the plan's wording ("gleichauf"):** gnn_final - bag+graph +0.036 [-0.006, +0.085], Holm p = 0.377, LODO 5/8; zs:pairwise - gnn_final +0.032 [-0.014, +0.085], Holm p = 0.614, LODO 7/8; zs:pairwise - gnn_hybrid +0.020 [-0.011, +0.053], Holm p = 0.614, LODO 7/8; zs:global_full - bag+graph +0.012 [-0.027, +0.050], Holm p = 0.614, LODO 7/8.
- **A row-level DeLong test is anti-conservative here.** For 3 of the 4 ties its raw p is < 0.05 (gnn_final - bag+graph DeLong p = 0.007 vs bootstrap p = 0.094, zs:pairwise - gnn_final DeLong p = 0.019 vs bootstrap p = 0.205, zs:pairwise - gnn_hybrid DeLong p = 0.034 vs bootstrap p = 0.226). The cluster-bootstrap standard errors are 1.44 to 1.87 times the DeLong ones, because the rows of one config are strongly dependent (§5).
- **Secondary (exploratory, not corrected):** these GNN controls and ablations differ from the matched reference m_noer (id0) by more than seed noise on at least one metric: control shuffle_labels, control shuffle_rows, ablation S2, ablation S1, ablation S0. These do not: control rewire, control shuffle_ef, ablation +clock, ablation +lex. Of the 22 id0 screen variants, the ones that clear seed noise are: `s_gtemp_none` (no temporal block). 18-fold architecture differences (m_* candidates, ensemble vs members) that clear it: none.

Scope: this is CV evidence on night_train only. The plan's full decision rule (§4) also needs sign agreement in at least 3 of the 4 held-out splits (protocol b). That criterion is **not** evaluated here, because the GNN still has 0 looks at the test splits.

## 1. Rows, keys and reproduction

- Dataset rebuilt with `gnn_opt/build_dataset.py --runs sim_dataset/runs_night` (scratch mini-repo, index.csv via symlink): 7560 snapshots, 6388 eval rows. The splits are not `unknown`: night_branch 524 rows / 33 pos, night_test_id 896 rows / 54 pos, night_test_ood_family 569 rows / 33 pos, night_test_ood_seed 349 rows / 36 pos, night_train 3370 rows / 135 pos, night_val 680 rows / 12 pos.
- night_train eval rows: 3370, 135 positives (prevalence 0.040), 64 configs, 128 runs. 45 runs tipped. 26 configs hold at least one positive row (at most 6 per config). Round bins 1-5 and 6-10 hold no positives.
- **Reproduction (step 1):** I ran `evaluate.py --pairs` on final, final+hgb_bag+graph+mem, hgb_bag+graph+mem, hgb_bag+graph, hgb_clock, edge_monitor_top3 and oracle_risk. It reproduces `gnn_opt_torch/preds/cv_table_final.csv` exactly: max |diff| = 0.0 over all 31-32 metric columns of all 7 models. Every value in the RESULTS.md step-4 table (select, ID AUROC/AUPRC, LODO mean/worst, tAUROC, R@5%FPR) is equal at 3 decimals: yes, for all 7 models. The bootstrap printout is identical too (e.g. final - hgb_bag+graph -0.003 / 0.035 / 0.083, share > 0 0.958; `step1_repro.log`).
- **LLM CV files (step 2),** built like `llm_monitor.py --to-cv`: every fold gets the same zero-shot score; run = episode_id, round = t, score = zs_tip (already /100, so 0-1). Each file has 17908 (run, round, fold) keys, identical to the GNN file `final.csv`. Missing vs the harness eval rows: pairwise 0, global_full 0, global_window 0; NaN scores: pairwise 0, global_full 0, global_window 0; distinct score values: pairwise 33, global_full 170, global_window 29. The harness labels (y3, risk, cfg, split) and llm_monitor `_base` (tip, risk_count, group_id, split) agree on all 3,370 rows.
- All 11 predictors were checked: 18 folds each, every fold holds exactly the eval rows of its test configs, no NaN, no missing OOF row.
- Sources: origin/gnn-opt-torch `6437efabdb`, origin/gnn-opt `38d1f5274e`. The LLM monitor data come from the worktree at origin/night-vx-validation `68744e2a35`.

## 2. Method

- **Unit of resampling = config** (64). Paired cluster bootstrap with B = 10,000 resamples (seed 20261108). All predictors and statistics share the same draws, so every difference is paired.
- The bootstrap is computed exactly, without materialising resampled rows. With config multiplicities k, AUROC(k) = k'Mk / ((k'n1)(k'n0)), where M[c,c'] counts the positive-in-c > negative-in-c' pairs (ties 0.5). Checks: equal to sklearn / harness `time_matched_auroc` on the full sample and on concatenated resamples (max |diff| 1.1e-16). With the harness's own draws (seed 0, 1000), it reproduces the `evaluate.py --pairs` quantiles bit for bit.
- **Scores:** repeat-averaged ID out-of-fold scores (`harness.id_oof`, as in `evaluate.py --pairs`). For the zero-shot monitors this is the raw score. The harness table's "ID AUROC" is the mean of the two per-repeat pooled AUROCs; it is reported as a sensitivity ("rep-mean").
- **Statistics:** (a) time-matched AUROC as in the harness (`metrics.time_matched_auroc`): AUROC within round bins 1-5, 6-10, ..., 26-30, weighted by positives. Because bins 1-10 have no positives, 4 bins remain. As a sensitivity, the plan / llm_monitor definition: rounds-to-cut bins (≤-9, -8..-5, -4..-1, 0..3, >3; cut = per-config deadline round 17/20/23/26), pairs-weighted. (b) pooled ID AUROC.
- **Estimate** = full-sample difference. **CI** = 2.5/97.5 % percentiles of the bootstrap differences. **p** = 2·min(P*(d ≤ 0), P*(d ≥ 0)), floored at 1/B = 1e-04. **Holm** over the 11 primary comparisons.
- **LODO sign count:** the same statistic in each of the 8 LODO folds, using each fold's own predictions (the trained models never saw the held-out domain). It counts the folds whose difference has the sign of the full-sample estimate, plus an exact two-sided binomial sign test. The LODO folds overlap (K2/K4 partition the configs; the other six cut across them), so the sign test is descriptive.
- **DeLong** (row-level, Sun & Xu) is shown only as a contrast (§5).

## 3. Joint harness table (step 3, `evaluate.py`, identical rows)

| model | select | ID AUROC | ID AUPRC | LODO mean | LODO worst | tAUROC | R@5%FPR | risk<=2 | risk3-7 | mixed | board | team/dm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| zs:pairwise | 0.905 | 0.922 | 0.257 | 0.920 | 0.873 | 0.886 | 0.474 | 0.856 | 0.714 | 0.895 | 0.922 | 0.925 |
| zs:global_full | 0.859 | 0.865 | 0.150 | 0.877 | 0.835 | 0.811 | 0.215 | 0.766 | 0.683 | 0.855 | 0.849 | 0.890 |
| zs:global_window | 0.870 | 0.880 | 0.166 | 0.888 | 0.842 | 0.808 | 0.244 | 0.815 | 0.689 | 0.839 | 0.863 | 0.886 |
| gnn_final | 0.839 | 0.880 | 0.280 | 0.870 | 0.766 | 0.847 | 0.570 | 0.731 | 0.766 | 0.882 | 0.873 | 0.767 |
| gnn_hybrid | 0.875 | 0.898 | 0.275 | 0.895 | 0.831 | 0.850 | 0.556 | 0.755 | 0.780 | 0.886 | 0.877 | 0.861 |
| hgb_bag+graph+mem | 0.848 | 0.867 | 0.234 | 0.864 | 0.814 | 0.806 | 0.400 | 0.707 | 0.727 | 0.839 | 0.848 | 0.874 |
| hgb_bag+graph | 0.834 | 0.843 | 0.197 | 0.848 | 0.811 | 0.779 | 0.378 | 0.699 | 0.735 | 0.812 | 0.823 | 0.809 |
| hgb_bag | 0.810 | 0.820 | 0.172 | 0.834 | 0.777 | 0.753 | 0.289 | 0.700 | 0.688 | 0.777 | 0.804 | 0.812 |
| edge_monitor_top3 | 0.836 | 0.870 | 0.216 | 0.858 | 0.779 | 0.798 | 0.444 | 0.828 | 0.736 | 0.823 | 0.854 | 0.902 |
| hgb_clock | 0.727 | 0.754 | 0.077 | 0.747 | 0.681 | 0.401 | 0.074 | 0.676 | 0.681 | 0.695 | 0.779 | 0.661 |
| oracle_risk | 0.926 | 0.926 | 0.425 | 0.947 | 0.906 | 0.907 | 0.615 | 0.742 | 0.650 | 0.931 | 0.927 | 0.959 |

LODO AUROC per fold:

| model | K2 | K4 | mix_duo | mix_majority | nonboard | seed_external | seed_pioneer | topo_clustered |
|---|---|---|---|---|---|---|---|---|
| zs:pairwise | 0.967 | 0.884 | 0.936 | 0.907 | 0.925 | 0.873 | 0.957 | 0.914 |
| zs:global_full | 0.903 | 0.835 | 0.857 | 0.873 | 0.890 | 0.846 | 0.914 | 0.899 |
| zs:global_window | 0.922 | 0.842 | 0.890 | 0.872 | 0.886 | 0.872 | 0.910 | 0.911 |
| gnn_final | 0.915 | 0.766 | 0.893 | 0.820 | 0.839 | 0.924 | 0.951 | 0.852 |
| gnn_hybrid | 0.938 | 0.831 | 0.890 | 0.881 | 0.888 | 0.932 | 0.929 | 0.873 |
| hgb_bag+graph+mem | 0.906 | 0.814 | 0.829 | 0.876 | 0.903 | 0.878 | 0.855 | 0.851 |
| hgb_bag+graph | 0.889 | 0.811 | 0.839 | 0.870 | 0.853 | 0.867 | 0.819 | 0.837 |
| hgb_bag | 0.867 | 0.777 | 0.824 | 0.864 | 0.840 | 0.844 | 0.811 | 0.844 |
| edge_monitor_top3 | 0.779 | 0.834 | 0.862 | 0.880 | 0.910 | 0.849 | 0.851 | 0.896 |
| hgb_clock | 0.777 | 0.776 | 0.722 | 0.772 | 0.681 | 0.723 | 0.800 | 0.721 |
| oracle_risk | 0.974 | 0.919 | 0.949 | 0.932 | 0.967 | 0.978 | 0.951 | 0.906 |

Notes: the zero-shot monitors are untrained, so their "LODO" values are AUROCs on domain subsets, not domain-shift tests. Their selection score therefore means something different. R@5%FPR uses the 5 %-FPR threshold of the same CV scores for every model (zero-shot scores are coarse and tied, so the realised FPR is < 5 %). Brier is meaningless for the uncalibrated zero-shot scores and is left out. The mixed column covers the 7 mixed-outcome configs present in night_train.

## 4. Primary family (pre-registered, Holm over 11 comparisons)

| # | family | comparison | metric | A | B | Δ = A − B | 95 % CI | p raw | p Holm | LODO same sign | sign-test p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | (a) | bag+graph - clock | tAUROC | 0.779 | 0.401 | **+0.378** | [+0.294, +0.456] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 2 | (a) | zs:pairwise - clock | tAUROC | 0.886 | 0.401 | **+0.484** | [+0.413, +0.549] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 3 | (a) | zs:global_full - clock | tAUROC | 0.811 | 0.401 | **+0.410** | [+0.318, +0.493] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 4 | (a) | gnn_final - clock | tAUROC | 0.847 | 0.401 | **+0.446** | [+0.364, +0.523] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 5 | (a) | gnn_hybrid - clock | tAUROC | 0.850 | 0.401 | **+0.448** | [+0.373, +0.520] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 6 | (b) | gnn_final - bag+graph | AUROC | 0.890 | 0.854 | **+0.036** | [-0.006, +0.085] | 0.0942 | 0.3768 | 5/8 | 0.727 | tie |
| 7 | (b) | gnn_hybrid - bag+graph | AUROC | 0.902 | 0.854 | **+0.048** | [+0.024, +0.078] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 8 | (b) | zs:pairwise - bag+graph | AUROC | 0.922 | 0.854 | **+0.068** | [+0.029, +0.112] | ≤1e-4 | 0.0011 | 8/8 | 0.008 | **different** |
| 9 | (b) | zs:pairwise - gnn_final | AUROC | 0.922 | 0.890 | **+0.032** | [-0.014, +0.085] | 0.2048 | 0.6144 | 7/8 | 0.070 | tie |
| 10 | (b) | zs:pairwise - gnn_hybrid | AUROC | 0.922 | 0.902 | **+0.020** | [-0.011, +0.053] | 0.2258 | 0.6144 | 7/8 | 0.070 | tie |
| 11 | (b) | zs:global_full - bag+graph | AUROC | 0.865 | 0.854 | **+0.012** | [-0.027, +0.050] | 0.5478 | 0.6144 | 7/8 | 0.070 | tie |

Sensitivity of the primary family. (a) uses the plan's rounds-to-cut time bins; (b) uses the harness per-repeat-mean AUROC. Holm is recomputed over the 11 sensitivity p-values. "seed-aware" adds the training-seed variance of a single GNN (from the seed-0 vs seed-100 pairs, 18-fold OOF) to the bootstrap variance; this is pessimistic for the 4-member ensemble (normal approximation).

| # | comparison | sensitivity Δ | 95 % CI | p | p Holm | LODO same sign | seed-aware 95 % CI | seed-aware p |
|---|---|---|---|---|---|---|---|---|
| 1 | bag+graph - clock (rtc bins) | +0.179 | [+0.098, +0.276] | ≤1e-4 | 0.0011 | 7/8 | - | - |
| 2 | zs:pairwise - clock (rtc bins) | +0.259 | [+0.176, +0.360] | ≤1e-4 | 0.0011 | 8/8 | - | - |
| 3 | zs:global_full - clock (rtc bins) | +0.201 | [+0.116, +0.299] | ≤1e-4 | 0.0011 | 8/8 | - | - |
| 4 | gnn_final - clock (rtc bins) | +0.239 | [+0.148, +0.349] | ≤1e-4 | 0.0011 | 8/8 | - | - |
| 5 | gnn_hybrid - clock (rtc bins) | +0.241 | [+0.156, +0.344] | ≤1e-4 | 0.0011 | 8/8 | - | - |
| 6 | gnn_final - bag+graph (rep-mean) | +0.037 | [-0.006, +0.085] | 0.0938 | 0.3616 | - | [-0.010, +0.083] | 0.1264 |
| 7 | gnn_hybrid - bag+graph (rep-mean) | +0.055 | [+0.032, +0.083] | ≤1e-4 | 0.0011 | - | [+0.020, +0.077] | 0.0009 |
| 8 | zs:pairwise - bag+graph (rep-mean) | +0.079 | [+0.041, +0.121] | ≤1e-4 | 0.0011 | - | - | - |
| 9 | zs:pairwise - gnn_final (rep-mean) | +0.042 | [-0.006, +0.098] | 0.0904 | 0.3616 | - | [-0.019, +0.083] | 0.2189 |
| 10 | zs:pairwise - gnn_hybrid (rep-mean) | +0.024 | [-0.008, +0.058] | 0.1462 | 0.3616 | - | [-0.014, +0.054] | 0.2490 |
| 11 | zs:global_full - bag+graph (rep-mean) | +0.022 | [-0.014, +0.059] | 0.2348 | 0.3616 | - | - | - |

LODO fold differences (A − B; (a) tAUROC, (b) AUROC):

| comparison | K2 | K4 | seed_external | seed_pioneer | nonboard | mix_duo | mix_majority | topo_clustered |
|---|---|---|---|---|---|---|---|---|
| bag+graph - clock | +0.328 | +0.201 | +0.202 | +0.192 | +0.206 | +0.261 | +0.282 | +0.301 |
| zs:pairwise - clock | +0.452 | +0.295 | +0.229 | +0.422 | +0.287 | +0.411 | +0.338 | +0.404 |
| zs:global_full - clock | +0.385 | +0.217 | +0.237 | +0.376 | +0.228 | +0.313 | +0.294 | +0.397 |
| gnn_final - clock | +0.384 | +0.247 | +0.281 | +0.396 | +0.145 | +0.377 | +0.256 | +0.343 |
| gnn_hybrid - clock | +0.406 | +0.240 | +0.293 | +0.364 | +0.222 | +0.341 | +0.298 | +0.348 |
| gnn_final - bag+graph | +0.025 | -0.045 | +0.056 | +0.132 | -0.014 | +0.054 | -0.050 | +0.015 |
| gnn_hybrid - bag+graph | +0.049 | +0.020 | +0.065 | +0.110 | +0.035 | +0.051 | +0.011 | +0.036 |
| zs:pairwise - bag+graph | +0.078 | +0.073 | +0.005 | +0.138 | +0.072 | +0.098 | +0.037 | +0.077 |
| zs:pairwise - gnn_final | +0.052 | +0.118 | -0.051 | +0.006 | +0.086 | +0.044 | +0.088 | +0.062 |
| zs:pairwise - gnn_hybrid | +0.029 | +0.053 | -0.060 | +0.028 | +0.037 | +0.047 | +0.026 | +0.041 |
| zs:global_full - bag+graph | +0.013 | +0.024 | -0.021 | +0.096 | +0.037 | +0.018 | +0.003 | +0.061 |

### Per predictor (full-sample value [95 % cluster-bootstrap CI], repeat-averaged OOF)

| predictor | AUROC | AUROC rep-mean | AUPRC | tAUROC (round bins) | tAUROC (rtc bins) | within mixed cfg × time | before 1st announcement |
|---|---|---|---|---|---|---|---|
| clock | 0.753 [0.702, 0.799] | 0.754 | 0.076 [0.048, 0.116] | 0.401 [0.347, 0.461] | 0.635 [0.521, 0.734] | 0.658 [0.578, 0.760] | 0.700 [0.622, 0.790] |
| bag+graph | 0.854 [0.802, 0.899] | 0.843 | 0.206 [0.124, 0.326] | 0.779 [0.709, 0.843] | 0.813 [0.730, 0.880] | 0.729 [0.606, 0.833] | 0.756 [0.602, 0.868] |
| zs:pairwise | 0.922 [0.896, 0.946] | 0.922 | 0.257 [0.171, 0.374] | 0.886 [0.845, 0.922] | 0.894 [0.845, 0.932] | 0.774 [0.491, 0.971] | 0.883 [0.803, 0.940] |
| zs:global_full | 0.865 [0.822, 0.905] | 0.865 | 0.150 [0.090, 0.261] | 0.811 [0.744, 0.872] | 0.835 [0.758, 0.897] | 0.707 [0.477, 0.914] | 0.808 [0.702, 0.887] |
| gnn_final | 0.890 [0.838, 0.935] | 0.880 | 0.284 [0.188, 0.413] | 0.847 [0.783, 0.906] | 0.874 [0.811, 0.925] | 0.940 [0.865, 0.991] | 0.742 [0.559, 0.876] |
| gnn_hybrid | 0.902 [0.865, 0.936] | 0.898 | 0.282 [0.183, 0.435] | 0.850 [0.792, 0.903] | 0.875 [0.816, 0.924] | 0.910 [0.797, 0.982] | 0.795 [0.676, 0.885] |
| bag+graph+mem | 0.876 [0.834, 0.915] | 0.867 | 0.232 [0.142, 0.370] | 0.806 [0.741, 0.866] | 0.838 [0.765, 0.898] | 0.797 [0.596, 0.927] | 0.780 [0.646, 0.873] |
| zs:global_window | 0.880 [0.841, 0.914] | 0.880 | 0.166 [0.102, 0.266] | 0.808 [0.748, 0.864] | 0.834 [0.760, 0.895] | 0.677 [0.396, 0.944] | 0.848 [0.770, 0.905] |
| edge_monitor_top3 | 0.877 [0.834, 0.914] | 0.870 | 0.225 [0.145, 0.337] | 0.798 [0.731, 0.858] | 0.836 [0.766, 0.892] | 0.812 [0.590, 0.975] | 0.836 [0.768, 0.891] |
| bag | 0.833 [0.776, 0.882] | 0.820 | 0.182 [0.108, 0.293] | 0.753 [0.679, 0.822] | 0.790 [0.701, 0.861] | 0.744 [0.429, 0.943] | 0.760 [0.597, 0.876] |
| oracle_risk | 0.923 [0.889, 0.956] | 0.926 | 0.418 [0.311, 0.579] | 0.907 [0.866, 0.945] | 0.898 [0.840, 0.946] | 0.977 [0.935, 1.000] | 0.798 [0.640, 0.923] |

Prevalence = 0.040. "Within mixed cfg × time" is the plan's "innerhalb gleicher Setups": a pairs-weighted AUROC within (config × rounds-to-cut bin) strata of the 7 mixed-outcome configs, so its CIs are very wide. "Before 1st announcement" covers rows before the first shortcut announcement (llm_monitor definition); it holds few positives. Both columns are descriptive and not tested.

### Supplementary comparisons (not in the Holm family, raw p)

| comparison | metric | Δ | 95 % CI | p raw | LODO same sign | DeLong p (contrast) |
|---|---|---|---|---|---|---|
| bag+graph+mem - clock | tAUROC | +0.404 | [+0.326, +0.480] | ≤1e-4 | 8/8 | - |
| zs:global_window - clock | tAUROC | +0.407 | [+0.323, +0.484] | ≤1e-4 | 8/8 | - |
| gnn_final - bag+graph+mem | AUROC | +0.015 | [-0.032, +0.061] | 0.5190 | 5/8 | 0.27 |
| gnn_hybrid - bag+graph+mem | AUROC | +0.027 | [+0.005, +0.050] | 0.0122 | 7/8 | 5.6e-05 |
| zs:pairwise - bag+graph+mem | AUROC | +0.046 | [+0.013, +0.081] | 0.0052 | 7/8 | 2.2e-05 |
| zs:global_full - bag+graph+mem | AUROC | -0.010 | [-0.046, +0.023] | 0.5768 | 4/8 | 0.38 |
| bag+graph+mem - bag+graph | AUROC | +0.022 | [+0.001, +0.044] | 0.0400 | 7/8 | 0.0029 |
| zs:global_window - bag+graph | AUROC | +0.026 | [-0.010, +0.062] | 0.1570 | 8/8 | 0.04 |
| zs:pairwise - zs:global_full | AUROC | +0.057 | [+0.025, +0.091] | 2.0e-04 | 8/8 | 5.3e-10 |
| zs:pairwise - zs:global_window | AUROC | +0.043 | [+0.018, +0.069] | 2.0e-04 | 8/8 | 9.8e-08 |
| gnn_hybrid - gnn_final | AUROC | +0.012 | [-0.012, +0.038] | 0.3590 | 6/8 | 0.1 |
| zs:pairwise - edge_monitor_top3 | AUROC | +0.045 | [+0.011, +0.086] | 0.0058 | 8/8 | 9e-05 |
| zs:pairwise - oracle_risk | AUROC | -0.001 | [-0.035, +0.031] | 0.9074 | 6/8 | 0.92 |
| bag+graph - clock | AUROC | +0.101 | [+0.042, +0.161] | 8.0e-04 | 8/8 | 9.5e-09 |
| zs:pairwise - clock | AUROC | +0.169 | [+0.122, +0.223] | ≤1e-4 | 8/8 | 7e-31 |
| zs:global_full - clock | AUROC | +0.113 | [+0.056, +0.173] | 2.0e-04 | 8/8 | 1e-12 |
| gnn_final - clock | AUROC | +0.137 | [+0.068, +0.207] | 4.0e-04 | 7/8 | 4.8e-13 |
| gnn_hybrid - clock | AUROC | +0.149 | [+0.095, +0.208] | ≤1e-4 | 8/8 | 7.9e-21 |

LLM sampling noise (zs:global_full, which averages k = 3 samples): using only the first sample changes AUROC by -0.005 [-0.013, +0.003] and tAUROC by -0.005 [-0.020, +0.009]. Sampling noise cannot be measured for zs:pairwise (k = 1).

## 5. Contrast: row-level DeLong vs the cluster bootstrap

| comparison | Δ AUROC | bootstrap 95 % CI | bootstrap p | DeLong 95 % CI | DeLong p | SE ratio boot / DeLong | implied design effect |
|---|---|---|---|---|---|---|---|
| gnn_final - bag+graph | +0.036 | [-0.006, +0.085] | 0.0942 | [+0.010, +0.063] | 0.007 | 1.72 | 3.0 |
| gnn_hybrid - bag+graph | +0.048 | [+0.024, +0.078] | ≤1e-4 | [+0.031, +0.065] | 2e-08 | 1.58 | 2.5 |
| zs:pairwise - bag+graph | +0.068 | [+0.029, +0.112] | ≤1e-4 | [+0.044, +0.093] | 3.9e-08 | 1.69 | 2.8 |
| zs:pairwise - gnn_final | +0.032 | [-0.014, +0.085] | 0.2048 | [+0.005, +0.058] | 0.019 | 1.87 | 3.5 |
| zs:pairwise - gnn_hybrid | +0.020 | [-0.011, +0.053] | 0.2258 | [+0.001, +0.038] | 0.034 | 1.75 | 3.1 |
| zs:global_full - bag+graph | +0.012 | [-0.027, +0.050] | 0.5478 | [-0.015, +0.038] | 0.4 | 1.44 | 2.1 |
| gnn_final - bag+graph+mem | +0.015 | [-0.032, +0.061] | 0.5190 | [-0.011, +0.040] | 0.27 | 1.80 | 3.2 |
| gnn_hybrid - bag+graph+mem | +0.027 | [+0.005, +0.050] | 0.0122 | [+0.014, +0.039] | 5.6e-05 | 1.74 | 3.0 |
| zs:pairwise - bag+graph+mem | +0.046 | [+0.013, +0.081] | 0.0052 | [+0.025, +0.068] | 2.2e-05 | 1.58 | 2.5 |
| zs:global_full - bag+graph+mem | -0.010 | [-0.046, +0.023] | 0.5768 | [-0.033, +0.012] | 0.38 | 1.54 | 2.4 |
| bag+graph+mem - bag+graph | +0.022 | [+0.001, +0.044] | 0.0400 | [+0.007, +0.036] | 0.0029 | 1.50 | 2.3 |
| zs:global_window - bag+graph | +0.026 | [-0.010, +0.062] | 0.1570 | [+0.001, +0.050] | 0.04 | 1.47 | 2.2 |

DeLong treats the 3,370 snapshots as independent draws. They are not. Consecutive rounds of one run share almost the same transcript, and its features and labels are autocorrelated: y3 is 1 for up to 3 consecutive rows before a tip. The two runs of a config share the setup, and the 135 positive rows come from only 45 tipped runs in 26 configs. The effective sample size is the number of configs, not rows. The row-level variance is too small by the design effect above, so DeLong p-values are too small. The cluster bootstrap resamples whole configs and keeps this dependence.

## 6. Secondary: GNN structure controls, ablations and seed noise (exploratory, no correction, plan §9)

**Matched reference.** `mac_log.jsonl` / `experiments/mac_*.jsonl` show that every control and ablation uses config {epochs 30, edge_readout off}, seed 0, cv id0 (+ control / feat / clock). That is the config of `m_noer`. Its id0 folds (`m_noer__s1`, merged into `m_noer.csv` with 0 differences) are the reference of RESULTS.md step 5: AUROC 0.871 [0.814, 0.923], tAUROC 0.830 [0.764, 0.891], AUPRC 0.293. RESULTS.md has 0.871 [0.816, 0.921] with 1000 resamples. The reference is unambiguous; no fallback was needed.

**Seed noise floor (id0, single model).** The pooled SD of a single-seed AUROC is 0.018 (df 4: s_base trio with seeds 0/100/200, plus the m_noer_swa and m_tmemgru seed-0 vs seed-100 pairs on id0). For a difference of two single-seed models that gives SD 0.026 and a 95 % band of ±0.071 (t, 4 df). The largest observed seed |Δ| on id0 is 0.039. For tAUROC: SD 0.017, band ±0.068, max observed 0.039. On the 18-fold repeat-averaged OOF statistic the seed noise is smaller: SD 0.0052 (2 df), max observed 0.0095.

| seed pair | set | Δ AUROC | 95 % CI | p | Δ tAUROC | 95 % CI | Δ select | Δ LODO worst |
|---|---|---|---|---|---|---|---|---|
| s_base − s_base_r1 | id0 | +0.000 | [-0.060, +0.051] | 0.9300 | +0.006 | [-0.051, +0.055] | - | - |
| s_base − s_base_r2 | id0 | +0.039 | [-0.013, +0.100] | 0.1556 | +0.039 | [-0.014, +0.100] | - | - |
| s_base_r1 − s_base_r2 | id0 | +0.039 | [-0.013, +0.102] | 0.1678 | +0.033 | [-0.018, +0.094] | - | - |
| m_noer_swa − m_noer_swa_s1 | id0 | -0.003 | [-0.039, +0.032] | 0.8758 | +0.004 | [-0.033, +0.039] | - | - |
| m_tmemgru − m_tmemgru_s1 | id0 | -0.024 | [-0.060, +0.006] | 0.1290 | -0.024 | [-0.063, +0.011] | - | - |
| s_noer − m_noer (same seed, rerun) | id0 | +0.019 | [-0.001, +0.046] | 0.0620 | +0.020 | [-0.001, +0.049] | - | - |
| m_noer_swa − m_noer_swa_s1 | 18-fold OOF | -0.010 | [-0.046, +0.021] | 0.5966 | -0.003 | [-0.036, +0.026] | +0.002 | +0.024 |
| m_tmemgru − m_tmemgru_s1 | 18-fold OOF | -0.004 | [-0.040, +0.027] | 0.8284 | +0.002 | [-0.039, +0.040] | -0.006 | +0.011 |

s_base, s_base_r1 and s_base_r2 are the same DEFAULT config with the default seed (0, as logged for the m_* runs that also set no seed), 100 and 200 (`experiments/screen_id0.jsonl`). m_noer_swa_s1 and m_tmemgru_s1 are seed 100 ("seed 2" in RESULTS.md). s_noer and m_noer have the same config and the same seed but come from separate runs (screen vs main search). Their difference shows run-to-run nondeterminism, or a code change between the two runs (cannot be told apart from the files).

**Controls and ablations vs m_noer (id0, 5 folds, seed 0).** "> max seed" means |Δ| is larger than the largest observed seed difference. "> 95 % band" means |Δ| is larger than t·√2·σ_seed. "seed-aware CI" = Δ ± 1.96·√(SE_boot² + 2σ²_seed).

| variant | AUROC [CI] | Δ AUROC [CI] | p | > max seed | > 95 % band | seed-aware CI excl. 0 | tAUROC | Δ tAUROC [CI] | p | > max seed | > 95 % band | seed-aware CI excl. 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control rewire | 0.867 [0.807, 0.920] | -0.004 [-0.032, +0.023] | 0.7856 | no | no | no | 0.820 | -0.011 [-0.044, +0.021] | 0.5232 | no | no | no |
| control shuffle_ef | 0.830 [0.743, 0.901] | -0.041 [-0.096, +0.006] | 0.0914 | yes | no | no | 0.769 | -0.062 [-0.118, -0.009] | 0.0198 | yes | no | no |
| control shuffle_labels | 0.737 [0.670, 0.799] | -0.134 [-0.218, -0.051] | 0.0022 | yes | yes | yes | 0.587 | -0.243 [-0.348, -0.140] | 2.0e-04 | yes | yes | yes |
| control shuffle_rows | 0.421 [0.310, 0.535] | -0.450 [-0.590, -0.303] | ≤1e-4 | yes | yes | yes | 0.431 | -0.399 [-0.543, -0.248] | ≤1e-4 | yes | yes | yes |
| ablation +clock | 0.851 [0.785, 0.909] | -0.021 [-0.079, +0.036] | 0.4816 | no | no | no | 0.803 | -0.028 [-0.089, +0.034] | 0.3760 | no | no | no |
| ablation +lex | 0.851 [0.793, 0.908] | -0.020 [-0.065, +0.026] | 0.3802 | no | no | no | 0.823 | -0.007 [-0.057, +0.044] | 0.7908 | no | no | no |
| ablation S2 | 0.814 [0.742, 0.877] | -0.057 [-0.107, -0.006] | 0.0284 | yes | no | no | 0.728 | -0.102 [-0.168, -0.039] | 0.0020 | yes | yes | yes |
| ablation S1 | 0.790 [0.694, 0.874] | -0.081 [-0.146, -0.021] | 0.0052 | yes | yes | yes | 0.703 | -0.127 [-0.198, -0.056] | 2.0e-04 | yes | yes | yes |
| ablation S0 | 0.804 [0.699, 0.891] | -0.067 [-0.134, -0.008] | 0.0248 | yes | no | no | 0.715 | -0.115 [-0.191, -0.044] | 4.0e-04 | yes | yes | yes |

Chance checks: shuffle_rows AUROC 0.421 [0.310, 0.535] (contains 0.5). shuffle_labels keeps the label-vs-round prior: AUROC 0.737, but tAUROC 0.587 [0.501, 0.673].

**Architectures, 18 folds (seed 0; repeat-averaged OOF).** Seed noise comes from the two 18-fold seed pairs (band ±0.031 AUROC and ±0.010 tAUROC, t with 2 df, so imprecise). Δ select and Δ LODO worst are point values from `harness.cv_summary`, without CI.

| comparison | Δ AUROC [CI] | p | seed-aware excl. 0 | Δ tAUROC [CI] | p | seed-aware excl. 0 | Δ select | Δ LODO worst |
|---|---|---|---|---|---|---|---|---|
| m_noer_swa − m_noer | -0.012 [-0.046, +0.018] | 0.4848 | no | -0.002 [-0.031, +0.025] | 0.8910 | no | +0.020 | +0.051 |
| m_tmemgru − m_noer | -0.020 [-0.048, +0.003] | 0.1030 | no | -0.025 [-0.060, +0.004] | 0.1002 | no | +0.021 | +0.084 |
| m_noer_crop10 − m_noer | -0.001 [-0.027, +0.026] | 0.9234 | no | +0.007 [-0.022, +0.035] | 0.6538 | no | +0.005 | +0.015 |
| m_tmemgru − m_noer_swa | -0.008 [-0.050, +0.035] | 0.6740 | no | -0.022 [-0.063, +0.016] | 0.2484 | no | +0.001 | +0.033 |
| gnn_final − m_noer_swa | +0.019 [-0.004, +0.050] | 0.1328 | no | +0.008 [-0.013, +0.033] | 0.5416 | no | +0.020 | +0.010 |
| gnn_final − m_tmemgru | +0.027 [+0.001, +0.058] | 0.0386 | no | +0.030 [+0.002, +0.064] | 0.0346 | no | +0.020 | -0.022 |

**id0 screen (22 variants vs s_base, seed 0).** Rows sorted by Δ AUROC.

| variant | AUROC | Δ AUROC [CI] | p | > max seed | seed-aware excl. 0 | Δ tAUROC [CI] | p | seed-aware excl. 0 |
|---|---|---|---|---|---|---|---|---|
| s_noer | 0.890 | +0.011 [-0.019, +0.045] | 0.5430 | no | no | +0.007 [-0.024, +0.040] | 0.7032 | no |
| s_novn | 0.876 | -0.003 [-0.035, +0.033] | 0.8012 | no | no | -0.001 [-0.034, +0.035] | 0.9366 | no |
| s_gtemp_none_tmem_gru | 0.876 | -0.004 [-0.043, +0.038] | 0.8062 | no | no | -0.013 [-0.058, +0.031] | 0.5562 | no |
| s_gine | 0.875 | -0.004 [-0.036, +0.030] | 0.7764 | no | no | -0.006 [-0.039, +0.029] | 0.7186 | no |
| s_noer_noap | 0.871 | -0.009 [-0.031, +0.012] | 0.4132 | no | no | -0.014 [-0.041, +0.012] | 0.2938 | no |
| s_pw6 | 0.870 | -0.010 [-0.059, +0.037] | 0.6828 | no | no | -0.018 [-0.067, +0.027] | 0.4460 | no |
| s_wnode1_wrisk05 | 0.869 | -0.011 [-0.058, +0.036] | 0.6364 | no | no | -0.021 [-0.069, +0.023] | 0.3596 | no |
| s_wnode0 | 0.868 | -0.011 [-0.046, +0.024] | 0.5198 | no | no | -0.015 [-0.051, +0.022] | 0.4242 | no |
| s_focal2 | 0.868 | -0.011 [-0.045, +0.022] | 0.4838 | no | no | -0.025 [-0.063, +0.008] | 0.1366 | no |
| s_focal1_pw3 | 0.863 | -0.017 [-0.052, +0.017] | 0.3298 | no | no | -0.026 [-0.062, +0.007] | 0.1238 | no |
| s_tf | 0.861 | -0.019 [-0.065, +0.024] | 0.3898 | no | no | -0.024 [-0.070, +0.018] | 0.2748 | no |
| s_noap | 0.851 | -0.028 [-0.075, +0.007] | 0.1422 | no | no | -0.028 [-0.077, +0.011] | 0.1988 | no |
| s_gatv2 | 0.850 | -0.030 [-0.070, +0.007] | 0.1142 | no | no | -0.041 [-0.090, +0.003] | 0.0644 | no |
| s_norev | 0.848 | -0.031 [-0.090, +0.020] | 0.2426 | no | no | -0.025 [-0.085, +0.026] | 0.3662 | no |
| s_pw1 | 0.845 | -0.035 [-0.078, +0.005] | 0.0896 | no | no | -0.030 [-0.072, +0.008] | 0.1306 | no |
| s_tmem_conv5 | 0.843 | -0.037 [-0.081, +0.006] | 0.0966 | no | no | -0.025 [-0.064, +0.017] | 0.2416 | no |
| s_waux0 | 0.842 | -0.038 [-0.098, +0.015] | 0.1644 | no | no | -0.033 [-0.091, +0.017] | 0.2090 | no |
| s_tmem_gru | 0.833 | -0.047 [-0.098, -0.002] | 0.0412 | yes | no | -0.041 [-0.092, +0.003] | 0.0734 | no |
| s_gtemp_conv5 | 0.820 | -0.060 [-0.109, -0.012] | 0.0126 | yes | no | -0.053 [-0.100, -0.007] | 0.0198 | no |
| s_noauxloss | 0.819 | -0.060 [-0.124, +0.000] | 0.0508 | yes | no | -0.058 [-0.124, +0.004] | 0.0664 | no |
| s_wrisk0 | 0.807 | -0.073 [-0.136, -0.012] | 0.0170 | yes | no | -0.067 [-0.128, -0.010] | 0.0204 | no |
| s_gtemp_none | 0.793 | -0.086 [-0.148, -0.024] | 0.0098 | yes | yes | -0.084 [-0.144, -0.023] | 0.0094 | yes |

**Answer: does any difference exceed the seed noise?** Criterion: the seed-aware 95 % CI (seed variance included) excludes 0. Controls/ablations on AUROC: control shuffle_labels, control shuffle_rows, ablation S1; on tAUROC: control shuffle_labels, control shuffle_rows, ablation S2, ablation S1, ablation S0. Within seed noise on both metrics: control rewire, control shuffle_ef, ablation +clock, ablation +lex. shuffle_ef has Δ AUROC -0.041 and Δ tAUROC -0.062: past the largest observed seed difference, but inside the 95 % band. Screen variants: s_gtemp_none (on AUROC or tAUROC). Past the largest observed seed |Δ| on some metric but not seed-aware: s_gatv2, s_gtemp_conv5, s_noauxloss, s_tmem_gru, s_wrisk0. Past the 95 % band but not seed-aware: s_wrisk0. 18-fold architecture differences: none. Reading: apart from the label-destroying controls, the only changes that clear seed noise remove the temporal memory (s_gtemp_none) or the interpretive jury dimensions (S0/S1/S2, at least on tAUROC). Topology (rewire), conv type, loss weighting and the m_* regularisers cannot be told apart from seed noise with this data.

## 7. Caveats

- **night_train only:** 64 configs, 3370 rows, 135 positive rows from 45 tipped runs in 26 configs. Inference rests on few independent units. A percentile bootstrap with 64 clusters can under-cover a little, so read p-values near 0.05 as approximate. B = 10,000 gives a p floor of 1e-04 (Holm floor 0.0011).
- **Not the plan's full decision rule.** Plan §4 needs (1) a CI that excludes 0 in protocol (a), pooled OOF over **all** night configs with llm_monitor folds, and (2) sign agreement in ≥ 3 of 4 held-out splits (protocol b). This report is the harness CV on night_train with the harness folds. LODO sign counts are a within-CV proxy, not criterion (2). Test splits were not touched (GNN looks: 0).
- **Zero-shot LLM monitors read raw message text, task words included** ("skip", "quarantine", shortcut names). The headline GNN and bag+graph inputs exclude the task lexicon (ablation-only: hgb_bag+graph+lex 0.873 vs 0.843 ID AUROC in RESULTS.md; GNN +lex -0.020 here). Part of the LLM advantage may be lexical access, not better reasoning about contagion.
- **zs:global_full sees an implicit clock:** the whole transcript from round 1, so its length grows with t. Its score has the highest rank correlation with the round of all predictors (Spearman ρ = 0.83, vs 0.73 pairwise, 0.65 bag+graph, 0.30 gnn_final). Time-matched AUROC controls for the round only coarsely (5-round bins).
- **Same LLM in the monitor and in the features:** the monitor is Claude Haiku 5.5, which is also one of the two jury judges (DeepSeek V4 Flash + Claude Haiku 5.5, FEATURES.md / README) whose ratings form the GNN and bag+graph edge/node features. The monitor families are therefore not independent views, and shared model biases are possible.
- **Zero-shot = untrained.** Their LODO values are subset AUROCs, not transfer tests, and the selection score has a different meaning for them. Prompt development used 8 night_train dev runs (all variants frozen at r0, no revision, llm_monitor README); those runs are part of these rows.
- **Repeat-averaged OOF** gives every trained model a 2-model mini-ensemble (repeat 0 and repeat 1 models); the zero-shot scores do not get this. The per-repeat (rep-mean) sensitivity is shown; it does not change any Holm verdict; it favours the zero-shot monitors slightly more.
- **Training and sampling noise is not in the config-bootstrap CIs.** The seed-aware sensitivity adds single-model seed variance for the GNN (pessimistic for the 4-member ensemble) and no verdict changes. The snapshot-level HGB baselines (clock, bag+graph, +mem) are deterministic given their fixed random_state (< 10,000 training rows, so no early-stopping split; no subsampling). LLM sampling noise was measured only for global_full (single sample vs k = 3: -0.005 AUROC), not for pairwise (k = 1).
- **The clock is a weak bar time-matched:** hgb_clock has tAUROC 0.401 (< 0.5) with round bins, because within a 5-round bin the clock model's ranking runs against the outcome. With the plan's rounds-to-cut bins it reaches 0.635. All five communication monitors also beat chance (lower CI bound > 0.5) on both definitions.
- **Secondary analyses** are on id0 (5 folds, one seed). The seed noise comes from few seed pairs (4 df on id0, 2 df on 18 folds), so the noise bands are themselves uncertain. No multiplicity correction (plan §9).
- **gnn_final** = `final.csv`, the probability mean of m_noer_swa and m_tmemgru with 2 seeds each (checked: max |diff| 0.0 to the mean of the 4 member files). gnn_hybrid = the logit mean 0.5/0.5 of final and hgb_bag+graph+mem (max |diff| 0.0). RESULTS.md mentions a better node-GRU GNN (e_ngru_4runs, select 0.871); it is not the shipped model and is not tested here. The plan's `gnn_final = ____` field is still empty and should name this configuration before any held-out evaluation.
- **Plan deviations:** B = 10,000 instead of 1,000 (the task asked for ≥ 2,000). Round-bin tAUROC (harness) is the primary time matching, and the plan's rounds-to-cut bins are the sensitivity; every Holm verdict of family (a) is the same under both.

## 8. What this means for the paper

- RQ2 is supported in CV: all five communication monitors beat the clock time-matched after Holm, in all 8 LODO folds each. The zero-shot pairwise LLM has the highest point estimates of all observable monitors (ID AUROC 0.922, tAUROC 0.886). It is significantly better than bag+graph (primary, Holm) and than edge_monitor_top3 (supplementary, uncorrected p = 0.0058), but it ties with gnn_final and gnn_hybrid.
- RQ3, architecture: the GNN alone does not separate from bag+graph (Holm p = 0.377, LODO 5/8). The hybrid (GNN + GBM) does (+0.048, LODO 8/8). The global LLM monitor ties with bag+graph. Wording for the paper: "the hybrid and the pairwise LLM monitor beat the tabular graph baseline; GNN, hybrid and pairwise LLM are statistically tied".
- None of these is a final paper verdict until protocol (b) on the held-out splits has been run (plan §4, rule 2).

## 9. Files and commands

Scratch: `/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/`

- `repo/gnn_opt/` (harness copy from origin/gnn-opt), `repo/sim_dataset` → symlink; `data/night/` (rebuilt dataset); `preds/` (CV files from git + `zs_*.csv`).
- `monitors/make_zs_cv.py` (step 2), `monitors/check_repro.py` (step 1 check), `monitors/statlib.py` (bootstrap, Holm, DeLong), `monitors/primary_stats.py` (step 4), `monitors/secondary_stats.py` (step 5), `monitors/sensitivity.py`, `monitors/diagnostics.py`, `monitors/make_report.py`.
- Outputs: `monitors/step1_repro.log`, `step1_repro_table.csv`, `step3_joint.log`, `step3_joint_table.csv`, `out/primary_results.json`, `out/comparisons.csv`, `out/descriptive_table.csv`, `out/secondary_results.json`, `out/controls_ablations.csv`, `out/seed_noise.csv`, `out/architectures_18fold.csv`, `out/screen_id0.csv`, `out/sensitivity_results.json`, `out/clock_likeness.csv`, `out/rank_corr_main.csv`.

```bash
PY=/Users/mauricio/sim_local/apart/sim_dataset/.venv/bin/python; ST=/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat
cd /Users/mauricio/sim_local/apart_ana && $PY -I $ST/repo/gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out $ST/data/night
$PY -I $ST/monitors/make_zs_cv.py --data $ST/data/night --folds $ST/repo/gnn_opt/folds.json \
    --llm-root /Users/mauricio/sim_local/apart_ana/data/llm_monitor --ref-cv $ST/preds/final.csv --out-dir $ST/preds
$PY -I $ST/repo/gnn_opt/evaluate.py --data $ST/data/night --preds $ST/preds/{zs_pairwise,zs_global_full,zs_global_window,final,final+hgb_bag+graph+mem,hgb_bag+graph+mem,hgb_bag+graph,hgb_bag,edge_monitor_top3,hgb_clock,oracle_risk}.csv --pairs
COMMON="--data $ST/data/night --base /Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv --folds $ST/repo/gnn_opt/folds.json --preds $ST/preds"
$PY -I $ST/monitors/primary_stats.py $COMMON --harness $ST/repo/gnn_opt --B 10000 --out $ST/monitors/out
$PY -I $ST/monitors/secondary_stats.py $COMMON --harness $ST/repo/gnn_opt --B 10000 --out $ST/monitors/out
$PY -I $ST/monitors/sensitivity.py $COMMON --llm-root /Users/mauricio/sim_local/apart_ana/data/llm_monitor --out $ST/monitors/out
```

