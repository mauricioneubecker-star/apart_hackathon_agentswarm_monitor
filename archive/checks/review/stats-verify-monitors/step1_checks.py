"""Data checks + full-sample point values, own code."""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/verify-monitors")
import vlib as L  # noqa

S, lab, cfgs = L.load_rows()
print("splits:", S.split.value_counts().to_dict())
ev = S[(S["eval"] == 1) & S.y3.notna()]
print("eval rows by split:", ev.groupby("split").agg(n=("y3", "size"), pos=("y3", "sum")).to_dict("index"))
print("night_train rows", len(lab), "pos", lab.y.sum(), "cfgs", lab.cfg.nunique(), "runs", lab.run.nunique(),
      "tipped runs", lab.groupby("run").tipped.first().sum(), "cfgs w/ pos", (lab.groupby("cfg").y.sum() > 0).sum(),
      "max pos/cfg", lab.groupby("cfg").y.sum().max())
print("label agreement harness y3 vs llm _base tip:", int((lab.tip.values == lab.y3.values).sum()), "/", len(lab),
      "; group_id==cfg:", bool((lab.group_id == lab.cfg).all()), "; rtc NaN:", int(lab.rounds_to_cut.isna().sum()))
print("rtc == t - cut:", bool((lab.rounds_to_cut == lab.t - lab.cut).all()), " cut values:", sorted(lab.cut.unique()))
F = json.load(open(L.FOLDS))
assert sorted(F["train_cfgs"]) == list(cfgs), "folds train_cfgs != lab cfgs"
pos_by_tbin = lab.groupby(pd.cut(lab.t, [0, 5, 10, 15, 20, 25, 30])).y.agg(["size", "sum"])
print("t-bins:", pos_by_tbin.to_dict("index"))
print("rtc bins:", lab.groupby(pd.cut(lab.rounds_to_cut, [-99, -9, -5, -1, 3, 99])).y.agg(["size", "sum"]).to_dict("index"))

files = {"clock": "hgb_clock.csv", "bag+graph": "hgb_bag+graph.csv", "gnn_final": "final.csv",
         "gnn_hybrid": "final+hgb_bag+graph+mem.csv", "bag+graph+mem": "hgb_bag+graph+mem.csv",
         "edge_monitor_top3": "edge_monitor_top3.csv", "e_ngru_4runs": "e_ngru_4runs.csv",
         "h_ngru4_hgb_logit55": "h_ngru4_hgb_logit55.csv", "final_hybrid(gnn-opt)": "final_hybrid.csv"}
preds = {}
for n, f in files.items():
    d = L.cv_scores(f"{L.GIT}/{f}", lab)
    assert not np.isnan(d["oof"]).any(), n
    for r, v in d["rep"].items():
        assert not np.isnan(v).any(), (n, r)
    # fold membership: each LODO fold holds exactly the eval rows of its held-out configs
    for f2, (rows, sc) in d["lodo"].items():
        exp = set(np.where(lab.cfg.isin(F["lodo"][f2]).values)[0])
        assert set(rows) == exp and len(rows) == len(exp), (n, f2)
    preds[n] = d
for v in ("pairwise", "global_full", "global_window"):
    s = L.zs_scores(v, lab)
    assert not np.isnan(s).any(), v
    preds["zs:" + v] = {"oof": s, "rep": {"id0": s, "id1": s},
                        "lodo": {f2: (np.where(lab.cfg.isin(F["lodo"][f2]).values)[0],
                                      s[lab.cfg.isin(F["lodo"][f2]).values]) for f2 in F["lodo"]}}
    # compare with the other analyst's derived CV file
    Z = pd.read_csv(f"{L.ST}/preds/zs_{v}.csv")
    zz = lab[["run", "round"]].merge(Z.groupby(["run", "round"]).score.agg(["min", "max"]).reset_index(),
                                     on=["run", "round"], how="left")
    print(f"zs:{v}: their CV file vs llm_monitor zs_tip: max|diff| {np.nanmax(np.abs(zz['max'].values - s)):.2e}, "
          f"fold-constant {bool((zz['min'] == zz['max']).all())}, range [{s.min():.3f}, {s.max():.3f}], distinct {len(np.unique(s))}")

nC = len(cfgs)
one = np.ones((1, nC))
y, t = lab.y.values, lab.t.values
P = {n: L.Pred(d["oof"], lab, nC) for n, d in preds.items()}
print("\n== full-sample values (own code) ==")
rows = []
for n, d in preds.items():
    s = d["oof"]
    a1 = P[n].auroc(one)[0]; a2 = roc_auc_score(y, s); a3 = L.mw_auc(y, s)
    tb = P[n].tauroc(one)[0]; tr = P[n].tauroc_rtc(one)[0]
    repmean = np.mean([L.mw_auc(y, v) for v in d["rep"].values()])
    rep0 = L.mw_auc(y, d["rep"]["id0"])
    rows.append({"pred": n, "auroc_oof": a1, "check_sklearn": a1 - a2, "check_mw": a1 - a3, "auroc_repmean": repmean,
                 "auroc_rep0": rep0, "tauroc_round": tb, "tauroc_rtc": tr})
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(R.round(4).to_string(index=False))

# resample equivalence: weighted levels vs materialised rows
rng = np.random.default_rng(99)
byc = [np.where(lab.c.values == c)[0] for c in range(nC)]
mx = 0.0
for _ in range(5):
    pick = rng.integers(0, nC, nC)
    rr = np.concatenate([byc[c] for c in pick])
    K = np.bincount(pick, minlength=nC)[None, :].astype(float)
    for n in ("zs:pairwise", "gnn_final", "clock", "bag+graph"):
        s = preds[n]["oof"]
        mx = max(mx, abs(P[n].auroc(K)[0] - roc_auc_score(y[rr], s[rr])))
        # tAUROC on materialised rows (own loop)
        num = den = 0.0
        for a in (1, 6, 11, 16, 21, 26):
            m = (t[rr] >= a) & (t[rr] <= a + 4)
            yy = y[rr][m]
            if m.sum() and 0 < yy.sum() < len(yy):
                num += yy.sum() * roc_auc_score(yy, s[rr][m]); den += yy.sum()
        mx = max(mx, abs(P[n].tauroc(K)[0] - num / den))
        rt = lab.rounds_to_cut.values[rr]
        num = den = 0.0
        for lo, hi in [(-99, -9), (-9, -5), (-5, -1), (-1, 3), (3, 99)]:
            m = (rt > lo) & (rt <= hi)
            yy = y[rr][m]
            if 0 < yy.sum() < len(yy):
                w = yy.sum() * (len(yy) - yy.sum()); num += w * roc_auc_score(yy, s[rr][m]); den += w
        mx = max(mx, abs(P[n].tauroc_rtc(K)[0] - num / den))
print(f"\nresample equivalence (levels vs materialised): max|diff| {mx:.2e}")
np.save(f"{L.V}/_dummy.npy", np.zeros(1))
