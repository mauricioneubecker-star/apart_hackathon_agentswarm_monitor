# θ/Δ-Sensitivität (Nacht-Batch, Protokoll a, OOF über alle 112 Konfigurationen)

Gerechnet mit `analysis/sens.py` (Labels neu, keine Simulation) und `analysis/sens_summary.py`. AUROC-Differenzen:
gepaarter Cluster-Bootstrap über Konfigurationen, 2000×, Seed 0, zweiseitiges p = 2·min(P(d ≤ 0), P(d ≥ 0)). Zeitgematcht
= AUROC innerhalb der Bins „Runden bis zur Deadline“ (≤ −9, −8…−5, −4…−1, 0…3, > 3), nach Paaren gewichtet.

|                                                    | θ=8, Δ=3                           | θ=6, Δ=3                           | θ=10, Δ=3                          | θ=10, Δ=3 (nur Zähler < 8)         | θ=8, Δ=2                           | θ=8, Δ=5                           |
|:---------------------------------------------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|
| gekippte Läufe                                     | 101/252                            | 120/252                            | 77/252                             | 77/252                             | 101/252                            | 101/252                            |
| Zeilen (positiv)                                   | 6468 (303)                         | 6177 (360)                         | 6796 (231)                         | 6468 (118)                         | 6468 (202)                         | 6468 (505)                         |
| nur Uhr                                            | 0.783                              | 0.776                              | 0.773                              | 0.774                              | 0.780                              | 0.780                              |
| nur Uhr (zeitgematcht)                             | 0.698                              | 0.713                              | 0.687                              | 0.682                              | 0.681                              | 0.715                              |
| bag + graph                                        | 0.864                              | 0.834                              | 0.834                              | 0.842                              | 0.850                              | 0.845                              |
| bag + graph (zeitgematcht)                         | 0.844                              | 0.826                              | 0.810                              | 0.820                              | 0.819                              | 0.831                              |
| LLM ganzes Protokoll                               | 0.844                              | 0.817                              | 0.860                              | 0.838                              | 0.860                              | 0.813                              |
| LLM ganzes Protokoll (zeitgematcht)                | 0.839                              | 0.829                              | 0.860                              | 0.837                              | 0.842                              | 0.834                              |
| LLM letzte 6 Runden                                | 0.856                              | 0.833                              | 0.858                              | 0.855                              | 0.864                              | 0.832                              |
| LLM letzte 6 Runden (zeitgematcht)                 | 0.835                              | 0.832                              | 0.840                              | 0.838                              | 0.830                              | 0.830                              |
| LLM Gespräch für Gespräch                          | 0.890                              | 0.878                              | 0.872                              | 0.864                              | 0.903                              | 0.866                              |
| LLM Gespräch für Gespräch (zeitgematcht)           | 0.871                              | 0.874                              | 0.851                              | 0.845                              | 0.878                              | 0.860                              |
| LLM Gespräch für Gespräch, gestackt                | 0.887                              | 0.871                              | 0.869                              | 0.855                              | 0.897                              | 0.866                              |
| LLM Gespräch für Gespräch, gestackt (zeitgematcht) | 0.857                              | 0.858                              | 0.841                              | 0.814                              | 0.867                              | 0.845                              |
| Verstoßzähler + Uhr (Referenz)                     | 0.934                              | 0.911                              | 0.935                              | 0.908                              | 0.946                              | 0.905                              |
| Verstoßzähler + Uhr (Referenz) (zeitgematcht)      | 0.897                              | 0.880                              | 0.909                              | 0.866                              | 0.913                              | 0.863                              |
| LLM Gespräch für Gespräch − Uhr                    | +0.107 [+0.059, +0.154], p = 0.001 | +0.102 [+0.055, +0.150], p = 0.001 | +0.099 [+0.041, +0.153], p = 0.001 | +0.090 [+0.030, +0.148], p = 0.009 | +0.122 [+0.075, +0.167], p = 0.001 | +0.086 [+0.040, +0.130], p = 0.001 |
| LLM ganzes Protokoll − Uhr                         | +0.061 [+0.017, +0.103], p = 0.011 | +0.040 [-0.006, +0.085], p = 0.078 | +0.087 [+0.037, +0.134], p = 0.001 | +0.064 [+0.015, +0.112], p = 0.013 | +0.080 [+0.036, +0.122], p = 0.001 | +0.033 [-0.011, +0.075], p = 0.121 |
| bag + graph − Uhr                                  | +0.080 [+0.035, +0.128], p = 0.001 | +0.058 [+0.010, +0.105], p = 0.019 | +0.061 [+0.010, +0.113], p = 0.031 | +0.068 [+0.014, +0.120], p = 0.017 | +0.070 [+0.021, +0.120], p = 0.007 | +0.065 [+0.021, +0.107], p = 0.004 |
| LLM Gespräch für Gespräch − bag + graph            | +0.026 [-0.002, +0.055], p = 0.066 | +0.044 [+0.017, +0.074], p = 0.005 | +0.037 [+0.013, +0.067], p = 0.002 | +0.022 [-0.009, +0.056], p = 0.144 | +0.053 [+0.023, +0.083], p = 0.001 | +0.021 [-0.010, +0.055], p = 0.196 |
| LLM ganzes Protokoll − bag + graph                 | -0.020 [-0.051, +0.009], p = 0.202 | -0.018 [-0.050, +0.014], p = 0.286 | +0.026 [-0.008, +0.059], p = 0.134 | -0.004 [-0.040, +0.028], p = 0.848 | +0.010 [-0.020, +0.040], p = 0.530 | -0.032 [-0.064, +0.000], p = 0.055 |

**Lesehilfe.**
- Die zero-shot-LLM-Monitore wurden auf θ = 8 und Δ = 3 gepromptet und bleiben unverändert. Bei anderen Werten ist ihre
  AUROC ein Übertragungstest eines festen Scores. Die gefitteten Modelle (bag + graph, gestackter Kopf) werden dagegen
  neu trainiert. Der Vergleich ist deshalb eher zu Ungunsten der LLMs verzerrt.
- **θ = 10:** Hier kommen Zeilen mit 8–9 Verstößen dazu (rund 5 % der Zeilen, fast die Hälfte der Positiven). Der auf
  θ = 8 gepromptete Monitor hält sie schon für gekippt. Die faire Spalte ist deshalb „nur Zähler < 8“, also genau die
  Zeilen von θ = 8 mit θ = 10-Labels. Aus der vollen θ = 10-Spalte folgt nicht, dass der Vorsprung der LLMs wächst.
- Die Spalte „innerhalb gleicher Setups“ fehlt mit Absicht. Welche Konfigurationen einen gemischten Ausgang haben,
  hängt von θ ab (18 / 19 / 16 bei θ = 8 / 6 / 10, nur 7 sind bei allen θ gemischt). Die Werte wären zwischen den
  Spalten nicht vergleichbar.
- Run-Ebene und Risiko-Slices in den Einzelergebnissen pro Einstellung sind auf θ = 8 fest verdrahtet und dürfen für
  θ ≠ 8 nicht zitiert werden.

