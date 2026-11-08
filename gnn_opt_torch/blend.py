#!/usr/bin/env python3
"""Blend prediction files (same harness folds / same rows): mean of per-fold rank-normalised or raw scores.

  python3 gnn_opt_torch/blend.py --preds a.csv b.csv --weights 0.5 0.5 --out ab.csv [--mode rank|prob|logit]
CV files: blending is done within each fold (rank normalisation within fold). Eval files: rank within the whole file
is NOT used (it would depend on the evaluated batch); for eval files use --mode prob or logit.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd


def blend(frames, weights, mode="prob"):
    key = ["run", "round"] + (["fold"] if "fold" in frames[0] else [])
    out = frames[0][key].copy()
    acc = 0.0
    for P, w in zip(frames, weights):
        Q = out.merge(P, on=key, how="left")
        s = Q.score.values.astype(float)
        if mode == "rank":
            s = Q.groupby("fold").score.rank(pct=True).values if "fold" in Q else pd.Series(s).rank(pct=True).values
        elif mode == "logit":
            s = np.log(np.clip(s, 1e-6, 1 - 1e-6) / (1 - np.clip(s, 1e-6, 1 - 1e-6)))
        acc = acc + w * s
    acc = acc / sum(weights)
    if mode == "logit":
        acc = 1 / (1 + np.exp(-acc))
    out["score"] = acc
    if all("count" in P for P in frames[:1]):
        out = out.merge(frames[0][key + ["count"]], on=key, how="left")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", nargs="+", required=True)
    ap.add_argument("--weights", nargs="+", type=float, default=None)
    ap.add_argument("--mode", default="prob")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fr = [pd.read_csv(p) for p in a.preds]
    w = a.weights or [1.0] * len(fr)
    blend(fr, w, a.mode).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
