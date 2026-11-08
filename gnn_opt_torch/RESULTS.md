# gnn_opt_torch: results (local Mac run, 2026-11-08)

Spatio-temporal GNN monitor for "the swarm tips within 3 rounds" (y3: >= 8 of 24 agents use the forbidden shortcut
within the next 3 rounds), trained on `night_train` only and scored with the shared harness (`gnn_opt/`).

## Setup
- Data: `python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night` (252 run dirs =
  112 configs x reps, 7560 snapshots). Harness training rows: night_train, eval == 1 -> 3370 rows, **135
  positives**, 64 configs / 128 runs. night_val: 680 rows, 12 positives.
- Inputs (headline): exactly `schema.json: headline_edge` (18) + `headline_node` (5), plus missing-value flags and the
  direct / broadcast / both relation type derived from the volume columns. No round / clock, no lexicon, no tool
  events, no config parameters, no risk count as input (risk and node labels are training targets only).
- Folds: `gnn_opt/folds.json` (2x5 grouped ID folds + 8 LODO folds). Selection score = mean(ID pooled AUROC, LODO mean
  AUROC, LODO worst AUROC); AUPRC breaks ties. Normalisation statistics are fit on each fold's training runs.
- Machine: Apple Silicon, 12 cores (8P + 4E), torch 2.15 / Python 3.12 (uv venv). Benchmark of one training epoch
  (102 runs, default model): CPU 1 thread 4.7 s, 4 threads 2.9 s, 12 threads 3.1 s; MPS 1.1 s (warm). The graphs
  are tiny, so training runs as 12 single-thread CPU processes, one fold per process (throughput ~12 folds per
  ~10 min at 30 epochs).

## Baselines (CV files from `gnn_opt/preds/cv`, evaluated here with `gnn_opt/evaluate.py`)
| model | select | ID AUROC | ID AUPRC | LODO mean | LODO worst | tAUROC | R@5%FPR |
|---|---|---|---|---|---|---|---|
| hgb_bag+graph (graph aggregates + GBM) | 0.834 | 0.843 | 0.197 | 0.848 | 0.811 | 0.779 | 0.378 |
| hgb_bag+graph+mem (+ lagged features) | 0.848 | 0.867 | 0.234 | 0.864 | 0.814 | 0.806 | 0.400 |
| edge_monitor_top3 (pairwise edge monitor) | 0.836 | 0.870 | 0.216 | 0.858 | 0.779 | 0.798 | 0.444 |
| edge_monitor_max | 0.831 | 0.868 | 0.211 | 0.853 | 0.771 | 0.795 | 0.407 |
| hgb_pairwise | 0.759 | 0.794 | 0.141 | 0.780 | 0.703 | 0.705 | 0.281 |
| hgb_bag (bag of edges) | 0.810 | 0.820 | 0.172 | 0.834 | 0.777 | 0.753 | 0.289 |
| lr_bag+graph | 0.814 | 0.833 | 0.212 | 0.856 | 0.753 | 0.777 | 0.370 |
| hgb_clock (clock only) | 0.727 | 0.754 | 0.077 | 0.747 | 0.681 | 0.401 | 0.074 |
| hgb_bag+graph+clock (ablation) | 0.861 | 0.875 | 0.227 | 0.876 | 0.833 | 0.797 | 0.422 |
| hgb_bag+graph+lex (ablation) | 0.850 | 0.873 | 0.222 | 0.877 | 0.801 | 0.816 | 0.430 |
| oracle_risk (reference only) | 0.926 | 0.926 | 0.425 | 0.947 | 0.906 | 0.907 | 0.615 |

The strongest headline-compliant tabular baseline is **hgb_bag+graph+mem (0.848)**; hgb_bag+graph (0.834) is the
named reference.

## Step 1: smoke test
One fold x 2 epochs trains (loss 21.4 -> 12.3), prediction file has `run,round,score,count[,fold]`. Fixes on the way:
device-aware tensors in `model.py`; the `rewire` / `shuffle_ef` controls now corrupt the prediction batch as well
(before, only training batches were corrupted, so the test graphs still carried the real structure);
`gnn_opt/judge_swap.py` added (the judge-swap augmentation referenced it but it did not exist), single-judge
`jury_disagreement` (all NaN for one judge) is replaced by the merged value in the swapped copies; true SWA
(`swa=1`: weight averaging at constant lr after a shortened one-cycle schedule) next to the existing prediction
snapshot ensemble of the last `swa_last` epochs.

## Step 2: screening on `--cv id0` (5 folds, 1 seed, 30 epochs, base = DEFAULT: rgine, reverse relations, virtual
node, graph GRU, edge readout + attention pool, w_aux 0.5 / w_node 0.5 / w_risk 0.2, pos_weight 3)
Pooled out-of-fold over the 5 folds of repeat 0 (128 runs, 135 positives).

| name | id_auroc | id_auprc | cfg (vs DEFAULT) |
|---|---|---|---|
| s_noer | 0.890 | 0.291 | epochs=30, edge_readout=False |
| s_base | 0.880 | 0.313 | epochs=30 |
| s_base_r1 | 0.879 | 0.273 | epochs=30 |
| s_novn | 0.876 | 0.255 | epochs=30, vn=False |
| s_gtemp_none_tmem_gru | 0.876 | 0.282 | epochs=30, gtemp=none, tmem=gru |
| s_gine | 0.875 | 0.263 | epochs=30, conv=gine |
| s_noer_noap | 0.871 | 0.278 | epochs=30, edge_readout=False, att_pool=False |
| s_pw6 | 0.870 | 0.281 | epochs=30, pos_weight=6.0 |
| s_wnode1_wrisk05 | 0.869 | 0.252 | epochs=30, w_node=1.0, w_risk=0.5 |
| s_wnode0 | 0.868 | 0.270 | epochs=30, w_node=0.0 |
| s_focal2 | 0.868 | 0.260 | epochs=30, pos_weight=1.0, focal_gamma=2.0 |
| s_focal1_pw3 | 0.863 | 0.257 | epochs=30, focal_gamma=1.0 |
| s_tf | 0.861 | 0.258 | epochs=30, conv=transformer |
| s_noap | 0.851 | 0.300 | epochs=30, att_pool=False |
| s_gatv2 | 0.850 | 0.259 | epochs=30, conv=gatv2 |
| s_norev | 0.848 | 0.295 | epochs=30, reverse=False |
| s_pw1 | 0.845 | 0.248 | epochs=30, pos_weight=1.0 |
| s_tmem_conv5 | 0.843 | 0.248 | epochs=30, tmem=conv5 |
| s_waux0 | 0.842 | 0.243 | epochs=30, w_aux=0.0 |
| s_base_r2 | 0.840 | 0.287 | epochs=30 |
| s_tmem_gru | 0.833 | 0.282 | epochs=30, tmem=gru |
| s_gtemp_conv5 | 0.820 | 0.238 | epochs=30, gtemp=conv5 |
| s_noauxloss | 0.819 | 0.285 | epochs=30, w_aux=0.0, w_node=0.0, w_risk=0.0 |
| s_wrisk0 | 0.807 | 0.284 | epochs=30, w_risk=0.0 |
| s_gtemp_none | 0.793 | 0.195 | epochs=30, gtemp=none |

**Seed noise is large**: the base config with three seeds gives 0.880 / 0.879 / 0.840 ID AUROC (AUPRC 0.27-0.31).
Differences below ~0.04 on id0 are not interpretable. What clearly matters:
- a temporal memory: no temporal block 0.793; a windowed causal conv (5 rounds) 0.820; a GRU over the whole history
  0.84-0.89, at graph level (default) or node level (`tmem=gru, gtemp=none` 0.876);
- the violator-count auxiliary head (Poisson, target only): w_risk = 0 -> 0.807, all aux losses off -> 0.819.
Within noise (no decision possible from id0): conv type (rgine / gine / gatv2 / transformer), reverse relations,
virtual node, edge readout, attention pool, node aux loss, y5/yrel3 aux heads, pos_weight 1/3/6 vs focal loss.
Simplest choices kept for the search: rgine + graph GRU, edge readout off (best single run, cheaper), w_risk > 0.

## Step 3: search (successive halving), cut short for time
`search.py` was rewritten so every stage runs through one process pool and stage 1 already contains the 8 LODO
folds (stage 1 = id0 + LODO, 13 folds; stage 2 adds the 5 id1 folds to the stage-1 predictions -> exact 18-fold
score; stage 3 = second seed). Reason: the full-fold result of the cloud session (`b_gine_ggru`: ID 0.885 but
hold_K4 0.696 -> select 0.804) showed that the id0 screen cannot see the domain-shift failure that dominates the
selection score.

Compute turned out to be the bottleneck: training is memory-bandwidth bound (throughput 16-17 fold-jobs/min of a
3-epoch job for 4, 8 or 12 CPU processes alike; pure-Python work scales 6.7x on the same machine; 6 workers incl. 2
on MPS: ~22 jobs/min). One config on 18 folds costs 15-25 min of the whole machine. After two random configs
(`rs1_0` 0.799, `rs1_1` 0.784 on id0+LODO) the random part was dropped and four hypothesis-driven candidates (base
architecture rgine + graph GRU, edge readout off, 30 epochs, + one LODO regulariser each) were run on all 18 folds:

| config (18 folds, seed 0) | select | ID AUROC | ID AUPRC | LODO mean | LODO worst (fold) |
|---|---|---|---|---|---|
| m_noer_swa (SWA, last 8 epochs at 0.25 lr) | 0.818 | 0.851 | 0.295 | 0.848 | 0.756 (K4) |
| m_tmemgru (node-level GRU instead of graph GRU) | 0.819 | 0.834 | 0.238 | 0.835 | 0.788 (mix_majority) |
| m_noer_crop10 (random start-crop <= 10 rounds) | 0.803 | 0.859 | 0.250 | 0.831 | 0.720 (K4) |
| m_noer (base) | 0.799 | 0.858 | 0.295 | 0.833 | 0.704 (nonboard) |
| b_gine_ggru (cloud session, same harness) | 0.804 | 0.885 | 0.282 | 0.830 | 0.696 (K4) |
| m_noer_swa, seed 2 | 0.816 | 0.869 | 0.276 | 0.848 | 0.731 |
| m_tmemgru, seed 2 | 0.825 | 0.853 | 0.239 | 0.844 | 0.777 |

Not searched (time): lr / wd / hid / layers / dropout / epochs / batch size beyond the two random configs.

## Step 4: final GNN = 2 configs x 2 seeds, vs baselines (18-fold CV on night_train)
Final GNN (`final`) = probability mean of m_noer_swa and m_tmemgru, each with 2 seeds (4 members per fold; the
tmemgru members are themselves snapshot ensembles of their last 8 epochs). Only 2 seeds per config instead of >= 3,
and no judge-swap / edge-drop / feature-noise variants beyond the defaults (edge_drop 0.1, feat_noise 0.05):
time. Blend = logit mean of `final` and hgb_bag+graph+mem with equal weights (0.5 / 0.5; 0.3-0.5 give 0.871-0.875,
the weight was not tuned further).

`python3 gnn_opt/evaluate.py --data gnn_opt_data/night --preds <files> --pairs` (full table:
`preds/cv_table_final.csv`):

| model | select | ID AUROC | ID AUPRC | LODO mean | LODO worst | tAUROC | R@5%FPR | risk<=2 | risk 3-7 | 15 mixed cfgs | MAE count |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **blend: final GNN + hgb_bag+graph+mem** | **0.875** | **0.898** | 0.275 | **0.895** | **0.831** | 0.850 | 0.556 | 0.755 | 0.780 | **0.886** | 0.72 |
| final GNN (2 cfg x 2 seeds) | 0.839 | 0.880 | 0.280 | 0.870 | 0.766 | 0.847 | **0.570** | 0.731 | 0.766 | 0.882 | 0.72 |
| m_noer_swa (1 seed) | 0.818 | 0.851 | **0.295** | 0.848 | 0.756 | 0.839 | 0.570 | 0.712 | **0.794** | 0.808 | 0.81 |
| m_tmemgru (1 seed) | 0.819 | 0.834 | 0.238 | 0.835 | 0.788 | 0.817 | 0.541 | 0.723 | 0.763 | 0.800 | 0.70 |
| hgb_bag+graph+mem | 0.848 | 0.867 | 0.234 | 0.864 | 0.814 | 0.806 | 0.400 | 0.707 | 0.727 | 0.839 | - |
| hgb_bag+graph | 0.834 | 0.843 | 0.197 | 0.848 | 0.811 | 0.779 | 0.378 | 0.699 | 0.735 | 0.812 | - |
| edge_monitor_top3 | 0.836 | 0.870 | 0.216 | 0.858 | 0.779 | 0.798 | 0.444 | **0.828** | 0.736 | 0.823 | - |
| hgb_bag | 0.810 | 0.820 | 0.172 | 0.834 | 0.777 | 0.753 | 0.289 | 0.700 | 0.688 | 0.777 | - |
| hgb_clock | 0.727 | 0.754 | 0.077 | 0.747 | 0.681 | 0.401 | 0.074 | 0.676 | 0.681 | 0.695 | - |
| oracle_risk (reference) | 0.926 | 0.926 | 0.425 | 0.947 | 0.906 | 0.907 | 0.615 | 0.742 | 0.650 | 0.931 | - |

Strata = AUROC within the stratum of the repeat-averaged ID out-of-fold predictions (evaluate.py); MAE count = mean
absolute error of the Poisson violator-count head (secondary target). Full table: `preds/cv_table_final.csv`.

LODO per fold (AUROC):

| model | K2 | K4 | mix_duo | mix_majority | nonboard | seed_external | seed_pioneer | topo_clustered |
|---|---|---|---|---|---|---|---|---|
| blend | 0.938 | 0.831 | 0.890 | 0.881 | 0.888 | 0.932 | 0.929 | 0.873 |
| final GNN | 0.915 | 0.766 | 0.893 | 0.820 | 0.839 | 0.924 | 0.951 | 0.852 |
| hgb_bag+graph+mem | 0.906 | 0.814 | 0.829 | 0.876 | 0.903 | 0.878 | 0.855 | 0.851 |
| hgb_bag+graph | 0.889 | 0.811 | 0.839 | 0.870 | 0.853 | 0.867 | 0.819 | 0.837 |

Bootstrap over configs (1000 resamples, ID pooled AUROC; median [2.5 %, 97.5 %], share of resamples > 0):
- blend: 0.903 [0.867, 0.934]; final GNN 0.892 [0.837, 0.936]; hgb_bag+graph+mem 0.876 [0.836, 0.912];
  hgb_bag+graph 0.855 [0.804, 0.899].
- blend - hgb_bag+graph+mem **+0.026 [+0.006, +0.049]** (99.6 %); blend - hgb_bag+graph +0.047 [+0.025, +0.076];
  blend - final GNN +0.011 [-0.011, +0.038] (84 %).
- final GNN - hgb_bag+graph +0.035 [-0.003, +0.083] (96 %); final GNN - hgb_bag+graph+mem +0.014 [-0.031, +0.060]
  (74 %); final GNN - edge_monitor_top3 +0.013 [-0.041, +0.067].
- risk 3-7 stratum: blend 0.780 [0.677, 0.861] vs hgb_bag+graph+mem 0.726 [0.620, 0.809], difference +0.053
  [+0.003, +0.104]; mixed configs: blend 0.895 vs 0.841, difference +0.048 [-0.020, +0.127].

Lead time (ID out-of-fold, threshold at 5 % FPR from the same CV file; `preds/oof_heldout_table.csv`):

| model | tipped runs alarmed before the tip | median lead (rounds) | untipped runs with >= 1 false alarm |
|---|---|---|---|
| blend | 75.6 % | 4 | 25.3 % |
| final GNN | 68.9 % | 4 | 28.9 % |
| hgb_bag+graph+mem | 68.9 % | 4 | 37.3 % |
| hgb_bag+graph | 71.1 % | 4 | 41.0 % |
| edge_monitor_top3 | 82.2 % | 4 | 27.7 % |

**Honest verdict.** On the harness selection score the GNN alone (0.839) beats hgb_bag+graph (0.834) by only
0.005 and does **not** beat hgb_bag+graph+mem (0.848; -0.009). It is clearly better where the GBM is weak: within
time bins (tAUROC 0.847 vs 0.806), recall at 5 % FPR (0.57 vs 0.40), the risk 3-7 band (0.766 vs 0.727), the mixed
configs (0.882 vs 0.839) and the seed / mix LODO folds. It is worse on hold_K4 (train on K2 only, 0.766 vs 0.814) and hold_nonboard (0.839 vs 0.903). The two are
complementary: the **blend beats both** (select 0.875, +0.027 over the best GBM, +0.036 over the GNN; ID AUROC
+0.026 [+0.006, +0.049] over hgb_bag+graph+mem; best LODO worst of all models, 0.831). The cloud session found the
same with its GINE model (rank blend 0.3/0.7: 0.866).

## Step 5: controls and ablations (ID repeat 0, 5 folds, seed-matched to m_noer)
| variant | ID AUROC [95 % CI over configs] | ID AUPRC | tAUROC | risk 3-7 |
|---|---|---|---|---|
| base m_noer (headline inputs = S3) | 0.871 [0.816, 0.921] | 0.293 | 0.830 | 0.792 |
| + clock (round/30 as node feature) | 0.851 [0.786, 0.906] | 0.322 | 0.803 | 0.793 |
| + lexicon (mech_ref, mech_ref_ema, pressure_lex, bcast_mech_ref, exposure_breadth) | 0.851 [0.791, 0.907] | 0.285 | 0.823 | 0.710 |
| S2 (no interpretive jury dims) | 0.814 [0.744, 0.877] | 0.157 | 0.728 | 0.716 |
| S1 (structure + escalation_lex) | 0.790 [0.703, 0.873] | 0.196 | 0.703 | 0.545 |
| S0 (structure only) | 0.804 [0.709, 0.888] | 0.220 | 0.715 | 0.721 |
| control rewire (random endpoints within each snapshot, train + test) | 0.867 [0.809, 0.918] | 0.269 | 0.820 | 0.776 |
| control shuffle_ef (edge-feature rows permuted, train + test) | 0.830 [0.742, 0.900] | 0.235 | 0.769 | 0.719 |
| control shuffle_labels (each run gets another run's label sequence) | 0.737 [0.673, 0.798] | 0.093 | 0.587 | 0.581 |
| control shuffle_rows (labels permuted across snapshots of the batch) | 0.421 [0.309, 0.531] | 0.035 | 0.431 | 0.568 |

- **shuffle_labels does not fall to chance (0.737), and that is expected, not leakage**: permuting whole label
  sequences across runs keeps the label-vs-round prior (tips cluster late), and a model with temporal memory learns
  that clock (clock-only GBM: 0.754). Within round bins it is close to chance (tAUROC 0.587). The strict
  `shuffle_rows` control (new) removes the time prior as well and is at chance: AUROC 0.42, CI [0.31, 0.53]
  contains 0.5, AUPRC 0.035 = prevalence 0.040.
- **rewire barely hurts (0.867 vs 0.871)**: the monitor gets almost nothing from *who* talks to whom beyond what the
  edge / node features and their counts carry. shuffle_edge-features costs 0.04 (tAUROC -0.06): the content of
  the edges matters, the topology does not (at this data size).
- **Clock and lexicon do not help** (both -0.02, inside the noise); the GNN is not missing the round index or the
  task lexicon. The headline model is therefore not a disguised clock: tAUROC 0.83 vs 0.40 for clock-only.
- **Feature stages:** the jury dimensions carry the signal: S0-S2 lose 0.06-0.08 ID AUROC and 0.10-0.13 tAUROC.

## Step 6: blend
See step 4: logit blend final GNN + hgb_bag+graph+mem (0.5 / 0.5) **beats both** in CV (0.875 vs 0.839 / 0.848).
The logit and rank blends give the same score (0.866 for the cloud GINE + GBM 0.3/0.7 both ways); logit is used
because it also works on single held-out files.

## Step 7: final model, night_val (looked at once), predict.py
- `finalize.py --only train`: both member configs x 2 seeds trained on all 128 night_train runs ->
  `models/final.pt` (members, states, training normalisation, blend name + weight; 30 MB) and
  `preds/eval/final.csv` (every snapshot); `preds/eval/final+hgb_bag+graph+mem.csv` (night_val rows).
- **night_val, the only look** (680 rows, **12 positives**, 6 configs):

| model | AUROC [95 % CI] | AUPRC | tAUROC | R@5%FPR (thr from CV) | FPR at thr |
|---|---|---|---|---|---|
| blend | 0.874 [0.812, 0.975] | 0.206 | 0.794 | **0.500** | 0.061 |
| final GNN | 0.818 [0.672, 0.932] | **0.236** | 0.705 | 0.417 | 0.073 |
| hgb_bag+graph+mem | **0.916** [0.871, 0.964] | 0.144 | 0.880 | 0.417 | 0.060 |
| hgb_bag+graph | 0.902 [0.824, 0.959] | 0.098 | 0.839 | 0.417 | 0.055 |

  Differences (bootstrap over configs): blend - GNN +0.053 [+0.018, +0.160]; blend - hgb_bag+graph+mem -0.037
  [-0.111, +0.022]; blend - hgb_bag+graph -0.023 [-0.076, +0.047]. On val the GBM ranks best by AUROC, the GNN /
  blend by AUPRC and recall at the CV threshold; with 12 positive rows (from very few tipped runs) none of the AUROC
  differences between the blend and the GBMs is significant. Val was not used for any choice.
- `predict.py` (one command, any runs_* dir): build_dataset -> GNN ensemble -> GBM refit on night_train
  (`baselines.py --apply`) -> logit blend -> evaluate.py:
  `python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_<new> [--splits all]`. Tested on a symlinked 2-config
  night_train directory (in-sample, pipeline check only); reloaded-model scores equal the training-time scores
  (max |diff| 5e-8).

## Step 8: LLM monitor baseline: skipped
`sim_dataset/secrets.json` does not exist on this machine, so the optional Haiku zero-shot baseline was not run
(another local session works on LLM communication-monitor baselines).

## Bookkeeping
- night_val looks: **1** (step 7). Test splits (night_test_*, night_branch): **0** looks.
- evaluate.py: no bug found, no change. Harness addition: `gnn_opt/judge_swap.py` (new file, separate commit).
- Mac logs: `preds/screen_log.jsonl` (step 2), `preds/search_log.jsonl` (rs1), `preds/mac_log.jsonl` (steps 3-5).
- Another (cloud) session worked on the same branch at the same time (a_/b_/c_/h_ files, `STATUS.md`, its own
  `DATA_REQUESTS.md`, which this session agrees with: the weak cells here are hold_K4 and hold_nonboard, i.e.
  K2->K4 transfer of late tipping and non-board channels with 15 positive rows).

## Limitations
- 135 positive rows from ~45 tipped runs: seed noise on id0 is +/- 0.02-0.04 AUROC; most architecture differences
  in the screen are not resolvable. LODO worst is a single fold with as few as 15 positives (nonboard).
- Search was shortened (2 random configs + 4 targeted ones); 2 seeds per member instead of >= 3; judge-swap
  augmentation was implemented (single-judge caches for both judges) but not evaluated here; controls and
  ablations on 5 folds (id0) only.
- The GNN's gain is from temporal memory over jury edge/node features, not from graph topology (rewire control).
- night_val is tiny and disagrees with the CV ranking on AUROC; the CV conclusion (blend > both) should be checked
  on the test splits.
