"""Issue 2: mixed-config set per theta/delta, fixed-set recomputation, cluster-bootstrap CIs for the slice."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/verify/confirm-sensitivity")
import numpy as np
import pandas as pd
from common_cs import TAGS, SENS, load, stratified_auroc, rtc_bin

KEYS = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise", "hgb:pairwise", "oracle"]
DATA = {t: load(t) for t in TAGS}
mixed = {}
for t in TAGS:
    B = pd.read_csv(f"{SENS}/data/{t}/_base/snapshots.csv", low_memory=False)
    # recompute "mixed" from scratch from tipped per run (as sens.py does) and compare with the stored column
    night = B.split.str.startswith("night_") & ~B.split.str.startswith("night_vx")
    run = B.groupby("episode_id").agg(g=("group_id", "first"), tipped=("tipped", "first"), mx=("mixed", "first"))
    m2 = run.groupby("g").tipped.nunique() > 1
    stored = set(run[run.mx == 1].g)
    assert stored == set(m2[m2].index)
    mixed[t] = stored
    print(f"{t}: mixed configs {len(stored)}; tipped runs {int(run.tipped.sum())}/{len(run)}")

M8, M6, M10 = mixed["t8d3"], mixed["t6d3"], mixed["t10d3"]
jac = lambda a, b: len(a & b) / len(a | b)  # noqa
print(f"t8d2 == t8d3: {mixed['t8d2'] == M8}, t8d5 == t8d3: {mixed['t8d5'] == M8}")
print(f"θ6∩θ8 {len(M6 & M8)} (Jaccard {jac(M6, M8):.2f}); θ10∩θ8 {len(M10 & M8)} (Jaccard {jac(M10, M8):.2f}); "
      f"all three {len(M6 & M8 & M10)} of union {len(M6 | M8 | M10)}")


def strata_info(D, cfgs):
    m = D.group_id.isin(cfgs).values
    s = (D.group_id + "|" + rtc_bin(D.rounds_to_cut)).values
    df = pd.DataFrame({"s": s[m], "y": D.tip.values[m]})
    g = df.groupby("s").y.agg(["sum", "size"])
    contrib = g[(g["sum"] > 0) & (g["sum"] < g["size"])]
    return set(contrib.index), int(df.y.sum()), int(m.sum())


S = {}
for t in TAGS:
    D = DATA[t][0]
    S[t] = strata_info(D, mixed[t])
    print(f"{t}: contributing strata {len(S[t][0])}, positives in mixed rows {S[t][1]}, mixed rows {S[t][2]}")
print(f"strata shared with t8d3: t6d3 {len(S['t6d3'][0] & S['t8d3'][0])}, t10d3 {len(S['t10d3'][0] & S['t8d3'][0])}")


def slice_auc(D, cfgs, k):
    m = D.group_id.isin(cfgs).values
    s = (D.group_id + "|" + rtc_bin(D.rounds_to_cut)).values
    return stratified_auroc(D.tip.values[m], D[k].values[m], s[m])


print("\nslice AUROC: reported (own mixed set) | θ=8 mixed set | 7-config intersection")
I3 = M6 & M8 & M10
for t in TAGS:
    D = DATA[t][0]
    print(f"  {t}")
    for k in KEYS:
        print(f"    {k:18s} {slice_auc(D, mixed[t], k):.3f} | {slice_auc(D, M8, k):.3f} | {slice_auc(D, I3, k):.3f}")


def cfg_parts(D, cfgs, k):
    """Per config: N_c = sum_b w_cb * auc_cb and W_c = sum_b w_cb over its config x time-bin strata."""
    from sklearn.metrics import roc_auc_score
    m = D.group_id.isin(cfgs).values
    Dm = D[m].assign(bin=rtc_bin(D.rounds_to_cut[m]).values)
    N, W = {}, {}
    for (c, _), g in Dm.groupby(["group_id", "bin"]):
        npos, nneg = int(g.tip.sum()), int((1 - g.tip).sum())
        N.setdefault(c, 0.0)
        W.setdefault(c, 0.0)
        if npos and nneg:
            N[c] += npos * nneg * roc_auc_score(g.tip, g[k])
            W[c] += npos * nneg
    cs = sorted(set(Dm.group_id))
    return cs, np.array([N[c] for c in cs]), np.array([W[c] for c in cs])


def boot_slice(D, cfgs, keys, n_boot, seed=0, diffs=(), merge_dups=False):
    """Cluster bootstrap over the slice's configs; each drawn copy is its own stratum (weight k_c), or with
    merge_dups the copies share one stratum (weight k_c^2, as a plain groupby on group_id|bin would do)."""
    parts = {k: cfg_parts(D, cfgs, k) for k in keys}
    cs = parts[keys[0]][0]
    rng = np.random.default_rng(seed)
    res = {k: [] for k in keys}
    for _ in range(n_boot):
        pick = rng.choice(len(cs), len(cs), replace=True)
        cnt = np.bincount(pick, minlength=len(cs)).astype(float)
        w = cnt ** 2 if merge_dups else cnt
        for k in keys:
            _, N, W = parts[k]
            den = (w * W).sum()
            res[k].append((w * N).sum() / den if den else np.nan)
    ci = {k: (np.nanpercentile(res[k], 2.5), np.nanpercentile(res[k], 97.5)) for k in keys}
    dd = {}
    for a, b in diffs:
        d = np.array(res[a]) - np.array(res[b])
        dd[f"{a} - {b}"] = (np.nanmean(d), np.nanpercentile(d, 2.5), np.nanpercentile(d, 97.5))
    return ci, dd


BK = ["clock", "bag+graph", "zs:global_full", "zs:pairwise", "oracle"]
DF = [("zs:pairwise", "bag+graph"), ("zs:global_full", "bag+graph"), ("clock", "bag+graph")]
for merge in (False, True):
    for setname in ("own", "theta8"):
        print(f"\n2000x config bootstrap (seed 0), slice on {setname} mixed set, merge_dups={merge}")
        for t in TAGS:
            D = DATA[t][0]
            cf = mixed[t] if setname == "own" else M8
            ci, dd = boot_slice(D, cf, BK, 2000, diffs=DF, merge_dups=merge)
            print(f"  {t}: " + "; ".join(f"{k} {slice_auc(D, cf, k):.3f} [{ci[k][0]:.3f}, {ci[k][1]:.3f}]" for k in BK))
            print("      diffs: " + "; ".join(f"{k} {v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}]" for k, v in dd.items()))
