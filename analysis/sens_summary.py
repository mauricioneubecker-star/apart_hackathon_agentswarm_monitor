"""Summarise the theta/delta sensitivity runs of sens.py into one Markdown table.

Point AUROCs are recomputed from each tag's oof/preds.csv (they match oof/results.json). Differences come from an
own paired cluster bootstrap over configs (B draws, same draws for all predictors). Extra column "θ=10, nur
Zähler < 8": the theta=10 labels on exactly the theta=8 rows (count < 8), because the zero-shot monitors were
prompted for theta=8 and treat rows with 8-9 violators as already tipped.

  python sens_summary.py <work_dir> [B] > sensitivity.md
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

work = sys.argv[1]
B = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
TAGS = [("t8d3", None), ("t6d3", None), ("t10d3", None), ("t10d3", "lt8"), ("t8d2", None), ("t8d5", None)]
PRED = [("clock", "nur Uhr"), ("bag+graph", "bag + graph"), ("zs:global_full", "LLM ganzes Protokoll"),
        ("zs:global_window", "LLM letzte 6 Runden"), ("zs:pairwise", "LLM Gespräch für Gespräch"),
        ("hgb:pairwise", "LLM Gespräch für Gespräch, gestackt"), ("oracle", "Verstoßzähler + Uhr (Referenz)")]
DIFFS = [("zs:pairwise", "clock", "LLM Gespräch für Gespräch − Uhr"),
         ("zs:global_full", "clock", "LLM ganzes Protokoll − Uhr"),
         ("bag+graph", "clock", "bag + graph − Uhr"),
         ("zs:pairwise", "bag+graph", "LLM Gespräch für Gespräch − bag + graph"),
         ("zs:global_full", "bag+graph", "LLM ganzes Protokoll − bag + graph")]


def load(tag, restrict):
    Bs = pd.read_csv(os.path.join(work, "data", tag, "_base", "snapshots.csv"), low_memory=False)
    P = pd.read_csv(os.path.join(work, "results", tag, "oof", "preds.csv"))
    night = Bs.split.str.startswith("night_") & ~Bs.split.str.startswith("night_vx")
    Ba = Bs[(night & Bs.tip.notna()).values].reset_index(drop=True)
    assert len(Ba) == len(P) and (Ba.episode_id.values == P.episode_id.values).all() and (Ba.t.values == P.t.values).all()
    names = [c for c in P.columns if c not in ("episode_id", "t")]
    D = pd.concat([Ba, P[names]], axis=1)
    D = D[np.all([D[n].notna().values for n in names], 0)].reset_index(drop=True)
    if restrict == "lt8":
        D = D[D.risk_count < 8].reset_index(drop=True)
    runs = Bs.groupby("episode_id").tipped.first()
    return D, runs


def tm_auroc(y, p, rtc):
    """Time-matched AUROC: pairs-weighted AUROC within rounds-to-cut bins (as llm_monitor.evaluate)."""
    s = np.asarray(pd.Series(pd.cut(np.asarray(rtc, dtype=float), [-99, -9, -5, -1, 3, 99])).astype(str))
    num = den = 0.0
    for b in np.unique(s):
        m = s == b
        npos = int(y[m].sum()); nneg = int(m.sum() - npos)
        if npos and nneg:
            num += npos * nneg * roc_auc_score(y[m], p[m]); den += npos * nneg
    return num / den if den else np.nan


def boot_diffs(D, pairs, n_boot, seed=0):
    g = D.group_id.values
    ug = np.unique(g)
    members = {u: np.where(g == u)[0] for u in ug}
    rng = np.random.default_rng(seed)
    y = D.tip.values.astype(float)
    need = sorted({a for a, _, _ in pairs} | {b for _, b, _ in pairs})
    res = {n: [] for n in need}
    for _ in range(n_boot):
        b = np.concatenate([members[u] for u in rng.choice(ug, len(ug), replace=True)])
        if not (0 < y[b].sum() < len(b)):
            continue
        for n in need:
            res[n].append(roc_auc_score(y[b], D[n].values[b]))
    out = {}
    for a, r, _ in pairs:
        d = np.array(res[a]) - np.array(res[r])
        p2 = min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))
        out[(a, r)] = (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), max(p2, 1 / len(d)))
    return out


cols, table = [], {}
for tag, restrict in TAGS:
    if not os.path.exists(os.path.join(work, "results", tag, "oof", "preds.csv")):
        continue
    D, runs = load(tag, restrict)
    y = D.tip.values.astype(float)
    th, de = tag[1:].split("d")
    col = f"θ={th}, Δ={de}" + (" (nur Zähler < 8)" if restrict else "")
    cols.append(col)
    t = table.setdefault(col, {})
    t["gekippte Läufe"] = f"{int(runs.sum())}/{len(runs)}"
    t["Zeilen (positiv)"] = f"{len(D)} ({int(y.sum())})"
    for k, name in PRED:
        t[name] = f"{roc_auc_score(y, D[k].values):.3f}"
        t[name + " (zeitgematcht)"] = f"{tm_auroc(y, D[k].values, D.rounds_to_cut.values):.3f}"
    full = {(a, r): roc_auc_score(y, D[a].values) - roc_auc_score(y, D[r].values) for a, r, _ in DIFFS}
    bd = boot_diffs(D, DIFFS, B)
    for a, r, name in DIFFS:
        lo, hi, p = bd[(a, r)]
        t[name] = f"{full[(a, r)]:+.3f} [{lo:+.3f}, {hi:+.3f}], p = {p:.3f}"
    # cross-check against llm_monitor.evaluate (point AUROCs, full rows only)
    if not restrict:
        R = json.load(open(os.path.join(work, "results", tag, "oof", "results.json")))
        for k, _ in PRED:
            assert abs(R["main"][k]["auroc"] - roc_auc_score(y, D[k].values)) < 2e-3, (tag, k)

rows = list(next(iter(table.values())).keys())
T = pd.DataFrame({c: [table[c].get(r, "–") for r in rows] for c in cols}, index=rows)
print(f"""# θ/Δ-Sensitivität (Nacht-Batch, Protokoll a, OOF über alle 112 Konfigurationen)

Gerechnet mit `analysis/sens.py` (Labels neu, keine Simulation) und `analysis/sens_summary.py`. AUROC-Differenzen:
gepaarter Cluster-Bootstrap über Konfigurationen, {B}×, Seed 0, zweiseitiges p = 2·min(P(d ≤ 0), P(d ≥ 0)). Zeitgematcht
= AUROC innerhalb der Bins „Runden bis zur Deadline“ (≤ −9, −8…−5, −4…−1, 0…3, > 3), nach Paaren gewichtet.

{T.to_markdown()}

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
""")
