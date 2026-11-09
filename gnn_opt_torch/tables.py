#!/usr/bin/env python3
"""Markdown tables from the CV summary logs (for RESULTS.md).

  python3 gnn_opt_torch/tables.py preds/screen_log.jsonl [--names s_base,s_gine] [--sort id_auroc]
Shows the last summary per name. Columns: ID AUROC / AUPRC (and selection score, LODO mean / worst when present),
cfg keys that differ from train.DEFAULT.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import train as T  # noqa: E402


def diff_cfg(cfg):
    return ", ".join(f"{k}={v}" for k, v in cfg.items() if T.DEFAULT.get(k) != v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--names", default=None)
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--sort", default=None)
    a = ap.parse_args()
    rows = {}
    for f in a.logs:
        for l in open(f):
            if l.strip():
                r = json.loads(l)
                if "name" in r:
                    rows[r["name"]] = r
    names = a.names.split(",") if a.names else list(rows)
    if a.prefix:
        names = [n for n in names if n.startswith(a.prefix)]
    R = [rows[n] for n in names if n in rows]
    has_sel = any(r.get("select") is not None for r in R)
    key = a.sort or ("select" if has_sel else "id_auroc")
    R.sort(key=lambda r: -(r.get(key) or 0))
    cols = (["select", "id_auroc", "id_auprc", "lodo_mean", "lodo_min"] if has_sel else ["id_auroc", "id_auprc"])
    print("| name | " + " | ".join(cols) + " | cfg (vs DEFAULT) |")
    print("|---" * (len(cols) + 2) + "|")
    for r in R:
        v = " | ".join("" if r.get(c) is None else f"{r[c]:.3f}" for c in cols)
        print(f"| {r['name']} | {v} | {diff_cfg(r.get('cfg', {}))} |")


if __name__ == "__main__":
    main()
