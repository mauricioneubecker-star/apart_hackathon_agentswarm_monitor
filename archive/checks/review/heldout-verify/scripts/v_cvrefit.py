"""Does a local CV refit of hgb_clock / hgb_bag+graph (id folds from folds.json) reproduce the committed CV files
that supply the 5 %-FPR thresholds? (Own code; folds.json read as data.)"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
V = f"{SCR}/heldout-verify"
S = pd.read_csv(f"{SCR}/stat/data/night/snapshots.csv", low_memory=False)
T = pd.read_csv(f"{SCR}/stat/data/night/table.csv")
F = json.load(open(f"{SCR}/stat/repo/gnn_opt/folds.json"))
TASK = ["mech_ref", "mech_ref_ema", "pressure_lex", "bcast_mech_ref", "exposure_breadth"]
ht = lambda c: any(k in c for k in TASK)
cols = list(T.columns)
bag = [c for c in cols if c.split("_")[0] in ("max", "sum", "mean", "n2", "top3", "nmax", "nmean", "nn")
       and not ht(c) and "tests_failed" not in c and "escalated" not in c] + ["n_edges"]
graph = [c for c in cols if (c.startswith("g_") or c.startswith("d3_g_")) and not ht(c)]
bg = list(dict.fromkeys(bag + graph))
base = ((S.split == "night_train") & (S["eval"] == 1) & S.y3.notna()).values
y = S.y3.values

def thr_at(yy, p):
    neg = np.sort(p[yy == 0]); k = int(np.ceil(0.95 * len(neg))) - 1
    return neg[min(max(k, 0), len(neg) - 1)] + 1e-12

for name, fc in (("hgb_clock", ["t"]), ("hgb_bag+graph", bg)):
    out = []
    for fold, te_cfgs in F["id"].items():
        te = base & S.cfg.isin(te_cfgs).values
        tr = base & ~S.cfg.isin(te_cfgs).values
        m = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05, random_state=0)
        m.fit(T.loc[tr, fc].values, y[tr])
        out.append(pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values,
                                 "score": m.predict_proba(T.loc[te, fc].values)[:, 1], "fold": fold}))
    P = pd.concat(out)
    C = pd.read_csv(f"{V}/preds/cv/{name}.csv")
    C = C[C.fold.str.startswith("id")]
    M = C.merge(P, on=["run", "round", "fold"], suffixes=("_c", "_m"))
    oofm = P.groupby(["run", "round"], as_index=False).score.mean()
    oofc = C.groupby(["run", "round"], as_index=False).score.mean()
    lab = S[base][["run", "round", "y3"]]
    tm = oofm.merge(lab, on=["run", "round"]); tc = oofc.merge(lab, on=["run", "round"])
    # float_format %.5g as in baselines.py
    print(f"{name:14s} id-fold rows {len(M)} max|diff| {np.abs(M.score_c - M.score_m).max():.3g} "
          f"(after %.5g rounding: {np.abs(M.score_c - M.score_m.map(lambda v: float(f'{v:.5g}'))).max():.3g}) | "
          f"thr committed CV {thr_at(tc.y3.values, tc.score.values):.5g}  thr local CV refit {thr_at(tm.y3.values, tm.score.values):.5g}")
