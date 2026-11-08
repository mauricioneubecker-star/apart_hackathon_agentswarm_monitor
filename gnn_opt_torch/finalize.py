#!/usr/bin/env python3
"""Final model + hybrid from the chosen config (step 7). No test split is touched.

  python3 gnn_opt_torch/finalize.py --cfg '{...}' --cv-files preds/cv/a.csv preds/cv/a_s1.csv ... --name final \
      --blend hgb_bag+graph+mem --blend-w 0.3
1. CV file of the chosen model = mean score over the given seed CV files (same folds / rows) -> preds/cv/<name>.csv
   (used for the R@5%FPR threshold) and the blend CV file preds/cv/<name>+<blend>.csv (logit blend)
2. trains the chosen config (cfg['seeds'] seeds) on all of night_train, predicts every snapshot of the night data:
   preds/eval/<name>.csv, saves models/<name>.pt (cfg, states, normalisation, blend weight)
3. blend eval file preds/eval/<name>+<blend>.csv from the GBM eval file (trained on all of night_train, night_val rows)
The single night_val look is then: gnn_opt/evaluate.py --splits night_val (printed command).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import train as T  # noqa: E402
from blend import blend  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "gnn_opt_data", "night"))
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--cv-files", nargs="+", required=True)
    ap.add_argument("--name", default="final")
    ap.add_argument("--blend", default="hgb_bag+graph+mem")
    ap.add_argument("--blend-w", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    cfg = json.loads(a.cfg)
    cvd, evd = os.path.join(HERE, "preds", "cv"), os.path.join(HERE, "preds", "eval")
    os.makedirs(evd, exist_ok=True)
    # 1. seed-ensemble CV file + blend CV file
    fr = [pd.read_csv(f) for f in a.cv_files]
    key = ["run", "round", "fold"]
    E = fr[0][key].copy()
    for c in ("score", "count"):
        E[c] = sum(E[key].merge(f, on=key, how="left")[c].values for f in fr) / len(fr)
    E.to_csv(os.path.join(cvd, f"{a.name}.csv"), index=False)
    bname = f"{a.name}+{a.blend}"
    if a.blend:
        G = pd.read_csv(os.path.join(REPO, "gnn_opt", "preds", "cv", f"{a.blend}.csv"))
        blend([E, G], [a.blend_w, 1 - a.blend_w], mode="logit").to_csv(os.path.join(cvd, f"{bname}.csv"),
                                                                          index=False)
    # 2. final GNN on all of night_train
    c = {**T.DEFAULT, **cfg}
    D = T.get_data(a.data, c["feat"], c["clock"])
    tr = [i for i, r in enumerate(D.runs) if r["split"] == T.TRAIN_SPLIT]
    df, states, norm = T.fit_models(a.data, cfg, tr, a.seed, keep_states=True, pred_runs_idx=list(range(len(D.runs))))
    os.makedirs(os.path.join(HERE, "models"), exist_ok=True)
    torch.save({"cfg": c, "states": states, "norm": norm, "blend": a.blend, "blend_w": a.blend_w,
                "trained_on": "night_train (all 128 runs)", "cv_files": a.cv_files},
               os.path.join(HERE, "models", f"{a.name}.pt"))
    df.to_csv(os.path.join(evd, f"{a.name}.csv"), index=False)
    print("wrote", os.path.join(evd, f"{a.name}.csv"), len(df), "and", os.path.join(HERE, "models", f"{a.name}.pt"))
    # 3. blend eval file (GBM eval file covers night_val)
    if a.blend:
        G = pd.read_csv(os.path.join(REPO, "gnn_opt", "preds", "eval", f"{a.blend}.csv"))
        Q = df.merge(G[["run", "round"]], on=["run", "round"])
        blend([Q, G], [a.blend_w, 1 - a.blend_w], mode="logit").to_csv(os.path.join(evd, f"{bname}.csv"), index=False)
    print("night_val look:\n  python3 gnn_opt/evaluate.py --data gnn_opt_data/night --splits night_val --pairs --preds "
          f"gnn_opt_torch/preds/eval/{bname}.csv gnn_opt_torch/preds/eval/{a.name}.csv "
          f"gnn_opt/preds/eval/{a.blend}.csv gnn_opt/preds/eval/hgb_bag+graph.csv --thr-from "
          f"gnn_opt_torch/preds/cv/{bname}.csv gnn_opt_torch/preds/cv/{a.name}.csv gnn_opt/preds/cv/{a.blend}.csv "
          "gnn_opt/preds/cv/hgb_bag+graph.csv")


if __name__ == "__main__":
    main()
