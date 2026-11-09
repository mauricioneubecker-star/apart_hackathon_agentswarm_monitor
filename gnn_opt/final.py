#!/usr/bin/env python3
"""Fit the final headline model on all night_train rows and save it.

  python3 gnn_opt/final.py            # -> weights/final_hybrid.pkl, weights/thresholds.json, preds/eval/final_hybrid.csv
Selected configuration (stage-2 sweep on 18 CV folds, selection score = mean(ID AUROC, LODO mean, LODO min)):
  stage 1: per-agent HGB (depth 4, 200 iters) on the causal node table, no ICA
  stage 2: HGB depth 2, 100 iters, min_samples_leaf 80, l2 3.0 on the 22 estimated-count/exposure features
  seeds 0, 1, 2 (stage-1 and stage-2 models averaged)
"""
from __future__ import annotations

import json
import os
import pickle
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402
import hybrid as HY  # noqa: E402
import metrics as M  # noqa: E402

FINAL = dict(ica=0, stage2="est", s2={"depth": 2, "iters": 100, "leaf": 80, "l2": 3.0}, seeds=(0, 1, 2))
THR_MODELS = ["final_hybrid", "hgb_bag+graph", "hgb_bag+graph+mem", "hgb_pairwise", "hgb_bag", "hgb_struct",
              "hgb_clock", "oracle_risk+clock", "edge_monitor_max", "edge_monitor_top3", "lr_bag+graph",
              "final_gnn"]


def thresholds(S):
    out = {}
    lab = S[(S["eval"] == 1) & S.y3.notna()]
    for n in THR_MODELS:
        f = os.path.join(HERE, "preds", "cv", f"{n}.csv")
        if os.path.exists(f):
            o = H.id_oof(pd.read_csv(f)).merge(lab, on=["run", "round"])
            out[n] = float(M.thr_at_fpr(o.y3.values, o.score.values))
    return out


def main():
    data = os.path.join(HERE, "..", "gnn_opt_data", "night")
    S = H.load(data, table=False)["S"]
    os.makedirs(os.path.join(HERE, "weights"), exist_ok=True)
    json.dump(thresholds(S), open(os.path.join(HERE, "weights", "thresholds.json"), "w"), indent=1)
    fh = HY.FinalHybrid(**FINAL).fit(data)
    pickle.dump(fh, open(os.path.join(HERE, "weights", "final_hybrid.pkl"), "wb"))
    P = fh.predict(data)
    P = P[P.run.isin(S.run[S.split != H.TRAIN_SPLIT])]
    P.to_csv(os.path.join(HERE, "preds", "eval", "final_hybrid.csv"), index=False, float_format="%.5g")
    print("saved weights/final_hybrid.pkl, thresholds.json, preds/eval/final_hybrid.csv")


if __name__ == "__main__":
    main()
