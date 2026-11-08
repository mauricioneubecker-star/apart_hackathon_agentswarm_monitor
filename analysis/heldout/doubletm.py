"""POST HOC sensitivity (8 Nov., after seeing that the RQ2 verdict depends on the time-matching definition):
time-matched AUROC within (deadline cut x rounds-to-cut bin) strata, i.e. absolute round AND distance to the
deadline held fixed at once. Same exact paired cluster bootstrap over configs as analysis.py (hlib)."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import hlib as L

S, lab = L.load_snapshots()
H = lab[lab.split.isin(L.HO)].reset_index(drop=True)
cfgs = sorted(H.cfg.unique()); C = len(cfgs); g = H.cfg.map({c: i for i, c in enumerate(cfgs)}).values
y = H.y.values
strata = (H.cut.astype(int).astype(str) + "|" + H.rtc_bin).values
names = ["clock", "bag+graph", "tab_mem", "zs:pairwise", "zs:global_full", "zs:agent", "gnn5", "hybrid", "oracle"]
scores = {}
for n in names:
    s, miss, nan = L.attach(H, L.read_pred(L.PREDICTORS[n][0]))
    assert miss == 0 and nan == 0, n
    scores[n] = s
K = L.draws(C, 10000, 20261108)
full = np.ones((1, C))
res = {"rows": int(len(H)), "positives": int(y.sum()), "configs": C,
       "strata_with_both_classes": int(sum(1 for b in np.unique(strata) if 0 < y[strata == b].sum() < (strata == b).sum()))}
vals, boots = {}, {}
for n in names:
    mats = L.pair_mats(y, scores[n], g, strata, C)
    vals[n] = float(L.stat_pairs(full, mats)[0]); boots[n] = L.stat_pairs(K, mats)
res["auroc_cut_x_rtc"] = {n: {"value": round(vals[n], 4), "ci": [round(x, 4) for x in L.ci(boots[n])]} for n in names}
fam = ["bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid"]
ps = [L.pval(boots[n] - boots["clock"]) for n in fam]
adj = L.holm(ps)
res["minus_clock"] = {n: {"diff": round(vals[n] - vals["clock"], 4), "ci": [round(x, 4) for x in L.ci(boots[n] - boots["clock"])],
                          "p": round(p, 4), "p_holm_5": round(float(a), 4)} for n, p, a in zip(fam, ps, adj)}
for n in ("tab_mem", "zs:agent"):
    d = boots[n] - boots["clock"]
    res["minus_clock"][n] = {"diff": round(vals[n] - vals["clock"], 4), "ci": [round(x, 4) for x in L.ci(d)], "p": round(L.pval(d), 4), "note": "secondary"}
json.dump(res, open(L.HO_DIR + "/out/doubletm.json", "w"), indent=1)
print(json.dumps(res, indent=1))
