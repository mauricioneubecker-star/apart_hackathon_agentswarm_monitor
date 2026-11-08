#!/usr/bin/env python3
"""Final hybrid monitor: GNN seed ensemble (trained on all of night_train) + HGB (hgb_bag+graph+mem), logit blend.

  python3 gnn_opt_torch/final.py --name cloud_final --cfg '{"tmem":"gru","gtemp":"none","epochs":30}' --seeds 5 \
      --gnn-cv preds/cv/b_rgine_ngru.csv --w-gnn 0.5
Writes
  models/<name>_gnn.pt                  GNN ensemble (cfg, states, training normalisation)
  preds/eval/<name>_gnn.csv             GNN scores for every snapshot of --data
  preds/eval/<name>.csv                 hybrid scores (logit blend with HGB) for every snapshot
  preds/cv/<name>.csv                   hybrid CV file (blend of --gnn-cv and the HGB CV file; for the 5%-FPR threshold)
No evaluation here (looks at night_val / test are done explicitly with gnn_opt/evaluate.py and counted).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import pandas as pd
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import train as T  # noqa: E402
from blend import blend  # noqa: E402

HGB = "hgb_bag+graph+mem"


def hgb_preds(data, out_csv, apply_dir=None):
    """HGB trained on night_train of `data`; predictions for all non-train splits (+ train rows via CV file)."""
    cmd = [sys.executable, os.path.join(REPO, "gnn_opt", "baselines.py"), "--data", data, "--only", HGB, "--no-cv",
           "--predict-splits", "all", "--tag", "__final_tmp"]
    if apply_dir:
        cmd += ["--apply", apply_dir]
    subprocess.run(cmd, check=True)
    src = os.path.join(REPO, "gnn_opt", "preds", "eval", f"{HGB}__final_tmp.csv")
    os.replace(src, out_csv)
    if apply_dir:
        return os.path.join(REPO, "gnn_opt", "preds", "apply", os.path.basename(apply_dir.rstrip("/")),
                            f"{HGB}__final_tmp.csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "gnn_opt_data", "night"))
    ap.add_argument("--name", default="cloud_final")
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--gnn-cv", required=True, help="CV file of the same GNN cfg (for the hybrid CV file)")
    ap.add_argument("--w-gnn", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    cfg = json.loads(a.cfg)
    cfg["seeds"] = a.seeds
    D = T.get_data(a.data, {**T.DEFAULT, **cfg}["feat"], {**T.DEFAULT, **cfg}["clock"])
    tr = [i for i, r in enumerate(D.runs) if r["split"] == T.TRAIN_SPLIT]
    G, states, norm = T.fit_models(a.data, cfg, tr, a.seed, keep_states=True, pred_runs_idx=list(range(len(D.runs))))
    os.makedirs(os.path.join(HERE, "models"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "preds", "eval"), exist_ok=True)
    # keep the last 3 snapshot states per seed (file size); predictions above use all swa_last snapshots
    k = {**T.DEFAULT, **cfg}["swa_last"]
    keep = [st for i, st in enumerate(states) if i % k >= k - 3]
    torch.save({"cfg": {**T.DEFAULT, **cfg}, "states": keep, "norm": norm, "w_gnn": a.w_gnn},
               os.path.join(HERE, "models", f"{a.name}_gnn.pt"))
    G.to_csv(os.path.join(HERE, "preds", "eval", f"{a.name}_gnn.csv"), index=False)
    hcsv = os.path.join(HERE, "preds", "eval", f"{HGB}__allsplits.csv")
    if not os.path.exists(hcsv):
        hgb_preds(a.data, hcsv)
    Hh = pd.read_csv(hcsv)
    Gm = G.merge(Hh[["run", "round"]], on=["run", "round"])          # non-train rows
    hyb = blend([Gm, Hh], [a.w_gnn, 1 - a.w_gnn], "logit")
    hyb.to_csv(os.path.join(HERE, "preds", "eval", f"{a.name}.csv"), index=False)
    cvg = pd.read_csv(os.path.join(HERE, a.gnn_cv) if not os.path.isabs(a.gnn_cv) else a.gnn_cv)
    cvh = pd.read_csv(os.path.join(REPO, "gnn_opt", "preds", "cv", f"{HGB}.csv"))
    hcv = blend([cvg, cvh], [a.w_gnn, 1 - a.w_gnn], "logit")
    hcv.to_csv(os.path.join(HERE, "preds", "cv", f"{a.name}.csv"), index=False)
    print("wrote", a.name, len(G), len(hyb), len(hcv))


if __name__ == "__main__":
    main()
