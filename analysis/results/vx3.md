# Bestätigungstest auf frischen Läufen (`runs_vx3`, ANALYSIS_PLAN.md Nachtrag 3)

**Stand:** 9. Nov. 2026, 11:40. Nachtrag 3 wurde um 07:44 gepusht (`e319c9e7`), bevor die erste Episode lief. Die
Vorhersagen aller 12 Monitore wurden vor der Auswertung eingefroren und gepusht (`289b8759`). Die Auswertung lief
einmal, 11:28–11:34 (`c97b90d1`). Vorher haben wir geprüft, dass kein anderer Branch schon eine Auswertung enthält.

**Daten.** 27 neue Läufe der 14 unveränderten `night_vx`-Setups (rep2: 14, rep3: 13), alle 14 Setups mit mindestens
einem Lauf, 698 bewertete Zeilen, 42 davon positiv. Ein Lauf brach in Runde 30 an einem Rate-Limit des Anbieters ab
und wurde nach der vorab festgelegten Startgrenze 10:30 nicht neu gestartet.

## Ergebnis

**H7 ist nicht gestützt.** Das LLM mit dem ganzen Protokoll (`global_full`) erreicht AUROC 0,871, das eingefrorene GNN
0,839. Die Differenz +0,032 hat die CI [−0,052; +0,138], die untere Grenze liegt also unter 0. Der Vorsprung von +0,08,
den wir nachträglich auf `night_vx` gefunden hatten, hat sich auf frischen Läufen nicht bestätigt. Er war vermutlich zum
Teil Zufall der ausgewählten Läufe.

**Nebenvergleiche** (vorab festgelegt, ohne Entscheidungsregel, nur beschreibend):

| Vergleich | Differenz [95 %-CI] |
|---|---|
| `global_full` − GNN, zeitgematcht | +0,010 [−0,155; +0,226] |
| `global_full` − GNN + Tabellenmodell | +0,004 [−0,071; +0,096] |
| LLM Gespräch für Gespräch (`pairwise`) − GNN | +0,116 [+0,046; +0,215] |

Das LLM Gespräch für Gespräch kommt auf den frischen Läufen auf 0,955. Seine CI gegen das GNN liegt über 0. Das ist aber
ein Nebenvergleich ohne Entscheidungsregel und ohne Korrektur, und Perzentil-CIs über 14 Setups sind antikonservativ.
Als Hypothese für künftige Arbeit taugt er, als Ergebnis nicht.

## Wiederholungsrauschen (beschreibend)

Dieselben 14 Setups liefen jetzt viermal (rep0–rep3). Die AUROC eines Monitors schwankt zwischen den Wiederholungen um
0,05 (`global_full`) bis 0,20 (Uhr). Die Uhr kommt auf 0,82, 0,63, 0,80 und 0,75: Ihr Einbruch in rep1 war ein
Ausreißer. Gekippt sind 6, 7, 7 und 7 Läufe, die mittlere Kipprunde liegt bei 20,8, 25,0, 22,7 und 23,3. Auch das spät
kippende rep1 sieht damit nach Zufall aus, nicht nach einem Effekt der Reihenfolge.

## Was wir sagen dürfen

- „Ein vorab festgelegter Bestätigungstest auf 27 frischen Läufen hat den nachträglich gefundenen Vorsprung des LLM mit
  dem ganzen Protokoll vor dem GNN nicht bestätigt (+0,03 [−0,05; +0,14]).“
- „Zwischen Wiederholungen derselben Setups schwankt die AUROC eines Monitors um bis zu 0,2. Validierungen brauchen
  deshalb mehrere Wiederholungen als Rauschkontrolle.“

Nicht sagen: „Das LLM Gespräch für Gespräch schlägt das GNN“ (nur Nebenvergleich), „die Monitore sind gleich gut“ (die
CIs sind breit) oder etwas über andere Setups als diese 14.

## Dateien

`analysis/results/vx3_eval.{json,md}`, `vx3_run.log`; Eingaben `analysis/vx3_preds/` (README mit genauen Befehlen);
Läufe `sim_dataset/runs_vx3/`; Plan ANALYSIS_PLAN.md Nachtrag 3; Skript `analysis/vx3_eval.py`.
