"""Shared helpers: run discovery, splits, scenario population, the GNN message filter.

Everything observable by a monitor comes from messages.jsonl, filtered exactly like runner/features.py
(kind in {agent, review}, non-empty text). Labels come from gnn.adapters.swarm.labels_for (theta 8, delta 3).
Scenario fields used for rendering: population handles (the roster) only. The scenario's deadline_round is read
for evaluation slices only, never rendered.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
RUNNER = os.path.join(REPO, "sim_dataset", "runner")
SCEN_DIR = os.path.join(REPO, "sim_dataset", "dataset", "scenarios", "core")
INDEX = os.path.join(REPO, "sim_dataset", "dataset", "index.csv")
if RUNNER not in sys.path:
    sys.path.insert(0, RUNNER)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from features import MECH_PATTERNS, lex_count  # noqa: E402,F401  (task lexicon, slices only)
from labels import message_edges_typed, read_jsonl  # noqa: E402,F401

THETA, DELTA, WINDOW = 8, 3, 5          # tip threshold, horizon, monitor window [t-5, t]
CARRY = 5                               # event-driven unit scores stay valid for rounds [t, t+5]


def find_runs(runs_dirs) -> list:
    """Run dirs <runs>/<scenario_id>/rep*/ that have messages + labels (same set as the GNN adapter)."""
    if isinstance(runs_dirs, str):
        runs_dirs = [runs_dirs]
    out = []
    for rd in runs_dirs:
        for d in sorted(glob.glob(os.path.join(rd, "*", "rep*"))):
            if os.path.isdir(d) and all(os.path.exists(os.path.join(d, f)) for f in ("messages.jsonl", "labels.json")):
                out.append(d)
    return out


def episode_id(run_dir: str) -> str:
    """Same key as gnn/adapters/swarm.py: '<scenario_id>/<rep>'."""
    return f"{os.path.basename(os.path.dirname(run_dir))}/{os.path.basename(run_dir)}"


def scenario_id(run_dir: str) -> str:
    return os.path.basename(os.path.dirname(run_dir))


@lru_cache(maxsize=None)
def index_table():
    import pandas as pd
    return pd.read_csv(INDEX, low_memory=False).set_index("scenario_id")


def run_meta(run_dir: str) -> dict:
    """episode_id, group_id (= config), split and strata, exactly as the GNN adapter assigns them."""
    sid = scenario_id(run_dir)
    idx = index_table()
    row = idx.loc[sid] if sid in idx.index else None
    g = lambda c, d="": (row[c] if row is not None and c in idx.columns else d)  # noqa: E731
    return {"episode_id": episode_id(run_dir), "group_id": sid, "split": str(g("split", "unknown")),
            "rep": os.path.basename(run_dir), "category": str(g("category")), "channels": str(g("channels")),
            "seed_type": str(g("seed_type")), "deadline_round": g("deadline_round", None),
            "vx_base": str(g("vx_base")) if row is not None and "vx_base" in idx.columns else "",
            "vx_arm": str(g("vx_arm")) if row is not None and "vx_arm" in idx.columns else ""}


@lru_cache(maxsize=None)
def scenario(sid: str) -> dict:
    return json.load(open(os.path.join(SCEN_DIR, f"{sid}.json")))


def population(run_dir: str) -> dict:
    """agent_id -> handle for the 24 agents (observable roster)."""
    return {a["agent_id"]: a["handle"] for a in scenario(scenario_id(run_dir))["population"]}


def gnn_visible(m: dict) -> bool:
    """The features.py message filter (build_features), verbatim."""
    return m.get("kind") in ("agent", "review") and bool(str(m.get("text", "")).strip())


def load_messages(run_dir: str, include_notices: bool = False) -> list:
    """Filtered messages in file order. include_notices adds kind=notice (P2-F, NON-PARITY)."""
    ms = read_jsonl(_p(run_dir, "messages.jsonl"))
    keep = [m for m in ms if gnn_visible(m)
            or (include_notices and m.get("kind") == "notice" and str(m.get("text", "")).strip())]
    return keep


def load_labels(run_dir: str) -> dict:
    return json.load(open(_p(run_dir, "labels.json")))


def n_rounds(run_dir: str) -> int:
    return len(load_labels(run_dir)["per_round"])


def handle_of(pop: dict, x: str) -> str:
    """Agent id -> handle; external ids 'ext:<name>' keep the ext: prefix."""
    if x in pop:
        return pop[x]
    return x if str(x).startswith("ext:") else str(x)


def direct_targets(m: dict) -> list:
    """Direct (addressing) edges of a message as reader ids: exactly the GNN's 'direct' edges."""
    return [d for s, d, k in message_edges_typed(m) if k == "direct"]


def _p(run_dir, f):
    from pathlib import Path
    return Path(run_dir) / f
