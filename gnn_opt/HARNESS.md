# gnn_opt harness: interfaces

Framework-agnostic. Any model (numpy here, torch/PyG on the Mac) plugs in by **writing a predictions CSV**;
`evaluate.py` produces every table. Python deps: numpy, pandas, scikit-learn (no torch needed for the harness).

## 1. Build the snapshot dataset (one command per runs_* directory)
```bash
python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night      # ~1.5 min
python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_<new> --out gnn_opt_data/<new>      # any new batch
```
`gnn_opt_data/` is git-ignored (rebuild locally). Output files:

| file | content |
|---|---|
| `snapshots.csv` | one row per (run, round). Keys `snap` (row id), `run` (`<cfg>/<rep>`), `round` (= `t`). Offsets `n0, n_nodes` (node rows), `e0, n_edges` (edge rows). Labels `y3` (primary: tip within Δ=3, NaN after the tip), `y5`, `yrel3`, `yrel5` (θ_rel), `risk` (violator count at t: **target only, never input**). `eval` = 1 if `y3` defined and not a duplicated branch prefix. Group `cfg`; `split`; hidden factors `cat, seed, channels, model_mix, topology` and `mixed` (**only for splitting/strata, never input**); `arm, branch_round, tipped, tip_round`. |
| `graphs.npz` | `X` [N_nodes, len(ncols)] node features; `EF` [N_edges, len(ecols)] edge features; `ES`, `ED` global node-row indices (src → dst, i.e. dst read src's messages in rounds [t−2, t]); edges are contiguous per snapshot (offset `e0`) and sorted by dst; nodes contiguous per snapshot (offset `n0`). `node_snap` snapshot of each node row; `node_name` (agent id or `ext:*`); `prev` row of the same node in the previous round of the same run (−1 if none; for temporal node memory); `node_lab[:,0]` = agent has violated by t, `node_lab[:,1]` = agent violates within Δ=3 (NaN once violated and for externals); `node_ext` external sender flag; `ecols`, `ncols` column names. Raw values, NaNs kept (fill + missing flag in the model). |
| `table.csv` | tabular per-snapshot features for the baselines (same row order as `snapshots.csv`) |
| `schema.json` | which columns are allowed in the **headline** model (`headline_edge`, `headline_node`), ablation-only columns (lexicon, tool, clock), FEATURES.md stages S0–S3 restricted to allowed columns, `mixed_cfgs` |

**Input rules.** Headline model: only `schema.json: headline_edge + headline_node` (structure, generic jury dims and
derived, escalation_lex, role_external). `mech_ref, mech_ref_ema, pressure_lex, bcast_mech_ref, exposure_breadth`
(task lexicon), `tests_failed, escalated_unresolved` (tool), and the round index are ablations only. `role_lead,
role_auditor, n_deps, n_dependents` and `contradiction` (100 % NaN) are not exported. Do not use `round`/`t` or the
episode length as an input (all runs have R = 30; `round_frac` = clock).

## 2. Folds (identical in both sessions): `gnn_opt/folds.json`
Train only on `split == night_train` rows with `eval == 1`. Folds list the **test-fold configs**; train = all other
night_train configs.
- `id`: `id<r>_<k>`, 2 repeats × 5 folds, StratifiedGroupKFold by config (stratified by "config tipped at least once").
- `lodo`: leave-one-domain-out over hidden factors: `hold_K2`, `hold_K4`, `hold_seed_external`, `hold_seed_pioneer`,
  `hold_nonboard` (team_channels + dm_only), `hold_mix_duo`, `hold_mix_majority`, `hold_topo_clustered`.
- **Selection score** = mean(ID pooled AUROC, LODO mean AUROC, LODO worst AUROC). AUPRC as tie-break.
- `night_val` only at milestones; test splits only for the final report (count your looks).

## 3. Prediction files
```
CV   : run,round,score[,count],fold      one row per test-fold snapshot per fold (all 18 folds)
eval : run,round,score[,count]           model trained on all night_train rows; predict ALL snapshots of the
                                         target splits (incl. post-tip rows and branch prefixes; evaluate.py filters)
```
`score` = P(tip within Δ); `count` = optional predicted violator count (→ MAE). In Python: `harness.run_cv(S,
fit_predict)` runs all folds for any `fit_predict(train_mask, test_mask) -> scores`.

## 4. Evaluate
```bash
# CV: selection score, ID pooled, per-LODO-fold AUROC, strata, tAUROC, R@5%FPR, bootstrap differences
python3 gnn_opt/evaluate.py --data gnn_opt_data/night --preds gnn_opt/preds/cv/A.csv gnn_opt/preds/cv/B.csv --pairs
# held-out: threshold for R@5%FPR from the training-CV file of the same model; CIs = bootstrap over configs
python3 gnn_opt/evaluate.py --data gnn_opt_data/night --preds A_eval.csv B_eval.csv --thr-from A_cv.csv B_cv.csv \
    --splits night_val --pairs
# a new batch: --data gnn_opt_data/<new> --splits all ;  night_branch → also the branch-arm divergence analysis
```
Reported per model: AUROC, AUPRC (+ bootstrap CIs over configs), Brier, R@5%FPR (threshold from training CV), MAE
(if `count`), time-matched AUROC (within round bins 1–5, 6–10, …, positive-weighted), strata (risk ≤ 2, risk 3–7,
15 mixed configs, K2/K4, board vs team/dm, seed types), lead time (first alarm before the tip) and false-alarm
share of untipped runs. Controls (rewire, shuffled edge features, shuffled labels) are just additional prediction
files evaluated side by side. `--target y5|yrel3|yrel5` for the robustness labels.

## 5. Baselines
```bash
python3 gnn_opt/baselines.py --data gnn_opt_data/night            # all baselines: CV + night_val preds (~3 min)
python3 gnn_opt/baselines.py --data gnn_opt_data/night --only hgb_bag+graph --predict-splits all   # final
```
Files land in `gnn_opt/preds/{cv,eval}/<name>.csv`.
