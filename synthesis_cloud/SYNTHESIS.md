# Synthesis across all monitor analyses (cloud GNN session, 9 Nov 2026, ~00:30 UTC)

Branch `cloud-synthesis` = `night-vx-validation` (d083547d) + the outputs of the one pre-registered night_vx
evaluation (`analysis/results/vx_*`, run unchanged with `analysis/vx_preds/run_eval.sh`) + this file +
`synthesis_cloud/test_look1/` (tables of the GNN team's test look; they were never pushed because `results/` is
gitignored). Nothing else was changed; no other branch was touched.

Sources read: `gnn-opt-torch` (GNN sessions "Mac" and "cloud": `gnn_opt_torch/RESULTS.md`, LOOKS, STATUS),
`gnn-opt` (harness + two-stage per-agent model), `llm-monitor-baseline` / `night-vx-validation` (LLM monitors,
FINDINGS.md, ANALYSIS_PLAN.md v2 + Nachträge, `analysis/results/*`, `analysis/review/*`). The transcript-monitor
baseline you asked about is `origin/llm-monitor-baseline` (`llm_monitor/`, `results/llm_monitor/RESULTS.md`),
merged into `night-vx-validation`.

## 1. Short overview: what holds

| # | Finding | Strength | Basis |
|---|---|---|---|
| 1 | Communication monitors (LLM, GNN, hybrid, counted features) clearly beat structure-only and the clock in CV | **strong** (Holm p ≤ 0.0011, all LODO folds) | stats-monitors REPORT (CV, 11 tests) |
| 2 | The top group (zero-shot LLM `pairwise`, GNN+tabular hybrid, two-stage per-agent tabular model) is statistically indistinguishable | **strong as a null**: no pair differs on CV, test or vx | CV Holm 0.61; test p ≥ 0.23, Holm 1.0; vx CIs ±0.1-0.2 |
| 3 | Hybrid and zero-shot `pairwise` beat counted features (bag+graph) in CV | strong in CV (+0.048 / +0.068, Holm 0.0011); **not replicated on test** (+0.020 / +0.042, Holm 0.78) | CV vs heldout.md |
| 4 | The signal is in jury-scored message content, not in topology | robust (two GNN sessions, two bases; rewire = no loss; S0-S2 lose 0.06-0.08, beyond seed noise) | cloud 9b, Mac step 5, stats-monitors |
| 5 | GNN/hybrid best in distribution, LLM monitors more robust under shift | consistent direction in test and vx, **exploratory** (test OOD: LLM − GNN +0.097, p 0.02 uncorrected; vx: `global_full` best in every arm) | heldout.md, vx_eval |
| 6 | Injection via tool output: trained monitors near chance within time (0.54-0.56), zero-shot LLMs 0.64-0.70 | descriptive, one split (8 configs) | heldout.md |
| 7 | Contagion through communication (RQ1): association OR 2.34 [1.54, 3.57], only in K4 | association only; causal reading refuted by the reviewers | contagion.md, review |
| 8 | night_vx (pre-registered): H1-H4 not supported, H5 supported (CI includes 0); tip-rate shift only in glm (13/14 vs 6/14, Holm 0.06) | weak: replicate noise 0.06-0.25 AUROC, 14 bases | this run, `analysis/results/vx_verdicts.md` |

## 2. Results that differ between sources, and which one to keep

| Quantity | Version A | Version B | Why they differ | Keep | Validity of the kept statement |
|---|---|---|---|---|---|
| Best monitor | cloud summary: "hybrid is best" (CV 0.880) | gnn-opt two-stage 0.892; zs:pairwise 0.905 (same rows/folds) | the cloud summary ignored the other teams' models | **no monitor is best**: top three within ±0.03, no pair significant (CV, test, vx) | strong as a null; any single "best" claim is wrong |
| Hybrid − GBM | cloud CV +0.022 [+0.004, +0.043] vs hgb_bag+graph+mem | test +0.020 [−0.005, +0.045], Holm 0.78 vs bag+graph | CV used the rows the model was selected on; test is held out | **test: tie** | CV gain is optimistic (selection on same rows) |
| GNN alone − counted features | cloud CV: GNN 0.863 > GBM 0.848 | stats-monitors CV Holm 0.377 (Mac file); test +0.004, Holm 1.0 | different GNN files (proxy 0.871 vs exact 0.863 vs Mac 0.839) | **tie** | strong: GNN alone does not beat counted features |
| Monitors beat the clock within time (RQ2) | CV: all, Holm ≤ 0.0011 (both bin definitions) | test, plan's deadline bins: none after Holm (best: LLM pairwise Holm 0.09) | definition of "time-matched" (absolute round vs rounds-to-deadline vs both) and data size | **CV yes; test depends on the definition** (round bins: all p ≤ 0.0002; deadline × bin: 4/5 Holm-significant, GNN alone not) | moderate; the RQ2 verdict is a definitional choice |
| Node- vs graph-level GRU memory | cloud: node memory transfers (hold_K4 0.82 vs 0.70) | stats-monitors: no 18-fold architecture difference clears seed noise; Mac m_tmemgru ≈ m_noer_swa (0.819 vs 0.818) | cloud based it on single-seed runs and one LODO fold | **not established** | suggestive only |
| Ensembling helps the GNN | cloud 4-run 0.871, 5-seed exact 0.863 | single runs 0.80-0.85 | seed noise ±0.02 | keep: ensembles of ≥ 4 runs | moderate (CV only) |
| Stored GNN = evaluated GNN | cloud: Spearman 0.99+, max diff 0.05 (120 rows) | Nachtrag 2: Spearman 0.987-0.998, max 0.11 (7560 rows), check "nicht bestanden"; AUROC 0.813 vs 0.817 | file keeps 15 of 40 states | **Nachtrag 2** | small but real (−0.004 AUROC) |
| Test-look timing | LOOKS.md "~17:45 UTC" | git: test-look commit 17:06 UTC, weights unchanged since 16:53 | times in LOOKS were written from memory | **git** | look is valid (model frozen before it) |
| zs:pairwise AUROC | 0.890 (protocol a) | 0.922 (harness CV), 0.855 (test) | different rows: all 112 configs pooled / night_train / held-out | per comparison use identical rows (CV 0.922, test 0.855) | protocol (a) pools test configs (reviewer: not clean) |
| CV "ID AUROC" of the same file | harness: mean of per-repeat AUROCs | stats-monitors/FINDINGS: AUROC of repeat-averaged OOF | aggregation | either, label it | ±0.01 |
| Seed injection "invisible to all monitors" | cloud step 9 | heldout.md: zero-shot LLMs 0.64-0.70 | cloud looked at trained monitors only | **heldout.md** | descriptive |

## 3. night_vx validation (run now, once, as pre-registered)

`run_eval.sh` ran unchanged in a clean checkout of d083547d (00:04 UTC; Python 3.13 / pandas 3.0.5 instead of 3.12 /
3.1.1, scikit-learn 1.9.1 and scipy 1.18.1 as planned; call 2 reproduced call 1 exactly). AUROC per arm (14 bases;
topo 7):

| monitor | id rep0 | id rep1 | time | glm | enf | topo |
|---|---|---|---|---|---|---|
| clock | 0.797 | 0.543 | 0.711 | 0.866 | 0.763 | 0.799 |
| bag+graph | 0.801 | 0.722 | 0.787 | 0.709 | 0.795 | 0.762 |
| tab_mem | 0.791 | 0.731 | 0.773 | 0.750 | 0.764 | 0.800 |
| edge monitor | 0.803 | 0.589 | 0.850 | 0.763 | 0.888 | 0.711 |
| GNN (cloud_final_gnn) | 0.786 | 0.640 | 0.846 | 0.734 | 0.843 | 0.890 |
| hybrid | 0.815 | 0.756 | 0.837 | 0.750 | 0.844 | 0.873 |
| LLM pairwise (zero-shot) | 0.833 | 0.691 | 0.877 | 0.806 | 0.834 | 0.784 |
| LLM global_full (zero-shot) | **0.909** | **0.772** | **0.890** | **0.872** | **0.939** | **0.950** |
| oracle (reference) | 0.931 | 0.730 | 0.817 | 0.900 | 0.883 | 0.919 |

Verdicts (mechanical, `vx_verdicts.md`): **H1** GNN within-config separation 0.759 [0.450, 0.974] → not supported
(CI includes 0.5). **H2** clock does not break down under the time shift (CI [−0.09, 0.27]) → not supported. **H3**
(glm backbone) GNN not more stable than bag → not supported. **H4** GNN false alarms in the enforcement arm 3/9
untipped runs vs 1/8 in id rep0 → not supported; the hybrid and both LLM monitors pass H4. **H5** (topology) GNN
shift +0.104 vs bag +0.007 → supported by the rule, CI of the difference [−0.21, +0.61] includes 0.

Reading: the two replicates of the same 14 configs (id rep0 vs rep1) already differ by 0.06-0.25 AUROC. The suite
can only detect very large shifts (the plan says > 0.1). No monitor collapses in any arm. The one consistent
pattern is that the zero-shot `global_full` LLM is best in every arm, which matches the test-split OOD result
(exploratory; `global_full` also tracks elapsed time, Spearman 0.83 with the round).

## 3b. Where the GNN generalizes and where it does not

Final GNN (`cloud_final_gnn`, 5 seeds), AUROC of y3. Sources: CV LODO folds (`gnn_opt_torch/preds/cv/cloud_final_gnn_cv5.csv`,
18 folds), test splits (`synthesis_cloud/test_look1/`, `analysis/results/heldout.md`), night_vx arms (§3), judge swap
(RESULTS.md step 9 / 9c). "Holds" = within noise of the in-distribution level; cells are small (7-14 configs), so
this is indicative.

| dimension | evidence | GNN AUROC | verdict |
|---|---|---|---|
| model mix (duo / majority held out) | CV LODO | 0.911 / 0.842 | holds |
| seed type (external / pioneer held out) | CV LODO | 0.899 / 0.941 | holds |
| channels (train board only, test team / DM) | CV LODO | 0.854 | holds |
| topology (clustered held out) | CV LODO | 0.889 | holds |
| topology (scale-free) | vx topo arm (7 bases) | 0.890 vs id rep0 0.786 | holds (H5 supported, CI includes 0) |
| deadline timing shift | vx time arm | 0.846 vs 0.786 | holds |
| task category (train K2, test K4) | CV LODO | 0.822 (weakest fold; graph-level-GRU GNNs 0.70-0.76) | small drop |
| new task family (metricore) | test_ood_family | 0.794 vs test_id 0.921 | drops |
| new agent backbone (GLM) | vx glm arm | 0.734 vs 0.786 (13/14 runs tip: mostly timing) | drops |
| injection via tool output | test_ood_seed | 0.744; time-matched 0.54 | fails (near chance within time) |
| counterfactual branch arms | night_branch | tipping arm higher in 1 / 6 pairs after the branch point | fails |
| stronger enforcement | vx enf arm | 0.843, but false alarms in 3/9 untipped runs vs 1/8 | ranking holds, alarms do not (H4 not supported) |
| single jury judge | test, single-judge features | −0.04 to −0.05 (CV with judge-swap aug −0.01 to −0.02) | drops |

Interpretation: the GNN generalizes where the communication looks the same (population mix, seed type, channel,
topology, timing; topology plays no role, consistent with the rewire control). It fails where the communication itself
changes: a new task family, a different agent model (different language), triggers that never appear in messages
(tool output), or a different judge scoring the messages. The zero-shot LLM monitors lose less on exactly these
shifts (test OOD splits, every vx arm), the main argument for combining both. Caveat: id rep0 vs rep1 (same 14
configs) already differ by 0.15 for the GNN, so single-arm differences below ~0.1 are not reliable.

## 4. How far can you trust this?

Trust (holds across sources, rows and definitions): findings 1, 2, 4 of §1; "GNN alone ≈ counted features";
"no single best monitor".

Do not over-read:
- **Fine rankings among the top monitors** and any CV advantage of GNN/hybrid models: they were selected on the same
  CV rows (cloud: ~35 configs; gnn-opt: best of 23 variants), so their CV numbers are optimistic. Held-out data
  (test, vx) show ties.
- **Test splits are not blind:** each team knew its own test numbers before the joint comparison. Only night_vx is
  blind, and it is small (14 bases, replicate noise 0.06-0.25 AUROC).
- **Single-seed ablations** (seed noise ±0.02 select): only effects ≥ 0.05 (S0-S2, no temporal block) are solid.

Choices that change conclusions although they were one option among several:
1. **Definition of time-matching** (absolute round / rounds to deadline / both): decides RQ2 on the test splits.
2. **Holm family of 11 tests:** with fewer, pre-chosen tests several test-split differences (LLM pairwise − clock,
   hybrid − clock) would be significant.
3. **Alarm thresholds** (proxy CV vs exact CV, 5 % FPR per row): drive recall, lead time and the H4 false-alarm
   verdict; the GNN/hybrid thresholds come from a proxy ensemble.
4. **Label definition** θ = 8, Δ = 3 (θ/Δ sensitivity is exploratory, `sensitivity.md`).
5. **Rows/protocol:** pooled OOF over all configs (LLM protocol a) vs harness CV vs held-out give 0.89 / 0.92 /
   0.86 for the same monitor.
6. **Shared information:** Haiku is both a monitor and one of the two jury judges behind every GNN feature; the
   LLM monitors read raw task words; `global_full` sees elapsed time.
7. **Simulator design** (one task family per batch, scripted seeds): all results are about this simulator.

Bottom line: the qualitative picture (content beats structure and clock; the best learned and zero-shot monitors are
roughly equal; LLM monitors look more robust under shift) is well supported. Numerical rankings between the top
monitors, and GNN-specific architecture claims, are not.
