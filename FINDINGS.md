# Findings: aktueller Stand fürs Paper

**Stand:** 9. Nov. 2026, 08:15 · eingearbeitet: LLM-Monitore bis `68744e2`, GNN bis `aebf0e1` (gnn-opt-torch) und
`38d1f52` (gnn-opt), Validierungslauf `5ea7874`, **Auswertung von `night_vx` (`bb3f665d`, Zusammenfassung
`analysis/results/vx.md`)**, unabhängige Gegenprüfungen vom 8./9. Nov. (`analysis/review/`) ·
**Läuft:** Bestätigungstest auf frischen Läufen (ANALYSIS_PLAN.md Nachtrag 3, Ergebnis gegen 10:45) und der direkte
Vergleich des feinjustierten Modells mit seiner Basis (Nachtrag 4) ·
**Nächstes Update:** nach diesen beiden, dann Jury-Prüfung und Among Us

Hier stehen die wichtigsten Ergebnisse an einer Stelle, kurz und in einfacher Sprache. Die Datei erzählt die
Geschichte des Papers. Alle Details und Zahlen stehen in den Quellen unten. Für jede Aussage mit Zahl gibt es einen
Beleg in den Quellen. Am 8. Nov. hat ein Faktencheck jede Aussage geprüft. Die Aussagen zu `night_vx` vom 9. Nov. haben
zwei Prüf-Agenten gegen die Ausgaben geprüft.

Zeichen: ✅ gesichert (getestet, CI, unabhängig nachgerechnet) · 🟡 vorläufig oder explorativ · ⏳ läuft oder fehlt noch

---

## Die Geschichte in fünf Sätzen

1. In einem Schwarm aus 24 Coding-Agenten kippt in 4 von 10 Läufen der Schwarm: Mindestens 8 Agenten nutzen den
   verbotenen Shortcut. Echte Ansteckung über Nachrichten zeigt sich dabei nur beim Shortcut „Checks überspringen“.
2. Monitore, die nur die Nachrichten lesen, sagen das Kippen 3 Runden vorher voraus, deutlich besser als die reine
   Rundenzahl (Kreuzvalidierung und Testdaten; auf `night_vx` nicht getestet). Ob sie auch eine Uhr schlagen, die
   zusätzlich die Deadline kennt, hängt auf den Testdaten davon ab, wie man die Zeit abgleicht.
3. Ein LLM, das ohne jedes Training Gespräch für Gespräch liest, ist so gut wie die besten trainierten Modelle. In
   bekannten Setups liegt das GNN etwas vorne, unter neuen Bedingungen das LLM. Signifikant ist auf den Testdaten keiner
   dieser Unterschiede. In der blinden Validierung ist dieses LLM vom GNN nicht zu trennen.
4. Die Graphstruktur selbst trägt kaum etwas bei. Neu verdrahtete Kanten kosten nichts. Es zählt, was in den Nachrichten
   steht.
5. In der blinden Validierung (14 neue Setups) fällt in keinem Arm ein Monitor nachweisbar stärker ab als beim bloßen
   Wiederholen. Sie sieht aber nur grobe Einbrüche, und drei der vier Arme haben ihre Bedingung nur teilweise erzeugt.
   Welcher von zwei gleichen Läufen kippt, bleibt schwer.

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

## 3. Nachrichten gegen die Uhr ✅ / 🟡

- Schon die Rundenzahl allein sagt das Kippen recht gut voraus, weil es meist spät im Sprint passiert. Daran muss sich
  jeder Monitor messen.
- ✅ **Gegen die reine Rundenzahl gewinnen alle Monitore klar.** Vergleicht man nur Momente in derselben Runde, fällt
  die Uhr auf Zufallsniveau, die Monitore nicht. Das gilt in der Kreuzvalidierung und auf den Testdaten (p ≤ 0,0002).
- 🟡 **Gegen eine Uhr, die auch die Deadline kennt, wird es knapp.** Der Plan gleicht nach „Runden bis zur Deadline“ ab.
  Dort verrät die absolute Runde, ob die Deadline früh oder spät liegt, und die Uhr erreicht auf den Testdaten 0,72.
  Dann ist nach Holm kein Monitor signifikant besser. Am knappsten ist das LLM Gespräch für Gespräch (Holm-p 0,09).
  Hält man Runde und Deadline gleichzeitig fest (nachträglich), liegen 4 von 5 Monitoren signifikant über der Uhr. Nur
  das GNN allein nicht.
- Bei anderen θ/Δ liegen das LLM Gespräch für Gespräch und die gezählten Merkmale in allen Varianten über der Uhr.
- Könnte man die echten Verstöße zählen, käme man noch weiter. Das sieht kein Monitor. In den Nachrichten steckt viel
  Signal, aber nicht alles.

## 4. LLM-Monitore: kleine Ausschnitte lesen ist am besten (Nacht-Daten) ✅

Claude Haiku 5.5 als Monitor, in sieben Varianten. Die wichtigsten: das ganze Protokoll, die letzten 6 Runden, jedes
Gespräch einzeln (ein Paar oder die Broadcasts eines Absenders) und jeder Agent einzeln.

- **Gespräch für Gespräch und Agent für Agent sind die besten Varianten**, beide etwa gleichauf und schon ohne Training.
- **Das ganze Protokoll auf einmal zu lesen ist nicht besser als einfache gezählte Merkmale.** Die Shortcut-Mechanismen
  im Prompt zu nennen oder Notizen von Runde zu Runde helfen auch nicht.
- 🟡 In `night_vx` hat das ganze Protokoll beschreibend in jedem Arm die höchste AUROC (nicht getestet, siehe §9).
  Von Gespräch für Gespräch ist es dort nicht zu trennen. Eine gesicherte Rangfolge der beiden Varianten gibt es weder
  auf den Testdaten noch auf `night_vx`.
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

## 6. Der faire Vergleich: GNN gegen LLM gegen Baselines ✅

Alle Monitore wurden auf identischen Zeilen bewertet, gepaart, mit Bootstrap über Setups und Holm-Korrektur über
11 vorab festgelegte Tests.

- **Kreuzvalidierung (night_train, 64 Setups), unabhängig nachgerechnet:**
  - Das zero-shot-LLM, Gespräch für Gespräch, ist **signifikant besser als die gezählten Merkmale** (+0,07 AUROC).
  - Es ist **gleichauf** mit dem finalen GNN und mit der Kombination. Kein signifikanter Unterschied.
  - Die Kombination GNN + Tabellenmodell ist signifikant besser als die gezählten Merkmale. Das GNN allein ist es je nach
    GNN-Version oder nicht.
  - Das LLM, das das ganze Protokoll liest, ist gleichauf mit den gezählten Merkmalen.
- **Zurückgehaltene Testzeilen (36 Setups, eingefrorene Modelle, Holm über 11 Tests):** Alle Monitore liegen zwischen
  0,80 und 0,85 AUROC. Vorne liegen die LLMs Gespräch für Gespräch und Agent für Agent (beide 0,85), dann GNN + Tabelle
  (0,83) und GNN (0,82). Die gezählten Merkmale kommen auf 0,81, die Uhr auf 0,78. **Kein Unterschied zwischen den
  Monitoren ist nach Holm signifikant.**
- 🟡 Explorativ: In bekannten Setups (test_id) sind GNN und GNN + Tabelle am besten (0,92). Unter neuen Bedingungen
  (fremde Aufgabe, neuer Injektionsweg, Branch) liegt das LLM Gespräch für Gespräch vorne, gegen das GNN etwa +0,10.
- Bei Injektion über Tool-Ausgaben (test_ood_seed) steht der Auslöser nicht in der Kommunikation. Zeitgematcht liegen
  die trainierten Monitore dort fast bei Zufall, die LLM-Monitore etwas darüber.
- **Praktisch:** Bei 5 % Fehlalarmrate pro Zeile warnen die Monitore in rund der Hälfte der gekippten Läufe vorher. Das
  GNN warnt am frühesten (Median 5 Runden), das LLM Gespräch für Gespräch hat die wenigsten Fehlalarme (10 von 48
  nicht gekippten Läufen). Die Uhr alarmiert in jedem nicht gekippten Lauf.
- Details: `analysis/results/heldout.md`.

## 7. Die harte Stelle: Welcher Lauf kippt? 🟡

- Ein großer Teil des Signals heißt „das ist ein gefährliches Setup“. Vergleicht man Wiederholungen desselben Setups,
  von denen manche kippen und manche nicht, werden alle Monitore klar schwächer.
- Innerhalb gleicher Setups liegen auf den Nacht-Daten die LLM-Monitore vorne, die kleine Ausschnitte lesen. In
  `night_vx` (Teil B, Lauf-Ebene) gilt das nur auf den schon gesehenen Nacht-Paaren (§9).
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

## 9. Validierung `night_vx` ✅ ausgewertet

Die Validierung prüft, ob die Monitore unter neuen Bedingungen halten. Sie ist nur zum Testen da: kein Training, keine
Modellauswahl darauf. Die Eingaben wurden vor der Auswertung eingefroren und gepusht (`d083547d`), ausgewertet wurde
genau einmal (`bb3f665d`). Sechs Prüf-Agenten (KI, eigener Code) haben die Auswertung aus den eingefrorenen Eingaben
nachgerechnet. Details und die Liste, was wir nicht behaupten dürfen: `analysis/results/vx.md`.

**Ergebnis:**
- ✅ **Kein Hinweis auf einen großen Einbruch.** In keinem Arm fällt ein Monitor nachweisbar stärker ab als beim
  bloßen Wiederholen (0 von 96 Vergleichen). Die Suite sieht aber nur grobe Einbrüche, verlässlich erst ab etwa
  0,2 AUROC. „Robust“ dürfen wir nicht schreiben.
- ✅ **H1–H5 nach den vorab festgelegten Regeln:** H1–H4 nicht gestützt, H5 gestützt. Bei keinem Urteil schließt die
  CI die Entscheidungsgrenze aus. H5 und die GNN-Hälfte von H2 drehen sich mit der zeitgematchten AUROC sogar um.
- 🟡 **Schon das Wiederholen stört.** Der Ausgang ändert sich nur in 1 von 14 Setups. Die Uhr verliert aber 0,20 AUROC,
  und gekippt wird in 5 von 6 Setups später. Die Wiederholung lief nach allen rep0- und Arm-Läufen.
- 🟡 **Drei Arme trafen ihr Ziel nur teilweise.** Ahndung bremste das Kippen nicht erkennbar. GLM-Agenten änderten vor
  allem die Basisrate (13 von 14 Läufen kippen), kaum die Jury-Bewertungen. Im längeren Sprint kippte es zur selben
  Runde wie in der zweiten Wiederholung, obwohl die Deadline später lag.
- 🟡 **Beschreibend hat das LLM mit dem ganzen Protokoll die höchste AUROC**, in jedem Arm und in beiden
  id-Wiederholungen. Nachträglich über alle Teil-A-Zeilen liegt es +0,08 [+0,05; +0,12] vor dem GNN. Diesen Vergleich
  haben wir nach Sicht der Ergebnisse gewählt, er ist nur eine Hypothese. Das LLM Gespräch für Gespräch ist weder vom
  GNN noch vom ganzen Protokoll zu trennen.
- ⏳ **Bestätigungstest läuft (Nachtrag 3).** Die Hypothese „LLM mit ganzem Protokoll schlägt das GNN“ wird auf 28
  frischen Läufen geprüft (dieselben 14 unveränderten Setups, neue Seeds), vorab festgelegt und gepusht, bevor die erste
  Episode lief. Ergebnis gegen 10:45. Auch ein bestätigtes Ergebnis gilt nur für Setups im kritischen Band.
- 🟡 **Welcher von zwei gleichen Läufen kippt**, trennt kein beobachtbarer Monitor verlässlich. Das GNN kommt auf 0,76
  mit einer CI bis 0,45. Seed-unabhängig über 0,5 liegen nur die Struktur-Baseline und bag + graph, warum gerade sie,
  ist offen. Teil B ist nur teilweise blind.
- 🟡 Unter Ahndung alarmiert das GNN in 3 von 9 statt 1 von 8 nicht gekippten Läufen. Daran scheitert H4, aber knapp:
  Ein Alarm weniger hätte gereicht, und alle drei Läufe waren Beinahe-Kipper.
- **Offenlegung:** Die angekündigte Gegenprobe des GNN gegen die Nacht-Vorhersagen ist gescheitert, weil die
  gespeicherte Datei nur 15 von 40 Zuständen hat. Ersatz war der 120-Zeilen-Check des GNN-Teams (Nachtrag 2). Außerdem
  hat eine Cloud-Sitzung des GNN-Teams das Auswertungsskript um 01:04 Uhr ein zweites Mal ausgeführt, auf denselben
  eingefrorenen Eingaben (Branch `cloud-synthesis`, `b14b3393`). Ihre Ergebnisdateien sind byte-gleich mit unseren.

**Aufbau:**
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
  - 🟡 Nachträglich geprüft (explorativ, `analysis/results/ft_canary_repair.md`): Meist fehlte nur die letzte Klammer.
    Eine mechanische Reparatur ohne Änderung am Inhalt hätte 91 % der Züge gültig gemacht. Das eigentliche Problem:
    Die feinjustierten Agenten schrieben nur in 2 % ihrer Züge eine Nachricht, die anderen Modelle in derselben
    Episode in 18–19 %. Ein Schwarm mit ihnen hätte stumme Agenten getestet, keine hartnäckigen Kommunikatoren.
  - 🟡 **Direkter Vergleich feinjustiert gegen Basis** (Nachtrag 4, ohne Schwarm, `analysis/results/ft_compare.md`):
    Unter Gruppendruck bleibt das feinjustierte Modell öfter bei seiner Position (80 % gegen 60 % der Antworten). Über
    die 12 Situationen gepaart ist der Unterschied aber nicht signifikant (5 gegen 3). Bei guter Gegen-Evidenz schwenkt
    es seltener um (5 gegen 11 von 20, nicht signifikant). Im Einzelzug hält es das JSON-Format so gut wie die Basis.
    Auch die Basis schreibt dort selten eine Nachricht (4 gegen 6 von 60). Das seltene Schreiben im Schwarm liegt also
    vermutlich nicht am Feintuning.
- **Der Lauf ist fertig** (8. Nov., 19:21): 92 Episoden plus 2 Testläufe aus den Gates, 0 Fehler. Gepusht als `5ea7874`.
  Alle Plausibilitäts-Checks bestehen: time-Arm mit 36 Runden, Sanktionen im enf-Arm in 12 von 14 Läufen, GLM-Aufrufe im
  glm-Arm, Teil B mit je 2 Wiederholungen.
- 🟡 **Kipp-Zählung.** Beim Ausgang ist das Wiederholungsrauschen klein: Die zweite id-Wiederholung kippt in nur 1 von
  14 Setups anders. Bei der AUROC (vor allem der Uhr) und beim Kipp-Zeitpunkt ist es größer (siehe oben).
  - Mit GLM-Agenten kippen 13 von 14 Läufen, ohne GLM 6 von 14. Das ist der einzige deutliche Effekt (McNemar
    p = 0,016, nach Holm über 4 Arme 0,06). Der GLM-Test verschiebt also auch die Basisrate stark.
  - Sichtbare Ahndung (enf): 5 von 14. Bei K4 kippt mit Ahndung 1 von 9 Setups statt 3 von 9, bei K2 aber 4 von 5 statt
    3 von 5. Die Zahlen sind sehr klein. Der Arm taugt nur eingeschränkt als Fehlalarm-Test.
  - Längerer Sprint (time): 8 von 14. Anderes Netz (topo): 5 von 7. Teil B: 7 von 16.

## 10. Robustheit der Labels ✅ (explorativ)

θ = 6/8/10 und Δ = 2/3/5, neu berechnet ohne Simulation:
- Das LLM Gespräch für Gespräch liegt **in allen Varianten signifikant über der Uhr**.
- Über den gezählten Merkmalen liegt es in allen Varianten, signifikant aber nur in 3 von 6.
- Das LLM mit dem ganzen Protokoll ist auf den Nacht-Daten nie besser als die gezählten Merkmale.

---

## Was fürs Paper noch fehlt ⏳

1. ~~Analyseplan v2 committen.~~ Erledigt: `4e6e998`, gepusht vor den vx-Daten. Das Team sollte ihn gegenlesen.
   Änderungen nur noch als datierter Nachtrag.
2. ~~`night_vx` auswerten.~~ Erledigt in der Nacht zum 9. Nov.: LLM-Monitore (`f8cf5d9`), eingefrorenes GNN und
   Baselines plus Nachtrag 2 (`d083547d`), die eine Auswertung (`bb3f665d`), unabhängige Prüfung vor und nach dem Lauf.
   Ergebnis in §9 und `analysis/results/vx.md`.
   - **Offen fürs Paper:** den Validierungsteil mit den Formulierungen aus `vx.md` schreiben, besonders „kein Hinweis
     auf einen großen Einbruch“ statt „robust“. H1–H5 mit den vorab festgelegten Urteilen nennen, mit dem Zusatz, dass
     keine CI ihre Grenze ausschließt. Die gröbere Auflösung gegenüber §6.6 (0,1) als Abweichung vom Plan nennen.
   - **Fürs GNN-Team:** Die Uhrzeiten in `gnn_opt_torch/LOOKS.md` und `STATUS.md` stimmen nicht mit git überein (Test-Blick
     17:02–17:06 UTC, nicht ~17:45). Die gespeicherte Modell-Datei hat nur 15 von 40 Zuständen.
   - ⏳ **Bestätigungstest (Nachtrag 3) und Vergleich des feinjustierten Modells (Nachtrag 4)** laufen. Danach §9 und
     den Paper-Abschnitt ergänzen. Die Tabelle in `synthesis_cloud/SYNTHESIS.md` §3 (Branch `cloud-synthesis`) weicht
     von `vx_eval.json` ab. Fürs Paper gelten die Zahlen aus `vx_eval.json` und `vx.md`.
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
- Auf den Testdaten (36 Setups) ist kein Unterschied zwischen Monitoren nach Holm signifikant. Rangfolgen müssen wir
  deshalb vorsichtig formulieren. Ob die Monitore die Uhr schlagen, hängt davon ab, wie man Zeit abgleicht.
- Die GNN-Konfiguration wurde auf denselben CV-Zeilen gewählt, auf denen sie verglichen wird. Die CV-Zahlen des GNN
  sind deshalb optimistisch.
- Der LLM-Monitor stammt aus derselben Modellfamilie wie ein Jury-Mitglied, das die GNN-Merkmale bewertet. Beide
  Messungen sind nicht unabhängig.
- Die LLM-Monitore lesen den Rohtext mit Aufgabenwörtern (`skip_checks`, `.ci/scoring.toml`), das GNN nicht. Der
  Monitor mit dem ganzen Protokoll sieht außerdem indirekt die vergangene Zeit.
- Alle fair verglichenen Monitore sehen nur Nachrichten. Wer still verstößt, bleibt unsichtbar, ebenso der Merge-Feed.
- Antrainierte Hartnäckigkeit ist nicht getestet (Teil C entfallen), Sanktionen praktisch auch nicht.
- Die Validierung hat 14 Basen (topo 7) und erkennt Einbrüche verlässlich erst ab etwa 0,2 AUROC (beim GNN 0,2–0,35).
  Ihr Rauschen beruht auf einem einzigen Wiederholungspaar, das nach allen rep0- und Arm-Läufen lief. Ahndung, GLM und
  der längere Sprint haben ihre Bedingung nur teilweise erzeugt. topo ist nur ein Zwilling auf Ebene der Faktoren.
- Die angekündigte Gegenprobe des GNN ist gescheitert, ersetzt durch den 120-Zeilen-Check (Nachtrag 2). Die
  H4-Schwellen von GNN und Hybrid stammen aus Proxy-CVs.
- Teil B der Validierung ist nur teilweise blind: 10 von 29 Paaren stammen aus schon ausgewerteten Nacht-Läufen.

---

## Zahlen auf einen Blick

**Zurückgehaltene Testzeilen** (Hauptergebnis: 2.338 Zeilen, 36 Setups, eingefrorene Modelle, gepaarter Bootstrap über
Setups, Holm über 11 Tests). AUROC: 0,5 = Raten, 1 = perfekt.

| Monitor | AUROC gesamt | in gleicher Runde | Runde + Deadline fest* | bekannte Setups | neue Bedingungen** |
|---|---|---|---|---|---|
| nur Uhr | 0,78 | 0,53 | 0,66 | 0,85 | 0,66 / 0,82 / 0,78 |
| gezählte Merkmale (bag + graph) | 0,81 | 0,72 | 0,78 | 0,90 | 0,79 / 0,76 / 0,74 |
| GNN (eingefroren) | 0,82 | 0,74 | 0,76 | **0,92** | 0,79 / 0,74 / 0,73 |
| GNN + Tabellenmodell | 0,83 | 0,75 | 0,80 | **0,92** | 0,82 / 0,79 / 0,73 |
| LLM, ganzes Protokoll | 0,82 | 0,73 | 0,79 | 0,87 | 0,78 / 0,83 / 0,73 |
| LLM, Gespräch für Gespräch | **0,85** | **0,79** | **0,82** | 0,87 | **0,87 / 0,84 / 0,80** |
| echte Verstöße zählen (nicht beobachtbar) | 0,91 | 0,87 | 0,87 | 0,93 | 0,90 / 0,92 / 0,88 |

Kein Unterschied zwischen Monitoren ist nach Holm signifikant (Details `analysis/results/heldout.md`).
\* nachträglich. \*\* fremde Aufgabenfamilie / Injektion über Tool-Ausgaben / Branch-Arme.

**Blinde Validierung `night_vx`** (14 Basen, topo 7, einmal ausgewertet; beschreibend: ein Vergleich der
AUROC-Niveaus zwischen Monitoren war nicht vorab festgelegt). AUROC.

| Monitor | id rep0 | id rep1 | Spanne in den 4 Armen | Teil B, innerhalb Konfiguration* |
|---|---|---|---|---|
| nur Uhr | 0,82 | 0,63 | 0,71–0,87 | 0,50 (per Konstruktion) |
| nur Struktur | 0,58 | 0,69 | 0,59–0,73 | 0,86 |
| gezählte Merkmale (bag + graph) | 0,78 | 0,76 | 0,71–0,79 | 0,69 |
| GNN (gespeicherte Fassung) | 0,79 | 0,74 | 0,73–0,89 | 0,76 |
| GNN + Tabellenmodell | 0,81 | 0,79 | 0,75–0,87 | 0,69 |
| LLM, ganzes Protokoll | **0,91** | **0,85** | **0,87–0,95** | 0,78 |
| LLM, Gespräch für Gespräch | 0,90 | 0,83 | 0,78–0,88 | 0,76 |
| echte Verstöße zählen (nicht beobachtbar) | 0,97 | 0,85 | 0,82–0,92 | 0,55 |

\* Lauf-Ebene, 29 Paare aus 6 Konfigurationen, CIs etwa ±0,25, nur teilweise blind.

Kein Monitor fällt in einem Arm nachweisbar stärker ab als zwischen rep0 und rep1. Höhere Werte in einem Arm heißen
nicht, dass ein Monitor dort besser wurde. Mit den Testzeilen oben sind die Werte nicht vergleichbar: GNN,
Tabellenmodell und Hybrid sind andere Instanzen, und die Setups liegen im kritischen Band (`analysis/results/vx.md`).

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
| Fairer Vergleich (Testzeilen) | `analysis/results/heldout.md`, Skripte `analysis/heldout/` | night-vx-validation |
| θ/Δ-Sensitivität | `analysis/results/sensitivity.md`, Skripte `analysis/sens.py`, `analysis/sens_summary.py` | night-vx-validation (nach dem Push) |
| Among Us | `gnn/RESULTS_amongus.md` | alle |
| Validierung | `sim_dataset/VALIDATION.md`, `sim_dataset/runs_vx/_logs/vx_decisions.md` | night-vx-validation (nach dem Push) |
| Validierung: Auswertung | `analysis/results/vx.md` (Zusammenfassung), `vx_eval.md`, `vx_verdicts.md`; nachträgliche Zahlen `analysis/vx_posthoc.py` / `vx_posthoc.json`; Eingaben `analysis/vx_preds/`; Prüfungen `analysis/review/vx-preeval/` und `vx-posteval/` | night-vx-validation |
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
- ~~„Das Wiederholungsrauschen ist klein (die id-Wiederholung kippt nur in 1 von 14 Setups anders).“~~ Gilt nur für den
  Ausgang. Die Uhr verliert 0,20 AUROC, gekippt wird in 5 von 6 Setups später (Auswertung `night_vx`, 9. Nov.).
- ~~„Die Validierung erkennt Einbrüche über 0,1 AUROC“ (Plan §6.6).~~ Verlässlich erst ab etwa 0,2 AUROC, beim GNN ab
  0,2–0,35.
