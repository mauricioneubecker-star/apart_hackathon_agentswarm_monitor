"""Per-snapshot tabular features for the baselines (same rows as the GNN).

Port of /home/claude/analysis/compare.py to the flat arrays of data.build(), plus causal per-agent memory features.
All features are computed from the snapshot at t (and t-3 for deltas, or rounds <= t for memory): causal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from data import E_GEN, E_JURY, E_LEX, E_STRUCT, N_GEN, N_LEX, N_TOOL

SEM_HI = ["rule_legitimization", "unverified_authority", "uncritical_adoption", "success_claim"]
PAIR_SEM = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
            "goal_shift", "unverified_authority", "secrecy", "frustration", "legitimization_trend"]


def edge_frame(D):
    E = pd.DataFrame(np.nan_to_num(D["EF"], nan=0.0) if False else D["EF"], columns=D["ecols"])
    snap_of_node = D["node_snap"]
    E["snap"] = snap_of_node[D["ES"]]
    E["src"] = D["ES"]
    E["dst"] = D["ED"]
    return E


def node_frame(D):
    V = pd.DataFrame(D["X"], columns=D["ncols"])
    V["snap"] = D["node_snap"]
    V["node"] = np.arange(len(V))
    return V


def _agg(E, cols, n_snap):
    g = E.groupby("snap")
    out = {}
    for f in cols:
        v = E[f]
        out[f"max_{f}"] = g[f].max()
        out[f"sum_{f}"] = v.fillna(0).groupby(E.snap).sum()
        out[f"mean_{f}"] = g[f].mean()
        out[f"n2_{f}"] = (v >= 2).groupby(E.snap).sum()
        out[f"top3_{f}"] = g[f].apply(lambda s: s.nlargest(3).mean())
    df = pd.DataFrame(out).reindex(range(n_snap))
    return df


def graph_aggs(E, D, n_snap, lex=False):
    """Hand-built message passing (compare.py graph_feats)."""
    rows = {}
    feats = SEM_HI + (["mech_ref"] if lex else [])
    for f in feats:
        hi = E[E[f] >= 2]
        g = hi.groupby("snap")
        rows[f"g_{f}_receivers"] = g.dst.nunique()
        rows[f"g_{f}_senders"] = g.src.nunique()
        per = hi.groupby(["snap", "dst"]).src.nunique()
        rows[f"g_{f}_max_srcs_per_node"] = per.groupby(level=0).max()
        rows[f"g_{f}_nodes_2plus_srcs"] = (per >= 2).groupby(level=0).sum()
        # receivers who also send high-f in the same snapshot
        rws = {}
        for s, gg in hi.groupby("snap"):
            rws[s] = len(set(gg.dst) & set(gg.src))
        rows[f"g_{f}_receivers_who_send"] = pd.Series(rws, dtype=float)
    hi = E[(E.rule_legitimization >= 2) | (E.unverified_authority >= 2)]
    top = {}
    for s, gg in hi.groupby("snap"):
        top[s] = gg.groupby("src").dst.nunique().max() / max(1, gg.dst.nunique())
    rows["g_legit_top_src_share"] = pd.Series(top, dtype=float)
    act = {}
    for s, gg in E.groupby("snap"):
        act[s] = len(set(gg.src) | set(gg.dst))
    rows["g_active_nodes"] = pd.Series(act, dtype=float)
    rows["g_direct_edges"] = (E.direct_volume > 0).groupby(E.snap).sum()
    df = pd.DataFrame(rows).reindex(range(n_snap)).fillna(0)
    n_ag = D["snaps"].n_nodes.values - 0
    df["g_density_direct"] = df.g_direct_edges / np.maximum(1, n_ag * (n_ag - 1))
    return df


def memory_feats(D, E, V):
    """Causal per-agent memory: an agent's own max outgoing jury score in any snapshot <= t (ever), and an
    EMA; counted over agents. These approximate 'how many agents have ever claimed/legitimized' without any label."""
    S = D["snaps"]
    names = D["node_name"]
    run_of_snap = S.run_i.values
    t_of_snap = S.t.values
    feats = ["success_claim", "rule_legitimization", "uncritical_adoption", "workaround_request", "goal_shift",
             "unverified_authority", "frustration"]
    # per (snap, src) max outgoing
    out = E.groupby(["snap", "src"])[feats].max().reset_index()
    out["run"] = run_of_snap[out.snap.values]
    out["t"] = t_of_snap[out.snap.values]
    out["name"] = names[out.src.values]
    res = []
    for ri, g in out.groupby("run"):
        snaps = S.index[S.run_i == ri].values
        ts = t_of_snap[snaps]
        piv = {f: g.pivot_table(index="t", columns="name", values=f, aggfunc="max").reindex(ts).fillna(0) for f in feats}
        r = pd.DataFrame(index=snaps)
        for f in feats:
            p = piv[f]
            ever = p.cummax()
            ema = p.ewm(alpha=0.3, adjust=False).mean()
            r[f"mem_n_ever2_{f}"] = (ever >= 2).sum(1).values
            r[f"mem_n_ever3_{f}"] = (ever >= 3).sum(1).values
            r[f"mem_ema_sum_{f}"] = ema.sum(1).values
            r[f"mem_ema_max_{f}"] = ema.max(1).values
            r[f"mem_n_new2_{f}"] = ((ever >= 2).astype(int) - (ever >= 2).astype(int).shift(3).fillna(0)).sum(1).values
        res.append(r)
    M = pd.concat(res).reindex(range(len(S))).fillna(0)
    return M


def build_table(D, lex=False, tool=False, memory=True):
    n_snap = len(D["snaps"])
    E = edge_frame(D)
    V = node_frame(D)
    ecols = E_GEN + (E_LEX if lex else [])
    A = _agg(E, ecols, n_snap)
    A["n_edges"] = D["snaps"].n_edges.values
    ncols = N_GEN + (N_LEX if lex else []) + (N_TOOL if tool else [])
    g = V.groupby("snap")
    nd = {}
    for f in ncols:
        nd[f"nmax_{f}"] = g[f].max()
        nd[f"nmean_{f}"] = g[f].mean()
        nd[f"nn_{f}"] = (V[f] > (0 if f == "role_external" else 0.5)).groupby(V.snap).sum()
    A = pd.concat([A, pd.DataFrame(nd).reindex(range(n_snap))], axis=1)
    G = graph_aggs(E, D, n_snap, lex=lex)
    run = D["snaps"].run_i
    for c in list(G.columns):
        G[f"d3_{c}"] = G[c] - G.groupby(run)[c].shift(3).fillna(0)
    T = pd.concat([A.fillna(0), G], axis=1)
    if memory:
        T = pd.concat([T, memory_feats(D, E, V)], axis=1)
    T["t"] = D["snaps"].t.values
    return T


def feature_sets(cols):
    task = ["mech_ref", "mech_ref_ema", "pressure_lex", "bcast_mech_ref", "exposure_breadth"]
    def has_task(c):
        return any(k in c for k in task)
    struct = ["n_edges", "g_active_nodes", "g_direct_edges", "g_density_direct"] + \
        [f"{a}_{f}" for f in E_STRUCT for a in ("sum", "max", "mean")] + ["nmean_unanswered_share", "nn_role_external"]
    pairwise = [f"{a}_{f}" for f in PAIR_SEM for a in ("max", "top3")] + \
        ["nmax_bcast_legitimization", "nmax_stance_drift", "nmax_frustration_own"]
    bag = [c for c in cols if c.split("_")[0] in ("max", "sum", "mean", "n2", "top3", "nmax", "nmean", "nn")
           and not has_task(c) and "tests_failed" not in c and "escalated" not in c] + ["n_edges"]
    graph = [c for c in cols if (c.startswith("g_") or c.startswith("d3_g_")) and not has_task(c)]
    mem = [c for c in cols if c.startswith("mem_")]
    task_all = [c for c in cols if has_task(c)]
    tool = [c for c in cols if "tests_failed" in c or "escalated" in c]
    u = lambda *xs: list(dict.fromkeys([c for x in xs for c in x]))
    return {"clock": ["t"], "struct": struct, "pairwise": pairwise, "bag": bag, "bag+graph": u(bag, graph),
            "bag+graph+mem": u(bag, graph, mem), "bag+graph+clock": u(bag, graph, ["t"]),
            "bag+graph+lex": u(bag, graph, task_all), "bag+graph+mem+lex": u(bag, graph, mem, task_all),
            "bag+graph+mem+clock": u(bag, graph, mem, ["t"]), "bag+graph+mem+tool": u(bag, graph, mem, tool)}
