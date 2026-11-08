#!/usr/bin/env python3
"""Snapshot builder (framework-agnostic). One command per runs_* directory:

  python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night
  python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_new  --out gnn_opt_data/new      # any new batch
  python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night_ds --judge deepseek-v4-flash

Writes (see HARNESS.md for the exact schema):
  graphs.npz      node features X, edge index (ES, ED: global node rows), edge features EF, node labels, names
  snapshots.csv   one row per (run, round): offsets, graph labels (y3, y5, yrel3, yrel5, risk), split, group (cfg),
                  hidden factors (cat, seed, channels, model_mix, topology; ONLY for splitting / strata), eval mask
  runs.csv        one row per run
  table.csv       tabular per-snapshot features (baselines; same rows as snapshots.csv)
  schema.json     feature tiers: which columns are allowed in the headline model
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data  # noqa: E402
import tabular  # noqa: E402


def mixed_cfgs(runs):
    c = runs[runs.arm == "control"].groupby("cfg").tipped.mean()
    return sorted(c[(c > 0) & (c < 1)].index)


def export(D, out, table=True):
    os.makedirs(out, exist_ok=True)
    S = D["snaps"].copy()
    R = D["runs"]
    S.insert(0, "snap", np.arange(len(S)))
    S["e0"] = np.concatenate([[0], np.cumsum(S.n_edges.values)[:-1]])
    S = S.join(R[["run", "cfg", "rep", "arm", "branch_round", "tipped", "tip_round", "split", "cat", "seed",
                  "channels", "model_mix", "topology"]], on="run_i")
    S["round"] = S.t
    mx = mixed_cfgs(R)
    S["mixed"] = S.cfg.isin(mx).astype(int)
    S["eval"] = (S.y3.notna() & (S.dup == 0)).astype(int)
    S.to_csv(os.path.join(out, "snapshots.csv"), index=False)
    R.to_csv(os.path.join(out, "runs.csv"), index=False)
    np.savez_compressed(os.path.join(out, "graphs.npz"), X=D["X"], EF=D["EF"], ES=D["ES"], ED=D["ED"],
                        node_snap=D["node_snap"], node_lab=D["node_lab"], node_ext=D["node_ext"],
                        node_name=D["node_name"].astype(str), ecols=np.array(D["ecols"]), ncols=np.array(D["ncols"]),
                        prev=data.prev_index(D))
    schema = {
        "edge_cols": D["ecols"], "node_cols": D["ncols"],
        "headline_edge": data.E_GEN, "headline_node": data.N_GEN,
        "ablation_lexicon_edge": data.E_LEX, "ablation_lexicon_node": data.N_LEX, "ablation_tool_node": data.N_TOOL,
        "ablation_clock": "snapshots.csv:t",
        "stages": data.STAGE, "nan_columns": data.NAN_FLAG,
        "node_labels": ["violated_by_t", "violates_within_3 (NaN once violated / externals)"],
        "graph_labels": {"y3": "tip within 3 (primary)", "y5": "tip within 5", "yrel3": "relative theta, delta 3",
                         "yrel5": "relative theta, delta 5", "risk": "violator count at t (secondary target; NEVER input)"},
        "mixed_cfgs": mx, "n_snapshots": int(len(S)), "n_runs": int(len(R)),
    }
    json.dump(schema, open(os.path.join(out, "schema.json"), "w"), indent=1)
    if table:
        T = tabular.build_table(D, lex=True, tool=True)
        T.insert(0, "snap", np.arange(len(T)))
        T.to_csv(os.path.join(out, "table.csv"), index=False)
    return S


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--judge", default=None, help="single-judge features (needs gnn_opt/judge_swap.py output)")
    ap.add_argument("--no-table", action="store_true")
    a = ap.parse_args()
    D = data.build(a.runs, judge=a.judge)
    S = export(D, a.out, table=not a.no_table)
    ev = S[S["eval"] == 1]
    print(json.dumps({"snapshots": len(S), "eval_rows": len(ev), "pos_y3": int(ev.y3.sum()),
                      "splits": ev.groupby("split").y3.agg(["size", "sum"]).astype(int).to_dict("index")}, indent=1))


if __name__ == "__main__":
    main()
