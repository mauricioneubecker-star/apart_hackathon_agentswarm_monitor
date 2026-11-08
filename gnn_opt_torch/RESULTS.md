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
