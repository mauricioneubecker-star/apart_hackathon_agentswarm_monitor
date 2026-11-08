#!/usr/bin/env bash
# Run several monitor variants in parallel, one log per variant, and wait for all (resumable: just re-run).
#   bash llm_monitor/run_batch.sh "global_full global_window" --runs sim_dataset/runs_night [--where ...] [--yes]
# Long jobs:  nohup bash llm_monitor/run_batch.sh "pairwise agent" > logs/llm_monitor/batch.out 2>&1 &
# Progress (calls, ok rate, cost so far) is logged every 200 calls to logs/llm_monitor/<variant>.log.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
LOG=${LOG:-logs/llm_monitor}
mkdir -p "$LOG"
VARIANTS="$1"; shift
pids=()
for v in $VARIANTS; do
  echo "$(date '+%F %T') start $v $*" >> "$LOG/$v.log"
  $PY -m llm_monitor.run --variant "$v" "$@" >> "$LOG/$v.log" 2>&1 &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
echo "$(date '+%F %T') batch done ($VARIANTS) rc=$rc"
exit $rc
