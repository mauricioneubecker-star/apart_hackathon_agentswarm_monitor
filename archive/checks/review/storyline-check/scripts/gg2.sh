#!/usr/bin/env bash
# usage: gg2.sh [git grep options and -e patterns...]  -- greps docs/results on all 14 origin branches (read-only),
# skipping run transcripts (*.jsonl), run dirs and generated package data.
cd /Users/mauricio/sim_local/apart_vx || exit 1
B=(origin/cloud-synthesis origin/feature-catalog-v1 origin/fix/scenarios-core500 origin/gnn-opt origin/gnn-opt-torch origin/gnn-pipeline origin/gnn-swarm origin/llm-monitor-baseline origin/main origin/night-vx-validation origin/pilot2-fixes origin/pilot3-fixes origin/pilot4-fixes origin/pilot5-v1.5)
git -c grep.threads=2 grep -I "$@" "${B[@]}" -- . ':!*.jsonl' ':!sim_dataset/runs*/*/*' ':!sim_dataset/dataset/packages/*' ':!sim_dataset/authoring/*' ':!*runs_vx3*' ':!*secrets.local.json' ':!analysis/vx_preds/preds/*' ':!analysis/vx_preds/snap/*'
