# runs_vx3: frozen inputs of the one confirmatory evaluation

Everything here was produced before any runs_vx3 score was compared with a label (ANALYSIS_PLAN.md Nachtrag 3,
pushed as `e319c9e7` before the first episode started). The evaluation is `run_eval.sh`, run once from the repo root.

## Data

28 new episodes: the 14 `night_vx_id` configurations, unchanged, with replicates 2 and 3 (`replicate_seeds[2]`,
`[3]`, never run before), in `sim_dataset/runs_vx3/`. Started 9 Nov 07:45 with

```bash
cd sim_dataset && OUT=runs_vx3 WHERE="split=='__none__'" STAGE2_WHERE="split=='night_vx_id'" STAGE2_REPS=4 \
    EXTRA="--rep-start 2" STOP_AT=1030 bash tools/night_run.sh
```

`--rep-start` (commit `6d1b9c5e`) only selects the replicate indices. Models, jury, labels and features are the code of
the night_vx run.

**Outcome of the run (11:24).** 27 of 28 episodes finished, 0 errors, jury complete for all 27; all 14 bases have at
least one new run (rep2: 14, rep3: 13). `core-night_vx-K2-150-id/rep3` was aborted at 10:36 in round 30 after a
provider rate limit (429). The runner re-queues such an episode, but under STOP_AT 10:30 (Nachtrag 3, item 7) no new
episode starts, so it was not re-run. Its partial directory is kept for transparency; it has no labels and is not part
of any analysis. A second episode (`K2-026-id/rep3`) had aborted earlier for the same reason and was re-run from scratch
before 10:30. Outcome counts were visible in the run log (`runner/run.py status`); no monitor score was compared with a
label before the evaluation.

## Contents

| path | what |
|---|---|
| `preds/<name>.csv` | (run, round, score) for every runs_vx3 snapshot, 12 predictors |
| `snap/runs_vx3_snapshots.csv` | harness snapshot table of runs_vx3 (`gnn_opt/build_dataset.py`), the `--snap` input |
| `manifest.json` | sources, sha256 of every file, coverage check (every eval row has a finite score in [0, 1]) |
| `raw/` | raw GNN output, baseline refit report and logs |
| `assemble_vx3.py` | builds the files above |
| `run_eval.sh` | the evaluation: one call of `analysis/vx3_eval.py`, guarded against a second run |

## Exact commands

Same producers and environments as `analysis/vx_preds/README.md`: scratch checkout `R` = git archive of
origin/gnn-opt-torch `f7194430` (gnn_opt, gnn_opt_torch) plus the symlink `R/sim_dataset`.

```bash
# 1. zero-shot LLM monitors (prompt lm1-2026-11-08 r0, Claude Haiku 5.5; global_full k = 3) and aggregation
PY=sim_dataset/.venv/bin/python bash llm_monitor/run_batch.sh "global_full pairwise" --runs sim_dataset/runs_vx3 --yes
sim_dataset/.venv/bin/python -m llm_monitor.aggregate --runs sim_dataset/runs_vx3 --out data/llm_monitor_vx3 \
    --variants global_full pairwise
# 2. harness dataset and frozen GNN (torch env, CPU, no evaluation, no blend)
cd "$R" && sim_dataset/.venv/bin/python gnn_opt/build_dataset.py --runs sim_dataset/runs_vx3 --out gnn_opt_data/runs_vx3
cd "$R" && GNN_DEVICE=cpu python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_vx3 --data-out gnn_opt_data/runs_vx3 \
    --model gnn_opt_torch/models/cloud_final_gnn.pt --blend '' --no-eval
# 3. baselines refit on night_train (deterministic, single thread), same script as for night_vx
OMP_NUM_THREADS=1 sim_dataset/.venv/bin/python analysis/vx_preds/make_baselines.py --harness "$R/gnn_opt" \
    --night "$R/gnn_opt_data/night" --vx "$R/gnn_opt_data/runs_vx3" --out "$B" --regen <held-out regen dir>
# 4. assemble
OMP_NUM_THREADS=1 sim_dataset/.venv/bin/python analysis/vx3_preds/assemble_vx3.py \
    --gnn-vx3 "$R/gnn_opt_torch/preds/new/runs_vx3__cloud_final_gnn.csv" --baselines "$B" --llm data/llm_monitor_vx3 \
    --vx3-data "$R/gnn_opt_data/runs_vx3" --gnn-repo "$R" --index sim_dataset/dataset/index.csv --out analysis/vx3_preds
```

`analysis/vx3_eval.py` was tested before the evaluation only with random scores (on the night_vx id rows relabelled as
rep2 / rep3, 200 draws).
