"""Issue 1: theta=10 rows with risk_count 8-9 and what they do to the global LLM monitors."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/verify/confirm-sensitivity")
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from common_cs import SENS, load, bootstrap, stratified_auroc, rtc_bin

D10, names, R10 = load("t10d3")
D8, _, R8 = load("t8d3")
y = D10.tip.values
hi = D10.risk_count.between(8, 9).values
lo = D10.risk_count.values < 8
print(f"t10d3 rows {len(D10)}; count 8-9: {hi.sum()} ({hi.mean():.3%}); positives {int(y.sum())}, in 8-9: "
      f"{int(y[hi].sum())} ({y[hi].sum() / y.sum():.1%}); pos rate 8-9 {y[hi].mean():.3f}, <8 {y[lo].mean():.3f}")
print("count>=10 rows in t10d3:", int((D10.risk_count >= 10).sum()))

# same row set as theta 8?
k10 = set(zip(D10.episode_id[lo], D10.t[lo]))
k8 = set(zip(D8.episode_id, D8.t))
print(f"count<8 rows at t10: {len(k10)}; t8d3 rows_common: {len(k8)}; identical: {k10 == k8}")
L = D10[lo].merge(D8[["episode_id", "t", "tip"]].rename(columns={"tip": "tip8"}), on=["episode_id", "t"])
print("label flips on shared rows (tip8 -> tip10):", pd.crosstab(L.tip8, L.tip).to_dict())

# raw p_tip_3 + est_violators by true count (global_full)
G = pd.read_csv(f"{SENS}/data/t10d3/global_full/snapshots.csv")
Dm = D10.merge(G[["episode_id", "t", "p_tip_3", "est_violators", "p_tip_end"]], on=["episode_id", "t"], how="left")
tab = Dm.groupby("risk_count").agg(n=("tip", "size"), pos=("tip", "sum"), med_p_tip_3=("p_tip_3", "median"),
                                    mean_p_tip_3=("p_tip_3", "mean"), med_est=("est_violators", "median"),
                                    med_bag=("bag+graph", "median"), med_pair=("zs:pairwise", "median"))
print(tab.round(3).to_string())
print("share of 8-9 rows with est_violators >= 8:", float((Dm.est_violators[hi] >= 8).mean()))

KEYS = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise", "hgb:pairwise", "oracle"]
rb = rtc_bin(D10.rounds_to_cut).values
print("\nAUROC by row set (theta 10 labels)")
print(f"  {'pred':18s} {'all':>7s} {'<8':>7s} {'8-9':>7s} {'tm all':>7s} {'tm <8':>7s} {'t8d3 all':>8s}")
for k in KEYS:
    a = roc_auc_score(y, D10[k])
    b = roc_auc_score(y[lo], D10[k][lo])
    c = roc_auc_score(y[hi], D10[k][hi])
    tma = stratified_auroc(y, D10[k].values, rb)
    tml = stratified_auroc(y[lo], D10[k].values[lo], rb[lo])
    a8 = roc_auc_score(D8.tip, D8[k])
    print(f"  {k:18s} {a:7.3f} {b:7.3f} {c:7.3f} {tma:7.3f} {tml:7.3f} {a8:8.3f}")

# between-stratum part: how often a positive 8-9 row outranks a negative <8 row, per predictor
print("\nP(score of positive 8-9 row > score of negative <8 row) [cross-pairs]:")
for k in ["bag+graph", "zs:global_full", "zs:pairwise", "clock"]:
    p_pos_hi = D10[k].values[hi & (y == 1)]
    p_neg_lo = D10[k].values[lo & (y == 0)]
    sub = np.concatenate([p_pos_hi, p_neg_lo])
    lab = np.concatenate([np.ones(len(p_pos_hi)), np.zeros(len(p_neg_lo))])
    print(f"  {k:18s} {roc_auc_score(lab, sub):.3f}  (n_pos {len(p_pos_hi)}, n_neg {len(p_neg_lo)})")
# share of pos x neg pairs that involve an 8-9 row
npos_hi, npos_lo = int(y[hi].sum()), int(y[lo].sum())
nneg_hi, nneg_lo = int((1 - y[hi]).sum()), int((1 - y[lo]).sum())
tot = (npos_hi + npos_lo) * (nneg_hi + nneg_lo)
print(f"pair shares: lo-lo {npos_lo * nneg_lo / tot:.3f}, hi+ x lo- {npos_hi * nneg_lo / tot:.3f}, "
      f"lo+ x hi- {npos_lo * nneg_hi / tot:.3f}, hi-hi {npos_hi * nneg_hi / tot:.3f}")

# paired bootstrap on the restricted rows (1000x, seed 0, cluster = config), as the reviewer did
DIFFS = [("zs:pairwise", "bag+graph"), ("zs:global_full", "bag+graph"), ("clock", "bag+graph"),
         ("zs:global_window", "bag+graph")]
NM = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise"]
for lab, mask in (("all t10d3", np.ones(len(D10), bool)), ("t10d3 count<8", lo)):
    for nb in (1000, 2000):
        dd, _ = bootstrap(D10[mask].reset_index(drop=True), NM, nb, seed=0, diffs=DIFFS)
        print(f"\n{lab}, {nb}x seed 0:")
        for k, v in dd.items():
            print(f"  {k:30s} {v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}] p<=0 {v[3]:.3f}")
