#!/usr/bin/env python3
"""CV / final training for the numpy GNN.

  python3 gnn_opt/run_gnn.py --name gnn_base --cfg '{"h":32}' --seeds 0,1,2            # all 18 folds (CV file)
  python3 gnn_opt/run_gnn.py --name gnn_base --cfg ... --folds id                       # only ID folds
  python3 gnn_opt/run_gnn.py --name gnn_base --cfg ... --final --predict-splits night_val   # train on all train
  options: --feats gen|gen+lex|gen+tool|S0|S1|S2 ; --control rewire|shuffle_edges|shuffle_labels ; --target y3|y5|...
Writes gnn_opt/preds/cv/<name>.csv or gnn_opt/preds/eval/<name>.csv (+ weights .npz with --final).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402
import train as TR  # noqa: E402

G = {}


def _init(data_dir, feats, control, target, shuffle_seed):
    D = TR.Data(data_dir, feats, control=control if control != "shuffle_labels" else None)
    if control == "shuffle_labels":
        # permute labels across training runs (whole label sequences, so prevalence/time structure is kept)
        S = D.S
        rng = np.random.default_rng(shuffle_seed)
        tr_runs = S[S.split == H.TRAIN_SPLIT].run.unique()
        perm = dict(zip(tr_runs, rng.permutation(tr_runs)))
        for col in [target, "risk", "eval"]:
            by = {r: g[col].values for r, g in S.groupby("run")}
            S[col] = np.concatenate([by[perm.get(r, r)] for r in S.run.unique()])
        # node labels are shuffled with the same run permutation
        nl = D.node_lab.copy()
        for r in tr_runs:
            a, b = D.run_block(r), D.run_block(perm[r])
            nl[a["n0"]:a["n1"]] = D.node_lab[b["n0"]:b["n1"]][: a["n1"] - a["n0"]] if (b["n1"] - b["n0"]) == (a["n1"] - a["n0"]) else np.nan
        D.node_lab = nl
        D._cache = {}
    G["D"] = D


def _job(args):
    name, tr_runs, te_runs, cfg, seeds, target, snap_ens = args
    D = G["D"]
    t0 = time.time()
    P, _ = TR.ensemble_fit_predict(D, tr_runs, te_runs, cfg, seeds, target, snapshot_ens=snap_ens)
    P["fold"] = name
    return P, name, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "..", "gnn_opt_data", "night"))
    ap.add_argument("--name", required=True)
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--feats", default="gen")
    ap.add_argument("--control", default=None)
    ap.add_argument("--target", default="y3")
    ap.add_argument("--folds", default="id,lodo")
    ap.add_argument("--only-folds", default=None, help="comma list of fold names (dev runs)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--snap-ens", type=int, default=0)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--predict-splits", default="night_val")
    ap.add_argument("--apply", nargs="*", default=[])
    a = ap.parse_args()
    cfg = json.loads(a.cfg)
    seeds = [int(s) for s in a.seeds.split(",")]
    _init(a.data, a.feats, a.control, a.target, 123)
    D = G["D"]
    S = D.S
    base = H.train_rows(S, a.target)
    train_runs_all = list(dict.fromkeys(S.run[base]))
    if not a.final:
        F = H.folds()
        jobs = []
        for kind in a.folds.split(","):
            for fname, te_cfgs in F[kind].items():
                if a.only_folds and fname not in a.only_folds.split(","):
                    continue
                te_runs = [r for r in train_runs_all if S.cfg[S.run == r].iloc[0] in te_cfgs]
                tr_runs = [r for r in train_runs_all if r not in set(te_runs)]
                jobs.append((fname, tr_runs, te_runs, cfg, seeds, a.target, a.snap_ens))
        t0 = time.time()
        outs = []
        with Pool(a.workers) as pool:
            for P, fname, dt in pool.imap_unordered(_job, jobs):
                outs.append(P)
        P = pd.concat(outs, ignore_index=True)
        P = P.merge(S[["snap", "run", "round"]], on="snap")
        # only test-fold rows with labels are needed, keep all for completeness of temporal analysis
        P = P[["run", "round", "score", "count", "fold"]]
        os.makedirs(os.path.join(HERE, "preds", "cv"), exist_ok=True)
        P.to_csv(os.path.join(HERE, "preds", "cv", f"{a.name}.csv"), index=False, float_format="%.5g")
        Pl = P.merge(S[["run", "round", "eval", a.target]], on=["run", "round"])
        Pl = Pl[(Pl["eval"] == 1) & Pl[a.target].notna()]
        cs = H.cv_summary(S, Pl.drop(columns=["eval", a.target]), a.target)
        if a.only_folds:
            import metrics as M
            print(a.name, {f: round(M.auroc(g[a.target], g.score), 3) for f, g in Pl.groupby("fold")}, flush=True)
            return
        print(json.dumps({"name": a.name, "select": round(cs["select"], 4), "id_auroc": round(cs["id_auroc"], 4),
                          "id_auprc": round(cs["id_auprc"], 4), "lodo_mean": round(cs["lodo_mean"], 4),
                          "lodo_min": round(cs["lodo_min"], 4),
                          "lodo": {k: round(v, 3) for k, v in cs["lodo"].items()},
                          "minutes": round((time.time() - t0) / 60, 1), "cfg": cfg, "seeds": seeds,
                          "feats": a.feats, "control": a.control, "target": a.target}), flush=True)
        with open(os.path.join(HERE, "preds", "cv_log.jsonl"), "a") as f:
            f.write(json.dumps({"name": a.name, **{k: (v if not isinstance(v, dict) else v) for k, v in cs.items()},
                                "cfg": cfg, "seeds": seeds, "feats": a.feats, "control": a.control,
                                "target": a.target}) + "\n")
        return
    # final: train on all night_train runs, predict requested splits (+ new datasets)
    sps = None if a.predict_splits == "all" else a.predict_splits.split(",")
    pr = list(dict.fromkeys(S.run[(S.split != H.TRAIN_SPLIT) if sps is None else S.split.isin(sps)]))
    P, models = TR.ensemble_fit_predict(D, train_runs_all, pr, cfg, seeds, a.target, snapshot_ens=a.snap_ens)
    P = P.merge(S[["snap", "run", "round"]], on="snap")[["run", "round", "score", "count"]]
    os.makedirs(os.path.join(HERE, "preds", "eval"), exist_ok=True)
    P.to_csv(os.path.join(HERE, "preds", "eval", f"{a.name}.csv"), index=False, float_format="%.5g")
    wdir = os.path.join(HERE, "weights")
    os.makedirs(wdir, exist_ok=True)
    blob = {"cfg": json.dumps({**models[0].cfg, "seeds": seeds, "feats": a.feats, "target": a.target}),
            "mu_n": D.mu_n, "sd_n": D.sd_n, "mu_e": D.mu_e, "sd_e": D.sd_e}
    for i, m in enumerate(models):
        sds = m.snapshots if m.snapshots else [m.state_dict()]
        for j, sd in enumerate(sds):
            for k, v in sd.items():
                blob[f"m{i}_{j}/{k}"] = v
    np.savez_compressed(os.path.join(wdir, f"{a.name}.npz"), **blob)
    print("wrote", f"preds/eval/{a.name}.csv", f"weights/{a.name}.npz")


if __name__ == "__main__":
    main()
