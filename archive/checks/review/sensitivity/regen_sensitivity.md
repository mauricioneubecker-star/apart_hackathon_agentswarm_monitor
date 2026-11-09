# θ/Δ-Sensitivität (Nacht-Batch, Protokoll a, OOF, Bootstrap 200× über Konfigurationen)

Zero-shot-Monitore sind auf θ = 8, Δ = 3 gepromptet und bleiben unverändert; gefittete Modelle neu trainiert.

|                                                      | θ=8, Δ=3                | θ=6, Δ=3                | θ=10, Δ=3               | θ=8, Δ=2                | θ=8, Δ=5                |
|:-----------------------------------------------------|:------------------------|:------------------------|:------------------------|:------------------------|:------------------------|
| gekippte Läufe                                       | 101/252                 | 120/252                 | 77/252                  | 101/252                 | 101/252                 |
| positive Zeilen                                      | 303/6468                | 360/6177                | 231/6796                | 202/6468                | 505/6468                |
| nur Uhr                                              | 0.783                   | 0.776                   | 0.773                   | 0.780                   | 0.780                   |
| nur Uhr (zeitgematcht)                               | 0.698                   | 0.713                   | 0.687                   | 0.681                   | 0.715                   |
| nur Uhr (gleiches Setup)                             | 0.682                   | 0.771                   | 0.645                   | 0.610                   | 0.749                   |
| bag + graph                                          | 0.864                   | 0.834                   | 0.834                   | 0.850                   | 0.845                   |
| bag + graph (zeitgematcht)                           | 0.844                   | 0.826                   | 0.810                   | 0.819                   | 0.831                   |
| bag + graph (gleiches Setup)                         | 0.748                   | 0.779                   | 0.676                   | 0.694                   | 0.775                   |
| LLM ganzes Protokoll                                 | 0.844                   | 0.817                   | 0.860                   | 0.860                   | 0.813                   |
| LLM ganzes Protokoll (zeitgematcht)                  | 0.839                   | 0.829                   | 0.860                   | 0.842                   | 0.834                   |
| LLM ganzes Protokoll (gleiches Setup)                | 0.746                   | 0.894                   | 0.719                   | 0.731                   | 0.807                   |
| LLM letzte 6 Runden                                  | 0.856                   | 0.833                   | 0.858                   | 0.864                   | 0.832                   |
| LLM letzte 6 Runden (zeitgematcht)                   | 0.835                   | 0.832                   | 0.840                   | 0.830                   | 0.830                   |
| LLM letzte 6 Runden (gleiches Setup)                 | 0.718                   | 0.850                   | 0.673                   | 0.683                   | 0.787                   |
| LLM Gespräch für Gespräch                            | 0.890                   | 0.878                   | 0.872                   | 0.903                   | 0.866                   |
| LLM Gespräch für Gespräch (zeitgematcht)             | 0.871                   | 0.874                   | 0.851                   | 0.878                   | 0.860                   |
| LLM Gespräch für Gespräch (gleiches Setup)           | 0.824                   | 0.878                   | 0.712                   | 0.805                   | 0.851                   |
| LLM Gespräch für Gespräch, gestackt                  | 0.887                   | 0.871                   | 0.869                   | 0.897                   | 0.866                   |
| LLM Gespräch für Gespräch, gestackt (zeitgematcht)   | 0.857                   | 0.858                   | 0.841                   | 0.867                   | 0.845                   |
| LLM Gespräch für Gespräch, gestackt (gleiches Setup) | 0.798                   | 0.877                   | 0.721                   | 0.813                   | 0.828                   |
| Verstoßzähler + Uhr (Referenz)                       | 0.934                   | 0.911                   | 0.935                   | 0.946                   | 0.905                   |
| Verstoßzähler + Uhr (Referenz) (zeitgematcht)        | 0.897                   | 0.880                   | 0.909                   | 0.913                   | 0.863                   |
| Verstoßzähler + Uhr (Referenz) (gleiches Setup)      | 0.895                   | 0.905                   | 0.836                   | 0.917                   | 0.881                   |
| LLM paarweise − bag+graph                            | +0.026 [-0.001, +0.053] | +0.044 [+0.020, +0.072] | +0.037 [+0.012, +0.066] | +0.052 [+0.024, +0.082] | +0.022 [-0.011, +0.052] |
| LLM ganzes Protokoll − bag+graph                     | -0.019 [-0.051, +0.009] | -0.018 [-0.053, +0.019] | +0.028 [-0.007, +0.064] | +0.011 [-0.019, +0.038] | -0.030 [-0.066, +0.002] |
| Uhr − bag+graph                                      | -0.079 [-0.120, -0.034] | -0.059 [-0.109, -0.014] | -0.059 [-0.110, +0.012] | -0.068 [-0.116, -0.016] | -0.063 [-0.102, -0.020] |
