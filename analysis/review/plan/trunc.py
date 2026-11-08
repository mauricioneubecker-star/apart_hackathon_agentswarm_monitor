import pandas as pd, numpy as np
B = pd.read_csv("/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv", low_memory=False)
y = B[B.tip.notna()]
for off in (0, 1, 2):
    g = y[y.t == y.R - off]
    print(f"t = R-{off}: target rows {len(g)}, positives {int(g.tip.sum())}")
print("all target rows", len(y), "pos", int(y.tip.sum()), "R values", sorted(B.R.unique()))
# share of target rows with t > R - 3 among negatives
neg = y[y.tip == 0]
print("negatives with t >= R-2:", int((neg.t >= neg.R - 2).sum()), "of", len(neg))
