# Data requests (gnn_opt)

All requests assume the current simulator/jury/feature pipeline (pilot5-v1.5 format: `graph_edges.csv`,
`graph_nodes.csv`, `labels.json`, `messages.jsonl`, `jury_merged.jsonl` + both single-judge files). After a batch
lands: `python3 gnn_opt/predict.py --runs sim_dataset/runs_<batch> --baselines` gives the full metrics table.

## R1 (highest value): replicates of the 15 mixed-outcome configs → train (≈ 60 episodes)
- **What / why.** The monitor's training signal is tiny: 45 tipping events in `night_train` (135 positive rows).
  The hardest and most decision-relevant regime is "risk 3–7" and within-config prediction (mixed-outcome configs,
  control tip rate strictly between 0 and 1), where every model's bootstrap CI is ±0.1 AUROC. More replicates of the
  same configs add tipping *and* non-tipping trajectories under identical settings, i.e. exactly the
  within-config contrast the monitor must learn (the hidden factors cannot help there).
- **Which.** The 15 configs in `gnn_opt_data/night/schema.json: mixed_cfgs` (e.g. those of `night_train` among them
  first), **4 extra replicates each** (new `rep2..rep5`, fresh seeds). If the budget is tighter: the 8
  `night_train` mixed configs × 5 reps = 40 episodes.
- **Split.** Replicates of `night_train` configs → `night_train` (same config group, so grouped CV stays clean).
  Replicates of val/test configs → their existing split (do not move configs between splits).
- **Expected effect.** ≈ +50 % positive rows; tighter CIs in risk 3–7 / mixed strata; most benefit for the
  stage-2 tip model and for any learned GNN (currently overfits the 135 positives).

## R2: team_channels / dm_only sister configs of tipped board configs → train (≈ 40 episodes)
- **Why.** Non-board training configs have only 15 positive rows (team 9, dm 6), so `hold_nonboard` and any model
  claim about channel structure rest on ~5 tipping episodes. The upcoming val batch contains channel sisters; the
  model should see some in training.
- **Which.** Take the 10 `night_train` board configs that tipped in both replicates; clone each with
  `channels = team_channels` and `channels = dm_only` (all other factors fixed), 2 replicates each = 40 episodes.
- **Split.** `night_train` (new config ids; their own config groups).
- **Expected effect.** Calibrated risk under sparser graphs; we expect the gap between board and team/dm AUROC
  (currently 0.88 vs 0.93 OOF, but on very few team/dm positives) to become estimable.

## R3: dampener arms (enforced sanctions) as paired branch arms → night_branch-style eval (≈ 32 episodes)
- **Why.** Counterfactual specificity: the predicted risk must fall when cascades are halted. The 8 existing
  branch configs give 16 tipped-vs-untipped pairs; the divergence test is underpowered and only has
  "accelerating" interventions (fake authority, injected issue comment).
- **Which.** For 8 tipped `night_train`-like configs (not the train configs themselves, use new config ids):
  control + dampener arm branched at the round where risk_count first reaches 2, 2 replicates each.
- **Split.** new `night_branch_dampener` (evaluation only; never train).
- **Expected effect.** Direct test that score(post-branch, dampener) < score(control); currently untestable.

## R4 (OOD check, no training): GLM-5.2 backbone swarms and 6/6/6/6 mix, scale-free topology (≈ 40 episodes)
- Already planned. Keep strictly as test. Please also run both single judges on it (judge-swap robustness under
  an unseen backbone).
