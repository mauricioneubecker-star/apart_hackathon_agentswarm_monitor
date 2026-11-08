#!/usr/bin/env python3
"""Stage-2 sweep of the hybrid on cached stage-1 node probabilities (all 18 folds x seeds).

  python3 gnn_opt/hybrid_sweep.py --seeds 0,1,2 [--ica 0]
Prints the selection table and writes the best variants' CV files to preds/cv/hybsw_<variant>.csv.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402
import hybrid as HY  # noqa: E402
import nodefeat as NF  # noqa: E402
import tabular  # noqa: E402


def variants():
    V = {}
    for d, it, leaf, l2 in itertools.product([2, 3], [100, 250], [20, 80], [0.0, 3.0]):
        V[f"hgb_d{d}_i{it}_l{leaf}_r{l2:g}"] = ("hgb", dict(depth=d, iters=it, lr=0.05, leaf=leaf, l2=l2), "est")
    V["lr_est"] = ("lr", {}, "est")
    for fs in ["est+pair", "est+struct", "est+mem"]:
        V[f"hgb_d2_i100_l80_{fs}"] = ("hgb", dict(depth=2, iters=100, lr=0.05, leaf=80, l2=3.0), fs)
        V[f"hgb_d3_i250_l20_{fs}"] = ("hgb", dict(depth=3, iters=250, lr=0.05, leaf=20, l2=0.0), fs)
    return V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "..", "gnn_opt_data", "night"))
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--ica", type=int, default=0)
    ap.add_argument("--target", default="y3")
    ap.add_argument("--write", default="", help="comma list of variants to write as CV files")
    a = ap.parse_args()
    hy = HY.Hybrid(a.data, ica=a.ica, stage2="est")
    S = hy.S
    T = hy.D["T"]
    fs = tabular.feature_sets(T.columns)
    extra = {"est": [], "est+pair": fs["pairwise"], "est+struct": fs["struct"], "est+mem": [c for c in T.columns if c.startswith("mem_")]}
    F = H.folds()
    base = H.train_rows(S, a.target)
    y = S[a.target].values
    seeds = [int(s) for s in a.seeds.split(",")]
    V = variants()
    preds = {v: [] for v in V}
    for kind in ("id", "lodo"):
        for fname, te_cfgs in F[kind].items():
            te = (base & S.cfg.isin(te_cfgs)).values
            tr = (base & ~S.cfg.isin(te_cfgs)).values
            tr_runs = S.run[tr].unique()
            tr_snaps = S.snap[S.run.isin(tr_runs)].values
            te_snaps = S.snap[S.run.isin(S.run[te].unique())].values
            acc = {v: [] for v in V}
            cnt = []
            for sd in seeds:
                ps, pf = hy.stage1(tr_snaps, te_snaps, sd)
                GF = NF.graph_from_nodes(ps, pf, hy.NT, hy.D, S).reset_index(drop=True)
                cnt.append(GF.est_count.values[te])
                for v, (kindm, prm, fset) in V.items():
                    X = pd.concat([GF, T[extra[fset]].reset_index(drop=True)], axis=1).values
                    if kindm == "hgb":
                        m = HY.hgb2(sd, **prm)
                    else:
                        m = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))
                    m.fit(X[tr], y[tr])
                    acc[v].append(m.predict_proba(X[te])[:, 1])
            for v in V:
                preds[v].append(pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values,
                                              "score": np.mean(acc[v], 0), "count": np.mean(cnt, 0), "fold": fname}))
            print("done", fname, flush=True)
    rows = []
    for v in V:
        P = pd.concat(preds[v], ignore_index=True)
        cs = H.cv_summary(S, P, a.target)
        rows.append({"variant": v, "select": cs["select"], "id_auroc": cs["id_auroc"], "id_auprc": cs["id_auprc"],
                     "lodo_mean": cs["lodo_mean"], "lodo_min": cs["lodo_min"]})
        if v in a.write.split(","):
            P.to_csv(os.path.join(HERE, "preds", "cv", f"hybsw{a.ica}_{v}.csv"), index=False, float_format="%.5g")
    R = pd.DataFrame(rows).sort_values("select", ascending=False)
    print(R.round(4).to_string(index=False))
    R.to_csv(os.path.join(HERE, "preds", f"hybrid_sweep_ica{a.ica}.csv"), index=False)


if __name__ == "__main__":
    main()
