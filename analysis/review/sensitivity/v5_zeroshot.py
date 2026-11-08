"""(6) Zero-shot scores (prompted for theta 8 / 3 rounds) evaluated under other theta/delta."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

SENS = sys.argv[1]
PRED = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise", "hgb:pairwise", "oracle"]
BINS = ([-99, -9, -5, -1, 3, 99], ["<=-9", "-8..-5", "-4..-1", "0..3", ">3"])


def load(tag):
    B = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    P = pd.read_csv(os.path.join(SENS, "results", tag, "oof", "preds.csv"))
    X = P.merge(B[["episode_id", "t", "tip", "group_id", "rounds_to_cut", "risk_count", "tipped"]], on=["episode_id", "t"])
    X["rtc"] = pd.cut(X.rounds_to_cut, *BINS[:1], labels=BINS[1]).astype(str)
    return X


def strat(y, p, s):
    df = pd.DataFrame({"y": y, "p": p, "s": s}).dropna()
    num = den = 0.0
    for _, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            num += npos * nneg * roc_auc_score(g.y, g.p)
            den += npos * nneg
    return num / den if den else np.nan


# raw zero-shot features (global_full p_tip_3, est_violators) for the score distribution by true count
GF = pd.read_csv(os.path.join(SENS, "data", "t8d3", "global_full", "snapshots.csv"))
GW = pd.read_csv(os.path.join(SENS, "data", "t8d3", "global_window", "snapshots.csv"))
X10, X8, X6 = load("t10d3"), load("t8d3"), load("t6d3")
X10 = X10.merge(GF[["episode_id", "t", "p_tip_3", "est_violators"]], on=["episode_id", "t"], how="left")
hi = X10.risk_count.between(8, 9)
print(f"t10d3 rows {len(X10)}, of which count 8-9: {int(hi.sum())} ({hi.mean():.3f}); positives {int(X10.tip.sum())}, of which "
      f"in count 8-9 rows: {int(X10.tip[hi].sum())} ({X10.tip[hi].sum()/X10.tip.sum():.3f}); pos rate count<8 "
      f"{X10.tip[~hi].mean():.3f}, count 8-9 {X10.tip[hi].mean():.3f}")
for c in ("zs:global_full", "zs:global_window", "zs:pairwise", "p_tip_3", "est_violators"):
    print(f"  mean {c:16s}: count<8 neg {X10[c][~hi & (X10.tip == 0)].mean():.3f} pos {X10[c][~hi & (X10.tip == 1)].mean():.3f} | "
          f"count 8-9 neg {X10[c][hi & (X10.tip == 0)].mean():.3f} pos {X10[c][hi & (X10.tip == 1)].mean():.3f}")
print("  global_full p_tip_3 quantiles (10/50/90) by true count:")
for k in range(0, 10):
    m = X10.risk_count == k
    if m.sum():
        q = np.nanpercentile(X10.p_tip_3[m], [10, 50, 90])
        print(f"    count {k}: n {int(m.sum()):5d}  p_tip_3 {q.round(1)}  est_violators median {np.nanmedian(X10.est_violators[m]):.1f}")

rows = []
for nm, X, mask in (("t8d3 all", X8, np.ones(len(X8), bool)), ("t10d3 all", X10, np.ones(len(X10), bool)),
                    ("t10d3 count<8 only", X10, ~hi.values), ("t10d3 count 8-9 only", X10, hi.values),
                    ("t6d3 all", X6, np.ones(len(X6), bool)), ("t8d3 count<6 only", X8, (X8.risk_count < 6).values)):
    r = {"set": nm, "rows": int(mask.sum()), "pos": int(X.tip[mask].sum())}
    for p in PRED:
        y, s = X.tip.values[mask], X[p].values[mask]
        r[p] = round(roc_auc_score(y, s), 3) if 0 < y.sum() < len(y) else np.nan
        r[p + "|tm"] = round(strat(y, s, X.rtc.values[mask]), 3)
    rows.append(r)
R = pd.DataFrame(rows).set_index("set")
pd.set_option("display.width", 250)
print("\nAUROC (pooled):")
print(R[["rows", "pos"] + PRED].to_string())
print("\nAUROC (time-matched):")
print(R[[p + "|tm" for p in PRED]].to_string())
print("\ndiff zs:global_full - bag+graph pooled:", (R["zs:global_full"] - R["bag+graph"]).round(3).to_dict())

# delta: is p_tip_3 (3-round forecast) still the right-horizon score? compare AUROC by delta on identical rows (theta 8)
print("\nTheta 8, identical rows, label horizon 2/3/5 (zero-shot scores identical across tags):")
for tag in ("t8d2", "t8d3", "t8d5"):
    X = load(tag)
    print(f"  {tag}: pos {int(X.tip.sum())}/{len(X)}  " + "  ".join(f"{p} {roc_auc_score(X.tip, X[p]):.3f}" for p in PRED))
# sanity: are zs columns identical across tags on shared rows (they must be; zero-shot is not refit)
A = load("t8d3").set_index(["episode_id", "t"])
for tag in ("t6d3", "t10d3", "t8d2", "t8d5"):
    Bq = load(tag).set_index(["episode_id", "t"])
    j = A.index.intersection(Bq.index)
    d = max(float(np.nanmax(np.abs(A.loc[j, c].values - Bq.loc[j, c].values))) for c in ("zs:global_full", "zs:global_window", "zs:pairwise", "clock"))
    print(f"  max |zs score diff| t8d3 vs {tag} on {len(j)} shared rows: {d}")
