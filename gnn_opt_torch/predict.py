#!/usr/bin/env python3
"""One command: new runs_* directory -> snapshot dataset -> GNN monitor predictions -> full metrics table.

  python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_<new> [--model gnn_opt_torch/models/final.pt] \
      [--thr-from gnn_opt_torch/preds/cv/final.csv] [--splits all] [--no-eval]

Steps: (1) gnn_opt/build_dataset.py --runs <dir> --out gnn_opt_data/<name> (skipped if it exists, --rebuild to force)
(2) load the saved ensemble (cfg + seed/snapshot states + training normalisation; trained on night_train only)
(3) write gnn_opt_torch/preds/new/<name>__<model>.csv (run, round, score, count) for every snapshot
(3b) with --blend (default hgb_bag+graph+mem): the GBM refit on all of night_train (gnn_opt/baselines.py --apply)
     predicts the batch, and the logit blend (GNN weight from the model file, default 0.3) is written next to it
(4) gnn_opt/evaluate.py --splits all on it (threshold for R@5%FPR from the model's training-CV file); the
    branch-arm divergence table is printed when the batch has branch arms.
Requires labels.json + graph_*.csv in each run (run.py jury / labels / features). Labels are only used by step 4.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import pandas as pd
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from tdata import Data  # noqa: E402
import train as T  # noqa: E402
from blend import blend  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--model", default=os.path.join(HERE, "models", "final.pt"))
    ap.add_argument("--thr-from", default=None)
    ap.add_argument("--data-out", default=None)
    ap.add_argument("--train-data", default=os.path.join(REPO, "gnn_opt_data", "night"),
                    help="night_train dataset dir (GBM refit for the blend)")
    ap.add_argument("--blend", default="hgb_bag+graph+mem", help="tabular baseline to blend with ('' = none)")
    ap.add_argument("--blend-w", type=float, default=None, help="GNN weight in the logit blend (default: from model)")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--no-eval", action="store_true")
    ap.add_argument("--target", default="y3")
    ap.add_argument("--splits", default="all", help="splits passed to evaluate.py (comma list or 'all')")
    a = ap.parse_args()
    name = os.path.basename(os.path.normpath(a.runs))
    dd = a.data_out or os.path.join(REPO, "gnn_opt_data", name)
    if a.rebuild or not os.path.exists(os.path.join(dd, "graphs.npz")):
        subprocess.run([sys.executable, os.path.join(REPO, "gnn_opt", "build_dataset.py"), "--runs", a.runs,
                        "--out", dd], check=True)
    M = torch.load(a.model, weights_only=False)
    members = M.get("members") or [{"cfg": M["cfg"], "states": M["states"], "norm": M["norm"]}]
    Ps = []
    for mb in members:     # ensemble of member configs (each: seed x snapshot/SWA states)
        D = Data(dd, mb["cfg"]["feat"], mb["cfg"]["clock"])
        Ps.append(T.predict_states(D, mb["cfg"], mb["states"], mb["norm"]))
    P = Ps[0][["run", "round"]].copy()
    for col in ("score", "count"):
        P[col] = sum(q[col].values for q in Ps) / len(Ps)
    mname = os.path.basename(a.model).replace(".pt", "")
    od = os.path.join(HERE, "preds", "new")
    os.makedirs(od, exist_ok=True)
    out = os.path.join(od, f"{name}__{mname}.csv")
    P.to_csv(out, index=False)
    print("wrote", out, len(P))
    outs, thrs = [out], [a.thr_from or os.path.join(HERE, "preds", "cv", f"{mname}.csv")]
    if a.blend:
        # hybrid: GBM refit on all of night_train (baselines.py --apply), logit blend with the GNN scores
        subprocess.run([sys.executable, os.path.join(REPO, "gnn_opt", "baselines.py"), "--data", a.train_data,
                        "--only", a.blend, "--no-cv", "--predict-splits", "night_val", "--tag", "__predict",
                        "--apply", dd], check=True)
        G = pd.read_csv(os.path.join(REPO, "gnn_opt", "preds", "apply", os.path.basename(os.path.normpath(dd)),
                                     f"{a.blend}__predict.csv"))
        w = a.blend_w if a.blend_w is not None else M.get("blend_w", 0.3)
        Bl = blend([P, G], [w, 1 - w], mode="logit")
        bname = f"{mname}+{a.blend}"
        outb = os.path.join(od, f"{name}__{bname}.csv")
        Bl.to_csv(outb, index=False)
        print("wrote", outb, len(Bl), f"(logit blend, GNN weight {w})")
        outs.append(outb)
        thrs.append(os.path.join(HERE, "preds", "cv", f"{bname}.csv"))
    if not a.no_eval:
        cmd = [sys.executable, os.path.join(REPO, "gnn_opt", "evaluate.py"), "--data", dd, "--preds", *outs,
               "--splits", a.splits, "--target", a.target]
        if all(os.path.exists(t) for t in thrs):
            cmd += ["--thr-from", *thrs]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
