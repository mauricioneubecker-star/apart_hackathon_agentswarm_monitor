"""Load runs_* directories into flat numpy arrays (one graph snapshot per (run, round)).

Inputs per run: graph_edges.csv, graph_nodes.csv, labels.json [, branch.json]. Optional judge swap: graph_*_<judge>.csv
(built by gnn_opt/judge_swap.py). Split and hidden factors come from sim_dataset/dataset/index.csv (only used for
splitting / stratifying, never as model input).

Feature tiers (input rules, see RESULTS.md):
  GEN   generic, allowed in the headline model (structure + generic jury dims + escalation_lex + role_external)
  LEX   task lexicon (ablation only)
  TOOL  tool events (ablation only)
  clock (round index) is kept separately in `snap_t` and only used by ablation models.
Never loaded as features: role_lead, role_auditor, n_deps, n_dependents, contradiction (100 % NaN), config params.
"""
from __future__ import annotations

import glob
import json
import os
import pickle

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
INDEX = os.path.join(REPO, "sim_dataset", "dataset", "index.csv")
SCEN = os.path.join(REPO, "sim_dataset", "dataset", "scenarios", "core")

E_STRUCT = ["volume", "direct_volume", "bcast_volume", "responsiveness", "reciprocity", "new_contact"]
E_JURY = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
          "goal_shift", "unverified_authority", "secrecy", "frustration"]
E_DERIV = ["legitimization_trend", "jury_disagreement", "escalation_lex"]
E_GEN = E_STRUCT + E_JURY + E_DERIV
E_LEX = ["mech_ref", "mech_ref_ema", "pressure_lex"]
N_STRUCT = ["unanswered_share", "role_external"]
N_SEM = ["bcast_legitimization", "stance_drift", "frustration_own"]
N_GEN = N_STRUCT + N_SEM
N_LEX = ["bcast_mech_ref", "exposure_breadth"]
N_TOOL = ["tests_failed", "escalated_unresolved"]
NAN_FLAG = ["responsiveness", "reciprocity", "unanswered_share", "stance_drift", "frustration_own"]
# stage membership (FEATURES.md tiers) restricted to allowed generic features
STAGE = {"S0": E_STRUCT + ["unanswered_share", "role_external"],
         "S1": E_STRUCT + ["escalation_lex", "unanswered_share", "role_external"],
         "S2": E_STRUCT + ["escalation_lex", "success_claim", "workaround_request", "verification", "frustration",
                           "unanswered_share", "role_external", "frustration_own"],
         "S3": E_GEN + N_GEN}


def find_runs(runs_dirs):
    out = []
    for rd in runs_dirs:
        for d in sorted(glob.glob(os.path.join(rd, "*", "rep*"))):
            if all(os.path.exists(os.path.join(d, f)) for f in ("graph_edges.csv", "graph_nodes.csv", "labels.json")):
                out.append(d)
    return out


def factors_for(sid, idx):
    """Hidden factors (for CV splitting and stratification only)."""
    f = {"split": "unknown", "cat": "", "seed": "", "channels": "", "model_mix": "", "topology": ""}
    if idx is not None and sid in idx.index:
        m = idx.loc[sid]
        f.update({"split": str(m["split"]), "seed": str(m.get("seed_type", "")), "channels": str(m.get("channels", "")),
                  "model_mix": str(m.get("model_mix", "")), "topology": str(m.get("topology", ""))})
        c = str(m.get("category", ""))
        f["cat"] = "K2" if c.startswith("K2") else ("K4" if c.startswith("K4") else c)
    p = os.path.join(SCEN, f"{sid}.json")
    if (not f["cat"]) and os.path.exists(p):
        sc = json.load(open(p))
        f["cat"] = "K2" if sc["refs"]["category"].startswith("K2") else "K4"
    return f


def load_run(d, judge=None):
    sfx = f"_{judge}" if judge else ""
    fe = os.path.join(d, f"graph_edges{sfx}.csv")
    fn = os.path.join(d, f"graph_nodes{sfx}.csv")
    if judge and not os.path.exists(fe):
        alt = os.path.join(os.environ.get("GNN_OPT_CACHE", "/home/claude/cache"), "judge", judge,
                           os.path.basename(os.path.dirname(d)), os.path.basename(d))
        fe, fn = os.path.join(alt, "graph_edges.csv"), os.path.join(alt, "graph_nodes.csv")
    E = pd.read_csv(fe)
    V = pd.read_csv(fn)
    L = json.load(open(os.path.join(d, "labels.json")))
    br = json.load(open(os.path.join(d, "branch.json"))) if os.path.exists(os.path.join(d, "branch.json")) else None
    return E, V, L, br


def build(runs_dirs, judge=None, cache=None, deltas=(3, 5)):
    """Return dict of flat arrays. Snapshots ordered by (run, t); nodes contiguous per snapshot; edges sorted by
    (snapshot, dst)."""
    if cache and os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    idx = pd.read_csv(INDEX, low_memory=False).set_index("scenario_id") if os.path.exists(INDEX) else None
    ecols = E_GEN + E_LEX
    ncols = N_GEN + N_LEX + N_TOOL
    runs = find_runs(runs_dirs)
    R_meta, S, X, EF, ES, ED, NL, NAMES = [], [], [], [], [], [], [], []
    n_off = 0
    for ri, d in enumerate(runs):
        E, V, L, br = load_run(d, judge)
        sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
        f = factors_for(sid, idx)
        th, th_rel = L["theta_agents"], L.get("theta_rel") or L["theta_agents"]
        first = L["first_violation_round"]
        T = len(L["per_round"])
        cnt = np.array([sum(1 for r in first.values() if r <= t) for t in range(0, T + 1)])
        b0 = int(br["branch_round"]) if br else 0
        R_meta.append({"run": f"{sid}/{rep}", "cfg": sid, "rep": rep, "arm": (br or {}).get("arm", "control"),
                       "branch_round": b0, "branch_of": (br or {}).get("branch_of"), "tipped": int(bool(L["tipped"])),
                       "tip_round": L["tip_round"], "theta": th, "theta_rel": th_rel, "T": T, "path": d, **f})
        Eg = {t: g for t, g in E.groupby("round")}
        Vg = {t: g for t, g in V.groupby("round")}
        nodes_all = sorted(V.node.unique(), key=lambda n: (n.startswith("ext:"), n))
        for t in range(1, T + 1):
            v = Vg.get(t)
            if v is None:
                v = pd.DataFrame({"node": [n for n in nodes_all if not n.startswith("ext:")]})
            v = v.copy()
            # externals: only once they have appeared (sent something up to t)
            names = list(v.node)
            nid = {n: i for i, n in enumerate(names)}
            xv = np.zeros((len(names), len(ncols)), np.float32)
            for j, c in enumerate(ncols):
                if c in v:
                    xv[:, j] = v[c].values.astype(np.float32)
                else:
                    xv[:, j] = np.nan
            e = Eg.get(t)
            if e is not None and len(e):
                e = e[e.src.isin(nid) & e.dst.isin(nid)]
                s_i = e.src.map(nid).values
                d_i = e.dst.map(nid).values
                o = np.argsort(d_i, kind="stable")
                s_i, d_i = s_i[o], d_i[o]
                xe = np.stack([e[c].values.astype(np.float32) for c in ecols], 1)[o]
            else:
                s_i = d_i = np.zeros(0, int)
                xe = np.zeros((0, len(ecols)), np.float32)
            pr = L["per_round"][t - 1]
            lab = {"y3": (np.nan if pr["tip_within_delta"] is None else float(pr["tip_within_delta"])),
                   "risk": float(cnt[t])}
            for D in deltas:
                hi = min(T, t + D)
                lab[f"y{D}"] = float(np.any(cnt[t + 1:hi + 1] >= th)) if cnt[t] < th else np.nan
                lab[f"yrel{D}"] = float(np.any(cnt[t + 1:hi + 1] >= th_rel)) if cnt[t] < th_rel else np.nan
            S.append({"run_i": ri, "t": t, "n0": n_off, "n_nodes": len(names), "n_edges": len(s_i), "dup": int(t <= b0), **lab})
            X.append(xv)
            EF.append(xe)
            ES.append(s_i + n_off)
            ED.append(d_i + n_off)
            for n in names:
                fr = first.get(n)
                ext = n.startswith("ext:")
                viol_now = float(fr is not None and fr <= t)
                fut = np.nan if (ext or viol_now) else float(fr is not None and fr <= min(T, t + 3))
                NL.append((viol_now if not ext else np.nan, fut, ext))
            NAMES += names
            n_off += len(names)
    S = pd.DataFrame(S)
    out = {"runs": pd.DataFrame(R_meta), "snaps": S, "ecols": ecols, "ncols": ncols,
           "X": np.concatenate(X), "EF": np.concatenate(EF), "ES": np.concatenate(ES).astype(np.int64),
           "ED": np.concatenate(ED).astype(np.int64), "node_lab": np.array([x[:2] for x in NL], np.float32),
           "node_ext": np.array([x[2] for x in NL], bool)}
    out["node_name"] = np.array(NAMES, dtype=object)
    out["node_snap"] = np.repeat(np.arange(len(S)), S.n_nodes.values)
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        pickle.dump(out, open(cache, "wb"))
    return out


def prev_index(D):
    """For each node row, index of the same node in the previous snapshot of the same run (-1 if none)."""
    S = D["snaps"]
    prev = -np.ones(len(D["X"]), np.int64)
    last = {}
    for si, (ri, n0, nn) in enumerate(zip(S.run_i.values, S.n0.values, S.n_nodes.values)):
        for k in range(n0, n0 + nn):
            key = (ri, D["node_name"][k])
            prev[k] = last.get(key, -1)
            last[key] = k
    return prev
