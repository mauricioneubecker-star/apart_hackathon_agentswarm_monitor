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


def apply_control(D, control, seed=0):
    """Controls on the graph arrays (in place). rewire: degree-preserving destination swaps within each snapshot
    (keeps every sender's out-edges and their features, breaks who-read-whom). shuffle_edges: permute edge feature
    rows within each snapshot (keeps the snapshot's bag of edge features, breaks attribution to sender/receiver).
    shuffle_edges_global: permute edge feature rows across all snapshots (destroys content)."""
    import train as TR
    rng = np.random.default_rng(seed)
    esnap = D["node_snap"][D["ES"]]
    if control == "rewire":
        D["ES"], D["ED"] = TR.rewire(D["ES"], D["ED"], esnap, rng)
    elif control == "shuffle_edges":
        order = np.argsort(esnap, kind="stable")
        b = np.flatnonzero(np.diff(np.r_[-1, esnap[order], -2]))
        perm = np.arange(len(esnap))
        for x, y in zip(b[:-1], b[1:]):
            idx = order[x:y]
            perm[idx] = rng.permutation(idx)
        D["EF"] = D["EF"][perm]
    elif control == "shuffle_edges_global":
        D["EF"] = D["EF"][rng.permutation(len(esnap))]
    elif control != "shuffle_labels":
        raise ValueError(control)
    if control == "shuffle_labels":
        S = D["S"]
        tr = S[S.split == H.TRAIN_SPLIT].run.unique()
        perm = dict(zip(tr, rng.permutation(tr)))
        by = {r: g for r, g in S.groupby("run")}
        nl = D["node_lab"].copy()
        for col in ["y3", "y5", "yrel3", "yrel5", "risk", "eval"]:
            S[col] = np.concatenate([by[perm.get(r, r)][col].values for r in S.run.unique()])
        for r in tr:
            a, b = by[r], by[perm[r]]
            na, nb = a.n0.iloc[0], b.n0.iloc[0]
            ka, kb = a.n_nodes.iloc[0] * len(a), b.n_nodes.iloc[0] * len(b)
            nl[na:na + ka] = D["node_lab"][nb:nb + kb] if ka == kb else np.nan
        D["node_lab"] = nl


STAGE_KEEP = {   # generic columns kept per FEATURES.md stage (tier <= k); everything else zeroed
    "S0": {"edge": ["volume", "direct_volume", "bcast_volume", "responsiveness", "reciprocity", "new_contact"],
           "node": ["unanswered_share", "role_external"]},
}
STAGE_KEEP["S1"] = {"edge": STAGE_KEEP["S0"]["edge"] + ["escalation_lex"], "node": STAGE_KEEP["S0"]["node"]}
STAGE_KEEP["S2"] = {"edge": STAGE_KEEP["S1"]["edge"] + ["success_claim", "workaround_request", "verification",
                                                        "frustration"],
                    "node": STAGE_KEEP["S1"]["node"] + ["frustration_own"]}


def restrict_stage(D, stage):
    if not stage or stage == "S3":
        return
    keep = STAGE_KEEP[stage]
    ec, nc = list(D["ecols"]), list(D["ncols"])
    EF, X = D["EF"].copy(), D["X"].copy()
    for i, c in enumerate(ec):
        if c not in keep["edge"]:
            EF[:, i] = 0.0
    for i, c in enumerate(nc):
        if c not in keep["node"] and c not in ("tests_failed", "escalated_unresolved"):
            X[:, i] = 0.0
    D["EF"], D["X"] = EF, X


class Hybrid:
    def __init__(self, data_dir, lex=False, stage2="est+mem", cache=True, judge_ef=None, ica=0, control=None,
                 stage=None, tool=False, test_data=None):
        self.ica = ica
        self.tag = os.path.abspath(data_dir) + ("lex" if lex else "") + (control or "") + (stage or "") + \
            ("tool" if tool else "") + (os.path.abspath(test_data) if test_data else "")
        self.D = H.load(data_dir, graphs=True)
        S = self.D["S"]
        if control:
            apply_control(self.D, control)
            cache = False
        if stage or tool:
            restrict_stage(self.D, stage)
            cache = False
        self.tool = tool
        cp = os.path.join(data_dir, f"node_table{'_lex' if lex else ''}.pkl")
        if cache and os.path.exists(cp) and judge_ef is None:
            self.NT, self.ncols = pickle.load(open(cp, "rb"))
        else:
            self.NT, self.ncols = NF.build_node_table(self.D, S, lex=lex, judge_ef=judge_ef, tool=tool)
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
        self.NT_test = None
        if test_data:      # judge swap: test rows use another dataset's features (same runs / nodes / edges)
            Dt = H.load(test_data, graphs=True)
            assert len(Dt["X"]) == len(self.D["X"]) and (Dt["ES"] == self.D["ES"]).all()
            if stage:
                restrict_stage(Dt, stage)
            self.NT_test, c2 = NF.build_node_table(Dt, Dt["S"], lex=lex, tool=tool)
            assert c2 == self.ncols

    def stage1(self, tr_snaps, te_snaps, seed=0):
        """Stage-1 node probabilities, cached on disk by (train set, test set, seed, ica, feature table)."""
        import hashlib
        key = hashlib.md5(np.sort(tr_snaps).tobytes() + np.sort(te_snaps).tobytes() +
                          f"{seed}-{self.ica}-{len(self.ncols)}-{self.tag}".encode()).hexdigest()[:16]
        cp = os.path.join(CACHE, f"{key}.npz")
        if os.path.exists(cp):
            z = np.load(cp)
            return z["ps"], z["pf"]
        NT = self.NT
        if self.NT_test is not None:
            NT = self.NT.copy()
            m = np.isin(NT.snap.values, te_snaps)
            NT.loc[m, self.ncols] = self.NT_test.loc[m, self.ncols].values
        if self.ica:
            ps, pf = NF.node_stage_ica(NT, self.ncols, self.node_lab, self.S, self.D, tr_snaps, te_snaps, seed,
                                       rounds=self.ica)
        else:
            ps, pf, _ = NF.node_stage(NT, self.ncols, self.node_lab, self.S, tr_snaps, te_snaps, seed=seed)
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


class FinalHybrid:
    """Trained-on-all-night_train hybrid bundle (stage-1 node models, stage-2 GBM, per seed), applicable to any
    dataset directory built by build_dataset.py."""

    def __init__(self, ica=0, stage2="est", s2=None, seeds=(0, 1, 2), extra_cols=(), target="y3"):
        self.ica, self.stage2, self.s2, self.seeds, self.extra_cols, self.target = ica, stage2, s2 or {}, list(seeds), \
            list(extra_cols), target

    def fit(self, data_dir):
        hy = Hybrid(data_dir, stage2="est", ica=self.ica)
        S = hy.S
        tr = H.train_rows(S, self.target).values
        tr_snaps = S.snap[S.run.isin(S.run[tr].unique())].values
        self.ncols = hy.ncols
        self.models = []
        y = S[self.target].values
        for sd in self.seeds:
            ps, pf, nm = NF.node_stage_ica(hy.NT, hy.ncols, hy.node_lab, S, hy.D, tr_snaps, tr_snaps, sd,
                                           rounds=self.ica, return_models=True)
            GF = NF.graph_from_nodes(ps, pf, hy.NT, hy.D, S).reset_index(drop=True)
            X = pd.concat([GF, hy.D["T"][self.extra_cols].reset_index(drop=True)], axis=1)
            self.gcols = list(X.columns)
            m2 = hgb2(sd, **self.s2).fit(X.values[tr], y[tr])
            self.models.append((nm, m2))
        return self

    def predict(self, data_dir):
        D = H.load(data_dir, graphs=True)
        S = D["S"]
        NT, cols = NF.build_node_table(D, S)
        assert cols == self.ncols
        sc, cn = [], []
        for nm, m2 in self.models:
            ps, pf = NF.apply_node_models(nm, NT, cols, D, S)
            GF = NF.graph_from_nodes(ps, pf, NT, D, S).reset_index(drop=True)
            X = pd.concat([GF, D["T"][self.extra_cols].reset_index(drop=True)], axis=1)
            sc.append(m2.predict_proba(X[self.gcols].values)[:, 1])
            cn.append(GF.est_count.values)
        return pd.DataFrame({"run": S.run.values, "round": S["round"].values, "score": np.mean(sc, 0),
                             "count": np.mean(cn, 0)})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "..", "gnn_opt_data", "night"))
    ap.add_argument("--name", required=True)
    ap.add_argument("--stage2", default="est+mem")
    ap.add_argument("--s2", default="{}")
    ap.add_argument("--lex", action="store_true")
    ap.add_argument("--ica", type=int, default=0, help="iterative-classification rounds (neighbour propagation)")
    ap.add_argument("--stage", default=None, help="S0|S1|S2 feature-stage ablation")
    ap.add_argument("--tool", action="store_true", help="+ tool-event node features (ablation)")
    ap.add_argument("--clock", action="store_true", help="+ round index in stage 2 (ablation)")
    ap.add_argument("--test-data", default=None, help="judge swap: dataset dir whose features are used for test rows")
    ap.add_argument("--control", default=None, help="rewire | shuffle_edges | shuffle_edges_global | shuffle_labels")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--target", default="y3")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--predict-splits", default="night_val")
    a = ap.parse_args()
    t0 = time.time()
    hy = Hybrid(a.data, lex=a.lex, stage2=a.stage2, ica=a.ica, control=a.control, stage=a.stage, tool=a.tool,
                test_data=a.test_data)
    if a.clock:
        hy.tcols = list(hy.tcols) + ["t"]
    S = hy.S
    seeds = [int(s) for s in a.seeds.split(",")]
    s2 = json.loads(a.s2)

    def fp(tr, te):
        r = [hy.fit_predict(tr, te, a.target, s, s2) for s in seeds]
        return np.mean([x[0] for x in r], 0), np.mean([x[1] for x in r], 0)

    if not a.final:
        P = H.run_cv(S, fp, target=a.target)
        P.to_csv(os.path.join(HERE, "preds", "cv", f"{a.name}.csv"), index=False, float_format="%.5g")
        S_true = H.load(a.data, table=False)["S"]          # controls may have permuted labels in hy.S
        cs = H.cv_summary(S_true, P, a.target)
        print(json.dumps({"name": a.name, "select": round(cs["select"], 4), "id_auroc": round(cs["id_auroc"], 4),
                          "id_auprc": round(cs["id_auprc"], 4), "lodo_mean": round(cs["lodo_mean"], 4),
                          "lodo_min": round(cs["lodo_min"], 4), "lodo": {k: round(v, 3) for k, v in cs["lodo"].items()},
                          "minutes": round((time.time() - t0) / 60, 1)}))
        with open(os.path.join(HERE, "preds", "cv_log.jsonl"), "a") as f:
            f.write(json.dumps({"name": a.name, **cs, "stage2": a.stage2, "s2": s2, "ica": a.ica, "control": a.control, "stage": a.stage, "tool": a.tool, "clock": a.clock,
                                "test_data": a.test_data, "lex": a.lex, "seeds": seeds,
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
