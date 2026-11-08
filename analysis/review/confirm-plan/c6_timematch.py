"""Issue 6: the two 'time-matched AUROC' definitions on identical rows (harness night_train ID OOF of hgb_clock)."""
import io, subprocess, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, "/Users/mauricio/sim_local/apart_ana")
from llm_monitor.evaluate import stratified_auroc
R = "/Users/mauricio/sim_local/apart_ana"
def show(path):
    return pd.read_csv(io.StringIO(subprocess.run(["git", "-C", R, "show", path], capture_output=True, text=True, check=True).stdout))
def harness_tauroc(y, p, t, bins=(1, 6, 11, 16, 21, 26, 31)):
    num = den = 0.0
    for a, b in zip(bins[:-1], bins[1:]):
        m = (t >= a) & (t < b)
        if m.sum() and len(np.unique(y[m])) == 2:
            w = y[m].sum(); num += w * roc_auc_score(y[m], p[m]); den += w
    return num / den
base = pd.read_csv(f"{R}/data/llm_monitor/_base/snapshots.csv", low_memory=False)
for name in ["hgb_clock", "hgb_bag+graph", "hgb_bag+graph+mem"]:
    C = show(f"origin/gnn-opt:gnn_opt/preds/cv/{name}.csv")
    C = C[C.fold.str.startswith("id0_")]                       # ID repeat 0: each night_train row once
    M = C.merge(base, left_on=["run", "round"], right_on=["episode_id", "t"])
    M = M[M.tip.notna()]
    y, p = M.tip.values, M.score.values
    rtc = pd.cut(M.rounds_to_cut, [-99, -9, -5, -1, 3, 99]).astype(str).values
    print(f"{name}: rows {len(M)} pos {int(y.sum())} AUROC {roc_auc_score(y, p):.3f}  harness tAUROC (round bins, pos-weighted) "
          f"{harness_tauroc(y, p, M.t.values):.3f}  llm_monitor time-matched (rtc bins, pairs-weighted) {stratified_auroc(y, p, rtc):.3f}")
