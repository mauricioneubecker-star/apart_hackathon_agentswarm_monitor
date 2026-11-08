#!/usr/bin/env bash
# One command: run the monitors on (new) runs, aggregate together with the night batch, evaluate.
#   bash llm_monitor/rerun.sh sim_dataset/runs_vx                       # P0 + P1 monitors (default)
#   VARIANTS="global_full global_window" YES=1 COMPARE=gnn_preds.csv bash llm_monitor/rerun.sh sim_dataset/runs_vx
# The heads / thresholds are fit on night_train + night_val only, so new runs are pure evaluation.
set -eu
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
RUNS=${1:-sim_dataset/runs_night}
VARIANTS=${VARIANTS:-"global_full global_window pairwise agent"}
ALL="sim_dataset/runs_night"; [ "$RUNS" != "sim_dataset/runs_night" ] && ALL="sim_dataset/runs_night $RUNS"
for v in $VARIANTS; do $PY -m llm_monitor.run --variant "$v" --runs $RUNS --dry-run; done
bash llm_monitor/run_batch.sh "$VARIANTS" --runs $RUNS ${YES:+--yes}
$PY -m llm_monitor.aggregate --runs $ALL --variants $VARIANTS
$PY -m llm_monitor.evaluate --runs $ALL --variants $VARIANTS ${COMPARE:+--compare $COMPARE}
