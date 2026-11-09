import json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
P = pd.read_csv("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/oof/preds.csv")
B = pd.read_csv("/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv", low_memory=False)
M = P.merge(B[["episode_id", "t", "split", "tip"]], on=["episode_id", "t"])
F = json.load(open("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/frozen/results.json"))
print("rows in (a) preds:", len(M))
for s in ("night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"):
    g = M[M.split == s]
    out = []
    for n in ("clock", "bag+graph", "zs:pairwise", "zs:global_full"):
        ok = g[n].notna()
        a = roc_auc_score(g.tip[ok], g[n][ok])
        b = F["splits"][s]["metrics"][n]["auroc"]
        out.append(f"{n}: (a)-rows {a:.3f} vs (b) {b:.3f}")
    print(s, " | ".join(out))
pool = M[M.split.isin(["night_train", "night_val"])]
print("pool rows", len(pool), "pos", int(pool.tip.sum()), "| held-out rows", int((~M.split.isin(['night_train','night_val'])).sum()),
      "pos", int(M[~M.split.isin(['night_train','night_val'])].tip.sum()))
