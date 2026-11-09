"""Independent refit of the three harness baselines whose committed eval files cover night_val only:
hgb_clock (feature t), hgb_bag+graph (bag + graph aggregates, no task lexicon), oracle_risk+clock (risk, t).

Spec re-implemented from gnn_opt/baselines.py + tabular.feature_sets (read, not imported):
HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05, random_state=0), trained on
night_train rows with eval == 1 and y3 defined; predictions for every snapshot outside night_train."""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
D = f"{SCR}/stat/data/night"
OUT = f"{SCR}/heldout-verify/preds/refit"
import os
os.makedirs(OUT, exist_ok=True)

S = pd.read_csv(f"{D}/snapshots.csv", low_memory=False)
T = pd.read_csv(f"{D}/table.csv")
assert (T.snap.values == S.snap.values).all()
T["risk"] = S.risk.values

TASK = ["mech_ref", "mech_ref_ema", "pressure_lex", "bcast_mech_ref", "exposure_breadth"]
def has_task(c):
    return any(k in c for k in TASK)
cols = list(T.columns)
bag = [c for c in cols if c.split("_")[0] in ("max", "sum", "mean", "n2", "top3", "nmax", "nmean", "nn")
       and not has_task(c) and "tests_failed" not in c and "escalated" not in c] + ["n_edges"]
graph = [c for c in cols if (c.startswith("g_") or c.startswith("d3_g_")) and not has_task(c)]
bg = list(dict.fromkeys(bag + graph))
print("bag+graph features:", len(bg), "(bag", len(bag), "graph", len(graph), ")")
print("  any task-lexicon column?", any(has_task(c) for c in bg), " has t?", "t" in bg, " has risk?", "risk" in bg)

tr = ((S.split == "night_train") & (S["eval"] == 1) & S.y3.notna()).values
te = (S.split != "night_train").values
y = S.y3.values
print("train rows", int(tr.sum()), "pos", int(np.nansum(y[tr])), "| predict", int(te.sum()))

specs = {"hgb_clock": ["t"], "hgb_bag+graph": bg, "oracle_risk+clock": ["risk", "t"]}
for name, fc in specs.items():
    m = HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05, random_state=0)
    m.fit(T.loc[tr, fc].values, y[tr])
    p = m.predict_proba(T.loc[te, fc].values)[:, 1]
    P = pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": p})
    P.to_csv(f"{OUT}/{name}.csv", index=False, float_format="%.5g")
    # compare with committed night_val file
    C = pd.read_csv(f"{SCR}/heldout-verify/preds/eval/gnnopt_{name}.csv")
    Q = C.merge(pd.read_csv(f"{OUT}/{name}.csv"), on=["run", "round"], suffixes=("_c", "_m"))
    lab = S[(S.split == "night_val") & (S["eval"] == 1) & S.y3.notna()][["run", "round", "y3"]]
    Qv = Q.merge(lab, on=["run", "round"])
    print(f"{name:20s} val rows matched {len(Q)} | max|diff| {np.abs(Q.score_c - Q.score_m).max():.3g} "
          f"exact-equal share {(Q.score_c == Q.score_m).mean():.4f} | val AUROC committed {roc_auc_score(Qv.y3, Qv.score_c):.4f}"
          f" refit {roc_auc_score(Qv.y3, Qv.score_m):.4f}")
    # compare with the other analyst's regen file (if present)
    o = f"{SCR}/heldout/preds/regen/{name}.csv"
    if os.path.exists(o):
        O = pd.read_csv(o).merge(pd.read_csv(f"{OUT}/{name}.csv"), on=["run", "round"], suffixes=("_o", "_m"))
        print(f"{'':20s} vs other analyst's regen: rows {len(O)} max|diff| {np.abs(O.score_o - O.score_m).max():.3g}"
              f" exact-equal share {(O.score_o == O.score_m).mean():.4f}")
