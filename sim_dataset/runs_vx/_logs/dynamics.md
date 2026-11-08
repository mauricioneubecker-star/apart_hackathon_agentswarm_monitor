# Dynamics report: runs_vx

94 episodes, 72 configs, 51 tipped, 2904 (episode, cycle) rows, 153 positive rows (tip_within_delta)

## 1. Shortcut baselines (AUROC for tip_within_delta; GNN must clearly beat these)

- time only (cycle t): 0.750
- time to cut (t - cut): 0.758
- config only (mean of per-factor rates): 0.525
- time to cut + config: 0.762
- current risk count (violation events, NOT a GNN input): 0.887

## 2. Diversity of the tipped episodes

- carried by 51 episodes from 43 distinct configs (branch arms share their prefix: count configs, not arms)
- tip cycle relative to the cut: median 0, range -10..7, distinct values 15; absolute tip cycles [(14, 1), (15, 2), (17, 3), (18, 3), (19, 9), (20, 2), (21, 2), (22, 4), (23, 5), (24, 6), (25, 1), (26, 2), (27, 2), (28, 2), (29, 3), (30, 3), (31, 1)]
- tip cycle relative to the manager push: median 6, range -6..15; tipped without push: 6
- cascade speed (first violation -> theta): median 8 cycles, range 0..19
- who started: {'organic': 25, 'instructed': 12, 'after_injection': 14}; category {'K2': 21, 'K4': 30}; seed type {'pioneer': 8, 'side_task': 11, 'none': 8, 'external': 14, 'knower': 10}
- exposure channels of later adopters: {'adopters considered': 518, 'exposed via any message edge': 323, 'exposed via direct DM/mention': 87, 'exposed via merge feed': 309}

Read: if (a) the time/config baselines are close to 1, (b) tip cycles sit at one value relative to the cut,
(c) one category/seed type/channel carries almost all positives, the GNN can learn one pattern. Then
evaluate stratified (per category, seed type, push yes/no, channel) and leave-one-level-out.
