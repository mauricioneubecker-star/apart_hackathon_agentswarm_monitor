# Unabhängige Gegenprüfung vom 8. Nov. 2026 (Archiv)

Am 8. Nov. haben unabhängige Prüf-Agenten die Analysen in `analysis/` nachgerechnet und angegriffen. Sie bekamen den Code
und die Daten, nicht die Schlussfolgerungen. Jeder schwere Befund wurde von einem zweiten Agenten noch einmal geprüft.
Hier liegen ihre Skripte, Text-Ausgaben und Rückgaben, damit jede zitierte Zahl nachvollziehbar bleibt.

| Ordner | Was geprüft wurde |
|---|---|
| `contagion-code/` | Code von `analysis/contagion.py` (Risikomenge, Fenster, Placebo, Mantel-Haenszel, Bootstrap, Branch-Test) |
| `contagion-confounding/`, `confirm-contagion-confounding/` | Störfaktoren: Modell, Ticket-Abhängigkeiten, Rollen, Kanäle, K2/K4, CI-Stand; bedingte logistische Regression |
| `contagion-design/`, `confirm-contagion-design/` | Design: Zeit-Misch-Test, Negativkontrolle, Gültigkeit des Placebos, Homophilie-Simulation, Branch-Arme |
| `sensitivity/`, `confirm-sensitivity/` | θ/Δ-Sensitivität (`analysis/sens.py`, `sens_summary.py`) |
| `plan/`, `confirm-plan/` | `ANALYSIS_PLAN.md` gegen `llm_monitor/evaluate.py`, `VALIDATION.md` §3 und die GNN-Harness |
| `findings/` | Faktencheck jeder Aussage in `FINDINGS.md` |
| `stats-monitors/`, `stats-verify-monitors/` | GNN gegen LLM gegen Baselines auf identischen Harness-Zeilen (CV auf night_train), Holm |
| `stats-factors/`, `stats-verify-factors/` | Design-Faktoren → Kippen: Permutationstests über Konfigurationen, Holm, logistische Regression |
| `heldout-verify/` | Nachrechnung des Vergleichs auf den zurückgehaltenen Testzeilen (`analysis/heldout/`, `analysis/results/heldout.md`) |
| `_agent_results/` | strukturierte Rückgaben aller Prüfer (JSON) |

Hinweise:
- Die Skripte enthalten absolute Pfade in ein temporäres Arbeitsverzeichnis. Wer sie erneut laufen lässt, muss die Pfade
  anpassen. Die Eingabedaten sind `sim_dataset/runs_night` (Stand 68744e2) und die Vorhersagedateien der Branches
  `gnn-opt` und `gnn-opt-torch`.
- Große Zwischendateien (Pickle, NPZ) sind nicht archiviert.
- Ein Prüfer hat entgegen der Vorgabe einmal `git fetch --dry-run` ausgeführt. Refs und Worktree blieben unverändert.
