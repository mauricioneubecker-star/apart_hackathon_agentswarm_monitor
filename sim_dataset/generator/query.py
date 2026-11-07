#!/usr/bin/env python3
"""Query and load scenarios.

Python:
    from query import Dataset
    ds = Dataset()                                    # dataset/ next to generator/
    df = ds.index                                     # pandas DataFrame, one row per scenario
    sel = ds.where("batch == 'full' and category == 'K2_scorer_config_tamper' and pressure_level == 'high' and split == 'train'")
    sc = ds.load(sel.scenario_id.iloc[0])             # full scenario dict
    vfs = ds.files(sc)                                # complete initial repository {path: content}
    print(ds.prompt(sc, "a03"))                       # system prompt of one agent
    for r, events in ds.timeline(sc): ...             # scripted events per round

CLI:
    python3 generator/query.py "category == 'K1_protected_test_edit' and malicious_count > 0" --limit 10
    python3 generator/query.py --show full-textkit-K1-0003 --agent a05
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import MockRepo, load_vfs  # noqa: E402

DEFAULT = Path(__file__).resolve().parents[1] / "dataset"


class Dataset:
    def __init__(self, root: str | Path = DEFAULT):
        import pandas as pd
        self.root = Path(root)
        self.index = pd.read_parquet(self.root / "index.parquet")

    def where(self, expr: str):
        return self.index.query(expr, engine="python")

    def load(self, scenario_id: str) -> dict:
        row = self.index[self.index.scenario_id == scenario_id]
        if row.empty:
            raise KeyError(scenario_id)
        return json.loads((self.root / row.path.iloc[0]).read_text())

    def iter(self, expr: str | None = None):
        rows = self.where(expr) if expr else self.index
        for p in rows.path:
            yield json.loads((self.root / p).read_text())

    def files(self, sc: dict) -> dict:
        return load_vfs(sc, self.root)

    def env(self, sc: dict) -> MockRepo:
        return MockRepo(sc, self.root)

    def package(self, sc: dict) -> dict:
        return json.loads((self.root / sc["refs"]["package_path"] / "package.json").read_text())

    @staticmethod
    def prompt(sc: dict, agent_id: str) -> str:
        return next(a for a in sc["population"] if a["agent_id"] == agent_id)["system_prompt"]

    @staticmethod
    def timeline(sc: dict):
        for t in sc["timeline"]:
            yield t["round"], t["events"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expr", nargs="?")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--cols", default="scenario_id,split,category,pressure_level,frac_impossible,channels,prohibition_form,early_adopter_source,malicious_variants")
    ap.add_argument("--show")
    ap.add_argument("--agent")
    a = ap.parse_args()
    ds = Dataset()
    if a.show:
        sc = ds.load(a.show)
        if a.agent:
            print(ds.prompt(sc, a.agent))
        else:
            print(json.dumps(sc["spec"], indent=1))
        return
    df = ds.where(a.expr) if a.expr else ds.index
    print(f"{len(df)} scenarios")
    print(df[a.cols.split(",")].head(a.limit).to_string(index=False))


if __name__ == "__main__":
    main()
