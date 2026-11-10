# Simulator and simulation runs

The simulator behind Section 3 of the paper and all runs used in it. The run folders, their sizes and the files of
a run directory are described in the [main README](../README.md#data).

| Folder | Content |
|---|---|
| `generator/` | scenario generator: draws the design factors, writes and validates scenario specifications |
| `authoring/` | the six self-written Python libraries the agents work on (see `authoring/AUTHORING.md`) |
| `runner/` | episode runner (`orchestrator.py`), labels from the tool log (`labels.py`), LLM jury (`jury.py`), communication graph and features (`features.py`) |
| `tools/` | batch scripts, reports and checks for the night batch and the validation suite |
| `dataset/` | scenario specifications (`scenarios/`), the index of all configurations with their split and factors (`index.csv`), the code packages of the six libraries (`packages/`) |
| `runs*/` | simulation runs; each batch has its logs in `_logs/` |

Further documents:

- `VALIDATION.md`: design of the blind validation suite (`runs_vx`). Its Part C, a fine-tuned 4B model, was planned
  but dropped after its canary run failed (`runs_vx/_logs/vx_decisions.md`); the paper uses Parts A and B (93 runs).
- `FEATURES.md` (in German): the full feature catalog. The monitors in the paper use its 18 generic edge and
  5 node features (`E_GEN`, `N_GEN` in `gnn_opt/data.py`); the lexical features are used only in the ablation of
  Section 5.3.
- `DECISIONS.md` (in German): development log of the simulator design, including the pilots and the leakage check
  (AUROC 0.48). It also covers earlier design variants that were not used for the final batch.
- `secrets.example.json`: format of the local key file; keys are never committed.
