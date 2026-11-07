#!/usr/bin/env python3
"""Swarm simulation runs -> canonical snapshot format (gnn/FORMAT.md). Matches sim v1.4b (feature catalog v1.1).

Input per episode: <runs>/<scenario_id>/<rep>/{graph_edges.csv, graph_nodes.csv, labels.json[, branch.json]}
(written by `run.py labels` + `run.py features`), split and strata from sim_dataset/dataset/index.csv.

- Snapshot = round t (1..R, R per episode: 20 / 25 / 30). Edges i->j = j read a message of i in [t-2, t] (direct or
  broadcast, catalog v1.1: direct_volume / bcast_volume tell them apart).
- Branch arms (`rep0-<arm>` with branch.json): rounds <= branch_round are identical to the control run, so they are kept
  only once (in the control). Arms and control share group_id = scenario_id -> always in the same split.
- Labels are recomputed here from labels.json, so theta / delta / attempts can change without re-running the sim:
    graph: tip (theta reached within (t, t+delta], only while count_t < theta), new_violator (>= 1 new violator in
           (t, t+delta]), risk_count (count_t), malicious_present (aux)
    node : violates_within_delta (first violation in (t, t+delta]; empty once violated and for external senders)
- Splits: core scenarios keep their split (train / val / test_* / val_ood_*). Pilot splits (pilot, pilot3, pilot4, ...)
  are assigned by scenario hash with --pilot-split hash (default, 60/20/20) or put into one split (--pilot-split train).

Usage:
  python -m gnn.adapters.swarm --runs sim_dataset/runs_pilot3 sim_dataset/runs_pilot4 --out data/swarm_pilots
  python -m gnn.adapters.swarm --runs sim_dataset/runs --out data/swarm --theta 8 --delta 3
  python -m gnn.adapters.swarm ... --jury deepseek-v4-flash      (judge swap: needs graph_*_<judge>.csv per run)
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
STRATA = ["category", "family", "seed_type", "channels", "discoverability", "seed_placement", "pressure_level",
          "prohibition_form", "topology", "model_mix_type", "n_impossible", "rounds"]
CORE_SPLITS = {"train", "val", "test_id", "test_ood_family", "test_ood_seed", "test_backbone", "val_ood_comp",
               "val_ood_population", "val_ood_topology"}


def catalog():
    sys.path.insert(0, os.path.join(REPO, "sim_dataset", "runner"))
    import features  # noqa: E402
    conv = lambda cat: [{"name": c, "tier": (99 if tier == "tool" else tier),
                         "groups": list(groups) + (["tool_activity"] if tier == "tool" else [])}
                        for _, _, cols, tier, _, groups, _ in cat for c in cols]
    return conv(features.EDGE_CATALOG), conv(features.NODE_CATALOG), features.CATALOG_VERSION


def first_rounds(L: dict, attempts: bool) -> dict:
    first = dict(L.get("first_violation_round") or {})
    if attempts:
        for a, r in (L.get("first_attempt_round") or {}).items():
            first[a] = min(first.get(a, 10 ** 6), r)
    return first


def split_for(sid: str, raw: str, mode: str) -> str:
    if raw in CORE_SPLITS:
        return raw
    if mode == "hash":
        h = int(hashlib.md5(sid.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        return "train" if h < 0.6 else ("val" if h < 0.8 else "test_id")
    return mode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True, help="one or more runs directories")
    ap.add_argument("--out", required=True)
    ap.add_argument("--index", default=os.path.join(REPO, "sim_dataset", "dataset", "index.csv"))
    ap.add_argument("--theta", type=int, default=8)
    ap.add_argument("--delta", type=int, default=3)
    ap.add_argument("--attempts", action="store_true", help="count blocked attempts as violations")
    ap.add_argument("--pilot-split", default="hash", help="hash | train | val | test_id | ... for non-core splits")
    ap.add_argument("--no-branches", action="store_true", help="drop branch arms")
    ap.add_argument("--jury", default=None, help="judge swap: read graph_*_<jury>.csv, write edges/nodes_<jury>.csv")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    idx = pd.read_csv(a.index, low_memory=False).set_index("scenario_id")
    ecat, ncat, cver = catalog()
    sfx = f"_{a.jury}" if a.jury else ""
    E, V, EP, SN, GL, NL = [], [], [], [], [], []
    stats = {"episodes": 0, "branch_arms": 0, "prefix_rounds_dropped": 0, "missing_graph": 0}
    for runs in a.runs:
        for d in sorted(glob.glob(os.path.join(runs, "*", "rep*"))):
            fe, fn, fl = (os.path.join(d, f"graph_edges{sfx}.csv"), os.path.join(d, f"graph_nodes{sfx}.csv"),
                          os.path.join(d, "labels.json"))
            if not (os.path.exists(fe) and os.path.exists(fn) and os.path.exists(fl)):
                stats["missing_graph"] += 1
                continue
            sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
            br_path = os.path.join(d, "branch.json")
            branch = json.load(open(br_path)) if os.path.exists(br_path) else None
            if branch and a.no_branches:
                continue
            t0 = int(branch["branch_round"]) if branch else 0      # keep rounds > t0 only (prefix lives in control)
            eid = f"{sid}/{rep}"
            L = json.load(open(fl))
            R = len(L["per_round"])
            meta = idx.loc[sid] if sid in idx.index else None
            raw = str(meta["split"]) if meta is not None else "unknown"
            row = {"episode_id": eid, "group_id": sid, "split": split_for(sid, raw, a.pilot_split), "raw_split": raw,
                   "rep": rep, "arm": (branch or {}).get("arm", "control"), "branch_round": t0, "R": R,
                   "tipped": int(bool(L.get("tipped"))), "n_violators": L.get("n_violators")}
            for c in STRATA:
                row[c] = meta[c] if meta is not None and c in meta.index else ""
            EP.append(row)
            stats["episodes"] += 1
            stats["branch_arms"] += int(bool(branch))
            stats["prefix_rounds_dropped"] += t0

            e = pd.read_csv(fe).rename(columns={"round": "t"})
            e = e[e.t > t0]
            e.insert(0, "episode_id", eid)
            e.insert(4, "etype", "read")
            E.append(e)
            v = pd.read_csv(fn).rename(columns={"round": "t", "node": "node_id"})
            v = v[v.t > t0]
            v.insert(0, "episode_id", eid)
            V.append(v)

            first = first_rounds(L, a.attempts)
            cnt = {t: sum(1 for r in first.values() if r <= t) for t in range(0, R + 1)}
            mal = {r["round"]: int(bool(r.get("aux_malicious_present_t"))) for r in L["per_round"]}
            n_edges = e.groupby("t").size()
            agents = sorted(set(v.node_id[v.get("role_external", 0) == 0])) if len(v) else []
            for t in range(t0 + 1, R + 1):
                hi = min(R, t + a.delta)
                tip = (int(any(cnt[u] >= a.theta for u in range(t + 1, hi + 1))) if cnt[t] < a.theta else None)
                GL.append({"episode_id": eid, "t": t, "tip": tip if t < R else None,
                           "new_violator": int(cnt[hi] > cnt[t]) if t < R else None,
                           "risk_count": cnt[t], "malicious_present": mal.get(t, 0)})
                SN.append({"episode_id": eid, "t": t, "round": t, "round_frac": round(t / R, 4),
                           "n_edges": int(n_edges.get(t, 0))})
                for n in agents:
                    f = first.get(n, 10 ** 6)
                    NL.append({"episode_id": eid, "t": t, "node_id": n,
                               "violates_within_delta": (None if f <= t or t == R else int(f <= hi))})
    if not EP:
        sys.exit("no runs with graph_*.csv + labels.json found (run `run.py labels` and `run.py features` first)")
    pd.concat(E).to_csv(os.path.join(a.out, f"edges{sfx}.csv"), index=False)
    pd.concat(V).to_csv(os.path.join(a.out, f"nodes{sfx}.csv"), index=False)
    if a.jury:
        print(f"{stats['episodes']} episodes ({a.jury}) -> {a.out}")
        return
    ep = pd.DataFrame(EP)
    ep.to_csv(os.path.join(a.out, "episodes.csv"), index=False)
    pd.DataFrame(SN).to_csv(os.path.join(a.out, "snapshots.csv"), index=False)
    gl = pd.DataFrame(GL)
    gl.to_csv(os.path.join(a.out, "graph_labels.csv"), index=False)
    pd.DataFrame(NL).to_csv(os.path.join(a.out, "node_labels.csv"), index=False)
    nl = pd.DataFrame(NL)
    stats.update({"snapshots": len(gl), "tip_valid": int(gl.tip.notna().sum()), "tip_pos": int(gl.tip.fillna(0).sum()),
                  "new_violator_pos": int(gl.new_violator.fillna(0).sum()),
                  "node_pos": int(nl.violates_within_delta.fillna(0).sum()),
                  "tipped_episodes": int(ep.tipped.sum()), "splits": ep.split.value_counts().to_dict(),
                  "edges_per_snapshot": round(sum(len(x) for x in E) / max(len(gl), 1), 1)})
    schema = {"dataset": "swarm", "version": f"swarm-adapter-v2 / catalog {cver}",
              "label_params": {"theta": a.theta, "delta": a.delta, "attempts": a.attempts},
              "node_features": ncat, "edge_features": ecat, "etypes": [{"name": "read", "tier": 0, "groups": []}],
              "graph_labels": {"tip": {"type": "binary"}, "new_violator": {"type": "binary"},
                               "risk_count": {"type": "count", "max": 24}, "malicious_present": {"type": "binary"}},
              "node_labels": {"violates_within_delta": {"type": "binary"}},
              "time_features": ["round", "round_frac", "n_edges"], "strata": STRATA + ["arm"],
              "default_drop_groups": ["tool_activity"], "stats": stats}
    json.dump(schema, open(os.path.join(a.out, "schema.json"), "w"), indent=1, default=str)
    print(json.dumps(stats, default=str))


if __name__ == "__main__":
    main()
