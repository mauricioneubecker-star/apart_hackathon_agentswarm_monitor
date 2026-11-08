# Dynamics report: runs_night

239 episodes, 112 configs, 92 tipped, 7170 (episode, cycle) rows, 276 positive rows (tip_within_delta)

## 1. Shortcut baselines (AUROC for tip_within_delta; GNN must clearly beat these)

- time only (cycle t): 0.772
- time to cut (t - cut): 0.731
- config only (mean of per-factor rates): 0.661
- time to cut + config: 0.744
- current risk count (violation events, NOT a GNN input): 0.909

## 2. Diversity of the tipped episodes

- carried by 92 episodes from 52 distinct configs (branch arms share their prefix: count configs, not arms)
- tip cycle relative to the cut: median -1.0, range -14..8, distinct values 22; absolute tip cycles [(9, 1), (11, 1), (13, 1), (14, 5), (15, 2), (16, 5), (17, 6), (18, 5), (19, 11), (20, 11), (21, 11), (22, 9), (23, 7), (24, 3), (25, 4), (26, 1), (27, 5), (28, 2), (29, 2)]
- tip cycle relative to the manager push: median 6.0, range -8..13; tipped without push: 26
- cascade speed (first violation -> theta): median 7.0 cycles, range 0..19
- who started: {'after_injection': 33, 'organic': 42, 'instructed': 17}; category {'K2': 28, 'K4': 64}; seed type {'none': 19, 'knower': 12, 'side_task': 17, 'external': 25, 'pioneer': 19}
- exposure channels of later adopters: {'adopters considered': 984, 'exposed via any message edge': 658, 'exposed via direct DM/mention': 190, 'exposed via merge feed': 753}

Read: if (a) the time/config baselines are close to 1, (b) tip cycles sit at one value relative to the cut,
(c) one category/seed type/channel carries almost all positives, the GNN can learn one pattern. Then
evaluate stratified (per category, seed type, push yes/no, channel) and leave-one-level-out.
