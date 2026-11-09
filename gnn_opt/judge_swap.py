#!/usr/bin/env python3
"""Judge-swap ablation: rebuild graph_edges.csv / graph_nodes.csv with ONE judge's scores (no disagreement), using
the project's own feature code (sim_dataset/runner/features.py, jury=<judge>). Outputs go to a cache directory, the
run directories are not modified.

  python3 gnn_opt/judge_swap.py --runs sim_dataset/runs_night --judge deepseek-v4-flash
  python3 gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night_deepseek --judge deepseek-v4-flash
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "sim_dataset", "runner"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--cache", default=os.environ.get("GNN_OPT_CACHE", "/home/claude/cache"))
    a = ap.parse_args()
    import features  # noqa: E402
    scen = os.path.join(REPO, "sim_dataset", "dataset", "scenarios", "core")
    n = 0
    for d in sorted(glob.glob(os.path.join(a.runs, "*", "rep*"))):
        if not os.path.exists(os.path.join(d, f"jury_{a.judge}.jsonl")):
            continue
        cfg, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
        out = os.path.join(a.cache, "judge", a.judge, cfg, rep)
        if os.path.exists(os.path.join(out, "graph_edges.csv")):
            continue
        sc = json.load(open(os.path.join(scen, f"{cfg}.json")))
        with tempfile.TemporaryDirectory() as tmp:
            for f in ("messages.jsonl", f"jury_{a.judge}.jsonl", "events.jsonl"):
                if os.path.exists(os.path.join(d, f)):
                    os.symlink(os.path.abspath(os.path.join(d, f)), os.path.join(tmp, f))
            features.build_features(sc, Path(tmp), nli=None, jury=a.judge)
            os.makedirs(out, exist_ok=True)
            shutil.copy(os.path.join(tmp, f"graph_edges_{a.judge}.csv"), os.path.join(out, "graph_edges.csv"))
            shutil.copy(os.path.join(tmp, f"graph_nodes_{a.judge}.csv"), os.path.join(out, "graph_nodes.csv"))
        n += 1
    print(f"{n} runs rebuilt for judge {a.judge} -> {a.cache}/judge/{a.judge}")


if __name__ == "__main__":
    main()
