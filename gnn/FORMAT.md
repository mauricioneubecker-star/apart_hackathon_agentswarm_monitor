# Kanonisches Snapshot-Format (gnn/)

Ein Verzeichnis pro Datensatz. Jede Zeile ist an `(episode_id, t)` gebunden; ein Snapshot = ein Graph.
Adapter: `adapters/swarm.py` (Simulation), `adapters/amongus.py` (AmongUs-X, nur Stdlib).

| Datei | Pflichtspalten | Inhalt |
|---|---|---|
| `episodes.csv` | `episode_id, group_id, split` | eine Zeile pro Episode; `group_id` = Einheit für Splits/Bootstrap (Swarm: Konfiguration, Among Us: Spiel); weitere Spalten = Strata |
| `snapshots.csv` | `episode_id, t` | Metadaten pro Snapshot (Zeit-Baseline, Stratifizierung), z. B. `round`, `meeting`, `n_alive` |
| `nodes.csv` | `episode_id, t, node_id` + Features | Knoten eines Snapshots |
| `edges.csv` | `episode_id, t, src, dst, etype` + Features | gerichtete Kanten; Features, die für einen Kantentyp nicht gelten, sind 0 |
| `graph_labels.csv` | `episode_id, t` + Labels | leer/NaN = für diesen Snapshot nicht definiert (wird maskiert) |
| `node_labels.csv` | `episode_id, t, node_id` + Labels | leer/NaN = nicht definiert |
| `schema.json` | | `node_features`/`edge_features`/`etypes`: `{name, tier, groups}`; `graph_labels`/`node_labels`: `{type: binary|count, max}`; `time_features`; `strata`; `default_drop_groups` |

Feature-Auswahl im Loader: Feature aktiv, wenn `tier <= stage` und keine seiner Gruppen in
`drop_groups ∪ (default_drop_groups − include_groups)`. Kantentypen werden genauso gefiltert und als One-Hot an
die Kantenfeatures gehängt (bei nur einem Typ entfällt das One-Hot). Rückkanten bekommen ein Flag `is_reverse`.

Standardisierung: Mittel/Std nur aus `train`. NaN → Mittelwert (= 0 nach Standardisierung) plus Spalte
`<feature>__missing`, wenn der NaN-Anteil in train > 1 % ist.

Nie als Input (in den Adaptern ausgeschlossen): Rollen/Identität, private Gedanken, Modellidentität, verbotene
Tool-Events (Swarm), Kills/Vents (Among Us). Privilegierte Signale nur über `include_groups`.
