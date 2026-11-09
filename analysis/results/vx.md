# Validierung `night_vx`: Ergebnis der vorab festgelegten Auswertung

**Stand:** 9. Nov. 2026, 01:40. Die Eingaben wurden vor der Auswertung eingefroren und gepusht (`d083547d`). Die
Auswertung lief nach Plan einmal bei uns (`analysis/vx_preds/run_eval.sh`, 00:00–00:24 Uhr), die Rohausgaben sind
gepusht (`bb3f665d`). Eine Cloud-Sitzung führte dasselbe Skript parallel ein zweites Mal aus, mit byte-gleichen
Ergebnissen (siehe Offenlegung). Die Regeln stehen in ANALYSIS_PLAN.md §6 und Nachtrag 2. Sechs Prüf-Agenten (KI, eigener Code) haben die
Auswertung aus den eingefrorenen Eingaben nachgerechnet. Alle Punkt-Schätzer stimmen auf 4 Stellen, mit dem Seed des
Laufs auch alle CIs (`analysis/review/vx-posteval/`). Alle Zahlen, die nicht in `vx_eval.json` stehen, sind
nachträglich gerechnet, nach Sicht der Ergebnisse. Sie stammen aus `analysis/vx_posthoc.py` (`vx_posthoc.json`), die
Angaben zur Seed-Abhängigkeit aus den Prüfberichten in `analysis/review/vx-posteval/`.

## Das Wichtigste

1. **Kein Hinweis auf einen großen Einbruch, aber die Auflösung ist grob.** In keinem der vier Arme fällt ein Monitor
   nachweisbar stärker ab als beim bloßen Wiederholen. In keinem der 96 Vergleiche (12 Monitore × 4 Arme × 2 Metriken)
   liegt die CI von „Arm minus zweite id-Wiederholung (rep1)“ ganz unter null. Diese CIs sind aber im Median ±0,15 AUROC
   breit, beim GNN ±0,16–0,26, zeitgematcht ±0,34. Verlässlich, also mit etwa 80 % Wahrscheinlichkeit, hätte die Suite
   einen Einbruch erst ab etwa 0,2 AUROC erkannt, beim GNN ab 0,2–0,35, zeitgematcht ab etwa 0,5. Geplant waren 0,1
   (§6.6), das ist eine Abweichung vom Plan. Bezug ist rep1, und rep1 war für 9 von 12 Monitoren die schwerere
   Wiederholung. Der Rauschboden kann deshalb zu großzügig sein. „Robust“ dürfen wir nicht schreiben.
2. **H1–H5: die vorab festgelegten Urteile sind nicht belastbar.** Nach den Regeln sind H1–H4 nicht gestützt und H5
   gestützt. Bei keinem Urteil schließt die CI die Entscheidungsgrenze aus. H5 und die GNN-Hälfte von H2 drehen sich
   außerdem um, sobald man die zeitgematchte AUROC nimmt. Fürs Paper: die Urteile so nennen, mit genau diesem Zusatz.
3. **Schon das Wiederholen stört.** Die zweite id-Wiederholung kippt nur in 1 von 14 Setups anders. Die Uhr verliert
   aber 0,20 AUROC [0,09; 0,29], die Monitore bis zu 0,07 (deren CIs schließen 0 ein). Gekippt wird in 5 von 6 Setups
   später, im Mittel 4 Runden (Vorzeichentest p = 0,22). Die Wiederholung lief nach allen rep0- und Arm-Läufen, danach
   kamen nur noch die Wiederholungen von Teil B. Ob der Unterschied Zufall ist oder an der Reihenfolge liegt, lässt sich
   mit einem einzigen Paar nicht sagen.
4. **Drei Arme haben ihr Ziel nur teilweise erreicht.** Sichtbare Ahndung bremste das Kippen nicht erkennbar (5 statt 6
   von 14, p = 1,0). Mit GLM-Agenten kippen fast alle Läufe (13 von 14), die Jury-Bewertungen der Nachrichten weichen
   aber nicht stärker ab als zwischen zwei Wiederholungen. Im längeren Sprint kippte es im Mittel zur selben Runde wie
   in rep1 (24,9 gegen 25,0), obwohl die Deadline bei 29 statt im Mittel 22 lag. Als Tests sind H2, H3 und H4 deshalb
   schwach. topo ist nur ein Zwilling auf Ebene der Faktoren, mit 7 Basen.
5. **Beschreibend hat das LLM mit dem ganzen Protokoll die höchste AUROC**, in jedem Arm und in beiden
   id-Wiederholungen (0,85–0,95). Nachträglich über alle Teil-A-Zeilen gerechnet liegt es +0,08 [+0,05; +0,12] vor dem
   GNN. Diesen Vergleich haben wir erst nach Sicht der Ergebnisse gewählt, er ist nur eine Hypothese. `pairwise`, auf
   den Testdaten knapp vorne (nicht signifikant), ist hier weder vom GNN (+0,03 [−0,04; +0,11]) noch von `global_full`
   (−0,05 [−0,12; +0,02]) zu trennen. Eine gesicherte Rangfolge der beiden LLM-Varianten gibt es weder auf den
   Testdaten noch hier.
6. **Welcher von zwei gleichen Läufen kippt, bleibt schwer.** Innerhalb derselben Konfiguration (Teil B) kommt das GNN
   auf 0,76 [0,45; 0,97]. Seed-unabhängig über 0,5 liegen nur die Struktur-Baseline (0,86) und bag + graph (0,69).
   Warum gerade sie, ist offen. Das Oracle mit den echten Verstößen erreicht nur 0,55, die Kennzahl ist stark
   verrauscht. Teil B ist nur teilweise blind: Von den 29 Paaren sind 10 Nacht-Nacht-Paare schon ausgewerteter Läufe,
   16 Nacht-neu und nur 3 ganz neu.

**Offenlegung.** Die angekündigte Gegenprobe des GNN, Zeile für Zeile gegen die committeten Nacht-Vorhersagen und mit
Abbruchregel, ist gescheitert. Die gespeicherte Modell-Datei enthält nur 15 der 40 Zustände. An ihre Stelle trat der
120-Zeilen-Check aus dem `predict.py` des GNN-Teams, den unser Lauf reproduziert (Nachtrag 2, Punkt 3). Das stand vor
dem Nachtlauf in der Statusmeldung an Mauricio, eine ausdrückliche Bestätigung gibt es nicht. Die H4-Schwellen von GNN
und Hybrid stammen aus Proxy-CVs des GNN-Teams (Nachtrag 2, Punkt 6).

**Nachtrag zur Offenlegung (9. Nov., 08:15).** Eine Cloud-Sitzung des GNN-Teams hat `run_eval.sh` um 01:04 Uhr ein
zweites Mal ausgeführt, in einem sauberen Checkout von `d083547d` (Branch `cloud-synthesis`, `b14b3393`, mit Python 3.13
und pandas 3.0.5). Ihre Dateien `vx_eval.json`, `vx_eval_refbag.json`, `vx_jury_ks.json` und `vx_verdicts.json` sind
byte-gleich mit unseren. Die AUROC-Tabelle in ihrer `synthesis_cloud/SYNTHESIS.md` (§3) stimmt mit diesen Dateien nicht
überein. Es gelten die Zahlen auf dieser Seite.

## Die Hypothesen H1–H5

Die Regeln stehen in ANALYSIS_PLAN.md Nachtrag 2, Punkt 7. Sie gelten, wie vorab festgelegt, für das GNN.

| | Frage | Ergebnis (AUROC) | Urteil | schließt die CI die Grenze aus? |
|---|---|---|---|---|
| H1 | Liest das GNN die Dynamik? (Teil B, innerhalb der Konfiguration) | GNN 0,76 [0,45; 0,97], Merkmals-pairwise 0,52 | nicht gestützt | nein, die CI reicht unter 0,5 |
| H2 | Bricht die Uhr im längeren Sprint ein, das GNN aber nicht? | Uhr: Arm − rep1 +0,08 [−0,09; +0,27]. GNN: Verschiebung +0,05 bei Rauschen −0,05 | nicht gestützt: Die Uhr fällt nicht stärker ab als beim Wiederholen | nein. Die GNN-Hälfte besteht nur knapp und kippt zeitgematcht |
| H3 | Übersteht das GNN ein neues Agenten-Modell mindestens so gut wie bag? | GNN −0,06, bag −0,05, Differenz −0,01 [−0,19; +0,20] | nicht gestützt | nein |
| H4 | Bleibt das GNN unter Ahndung brauchbar, mit höchstens doppelt so vielen Fehlalarmen? | AUROC hält (+0,05). Fehlalarm in 3 von 9 statt 1 von 8 ungekippten Läufen | nicht gestützt | nein. Ein Alarm weniger hätte H4 bestehen lassen (Fisher p = 0,58) |
| H5 | Hält das GNN auf Netzen mit Hubs mindestens so gut wie bag? | GNN +0,10, bag +0,01, Differenz +0,10 [−0,21; +0,61], 7 Basen | gestützt | nein. Zeitgematcht −0,12 [−0,62; +0,52] |

Begleitzahlen, die Nachtrag 2 verspricht:
- **H2:** Die Uhr ohne die letzten 3 Runden gibt +0,05 [−0,12; +0,23], dasselbe Bild. Das ist ein schwacher Test.
  Gekippt wurde zur selben Runde wie in rep1. Bei ihrer Schwelle alarmiert die Uhr nur in Runde 18, egal wo die
  Deadline liegt. Das sieht keine AUROC.
- **Zeitgematcht:** H2, GNN-Hälfte: Verschiebung +0,12 bei Rauschen −0,11, besteht nicht. H3: GNN −0,13, bag −0,08,
  weiter nicht gestützt. H4 (i): +0,13 ≥ −0,11, besteht. H5: GNN −0,05, bag +0,07, nicht gestützt.
- **H4:** Zeilen-FPR auf ungekippten Läufen 3,3 % unter Ahndung gegen 0,4 % ohne, beides unter den nominellen 5 %.
- **H1:** Die id-Paare aus Teil A beruhen auf einem einzigen gemischten Paar, ihre CI ist entartet.

H6 (feinjustierte Agenten) entfällt, weil Teil C technisch scheiterte. Die erwartete Reihenfolge Merkmals-pairwise
< bag ≤ bag + graph ≤ GNN gilt in keinem Arm, auch mit dem Kanten-Monitor an Stelle von Merkmals-pairwise nicht. Das
liegt vor allem daran, dass Merkmals-pairwise vor bag liegt. Das GNN liegt in jedem Arm mindestens gleichauf mit bag +
graph.

## AUROC je Block (beschreibend)

| Monitor | id rep0 | id rep1 | time | glm | enf | topo* |
|---|---|---|---|---|---|---|
| LLM, ganzes Protokoll (`global_full`) | 0,91 | 0,85 | 0,89 | 0,87 | 0,94 | 0,95 (0,91 / 0,77) |
| LLM, Gespräch für Gespräch (`pairwise`) | 0,90 | 0,83 | 0,88 | 0,81 | 0,83 | 0,78 (0,83 / 0,69) |
| GNN + Tabellenmodell | 0,81 | 0,79 | 0,84 | 0,75 | 0,84 | 0,87 (0,82 / 0,76) |
| GNN (gespeicherte Fassung, 15 Zustände) | 0,79 | 0,74 | 0,85 | 0,73 | 0,84 | 0,89 (0,79 / 0,64) |
| Tabellenmodell mit Gedächtnis | 0,80 | 0,78 | 0,77 | 0,75 | 0,76 | 0,80 (0,79 / 0,73) |
| gezählte Merkmale (bag + graph) | 0,78 | 0,76 | 0,79 | 0,71 | 0,79 | 0,76 (0,80 / 0,72) |
| Kanten-Monitor | 0,79 | 0,73 | 0,85 | 0,76 | 0,89 | 0,71 (0,80 / 0,59) |
| nur Struktur | 0,58 | 0,69 | 0,69 | 0,60 | 0,59 | 0,73 (0,55 / 0,71) |
| nur Uhr | 0,82 | 0,63 | 0,71 | 0,87 | 0,76 | 0,80 (0,80 / 0,54) |
| echte Verstöße + Uhr (nicht beobachtbar) | 0,97 | 0,85 | 0,82 | 0,90 | 0,88 | 0,92 (0,93 / 0,73) |

\* topo hat nur 7 Basen. In Klammern stehen id rep0 / id rep1 auf genau diesen 7 Basen. Die übrigen Spalten beruhen auf
denselben 14 Basen, jede Zelle auf nur 15–39 positiven Zeilen (topo: 9–15). Verschiebungen mit CIs stehen in
`vx_eval.md`.

Höhere Werte in einem Arm heißen nicht, dass ein Monitor dort besser wurde. Bezug ist immer die Spanne zwischen rep0
und rep1. Die Uhr ist auf rep0 besser als das GNN (0,82 gegen 0,79), auf rep1 deutlich schlechter. Nur im glm-Arm
liegen vier der sechs Monitore des Hauptsets (Uhr, bag + graph, GNN, Hybrid, `pairwise`, `global_full`; ANALYSIS_PLAN
§3) unter beiden id-Wiederholungen, nämlich bag + graph, GNN, Hybrid und `pairwise`, um 0,03–0,06 unter deren Mittel.
Gegenüber rep1 ist keiner der vier nachweisbar schlechter. In glm kippen 13 von 14 Läufen, die AUROC misst dort vor
allem das Timing. Mit den Testzeilen in `heldout.md` sind diese Werte nicht vergleichbar. GNN, Tabellenmodell und
Hybrid sind hier andere Instanzen (Nachtrag 2, Punkte 3 und 4), und alle Setups liegen absichtlich im kritischen Band.

## Teil B: Welcher Lauf derselben Konfiguration kippt?

Score 6 Runden vor der Deadline, alle Paare aus gekipptem und nicht gekipptem Lauf derselben Konfiguration (29 Paare
aus 6 Konfigurationen; die 2 Beinahe-Kipper liefern keine Paare). Zeilen-Ebene: innerhalb Konfiguration × Zeit-Bin.

| Monitor | Lauf-Ebene [CI] | Zeilen-Ebene [CI] |
|---|---|---|
| nur Struktur | 0,86 [0,73; 0,98] | 0,58 [0,44; 0,70] |
| LLM, ganzes Protokoll (`global_full`) | 0,78 [0,52; 0,97] | 0,74 [0,60; 0,87] |
| GNN (gespeicherte Fassung, 15 Zustände) | 0,76 [0,45; 0,97] | 0,63 [0,54; 0,74] |
| LLM, Gespräch für Gespräch (`pairwise`) | 0,76 [0,48; 0,93] | 0,73 [0,63; 0,85] |
| gezählte Merkmale (bag + graph) | 0,69 [0,56; 0,86] | 0,68 [0,62; 0,74] |
| Kanten-Monitor | 0,69 [0,50; 0,89] | 0,59 [0,51; 0,72] |
| GNN + Tabellenmodell | 0,69 [0,41; 0,90] | 0,69 [0,60; 0,78] |
| Tabellenmodell mit Gedächtnis | 0,59 [0,35; 0,83] | 0,70 [0,59; 0,81] |
| bag | 0,55 [0,32; 0,80] | 0,62 [0,51; 0,71] |
| echte Verstöße + Uhr (nicht beobachtbar) | 0,55 [0,25; 0,77] | 0,82 [0,72; 0,92] |
| Merkmals-pairwise | 0,52 [0,29; 0,75] | 0,63 [0,59; 0,69] |
| nur Uhr | 0,50 (per Konstruktion) | 0,57 [0,51; 0,65] |

- Seed-unabhängig über 0,5 liegt die CI nur bei der Struktur-Baseline und bei bag + graph. Bei `global_full` hängt die
  Untergrenze 0,52 vom Seed ab, nur in etwa zwei Dritteln der Seeds liegt sie über 0,5.
- Auf den 29 Paaren liegen `pairwise` und GNN gleichauf (je 0,76), `global_full` knapp darüber. Vorne liegen die LLMs
  nur auf den 10 Nacht-Nacht-Paaren (0,90 und 0,95 gegen 0,80 beim GNN). Auf den 19 Paaren mit mindestens einem neuen
  Lauf kommen GNN 0,74, beide LLMs 0,68 und die Struktur-Baseline 1,00.
- Die Struktur-Baseline ordnet alle 16 Nacht-neu-Paare richtig, in beide Richtungen (9 von 9 und 7 von 7), und auch
  die 3 ganz neuen. Ein einfacher Niveau-Unterschied zwischen den Batches erklärt das nicht.
- Auf Zeilen-Ebene liegen die beobachtbaren Monitore bei 0,57–0,74, die Uhr schon bei 0,57. Beschreibend sind die LLMs
  dort am höchsten, aber 544 der 960 Zeilen stammen aus schon ausgewerteten Nacht-Läufen.

## Kipprate je Arm

Exakter McNemar-Test gegen id rep0, Holm über 4 Arme. Die Zählungen waren schon vor dem Plan bekannt.

| Arm | gekippt (Arm gegen id rep0) | p | nach Holm |
|---|---|---|---|
| time | 8 / 14 gegen 6 / 14 | 0,63 | 1,0 |
| glm | 13 / 14 gegen 6 / 14 | 0,016 | 0,06 |
| enf | 5 / 14 gegen 6 / 14 | 1,0 | 1,0 |
| topo | 5 / 7 gegen 3 / 7 | 0,63 | 1,0 |

Kein Arm ändert die Kipprate nach Holm signifikant. Mit GLM-Agenten steigt sie am deutlichsten.

## Fehlalarme unter Ahndung (H4)

Fehlalarm heißt: Ein nicht gekippter Lauf hat mindestens einen Score über der Trainingsschwelle (5 % FPR).

| Monitor | enf | id rep0 |
|---|---|---|
| GNN | 3 von 9 | 1 von 8 |
| GNN + Tabellenmodell | 3 von 9 | 3 von 8 |
| LLM, Gespräch für Gespräch | 3 von 9 | 2 von 8 |
| LLM, ganzes Protokoll | 1 von 9 | 1 von 8 |
| gezählte Merkmale | 3 von 9 | 5 von 8 |
| nur Uhr | 9 von 9 | 8 von 8 |

Nur beim GNN steigt der Anteil auf mehr als das Doppelte, deshalb scheitert H4. Die drei enf-Läufe waren
Beinahe-Kipper mit 6, 6 und 7 Regelbrechern (gekippt heißt: mindestens 8). Der eine id-Lauf hatte 3. Die Uhr alarmiert
in jedem nicht gekippten Lauf, wie schon auf den Testdaten.

## Jury-Bewertungen unter GLM (zu H3)

Gemessen über alle Nachrichten des glm-Arms, also zur Hälfte von GLM-Agenten. Pro Jury-Dimension weichen sie von id
rep0 nicht stärker ab als die beiden id-Wiederholungen voneinander: KS-Abstand 0,004–0,048 gegen 0,003–0,049, die CIs
überlappen. Getrennt für die GLM-Agenten wurde das nicht geprüft. Der glm-Arm verschiebt vor allem die Basisrate und
die Menge der Nachrichten (1.708 statt 1.278), kaum die Jury-Merkmale.

## Was wir nicht behaupten dürfen

- „Die Monitore sind robust gegen Zeit, Population, Ahndung und Topologie.“ Richtig ist: kein Hinweis auf einen
  Einbruch ab etwa 0,2 AUROC (beim GNN 0,2–0,35).
- „Die Suite erkennt Einbrüche über 0,1 AUROC“ (Plan §6.6).
- „1 von 5 Hypothesen bestätigt“, „H5 zeigt, dass das Graphsignal auf Hub-Netzen hält“ oder „das GNN ist robuster
  gegen die Topologie als bag“. H5 ist eine Punktregel auf 7 Basen, die CI enthält 0, zeitgematcht dreht sie sich um.
- „H1 zeigt, dass das GNN Dynamik liest“, und auch nicht das Gegenteil. Die CI [0,45; 0,97] deckt beides. Ebenso wenig
  „das GNN trennt die id-Wiederholungen perfekt“, das beruht auf einem einzigen Paar.
- „Teil B ist ein blinder Test“ oder „die LLM-Monitore sind innerhalb der Konfiguration am besten“.
- „Die Uhr bricht im längeren Sprint ein“ oder „der time-Arm zeigt, dass das GNN keine Zeit kodiert“.
- „H3 zeigt, dass die Semantik auf ein neues Modell übertragbar ist“ oder „der Graph macht anfälliger“. Die
  Jury-Merkmale haben sich kaum verschoben, und die Differenz −0,01 [−0,19; +0,20] ist ein Münzwurf.
- „GLM-Agenten erhöhen das Kippen signifikant“ (Holm 0,06) oder „Ahndung bremst das Kippen“ (5 gegen 6).
- „Unter Ahndung schlägt das GNN achtmal so oft falschen Alarm.“ Es sind 3 gegen 1 Läufe, die drei waren
  Beinahe-Kipper. Ebenso wenig „H4 hält doch“ über eine andere Lesart der Basen oder eine andere Schwelle.
- „Unter den Verschiebungen wurden die Monitore besser“ oder „`pairwise` bricht unter Ahndung ein“. Positive Werte
  beziehen sich auf das leichte rep0. Die −0,07 von `pairwise` unter Ahndung entsprechen genau seinem eigenen Rauschen.
- „Die gescheiterte Reihenfolge zeigt, dass das GNN schlechter ist als einfache Baselines.“ Das GNN liegt in jedem Arm
  mindestens gleichauf mit bag + graph.
- „Die zeitgematchte AUROC zeigt große Verschiebungen.“ Ihr Rauschen ist genauso groß.
- „Die blinde Validierung bestätigt, dass die LLM-Monitore das GNN schlagen“, „sie bestätigt die Rangfolge der
  Testdaten“ oder „auf vx schlagen die Monitore die Uhr“. Ein Vergleich der AUROC-Niveaus war nicht vorab festgelegt.
  Auf id rep0 liegt die Uhr über dem GNN.
- „vx zeigt eine Lücke oder einen Gewinn gegenüber den Testdaten.“ Modell-Instanzen, Schwellen und Setups sind
  verschieden.
- „Das Wiederholungsrauschen ist klein.“ Das gilt nur für den Ausgang der Läufe.
- „Die Jury-Merkmale verschieben sich unter GLM.“
- Bei den Seed-abhängigen Intervallen weder „schließt 0 aus“ noch „schließt 0 ein“ ohne Hinweis schreiben. Das sind
  die `pairwise`-Verschiebung in glm (mit vielen Ziehungen schließt ihre CI 0 knapp aus), das Oracle in glm, die
  zeitgematchten LLM-Werte im time-Arm, die zeitgematchte Uhr ohne die letzten 3 Runden und Teil B `global_full`.
- Alles über AUPRC, Recall, Vorwarnzeit, Kalibrierung, Sanktionen oder feinjustierte Agenten auf vx. Das wurde bewusst
  nicht gerechnet (Nachtrag 2, Punkt 9) oder war nicht testbar.

## Grenzen

- 14 Basen, bei topo 7. Die Perzentil-CIs über so wenige Cluster sind antikonservativ, die wahren Intervalle also noch
  breiter.
- Das Rauschen beruht auf einem einzigen Wiederholungspaar. rep1 lief nach allen rep0- und Arm-Läufen.
- Drei Arme haben ihre Bedingung nur teilweise erzeugt (siehe oben). topo ist nur ein Zwilling auf Ebene der Faktoren.
- Teil B ist nur teilweise blind und hat nur 6 Konfigurationen mit Paaren.
- Das GNN ist die gespeicherte Fassung mit 15 von 40 Zuständen, auf den Testzeilen 0,004 AUROC schwächer. Tabellenmodell
  und Hybrid sind lokal neu gefittet, die Schwellen von GNN und Hybrid stammen aus Proxy-CVs. Die angekündigte
  Gegenprobe des GNN ist gescheitert (siehe Offenlegung).
- Die zero-shot-LLMs lesen den Rohtext mit Aufgabenwörtern. `global_full` sieht indirekt die vergangene Zeit, und Haiku
  ist auch Richter in der Jury hinter den GNN-Merkmalen.

## Dateien

- `analysis/results/vx_eval.md` und `.json` (Aufruf 1), `vx_eval_refbag.json` (Aufruf 2), `vx_verdicts.md`,
  `vx_jury_ks.md`, `vx_gnn15_heldout.md`, `vx_run.log`
- `analysis/vx_posthoc.py` mit `analysis/results/vx_posthoc.json`: alle nachträglichen Zahlen dieser Seite
- `analysis/vx_preds/README.md`: Eingaben, genaue Befehle, Umgebung
- `analysis/review/vx-preeval/` (Prüfung vor dem Lauf), `analysis/review/vx-posteval/` (Nachrechnung)
- ANALYSIS_PLAN.md, Nachtrag 2
