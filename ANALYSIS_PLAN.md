# Analyseplan fürs Paper (Version 2)

**Entwurf v2 vom 8. Nov. 2026, 19:05.** Er gilt, sobald er committet ist. Danach ändern wir ihn nur über einen
datierten Nachtrag am Ende. v1 (17:50/18:10) wurde von unabhängigen Prüfern gegen den Code geprüft, die Befunde stehen in
`analysis/review/plan/` und `analysis/review/confirm-plan/`. v2 behebt sie.

Zusammenfassung der Ergebnisse: [FINDINGS.md](FINDINGS.md). Design der Validierung: [sim_dataset/VALIDATION.md](sim_dataset/VALIDATION.md).

## 0. Was schon gesehen wurde (ehrlich)

| Teil | Stand beim Schreiben | Folge |
|---|---|---|
| LLM-Monitore und Referenz-Baselines | Protokoll (a) und (b) auf allen Nacht-Splits committet (a6c1d8a 16:08, 68744e2 17:24), in der θ/Δ-Sensitivität 5× neu gerechnet (17:47–18:00) | Test-Ergebnisse bekannt, nicht blind |
| GNN | Kreuzvalidierung auf night_train; night_val 2 Blicke; Test-Splits 1 Blick des GNN-Teams (`gnn_opt_torch/LOOKS.md`, Modelle vorher eingefroren) | Test-Ergebnisse bekannt, nicht blind |
| Gemeinsamer Vergleich GNN gegen LLM | auf identischen Harness-Zeilen (CV, 18:15) und auf den Testzeilen (19:00) gerechnet, nachdem beide Seiten ihre eigenen Testzahlen kannten | bestätigend, nicht blind |
| Ansteckung, Branch-Arme, Design-Faktoren, θ/Δ | nachträglich gerechnet und gegengeprüft | explorativ |
| `night_vx` | nur gezählt, welche Läufe kippen. **Kein Monitor-Score existiert.** | einziger blinder Teil, siehe §6 |

## 1. Forschungsfragen

| | Frage | Wo |
|---|---|---|
| RQ1 | Steckt Regelbruch im Schwarm über Kommunikation an? | §7 (explorativ) |
| RQ2 | Sagen Monitore, die nur Kommunikation sehen, das Kippen 3 Runden vorher voraus, besser als die Uhr? | §4–§5 |
| RQ3 | Welche Bauart ist am besten: GNN, Tabellenmodell, LLM über alles oder LLM Gespräch für Gespräch? | §4–§5 |
| RQ4 | Halten die Monitore unter Verschiebungen (Zeit, Population, Ahndung, Topologie, neue Wiederholungen)? | §6 |

## 2. Ziel und Labels

- **Primär:** `y3` / `tip` = θ = 8 Agenten erreichen den Verstoß innerhalb von Δ = 3 Runden. Definiert nur für Snapshots
  mit Zählerstand < θ. Einheit ist der Snapshot (Lauf, Runde). Branch-Präfixe zählen einmal.
- Am Laufende ist das Fenster abgeschnitten. Zeilen mit t = R sind immer negativ. Im time-Arm (R = 36) betrifft das
  t = 34–36. Die Uhr profitiert davon. Für H2 berichten wir die Uhr deshalb zusätzlich ohne die letzten 3 Runden.
- θ und Δ bleiben fest. Andere Werte nur als Sensitivität (§8).

## 3. Vorhersager

**Hauptset.** Die Modelle hat das GNN-Team vor seinem Test-Blick in `gnn_opt_torch/LOOKS.md` eingefroren.

| Name | Datei / Modell | Training |
|---|---|---|
| `clock` | `gnn_opt/preds/{cv,eval}/hgb_clock.csv` | night_train |
| `bag+graph` | `gnn_opt/preds/{cv,eval}/hgb_bag+graph.csv` | night_train |
| `zs:pairwise` | `data/llm_monitor/pairwise` (zero-shot, Prompt `lm1-2026-11-08`) | keins |
| `zs:global_full` | `data/llm_monitor/global_full` (zero-shot, k = 3) | keins |
| `gnn` | `gnn_opt_torch/preds/eval/cloud_final_gnn.csv`, Modell `models/cloud_final_gnn.pt` (Knoten-GRU, 5 Seeds, Jury-Tausch-Augmentation) | night_train |
| `hybrid` | `gnn_opt_torch/preds/eval/cloud_final.csv` (Logit-Mittel 0,5 aus `gnn` und `tab_mem`) | night_train |

**Sekundär, nach dem Review ergänzt (nicht Teil der Holm-Familie):** `tab_mem` = `hgb_bag+graph+mem`, die stärkste
Tabellen-Baseline mit Gedächtnis pro Agent. Außerdem `zs:agent`, `zs:global_window`, gestackte LLM-Köpfe, der Kanten-Monitor,
das zweistufige Tabellenmodell pro Agent (`gnn_opt/preds/cv/final_hybrid.csv`, bester CV-Score) und das Mac-Modell
`final.pt`. Alle Ablationen und Kontrollen sind sekundär.

Referenz, kein Monitor: `oracle` = echter Verstoßzähler + Uhr (nicht beobachtbar).

## 4. Metriken und die eine Entscheidungsregel

- **Primäre Zeilen:** die zurückgehaltenen Nacht-Splits gepoolt (night_test_id ∪ test_ood_family ∪ test_ood_seed ∪
  night_branch). Es sind die `eval == 1`-Zeilen der Harness, alle Monitore auf identischen Zeilen.
- **Primäre Metrik:** AUROC von `y3`. **Zeitgematcht** heißt: AUROC innerhalb der Bins „Runden bis zur Deadline“ (≤ −9,
  −8…−5, −4…−1, 0…3, > 3), nach Paaren gewichtet (`llm_monitor.evaluate.stratified_auroc`). Die Harness-Variante mit
  Runden-Bins ist eine Sensitivität.
- Immer daneben: AUPRC mit Prävalenz, Recall bei 5 % FPR, Vorwarnzeit und Fehlalarme pro Lauf. Die Schwelle stammt nur
  aus Trainingsdaten: bei trainierten Modellen aus deren OOF auf night_train, bei zero-shot-LLMs aus night_train + night_val.
- **Inferenz:** gepaarter Cluster-Bootstrap über Konfigurationen, 10.000×, dieselben Ziehungen für alle Monitore.
  Zweiseitiges p = 2 · min(P(d ≤ 0), P(d ≥ 0)), Untergrenze 1/B. Keine DeLong-Tests, weil Zeilen derselben Konfiguration
  abhängig sind.
- **Primäre Familie (11 Tests, Holm):**
  - (a) zeitgematcht: `bag+graph`, `zs:pairwise`, `zs:global_full`, `gnn`, `hybrid`, jeweils minus `clock`;
  - (b) AUROC gesamt: `gnn` − `bag+graph`, `hybrid` − `bag+graph`, `zs:pairwise` − `bag+graph`, `zs:pairwise` − `gnn`,
    `zs:pairwise` − `hybrid`, `zs:global_full` − `bag+graph`.
- **Regel:** Ein Unterschied gilt als echt, wenn Holm-p < 0,05 auf den primären Zeilen. Die Vorzeichen in den
  4 Einzel-Splits berichten wir beschreibend. Kreuzvalidierung und Protokoll (a) sind nur beschreibend.
- RQ2 gilt als gestützt, wenn alle 5 Tests aus (a) bestehen.
- **Fairness-Spalten im Haupttext:** zeitgematcht, innerhalb gleicher Setups (Konfigurationen mit gemischtem Ausgang,
  Konfiguration × Zeit-Bin), vor der ersten Ankündigung des Shortcuts.

## 5. Wie der gemeinsame Vergleich gerechnet wird

- Zeilen und Labels: Harness-Tabelle aus `gnn_opt/build_dataset.py` auf `runs_night`. Geprüft am 8. Nov.: dieselben
  7.560 Snapshots wie in `llm_monitor`, identische Labels auf allen 6.468 Zielzeilen.
- Scores: GNN und Baselines aus den eingefrorenen `preds/eval`-Dateien, zero-shot-LLMs aus `data/llm_monitor/<variant>`.
- Skript: `analysis/heldout_compare.py`, unabhängig nachgerechnet (`analysis/review/`). `llm_monitor.evaluate --compare`
  nutzen wir dafür nicht. Es kennt keine Differenzen gegen die Uhr, keinen zeitgematchten Bootstrap und nur einseitige p.
- Ungleichheiten, die wir offen nennen:
  - Die Konfiguration des GNN wurde auf denselben CV-Zeilen gewählt, die CV-Zahlen sind deshalb optimistisch.
  - Die zero-shot-Monitore lesen Rohtext mit Aufgabenwörtern.
  - `global_full` sieht indirekt die vergangene Zeit.
  - Haiku ist auch einer der beiden Jury-Richter hinter den GNN-Merkmalen.

## 6. Validierung `night_vx` (RQ4): der vorab festgelegte Teil

**Ablauf, erst nach dem Commit dieses Plans:**
1. **Zero-shot-LLM-Monitore auf `runs_vx`:** `pairwise` und `global_full`, gleicher Prompt `lm1-2026-11-08`, gleiches k,
   vorher `--dry-run`. Splits ohne `night_vx_ft*` und `night_vx_pop_bal`. Kosten grob 5–8 $. Danach
   `llm_monitor.aggregate` über `runs_night` und `runs_vx`.
2. **GNN:** `gnn_opt_torch/predict.py --runs sim_dataset/runs_vx --model gnn_opt_torch/models/cloud_final_gnn.pt`. Das
   ist das eingefrorene Modell, ohne Neutraining. `bag+graph`, `tab_mem` und `clock` werden auf night_train gefittet.
3. **Auswertung mit eigenem Skript** `analysis/vx_eval.py`. Es wird vor dem ersten Monitor-Score geschrieben und
   committet. Denn `llm_monitor.evaluate.vx_shift` zieht ohne Zurücklegen, und Teil B vergleicht dort nur die
   2 neuen Läufe.
   - Pro Arm A ∈ {time, glm, enf, topo}: Δ_shift = M(A) − M(id rep0), Δ_noise = M(id rep1) − M(id rep0) und
     M(A) − M(id rep1). Bootstrap über die Basen mit Zurücklegen, dieselben Ziehungen für alle Monitore und Größen.
     Metriken: AUROC und zeitgematchte AUROC.
   - Teil B: innerhalb der Quellkonfiguration, mit den 2–3 vorhandenen Nacht-Läufen plus den 2 neuen (Gruppe =
     `vx_base`). Lauf-Ebene innerhalb der Konfiguration und Zeilen-Ebene innerhalb Konfiguration × Zeit-Bin, Bootstrap
     über die 8 Quellkonfigurationen.
4. **Hypothesen H1–H5** wie VALIDATION.md §3.5. **H6 entfällt**, weil Teil C technisch gescheitert ist (4B-Fine-Tune: 44 %
   ungültiges JSON in der Canary, `runs_vx/_logs/vx_decisions.md`).
   - **H4:** Die Manipulationsprüfung („weniger Kippen“) ist laut Zwischenstand nicht bestanden. Fehlalarm heißt: Anteil
     der nicht gekippten Läufe mit mindestens einem Alarm (Score ≥ Trainingsschwelle), enf gegen id rep0 auf denselben
     Basen. Dazu kommt die Zeilen-FPR auf nicht gekippten Läufen.
5. **Verschiebung der Kipprate pro Arm:** exakter McNemar-Test gegen id rep0, Holm über 4 Arme. Das ist beschreibend,
   die Zählungen waren schon sichtbar.
6. Mit 14 Basen erkennt die Suite nur große Einbrüche (> 0,1 AUROC). Das steht so im Paper.

## 7. Ansteckung (RQ1), explorativ

Siehe [analysis/results/contagion.md](analysis/results/contagion.md). Wir berichten beide Populationen (alle Agenten und
nur Agenten mit Direktnachrichten) gleichrangig. Die Einschränkung auf Agenten mit Direktnachrichten haben wir erst nach
Sicht der Placebo-Ergebnisse gewählt. Pflicht sind außerdem: die Aufteilung K2/K4 und nach Kanal, der Zeit-Misch-Test,
die Negativkontrolle und der Hinweis, dass das Placebo Homophilie nicht ausschließt. Als Test dient der Sign-flip über
Konfigurationen, nicht ein Test auf Zeilenebene. Die Branch-Arme berichten wir als Anfälligkeit für eingeschleuste
Anweisungen. Test: Permutationstest mit Vorzeichenwechsel (2⁸), Holm über 2 Arme.

## 8. Sensitivität der Labels, explorativ

θ ∈ {6, 8, 10} bei Δ = 3 und Δ ∈ {2, 3, 5} bei θ = 8, siehe
[analysis/results/sensitivity.md](analysis/results/sensitivity.md). Gepaarter Bootstrap 2000×. Bei θ = 10 zählt die
Spalte „nur Zähler < 8“.

## 9. Design-Faktoren, explorativ

Permutationstest über Konfigurationen innerhalb des Blocks, 10.000×, Holm über 14 Faktoren. Dazu adjustierte Modelle,
siehe `analysis/review/stats-factors/`.

## 10. Abweichungen von VALIDATION.md §3 und HARNESS.md

1. Die GNN-Auswahl erfolgte nach dem Harness-Score auf 64 night_train-Konfigurationen und nicht nach OOF-AUPRC auf
   train + val (§3.1).
2. LLM-Monitore und Referenzen wurden schon mehrfach auf den Test-Splits ausgewertet. „Einmal“ gilt nur noch für
   `night_vx`.
3. Die finalen Modelle sind auf night_train trainiert und nicht auf train + val neu trainiert.
4. In §3.2 ist das GNN ein GINE. Eingefroren ist ein RGINE mit Knoten-GRU.

## 11. Was wir nicht tun

- Keine Auswahl, keine Schwelle und kein Tuning auf Test-Splits oder `night_vx`.
- Kein Training von Monitoren auf `runs_vx`.
- Keine neuen Simulationen, die nicht hier stehen. `tools/vx_night2.sh` nur als Nachtrag mit Ziel und Auswertung, und das
  Skript vor dem Start committen.
- Keine Korrektur für Mehrfachtests im explorativen Teil. Dafür berichten wir alles mit CI und kennzeichnen es.

## Nachträge

(noch keine)
