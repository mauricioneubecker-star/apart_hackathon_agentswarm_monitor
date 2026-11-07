#!/usr/bin/env python3
"""Helpers for tools/night_run.sh (portable between macOS and Linux, no GNU tools needed).

  night_util.py remaining <out> <where> <replicates>   number of episodes still missing (replicates 0 = planned)
  night_util.py finished <out>                         number of finished run dirs (meta.json, incl. branch arms)
  night_util.py idle <out>                             minutes since any episode log was last written
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))


def remaining(out: Path, where: str, reps: int) -> int:
    from query import Dataset
    rows = Dataset(ROOT / "dataset").where(where)
    n = 0
    for sid, rp in zip(rows.scenario_id, rows.get("replicates_planned", [1] * len(rows))):
        k = int(rp) if reps == 0 and rp == rp else max(1, reps)
        n += sum(1 for r in range(k) if not (out / sid / f"rep{r}" / "meta.json").exists())
    return n


def idle_minutes(out: Path) -> float:
    newest = 0.0
    for f in out.glob("*/rep*/rounds.jsonl"):
        try:
            newest = max(newest, f.stat().st_mtime)
        except OSError:
            pass
    return (time.time() - newest) / 60 if newest else 0.0


if __name__ == "__main__":
    cmd, out = sys.argv[1], Path(sys.argv[2])
    if cmd == "remaining":
        print(remaining(out, sys.argv[3], int(sys.argv[4])))
    elif cmd == "finished":
        print(len(list(out.glob("*/rep*/meta.json"))))
    elif cmd == "idle":
        print(int(idle_minutes(out)))
    else:
        sys.exit(f"unknown command {cmd}")
