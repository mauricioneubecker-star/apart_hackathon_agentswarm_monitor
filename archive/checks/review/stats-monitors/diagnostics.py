#!/usr/bin/env python3
"""Descriptive diagnostics: how clock-like is each score (Spearman rho with the round t, all rows and negatives only),
and rank correlations between the main predictors (repeat-averaged OOF scores on the 3,370 rows)."""
from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statlib as L  # noqa: E402
from primary_stats import EXTRA, PRIMARY  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S, lab, cfgs = L.load_rows(a.data, a.base)
    folds = json.load(open(a.folds))
    P = {n: L.load_cv(os.path.join(a.preds, f), lab, folds)[0]["oof"] for n, f in {**PRIMARY, **EXTRA}.items()}
    neg = lab.y.values == 0
    rows = []
    for n, s in P.items():
        rows.append({"predictor": n, "rho_t_all": spearmanr(s, lab.t).statistic,
                     "rho_t_neg": spearmanr(s[neg], lab.t.values[neg]).statistic,
                     "rho_rtc_neg": spearmanr(s[neg], lab.rounds_to_cut.values[neg]).statistic})
    R = pd.DataFrame(rows)
    main6 = list(PRIMARY)
    C = pd.DataFrame({n: P[n] for n in main6}).corr(method="spearman")
    R.to_csv(os.path.join(a.out, "clock_likeness.csv"), index=False)
    C.to_csv(os.path.join(a.out, "rank_corr_main.csv"))
    pd.set_option("display.width", 200)
    print(R.round(3).to_string(index=False))
    print(C.round(3).to_string())


if __name__ == "__main__":
    main()
