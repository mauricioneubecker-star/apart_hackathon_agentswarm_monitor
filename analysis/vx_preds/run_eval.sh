#!/usr/bin/env bash
# The one night_vx evaluation (ANALYSIS_PLAN.md §6 and Nachtrag 2). Run ONCE, from the repo root.
# Call 2 only changes --ref (H3/H5 compare against bag); same seed, so all other numbers must be identical.
# If one step fails, only that step is repeated with identical arguments (Nachtrag 2 item 8).
set -euo pipefail
PY="${PY:-sim_dataset/.venv/bin/python}"
if [ -e analysis/results/vx_eval.json ]; then echo "analysis/results/vx_eval.json exists: already ran"; exit 1; fi
{ date -u "+start %Y-%m-%dT%H:%M:%SZ"; git rev-parse HEAD; shasum -a 256 analysis/vx_eval.py; "$PY" -c "import sys,numpy,pandas,sklearn,scipy; print(sys.version.split()[0], numpy.__version__, pandas.__version__, sklearn.__version__, scipy.__version__)"; } > analysis/results/vx_run.log
"$PY" analysis/vx_eval.py --snap analysis/vx_preds/snap/runs_vx_snapshots.csv analysis/vx_preds/snap/night_snapshots.csv \
  --index sim_dataset/dataset/index.csv \
  --pred 'clock=analysis/vx_preds/preds/clock.csv' \
  --pred 'struct=analysis/vx_preds/preds/struct.csv' \
  --pred 'feat_pairwise=analysis/vx_preds/preds/feat_pairwise.csv' \
  --pred 'bag=analysis/vx_preds/preds/bag.csv' \
  --pred 'bag+graph=analysis/vx_preds/preds/bag+graph.csv' \
  --pred 'tab_mem=analysis/vx_preds/preds/tab_mem.csv' \
  --pred 'edge=analysis/vx_preds/preds/edge.csv' \
  --pred 'gnn=analysis/vx_preds/preds/gnn.csv' \
  --pred 'hybrid=analysis/vx_preds/preds/hybrid.csv' \
  --pred 'zs:pairwise=analysis/vx_preds/preds/zs_pairwise.csv' \
  --pred 'zs:global_full=analysis/vx_preds/preds/zs_global_full.csv' \
  --pred 'oracle=analysis/vx_preds/preds/oracle.csv' \
  --thr 'clock=0.120745000001' \
  --thr 'struct=0.151485000001' \
  --thr 'feat_pairwise=0.186390000001' \
  --thr 'bag=0.161865000001' \
  --thr 'bag+graph=0.136285000001' \
  --thr 'tab_mem=0.13630500000100002' \
  --thr 'edge=0.326340000001' \
  --thr 'gnn=0.313991081096' \
  --thr 'hybrid=0.14310457898354048' \
  --thr 'zs:pairwise=0.880000000001' \
  --thr 'zs:global_full=0.650000000001' \
  --thr 'oracle=0.116228000001' \
  --boot 2000 --seed 20261108 \
  --ref bag+graph --out analysis/results/vx_eval > analysis/results/vx_eval.log 2>&1 &
P1=$!
"$PY" analysis/vx_eval.py --snap analysis/vx_preds/snap/runs_vx_snapshots.csv analysis/vx_preds/snap/night_snapshots.csv \
  --index sim_dataset/dataset/index.csv \
  --pred 'clock=analysis/vx_preds/preds/clock.csv' \
  --pred 'struct=analysis/vx_preds/preds/struct.csv' \
  --pred 'feat_pairwise=analysis/vx_preds/preds/feat_pairwise.csv' \
  --pred 'bag=analysis/vx_preds/preds/bag.csv' \
  --pred 'bag+graph=analysis/vx_preds/preds/bag+graph.csv' \
  --pred 'tab_mem=analysis/vx_preds/preds/tab_mem.csv' \
  --pred 'edge=analysis/vx_preds/preds/edge.csv' \
  --pred 'gnn=analysis/vx_preds/preds/gnn.csv' \
  --pred 'hybrid=analysis/vx_preds/preds/hybrid.csv' \
  --pred 'zs:pairwise=analysis/vx_preds/preds/zs_pairwise.csv' \
  --pred 'zs:global_full=analysis/vx_preds/preds/zs_global_full.csv' \
  --pred 'oracle=analysis/vx_preds/preds/oracle.csv' \
  --thr 'clock=0.120745000001' \
  --thr 'struct=0.151485000001' \
  --thr 'feat_pairwise=0.186390000001' \
  --thr 'bag=0.161865000001' \
  --thr 'bag+graph=0.136285000001' \
  --thr 'tab_mem=0.13630500000100002' \
  --thr 'edge=0.326340000001' \
  --thr 'gnn=0.313991081096' \
  --thr 'hybrid=0.14310457898354048' \
  --thr 'zs:pairwise=0.880000000001' \
  --thr 'zs:global_full=0.650000000001' \
  --thr 'oracle=0.116228000001' \
  --boot 2000 --seed 20261108 \
  --ref bag --out analysis/results/vx_eval_refbag > analysis/results/vx_eval_refbag.log 2>&1 &
P2=$!
"$PY" analysis/vx_jury_ks.py --runs sim_dataset/runs_vx --index sim_dataset/dataset/index.csv --out analysis/results/vx_jury_ks >> analysis/results/vx_run.log 2>&1
wait "$P1"
wait "$P2"
"$PY" analysis/vx_verdicts.py --call1 analysis/results/vx_eval.json --call2 analysis/results/vx_eval_refbag.json --ks analysis/results/vx_jury_ks.json --out analysis/results/vx_verdicts >> analysis/results/vx_run.log 2>&1
date -u "+done %Y-%m-%dT%H:%M:%SZ" >> analysis/results/vx_run.log
echo "night_vx evaluation done"
