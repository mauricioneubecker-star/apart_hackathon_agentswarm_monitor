#!/usr/bin/env bash
# The one evaluation of runs_vx3 (ANALYSIS_PLAN.md Nachtrag 3). Run ONCE, from the repo root.
# If it fails, only this call is repeated with identical arguments.
set -euo pipefail
PY="${PY:-sim_dataset/.venv/bin/python}"
if [ -e analysis/results/vx3_eval.json ]; then echo "analysis/results/vx3_eval.json exists: already ran"; exit 1; fi
{ date -u "+start %Y-%m-%dT%H:%M:%SZ"; git rev-parse HEAD; shasum -a 256 analysis/vx3_eval.py analysis/vx_eval.py; "$PY" -c "import sys,numpy,pandas,sklearn; print(sys.version.split()[0], numpy.__version__, pandas.__version__, sklearn.__version__)"; } > analysis/results/vx3_run.log
"$PY" analysis/vx3_eval.py --snap analysis/vx3_preds/snap/runs_vx3_snapshots.csv --index sim_dataset/dataset/index.csv \
  --pred 'clock=analysis/vx3_preds/preds/clock.csv' \
  --pred 'struct=analysis/vx3_preds/preds/struct.csv' \
  --pred 'feat_pairwise=analysis/vx3_preds/preds/feat_pairwise.csv' \
  --pred 'bag=analysis/vx3_preds/preds/bag.csv' \
  --pred 'bag+graph=analysis/vx3_preds/preds/bag+graph.csv' \
  --pred 'tab_mem=analysis/vx3_preds/preds/tab_mem.csv' \
  --pred 'edge=analysis/vx3_preds/preds/edge.csv' \
  --pred 'gnn=analysis/vx3_preds/preds/gnn.csv' \
  --pred 'hybrid=analysis/vx3_preds/preds/hybrid.csv' \
  --pred 'zs:pairwise=analysis/vx3_preds/preds/zs_pairwise.csv' \
  --pred 'zs:global_full=analysis/vx3_preds/preds/zs_global_full.csv' \
  --pred 'oracle=analysis/vx3_preds/preds/oracle.csv' \
  --vx-eval analysis/results/vx_eval.json --vx-snap analysis/vx_preds/snap/runs_vx_snapshots.csv \
  --boot 10000 --seed 20261109 --out analysis/results/vx3_eval >> analysis/results/vx3_run.log 2>&1
date -u "+done %Y-%m-%dT%H:%M:%SZ" >> analysis/results/vx3_run.log
echo "runs_vx3 evaluation done"
