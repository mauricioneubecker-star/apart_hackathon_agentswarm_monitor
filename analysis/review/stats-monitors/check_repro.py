#!/usr/bin/env python3
"""Step 1 check: evaluate.py output on the rebuilt dataset vs the published gnn_opt_torch/preds/cv_table_final.csv
(full precision) and vs the RESULTS.md step-4 markdown table (3 decimals)."""
from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd

NAME = {"final": "final_gnn_ens4", "final+hgb_bag+graph+mem": "blend(final+hgb_mem)"}
MD = {"final": "final GNN (2 cfg x 2 seeds)", "final+hgb_bag+graph+mem": "**blend: final GNN + hgb_bag+graph+mem**",
      "hgb_bag+graph+mem": "hgb_bag+graph+mem", "hgb_bag+graph": "hgb_bag+graph", "edge_monitor_top3": "edge_monitor_top3",
      "hgb_clock": "hgb_clock", "oracle_risk": "oracle_risk (reference)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mine", required=True)
    ap.add_argument("--published", required=True)
    ap.add_argument("--results-md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A = pd.read_csv(a.mine)
    P = pd.read_csv(a.published)
    A["key"] = A.model.map(lambda m: NAME.get(m, m))
    cols = [c for c in A.columns if c in P.columns and c not in ("model",)]
    res = {}
    for _, r in A.iterrows():
        q = P[P.model == r.key]
        if not len(q):
            res[r.model] = "not in published table"
            continue
        q = q.iloc[0]
        diffs = {c: abs(float(r[c]) - float(q[c])) for c in cols if pd.notna(r[c]) and pd.notna(q[c])}
        nan_mismatch = [c for c in cols if pd.isna(r[c]) != pd.isna(q[c])]
        res[r.model] = {"n_cols": len(diffs), "max_abs_diff": max(diffs.values()), "nan_mismatch": nan_mismatch}
    # markdown step-4 table: | model | select | ID AUROC | ID AUPRC | LODO mean | LODO worst | tAUROC | R@5%FPR | ...
    txt = open(a.results_md).read()
    sec = txt.split("## Step 4")[1].split("## Step 5")[0]
    rows = {}
    for line in sec.splitlines():
        if line.startswith("| ") and not line.startswith("| model") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 8 and re.match(r"^\**[0-9.]+\**$", cells[1]) and cells[0] not in rows:
                rows[cells[0]] = [float(c.strip("*")) for c in cells[1:8]]   # first table only (main step-4 table)
    md = {}
    for m, lbl in MD.items():
        r = A[A.model == m].iloc[0]
        mine = [r.select, r.ID_AUROC, r.ID_AUPRC, r.LODO_mean, r.LODO_min, r.tAUROC, r["R@5%FPR"]]
        pub = rows.get(lbl)
        md[m] = {"published_md": pub, "mine_rounded": [round(float(x), 3) for x in mine],
                 "all_equal_at_3dp": bool(pub is not None and np.allclose(np.round(mine, 3), pub, atol=5e-4 + 1e-9))}
    out = {"vs_cv_table_final_csv": res, "vs_results_md_step4": md}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
