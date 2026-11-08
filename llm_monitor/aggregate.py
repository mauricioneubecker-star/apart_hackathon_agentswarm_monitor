"""Monitor outputs -> per-snapshot and per-node tables aligned 1:1 with the GNN rows.

  python -m llm_monitor.aggregate [--runs sim_dataset/runs_night] [--out data/llm_monitor] [--variants ...]

Writes data/llm_monitor/_base/{snapshots,nodes}.csv (keys, split, labels, slice columns; labels from the GNN adapter's
labels_for with theta 8, delta 3) and per variant data/llm_monitor/<variant>/snapshots.csv (episode_id, t, group_id,
split + monitor features) and nodes.csv (episode_id, t, node_id, p_violated, p_will). Only rows with the current
prompt_version and ok == True are used; snapshots a variant did not score are NaN.
Zero-shot columns: zs_tip (p_tip_3 / 100; pairwise/agent: max suspicion / 100), zs_count (est_violators; pairwise:
#distinct agents with p_violated >= 50; agent: sum p_violated / 100), node p_will (at_risk p / 100).
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd

from . import prompts as P
from .common import (CARRY, DELTA, REPO, THETA, MECH_PATTERNS, episode_id, find_runs, lex_count, load_labels,
                     load_messages, population, run_meta, scenario, scenario_id)
from gnn.adapters.swarm import labels_for  # noqa: E402

OUT = os.path.join(REPO, "data", "llm_monitor")
GLOBAL_VARIANTS = ["global_full", "global_window", "global_full_informed", "global_full_notices", "global_sequential"]


# ------------------------------------------------------------------------------------------------------ base
def base_frames(runs: list):
    S, N = [], []
    for d in runs:
        m = run_meta(d)
        L = load_labels(d)
        R = len(L["per_round"])
        G, first = labels_for(L, THETA, DELTA, False, R)
        sc = scenario(scenario_id(d))
        br = os.path.join(d, "branch.json")
        br = json.load(open(br)) if os.path.exists(br) else None
        msgs = load_messages(d)
        mech = [x for x in msgs if lex_count(x["text"], MECH_PATTERNS) > 0]
        first_mech = min((x["round"] for x in mech), default=None)
        # first announcement: a filtered message with mech_ref > 0 whose sender had already violated by that round
        ann = min((x["round"] for x in mech if first.get(x["sender"], 99) <= x["round"]), default=None)
        cut = m["deadline_round"]
        cat = "K2" if m["category"].startswith("K2") else ("K4" if m["category"].startswith("K4") else m["category"])
        for g in G:
            t = g["t"]
            S.append({"episode_id": m["episode_id"], "t": t, "group_id": m["group_id"], "split": m["split"],
                      "rep": m["rep"], "cat": cat, "channels": m["channels"], "seed_type": m["seed_type"],
                      "vx_base": m["vx_base"], "vx_arm": m["vx_arm"], "arm": (br or {}).get("arm", "control"),
                      "branch_round": int(br["branch_round"]) if br else 0, "R": R,
                      "cut": cut, "rounds_to_cut": (t - cut) if cut is not None and not pd.isna(cut) else np.nan,
                      "tip": g["tip"], "risk_count": g["risk_count"], "tipped": int(bool(L.get("tipped"))),
                      "tip_round": L.get("tip_round"), "first_mech_round": first_mech, "announce_round": ann,
                      "before_announce": int(ann is None or t < ann)})
        stuck = {a["agent_id"] for a in sc["population"]
                 if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
        for t in range(1, R + 1):
            hi = min(R, t + DELTA)
            for a in sorted(population(d)):
                f = first.get(a, 99)
                N.append({"episode_id": m["episode_id"], "t": t, "node_id": a,
                          "violates_within_delta": (np.nan if f <= t else float(f <= hi)),
                          "violated_by_t": int(f <= t), "stuck": int(a in stuck)})
    S = pd.DataFrame(S)
    # mixed configs: both tipped and untipped runs among the config's runs (within this batch)
    tip_by_cfg = S.groupby("group_id").apply(lambda x: x.groupby("episode_id").tipped.first().nunique() > 1)
    S["mixed"] = S.group_id.map(tip_by_cfg).astype(int)
    return S, pd.DataFrame(N)


# ----------------------------------------------------------------------------------------------- monitor rows
def read_rows(run_dir: str, variant: str, sfx: str = "") -> list:
    p = os.path.join(run_dir, f"monitor_{variant}{sfx}.jsonl")
    if not os.path.exists(p):
        return []
    pv = P.version(variant)
    rows = {}
    for line in open(p):
        if line.strip():
            r = json.loads(line)
            if r.get("prompt_version") == pv:
                rows[(r["t"], r["unit"], r["sample"])] = r       # last row per call wins (resume / retries)
    return list(rows.values())


def _clip(x, lo, hi):
    try:
        return float(min(hi, max(lo, float(x))))
    except (TypeError, ValueError):
        return np.nan


def handle_map(pop: dict) -> dict:
    """lowercased handle (with or without @ / ext:) -> agent id; agent ids map to themselves."""
    h = {}
    for a, name in pop.items():
        for k in (name, "@" + name, a):
            h[k.lower()] = a
    return h


def to_agent(name, hm):
    return hm.get(str(name).strip().lower().lstrip("@"), None)


def global_features(run_dir, variant, rows):
    pop = population(run_dir)
    hm = handle_map(pop)
    snap, nodes = defaultdict(list), defaultdict(lambda: defaultdict(list))
    n_ok = n_all = 0
    for r in rows:
        n_all += 1
        p = r.get("parsed") if r.get("ok") else None
        if not isinstance(p, dict):
            continue
        n_ok += 1
        viol = {to_agent(v, hm) for v in (p.get("violators") or [])} - {None}
        risk = {}
        for it in (p.get("at_risk") or [])[:10]:
            a = to_agent((it or {}).get("agent"), hm) if isinstance(it, dict) else None
            if a and a not in viol:
                risk[a] = max(risk.get(a, 0), _clip(it.get("p"), 0, 100))
        f = {"p_tip_3": _clip(p.get("p_tip_3"), 0, 100), "p_tip_end": _clip(p.get("p_tip_end"), 0, 100),
             "risk_level": _clip(p.get("risk_level"), 0, 100), "est_violators": _clip(p.get("est_violators"), 0, 24),
             "n_named_violators": float(len(viol)), "at_risk_max": max(risk.values(), default=0.0),
             "at_risk_sum": float(sum(risk.values())), "n_at_risk": float(len(risk))}
        snap[r["t"]].append((r["sample"], f))
        for a in pop:
            nodes[r["t"]][a].append((100.0 if a in viol else 0.0, risk.get(a, 0.0)))
    S, N = [], []
    eid = episode_id(run_dir)
    for t, lst in snap.items():
        lst.sort(key=lambda x: x[0])
        F = pd.DataFrame([f for _, f in lst])
        row = {"episode_id": eid, "t": t, **F.mean().to_dict(), "n_samples": len(lst),
               "p_tip_3_sd": float(F.p_tip_3.std(ddof=0)) if len(F) > 1 else 0.0, "p_tip_3_s0": F.p_tip_3.iloc[0]}
        S.append(row)
    for t, d in nodes.items():
        for a, lst in d.items():
            v = np.array(lst)
            N.append({"episode_id": eid, "t": t, "node_id": a, "p_violated": v[:, 0].mean() / 100,
                      "p_will": v[:, 1].mean() / 100})
    return S, N, (n_ok, n_all)


def unit_features(run_dir, variant, rows, R):
    """pairwise / agent: carry each unit's latest score forward for rounds [t, t+CARRY]."""
    pop = population(run_dir)
    hm = handle_map(pop)
    eid = episode_id(run_dir)
    per_unit = defaultdict(dict)          # unit -> t -> scores
    n_ok = n_all = 0
    for r in rows:
        n_all += 1
        p = r.get("parsed") if r.get("ok") else None
        if not isinstance(p, dict):
            continue
        n_ok += 1
        parties = r.get("parties") or []
        sc = {"suspicion": _clip(p.get("suspicion"), 0, 100), "agents": {}}
        if variant == "pairwise":
            for it in p.get("parties") or []:
                if not isinstance(it, dict):
                    continue
                a = to_agent(it.get("agent"), hm)
                if a is None:                      # externals or unmapped names: match by position in parties
                    nm = str(it.get("agent", "")).lower().replace("ext:", "")
                    a = next((x for x in parties if x.lower().replace("ext:", "") == nm), None)
                if a is None or a not in parties:
                    continue
                sc["agents"][a] = (_clip(it.get("p_violated"), 0, 100), _clip(it.get("p_will_violate_3"), 0, 100))
        else:
            sc["agents"][parties[0]] = (_clip(p.get("p_violated"), 0, 100), _clip(p.get("p_will_violate_3"), 0, 100))
        per_unit[r["unit"]][r["t"]] = sc
    S, N = [], []
    for t in range(1, R + 1):
        live = []
        for u, d in per_unit.items():
            ts = [x for x in d if t - CARRY <= x <= t]
            if ts:
                live.append(d[max(ts)])
        sus = sorted((s["suspicion"] for s in live if not np.isnan(s["suspicion"])), reverse=True)
        agent_v, agent_w = defaultdict(float), defaultdict(float)
        for s in live:
            for a, (pv, pw) in s["agents"].items():
                if a in pop:
                    agent_v[a] = max(agent_v[a], 0 if np.isnan(pv) else pv)
                    agent_w[a] = max(agent_w[a], 0 if np.isnan(pw) else pw)
        will = sorted(agent_w.values(), reverse=True)
        row = {"episode_id": eid, "t": t, "n_live_units": float(len(live)),
               "sus_max": sus[0] if sus else 0.0, "sus_top3": float(np.mean(sus[:3])) if sus else 0.0,
               "n_sus50": float(sum(x >= 50 for x in sus)),
               "n_flagged": float(sum(v >= 50 for v in agent_v.values())),
               "sum_p_violated": float(sum(agent_v.values()) / 100),
               "will_max": will[0] if will else 0.0, "will_top3": float(np.mean(will[:3])) if will else 0.0}
        S.append(row)
        for a in pop:
            N.append({"episode_id": eid, "t": t, "node_id": a, "p_violated": agent_v.get(a, 0.0) / 100,
                      "p_will": agent_w.get(a, 0.0) / 100})
    return S, N, (n_ok, n_all)


STACK_BASE = {"global": ["p_tip_3", "p_tip_end", "risk_level", "est_violators", "n_named_violators",
                         "at_risk_max", "at_risk_sum"],
              "unit": ["sus_max", "sus_top3", "n_sus50", "n_flagged", "sum_p_violated", "will_max", "will_top3",
                       "n_live_units"]}


def add_deltas(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.sort_values(["episode_id", "t"]).copy()
    g = df.groupby("episode_id")
    for c in cols:
        for lag in (1, 3):
            df[f"d{lag}_{c}"] = (df[c] - g[c].shift(lag)).fillna(0.0)
    return df


def variant_tables(base: pd.DataFrame, runs: list, variant: str, sfx: str = ""):
    S, N, stats = [], [], {"ok": 0, "all": 0, "refusals": 0}
    R_of = base.groupby("episode_id").R.first().to_dict()
    for d in runs:
        rows = read_rows(d, variant, sfx)
        if not rows:
            continue
        stats["refusals"] += sum(1 for r in rows if str(r.get("error", "")).startswith("refusal"))
        if variant in GLOBAL_VARIANTS:
            s, n, (ok, al) = global_features(d, variant, rows)
        else:
            s, n, (ok, al) = unit_features(d, variant, rows, R_of[episode_id(d)])
        S += s
        N += n
        stats["ok"] += ok
        stats["all"] += al
    if not S:
        return None, None, stats
    keys = base[["episode_id", "t", "group_id", "split"]]
    S = keys.merge(pd.DataFrame(S), on=["episode_id", "t"], how="left")
    kind = "global" if variant in GLOBAL_VARIANTS else "unit"
    scored = S.groupby("episode_id")[STACK_BASE[kind][0]].transform(lambda x: x.notna().any())
    S = add_deltas(S, STACK_BASE[kind])
    for c in [c for c in S.columns if c.startswith("d1_") or c.startswith("d3_")]:
        S.loc[~scored, c] = np.nan
    if kind == "global":
        S["zs_tip"], S["zs_count"] = S.p_tip_3 / 100, S.est_violators
        S["zs_tip_end"] = S.p_tip_end / 100
    else:
        S["zs_tip"] = S.sus_max / 100
        S["zs_count"] = S.n_flagged if variant == "pairwise" else S.sum_p_violated
        S["zs_tip_end"] = S.sus_max / 100
    return S.sort_values(["episode_id", "t"]).reset_index(drop=True), pd.DataFrame(N), stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", default=["sim_dataset/runs_night"])
    ap.add_argument("--out", default=None, help="default data/llm_monitor (data/llm_monitor_<tag> for other runs)")
    ap.add_argument("--variants", nargs="*", default=P.VARIANTS)
    ap.add_argument("--suffix", default="", help="file suffix of the monitor rows: '' (default), _dm, _fake")
    a = ap.parse_args(argv)
    out = a.out or OUT
    runs = find_runs(a.runs)
    base, nodes = base_frames(runs)
    os.makedirs(os.path.join(out, "_base"), exist_ok=True)
    base.to_csv(os.path.join(out, "_base", "snapshots.csv"), index=False)
    nodes.to_csv(os.path.join(out, "_base", "nodes.csv"), index=False)
    print(f"{len(runs)} runs, {len(base)} snapshots, tip rows {int(base.tip.notna().sum())}, "
          f"tip positives {int(base.tip.fillna(0).sum())}", flush=True)
    summary = {}
    for v in a.variants:
        S, N, st = variant_tables(base, runs, v, a.suffix)
        summary[v] = st
        if S is None:
            continue
        od = os.path.join(out, v + a.suffix)
        os.makedirs(od, exist_ok=True)
        S.to_csv(os.path.join(od, "snapshots.csv"), index=False, float_format="%.6g")
        N.to_csv(os.path.join(od, "nodes.csv"), index=False, float_format="%.6g")
        cov = S[STACK_BASE["global" if v in GLOBAL_VARIANTS else "unit"][0]].notna().mean()
        print(f"{v}: {st['ok']}/{st['all']} ok calls, refusals {st['refusals']}, snapshot coverage {cov:.3f}",
              flush=True)
    json.dump(summary, open(os.path.join(out, "_base", "parse_stats.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
