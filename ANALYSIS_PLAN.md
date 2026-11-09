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

**1 (8. Nov., 19:35).**
- Die gemeinsame Auswertung auf den Testzeilen (§4–§5) lief von 19:00 bis 19:16, also vor dem Commit dieses Plans
  (`4e6e998`, 19:25). Gelesen habe ich die Ergebnisse erst danach. Ergebnis: [analysis/results/heldout.md](analysis/results/heldout.md).
  Nach Holm ist keiner der 11 Tests signifikant.
- Die committeten Baseline-Dateien `hgb_bag+graph`, `hgb_clock` und `oracle_risk+clock` in `gnn_opt/preds/eval`
  decken nur night_val ab. Für die Testzeilen wurden sie mit den Harness-Einstellungen auf night_train neu gefittet
  (`analysis/heldout/regen_baselines.py`).
- Nachträgliche Sensitivität (`analysis/heldout/doubletm.py`): Zeitabgleich innerhalb Deadline × Bin, also absolute
  Runde und Abstand zur Deadline gleichzeitig fest. Anlass: Das Urteil zu RQ2 hängt von der Definition ab. Das ist
  explorativ und ändert die primäre Regel nicht.

**2 (8. Nov., Entwurf 22:45, nach interner Prüfung überarbeitet bis 23:55, vor jeder Auswertung von `night_vx`).**
Festgelegt, bevor ein Monitor-Score auf `runs_vx` mit Labels verglichen wurde. Alle Eingaben liegen in
`analysis/vx_preds/`: Vorhersagen, Schwellen, Prüfprotokoll `manifest.json`, die genauen Befehle in `README.md` und der
Aufruf `run_eval.sh`. Vor dem Commit haben sechs unabhängige Agenten und ein Kritiker die Eingaben geprüft (Berichte in
`analysis/review/vx-preeval/`). Auf vx arbeiteten sie nur mit Zufalls-Scores oder mit schon bekannten Label-Zählungen.

1. **Vorhersager.** Das Hauptset aus §3. Dazu kommen die Baselines, die H1–H5 nennen (VALIDATION.md §3.2): `struct`
   (hgb_struct), `feat_pairwise` (hgb_pairwise) und `bag` (hgb_bag), außerdem `oracle` als Referenz. Sekundär wie in §3
   sind `tab_mem` und `edge` (Kanten-Monitor, top-3). Es fehlen K0 (GNN ohne Message Passing) und die
   Mean-Aggregations-Variante aus H5, weil es von beiden kein eingefrorenes Modell gibt.
2. **Benennung.** „pairwise monitor (max / top-3 over single edges)“ in VALIDATION.md ist die Merkmals-Baseline
   `feat_pairwise` (Merkmalsgruppe `pairwise` in `gnn_opt/tabular.py`). Mit dem LLM-Monitor `zs:pairwise` hat sie
   nichts zu tun. Den Kanten-Monitor `edge` berichten wir bei H1 und bei der Reihenfolge (Punkt 7) daneben.
3. **GNN.** `gnn_opt_torch/predict.py --no-eval --blend ''` mit `models/cloud_final_gnn.pt` (origin/gnn-opt-torch
   `f7194430`). Gewichte, Normierung, cfg und `w_gnn = 0,5` sind seit `b87b2afb` (16:53 UTC) unverändert, also seit vor
   dem Test-Blick des Teams (`f7aa3324`, 17:06 UTC; die Uhrzeiten in LOOKS.md und STATUS.md stimmen nicht mit git
   überein). Nach dem Test-Blick kam in `a35c6d96` (17:11 UTC) nur das Feld `blend_w = 0,5` hinzu. Alle 1.835 übrigen
   Einträge sind bitgleich, geprüft von uns und zwei Prüfern unabhängig. `63123a27` (17:12 UTC) benannte
   `final_gnn.pt` in `cloud_final_gnn.pt` um. Die eval- und Schwellen-Dateien `preds/{eval,cv}/cloud_final*.csv` sind
   blob-gleich mit denen des Test-Blicks. Die Datei enthält nur 15 der 40 Zustände (5 Seeds × die letzten 3
   Snapshots, laut RESULTS.md; ein Prüfer hat das an den Gewichten bestätigt). Die Held-out-Zahlen des Teams mitteln
   alle 40. Die angekündigte Gegenprobe Zeile für Zeile gegen die committete eval-Datei (7.560 Zeilen) ist deshalb
   **nicht bestanden**: Spearman 0,987–0,998 pro Split, größte Abweichung 0,11. An ihre Stelle treten der
   `predict.py`-Check des GNN-Teams, den unser Lauf auf 120 von 120 Zeilen reproduziert (Abweichung ≤ 1,2·10⁻⁷), und
   eine unabhängige Wiederholung durch einen Prüfer mit gleichem sha256. Auf den Held-out-Zeilen von heldout.md (nur
   Nacht-Daten, vor der Auswertung gerechnet, `analysis/results/vx_gnn15_heldout.md`) ist die gespeicherte Fassung
   leicht, aber messbar schwächer: AUROC 0,813 statt 0,817 (Δ −0,004 [−0,009; −0,000]), zeitgematcht −0,007
   [−0,013; −0,000]. Damit Teil B in sich vergleichbar ist, bekommen auch die Nacht-Läufe seiner
   Quellkonfigurationen Scores aus der gespeicherten Datei.
4. **Hybrid und Baselines.** `predict.py` würde das Tabellenmodell in derselben Umgebung wie das GNN neu fitten. Hier
   fehlt dort scikit-learn, deshalb läuft dieser Schritt getrennt mit derselben Formel und denselben Trainingszeilen:
   Hybrid = Logit-Mittel aus `gnn` und `tab_mem`, Gewicht 0,5 aus der Modelldatei (`w_gnn`, schon vor dem Test-Blick
   gespeichert; Formel gegen `cloud_final.csv` geprüft, Abweichung 5·10⁻⁸). Alle Tabellen-Baselines sind wie im
   Held-out-Vergleich auf night_train neu gefittet (`make_baselines.py`). Die fünf, die dort schon neu gefittet wurden,
   sind auf den Nacht-Zeilen identisch. `tab_mem` und damit der Hybrid sind auf vx andere Instanzen als die Dateien des
   Teams in heldout.md. Auf den Held-out-Zeilen hat der vx-Hybrid trotzdem dieselbe AUROC (0,832). Unterschiede
   zwischen vx und heldout.md lesen wir deshalb nicht als Verschiebung. Verglichen wird nur innerhalb von vx.
5. **Umgebung und Merkmale.** Das GNN läuft mit Python 3.11 und torch 2.11 auf der CPU, mit Standard-Threads (mit
   1 Thread weichen Scores um ≤ 2·10⁻⁸ ab). Alles andere läuft mit `sim_dataset/.venv` (Python 3.12, scikit-learn
   1.9.1). Die Datensätze aus `gnn_opt/build_dataset.py` sind byte-gleich mit denen des Held-out-Vergleichs. Merkmals-,
   Label- und Jury-Code sind zwischen Nacht-Batch und vx-Lauf unverändert. Zwei Eigenheiten betreffen alle Modelle auf
   Merkmalen, nicht die LLM-Monitore. Erstens hat eine vx-Nachricht nur einen Richter (m158 in
   `core-night_vx-K2-266-time/rep0`, Haiku fünfmal unlesbar; im Nacht-Batch kommt das nicht vor), betroffen sind 23
   von 190.126 Kanten-Zeilen. Zweitens stehen externe Absender ab Runde 1 als Knoten im Graphen, also vor ihrer ersten
   Nachricht. Das war schon im Training so, ist innerhalb jeder vx-Basis in allen Armen gleich und verschiebt die
   Held-out-AUROC des GNN um höchstens 0,0006. `data/llm_monitor` ist nicht im Repo. Die zs-Dateien lassen sich aus
   den committeten `monitor_*.jsonl` mit `llm_monitor.aggregate` neu bauen.
6. **Schwellen für H4.** 5 % FPR mit `metrics.thr_at_fpr`, Alarm bei Score ≥ Schwelle. Die +10⁻¹² aus `thr_at_fpr`
   stehen mit in `run_eval.sh`. Sie zählen, weil viele zero-shot-Scores genau auf dem Schwellwert liegen.
   Zero-shot-LLMs: aus night_train + night_val. Tabellenmodelle: aus ihrer ID-OOF auf night_train. Diese CV-Dateien
   stammen aus dem `table.csv`-Build des Teams und werden auf unsere Neu-Fits angewandt. GNN und Hybrid: die Dateien,
   mit denen das Team vor dem Test-Blick seine Schwellen gesetzt hat (`preds/cv/cloud_final*.csv`). Das sind
   Proxy-CVs (`e_ngru_4runs`, `h_ngru4_hgb_logit55`), nicht die OOF der eingefrorenen Konfiguration. Das weicht von §4
   ab. Wir behalten sie, damit vx dieselben Schwellen hat wie der Test-Blick. Die Schwellen aus der exakten
   5-Seed-CV (laut Prüfer 0,3354 und 0,1511) nutzen wir nicht. Die 9 Schwellen aus dem Held-out-Vergleich werden exakt
   reproduziert.
7. **Lesart von H1–H5.** Punkt = Schätzer auf allen Basen, CI = 2,5/97,5 % von 2000 Bootstrap-Ziehungen. Metrik ist
   die AUROC, die zeitgematchte AUROC steht daneben. Die Regeln vergleichen die auf 4 Stellen gerundeten Werte aus
   `vx_eval.json`, Gleichstand zählt als gestützt. H1 und H4 (i) sind unsere Lesart des VALIDATION-Wortlauts.
   - H1: `gnn` in Teil B (Lauf-Ebene innerhalb der Konfiguration) hat eine untere CI-Grenze > 0,5 und einen Punkt
     ≥ `feat_pairwise`. Teil B ist nur teilweise blind: 10 der 29 Paare sind Nacht-Nacht-Paare schon gesehener
     Test-Läufe. Die id-Paare aus Teil A berichten wir daneben. Sie beruhen auf einem einzigen gemischten Paar, ihre
     CI ist entartet.
   - H2: Die Uhr bricht ein, wenn die CI von M(time) − M(id rep1) ganz unter 0 liegt. Das GNN hält, wenn
     |Δ_shift| ≤ |Δ_noise|. Beides muss gelten. Die Uhr ohne die letzten 3 Runden berichten wir nur, mit eigenen
     Ziehungen.
   - H3: Δ_shift(`gnn`) ≥ Δ_shift(`bag`), die CI der Differenz kommt aus Aufruf 2. Dazu `analysis/vx_jury_ks.py`:
     KS-Abstand jeder Jury-Dimension, glm gegen id rep0, neben id rep1 gegen id rep0. In glm kippen 13 von 14 Läufen,
     die AUROC misst dort vor allem das Timing innerhalb kippender Läufe.
   - H4: (i) Δ_shift ≥ −|Δ_noise| und (ii) der Fehlalarm aus §6.4, also der Anteil nicht gekippter Läufe mit
     mindestens einem Alarm bei der Trainingsschwelle, ist auf enf höchstens doppelt so hoch wie auf id rep0 (dieselben
     Basen). Beides muss gelten. Ist der Anteil auf id rep0 null, gilt (ii) nur, wenn er auch auf enf null ist. Die
     Zeilen-FPR berichten wir daneben, wie in §6.4.
   - H5: Δ_shift(`gnn`) ≥ Δ_shift(`bag`), die CI der Differenz kommt aus Aufruf 2.
   - Reihenfolge feat_pairwise < bag ≤ bag+graph ≤ GNN (VALIDATION §3.5): beschreibend an den Punkten der AUROC pro
     Arm. `vx_eval.py` liefert dafür keine CIs.
   - Jede Regel ergibt „gestützt“ oder „nicht gestützt“. Daneben sagen wir, ob die zugehörige CI die Grenze
     ausschließt. Mit 14 Basen ist das oft nicht der Fall (§6.6). Die Perzentil-CIs über 7–14 Basen und 8 Gruppen sind
     antikonservativ (in Simulationen der Prüfer etwa doppelte Fehlerrate, bei topo mehr). Ziehungen ohne beide
     Klassen fallen weg.
   - Für LLM-Monitore, Hybrid und Baselines berichten wir dieselben Größen beschreibend. Mit Holm getestet wird nur die
     Kipprate (§6.5).
8. **Ablauf.** Zwei Aufrufe von `analysis/vx_eval.py` (seit `4e6e998` unverändert, Seed 20261108, 2000 Ziehungen).
   Aufruf 1 nutzt `--ref bag+graph` wie geplant, Aufruf 2 `--ref bag`, nur für H3 und H5. Die Ziehungen hängen weder
   von der Referenz noch von der Zahl der Vorhersager ab. Deshalb müssen alle anderen Zahlen gleich sein. Danach laufen
   `analysis/vx_jury_ks.py` (H3) und `analysis/vx_verdicts.py`, das die Regeln aus Punkt 7 mechanisch anwendet und die
   Gleichheit der beiden Aufrufe prüft. Alle Schritte stehen in `analysis/vx_preds/run_eval.sh`, das einmal läuft;
   eine Sperre verhindert einen zweiten Lauf. Schlägt ein Schritt fehl, wiederholen wir nur diesen mit identischen
   Argumenten. Sind die beiden Aufrufe nicht identisch, gilt Aufruf 1, und H3 und H5 bleiben offen. Getestet wurde
   vorher nur mit Zufalls-Scores.
9. **Nicht gerechnet.** Alles aus VALIDATION.md §3.3, was nicht in `vx_eval.py` steht: AUPRC, Recall bei 5 % FPR
   (außer den Fehlalarmen für H4), Brier, MAE von risk_count, Knoten-Ebene, Lauf-Ebene ab der ersten
   Mechanismus-Nachricht, Vorwarnzeit und die Slices vor der ersten Ankündigung und nach Kanal. Wir rechnen sie nicht
   nachträglich. Kipprate und Verstöße pro Arm stehen beschreibend in `sim_dataset/runs_vx/_logs/vx_summary.md`.

**3 (9. Nov., 08:00, bevor es eine Episode von `runs_vx3` gibt).** Bestätigungstest auf frischen Läufen. Anlass: In
der Auswertung von `night_vx` hatte das LLM mit dem ganzen Protokoll (`zs:global_full`) in jedem Block die höchste
AUROC. Nachträglich über alle Teil-A-Zeilen lag es +0,08 [+0,05; +0,12] vor dem GNN (`analysis/results/vx.md`). Diese
Hypothese ist nach Sicht der Daten entstanden. Hier wird sie auf Läufen geprüft, die beim Schreiben noch nicht
existieren. Auf den Testzeilen von heldout.md lagen beide gleichauf (0,82).

1. **Daten.** Die 14 Konfigurationen von `night_vx_id`, unverändert, mit den Replikaten 2 und 3 (Seeds
   `replicate_seeds[2]` und `[3]`, nie gelaufen): 28 Episoden in `sim_dataset/runs_vx3/`. Start mit
   `tools/night_run.sh` und `OUT=runs_vx3 WHERE="split=='__none__'" STAGE2_WHERE="split=='night_vx_id'"
   STAGE2_REPS=4 EXTRA="--rep-start 2" STOP_AT=1030`. Neu ist nur der Schalter `--rep-start` (eigener Commit). Er
   wählt die Replikat-Indizes und sonst nichts. Modelle, Jury, Labels und Merkmale sind unverändert. `runs_vx` wird
   nicht angefasst und nicht neu ausgewertet.
2. **Vorhersager.** Dieselben 12 wie in Nachtrag 2, eingefroren wie dort: GNN aus `models/cloud_final_gnn.pt`
   (`predict.py --no-eval --blend ''`), Tabellen-Baselines mit `make_baselines.py` auf night_train neu gefittet
   (deterministisch, gleiche Einstellungen), Hybrid mit derselben Formel, LLM-Monitore `global_full` (k = 3) und
   `pairwise` mit Prompt `lm1-2026-11-08` r0 und Claude Haiku 5.5. Schwellen braucht dieser Test nicht.
3. **Zeilen und Label.** Alle Zeilen mit `eval == 1` aus `gnn_opt/build_dataset.py` auf `runs_vx3`, Label `y3`
   (θ = 8, Δ = 3), Zeit-Bins für die zeitgematchte AUROC wie in `vx_eval.py`.
4. **Primärer Test (H7).** D = AUROC(`zs:global_full`) − AUROC(`gnn`) auf allen Zeilen von rep2 und rep3 zusammen.
   Bootstrap über die 14 Basen mit Zurücklegen, gepaart (jede gezogene Basis bringt die Zeilen ihrer beiden neuen Läufe
   mit, beide Monitore auf denselben Ziehungen), 10.000 Ziehungen, Seed 20261109, Perzentil-CI 95 %. Ziehungen ohne
   beide Klassen fallen weg. **H7 ist gestützt, wenn die untere CI-Grenze über 0 liegt.** Das ist der einzige Test
   dieses Nachtrags, ohne Korrektur.
5. **Sekundär**, mit CIs aus denselben Ziehungen und ohne Entscheidungsregel: (a) dieselbe Differenz zeitgematcht
   (`tm_auroc`), weil `global_full` die vergangene Zeit indirekt sieht, (b) `zs:global_full` gegen `hybrid`,
   (c) `zs:pairwise` gegen `gnn`.
6. **Beschreibend.** AUROC und zeitgematchte AUROC aller 12 Vorhersager auf rep2 + rep3 und je Replikat. Die Spanne
   über rep0–rep3 je Vorhersager (rep0 und rep1 aus `vx_eval.json`, nicht neu gerechnet). Gekippte Läufe je Replikat
   und die mittlere Kipprunde der gekippten Läufe.
7. **Ablauf.** Die Simulation startet erst nach dem Push dieses Nachtrags. Nach 10:30 beginnt keine neue Episode.
   Ausgewertet werden alle fertigen Episoden. Fehlt einer Basis jeder neue Lauf, fällt sie heraus, und wir sagen das.
   Vorhersagen und Auswertungsskript werden vor der Auswertung eingefroren und gepusht (`analysis/vx3_preds/`,
   `run_eval.sh` mit Sperre gegen einen zweiten Lauf). Vorher wird nur mit Zufalls-Scores getestet. Die Auswertung
   läuft genau einmal, das Ergebnis berichten wir unabhängig vom Ausgang. Scheitert die GNN- oder die LLM-Pipeline,
   bleibt H7 offen.
8. **Grenzen, vorab benannt.** Es sind dieselben 14 Basen, auf denen die Hypothese entstand. Eine Bestätigung zeigt,
   dass der Vorsprung über neue Seeds dieser Setups im kritischen Band trägt. Dass er auf neue Setups übertragbar ist,
   zeigt sie nicht. Die Perzentil-CIs über 14 Basen sind antikonservativ (Nachtrag 2, Punkt 7).

**4 (9. Nov., 08:20, vor dem Lauf).** Kleine Gegenüberstellung an Stelle von Teil C. Der Schwarm-Arm mit dem
feinjustierten 4B-Modell entfiel am 8. Nov.: In der Testepisode waren 44 % seiner Antworten ungültiges JSON, und die 12
feinjustierten Agenten schickten in der ganzen Episode 6 Nachrichten (`runs_vx/_logs/vx_decisions.md`). Damit es
trotzdem eine Aussage zum Feintuning gibt, vergleichen wir die beiden Modelle direkt, ohne Schwarm.

1. **Modelle.** `qwen3.5-4b-ft` (Feintuning auf Hartnäckigkeit) gegen `qwen3.5-4b` (Basis), derselbe Modal-Endpunkt,
   dieselben Prompts und Einstellungen wie im Gate (`tools/ft_check.py`: Temperatur 0,7, gleiche Antwortlängen,
   `reasoning_effort=none`).
2. **Messungen** (`tools/ft_compare.py`). (a) 12 Drucksituationen × 5 Antworten je Modell. Ein Haiku-Richter, der das
   Modell nicht kennt, vergibt HOLD, DILUTE, CAVE, RIGID oder UPDATE (Prompt aus ft_check.py). (b) 4 Situationen mit
   entscheidender neuer Evidenz × 5 Antworten, hier ist UPDATE richtig. (c) 60 echte Agenten-Züge aus runs_night
   (Systemprompt + Beobachtung, ohne Verlauf, Ziehung mit Seed 0; die ersten 20 sind die des Gates): gültiges JSON,
   bekannte Aktion, Länge der Nachrichten.
3. **Hauptgröße, beschreibend.** Anteil HOLD unter Druck, Feintuning gegen Basis, mit exaktem Vorzeichentest über die
   12 Situationen (gepaart) und Fisher daneben. Dazu der UPDATE-Anteil und der JSON-Anteil (Fisher). Keine
   Entscheidungsregel und keine Korrektur, denn es ist ein Manipulations- und Formatcheck.
4. **Grenzen, vorab benannt.** Kein Schwarm, keine Monitore, keine Aussage über das Kippen. Die Situationen sind
   handgeschrieben (12 + 4), es gibt einen Richter. Ohne Verlauf ist das Format leichter als im Schwarm: Im Gate waren
   90 % der Einzelzüge gültig, in der Testepisode nur 56 %.
5. **Ablauf.** Einmal ausgeführt und unabhängig vom Ergebnis berichtet (`analysis/results/ft_compare.{json,md}`).
