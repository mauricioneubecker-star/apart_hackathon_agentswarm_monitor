"""Score GNN / hybrid / GBM CV prediction files with a re-implementation of gnn_opt harness.cv_summary.
Read-only on all sources; the harness snapshot table is the scratch build (cfg/run/round/y3/eval valid)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

SC = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
S = pd.read_csv(f"{SC}/gnnopt_data/night/snapshots.csv", low_memory=False)
GO = f"{SC}/gnnopt_code/gnn_opt/preds/cv"
TO = f"{SC}/verify/findings/torch_cv"


def auroc(y, p):
    y = np.asarray(y)
    return roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan


def auprc(y, p):
    y = np.asarray(y)
    return average_precision_score(y, p) if len(np.unique(y)) == 2 else np.nan


def cv_summary(P, target="y3"):
    lab = S[["run", "round", target]].rename(columns={target: "y"})
    P = P.merge(lab, on=["run", "round"], how="left")
    ok = S.set_index(["run", "round"])["eval"].reindex(pd.MultiIndex.from_frame(P[["run", "round"]])).values == 1
    P = P[ok & P.y.notna().values]
    idm = P.fold.str.startswith("id")
    reps = P[idm].fold.str.split("_").str[0]
    id_au = [auroc(g.y, g.score) for _, g in P[idm].groupby(reps)]
    id_pr = [auprc(g.y, g.score) for _, g in P[idm].groupby(reps)]
    lodo = {f: auroc(g.y, g.score) for f, g in P[~idm].groupby("fold")}
    res = {"id": float(np.mean(id_au)) if id_au else np.nan, "id_pr": float(np.mean(id_pr)) if id_pr else np.nan,
           "n_id_reps": len(id_au), "lodo": lodo}
    if lodo:
        v = np.array([x for x in lodo.values() if x == x])
        res.update(lodo_mean=float(v.mean()), lodo_min=float(v.min()),
                   worst=min(lodo, key=lambda k: lodo[k] if lodo[k] == lodo[k] else 9),
                   select=float(np.mean([res["id"], v.mean(), v.min()])))
    return res


files = [("gnn-opt", GO, n) for n in ["final_hybrid", "abl_seed0", "hyb_est_s3", "hgb_bag+graph+mem", "hgb_bag+graph",
                                       "gnn_bn_gen+nt", "gnn_v1_s0"]]
files += [("torch", TO, n) for n in ["final", "final+hgb_bag+graph+mem", "e_ngru_4runs", "e_ngru_2seeds",
                                     "h_ngru4_hgb_logit55", "h_ngru_hgb_logit55", "b_gine_ggru", "b_rgine_ngru",
                                     "b_rgine_ggru", "c_ngru_seed1", "c_ngru_judgeaug"]]
rows = []
for br, d, n in files:
    p = os.path.join(d, n + ".csv")
    if not os.path.exists(p):
        print("missing", p)
        continue
    P = pd.read_csv(p)
    r = cv_summary(P)
    row = dict(branch=br, model=n, select=r.get("select"), ID=r["id"], ID_PR=r["id_pr"], reps=r["n_id_reps"],
               LODO_mean=r.get("lodo_mean"), LODO_min=r.get("lodo_min"), worst=r.get("worst"))
    row.update({k.replace("hold_", "L:"): v for k, v in r["lodo"].items()})
    rows.append(row)
T = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(T.round(3).to_string(index=False))
T.to_csv(f"{SC}/verify/findings/gnn_cv_table.csv", index=False)

# ID-only screens/controls (id0) for rewire / shuffle_ef
for n in ["m_ctl_rewire__id0", "m_ctl_shuffle_ef__id0"]:
    P = pd.read_csv(os.path.join(TO, n + ".csv"))
    r = cv_summary(P)
    print(n, "ID AUROC %.3f (reps %d)" % (r["id"], r["n_id_reps"]))
