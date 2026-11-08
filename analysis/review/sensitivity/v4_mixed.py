"""(5) How the mixed-config set ('gleiches Setup') changes with theta, and what the row looks like on a fixed set."""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

SENS = sys.argv[1]
TAGS = ["t8d3", "t6d3", "t10d3", "t8d2", "t8d5"]
PRED = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise", "hgb:pairwise", "oracle"]
BINS = ([-99, -9, -5, -1, 3, 99], ["<=-9", "-8..-5", "-4..-1", "0..3", ">3"])


def strat(y, p, s):
    df = pd.DataFrame({"y": y, "p": p, "s": s}).dropna()
    num = den = 0.0
    used = set()
    for k, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            num += npos * nneg * roc_auc_score(g.y, g.p)
            den += npos * nneg
            used.add(k)
    return (num / den if den else np.nan), used, den


D = {}
for tag in TAGS:
    B = pd.read_csv(os.path.join(SENS, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    P = pd.read_csv(os.path.join(SENS, "results", tag, "oof", "preds.csv"))
    X = P.merge(B[["episode_id", "t", "tip", "group_id", "rounds_to_cut", "mixed", "tipped", "risk_count", "split"]],
                on=["episode_id", "t"], how="left")
    X["rtc"] = pd.cut(X.rounds_to_cut, *BINS[:1], labels=BINS[1]).astype(str)
    X["stratum"] = X.group_id + "|" + X.rtc
    cols = [c for c in P.columns if c not in ("episode_id", "t")]
    X["common"] = np.all([X[c].notna().values for c in cols], 0)
    mixed_cfgs = set(B.loc[B.mixed == 1, "group_id"])
    D[tag] = (B, X, mixed_cfgs)

M = {t: D[t][2] for t in TAGS}
print("mixed configs per tag:", {t: len(M[t]) for t in TAGS})
print("t8d2/t8d5 mixed set == t8d3:", M["t8d2"] == M["t8d3"], M["t8d5"] == M["t8d3"])
for a, b in (("t6d3", "t8d3"), ("t10d3", "t8d3"), ("t6d3", "t10d3")):
    i = M[a] & M[b]
    print(f"{a} vs {b}: intersection {len(i)}, only {a} {len(M[a]-M[b])}, only {b} {len(M[b]-M[a])}, "
          f"Jaccard {len(i)/len(M[a]|M[b]):.2f}")
allthree = M["t6d3"] & M["t8d3"] & M["t10d3"]
union = M["t6d3"] | M["t8d3"] | M["t10d3"]
print("in all three theta sets:", len(allthree), " union:", len(union))
print("only-in sets:\n  t6 only:", sorted(M["t6d3"] - M["t8d3"]), "\n  t8 not t6:", sorted(M["t8d3"] - M["t6d3"]),
      "\n  t10 only:", sorted(M["t10d3"] - M["t8d3"]), "\n  t8 not t10:", sorted(M["t8d3"] - M["t10d3"]))

# per-config number of tipped runs out of total, for the union
rows = []
for c in sorted(union):
    r = {"cfg": c}
    for t in ("t6d3", "t8d3", "t10d3"):
        B = D[t][0]
        e = B[B.group_id == c].groupby("episode_id").tipped.first()
        r[t] = f"{int(e.sum())}/{len(e)}"
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

# slice composition per tag
print("\nmixed-slice composition (rows_common & mixed):")
comp = {}
used_strata = {}
for t in TAGS:
    B, X, mc = D[t]
    m = X.common & (X.mixed == 1)
    a, used, den = strat(X.tip[m].values, X["zs:pairwise"][m].values, X.stratum[m].values)
    cfg_used = {s.split("|")[0] for s in used}
    used_strata[t] = used
    comp[t] = {"mixed_cfgs": len(mc), "rows": int(m.sum()), "pos": int(X.tip[m].sum()), "strata_both_classes": len(used),
               "cfgs_contributing": len(cfg_used), "pair_weight": int(den),
               "share_rows_of_all": round(m.sum() / X.common.sum(), 3)}
print(pd.DataFrame(comp).T.to_string())
for a, b in (("t6d3", "t8d3"), ("t10d3", "t8d3"), ("t8d2", "t8d3"), ("t8d5", "t8d3")):
    i = used_strata[a] & used_strata[b]
    print(f"contributing strata {a} vs {b}: shared {len(i)}, only {a} {len(used_strata[a]-used_strata[b])}, only {b} {len(used_strata[b]-used_strata[a])}")

# fixed config sets
print("\n'gleiches Setup' AUROC: reported (own mixed set) vs fixed set = theta-8 mixed set vs fixed set = configs mixed under all 3 thetas")
out = []
for t in TAGS:
    B, X, mc = D[t]
    for nm, cfgs in (("own", mc), ("fixed_t8set", M["t8d3"]), ("fixed_all3", allthree)):
        m = X.common & X.group_id.isin(cfgs)
        r = {"tag": t, "set": nm, "n_cfg": len(cfgs), "rows": int(m.sum()), "pos": int(X.tip[m].sum())}
        for p in PRED:
            a, used, _ = strat(X.tip[m].values, X[p][m].values, X.stratum[m].values)
            r[p] = round(a, 3)
        r["strata"] = len(used)
        out.append(r)
O = pd.DataFrame(out)
pd.set_option("display.width", 250)
print(O.to_string(index=False))

# bootstrap over configs of the reported mixed-slice AUROC (own set), 2000 draws. Each stratum lies inside one config,
# so a cluster draw just re-weights per-config sums (num_c = sum w_s*auc_s, den_c = sum w_s); duplicates count twice.
print("\nconfig-bootstrap (2000x) 95% CI of the reported 'gleiches Setup' AUROC:")
for t in TAGS:
    B, X, mc = D[t]
    m = (X.common & (X.mixed == 1)).values
    Z = X[m]
    per = {}
    for p in PRED:
        num, den = {}, {}
        for k, g in Z.groupby("stratum"):
            npos, nneg = int(g.tip.sum()), int((1 - g.tip).sum())
            if npos and nneg:
                c = k.split("|")[0]
                w = npos * nneg
                num[c] = num.get(c, 0) + w * roc_auc_score(g.tip, g[p])
                den[c] = den.get(c, 0) + w
        per[p] = (num, den)
    cfgs = np.array(sorted(set(Z.group_id)))
    rng = np.random.default_rng(0)
    draws = [rng.choice(cfgs, len(cfgs), replace=True) for _ in range(2000)]
    res = {}
    for p in PRED:
        num, den = per[p]
        nv = np.array([num.get(c, 0.0) for c in cfgs]); dv = np.array([den.get(c, 0.0) for c in cfgs])
        pos = {c: i for i, c in enumerate(cfgs)}
        vals = []
        for d in draws:
            ii = np.array([pos[c] for c in d])
            if dv[ii].sum() > 0:
                vals.append(nv[ii].sum() / dv[ii].sum())
        res[p] = np.array(vals)
        point = nv.sum() / dv.sum()
        res[p + "_pt"] = point
    line = ", ".join(f"{p} {res[p + '_pt']:.3f} [{np.percentile(res[p], 2.5):.3f}, {np.percentile(res[p], 97.5):.3f}]" for p in PRED)
    dd = res["zs:pairwise"] - res["bag+graph"]
    dc = res["zs:pairwise"] - res["clock"]
    print(f"  {t} ({len(cfgs)} cfgs): {line}")
    print(f"      zs:pairwise-bag+graph [{np.percentile(dd, 2.5):+.3f}, {np.percentile(dd, 97.5):+.3f}]  zs:pairwise-clock [{np.percentile(dc, 2.5):+.3f}, {np.percentile(dc, 97.5):+.3f}]")
