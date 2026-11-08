# Stored 15-state GNN vs reported 40-state GNN on the held-out rows (exploratory)

Rows 2338, positives 156, configs 36, valid draws 2000.

| predictor | AUROC | time-matched AUROC |
|---|---|---|
| gnn40 | 0.817 | 0.769 |
| gnn15 | 0.813 | 0.762 |
| hybrid40 | 0.832 | 0.818 |
| hybrid15 | 0.832 | 0.818 |

| difference (15 − 40) | AUROC [CI] | time-matched [CI] |
|---|---|---|
| gnn | -0.004 [-0.009, -0.000] | -0.007 [-0.013, -0.000] |
| hybrid | +0.000 [-0.003, +0.003] | -0.000 [-0.004, +0.004] |

Spearman 15 vs 40 on these rows: {'gnn': 0.9959891816127766, 'hybrid': 0.997621953601097}

gnn15 = the stored models/cloud_final_gnn.pt (15 states). hybrid15 = the vx hybrid, i.e. gnn15 blended with the
locally refit tab_mem; hybrid40 = the team's cloud_final.csv (40-state GNN + the team's own tab_mem), so the
hybrid row differs in both components, not only in the stored states.
