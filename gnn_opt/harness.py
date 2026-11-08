"""Shared harness: dataset loading, fold file, CV driver for any model that maps (train rows) -> (test scores).

A model plugs in by writing a predictions CSV (see HARNESS.md):
  CV file   : run, round, score [, count] , fold          (fold = id<r>_<k> or hold_<domain>; test-fold rows only)
  eval file : run, round, score [, count]                 (model trained on all of night_train)
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

import metrics as M

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDS = os.path.join(HERE, "folds.json")
TRAIN_SPLIT = "night_train"


def load(data_dir, table=True, graphs=False):
    S = pd.read_csv(os.path.join(data_dir, "snapshots.csv"), low_memory=False)
    out = {"S": S, "runs": pd.read_csv(os.path.join(data_dir, "runs.csv")),
           "schema": json.load(open(os.path.join(data_dir, "schema.json")))}
    if table and os.path.exists(os.path.join(data_dir, "table.csv")):
        out["T"] = pd.read_csv(os.path.join(data_dir, "table.csv"))
        assert (out["T"].snap.values == S.snap.values).all()
    if graphs:
        z = np.load(os.path.join(data_dir, "graphs.npz"), allow_pickle=False)
        out.update({k: z[k] for k in z.files})
    return out


def make_folds(runs: pd.DataFrame, path=FOLDS, k=5, repeats=2, seed=0):
    tr = runs[(runs.split == TRAIN_SPLIT) & (runs.arm == "control")]
    f = {"train_split": TRAIN_SPLIT, "train_cfgs": sorted(tr.cfg.unique()),
         "id": {n: sorted(c) for n, c in M.id_folds(tr, k, repeats, seed)},
         "lodo": {n: sorted(c) for n, c in M.lodo_folds(tr)},
         "lodo_def": [list(x) for x in M.LODO],
         "note": "test-fold configs per fold; train = train_cfgs minus test cfgs. id<r>_<k>: repeat r, fold k "
                 "(StratifiedGroupKFold by config, stratified by 'config tipped at least once'). hold_*: leave-one-"
                 "domain-out over hidden factors (used ONLY for splitting)."}
    json.dump(f, open(path, "w"), indent=1)
    return f


def folds(path=FOLDS):
    return json.load(open(path))


def train_rows(S, target="y3"):
    return (S.split == TRAIN_SPLIT) & (S["eval"] == 1) & S[target].notna()


def run_cv(S, fit_predict, target="y3", which=("id", "lodo"), fold_file=FOLDS, verbose=False):
    """fit_predict(train_mask, test_mask) -> scores (or (scores, counts)) for test rows. Returns CV preds frame."""
    F = folds(fold_file)
    base = train_rows(S, target)
    out = []
    for kind in which:
        for name, te_cfgs in F[kind].items():
            te = base & S.cfg.isin(te_cfgs)
            tr = base & ~S.cfg.isin(te_cfgs)
            r = fit_predict(tr.values, te.values)
            sc, cn = (r if isinstance(r, tuple) else (r, None))
            df = pd.DataFrame({"run": S.run[te].values, "round": S["round"][te].values, "score": sc, "fold": name})
            if cn is not None:
                df["count"] = cn
            out.append(df)
            if verbose:
                print(f"  {name}: AUROC {M.auroc(S[target][te], sc):.3f}", flush=True)
    return pd.concat(out, ignore_index=True)


def cv_summary(S, P, target="y3"):
    """Summary of a CV predictions frame: pooled ID AUROC/AUPRC per repeat (mean), LODO per fold, selection score."""
    lab = S[["run", "round", target]].rename(columns={target: "y"})
    P = P.merge(lab, on=["run", "round"], how="left")
    idm = P.fold.str.startswith("id")
    reps = P[idm].fold.str.split("_").str[0]
    id_au = [M.auroc(g.y, g.score) for _, g in P[idm].groupby(reps)]
    id_pr = [M.auprc(g.y, g.score) for _, g in P[idm].groupby(reps)]
    lodo = {f: M.auroc(g.y, g.score) for f, g in P[~idm].groupby("fold")}
    lodo_pr = {f: M.auprc(g.y, g.score) for f, g in P[~idm].groupby("fold")}
    res = {"id_auroc": float(np.mean(id_au)) if id_au else np.nan, "id_auprc": float(np.mean(id_pr)) if id_pr else np.nan,
           "lodo": lodo, "lodo_auprc": lodo_pr}
    if lodo:
        v = np.array(list(lodo.values()))
        res.update({"lodo_mean": float(np.nanmean(v)), "lodo_min": float(np.nanmin(v)),
                    "select": M.selection_score(res)})
    return res


def id_oof(P):
    """Repeat-averaged ID out-of-fold predictions (one row per (run, round))."""
    Q = P[P.fold.str.startswith("id")]
    cols = ["score"] + (["count"] if "count" in Q else [])
    return Q.groupby(["run", "round"], as_index=False)[cols].mean()
