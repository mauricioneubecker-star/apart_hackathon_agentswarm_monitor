"""Paired config-bootstrap AUROC differences vs the clock, from committed OOF preds (read-only)."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

A = "/Users/mauricio/sim_local/apart_ana"
p = pd.read_csv(f"{A}/results/llm_monitor/oof/preds.csv")
b = pd.read_csv(f"{A}/data/llm_monitor/_base/snapshots.csv")
b = b[b.tip.notna()]
d = p.merge(b[["episode_id", "t", "group_id", "tip", "rounds_to_cut", "mixed", "risk_count"]], on=["episode_id", "t"],
            how="inner")
print("rows", len(d), "pos", int(d.tip.sum()), "configs", d.group_id.nunique())
cols = [c for c in p.columns if c not in ("episode_id", "t")]
common = d.dropna(subset=cols)
print("common rows", len(common))
y = common.tip.values.astype(int)
print("\nAUROC on common rows (to match RESULTS.md names):")
for c in cols:
    print("  %-40s %.3f" % (c, roc_auc_score(y, common[c].values)))

rng = np.random.default_rng(0)
groups = common.group_id.values
ug = np.unique(groups)
idx_by_g = {g: np.where(groups == g)[0] for g in ug}
B = 1000
draws = []
for _ in range(B):
    gs = rng.choice(ug, size=len(ug), replace=True)
    draws.append(np.concatenate([idx_by_g[g] for g in gs]))
targets = ["pairwise", "edge_monitor", "bag", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise",
           "zs:agent", "zs:global_sequential", "zs:global_full_informed", "lr:global_sequential"]
print("\nPaired bootstrap (1000x over configs) AUROC(monitor) - AUROC(clock):")
for c in targets:
    diffs = []
    for ix in draws:
        yy = y[ix]
        if yy.min() == yy.max():
            continue
        diffs.append(roc_auc_score(yy, common[c].values[ix]) - roc_auc_score(yy, common["clock"].values[ix]))
    diffs = np.array(diffs)
    point = roc_auc_score(y, common[c].values) - roc_auc_score(y, common["clock"].values)
    print("  %-25s %+.3f  CI [%+.3f, %+.3f]  P(<=0)=%.3f" % (c, point, *np.percentile(diffs, [2.5, 97.5]),
                                                        (diffs <= 0).mean()))
