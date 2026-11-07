#!/usr/bin/env bash
# Swarm runs -> GNN results in one go (run from the repo root).
#   gnn/run_swarm.sh sim_dataset/runs_core                 # quick sweep (6 arms, 3 seeds)
#   SPEC=gnn/sweeps/swarm_main.json gnn/run_swarm.sh sim_dataset/runs_core     # full sweep incl. ablations
# Env: THETA (8), DELTA (3), WORKERS (4), FEATURES=1 recomputes labels+features first, PILOT_SPLIT (hash),
#      JUDGES="deepseek-v4-flash claude-haiku-5-5" also builds the judge-swap tables (needs FEATURES=1 or existing files).
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <runs_dir> [<runs_dir> ...]"; exit 1; }
THETA=${THETA:-8}; DELTA=${DELTA:-3}; WORKERS=${WORKERS:-4}; SPEC=${SPEC:-gnn/sweeps/swarm_quick.json}
OUT=${OUT:-data/swarm}; PILOT_SPLIT=${PILOT_SPLIT:-hash}
if [ "${FEATURES:-0}" = "1" ]; then
  for r in "$@"; do
    python3 sim_dataset/runner/run.py labels --out "$r"
    python3 sim_dataset/runner/run.py features --out "$r"
    for j in ${JUDGES:-}; do python3 sim_dataset/runner/run.py features --jury "$j" --out "$r"; done
  done
fi
python3 -m gnn.adapters.swarm --runs "$@" --out "$OUT" --theta "$THETA" --delta "$DELTA" --pilot-split "$PILOT_SPLIT"
for j in ${JUDGES:-}; do
  python3 -m gnn.adapters.swarm --runs "$@" --out "$OUT" --theta "$THETA" --delta "$DELTA" --pilot-split "$PILOT_SPLIT" --jury "$j"
done
python3 -m gnn.sweep "$SPEC" --data "$OUT" --workers "$WORKERS"
RES=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['out'])" "$SPEC")
python3 -m gnn.report "$RES" --splits val,test_id --boot 1000 | tee "$RES/report.txt"
