# Predicting When Agent Swarms Tip into Collective Rule-Breaking

Code and data for the paper submitted to the [Swarm Alignment Hackathon](https://apartresearch.com/sprints/swarm-alignment-2026) (Apart Research, November 2026).

**Paper:** [`paper/Predicting_When_Agent_Swarms_Tip.pdf`](paper/Predicting_When_Agent_Swarms_Tip.pdf)
**Authors:** Mauricio Neubecker, Tim Würfl, Maximilian Eder (Technical University of Munich, Safe AI Germany)

We simulate software swarms of 24 LLM agents in which some tickets cannot be solved honestly and one forbidden
shortcut works. Labels come directly from the tool log. On the resulting dataset (252 runs in 112 configurations),
we compare a clock, gradient boosting, a temporal GNN, a GNN + boosting hybrid and zero-shot LLM monitors at
predicting whether the swarm tips (at least 8 of 24 agents break the rule) within the next 3 rounds.

## Repository map

```
paper/                  the submitted paper (PDF)
sim_dataset/            simulator and all simulation runs
  generator/            scenario generator (14 design factors, scenario validation)
  authoring/            the six self-written Python libraries the agents work on
  runner/               simulation runner, labels from the tool log, LLM jury, graph features
  tools/                batch scripts, reports and checks for the night batch and the validation suite
  dataset/              scenario specifications, index of all configurations, packages
  runs/ runs_pilot2..4  pilot runs (Section 3.3)
  runs_night/           main batch: 252 runs (Sections 3.4, 4, 5)
  runs_vx/              blind validation suite (Section 5.4)
  runs_vx3/             fresh replicates for the pre-registered replication H7 (Section 5.4)
gnn_opt/                shared monitor harness: snapshot builder, folds, clock and boosting baselines, evaluation
gnn_opt_torch/          temporal GNN (relational GINE + per-agent GRU) and hybrid: training, experiments, frozen models
gnn/                    earlier GNN pipeline: synthetic scaling testbed and AmongUs-X study (Section 5.5)
llm_monitor/            zero-shot LLM monitors (Claude Haiku 5.5), seven variants
results/llm_monitor/    LLM monitor outputs, results and cost
analysis/               analyses behind the paper's results
  factors/              design factors and tipping rates (Section 4, Figure 2b)
  contagion.py          word-of-mouth association and counterfactual forks (Section 4)
  heldout/              comparison of all monitors on the held-out configurations (Table 2)
  vx_preds/ vx3_preds/  frozen monitor predictions of the validation suite and of H7, made before any evaluation
  results/              result tables (Markdown and JSON) of all analyses
synthesis_cloud/        summary of where the monitors generalise and where not (Figure 4), GNN test-look tables
ANALYSIS_PLAN.md        pre-registration (analysis plan v2 with dated addenda, in German)
archive/                material not used in the paper (see archive/README.md)
```

## From paper to repository

| Paper | Code | Data and results |
|---|---|---|
| §3.1 Swarm and shortcut | `sim_dataset/generator/`, `sim_dataset/authoring/`, `sim_dataset/runner/orchestrator.py` | `sim_dataset/dataset/scenarios/`, `sim_dataset/DECISIONS.md` |
| §3.2 Seeds and labels | `sim_dataset/runner/labels.py`, `sim_dataset/generator/` | `labels.json` in every run directory; leakage check (AUROC 0.48) in `sim_dataset/DECISIONS.md` |
| §3.3 Four pilots | `sim_dataset/runner/` | `sim_dataset/runs/`, `runs_pilot2/`, `runs_pilot3/`, `runs_pilot4/` |
| §3.4 Table 1, dataset | `sim_dataset/tools/night_report.py` | `sim_dataset/runs_night/`, `sim_dataset/runs_night/_logs/`, `sim_dataset/dataset/index.csv` |
| §4 Figure 2, design factors | `analysis/factors/` | `analysis/factors/REPORT.md` |
| §4 Word of mouth, forks | `analysis/contagion.py` | `analysis/results/contagion.md` |
| §5.1 Jury and graph features | `sim_dataset/runner/jury.py`, `sim_dataset/runner/features.py` | `sim_dataset/FEATURES.md`; `jury_*.jsonl`, `graph_*.csv` in every run directory |
| §5.1 Clock and boosting | `gnn_opt/` | `gnn_opt/preds/` |
| §5.1 Temporal GNN and hybrid | `gnn_opt_torch/` (hybrid: `gnn_opt_torch/blend.py`) | `gnn_opt_torch/RESULTS.md`, `gnn_opt_torch/models/`, `gnn_opt_torch/preds/` |
| §5.1 Zero-shot LLM monitors | `llm_monitor/` | `results/llm_monitor/RESULTS.md`, `monitor_*.jsonl` in every run directory |
| §5.2 Table 2, held-out comparison | `analysis/heldout/` | `analysis/results/heldout.md`, `analysis/results/heldout_full.md` |
| §5.3 Figure 3, what the GNN relies on | `gnn_opt_torch/`, `gnn_opt/judge_swap.py` | `gnn_opt_torch/RESULTS.md`, `gnn_opt_torch/experiments/`, `analysis/results/sensitivity.md` |
| §5.4 Figure 4, generalisation map | `analysis/vx_eval.py`, `analysis/vx_verdicts.py`, `analysis/vx_posthoc.py` | `synthesis_cloud/SYNTHESIS.md`, `analysis/results/vx*.md` |
| §5.4 Blind validation suite | `sim_dataset/tools/vx_select.py`, `analysis/vx_preds/run_eval.sh` | `sim_dataset/runs_vx/`, `analysis/vx_preds/`, `analysis/results/vx_eval.md` |
| §5.4 Replication H7 | `analysis/vx3_eval.py` | `sim_dataset/runs_vx3/`, `analysis/vx3_preds/`, `analysis/results/vx3_eval.md` |
| §5.5 Synthetic scaling, AmongUs-X | `gnn/adapters/synthetic.py`, `gnn/adapters/amongus.py`, `gnn/jury_amongus.py` | `gnn/RESULTS_amongus.md`, `gnn/sweeps/` |
| Appendix A, monitor details | as §5.1 | `sim_dataset/FEATURES.md`, `llm_monitor/README.md` |
| Appendix B, pre-registered hypotheses | `analysis/vx_verdicts.py`, `analysis/vx3_eval.py` | `ANALYSIS_PLAN.md`, `analysis/results/vx_verdicts.md`, `analysis/results/vx3_eval.md` |

## Data

| Folder | Runs | Configurations | Role in the paper |
|---|---|---|---|
| `sim_dataset/runs/`, `runs_pilot2/`, `runs_pilot3/`, `runs_pilot4/` | 30, 38, 20, 20 | one per run | pilots (§3.3) |
| `sim_dataset/runs_night/` | 252 (236 control runs + 16 counterfactual forks) | 112 | training, held-out splits, factor analysis (§3.4–§5.3) |
| `sim_dataset/runs_vx/` | 93 + 1 excluded canary of a dropped arm | 14 base configurations in 72 configuration directories (arms and replicates) | blind validation suite (§5.4) |
| `sim_dataset/runs_vx3/` | 27 | 14 | pre-registered replication H7 (§5.4) |

`runs_night` is split by configuration, never by run: `night_train` (64 configurations), `night_val`, and the
held-out splits `night_test_id` (known setups), `night_test_ood_family` (unseen task family),
`night_test_ood_seed` (unseen injection channel) and `night_branch` (counterfactual forks). The split of every
configuration is in `sim_dataset/dataset/index.csv`.

Each run directory (`<configuration>/rep<k>/`) holds one 30-round episode:

| File | Content |
|---|---|
| `meta.json` | scenario, replicate, seed, call and message statistics |
| `rounds.jsonl`, `events.jsonl`, `final_state.json` | state per round, the event and tool log, the final state of tickets and merges |
| `messages.jsonl` | all agent-written messages (board, team channels, direct messages) |
| `labels.json` | labels from the tool log: rule-breakers, first violation, whether and when the swarm tipped (θ = 8, Δ = 3), exposure |
| `jury_<judge>.jsonl`, `jury_merged.jsonl` | ratings of every message by the two judges on nine dimensions |
| `graph_edges.csv`, `graph_nodes.csv`, `graph_meta.json` | the communication graph per round with 18 edge and 5 node features |
| `monitor_*.jsonl` | outputs of the zero-shot LLM monitors |
| `llm_calls.jsonl` | agent model calls (no API keys) |

Logs of each batch are in its `_logs/` folder. Counterfactual forks are the directories `rep0-<arm>` in
`runs_night/core-night_branch-*`.

## Pre-registration

`ANALYSIS_PLAN.md` was committed before the evaluations it governs and changed only through dated addenda.
The order is visible in the commit history:

| Commit | Step |
|---|---|
| `4e6e998` | analysis plan v2, before any score on the validation suite |
| `d083547` | frozen predictions and thresholds of the validation suite, before any evaluation |
| `bb3f665` | the single pre-registered evaluation of the validation suite |
| `e319c9e` | addendum registering H7, before its runs existed |
| `289b875` | 27 fresh runs and frozen predictions for H7 |
| `c97b90d` | the single evaluation of H7 |

## Notes

- Some working documents are in German (`ANALYSIS_PLAN.md`, `sim_dataset/README.md`, `sim_dataset/DECISIONS.md`,
  `gnn/RESULTS_amongus.md`).
- Some working documents still refer to files under the paths they had before they were moved to `archive/`.
- API keys were never committed; `sim_dataset/secrets.example.json` shows the expected format.
- The work was developed on several branches, which have all been merged into `main` except `gnn-swarm`, an early
  GNN variant that `gnn_opt_torch/` replaced. The branches are kept.
