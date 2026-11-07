#!/usr/bin/env python3
"""Morning report for a batch: progress, errors, tipping and the factor ablations (one table per factor).

  .venv/bin/python tools/night_report.py runs_night > runs_night/_logs/report.md
Works on partial runs too (prints what is finished).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
from query import Dataset  # noqa: E402

FACTORS = ["split", "category", "seed_type", "release_freeze", "manager_push", "discoverability", "channels",
           "self_merge", "persistent_share", "prohibition_form", "n_impossible", "persona_mix", "sanctions",
           "model_mix", "seed_status", "arm"]


def main(out: Path):
    ds = Dataset(ROOT / "dataset")
    rows = []
    for meta_f in sorted(out.glob("*/rep*/meta.json")):
        rd = meta_f.parent
        sc = ds.load(rd.parent.name)
        p = sc["params"]
        lab_f = rd / "labels.json"
        if not lab_f.exists():
            continue
        lab = json.loads(lab_f.read_text())
        meta = json.loads(meta_f.read_text())
        arm = rd.name.split("-", 1)[1] if "-" in rd.name else "control"
        row = {k: p.get(k) for k in FACTORS if k not in ("split", "arm", "model_mix")}
        row.update(split=sc["split"], arm=arm, model_mix=str(p.get("model_mix", "")).split(":")[0],
                   run=f"{rd.parent.name}/{rd.name}", tipped=bool(lab["tipped"]), tip_round=lab["tip_round"],
                   n_violators=lab["n_violators"], n_uninstructed=lab["n_violators_uninstructed"],
                   n_attempt_only=lab["n_attempters_without_violation"], n_at_risk=lab["n_at_risk"],
                   tipped_rel=bool(lab["tipped_rel"]), exposure=lab.get("exposure_share"),
                   viol_persistent=lab.get("n_violators_persistent"), n_persistent=lab.get("n_persistent"),
                   invalid_json=meta.get("invalid_json_rate"), jury=(rd / "jury_merged.jsonl").exists(),
                   features=(rd / "graph_nodes.csv").exists())
        rows.append(row)
    errors = sorted(str(p.parent.relative_to(out)) for p in out.glob("*/rep*/error.txt"))
    print(f"# Batch report: {out.name}\n")
    if not rows:
        print("No finished episodes with labels yet.")
        print(f"\nErrors: {len(errors)} {errors[:10]}")
        return
    df = pd.DataFrame(rows)
    print(f"Finished episodes: **{len(df)}**, errors: **{len(errors)}**, tipped (theta=8): **{df.tipped.sum()}** "
          f"({df.tipped.mean():.0%}), tipped_rel: {df.tipped_rel.mean():.0%}, mean violators {df.n_violators.mean():.1f}, "
          f"median tip round {df.tip_round.dropna().median() if df.tipped.any() else '-'}, "
          f"mean invalid_json {df.invalid_json.mean():.3f}, jury {df.jury.mean():.0%}, features {df.features.mean():.0%}\n")
    if errors:
        print("Errors:", ", ".join(errors[:20]), "\n")
    for f in FACTORS:
        if f not in df or df[f].nunique(dropna=False) < 2:
            continue
        g = df.groupby(df[f].astype(str)).agg(n=("tipped", "size"), tip_rate=("tipped", "mean"),
                                              violators=("n_violators", "mean"), attempt_only=("n_attempt_only", "mean"),
                                              tip_round=("tip_round", "median"))
        print(f"## {f}\n")
        try:
            print(g.round(2).to_markdown())
        except ImportError:   # tabulate missing
            print(g.round(2).to_string())
        print()
    pers = df[df.n_persistent.notna() & (df.n_persistent > 0)]
    if len(pers):
        print("## persistent persona (configs with persistent_share > 0)\n")
        print(f"violators among persistent agents: {pers.viol_persistent.sum():.0f} of {pers.n_persistent.sum():.0f} "
              f"persistent agents; all violators in these runs: {pers.n_violators.sum():.0f}\n")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "runs_night"))
