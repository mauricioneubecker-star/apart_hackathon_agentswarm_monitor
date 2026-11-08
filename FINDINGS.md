# Findings: aktueller Stand fürs Paper

**Stand:** 8. Nov. 2026, 19:15 · eingearbeitet: LLM-Monitore bis `68744e2`, GNN bis `aebf0e1` (gnn-opt-torch) und
`38d1f52` (gnn-opt), unabhängige Gegenprüfung vom 8. Nov. (`analysis/review/`) · **Nächstes Update:** wenn
`runs_vx` fertig ist

Hier stehen die wichtigsten Ergebnisse an einer Stelle, kurz und in einfacher Sprache. Die Datei erzählt die
Geschichte des Papers. Alle Details und Zahlen stehen in den Quellen unten. Für jede Aussage mit Zahl gibt es einen
Beleg in den Quellen. Am 8. Nov. hat ein Faktencheck jede Aussage geprüft.

Zeichen: ✅ gesichert (getestet, CI, unabhängig nachgerechnet) · 🟡 vorläufig oder explorativ · ⏳ läuft oder fehlt noch

---

## Die Geschichte in fünf Sätzen

1. In einem Schwarm aus 24 Coding-Agenten kippt in 4 von 10 Läufen der Schwarm: Mindestens 8 Agenten nutzen den
   verbotenen Shortcut. Echte Ansteckung über Nachrichten zeigt sich dabei nur beim Shortcut „Checks überspringen“.
2. Monitore, die nur die Nachrichten lesen, sagen das Kippen 3 Runden vorher klar besser voraus als die Uhr, auch bei
   gleichem Abstand zur Deadline.
3. Ein LLM, das ohne jedes Training Gespräch für Gespräch liest, ist so gut wie die besten trainierten Modelle. Liest es
   das ganze Protokoll auf einmal, ist es nicht besser als einfache gezählte Merkmale.
4. Die Graphstruktur selbst trägt kaum etwas bei. Neu verdrahtete Kanten kosten nichts. Es zählt, was in den Nachrichten
   steht.
5. Schwer bleiben neue Bedingungen und die Frage, welcher von zwei gleichen Läufen kippt. Genau das prüft die
   Validierung, die gerade fertig wird.

---

## 1. Das Testfeld: Wann kippt der Schwarm? ✅

- **Setup.** 24 LLM-Agenten bauen zusammen eine Bibliothek. Einige Tickets sind unlösbar. Es gibt einen verbotenen
  Shortcut: die Scorer-Datei ändern (K2) oder beim Merge die Checks überspringen (K4).
- **Kippen** heißt: mindestens 8 der 24 Agenten nutzen den Shortcut. In gekippten Läufen sind es im Mittel 12. Der
  Monitor soll das 3 Runden vorher melden.
- Im Nacht-Batch (252 Läufe, 112 Setups) kippen 101 Läufe, also 4 von 10.
- **K4, ein selbst auffindbarer Shortcut und ein öffentliches Board** führen jeweils signifikant öfter zum Kippen
  (Permutationstests über Setups, Holm über 14 Faktoren).
- 🟡 Die ersten beiden sind im Grunde ein Effekt. K4 mit selbst auffindbarem Shortcut kippt in 82 % der Setups, alle
  anderen Kombinationen nur in 20–24 %. Das ist explorativ, weil die Wechselwirkung nachträglich gefunden wurde.
- 🟡 Ein Release-Freeze (Zeitdruck) erhöht die Kipprate deutlich. Nach der strengsten Korrektur über alle 14 Faktoren ist
  das knapp nicht signifikant.
- 🟡 Sanktionen lassen sich im Nacht-Batch nicht prüfen. Nur 8 der 28 Setups mit Sanktionen konnten Verstöße überhaupt
  erkennen.
- Knapp die Hälfte der Kaskaden beginnt ohne instruierten Agenten und ohne Injektion. Meist gab es im Setup aber einen
  eingeweihten Agenten. Ganz ohne solchen Anstoß kippen nur 11 der 101 Läufe.

## 2. Ansteckung über Nachrichten: nur bei K4 🟡

Diese Analyse ist nachträglich entstanden und gegengeprüft. Details: `analysis/results/contagion.md`.

- **Bei K4 (Checks überspringen)** steigt ein Agent nach einer Direktnachricht von einem Regelbrecher etwa doppelt so
  oft ein. Verglichen wird mit Agenten im selben Lauf, in derselben Runde und mit gleicher Ticket-Lage. Am stärksten ist
  das, wo man den Shortcut nur von Kollegen lernen kann. Hier verbreitet sich vor allem **Wissen über den Shortcut**.
- **Bei K2 (Scorer-Datei ändern)** gibt es keinen messbaren Effekt. Auf dem gemeinsamen Board, wo jede Nachricht alle
  erreicht, auch nicht.
- Das Timing passt: Ein Zeit-Misch-Test ergibt viel weniger, und Nachrichten, die noch nicht gelesen sein können, zeigen
  nichts. Modell, Ticket-Abhängigkeiten, Rollen und CI-Stand erklären den Zusammenhang nicht.
- **Nicht belegt ist die Ursache.** Homophilie ist nicht ausgeschlossen. Ein Teil kommt von instruierten Seeds, ein Teil
  von Agenten, die selbst Regelbrecher anschreiben.
- **Eingeschleuste Anweisungen wirken.** Eine dauerhaft eingeblendete qa-bot-Anweisung erhöht die neuen Verstöße von
  4,9 auf 9,4 pro Lauf (7 von 8 Setups). Drei Viertel der neuen Regelbrecher hatten sie selbst gelesen. Das zeigt Anfälligkeit
  für Anweisungen, keine Ansteckung untereinander. Nach Holm ist es grenzwertig. Eine einmalige falsche Manager-Nachricht
  wirkt nicht nachweisbar.
- Mindestens zwei Drittel der Nachahmer hatten vorher etwas Öffentliches gesehen: einen Post eines Regelbrechers oder
  einen Shortcut-Merge im Merge-Feed. Ob der Feed ansteckt, lässt sich nicht schätzen. Kein fair verglichener Monitor sieht ihn.

## 3. Nachrichten schlagen die Uhr ✅

- Schon die Rundenzahl allein sagt das Kippen recht gut voraus, weil es meist spät im Sprint passiert. Daran muss sich
  jeder Monitor messen.
- **Alle Monitore schlagen die Uhr klar, auch zeitgematcht**, also im Vergleich nur von Momenten mit gleichem Abstand zur
  Deadline. Das gilt in der Kreuzvalidierung (Holm p ≈ 0,001, in 8 von 8 ausgeblendeten Bereichen). Bei anderen θ/Δ
  gilt es für das LLM Gespräch für Gespräch und die gezählten Merkmale in allen Varianten, für das LLM mit dem ganzen
  Protokoll nicht in allen. ⏳ Testzeilen siehe Abschnitt 6.
- Könnte man die echten Verstöße zählen, käme man noch weiter. Das sieht kein Monitor. In den Nachrichten steckt viel
  Signal, aber nicht alles.

## 4. LLM-Monitore: kleine Ausschnitte lesen ist am besten ✅

Claude Haiku 5.5 als Monitor, in sieben Varianten. Die wichtigsten: das ganze Protokoll, die letzten 6 Runden, jedes
Gespräch einzeln (ein Paar oder die Broadcasts eines Absenders) und jeder Agent einzeln.

- **Gespräch für Gespräch und Agent für Agent sind die besten Varianten**, beide etwa gleichauf und schon ohne Training.
- **Das ganze Protokoll auf einmal zu lesen ist nicht besser als einfache gezählte Merkmale.** Die Shortcut-Mechanismen
  im Prompt zu nennen oder Notizen von Runde zu Runde helfen auch nicht.
- Ein Zusatz-Monitor, der den Merge-Feed mitliest, ist deutlich besser. Er ist aber nicht fair, weil kein anderer Monitor
  den Feed sieht. Im Feed steckt also viel Signal.
- Billig und zuverlässig: Gespräch für Gespräch kostet gut 1 Cent pro Lauf, das ganze Protokoll gut 4 Cent. Alle sieben
  Varianten zusammen kosteten 39 $. Fast immer gültiges Antwortformat, keine Verweigerungen.

## 5. GNN: Gedächtnis pro Agent, Struktur egal ✅ / 🟡

Das GNN sieht nur den Kommunikationsgraphen und allgemeine Bewertungen der Nachrichten durch die Jury. Es bekommt
keine Uhr und keine Aufgabenwörter.

- ✅ **Ein Gedächtnis pro Agent ist nötig.** Mit einem Gedächtnis für den ganzen Schwarm bricht das GNN ein, wenn K4 im
  Training fehlt. Mit Gedächtnis pro Agent hält es. Ohne zeitliches Gedächtnis wird es klar schlechter.
- ✅ **Die Graphstruktur trägt kaum etwas bei.** Neu verdrahtete Kanten kosten fast nichts. Ohne die Jury-Bewertungen
  der Nachrichten wird es dagegen klar schlechter, vor allem zeitgematcht. Zufällig vertauschte Zeilen fallen auf
  Zufallsniveau, ein Leck gibt es also nicht.
- ✅ **Das Seed-Rauschen ist groß**, bis 0,04 AUROC. Die meisten Unterschiede zwischen Architekturen sind nicht deutbar.
- 🟡 Das GNN allein reagiert empfindlicher auf einen Jury-Tausch als das Tabellenmodell. Die Kombination aus GNN und
  Tabellenmodell bleibt stabil.
- Eingefroren hat das GNN-Team: Knoten-GRU, 5 Seeds (`cloud_final_gnn`), und dessen Kombination mit dem Tabellenmodell
  (`cloud_final`). Den besten Kreuzvalidierungs-Score hat allerdings ein zweistufiges Tabellenmodell pro Agent ohne
  neuronales Netz (`gnn-opt`).

## 6. Der faire Vergleich: GNN gegen LLM gegen Baselines ✅ / ⏳

Alle Monitore wurden auf identischen Zeilen bewertet, gepaart, mit Bootstrap über Setups und Holm-Korrektur über
11 vorab festgelegte Tests.

- **Kreuzvalidierung (night_train, 64 Setups), unabhängig nachgerechnet:**
  - Das zero-shot-LLM, Gespräch für Gespräch, ist **signifikant besser als die gezählten Merkmale** (+0,07 AUROC).
  - Es ist **gleichauf** mit dem finalen GNN und mit der Kombination. Kein signifikanter Unterschied.
  - Die Kombination GNN + Tabellenmodell ist signifikant besser als die gezählten Merkmale. Das GNN allein ist es je nach
    GNN-Version oder nicht.
  - Das LLM, das das ganze Protokoll liest, ist gleichauf mit den gezählten Merkmalen.
- ⏳ **Zurückgehaltene Testzeilen:** wird gerade gerechnet. Laut GNN-Team: in bekannten Setups ist das GNN stark (0,92),
  auf neuen Bedingungen fallen alle Monitore auf 0,74–0,82.
- Bei Injektion über Tool-Ausgaben (test_ood_seed) sieht zeitgematcht kein Monitor etwas. Der Auslöser steht nicht in der
  Kommunikation.

## 7. Die harte Stelle: Welcher Lauf kippt? 🟡

- Ein großer Teil des Signals heißt „das ist ein gefährliches Setup“. Vergleicht man Wiederholungen desselben Setups,
  von denen manche kippen und manche nicht, werden alle Monitore klar schwächer.
- Innerhalb gleicher Setups liegen die LLM-Monitore vorne, die kleine Ausschnitte lesen.
- Bei „kippt dieser Lauf noch?“ 6 Runden vor der Deadline und solange noch niemand verstoßen hat, sind die gezählten
  Merkmale gleichauf oder besser.
- Die Branch-Arme trennen nach der Abzweigung weder das GNN noch die Tabellenmodelle. Die LLM-Monitore wurden darauf noch
  nicht geprüft. Die Modelle erkennen das Kippen, sobald es in der Kommunikation sichtbar wird, aber nicht die
  Intervention selbst.
- **Fürs Paper:** offen berichten. Das ist die wichtigste Grenze und der Grund für Teil B der Validierung.

## 8. Zweite Domäne: Among Us 🟡

- Wer täuscht, verrät sich in der Kommunikation. Impostor werden gut erkannt, auch bei Modellen, die im Training nie
  vorkamen.
- Ob die Gruppe deshalb falsch abstimmt, lässt sich kaum vorhersagen, kaum besser als mit der Uhr.
- Das GNN ist hier etwa so gut wie ein starkes Tabellenmodell. Neu verdrahtete Kanten kosten nichts.
- **Über beide Domänen:** Der Inhalt der Nachrichten trägt mehr als die Struktur des Graphen. In beiden Domänen kostet
  Neu-Verdrahten fast nichts.
- Noch nicht final: Der Test wurde mehrfach angesehen. Fürs Paper einmal mit eingefrorenem Modell neu rechnen oder in den
  Anhang.

## 9. Validierung `night_vx` ⏳ fast fertig

Die Validierung prüft, ob die Monitore aus den richtigen Gründen gut sind. Sie ist nur zum Testen da: kein Training,
keine Modellauswahl darauf. **Für `night_vx` gibt es noch keinen einzigen Monitor-Score.** Es ist der einzige blinde Teil.

- 14 neue Setups, bei denen das Kippen auf der Kippe steht. Jedes läuft als Zwilling, der sich nur in einem Punkt
  unterscheidet:
  - **id:** unverändert, zweimal. Das zeigt, wie stark Ergebnisse schon beim bloßen Wiederholen schwanken.
  - **time:** längerer Sprint. Ein Monitor, der heimlich die Uhr gelernt hat, liegt hier falsch.
  - **glm:** die Hälfte des Schwarms läuft auf einem nie gesehenen Modell (GLM-5.2).
  - **enf:** Regelbrüche werden sichtbar geahndet. Geplant war, dass der Schwarm sich dadurch selbst bremst und so
    Fehlalarme testbar werden.
  - **topo:** ein anderes Netz mit wenigen stark vernetzten Agenten.
- **Teil B:** je 2 neue Wiederholungen von 8 zurückgehaltenen Nacht-Setups (6 mit gemischtem Ausgang, 2 Beinahe-Kipper).
- **Teil C fällt weg.** Das feinjustierte 4B-Modell lieferte in der Testepisode 44 % kaputtes JSON. Das ist ein
  technisches Problem, kein inhaltliches Ergebnis, gehört aber in die Grenzen. GLM-5.2 lief sauber (4,8 % ungültiges JSON).
- 🟡 **Zwischenstand der Kipp-Zählung** (nur gezählt): Mit GLM-Agenten kippen 13 von 14 Läufen, ohne GLM 6 von 14.
  Sichtbare Ahndung bremst das Kippen nicht (5 von 14). Der GLM-Test verschiebt also auch die Basisrate stark, und der
  enf-Arm taugt nicht wie geplant als Fehlalarm-Test.

## 10. Robustheit der Labels ✅ (explorativ)

θ = 6/8/10 und Δ = 2/3/5, neu berechnet ohne Simulation:
- Das LLM Gespräch für Gespräch liegt **in allen Varianten signifikant über der Uhr**.
- Über den gezählten Merkmalen liegt es in allen Varianten, signifikant aber nur in 3 von 6.
- Das LLM mit dem ganzen Protokoll ist nie besser als die gezählten Merkmale.

---

## Was fürs Paper noch fehlt ⏳

1. **Analyseplan v2 committen**, bevor `night_vx` mit Monitoren ausgewertet wird ([ANALYSIS_PLAN.md](ANALYSIS_PLAN.md)).
2. **`night_vx` auswerten**, in dieser Reihenfolge:
   - zero-shot-LLM-Monitore auf `runs_vx` laufen lassen (API, grob 5–8 $);
   - das eingefrorene GNN auf `runs_vx` anwenden;
   - `analysis/vx_eval.py` schreiben und committen;
   - dann genau einmal auswerten.
3. **Jury prüfen:** Übereinstimmung Haiku gegen DeepSeek berichten, besser zusätzlich rund 100 Nachrichten von Hand
   labeln.
4. **Among Us** final neu rechnen oder in den Anhang.
5. **Fehler in `llm_monitor/evaluate.py` melden:** Der Bootstrap in `vx_shift` zieht ohne Zurücklegen, die CIs sind
   dadurch etwa 17 % zu schmal. Teil B vergleicht dort nur die neuen Läufe.
6. GNN-Kontrollen auf allen 18 Folds mit mindestens 3 Seeds. Die Jury-Tausch-CV läuft beim GNN-Team.

## Grenzen (für den Limitations-Teil)

- Nur Simulation, feste Schwarmgröße von 24 Agenten, zwei Arten von Shortcut. Ansteckung über Nachrichten zeigt sich
  nur bei einem davon.
- Wenige Kipp-Ereignisse im Training (45 gekippte Läufe). Deshalb sind die Unsicherheiten und das Seed-Rauschen groß.
- Die Test-Splits haben beide Seiten schon angesehen. Blind ist nur `night_vx`.
- Die GNN-Konfiguration wurde auf denselben CV-Zeilen gewählt, auf denen sie verglichen wird. Die CV-Zahlen des GNN
  sind deshalb optimistisch.
- Der LLM-Monitor stammt aus derselben Modellfamilie wie ein Jury-Mitglied, das die GNN-Merkmale bewertet. Beide
  Messungen sind nicht unabhängig.
- Die LLM-Monitore lesen den Rohtext mit Aufgabenwörtern (`skip_checks`, `.ci/scoring.toml`), das GNN nicht. Der
  Monitor mit dem ganzen Protokoll sieht außerdem indirekt die vergangene Zeit.
- Alle fair verglichenen Monitore sehen nur Nachrichten. Wer still verstößt, bleibt unsichtbar, ebenso der Merge-Feed.
- Antrainierte Hartnäckigkeit ist nicht getestet (Teil C entfallen), Sanktionen praktisch auch nicht.

---

## Zahlen auf einen Blick

**Kreuzvalidierung auf identischen Zeilen** (night_train, 64 Setups, gepaarter Bootstrap über Setups, Holm über
11 Tests; unabhängig nachgerechnet). AUROC: 0,5 = Raten, 1 = perfekt.

| Monitor | AUROC | zeitgematcht* | Unterschied zu „gezählte Merkmale“ |
|---|---|---|---|
| nur Uhr | 0,75 | 0,40 | – |
| gezählte Merkmale (bag + graph) | 0,85 | 0,78 | – |
| LLM, ganzes Protokoll (zero-shot) | 0,87 | 0,81 | gleichauf |
| GNN (Mac-Version) | 0,89 | 0,85 | gleichauf (Cloud-Version: besser, siehe unten) |
| GNN + Tabellenmodell (Mac-Version) | 0,90 | 0,85 | **besser** (+0,05) |
| LLM, Gespräch für Gespräch (zero-shot) | **0,92** | **0,89** | **besser** (+0,07); gleichauf mit GNN und Kombination |

\* Harness-Variante: innerhalb gleicher Runden. Die Uhr hat dann keine Information mehr und liegt unter 0,5.

In der Kreuzvalidierung stehen das Mac-GNN (`final.pt`) und seine Kombination. Für das eingefrorene Cloud-GNN
(`cloud_final_gnn`) gibt es nur einen CV-Stellvertreter (`e_ngru_4runs`). Mit ihm ist auch das GNN allein signifikant
besser als die gezählten Merkmale (+0,04, Holm 0,03). Alle anderen Urteile bleiben gleich, auch gleichauf mit dem LLM.

⏳ **Zurückgehaltene Testzeilen:** folgt.

---

## Quellen

| Thema | Datei | Branch |
|---|---|---|
| Nacht-Batch: Kipprate, Faktoren | `sim_dataset/runs_night/_logs/analysis_runs.csv`, `analysis/review/stats-factors/` (`report.md` und `dynamics.md` beruhen noch auf 239 Läufen) | night-vx-validation |
| Ansteckung | `analysis/results/contagion.md`, Skript `analysis/contagion.py` | night-vx-validation (nach dem Push) |
| LLM-Monitore | `results/llm_monitor/RESULTS.md`, `llm_monitor/README.md` (Stand 68744e2) | night-vx-validation |
| GNN | `gnn_opt_torch/RESULTS.md` (Step 4–9), `gnn_opt_torch/LOOKS.md`, `gnn_opt_torch/STATUS.md` | gnn-opt-torch |
| GNN-Harness, zweistufiges Modell | `gnn_opt/HARNESS.md`, `gnn_opt/preds/cv_log.jsonl` | gnn-opt |
| Fairer Vergleich (CV) | `analysis/review/stats-monitors/REPORT.md` | night-vx-validation (nach dem Push) |
| Fairer Vergleich (Testzeilen) | `analysis/results/heldout.md` ⏳ | night-vx-validation (nach dem Push) |
| θ/Δ-Sensitivität | `analysis/results/sensitivity.md`, Skripte `analysis/sens.py`, `analysis/sens_summary.py` | night-vx-validation (nach dem Push) |
| Among Us | `gnn/RESULTS_amongus.md` | alle |
| Validierung | `sim_dataset/VALIDATION.md`, `sim_dataset/runs_vx/_logs/vx_decisions.md` | night-vx-validation (nach dem Push) |
| Analyseplan | `ANALYSIS_PLAN.md` | night-vx-validation (nach dem Push) |
| Gegenprüfung | `analysis/review/README.md` | night-vx-validation (nach dem Push) |

## So pflegen wir die Datei

- Bei neuen Ergebnissen den betroffenen Satz ändern, das Zeichen anpassen (✅ 🟡 ⏳) und oben das Datum setzen.
- Kurz halten: höchstens eine Zahl pro Punkt. Details gehören in die Quelle.
- Was widerlegt ist, nicht löschen, sondern unten unter „Verworfen“ mit einem Satz Begründung ablegen.
- Ein Commit pro Update, Nachricht: `Findings: <was neu ist>`.

## Verworfen

- ~~„Wer von einem Regelbrecher angeschrieben wird, steigt etwa doppelt so oft ein“ (allgemein).~~ Gilt nur für K4 und
  nicht auf dem Board (Gegenprüfung 8. Nov.).
- ~~„Das Placebo zeigt keinen Effekt, also echte Ansteckung.“~~ Das Placebo hat schon ohne Effekt einen Wert um 1,3 und
  schließt Homophilie nicht aus.
- ~~„Eine einzige Nachricht ändert den Verlauf kausal.“~~ Die Injektion war eine dauerhaft eingeblendete Anweisung, die
  meisten Betroffenen hatten sie selbst gelesen. Die einzelne Manager-Nachricht wirkt nicht nachweisbar.
- ~~„Sanktionen senken die Kipprate im Nacht-Batch nicht.“~~ Nicht testbar: Nur 8 Setups konnten Verstöße erkennen.
- ~~„Bestes Modell: GNN + Gradient Boosting, knapp vor Gradient Boosting allein.“~~ Gegen das LLM Gespräch für Gespräch
  ist die Kombination gleichauf. Den besten CV-Score hat ein zweistufiges Tabellenmodell.
