# AmongUs-X (Plan B): erste Ergebnisse (7. Nov. 2026, abends)

Daten: AmongUs-X Self-Play, 14 Modellordner, 1.831 Spiele, 2.602 Meetings, 7.806 Snapshots (Meeting × Diskussionsrunde).
`deepseek-r1-distill-qwen-32b` verliert 89 Spiele (Kompakt-Log und Spiel-Log passen nicht zusammen, offenbar
zusammengeführte Wiederholungsläufe). Split nach Spiel 70/15/15 (Hash). Adapter v2 (Wortlisten + Aussagen über Orte,
Widersprüche, Leichenraum, explizite Stimmabsicht; nur öffentlicher Text). Alle Zahlen: **test_id**, Mittel ± Std über
3 Seeds (Baselines teils 1 Seed). Auswahl/Early Stopping auf val. Noch keine finale Auswertung, Test wurde mehrfach angesehen
→ für das Paper final einmal mit eingefrorener Konfiguration und 5 Seeds neu rechnen.

## 1. Täuschende Agenten erkennen (Knoten: `is_impostor`, Prävalenz 0,30)

| Arm | Seeds | AUROC | AUPRC |
|---|---|---|---|
| K2 HGB (Knoten + Kanten-Aggregate) | 1 | **0,907** | **0,861** |
| A2 GatedGCN | 3 | 0,902 ± 0,001 | 0,859 ± 0,001 |
| A3 Transformer | 3 | 0,897 ± 0,003 | 0,852 ± 0,003 |
| A1 GINE | 3 | 0,890 ± 0,001 | 0,840 ± 0,001 |
| A1 GINE, Kanten zufällig neu verdrahtet | 3 | 0,889 ± 0,005 | 0,836 ± 0,007 |
| A1 GINE ohne Orts-/Widerspruchsfeatures | 3 | 0,885 ± 0,001 | 0,829 ± 0,002 |
| K0 ohne Message Passing | 3 | 0,878 ± 0,001 | 0,818 ± 0,002 |
| K1 LogReg | 1 | 0,872 | 0,818 |
| Nur Zeit | 1 | 0,504 | 0,298 |
| **OOD** (Claude + Llama-3.3-70B nie im Training): K2 HGB / Transformer / GINE / LogReg | 1/2/2/1 | 0,911 / 0,903 / 0,900 / 0,883 | 0,864 / 0,861 / 0,854 / 0,827 |

## 2. Gruppenfehler vorhersagen (Graph: `innocent_ejected`, Prävalenz 0,21; Knoten: Crewmate stimmt für Unschuldigen, 0,22)

| Arm | Graph AUROC | Graph AUPRC | Knoten AUROC | Knoten AUPRC |
|---|---|---|---|---|
| A3 Transformer + Impostor-Hilfskopf | 0,619 ± 0,009 | 0,328 ± 0,013 | 0,653 ± 0,004 | 0,357 ± 0,008 |
| A2 GatedGCN + Hilfskopf | 0,617 ± 0,011 | 0,325 ± 0,014 | 0,649 ± 0,003 | 0,366 ± 0,006 |
| K2 HGB | 0,612 ± 0,010 | 0,317 ± 0,004 | 0,647 ± 0,005 | 0,343 ± 0,003 |
| K1 LogReg | 0,601 | 0,312 | 0,641 | 0,342 |
| A1 GINE | 0,600 ± 0,010 | 0,299 ± 0,018 | 0,634 ± 0,004 | 0,335 ± 0,009 |
| K0 + Hilfskopf | 0,589 ± 0,017 | 0,289 ± 0,009 | 0,631 ± 0,012 | 0,332 ± 0,010 |
| Nur Zeit | 0,589 | 0,280 | 0,597 | 0,310 |
| GINE + Hilfskopf, neu verdrahtet | 0,571 ± 0,015 | 0,268 ± 0,020 | – | – |
| GINE + Hilfskopf, Labels gemischt | 0,520 ± 0,036 | 0,252 ± 0,028 | 0,505 ± 0,004 | 0,239 ± 0,004 |

Spielausgang (`game_impostor_win` ab jedem Meeting, Prävalenz 0,64): alle Modelle AUROC 0,63–0,65, nur Zeit 0,60.

**Obergrenze (Diagnose, Runde 2):** Selbst mit *bekannten* Rollen erreicht „Wahrscheinlichkeit, dass der Meistbeschuldigte
unschuldig ist“ nur AUROC 0,69 / AUPRC 0,41. Grund: Der Meistbeschuldigte fliegt nur in 46 % der Rauswürfe, und in 37 %
der Meetings fliegt niemand. Die Abstimmung folgt der Diskussion also nur lose; mit gelernten Impostor-Scores statt
echter Rollen kommt dieselbe Formel auf 0,60.

## Lesart
- **Erkennen geht, Vorhersagen kaum.** Wer täuscht, verrät sich in der Kommunikation (AUROC ~0,90) und das überträgt sich
  auf nie gesehene Modelle. Ob die Gruppe dadurch falsch entscheidet, ist aus der Diskussion nur schwach vorhersagbar.
- **GNN ≈ starke Tabellen-Baseline.** HGB mit Aggregaten über ein- und ausgehende Kanten ist gleichauf oder besser. Message
  Passing schlägt K0 (+0,01–0,02 AUROC), aber neu verdrahtete Kanten kosten beim Erkennen nichts: Es zählt, *was* über einen
  Spieler gesagt wird, nicht die genaue Struktur. Bei den Gruppenfehlern kostet Neuverdrahten etwas (0,57 vs. 0,59–0,62).
- **Kontrollen:** gemischte Labels → Zufall; nur Zeit/Größe klar unter den Modellen.

## Nächste Hebel
1. Pro Erwähnung eine Jury-Bewertung (beschuldigt / verteidigt / widerspricht einer Aussage), analog Swarm-Katalog.
2. Cross-Play (6.800 Spiele, gemischte Modelle in einer Gruppe): mehr Daten, näher an der Schwarm-Frage.
3. Epistemic States als Ziel: Verschiebt die Diskussion die Überzeugung eines Crewmates hin zu einem Unschuldigen?
   Das wäre die direkte Messung von „Ansteckung“ falscher Überzeugungen.
