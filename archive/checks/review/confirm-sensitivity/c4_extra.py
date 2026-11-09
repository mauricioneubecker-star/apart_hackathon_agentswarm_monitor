"""Extra checks: (a) what the fixed theta=8 mixed set means at theta 6/10; (b) mirror effect at theta 6;
(c) global_window on the theta=10 restricted rows; (d) time-matched bag+graph on restricted rows."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/verify/confirm-sensitivity")
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from common_cs import SENS, load, bootstrap, rtc_bin, stratified_auroc

runs = {}
for t in ("t8d3", "t6d3", "t10d3"):
    B = pd.read_csv(f"{SENS}/data/{t}/_base/snapshots.csv", low_memory=False)
    runs[t] = B.groupby("episode_id").agg(g=("group_id", "first"), tipped=("tipped", "first"), mx=("mixed", "first"))
M8 = set(runs["t8d3"][runs["t8d3"].mx == 1].g)
for t in ("t6d3", "t10d3"):
    r = runs[t][runs[t].g.isin(M8)]
    st = r.groupby("g").tipped.agg(["mean"])
    print(f"{t}: of the {len(M8)} θ=8-mixed configs -> mixed {int(((st['mean'] > 0) & (st['mean'] < 1)).sum())}, "
          f"all tipped {int((st['mean'] == 1).sum())}, none tipped {int((st['mean'] == 0).sum())}")
    D = load(t)[0]
    s = (D.group_id + "|" + rtc_bin(D.rounds_to_cut)).values
    m = D.group_id.isin(M8).values
    df = pd.DataFrame({"g": D.group_id.values[m], "s": s[m], "y": D.tip.values[m]})
    gg = df.groupby(["g", "s"]).y.agg(["sum", "size"]).reset_index()
    gg = gg[(gg["sum"] > 0) & (gg["sum"] < gg["size"])]
    cfg_state = st["mean"].to_dict()
    gg["state"] = gg.g.map(lambda c: "mixed" if 0 < cfg_state[c] < 1 else ("all" if cfg_state[c] == 1 else "none"))
    print("   contributing strata by config state:", gg.groupby("state").size().to_dict(),
          "pairs-weight share:", (gg.assign(w=gg["sum"] * (gg["size"] - gg["sum"])).groupby("state").w.sum()
                                  / (gg["sum"] * (gg["size"] - gg["sum"])).sum()).round(3).to_dict())

# (b) mirror at theta 6: theta-8 labels on count<6 rows vs theta-6 labels (row set of t6d3)
D8, D6 = load("t8d3")[0], load("t6d3")[0]
lo6 = D8.risk_count.values < 6
k6 = set(zip(D6.episode_id, D6.t))
print(f"\nθ=6 rows {len(D6)}; θ=8 rows with count<6 {lo6.sum()}; identical sets: {k6 == set(zip(D8.episode_id[lo6], D8.t[lo6]))}")
NM = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise"]
DF = [("zs:pairwise", "bag+graph"), ("zs:global_full", "bag+graph"), ("clock", "bag+graph")]
y8 = D8.tip.values
print("θ=8 labels, all vs count<6 rows; θ=6 for comparison")
for k in NM:
    print(f"  {k:18s} θ8 all {roc_auc_score(y8, D8[k]):.3f}  θ8 count<6 {roc_auc_score(y8[lo6], D8[k][lo6]):.3f}  "
          f"θ6 {roc_auc_score(D6.tip, D6[k]):.3f}")
dd, _ = bootstrap(D8[lo6].reset_index(drop=True), NM, 1000, seed=0, diffs=DF)
print("  θ8 labels on count<6 rows, 1000x: " + "; ".join(f"{k} {v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}]" for k, v in dd.items()))
dd, _ = bootstrap(D6, NM, 1000, seed=0, diffs=DF)
print("  θ6 (as in table), 1000x:          " + "; ".join(f"{k} {v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}]" for k, v in dd.items()))

# (c)/(d) theta 10 restricted: time-matched for all key predictors
D10 = load("t10d3")[0]
lo = D10.risk_count.values < 8
rb = rtc_bin(D10.rounds_to_cut).values
print("\nθ=10 time-matched AUROC, all rows vs count<8 rows (θ=8 tm in brackets)")
rb8 = rtc_bin(D8.rounds_to_cut).values
for k in NM:
    print(f"  {k:18s} {stratified_auroc(D10.tip.values, D10[k].values, rb):.3f} -> "
          f"{stratified_auroc(D10.tip.values[lo], D10[k].values[lo], rb[lo]):.3f}  "
          f"[θ8 {stratified_auroc(y8, D8[k].values, rb8):.3f}]")
# lo+ x hi- pairs (positive <8 vs negative 8-9) for completeness
hi = ~lo
for k in ["bag+graph", "zs:global_full"]:
    a = D10[k].values[lo & (D10.tip.values == 1)]
    b = D10[k].values[hi & (D10.tip.values == 0)]
    print(f"  lo+ x hi- {k}: {roc_auc_score(np.r_[np.ones(len(a)), np.zeros(len(b))], np.r_[a, b]):.3f}")
