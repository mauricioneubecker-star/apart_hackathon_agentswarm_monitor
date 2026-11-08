#!/usr/bin/env python3
"""One command for any runs_* directory (same file format): build snapshots, predict with the final models, print
the metrics table (if labels exist).

  python3 gnn_opt/predict.py --runs sim_dataset/runs_new                       # name = basename of the runs dir
  python3 gnn_opt/predict.py --runs sim_dataset/runs_new --splits all --baselines --boot 1000

Models (gnn_opt/weights/): final_hybrid.pkl (headline), final_gnn.npz (numpy GNN, optional, --gnn), plus the
config-free baselines refit on night_train (--baselines: hgb_bag+graph = hand-built aggregates, edge monitor,
pairwise, oracle). Predictions: gnn_opt/preds/apply/<name>/<model>.csv. Thresholds for R@5%FPR come from the
training CV of each model (stored in the bundle / thresholds.json).
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--data-root", default=os.path.join(REPO, "gnn_opt_data"))
    ap.add_argument("--train-data", default=os.path.join(REPO, "gnn_opt_data", "night"))
    ap.add_argument("--splits", default="all")
    ap.add_argument("--baselines", action="store_true")
    ap.add_argument("--gnn", action="store_true")
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    name = a.name or os.path.basename(os.path.normpath(a.runs[0]))
    out_data = os.path.join(a.data_root, name)
    py = sys.executable
    if a.rebuild or not os.path.exists(os.path.join(out_data, "snapshots.csv")):
        subprocess.check_call([py, os.path.join(HERE, "build_dataset.py"), "--runs", *a.runs, "--out", out_data])
    od = os.path.join(HERE, "preds", "apply", name)
    os.makedirs(od, exist_ok=True)
    thr = json.load(open(os.path.join(HERE, "weights", "thresholds.json")))
    import hybrid  # noqa: E402
    bundle = pickle.load(open(os.path.join(HERE, "weights", "final_hybrid.pkl"), "rb"))
    bundle.predict(out_data).to_csv(os.path.join(od, "final_hybrid.csv"), index=False, float_format="%.5g")
    files, names, ths = [os.path.join(od, "final_hybrid.csv")], ["final_hybrid"], [str(thr.get("final_hybrid", ""))]
    if a.gnn and os.path.exists(os.path.join(HERE, "weights", "final_gnn.npz")):
        import gnn_apply  # noqa: E402
        gnn_apply.apply(os.path.join(HERE, "weights", "final_gnn.npz"), out_data).to_csv(
            os.path.join(od, "final_gnn.csv"), index=False, float_format="%.5g")
        files.append(os.path.join(od, "final_gnn.csv")); names.append("final_gnn"); ths.append(str(thr.get("final_gnn", "")))
    if a.baselines:
        bl = ["hgb_bag+graph", "hgb_pairwise", "hgb_bag", "hgb_struct", "hgb_clock", "oracle_risk+clock"]
        subprocess.check_call([py, os.path.join(HERE, "baselines.py"), "--data", a.train_data, "--only", ",".join(bl),
                               "--no-cv", "--predict-splits", "night_val", "--apply", out_data])
        for b in bl:
            files.append(os.path.join(HERE, "preds", "apply", name, f"{b}.csv")); names.append(b)
            ths.append(str(thr.get(b, "")))
    cmd = [py, os.path.join(HERE, "evaluate.py"), "--data", out_data, "--preds", *files, "--names", ",".join(names),
           "--splits", a.splits, "--boot", str(a.boot), "--thr", ",".join(ths), "--pairs",
           "--out", os.path.join(od, "metrics.csv")]
    subprocess.call(cmd)


if __name__ == "__main__":
    main()
