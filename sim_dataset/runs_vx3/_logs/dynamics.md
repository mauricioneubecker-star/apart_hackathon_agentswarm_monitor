# Dynamics report: runs_vx3

27 episodes, 14 configs, 14 tipped, 810 (episode, cycle) rows, 42 positive rows (tip_within_delta)

## 1. Shortcut baselines (AUROC for tip_within_delta; GNN must clearly beat these)

- time only (cycle t): 0.649
- time to cut (t - cut): 0.706
- config only (mean of per-factor rates): 0.314
- time to cut + config: 0.663
- current risk count (violation events, NOT a GNN input): 0.885

## 2. Diversity of the tipped episodes

- carried by 14 episodes from 10 distinct configs (branch arms share their prefix: count configs, not arms)
- tip cycle relative to the cut: median 0.0, range -5..13, distinct values 8; absolute tip cycles [(18, 3), (20, 3), (23, 2), (24, 1), (26, 2), (27, 1), (29, 1), (30, 1)]
- tip cycle relative to the manager push: median 6, range 1..21; tipped without push: 1
- cascade speed (first violation -> theta): median 6.5 cycles, range 4..15
- who started: {'organic': 8, 'instructed': 3, 'after_injection': 3}; category {'K2': 6, 'K4': 8}; seed type {'pioneer': 3, 'side_task': 3, 'none': 2, 'external': 3, 'knower': 3}
- exposure channels of later adopters: {'adopters considered': 145, 'exposed via any message edge': 95, 'exposed via direct DM/mention': 20, 'exposed via merge feed': 95}

Read: if (a) the time/config baselines are close to 1, (b) tip cycles sit at one value relative to the cut,
(c) one category/seed type/channel carries almost all positives, the GNN can learn one pattern. Then
evaluate stratified (per category, seed type, push yes/no, channel) and leave-one-level-out.
