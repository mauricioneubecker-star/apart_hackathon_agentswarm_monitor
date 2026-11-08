# night_vx: frozen inputs of the one evaluation

Everything here was produced before any night_vx score was compared with a label (ANALYSIS_PLAN.md §6 and
Nachtrag 2). The evaluation is `run_eval.sh`, run once from the repo root.

## Contents

| path | what |
|---|---|
| `preds/<name>.csv` | (run, round, score) for every non-train night snapshot and every runs_vx snapshot; zs files hold all snapshots |
| `thresholds.json` | 5 % FPR alarm thresholds from training data only, with sources (H4) |
| `manifest.json` | sources, sha256 of every file, checks (hybrid formula, coverage of every scored row) |
| `snap/` | harness snapshot tables (gnn_opt/build_dataset.py) of runs_vx and runs_night, the `--snap` inputs |
| `raw/` | raw GNN outputs (with the count head), baseline check log, logs of the GNN runs, GNN source commit |
| `make_baselines.py`, `assemble.py` | the two scripts that produced the files |
| `run_eval.sh` | the evaluation: 2 calls of analysis/vx_eval.py, analysis/vx_jury_ks.py, analysis/vx_verdicts.py |

## Exact commands (8 Nov 2026, 22:35–23:55 CET)

```bash
# 0. code of the frozen GNN and the harness: git archive of origin/gnn-opt-torch f7194430 (gnn_opt, gnn_opt_torch)
#    into a scratch dir R, plus the symlink R/sim_dataset -> <this repo>/sim_dataset
git archive f7194430 gnn_opt gnn_opt_torch | tar -x -C "$R" && ln -s "$PWD/sim_dataset" "$R/sim_dataset"

# 1. harness datasets (deterministic; byte-identical to the builds of the held-out comparison)
cd "$R" && sim_dataset/.venv/bin/python gnn_opt/build_dataset.py --runs sim_dataset/runs_night --out gnn_opt_data/night
cd "$R" && sim_dataset/.venv/bin/python gnn_opt/build_dataset.py --runs sim_dataset/runs_vx --out gnn_opt_data/runs_vx

# 2. frozen GNN, no evaluation, no blend (torch env; default torch threads, CPU)
cd "$R" && GNN_DEVICE=cpu python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_night --data-out gnn_opt_data/night \
    --model gnn_opt_torch/models/cloud_final_gnn.pt --blend '' --no-eval
cd "$R" && GNN_DEVICE=cpu python3 gnn_opt_torch/predict.py --runs sim_dataset/runs_vx --data-out gnn_opt_data/runs_vx \
    --model gnn_opt_torch/models/cloud_final_gnn.pt --blend '' --no-eval

# 3. baselines refit on night_train (single thread), with checks against the held-out refits
OMP_NUM_THREADS=1 sim_dataset/.venv/bin/python analysis/vx_preds/make_baselines.py --harness "$R/gnn_opt" \
    --night "$R/gnn_opt_data/night" --vx "$R/gnn_opt_data/runs_vx" --out "$B" --regen <held-out regen dir>

# 4. zero-shot LLM scores (data/llm_monitor is gitignored; rebuild from the committed monitor_*.jsonl)
sim_dataset/.venv/bin/python -m llm_monitor.aggregate --runs sim_dataset/runs_night sim_dataset/runs_vx \
    --variants global_full pairwise

# 5. assemble predictions, thresholds, checks, snapshot copies and run_eval.sh
OMP_NUM_THREADS=1 sim_dataset/.venv/bin/python analysis/vx_preds/assemble.py \
    --gnn-night "$R/gnn_opt_torch/preds/new/runs_night__cloud_final_gnn.csv" \
    --gnn-vx "$R/gnn_opt_torch/preds/new/runs_vx__cloud_final_gnn.csv" --baselines "$B" --llm data/llm_monitor \
    --night-data "$R/gnn_opt_data/night" --vx-data "$R/gnn_opt_data/runs_vx" --gnn-repo "$R" \
    --index sim_dataset/dataset/index.csv --out analysis/vx_preds
```

## Environment

- GNN: Python 3.11.7, torch 2.11.0, numpy 2.4.4, pandas 3.0.3 (no scikit-learn), CPU, default torch threads.
  With 1 thread the scores differ by at most 2e-8.
- Everything else: `sim_dataset/.venv` (a symlink to the venv of the main checkout): Python 3.12.4, numpy 2.5.4,
  pandas 3.1.1, scikit-learn 1.9.1, scipy 1.18.1. `run_eval.sh` writes the versions into analysis/results/vx_run.log.

## Checks that passed (details in manifest.json and raw/make_baselines.json)

- GNN: our predict.py run reproduces the GNN team's own predict.py check (runs_check, 120 rows) to 1.2e-7; an
  independent re-run by an auditor gives the same sha256. It does not reproduce the committed 40-state eval file
  (Spearman 0.987–0.998 per split), because the stored .pt keeps 15 of the 40 states (RESULTS.md caveat).
- Baselines: the five refits of the held-out comparison are reproduced exactly on the night rows; clock, feature
  pairwise, oracle and edge monitor also match the committed night_val files exactly.
- Hybrid formula vs committed cloud_final.csv: 5e-8. Thresholds: the 9 of the held-out comparison reproduced exactly.
- Coverage: every row vx_eval.py scores has a finite score in [0, 1] for all 12 predictors. The 30 non-finite rows in
  the zs files are the excluded ft4 canary.
- Pre-run audit: 6 independent lenses + 1 critic (analysis/review/vx-preeval/), random scores only on vx.
