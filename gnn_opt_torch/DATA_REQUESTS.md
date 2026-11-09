# Data requests (GNN monitor, from the cloud session)

Budget asked for: **~150 episodes**, all with the night-batch recipe (R = 30, jury complete, labels + features).
Why: the training set has only 135 positive snapshot rows (45 tipped runs of 128). The weak spots of every
monitor (GNN and GBM) are exactly the cells with almost no tipped runs, and the CV is dominated by seed noise (base
GNN 0.84-0.88 ID AUROC over 3 seeds on the same folds).

Evidence (night_train, 64 configs x 2 reps):
- **Non-board channels:** K2 x team_channels / dm_only = 0 / 28 tipped runs; K4 x team_channels / dm_only = 5 / 24.
  hold_nonboard has 15 positive rows in total. The upcoming team/dm sister configs will be evaluated on exactly this
  cell.
- **Critical band:** only 7 / 64 configs have mixed outcomes (1 of 2 reps tipped). The risk 3-7 stratum and the
  mixed configs are where all monitors drop most (GNN 0.79, GBM 0.73 AUROC in the risk 3-7 stratum).
- **Late tipping and K2 -> K4 transfer:** the GNN trained on K2 only (LODO hold_K4) works in rounds 8-20 (0.79-0.82
  within-bin AUROC) and breaks after round 20 (0.61). Tips cluster at the cut (mean tip round 20.6, max 29).

| # | what | configs / factor levels | reps | episodes | split | why |
|---|---|---|---|---|---|---|
| 1 | critical-band replicates | the 7 mixed night_train configs (K2-012, K2-023, K2-039, K4-000, K4-020, K4-040, K4-052) + 9 configs with the recipe (freeze + push + no sanction) that never tipped | +3 | 48 | night_train | within-config contrast (same config, different outcome) is the only signal that is not a config fingerprint; densifies risk 3-7 |
| 2 | non-board positives | 16 new configs with channels = team_channels (8) / dm_only (8), K2 / K4 balanced, recipe on, seed types pioneer / knower / external | 2 | 32 | night_train | the nonboard cell has 5 tipped runs; the team/dm sister configs and dm-heavy shifts need direct-edge contagion examples |
| 3 | cut / onset spread | 16 configs: K4 with cut 17 / 20, K2 with cut 26, push offsets 4 / 8; recipe on | 2 | 32 | night_train | decouples K2 vs K4 from tip timing (the hold_K4 failure is late-round) |
| 4 | branch arms on training configs | 10 night_train configs (seed none / knower), control + inject + fake_authority arms | 1 x 3 | 30 | night_train (arms grouped with their config) | paired counterfactuals: same history up to the branch point, different outcome; directly trains "who is about to adopt" |
| 5 | small validation reserve | 4 of the 16 configs of #2 + 4 of #3, held out | 1 | 8 | night_val | milestone check of the new cells without touching test |

Total 150. Priority if the budget is smaller: #1 (48) > #2 (32) > #4 (30) > #3 (32).
Not requested: more test data (the planned critical-band / sister / dampener / mix 6/6/6/6 / scale-free / GLM
batches already cover the evaluation shifts).
