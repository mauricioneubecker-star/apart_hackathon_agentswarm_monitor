import sys
sys.path.insert(0, "/Users/mauricio/sim_local/apart_ana")
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from llm_monitor.evaluate import stratified_auroc
P = pd.read_csv("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/oof/preds.csv")
B = pd.read_csv("/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv", low_memory=False)
M = P.merge(B[["episode_id", "t", "split", "tip", "rounds_to_cut", "group_id"]], on=["episode_id", "t"])
rtc = pd.cut(M.rounds_to_cut, [-99, -9, -5, -1, 3, 99]).astype(str).values
for name, mask in (("pool (train+val)", M.split.isin(["night_train", "night_val"]).values),
                   ("night_train only", (M.split == "night_train").values)):
    g = M[mask]
    s = {n: (round(roc_auc_score(g.tip, g[n]), 3), round(stratified_auroc(g.tip.values, g[n].values, rtc[mask]), 3))
         for n in ("clock", "bag+graph", "zs:pairwise", "zs:global_full")}
    print(f"{name:32s} rows {len(g)} pos {int(g.tip.sum())} cfgs {g.group_id.nunique()} | (AUROC, time-matched):", s)
