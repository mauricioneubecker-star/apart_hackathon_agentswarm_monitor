# GNN-Monitor: Training-Pipeline für Swarm-Simulation und AmongUs-X

> **Note.** This earlier pipeline backs Section 5.5 of the paper (synthetic scaling testbed and AmongUs-X; results in
> `RESULTS_amongus.md`). The GNN monitor of Sections 5.1–5.4 is in `gnn_opt_torch/`.

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
