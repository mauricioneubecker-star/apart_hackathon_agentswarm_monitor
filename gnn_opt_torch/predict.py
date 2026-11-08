#!/usr/bin/env python3
"""One command: new runs_* directory -> snapshot dataset -> GNN monitor predictions -> full metrics table.

  python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_<new> [--model gnn_opt_torch/models/final.pt] \
      [--thr-from gnn_opt_torch/preds/cv/final.csv] [--splits all] [--no-eval]

Steps: (1) gnn_opt/build_dataset.py --runs <dir> --out gnn_opt_data/<name> (skipped if it exists, --rebuild to force)
(2) load the saved ensemble (cfg + seed/snapshot states + training normalisation; trained on night_train only)
(3) write gnn_opt_torch/preds/new/<name>__<model>.csv (run, round, score, count) for every snapshot
(4) gnn_opt/evaluate.py --splits all on it (threshold for R@5%FPR from the model's training-CV file); the
    branch-arm divergence table is printed when the batch has branch arms.
Requires labels.json + graph_*.csv in each run (run.py jury / labels / features). Labels are only used by step 4.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from tdata import Data  # noqa: E402
import train as T  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--model", default=os.path.join(HERE, "models", "final.pt"))
    ap.add_argument("--thr-from", default=None)
    ap.add_argument("--data-out", default=None)
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
    cfg = M["cfg"]
    D = Data(dd, cfg["feat"], cfg["clock"])
    P = T.predict_states(D, cfg, M["states"], M["norm"])
    mname = os.path.basename(a.model).replace(".pt", "")
    os.makedirs(os.path.join(HERE, "preds", "new"), exist_ok=True)
    out = os.path.join(HERE, "preds", "new", f"{name}__{mname}.csv")
    P.to_csv(out, index=False)
    print("wrote", out, len(P))
    if not a.no_eval:
        thr = a.thr_from or os.path.join(HERE, "preds", "cv", f"{mname}.csv")
        cmd = [sys.executable, os.path.join(REPO, "gnn_opt", "evaluate.py"), "--data", dd, "--preds", out,
               "--splits", a.splits, "--target", a.target]
        if os.path.exists(thr):
            cmd += ["--thr-from", thr]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
