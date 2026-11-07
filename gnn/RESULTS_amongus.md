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

# Synthetischer Skalierungstest (7. Nov., abends)

Frage: Wächst der Vorteil des GNN gegenüber strukturblinden Baselines mit der Graphgröße, wenn das Signal in der Struktur
steckt? Testbett `gnn/adapters/synthetic.py`: komplexe Ansteckung (Annahme erst ab 2 verschiedenen „riskanten“ Absendern)
auf Small-World-Communities à 24 Knoten; N = 24/48/96/192 (= 1/2/4/8 Communities); 2 Seeds (benachbart oder verstreut);
Kippen = 8 Agenten (absolut) innerhalb von Δ = 3 Runden; riskanter Inhalt nur verrauscht beobachtbar (TPR 0,8, FPR 0,05).
Je N 400 Episoden (280/60/60), 1 Seed, max. 25 Epochen. Das Regime ist über N stabil (~55–58 % der Episoden kippen).

Testdaten, Graph `tip` AUROC / AUPRC | Knoten „übernimmt in Δ“ AUPRC:

| Modell | N = 24 | 48 | 96 | 192 |
|---|---|---|---|---|
| GINE | 0,937 / 0,742 \| 0,515 | 0,966 / 0,838 \| 0,512 | 0,937 / 0,813 \| 0,389 | **0,930 / 0,718 \| 0,399** |
| HGB, globale Aggregate | 0,919 / 0,714 \| 0,476 | 0,905 / 0,744 \| 0,375 | 0,874 / 0,681 \| 0,285 | 0,808 / 0,566 \| 0,252 |
| HGB, 1-Hop-Aggregate | 0,925 / 0,731 | 0,956 / 0,800 | 0,914 / 0,756 | 0,895 / 0,676 |
| LogReg, 1-Hop | 0,933 / 0,752 \| 0,401 | 0,961 / 0,822 \| 0,280 | 0,937 / 0,810 \| 0,229 | 0,902 / 0,667 \| 0,185 |
| GINE, neu verdrahtet | 0,927 / 0,737 \| 0,335 | 0,935 / 0,765 \| 0,118 | 0,930 / 0,816 \| 0,039 | 0,903 / 0,626 \| 0,020 |
| K0 ohne Message Passing | 0,896 / 0,739 \| 0,311 | 0,882 / 0,672 \| 0,104 | 0,466 / 0,212 \| 0,023 | 0,547 / 0,204 \| 0,011 |
| Nur Zeit | 0,701 / 0,327 | 0,701 / 0,257 | 0,612 / 0,280 | 0,685 / 0,236 |

Lesart (synthetisch, ein Seed, Regime so gebaut, dass Struktur zählt; zeigt *Bedingungen*, keinen Beweis für echte Daten):
- Abstand GINE − HGB global (Graph-AUROC): +0,02 → +0,06 → +0,06 → **+0,12**; Knoten-AUPRC +0,04 → +0,14 → +0,10 → +0,15.
  Globale Aggregate verdünnen das lokale Signal, je größer der Graph.
- Ein 1-Hop-Baseline („ein Knoten hat ≥ 2 riskante Absender“) holt auf Graphebene viel auf, der Rest wächst trotzdem
  (+0,01 → +0,04).
- Knotenebene braucht echte Struktur: Neu verdrahtet fällt die AUPRC mit N gegen Null, K0 bricht ab N = 96 ein.
- Gegenbild Among Us (5–7 Spieler, alle hören alle): dort ist die Struktur redundant, deshalb GNN ≈ HGB.

# Mehr Daten: Self-Play + Cross-Play (7. Nov., spätabends)

Cross-Play verarbeitet: 6.795 Spiele, 9.415 Meetings (3 Spiele aus `eval-among-us-cf-gpt-claude` wegen Log-Mismatch
übersprungen). Zusammen mit Self-Play 8.626 Spiele, 12.017 Meetings, 36.051 Snapshots (`_canonical/all_v2`). Split nach
Spiel (Hash), test_id = 1.074 Spiele. Seed-gemittelte Vorhersagen, 95-%-Bootstrap-CIs über Spiele:

| Aufgabe | GatedGCN (+ Impostor-Hilfskopf bei Gruppe) | HGB | GNN neu verdrahtet | K0 | Nur Zeit |
|---|---|---|---|---|---|
| Impostor erkennen, AUROC | **0,938** [0,932; 0,944] (3 Seeds) | 0,924 [0,917; 0,930] | 0,920 | 0,905 | – |
| Impostor erkennen, AUPRC | **0,899** [0,891; 0,907] | 0,878 [0,869; 0,887] | 0,872 | 0,849 | – |
| Unschuldiger raus, AUROC | **0,705** [0,679; 0,731] (3 Seeds) | 0,642 [0,614; 0,672] | 0,667 | 0,641 | 0,550 |
| Unschuldiger raus, AUPRC (Präv. 0,22) | **0,415** [0,367; 0,455] | 0,333 [0,292; 0,379] | 0,379 | 0,346 | 0,258 |
| Crewmate stimmt für Unschuldigen, AUROC | **0,719** [0,700; 0,736] | 0,673 [0,651; 0,695] | 0,693 | 0,670 | 0,584 |
| OOD: Training Self-Play → Test Cross-Play (gemischte Modelle), Impostor AUROC | 0,902 | 0,907 | – | – | – |

- Mit 4,6× mehr Daten zieht das GNN vorbei: bei Gruppenfehlern +0,06 AUROC / +0,08 AUPRC gegenüber HGB, CIs getrennt.
  Bei der Impostor-Erkennung +0,014 AUROC, ebenfalls getrennte CIs. Das bestätigt die Lernkurve (Abstand schrumpfte mit Daten).
- Struktur trägt jetzt: Neu verdrahtet verliert das GNN bei Gruppenfehlern 0,04 AUROC.
- Die frühere „Obergrenze“ 0,69 war eine grobe Heuristik (Beschuldigungs-Softmax × bekannte Rolle), keine harte Schranke:
  das GNN liegt mit 0,705 darüber.
- Vorläufig: Test wurde für die Entwicklung mehrfach angesehen; für das Paper Konfiguration einfrieren und einmal final
  mit 5 Seeds rechnen.
