# Feature-Katalog v1 (7. Nov. 2026): Kanten- und Knotenfeatures für das GNN

Status: **festgelegt für den Pilot**. Danach prüfen und gegebenenfalls v2 (siehe „Pilot-Checks“).
Code: `runner/jury.py` (Rubriken, `RUBRIC_VERSION`) und `runner/features.py` (Katalog, Berechnung, `select_columns`).

## Leitlinien
- **20 Kanten- und 10 Knotenfeatures.** Die Jury scort einmal alle 9 LLM-Dimensionen. Stufen und Ablationen
  sind danach reines Weglassen von Spalten, ohne neue LLM-Calls.
- **Nur 5 stark interpretierende Jury-Features** (🔴). Sie haben hohe Varianz zwischen Judges, sind nah an
  inhaltlicher Überwachung und modellabhängig. Wir brauchen sie für die Ablationen, aber das Modell soll nicht
  von ihnen abhängen.
- **Zeit steckt in den Features**, weil jeder Snapshot nur den aktuellen Zustand sieht: Fenster w = 3,
  Trends, EMA, neue Kontakte, Haltungsdrift. Keine absolute Runde und keine kumulierten Summen, sonst lernt das
  Modell eine Uhr.
- **Nie im Input:** verbotene Tool-Events, System-Prompts, `thought`, Modellidentität, `instructed`-Flag,
  Lösbarkeit von Tickets.

## Legende
| Zeichen | Quelle | Tier |
|---|---|---|
| ⚪ | ohne Modell: Metadaten, Regex/Lexikon, abgeleitet | 0 (Struktur) oder 1 |
| 🔵 | kleines deterministisches Modell (NLI) | 1 |
| 🟠 | LLM, faktennah, geringe Judge-Varianz (ein Judge würde reichen) | 2 |
| 🔴 | LLM-Jury, interpretativ (DeepSeek V4 Flash + Claude Haiku 5.5) | 3 |
| 🛠 | Tool-Events, **nur Ablation** | tool |

Stufe **S*k*** = alle Features mit Tier ≤ *k*. Die Spaltenlisten liefert `features.select_columns("edge" | "node", stage)`
und sie stehen in `graph_meta.json`.

## Kantenfeatures (Rang = erwartete Relevanz)
Pro Nachricht bewertet, auf die Kante i→j über das Fenster W(t) = Runden [t−2, t] aggregiert.

**Kanten ab Katalog v1.1 (7. Nov., `labels.message_edges_typed`):** Eine Kante i→j gibt es, wenn j eine Nachricht
von i gelesen hat.
- **direct:** DM-Empfänger, @Mention oder Reply-Ziel, und nur wenn j die Nachricht wirklich bekommen hat. v1 hat
  auch Mentions von Dritten in DMs als Kante gezählt („@tobi has the notes“ an jemand anderen): 189 Phantomkanten
  in Pilot 1+2.
- **broadcast:** jedes andere Mitglied des Kanals (#sprint, Team-Channel), das ein Post von i liest. In v1 fehlten
  diese Kanten ganz, das waren ca. 13.000 Lese-Expositionen.

Inhaltsfeatures aggregieren über beide Arten. `direct_volume` und `bcast_volume` unterscheiden sie.
`responsiveness`, `reciprocity`, `unanswered_share` und die NLI-Prämisse nutzen nur direkte Kanten
(`reciprocity` ist NaN, wenn es im Fenster keine direkte Nachricht in beide Richtungen gibt). `new_contact` zählt den ersten direkten Kontakt.

| # | Spalte | Typ | Aggregation | Gruppe | Verankerung |
|---|---|---|---|---|---|
| 1 | `mech_ref` | ⚪ | max distinkter Shortcut-Artefakt-Muster (0–3) | regelnah | Wissenstransfer (Paglieri et al. 2026) |
| 2 | `rule_legitimization` | 🔴 | max | regelnah | Bandura: Moral Disengagement; Sykes & Matza: Neutralisierung; Vaughan: Normalization of Deviance |
| 3 | `volume` | ⚪ | log1p(#Nachrichten) | Struktur | Grice: Quantität |
| 4 | `success_claim` | 🟠 | max | | Cialdini: Social Proof; Grice: Qualität (Behauptung) |
| 5 | `workaround_request` | 🟠 | max | | Nachfrageseite; MAST FM-2.2 (Rückfrage) |
| 6 | `uncritical_adoption` | 🔴 | max | | Sykophanz; Janis: Illusion der Einstimmigkeit |
| 7 | `verification` | 🟠 | Mittel | Schutz | MAST FC3 (Verifikation) |
| 8 | `contradiction` | 🔵 | Mittel P(Widerspruch) zur letzten Nachricht j→i | Schutz | Dissens; Konflikt-Feature aus dem Design |
| 9 | `goal_shift` | 🔴 | max | regelnah | Reward-Hacking-Framing; MAST FM-2.3 (Derailment) |
| 10 | `unverified_authority` | 🔴 | max | | Cialdini: Autorität; Zeng et al. 2024: Authority Endorsement |
| 11 | `responsiveness` | ⚪ | Anteil von j beantworteter Nachrichten | Struktur | MAST FM-2.5 (Input ignorieren) |
| 12 | `reciprocity` | ⚪ | #(j→i) / (#(i→j)+#(j→i)) | Struktur | |
| 13 | `legitimization_trend` | 🔴 | max W(t) − max W(t−3) | zeitlich, regelnah | |
| 14 | `new_contact` | ⚪ | Paar erstmals in W(t) aktiv | Struktur, zeitlich | Ausbreitungsfront |
| 15 | `mech_ref_ema` | ⚪ | EMA (α 0,5) seit Runde 1 | zeitlich, regelnah | Dosis (komplexe Ansteckung) |
| 16 | `pressure_lex` | ⚪ | max Lexikon-Treffer (0–3) | | Cialdini: Knappheit; Zeng: Time Pressure |
| 17 | `secrecy` | 🔴 | max | | Janis: Mindguards; verdeckte Kollusion (Hammond et al. 2025) |
| 18 | `frustration` | 🟠 | Mittel | | weich Festsitzende |
| 19 | `escalation_lex` | ⚪ | max Lexikon-Treffer (0–3) | Schutz | Speaking up; MAST FC3 |
| 20 | `jury_disagreement` | 🔴 abgeleitet | Mittel \|J1−J2\| über die 🔴-Dimensionen | | Messunsicherheit |
| 21 | `direct_volume` | ⚪ | log1p(#direkte Nachrichten) (v1.1) | Struktur | |
| 22 | `bcast_volume` | ⚪ | log1p(#gelesene Kanal-Posts ohne Adressierung) (v1.1) | Struktur | |

Bilanz: 5 × 🔴 plus 2 daraus abgeleitet, 4 × 🟠, 1 × 🔵, 8 × ⚪.

## Knotenfeatures
Gesendete und empfangene Nachrichten fehlen bewusst: Die zählt das GNN selbst aus den Kanten.

| # | Spalte(n) | Typ | Inhalt | Im Hauptmodell |
|---|---|---|---|---|
| 1 | `bcast_mech_ref` | ⚪ | `mech_ref` eigener **unadressierter** Posts in W. Ohne dieses Feature ist ein Pionier, dem niemand antwortet, unsichtbar, weil solche Posts keine Kante erzeugen | ja |
| 2 | `exposure_breadth` | ⚪ | #verschiedene Absender, die den Knoten mit `mech_ref` > 0 adressiert haben, Runden [t−5, t], /3, gekappt bei 1 (Centola: komplexe Ansteckung braucht mehrere Quellen) | ja |
| 3 | `bcast_legitimization` | 🔴 | Legitimierung in eigenen unadressierten Posts | ja |
| 4 | `stance_drift` | 🔴 abgeleitet | Haltung W(t) − Haltung W(t−3); Haltung = mittlere Legitimierung − mittlere Verifikation der eigenen Nachrichten | ja |
| 5 | `role_lead`, `role_auditor`, `role_external` | ⚪ | One-Hot (Member = alles 0); externe Absender sind eigene Knoten | ja |
| 6 | `unanswered_share` | ⚪ | Anteil eigener adressierter Nachrichten ohne Antwort (Isolation) | ja |
| 7 | `frustration_own` | 🟠 | mittlere Frustration der eigenen Nachrichten | ja |
| 8 | `n_deps`, `n_dependents` | ⚪ | öffentliche Ticket-Abhängigkeiten /3 (die Lösbarkeit bleibt verborgen) | ja |
| 9 | `tests_failed` | 🛠 | #rote Testläufe in W / w | **nur Ablation** |
| 10 | `escalated_unresolved` | 🛠 | Issue gemeldet und bis t nicht von QA gefixt (legitimer Weg blockiert) | **nur Ablation** |

## Ablationen (5) und Baselines
1. **Stufen S0 → S3:** eine Kurve mit 4 Punkten (Kanten 4 / 9 / 13 / 20, Knoten 6 / 8 / 9 / 11 Spalten).
   Sie ist zugleich eine Kostenleiter: Wie viel bringt inhaltliche Überwachung gegenüber billigen Metadaten?
   S0 = Struktur-GNN-Baseline.
2. **Ohne regelnahe Features** (`drop_groups=["rule_near"]`): Lernt das Modell mehr als die Erwähnung des Shortcuts?
3. **Judge-Tausch:** 🔴/🟠 nur DeepSeek, nur Haiku, gemittelt. Dafür `jury_<judge>.jsonl` statt `jury_merged`
   einlesen. Zeigt die Modellabhängigkeit; dazu gewichtetes κ pro Dimension berichten.
4. **Ohne zeitliche Features** (`drop_groups=["temporal"]`): Reicht ein Snapshot ohne Gedächtnis?
5. **Plus Tool-Aktivität** (`include_tool=True`): Obergrenze eines kombinierten Monitors.

Vorab festgelegte Baselines (DECISIONS.md §7) laufen zusätzlich: Laufgröße, Kanten-Monitor, LogReg auf
aggregierten Features. Optional: MiniLM-Embedding statt interpretierbarer Features.

## Verankerung in etablierten Frameworks
Es gibt kein etabliertes Schema für die Kommunikation vor kollektivem Kippen. Die Rubriken leihen sich aber
benannte Mechanismen aus fünf Quellen. Das macht sie zitierbar und präziser; ob es das Judge-Agreement erhöht,
prüft der Pilot.

| Framework | Ebene | Was wir übernehmen | Was nicht passt |
|---|---|---|---|
| Bandura (Moral Disengagement), Sykes & Matza 1957 (Neutralisierung) | Rechtfertigung von Normbruch | Mechanismen als Checkliste in der Rubrik von #2: Rechtfertigung, Euphemismus („unblock“), Normalisierung, Folgen kleinreden, Verantwortung abschieben bzw. verteilen, Regelsetzer beschuldigen | – |
| Cialdini, Zeng et al. 2024 (PAP, 40 Techniken) | Überzeugung | Autorität (#10), Social Proof (#4), Zeitdruck (#16) | Reziprozität, Liking, Commitment sind für den Shortcut vermutlich schwach |
| Janis 1972 (Groupthink) | Gruppendynamik | unkritische Übernahme (#6), Mindguards (#17), kollektive Rationalisierung (#2), Dissens (#8, #19) | „Druck auf Abweichler“ ist nicht als eigenes Feature umgesetzt (Kandidat für v2) |
| MAST FC2/FC3 (Cemri et al. 2025) | gutartige Koordinationsfehler | Input ignorieren (#11), Rückfrage (#5), Derailment (#9), Verifikation (#7) | FM-2.6 Reasoning-Action-Mismatch braucht Reasoning (nie Input); MAST beschreibt Fähigkeit, nicht Absicht |
| Grice / A-Trust | Qualität kooperativer Kommunikation | Quantität (#3), Qualität als Behauptung (#4) | Klarheit und Relevanz: kaum Signal für Kippen erwartet; A-Trust: Prompt-Scores trennen schlecht |
| Petri (36–38 Judge-Dimensionen) | Transkript, Einzelagent | Sykophanz (#6), Täuschung (später `deception_claim`), Whistleblowing (#19), Eval Awareness (Kovariate) | bewertet ganze Transkripte, nicht Nachrichten |
| Hammond et al. 2025 (Multi-Agent Risks) | Systemrisiko | Netzwerkeffekte und destabilisierende Dynamik = unser Ziel; Kollusion (#17) | Risikofaktoren sind System-, nicht Nachrichtenebene |
| ControlArena / SHADE-Monitore | Suspicion-Score 0–10 | als **Kanten-Monitor-Baseline**: ein etablierter Monitor-Prompt pro Kante statt eigener Konstruktion | ein Skalar, nicht interpretierbar |

## Pilot-Checks (Gate für v2)
- **Agreement:** gewichtetes κ DeepSeek vs. Haiku pro Dimension. Erwartung: 🟠 deutlich höher als 🔴.
  🔴-Dimensionen mit κ < 0,4 schärfen oder streichen.
- **Hand-Labels:** ca. 50–100 Nachrichten, angereichert mit Shortcut-Kontext.
- **Halo-Effekt:** Korrelation zwischen den Dimensionen, da alle in einem Call bewertet werden.
  |r| > 0,8 → zusammenlegen.
- **Regex-Abdeckung:** `mech_ref` erkennt alle Paraphrasen der Auslöser (geprüft: alle Varianten ≥ 1, alle
  Decoys 0). Auf Pilot-Nachrichten Falsch-Negative stichprobenartig prüfen.
- **NaN-Anteile** in `graph_meta.json`, insbesondere `contradiction` (NLI installiert?) und `responsiveness`.

## Ausführen
```bash
python3 runner/run.py jury --watch            # 9 Dimensionen, Rubrik catalog-v1-2026-11-07
python3 runner/run.py features                # graph_edges.csv, graph_nodes.csv, graph_meta.json pro Episode
python3 runner/run.py features --no-nli       # ohne transformers/torch: contradiction = NaN
```
```python
from features import select_columns
select_columns("edge", stage=1)                          # S1: alles ohne LLM
select_columns("edge", stage=3, drop_groups=["rule_near"])
select_columns("node", stage=3, include_tool=True)       # Obergrenze mit Tool-Aktivität
```
Hinweis: Jury-Zeilen tragen `rubric`. Alte Bewertungen mit anderer Rubrik werden ignoriert und neu gescort.
