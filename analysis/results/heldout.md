# Fairer Vergleich auf den zurückgehaltenen Testzeilen (RQ2, RQ3)

Stand 8. Nov. 2026, 19:30. Skripte: `analysis/heldout/` (`analysis.py`, `hlib.py`, `make_report.py`; nachträglich
`doubletm.py`). Vollständiger Bericht auf Englisch: [heldout_full.md](heldout_full.md). Die unabhängige Nachrechnung
steht am Ende.

**Daten.** Die zurückgehaltenen Nacht-Splits gepoolt (night_test_id, test_ood_family, test_ood_seed, night_branch;
Branch-Präfixe einmal gezählt): 2.338 Zeilen, 156 positiv, 36 Setups, 100 Läufe. Alle Monitore wurden auf identischen
Zeilen bewertet. Die GNN-Modelle und Tabellen-Baselines sind eingefroren (`gnn_opt_torch/LOOKS.md`), die LLM-Monitore
zero-shot ohne Training. Die Testzahlen von GNN und LLM waren einzeln schon bekannt, deshalb ist dieser Vergleich
bestätigend und nicht blind.

**Inferenz.** Exakter gepaarter Cluster-Bootstrap über Setups, 10.000×. Zweiseitiges p, Holm über die 11 Tests aus
ANALYSIS_PLAN.md §4.

## AUROC pro Monitor

| Monitor | gesamt [95 % CI] | zeitgematcht (Plan: Runden bis Deadline) | zeitgematcht (absolute Runde) | Runde und Deadline fest (nachträglich) | test_id | neue Bedingungen (Familie / Injektion / Branch) | innerhalb gemischter Setups |
|---|---|---|---|---|---|---|---|
| nur Uhr | 0,781 [0,714; 0,841] | 0,716 | 0,530 | 0,661 | 0,847 | 0,659 / 0,816 / 0,776 | 0,682 |
| gezählte Merkmale (bag + graph) | 0,812 [0,759; 0,861] | 0,797 | 0,721 | 0,784 | 0,902 | 0,786 / 0,759 / 0,737 | 0,647 |
| Tabelle mit Gedächtnis (tab_mem) | 0,811 [0,756; 0,860] | 0,804 | 0,718 | 0,789 | 0,895 | 0,807 / 0,780 / 0,699 | 0,642 |
| Kanten-Monitor | 0,800 [0,753; 0,841] | 0,792 | 0,682 | – | 0,837 | 0,812 / 0,780 / 0,728 | 0,591 |
| GNN (cloud_final_gnn) | 0,817 [0,756; 0,873] | 0,769 | 0,739 | 0,763 | **0,921** | 0,794 / 0,744 / 0,731 | 0,639 |
| GNN + Tabelle (cloud_final) | 0,832 [0,782; 0,881] | 0,818 | 0,752 | 0,801 | **0,922** | 0,823 / 0,785 / 0,728 | 0,647 |
| LLM ganzes Protokoll | 0,816 [0,759; 0,869] | 0,819 | 0,734 | 0,791 | 0,875 | 0,782 / 0,825 / 0,734 | 0,747 |
| LLM letzte 6 Runden | 0,829 [0,780; 0,875] | 0,816 | 0,735 | – | 0,868 | 0,829 / 0,829 / 0,751 | 0,733 |
| LLM Gespräch für Gespräch | **0,855** [0,808; 0,899] | **0,838** | **0,787** | **0,821** | 0,872 | **0,867 / 0,842 / 0,797** | 0,820 |
| LLM Agent für Agent | 0,849 [0,803; 0,893] | 0,836 | 0,771 | 0,817 | 0,870 | 0,848 / 0,829 / 0,801 | **0,834** |
| Verstoßzähler + Uhr (Referenz, nicht beobachtbar) | 0,908 [0,872; 0,945] | 0,872 | 0,870 | 0,867 | 0,925 | 0,896 / 0,922 / 0,875 | 0,876 |

## Primäre Familie (vorab festgelegt, Holm über 11 Tests)

| Test | Differenz [95 % CI] | p | Holm-p | Vorzeichen in 4 Splits |
|---|---|---|---|---|
| bag + graph − Uhr, zeitgematcht | +0,080 [−0,012; +0,178] | 0,100 | 0,78 | 3 / 4 |
| LLM Gespräch für Gespräch − Uhr, zeitgematcht | +0,121 [+0,032; +0,213] | 0,008 | 0,09 | 4 / 4 |
| LLM ganzes Protokoll − Uhr, zeitgematcht | +0,103 [+0,017; +0,188] | 0,022 | 0,20 | 3 / 4 |
| GNN − Uhr, zeitgematcht | +0,053 [−0,048; +0,155] | 0,30 | 1,00 | 2 / 4 |
| GNN + Tabelle − Uhr, zeitgematcht | +0,101 [+0,015; +0,193] | 0,020 | 0,20 | 2 / 4 |
| GNN − bag + graph | +0,004 [−0,036; +0,046] | 0,83 | 1,00 | 2 / 4 |
| GNN + Tabelle − bag + graph | +0,020 [−0,005; +0,045] | 0,11 | 0,78 | 3 / 4 |
| LLM Gespräch für Gespräch − bag + graph | +0,042 [−0,008; +0,096] | 0,10 | 0,78 | 3 / 4 |
| LLM Gespräch für Gespräch − GNN | +0,038 [−0,025; +0,105] | 0,23 | 1,00 | 3 / 4 |
| LLM Gespräch für Gespräch − GNN + Tabelle | +0,022 [−0,030; +0,075] | 0,38 | 1,00 | 3 / 4 |
| LLM ganzes Protokoll − bag + graph | +0,003 [−0,050; +0,058] | 0,85 | 1,00 | 1 / 4 |

**Ergebnis: Nach Holm ist kein Test signifikant.** Am knappsten ist das LLM Gespräch für Gespräch gegen die Uhr
(Holm-p 0,09, Vorzeichen in allen 4 Splits gleich). Mit 36 Setups, von denen nur 23 überhaupt eine positive Zeile haben,
ist die Auflösung gering.

## Wie man „Zeit“ abgleicht, entscheidet über RQ2

- **Plan (Bins nach Runden bis zur Deadline):** Die Uhr erreicht 0,72. Bei gleichem Abstand zur Deadline verrät die
  absolute Runde, ob das Setup eine späte oder frühe Deadline hat. Die Uhr nutzt damit indirekt einen Setup-Faktor.
- **Harness (Bins nach absoluter Runde):** Die Uhr fällt auf 0,53. Alle 5 Monitore liegen klar darüber (p ≤ 0,0002,
  4 von 4 Splits).
- **Nachträglich, beides festgehalten (Deadline × Bin):** Die Uhr liegt bei 0,66. Nach Holm über diese 5 Tests liegen
  4 Monitore signifikant darüber: Gespräch für Gespräch +0,16 (Holm 0,002), GNN + Tabelle +0,14 (0,003), ganzes Protokoll
  +0,13 (0,03), bag + graph +0,12 (0,03). Das GNN allein nicht (+0,10, p = 0,07).

## Explorativ (nachträglich, ohne Korrektur)

- **Bekannte gegen neue Bedingungen.** In test_id liegt das GNN vorne: LLM Gespräch für Gespräch − GNN + Tabelle
  −0,050 [−0,115; +0,004]. Auf den drei neuen Splits zusammen liegt das LLM vorne: − GNN +0,097 [+0,016; +0,182],
  − GNN + Tabelle +0,073 [+0,008; +0,137], − bag + graph +0,088 [+0,029; +0,149].
- **Injektion über Tool-Ausgaben (test_ood_seed):** Der Auslöser steht nicht in der Kommunikation. Zeitgematcht liegen
  die trainierten Monitore fast bei Zufall (0,54–0,56), die zero-shot-LLMs bei 0,64–0,70.
- **Kombination** LLM Gespräch für Gespräch + GNN + Tabelle (Mittel der Ränge, ohne Fitting): 0,861. Das ist besser als
  GNN + Tabelle allein (+0,029 [+0,004; +0,056]), aber nicht besser als das LLM allein.

## Vorwarnzeit (Schwelle aus Trainingsdaten, 5 % FPR pro Zeile)

| Monitor | gekippte Läufe mit Alarm vorher | Median Vorwarnzeit (Runden) | nicht gekippte Läufe mit Fehlalarm |
|---|---|---|---|
| nur Uhr | 36 / 52 | 3 | **48 / 48** |
| bag + graph | 28 / 52 | 4,5 | 20 / 48 |
| LLM Gespräch für Gespräch | 25 / 52 | 2 | **10 / 48** |
| LLM ganzes Protokoll | 17 / 52 | 3 | 11 / 48 |
| GNN | 28 / 52 | 5 | 14 / 48 |
| GNN + Tabelle | 28 / 52 | 5,5 | 15 / 48 |

Die Uhr alarmiert in jedem nicht gekippten Lauf und ist als Alarm wertlos. Die Monitore warnen in rund der Hälfte der
gekippten Läufe vorher. Das GNN warnt früher, das LLM Gespräch für Gespräch hat die wenigsten Fehlalarme.

## Grenzen dieses Vergleichs

- Beide Seiten kannten ihre eigenen Testzahlen vorher, der Vergleich ist bestätigend und nicht blind.
- Die committeten Dateien `hgb_bag+graph`, `hgb_clock` und `oracle` deckten nur night_val ab. Sie wurden hier mit den
  Harness-Einstellungen auf night_train neu gefittet. `tab_mem` und die GNN-Dateien sind die committeten.
- Die Schwellen der GNN-Modelle stammen aus dem CV-Stellvertreter mit 4 Läufen, nicht aus dem finalen Modell mit
  5 Seeds.
- Die LLM-Monitore lesen Rohtext mit Aufgabenwörtern. `global_full` sieht indirekt die Zeit (Spearman mit der Runde
  0,83). Haiku ist auch Jury-Richter hinter den GNN-Merkmalen.
- Wenige Setups pro Split (12 / 8 / 8 / 8). Die Vorzeichen-Regel „3 von 4“ ist deshalb wackelig.

## Unabhängige Nachrechnung

**Bestätigt** (eigener Code, eigene Ziehungen, `analysis/review/heldout-verify/`). Zeilen, Splits, Labels und alle
AUROC-Werte stimmen. Alle 11 primären Differenzen sind innerhalb der Monte-Carlo-Schwankung reproduziert. Mit eigenen
Ziehungen ist ebenfalls keiner der 11 Tests signifikant (kleinstes Holm-p 0,084). Auch Schwellen, Vorwarnzeiten und
die Testzahlen des GNN-Teams sind reproduziert.

Hinweise des Prüfers:
- `bag+graph` ist für die Testzeilen neu gefittet und nicht die committete Instanz: night_val 0,901 statt 0,902. Diese
  Baseline steckt in 5 der 11 Tests. Ihre Schwelle stammt aus der committeten CV-Datei. Auf Recall und FPR wirkt sich das
  praktisch nicht aus.
- Die Fehlalarm-Schwellen von GNN und GNN + Tabelle stammen aus dem CV-Stellvertreter (`e_ngru_4runs`). Die realisierten
  FPR auf den Testzeilen liegen zwischen 0,029 und 0,063. Die Vorwarnzeiten sind deshalb nicht bei exakt gleicher
  FPR verglichen.
- Die vorab festgelegten Bins nach „Runden bis zur Deadline“ lassen der Uhr Information über die absolute Zeit. Die
  primäre Familie (a) testet die Monitore also gegen eine starke Uhr. Das muss so im Paper stehen.
- Von den 9 „gemischten“ Setups sind 3 Branch-Setups. Deren Arme unterscheiden sich durch die Intervention, es sind
  also keine echten Wiederholungen. Die Spalte „innerhalb gemischter Setups“ ist sekundär.
