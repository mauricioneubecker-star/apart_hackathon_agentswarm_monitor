#!/usr/bin/env bash
# usage: gg.sh [git grep options and -e patterns...]  -- greps all 14 origin branches (read-only)
cd /Users/mauricio/sim_local/apart_vx || exit 1
B=(origin/cloud-synthesis origin/feature-catalog-v1 origin/fix/scenarios-core500 origin/gnn-opt origin/gnn-opt-torch origin/gnn-pipeline origin/gnn-swarm origin/llm-monitor-baseline origin/main origin/night-vx-validation origin/pilot2-fixes origin/pilot3-fixes origin/pilot4-fixes origin/pilot5-v1.5)
git grep -I "$@" "${B[@]}" -- . ':!*runs_vx3*' ':!*secrets.local.json'
