#!/usr/bin/env python3
"""Baselines on exactly the GNN rows and folds. Writes CV and held-out prediction files.

  python3 gnn_opt/baselines.py --data gnn_opt_data/night [--only bag+graph,pairwise] [--target y3]
      [--predict-splits night_val]       # held-out predictions (default: val only; 'all' for final test runs)
      [--apply gnn_opt_data/new]         # also predict a new batch with the models trained on all of night_train

Outputs: gnn_opt/preds/cv/<name>.csv (fold column) and gnn_opt/preds/eval/<name>.csv (all snapshots of the
requested splits; evaluate.py restricts to labelled rows).
Models: HistGradientBoosting (compare.py settings) on tabular sets; logistic regression; per-edge classifier
max/top-3-pooled per snapshot (communication oversight); oracle (true violator count + clock, reference only).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402
import tabular  # noqa: E402
from data import E_GEN  # noqa: E402

PRED = os.path.join(HERE, "preds")


def hgb(seed=0):
    return HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05, random_state=seed)


def lr():
    return make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000))


class TabModel:
    def __init__(self, cols, make):
        self.cols, self.make = cols, make

    def fit(self, T, y):
        self.m = self.make().fit(T[self.cols].values, y)
        return self

    def predict(self, T):
        return self.m.predict_proba(T[self.cols].values)[:, 1]


class EdgeMonitor:
    """Per-edge classifier on single-edge generic features (+ log edge count of the snapshot is NOT used).
    Training label of an edge = label of its snapshot (multiple-instance, naive). Snapshot score = pooled edge
    scores (max or top-3 mean). Snapshots without edges get the training base rate of empty snapshots."""

    def __init__(self, G, pool="max"):
        self.G, self.pool = G, pool
        ec = list(G["ecols"])
        self.ci = [ec.index(c) for c in E_GEN]
        self.esnap = G["node_snap"][G["ES"]]

    def _edges(self, snaps):
        m = np.isin(self.esnap, snaps)
        X = np.nan_to_num(self.G["EF"][m][:, self.ci], nan=-1.0)
        return X, self.esnap[m]

    def fit(self, snaps, y):
        X, es = self._edges(snaps)
        lab = pd.Series(y, index=snaps)
        self.m = hgb().fit(X, lab.loc[es].values)
        self.empty = float(np.mean(y[~np.isin(snaps, es)])) if (~np.isin(snaps, es)).any() else 0.0
        return self

    def predict(self, snaps):
        X, es = self._edges(snaps)
        p = self.m.predict_proba(X)[:, 1]
        s = pd.Series(p).groupby(es)
        agg = s.max() if self.pool == "max" else s.apply(lambda v: np.sort(v.values)[-3:].mean())
        return pd.Series(snaps).map(agg).fillna(self.empty).values


def specs(T):
    fs = tabular.feature_sets(T.columns)
    sp = {f"hgb_{k}": (lambda c=v: TabModel(c, hgb)) for k, v in fs.items()}
    sp["lr_bag+graph"] = lambda: TabModel(fs["bag+graph"], lr)
    sp["lr_bag+graph+mem"] = lambda: TabModel(fs["bag+graph+mem"], lr)
    sp["oracle_risk+clock"] = lambda: TabModel(["risk", "t"], hgb)
    sp["oracle_risk"] = lambda: TabModel(["risk"], hgb)
    return sp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--target", default="y3")
    ap.add_argument("--predict-splits", default="night_val")
    ap.add_argument("--apply", nargs="*", default=[], help="extra dataset dirs to predict with the full-train models")
    ap.add_argument("--no-cv", action="store_true")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    D = H.load(a.data, graphs=True)
    S, T = D["S"], D["T"]
    T = T.assign(risk=S.risk.values)
    sp = specs(T)
    sp["edge_monitor_max"] = lambda: EdgeMonitor(D, "max")
    sp["edge_monitor_top3"] = lambda: EdgeMonitor(D, "top3")
    names = a.only.split(",") if a.only else list(sp)
    os.makedirs(os.path.join(PRED, "cv"), exist_ok=True)
    os.makedirs(os.path.join(PRED, "eval"), exist_ok=True)
    y = S[a.target].values
    snaps = S.snap.values
    tgt = "" if a.target == "y3" else f"_{a.target}"
    for n in names:
        mk = sp[n]
        is_edge = n.startswith("edge_monitor")

        def fp(tr, te):
            m = mk()
            if is_edge:
                return m.fit(snaps[tr], y[tr]).predict(snaps[te])
            return m.fit(T[tr], y[tr]).predict(T[te])

        if not a.no_cv:
            P = H.run_cv(S, fp, target=a.target)
            P.to_csv(os.path.join(PRED, "cv", f"{n}{tgt}{a.tag}.csv"), index=False, float_format="%.5g")
            cs = H.cv_summary(S, P, a.target)
            print(f"{n:28s} select {cs['select']:.3f}  ID {cs['id_auroc']:.3f}/{cs['id_auprc']:.3f}  "
                  f"LODO mean {cs['lodo_mean']:.3f} min {cs['lodo_min']:.3f}", flush=True)
        tr = H.train_rows(S, a.target).values
        m = mk()
        m = m.fit(snaps[tr], y[tr]) if is_edge else m.fit(T[tr], y[tr])
        sps = None if a.predict_splits == "all" else a.predict_splits.split(",")
        te = (S.split != H.TRAIN_SPLIT).values if sps is None else S.split.isin(sps).values
        p = m.predict(snaps[te]) if is_edge else m.predict(T[te])
        pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": p}).to_csv(
            os.path.join(PRED, "eval", f"{n}{tgt}{a.tag}.csv"), index=False, float_format="%.5g")
        for extra in a.apply:
            if is_edge:
                continue
            E = H.load(extra)
            pe = m.predict(E["T"].assign(risk=E["S"].risk.values))
            od = os.path.join(PRED, "apply", os.path.basename(extra.rstrip("/")))
            os.makedirs(od, exist_ok=True)
            pd.DataFrame({"run": E["S"].run, "round": E["S"]["round"], "score": pe}).to_csv(
                os.path.join(od, f"{n}{tgt}{a.tag}.csv"), index=False)


if __name__ == "__main__":
    main()
