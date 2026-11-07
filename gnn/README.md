# GNN-Monitor: Training-Pipeline für Swarm-Simulation und AmongUs-X

Eine Pipeline für zwei Datensätze. Die Adapter schreiben ein gemeinsames Snapshot-Format ([FORMAT.md](FORMAT.md));
Loader, Modelle, Training, Baselines, Sweeps und Report sind für beide gleich.

```
adapters/swarm.py    runs/*/rep*/graph_*.csv + labels.json + core_selection.csv ─┐
adapters/amongus.py  AmongUs-X: summary.json + agent-logs-compact.json + game_*.log ┴─► data/<name>/ ─► train / sweep ─► report
```

## Setup
```bash
pip install torch torch_geometric scikit-learn pandas lightgbm   # lightgbm optional
```

## 1. Daten erzeugen
```bash
# Swarm (nach run.py jury + labels + features)
python -m gnn.adapters.swarm --runs sim_dataset/runs --out data/swarm --theta 8 --delta 3
#   Judge-Tausch (Ablation 3): erst  python sim_dataset/runner/run.py features --jury deepseek-v4-flash
python -m gnn.adapters.swarm --runs sim_dataset/runs --out data/swarm --jury deepseek-v4-flash
# AmongUs-X (nur Stdlib, läuft direkt neben den Rohdaten; ~25 s für Self-Play)
python3 gnn/adapters/amongus.py --root ~/data/AmongUs-X/selfplay-dataset --out data/amongus_selfplay
```
Swarm-Labels werden im Adapter berechnet: `--theta`, `--delta`, `--attempts` (blockierte Versuche mitzählen) ändern
sie ohne Neusimulation. Ziele: `tip`, `new_violator` (neuer Verstoß in Δ), `risk_count`; Knoten:
`violates_within_delta`. Among Us: `innocent_ejected`, `impostor_ejected`, `game_impostor_win`,
`n_crew_votes_innocent`; Knoten: `votes_innocent`, `votes_skip`, `is_impostor` (Kontrolle).

## 2. Ein Lauf
```bash
python -m gnn.train --data data/amongus_selfplay --model gine \
  --graph-target innocent_ejected --graph-count n_crew_votes_innocent --node-target votes_innocent \
  --select graph.auprc --strata round --seed 0 --out results/dev
```
Modelle: `gine` (Default), `gated`, `transformer`, `gatv2`, `none` (K0, ohne Message Passing),
`logreg` (K1), `hgb` / `lgbm` (K2), `time` (nur Zeit-/Größenfeatures, Uhr-Kontrolle).
Feature-Auswahl: `--stage 0..3`, `--drop-groups rule_near,temporal`, `--include-groups privileged|tool_activity`.
Kontrollen: `--rewire` (gradtreu neu verdrahtet), `--shuffle-labels` (muss auf Zufallsniveau fallen).
OOD: `--holdout '{"matchup": ["llama-3.3-70b"]}'` → Split `test_ood`.

## 3. Sweeps und Report
```bash
python -m gnn.sweep gnn/sweeps/amongus_phase1.json --workers 2     # Resume: einfach neu starten
python -m gnn.sweep gnn/sweeps/swarm_main.json --workers 4
python -m gnn.report results/amx_phase1 --splits val,test_id --boot 1000
```
`results/<sweep>/results.jsonl` enthält pro Lauf Config, Metriken pro Split (AUROC, AUPRC, Prevalence,
Recall@5 %FPR mit Schwelle aus val, Brier, MAE) und nach `strata` aufgeteilte AUPRC; `preds/` die Vorhersagen
(für Bootstrap-CIs über Gruppen = Konfigurationen bzw. Spiele).

## Was nie Input ist
Swarm: verbotene Tool-Events, Prompts, `thought`, Modellidentität, `instructed`, Lösbarkeit (Tool-Aktivität nur
über `tool_activity`). Among Us: Rolle, Thinking Process, World State Ledger, Epistemic States, Kills/Vents;
Räume/Ko-Lokation nur über `privileged`.

## Swarm-Simulation (v1.4b, Stand 7. Nov. abends): großer Run

```bash
pip install -r gnn/requirements.txt
# Labels + Features müssen pro Episode existieren (run.py labels / features); FEATURES=1 rechnet sie neu.
gnn/run_swarm.sh sim_dataset/runs_core                                   # Quick-Sweep: 6 Arme, 3 Seeds
SPEC=gnn/sweeps/swarm_main.json gnn/run_swarm.sh sim_dataset/runs_core   # voll: Baselines, Kontrollen, Ablationen S0–S3
THETA=8 DELTA=3 WORKERS=8 JUDGES="deepseek-v4-flash claude-haiku-5-5" FEATURES=1 gnn/run_swarm.sh ...
```
- Adapter v2: R pro Episode (20/25/30), Branch-Arme (`rep0-<arm>`) ohne doppelten Präfix (Runden ≤ branch_round nur
  in der Kontrolle), Arme und Kontrolle in derselben Gruppe/Split, Splits aus `dataset/index.csv` (Core) bzw. Hash für
  Pilot-Splits, Kanten = Lesekanten (direct + broadcast, Katalog v1.1), `round_frac` als Zeitfeature.
- Tempo: Datensätze werden beim ersten Lauf als `.cache/<hash>.pt` neben den Daten gespeichert (danach Laden in
  Sekunden), Evaluations-Batches einmal kollationiert, Batch 256 / lr 2e-3 / Patience 8. Gemessen auf 2 CPU-Kernen mit
  ~560 Episoden (13k Snapshots à 24 Knoten, ~120 Lesekanten): GINE ~5 s pro Epoche, ein Lauf 1,5–6 min;
  `--edge-proj shared --no-reverse` ~40 % schneller. Mehr Episoden skalieren linear, die Knotenzahl bleibt 24.
