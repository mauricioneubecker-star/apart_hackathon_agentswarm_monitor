#!/usr/bin/env python3
"""Descriptive summary of the validation suite (no monitor evaluation; that runs once, after freezing the models).

  .venv/bin/python tools/vx_summary.py runs_vx [--night runs_night] > runs_vx/_logs/vx_summary.md

Tables: progress and data quality per arm (incl. invalid JSON per model key, so GLM / 4B format problems show up),
outcome per arm, base x arm outcome grid, paired outcome changes vs. the id twin (with the id rep1-vs-rep0 noise
floor), the 4B block (violators among the agents on the 4B model), and Part B (new replicates next to the night runs
of the same config).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
from query import Dataset  # noqa: E402

ARMS = ["id", "time", "glm", "enf", "topo", "bal", "ft4", "p4", "b4", "rep"]


def run_rows(out: Path, ds: Dataset):
    rows, per_model = [], defaultdict(lambda: [0, 0])
    for meta_f in sorted(out.glob("*/rep*/meta.json")):
        rd = meta_f.parent
        try:
            sc = ds.load(rd.parent.name)
        except KeyError:
            continue
        p = sc["params"]
        lab_f = rd / "labels.json"
        lab = json.loads(lab_f.read_text()) if lab_f.exists() else {}
        meta = json.loads(meta_f.read_text())
        model_of = {a["agent_id"]: a["model"] for a in sc["population"]}
        calls_f = rd / "llm_calls.jsonl"
        if calls_f.exists():
            with calls_f.open() as fh:
                for line in fh:
                    try:
                        c = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    k = per_model[(p.get("vx_arm"), model_of.get(c.get("agent"), "?"))]
                    k[0] += 1
                    k[1] += 0 if c.get("parse_ok", True) else 1
        jury = (rd / "jury_merged.jsonl").exists()
        rows.append(dict(arm=p.get("vx_arm"), base=p.get("vx_base"), rep=rd.name, split=sc["split"],
                         category=sc["refs"]["category"][:2], channels=p.get("channels"),
                         tipped=lab.get("tipped"), tipped_rel=lab.get("tipped_rel"), nv=lab.get("n_violators"),
                         tip_round=lab.get("tip_round"), first_v=lab.get("first_violation_round"),
                         nv_persistent=lab.get("n_violators_persistent"), n_persistent=lab.get("n_persistent"),
                         invalid_json=meta.get("invalid_json_rate"), msgs=meta.get("n_messages"), jury=jury,
                         features=(rd / "graph_edges.csv").exists(), error=(rd / "error.txt").exists()))
    return pd.DataFrame(rows), per_model


def md(df: pd.DataFrame) -> str:
    return df.to_markdown() if len(df) else "_(none yet)_"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--night", default=str(ROOT / "runs_night"))
    a = ap.parse_args()
    ds = Dataset(ROOT / "dataset")
    df, per_model = run_rows(Path(a.out), ds)
    print(f"# Validation suite summary: {a.out}\n")
    planned = ds.where("split.str.startswith('night_vx')")
    print(f"Finished runs: **{len(df)}**; planned (excl. reserve): "
          f"**{int(planned[planned.split != 'night_vx_pop_bal'].replicates_planned.sum())}**\n")
    if df.empty:
        return
    df["arm"] = pd.Categorical(df.arm, [x for x in ARMS if x in set(df.arm)], ordered=True)
    print("## Per arm\n")
    g = df.groupby("arm", observed=True).agg(runs=("rep", "size"), tip_rate=("tipped", "mean"),
                                             tip_rel=("tipped_rel", "mean"), violators=("nv", "mean"),
                                             tip_round=("tip_round", "median"), invalid_json=("invalid_json", "mean"),
                                             msgs=("msgs", "mean"), jury=("jury", "mean"), features=("features", "mean"),
                                             errors=("error", "sum"))
    print(md(g.round(3)), "\n")
    print("## Invalid JSON per model key (share of agent calls that did not parse)\n")
    pm = pd.DataFrame([dict(arm=k[0], model=k[1], calls=v[0], invalid=round(v[1] / max(1, v[0]), 3))
                       for k, v in per_model.items()]).sort_values(["arm", "model"]).set_index(["arm", "model"])
    print(md(pm), "\n")

    A = df[df.arm != "rep"].copy()
    if len(A):
        A["cell"] = A.apply(lambda r: f"{'T' if r.tipped else '-'}{int(r.nv) if r.nv == r.nv else '?'}", axis=1)
        A["col"] = A.apply(lambda r: f"{r.arm}" + (f"/{r.rep}" if r.arm == "id" else ""), axis=1)
        grid = A.pivot_table(index="base", columns="col", values="cell", aggfunc="first")
        print("## Part A: base x arm (T = tipped, number = violators)\n")
        print(md(grid), "\n")
        idr = {(r.base, r.rep): r for r in A[A.arm == "id"].itertuples()}
        pairs = []
        for r in A[A.arm != "id"].itertuples():
            ref = idr.get((r.base, "rep0"))
            if ref is not None:
                pairs.append(dict(arm=r.arm, flip=int(bool(r.tipped) != bool(ref.tipped)), d_nv=r.nv - ref.nv))
        for b in {x for x, _ in idr}:
            if (b, "rep0") in idr and (b, "rep1") in idr:
                r0, r1 = idr[(b, "rep0")], idr[(b, "rep1")]
                pairs.append(dict(arm="id rep1 (noise)", flip=int(bool(r1.tipped) != bool(r0.tipped)), d_nv=r1.nv - r0.nv))
        if pairs:
            P = pd.DataFrame(pairs).groupby("arm").agg(bases=("flip", "size"), outcome_flips=("flip", "sum"),
                                                       mean_d_violators=("d_nv", "mean"))
            print("## Paired outcome change vs. id rep0 (same base)\n")
            print(md(P.round(2)), "\n")
        F = A[A.arm.isin(["ft4", "p4", "b4"])]
        if len(F):
            print("## 4B block: violators among the agents on the 4B model\n")
            print(md(F.groupby("arm", observed=True).agg(runs=("rep", "size"), on_4b=("n_persistent", "mean"),
                                                         violators_4b=("nv_persistent", "mean"),
                                                         violators_all=("nv", "mean"), tip_rate=("tipped", "mean"))
                     .round(2)), "\n")
    B = df[df.arm == "rep"]
    if len(B):
        print("## Part B: new replicates next to the night runs of the same config\n")
        rows = []
        for src, grp in B.groupby("base"):
            old = []
            for lf in sorted(Path(a.night).glob(f"{src}/rep*/labels.json")):
                L = json.loads(lf.read_text())
                old.append(f"{'T' if L['tipped'] else '-'}{L['n_violators']}")
            new = [f"{'T' if r.tipped else '-'}{r.nv}" for r in grp.itertuples()]
            rows.append(dict(config=src.removeprefix("core-"), night=" ".join(old), new=" ".join(new)))
        print(md(pd.DataFrame(rows).set_index("config")), "\n")


if __name__ == "__main__":
    main()
