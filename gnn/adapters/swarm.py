#!/usr/bin/env python3
"""Swarm simulation runs -> canonical snapshot format (gnn/FORMAT.md).

Input: <runs>/<scenario_id>/rep<k>/{graph_edges.csv, graph_nodes.csv, labels.json} (run.py features + labels),
       sim_dataset/dataset/core_selection.csv (split + strata), feature catalog from sim_dataset/runner/features.py.
Snapshot = round t (1..R). Labels are recomputed here so theta / delta / attempts can change without re-running:
  graph: tip (theta reached within (t, t+delta], only while count_t < theta), new_violator (any new violator in
         (t, t+delta]), risk_count (count_t)
  node : violates_within_delta (agent's first violation in (t, t+delta]; empty once it has violated)
Optional judge swap: --jury deepseek-v4-flash expects graph_edges_<jury>.csv / graph_nodes_<jury>.csv per run
(written by a features run on jury_<judge>.jsonl) and writes edges_<jury>.csv / nodes_<jury>.csv.

Usage: python -m gnn.adapters.swarm --runs sim_dataset/runs --out data/swarm [--theta 8 --delta 3 --attempts]
       [--hash-split]   (pilot runs: assign train/val/test_id by scenario hash, for smoke tests only)
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
STRATA = ["category", "family", "seed_type", "channels", "discoverability", "seed_placement", "pressure_level",
          "prohibition_form", "topology", "model_mix_type", "vx_base", "vx_arm"]   # vx_*: validation-suite pairing


def catalog():
    sys.path.insert(0, os.path.join(REPO, "sim_dataset", "runner"))
    import features  # noqa: E402
    conv = lambda cat: [{"name": c, "tier": (99 if tier == "tool" else tier),
                         "groups": list(groups) + (["tool_activity"] if tier == "tool" else [])}
                        for _, _, cols, tier, _, groups, _ in cat for c in cols]
    return conv(features.EDGE_CATALOG), conv(features.NODE_CATALOG), features.CATALOG_VERSION


def labels_for(L: dict, theta: int, delta: int, attempts: bool, R: int):
    first = {a: r for a, r in L["first_violation_round"].items()}
    if attempts:
        for a, r in (L.get("first_attempt_round") or {}).items():
            first[a] = min(first.get(a, 99), r)
    cnt = {t: sum(1 for r in first.values() if r <= t) for t in range(0, R + 1)}
    G, N = [], {}
    for t in range(1, R + 1):
        hi = min(R, t + delta)
        tip = (int(any(cnt[u] >= theta for u in range(t + 1, hi + 1))) if cnt[t] < theta else None)
        G.append({"t": t, "tip": tip, "new_violator": int(cnt[hi] > cnt[t]) if t < R else None,
                  "risk_count": cnt[t]})
        N[t] = first
    return G, first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="one or more runs directories")
    ap.add_argument("--out", required=True)
    ap.add_argument("--selection", default=os.path.join(REPO, "sim_dataset", "dataset", "core_selection.csv"))
    ap.add_argument("--theta", type=int, default=8)
    ap.add_argument("--delta", type=int, default=3)
    ap.add_argument("--attempts", action="store_true", help="count blocked attempts as violations")
    ap.add_argument("--hash-split", action="store_true", help="split pilot runs by scenario hash (smoke tests)")
    ap.add_argument("--jury", default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sel = pd.read_csv(a.selection).set_index("scenario_id")
    # night / validation-suite configs are not in core_selection.csv: take split + strata from the index
    idx = pd.read_csv(os.path.join(REPO, "sim_dataset", "dataset", "index.csv"), low_memory=False).set_index("scenario_id")
    idx = idx.loc[~idx.index.isin(sel.index), [c for c in ["split"] + STRATA if c in idx.columns]]
    sel = pd.concat([sel, idx])
    ecat, ncat, cver = catalog()
    E, V, EP, SN, GL, NL = [], [], [], [], [], []
    sfx = f"_{a.jury}" if a.jury else ""
    n_runs = 0
    for runs in a.runs:
        for d in sorted(glob.glob(os.path.join(runs, "*", "rep*"))):
            fe, fn, fl = (os.path.join(d, f"graph_edges{sfx}.csv"), os.path.join(d, f"graph_nodes{sfx}.csv"),
                          os.path.join(d, "labels.json"))
            if not (os.path.exists(fe) and os.path.exists(fn) and os.path.exists(fl)):
                continue
            sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
            eid = f"{sid}/{rep}"
            L = json.load(open(fl))
            R = len(L["per_round"])
            split = sel.at[sid, "split"] if sid in sel.index else "unknown"
            if a.hash_split and split in ("pilot", "unknown"):
                h = int(hashlib.md5(sid.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
                split = "train" if h < 0.6 else ("val" if h < 0.8 else "test_id")
            row = {"episode_id": eid, "group_id": sid, "split": split, "rep": rep,
                   "tipped": int(bool(L.get("tipped"))), "n_violators": L.get("n_violators")}
            for c in STRATA:
                row[c] = sel.at[sid, c] if sid in sel.index and c in sel.columns else ""
            EP.append(row)
            e = pd.read_csv(fe)
            e.insert(0, "episode_id", eid)
            e = e.rename(columns={"round": "t"})
            e.insert(4, "etype", "address")
            E.append(e)
            v = pd.read_csv(fn).rename(columns={"round": "t", "node": "node_id"})
            v.insert(0, "episode_id", eid)
            V.append(v)
            G, first = labels_for(L, a.theta, a.delta, a.attempts, R)
            per_round_edges = e.groupby("t").size()
            for g in G:
                GL.append({"episode_id": eid, **g})
                SN.append({"episode_id": eid, "t": g["t"], "round": g["t"],
                           "n_edges": int(per_round_edges.get(g["t"], 0))})
            agents = set(v[v.role_external == 0].node_id) if "role_external" in v else set(v.node_id)
            for t in range(1, R + 1):
                hi = min(R, t + a.delta)
                for n in sorted(agents):
                    f = first.get(n, 99)
                    NL.append({"episode_id": eid, "t": t, "node_id": n,
                               "violates_within_delta": (None if f <= t else int(f <= hi)),
                               "violated_by_t": int(f <= t)})
            n_runs += 1
    if not n_runs:
        sys.exit("no runs with graph_*.csv + labels.json found (run `run.py features` and `run.py labels` first)")
    pd.concat(E).to_csv(os.path.join(a.out, f"edges{sfx}.csv"), index=False)
    pd.concat(V).to_csv(os.path.join(a.out, f"nodes{sfx}.csv"), index=False)
    if not a.jury:
        pd.DataFrame(EP).to_csv(os.path.join(a.out, "episodes.csv"), index=False)
        pd.DataFrame(SN).to_csv(os.path.join(a.out, "snapshots.csv"), index=False)
        pd.DataFrame(GL).to_csv(os.path.join(a.out, "graph_labels.csv"), index=False)
        pd.DataFrame(NL).to_csv(os.path.join(a.out, "node_labels.csv"), index=False)
        gl = pd.DataFrame(GL)
        schema = {"dataset": "swarm", "version": f"swarm-adapter-v1 / catalog {cver}",
                  "label_params": {"theta": a.theta, "delta": a.delta, "attempts": a.attempts},
                  "node_features": ncat, "edge_features": ecat, "etypes": [{"name": "address", "tier": 0, "groups": []}],
                  "graph_labels": {"tip": {"type": "binary"}, "new_violator": {"type": "binary"},
                                   "risk_count": {"type": "count", "max": 24}},
                  "node_labels": {"violates_within_delta": {"type": "binary"}},
                  "time_features": ["round", "n_edges"], "strata": STRATA,
                  "default_drop_groups": ["tool_activity"],
                  "stats": {"episodes": n_runs, "tip_pos": int(gl.tip.fillna(0).sum()),
                            "tip_valid": int(gl.tip.notna().sum()), "new_violator_pos": int(gl.new_violator.fillna(0).sum()),
                            "tipped_episodes": int(sum(r["tipped"] for r in EP))}}
        json.dump(schema, open(os.path.join(a.out, "schema.json"), "w"), indent=1)
        print(json.dumps(schema["stats"]))
    print(f"{n_runs} episodes -> {a.out}")


if __name__ == "__main__":
    main()
