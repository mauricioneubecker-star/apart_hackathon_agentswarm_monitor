#!/usr/bin/env python3
"""Two-stage propagated-feature hybrid (node model -> estimated count / exposure -> graph GBM).

  python3 gnn_opt/hybrid.py --name hyb_v1 [--stage2 est|est+table|est+mem] [--lex] [--seeds 0,1,2]
  python3 gnn_opt/hybrid.py --name hyb_v1 --final --predict-splits night_val
Writes gnn_opt/preds/cv/<name>.csv or preds/eval/<name>.csv (score, count = estimated violator count).
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402
import nodefeat as NF  # noqa: E402
import tabular  # noqa: E402


CACHE = os.environ.get("GNN_OPT_STAGE1_CACHE", "/home/claude/cache/stage1")


def hgb2(seed=0, depth=3, iters=250, lr=0.05, leaf=20, l2=0.0):
    return HistGradientBoostingClassifier(max_depth=depth, max_iter=iters, learning_rate=lr, min_samples_leaf=leaf,
                                          l2_regularization=l2, random_state=seed)


class Hybrid:
    def __init__(self, data_dir, lex=False, stage2="est+mem", cache=True, judge_ef=None, ica=0):
        self.ica = ica
        self.tag = os.path.abspath(data_dir) + ("lex" if lex else "")
        self.D = H.load(data_dir, graphs=True)
        S = self.D["S"]
        cp = os.path.join(data_dir, f"node_table{'_lex' if lex else ''}.pkl")
        if cache and os.path.exists(cp) and judge_ef is None:
            self.NT, self.ncols = pickle.load(open(cp, "rb"))
        else:
            self.NT, self.ncols = NF.build_node_table(self.D, S, lex=lex, judge_ef=judge_ef)
            if cache and judge_ef is None:
                pickle.dump((self.NT, self.ncols), open(cp, "wb"))
        self.S = S
        fs = tabular.feature_sets(self.D["T"].columns)
        self.tcols = {"est": [], "est+table": fs["bag+graph"], "est+mem": fs["bag+graph+mem"],
                      "est+mem+lex": fs["bag+graph+mem+lex"]}[stage2]
        if lex and stage2 == "est+mem":
            self.tcols = fs["bag+graph+mem+lex"]
        self.stage2 = stage2
        self.node_lab = self.D["node_lab"]

    def stage1(self, tr_snaps, te_snaps, seed=0):
        """Stage-1 node probabilities, cached on disk by (train set, test set, seed, ica, feature table)."""
        import hashlib
        key = hashlib.md5(np.sort(tr_snaps).tobytes() + np.sort(te_snaps).tobytes() +
                          f"{seed}-{self.ica}-{len(self.ncols)}-{self.tag}".encode()).hexdigest()[:16]
        cp = os.path.join(CACHE, f"{key}.npz")
        if os.path.exists(cp):
            z = np.load(cp)
            return z["ps"], z["pf"]
        if self.ica:
            ps, pf = NF.node_stage_ica(self.NT, self.ncols, self.node_lab, self.S, self.D, tr_snaps, te_snaps, seed,
                                       rounds=self.ica)
        else:
            ps, pf, _ = NF.node_stage(self.NT, self.ncols, self.node_lab, self.S, tr_snaps, te_snaps, seed=seed)
        os.makedirs(CACHE, exist_ok=True)
        np.savez(cp, ps=ps, pf=pf)
        return ps, pf

    def fit_predict(self, tr_mask, te_mask, target="y3", seed=0, s2=None):
        S = self.S
        s2 = s2 or {}
        tr_runs = S.run[tr_mask].unique()
        tr_snaps = S.snap[S.run.isin(tr_runs)].values          # all rounds of training runs (node labels)
        te_snaps = S.snap[S.run.isin(S.run[te_mask].unique())].values   # all rounds (lag features)
        ps, pf = self.stage1(tr_snaps, te_snaps, seed)
        GF = NF.graph_from_nodes(ps, pf, self.NT, self.D, S)
        X = pd.concat([GF.reset_index(drop=True), self.D["T"][self.tcols].reset_index(drop=True)], axis=1)
        y = S[target].values
        m = hgb2(seed, **s2).fit(X[tr_mask].values, y[tr_mask])
        return m.predict_proba(X[te_mask].values)[:, 1], GF.est_count.values[te_mask]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "..", "gnn_opt_data", "night"))
    ap.add_argument("--name", required=True)
    ap.add_argument("--stage2", default="est+mem")
    ap.add_argument("--s2", default="{}")
    ap.add_argument("--lex", action="store_true")
    ap.add_argument("--ica", type=int, default=0, help="iterative-classification rounds (neighbour propagation)")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--target", default="y3")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--predict-splits", default="night_val")
    a = ap.parse_args()
    t0 = time.time()
    hy = Hybrid(a.data, lex=a.lex, stage2=a.stage2, ica=a.ica)
    S = hy.S
    seeds = [int(s) for s in a.seeds.split(",")]
    s2 = json.loads(a.s2)

    def fp(tr, te):
        r = [hy.fit_predict(tr, te, a.target, s, s2) for s in seeds]
        return np.mean([x[0] for x in r], 0), np.mean([x[1] for x in r], 0)

    if not a.final:
        P = H.run_cv(S, fp, target=a.target)
        P.to_csv(os.path.join(HERE, "preds", "cv", f"{a.name}.csv"), index=False, float_format="%.5g")
        cs = H.cv_summary(S, P, a.target)
        print(json.dumps({"name": a.name, "select": round(cs["select"], 4), "id_auroc": round(cs["id_auroc"], 4),
                          "id_auprc": round(cs["id_auprc"], 4), "lodo_mean": round(cs["lodo_mean"], 4),
                          "lodo_min": round(cs["lodo_min"], 4), "lodo": {k: round(v, 3) for k, v in cs["lodo"].items()},
                          "minutes": round((time.time() - t0) / 60, 1)}))
        with open(os.path.join(HERE, "preds", "cv_log.jsonl"), "a") as f:
            f.write(json.dumps({"name": a.name, **cs, "stage2": a.stage2, "s2": s2, "ica": a.ica, "lex": a.lex, "seeds": seeds,
                                "target": a.target}) + "\n")
        return
    tr = H.train_rows(S, a.target).values
    sps = None if a.predict_splits == "all" else a.predict_splits.split(",")
    te = ((S.split != H.TRAIN_SPLIT) if sps is None else S.split.isin(sps)).values
    sc, cn = fp(tr, te)
    pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": sc, "count": cn}).to_csv(
        os.path.join(HERE, "preds", "eval", f"{a.name}.csv"), index=False, float_format="%.5g")
    print("wrote", a.name)


if __name__ == "__main__":
    main()
