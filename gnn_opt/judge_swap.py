#!/usr/bin/env python3
"""Single-judge feature builds for the judge-swap augmentation / ablation (sim_dataset runs stay untouched).

  python3 gnn_opt/judge_swap.py --runs sim_dataset/runs_night --judge deepseek-v4-flash --cache gnn_opt_data/cache
  GNN_OPT_CACHE=gnn_opt_data/cache python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night \
      --out gnn_opt_data/night_ds --judge deepseek-v4-flash --no-table

Per run: runner/features.build_features(..., jury=<judge>) (features from jury_<judge>.jsonl only, no NLI; the
NLI column 'contradiction' is not exported), then the graph_*_<judge>.csv outputs are moved to
<cache>/judge/<judge>/<cfg>/<rep>/graph_{edges,nodes}.csv, the layout data.load_run reads when a run dir has no
graph_*_<judge>.csv of its own.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "sim_dataset" / "runner"))
sys.path.insert(0, str(REPO / "sim_dataset" / "generator"))
from features import NLI, build_features  # noqa: E402
from query import Dataset  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--judge", required=True, help="deepseek-v4-flash | claude-haiku-5-5")
    ap.add_argument("--cache", default=os.environ.get("GNN_OPT_CACHE", str(REPO / "gnn_opt_data" / "cache")))
    a = ap.parse_args()
    ds = Dataset(REPO / "sim_dataset" / "dataset")
    nli = NLI(enabled=False)
    runs = sorted(p.parent for p in Path(a.runs).glob("*/rep*/meta.json"))
    n = 0
    for rd in runs:
        if not (rd / f"jury_{a.judge}.jsonl").exists() or not (rd / "graph_edges.csv").exists():
            continue
        out = Path(a.cache) / "judge" / a.judge / rd.parent.name / rd.name
        if (out / "graph_nodes.csv").exists():
            n += 1
            continue
        build_features(ds.load(rd.parent.name), rd, nli, jury=a.judge)
        out.mkdir(parents=True, exist_ok=True)
        for k in ("edges", "nodes"):
            shutil.move(str(rd / f"graph_{k}_{a.judge}.csv"), str(out / f"graph_{k}.csv"))
        shutil.move(str(rd / f"graph_meta_{a.judge}.json"), str(out / "graph_meta.json"))
        n += 1
    print(f"{a.judge}: {n}/{len(runs)} runs -> {Path(a.cache) / 'judge' / a.judge}")


if __name__ == "__main__":
    main()
