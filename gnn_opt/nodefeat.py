"""Per-agent (node-level) causal feature table + two-stage 'propagated' hybrid model.

Stage 1 (node model): per (agent, round) features -> P(agent has violated by t), P(agent violates within 3).
  Features: own outgoing messages in W(t) (max jury dims, volumes), incoming exposure in W(t) (max jury dims,
  #distinct high-score senders), own node features, causal memory over rounds <= t (running max, EMA, lag-3
  change) and 1-hop propagation (max/mean of neighbours' memory) -- all generic inputs, no clock.
Stage 2 (graph model): snapshot features = estimated violator count (sum of P_state), its lag-3 change, sum
  P_fut, exposure of likely non-violators to likely violators (edge-weighted), distribution stats; optionally
  concatenated with the bag+graph+mem table -> gradient boosting on tip within Delta.
Stage-1 predictions used to train stage 2 are out-of-fold (inner grouped CV by config), so stage 2 never sees
in-sample node probabilities.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

JURY = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
        "goal_shift", "unverified_authority", "secrecy", "frustration"]
MEM_DIMS = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "goal_shift",
            "unverified_authority", "frustration", "verification"]
LEX_E = ["mech_ref", "mech_ref_ema", "pressure_lex"]


def _dense_runs(S):
    """per run: snapshot ids in round order, node count (constant per run)."""
    out = []
    for run, g in S.groupby("run", sort=False):
        g = g.sort_values("t")
        out.append((run, g.snap.values, int(g.n_nodes.iloc[0]), int(g.n0.iloc[0])))
    return out


def ema_kernel(T, a):
    t = np.arange(T)
    K = np.where(t[:, None] >= t[None, :], a ** (t[:, None] - t[None, :]), 0.0)
    return K / K.sum(1, keepdims=True)


def build_node_table(G, S, lex=False, judge_ef=None, tool=False):
    """Returns DataFrame with one row per node row of graphs.npz (same order) + list of feature columns."""
    ec, nc = list(G["ecols"]), list(G["ncols"])
    EF = G["EF"] if judge_ef is None else judge_ef
    ES, ED = G["ES"], G["ED"]
    N = len(G["X"])
    dims = JURY + ["escalation_lex", "jury_disagreement", "legitimization_trend"] + (LEX_E if lex else [])
    E = pd.DataFrame(np.nan_to_num(EF[:, [ec.index(c) for c in dims]]), columns=dims)
    E["src"], E["dst"] = ES, ED
    E["direct"] = (EF[:, ec.index("direct_volume")] > 0).astype(float)
    E["vol"] = EF[:, ec.index("volume")]
    F = {}
    go = E.groupby("src")
    gi = E.groupby("dst")
    idx = np.arange(N)
    for d in dims:
        F[f"out_max_{d}"] = go[d].max().reindex(idx).fillna(0).values
        F[f"in_max_{d}"] = gi[d].max().reindex(idx).fillna(0).values
        F[f"in_mean_{d}"] = gi[d].mean().reindex(idx).fillna(0).values
    for d in ["rule_legitimization", "success_claim", "unverified_authority", "uncritical_adoption",
              "workaround_request"]:
        F[f"in_nsrc2_{d}"] = E[E[d] >= 2].groupby("dst").src.nunique().reindex(idx).fillna(0).values
        F[f"out_ndst2_{d}"] = E[E[d] >= 2].groupby("src").dst.nunique().reindex(idx).fillna(0).values
    F["out_deg"] = go.size().reindex(idx).fillna(0).values
    F["in_deg"] = gi.size().reindex(idx).fillna(0).values
    F["out_direct"] = go.direct.sum().reindex(idx).fillna(0).values
    F["in_direct"] = gi.direct.sum().reindex(idx).fillna(0).values
    F["out_vol"] = go.vol.max().reindex(idx).fillna(0).values
    for c in ["unanswered_share", "role_external", "bcast_legitimization", "stance_drift", "frustration_own"] + \
            (["bcast_mech_ref", "exposure_breadth"] if lex else []) + (["tests_failed", "escalated_unresolved"] if tool else []):
        v = G["X"][:, nc.index(c)]
        F[f"n_{c}"] = np.nan_to_num(v, nan=-1.0)
    F = pd.DataFrame(F)
    # causal memory per agent over rounds (dense per run: [T, n_nodes])
    mem_src = [f"out_max_{d}" for d in MEM_DIMS] + ["n_bcast_legitimization", "in_max_rule_legitimization",
                                                    "in_max_success_claim", "in_max_unverified_authority",
                                                    "out_deg"] + ([f"out_max_mech_ref", "n_bcast_mech_ref"] if lex else [])
    M = {f"cmax_{c}": np.zeros(N) for c in mem_src}
    M.update({f"ema_{c}": np.zeros(N) for c in mem_src})
    M.update({f"d3_{c}": np.zeros(N) for c in mem_src})
    M.update({f"cnt2_{c}": np.zeros(N) for c in mem_src[:8]})
    M["since_first_claim2"] = np.zeros(N)
    M["since_first_legit2"] = np.zeros(N)
    # neighbour memory propagation (1 hop, current window edges)
    for run, snaps, nn, n0 in _dense_runs(S):
        T = len(snaps)
        rows = (S.n0.values[snaps][:, None] + np.arange(nn)[None, :])        # [T, nn]
        K = ema_kernel(T, 0.7)
        for c in mem_src:
            x = F[c].values[rows]                                             # [T, nn]
            M[f"cmax_{c}"][rows] = np.maximum.accumulate(x, 0)
            M[f"ema_{c}"][rows] = K @ x
            lag = np.vstack([np.zeros((3, nn)), x[:-3]]) if T > 3 else np.zeros_like(x)
            M[f"d3_{c}"][rows] = x - lag
        for c in mem_src[:8]:
            x = F[c].values[rows]
            M[f"cnt2_{c}"][rows] = np.cumsum(x >= 2, 0)
        for key, c in [("since_first_claim2", "out_max_success_claim"), ("since_first_legit2", "out_max_rule_legitimization")]:
            x = F[c].values[rows] >= 2
            seen = np.maximum.accumulate(x, 0)
            first = np.where(seen.any(0), seen.argmax(0), T)
            tt = np.arange(T)[:, None]
            M[key][rows] = np.where(tt >= first[None, :], tt - first[None, :] + 1, 0)
    M = pd.DataFrame(M)
    NT = pd.concat([F, M], axis=1)
    # 1-hop: max / mean of in-neighbours' (senders') memory of claims / legitimisation
    for c in ["cmax_out_max_success_claim", "cmax_out_max_rule_legitimization", "ema_out_max_success_claim"]:
        v = pd.Series(NT[c].values[ES]).groupby(ED)
        NT[f"nb_in_max_{c}"] = v.max().reindex(idx).fillna(0).values
        NT[f"nb_in_mean_{c}"] = v.mean().reindex(idx).fillna(0).values
    NT["snap"] = G["node_snap"]
    NT["ext"] = G["node_ext"].astype(int)
    cols = [c for c in NT.columns if c not in ("snap", "ext")]
    return NT, cols


def hgb_node(seed=0):
    return HistGradientBoostingClassifier(max_depth=4, max_iter=200, learning_rate=0.06, min_samples_leaf=40,
                                          l2_regularization=1.0, random_state=seed)


def node_stage(NT, cols, node_lab, S, tr_snaps, pred_snaps, inner=4, seed=0):
    """Fit stage-1 node models on agents of tr_snaps; return P_state, P_fut for all node rows of
    (tr_snaps OOF via inner CV) and pred_snaps (full model)."""
    snap = NT.snap.values
    agent = NT.ext.values == 0
    cfg_of_snap = S.cfg.values
    ps = np.full(len(NT), np.nan)
    pf = np.full(len(NT), np.nan)
    tr_mask = np.isin(snap, tr_snaps) & agent
    pr_mask = np.isin(snap, pred_snaps) & agent
    X = NT[cols].values
    ys, yf = node_lab[:, 0], node_lab[:, 1]
    lab_ok = S["eval"].values[snap] >= 0                 # node labels defined on all rounds (state)
    groups = cfg_of_snap[snap]

    def fit2(m):
        a = m & ~np.isnan(ys) & lab_ok
        b = m & ~np.isnan(yf)
        return hgb_node(seed).fit(X[a], ys[a]), hgb_node(seed).fit(X[b], yf[b])

    tr_idx = np.flatnonzero(tr_mask)
    gkf = GroupKFold(inner)
    for a_i, b_i in gkf.split(tr_idx, groups=groups[tr_idx]):
        m = np.zeros(len(NT), bool); m[tr_idx[a_i]] = True
        ms, mf = fit2(m)
        ps[tr_idx[b_i]] = ms.predict_proba(X[tr_idx[b_i]])[:, 1]
        pf[tr_idx[b_i]] = mf.predict_proba(X[tr_idx[b_i]])[:, 1]
    ms, mf = fit2(tr_mask)
    only_pred = pr_mask & ~tr_mask
    if only_pred.any():
        ps[only_pred] = ms.predict_proba(X[only_pred])[:, 1]
        pf[only_pred] = mf.predict_proba(X[only_pred])[:, 1]
    return ps, pf, (ms, mf)


def graph_from_nodes(ps, pf, NT, G, S):
    """Snapshot features from node probabilities (+ edge-weighted exposure)."""
    snap = NT.snap.values
    ok = ~np.isnan(ps)
    d = pd.DataFrame({"snap": snap[ok], "ps": ps[ok], "pf": pf[ok]})
    g = d.groupby("snap")
    out = pd.DataFrame(index=S.snap.values)
    out["est_count"] = g.ps.sum()
    out["est_n50"] = (d.ps > 0.5).groupby(d.snap).sum()
    out["est_fut_sum"] = g.pf.sum()
    out["est_fut_max"] = g.pf.max()
    out["est_fut_top3"] = g.pf.apply(lambda v: np.sort(v.values)[-3:].sum())
    out["est_ps_entropy"] = (d.ps * (1 - d.ps)).groupby(d.snap).sum()
    # exposure: edges from likely violators to likely non-violators
    ES, ED = G["ES"], G["ED"]
    psf = np.nan_to_num(ps)
    w = psf[ES] * (1 - psf[ED])
    out["exp_v2nv"] = pd.Series(w).groupby(G["node_snap"][ES]).sum()
    rec = pd.Series(w).groupby(ED).sum()
    rr = pd.DataFrame({"snap": G["node_snap"][rec.index.values], "v": rec.values})
    out["exp_v2nv_n_recv"] = (rr.v > 0.5).groupby(rr.snap).sum()
    out = out.reindex(S.snap.values).fillna(0)
    run = S.run.values
    for c in ["est_count", "est_fut_sum", "est_n50"]:
        s = out[c]
        out[f"d3_{c}"] = s.values - s.groupby(run).shift(3).fillna(0).values
        out[f"d1_{c}"] = s.values - s.groupby(run).shift(1).fillna(0).values
    return out


def run_memory(v, S, alpha=0.7):
    """Causal per-agent running max and EMA of a node-row vector v (rows ordered as graphs.npz)."""
    cm, em = np.zeros(len(v)), np.zeros(len(v))
    for run, snaps, nn, n0 in _dense_runs(S):
        rows = S.n0.values[snaps][:, None] + np.arange(nn)[None, :]
        x = v[rows]
        cm[rows] = np.maximum.accumulate(x, 0)
        em[rows] = ema_kernel(len(snaps), alpha) @ x
    return cm, em


def neighbor_feats(ps, pf, G, S):
    """Iterative-classification features: what each agent read from / said to likely violators (stage-1 P_state)."""
    ec = list(G["ecols"])
    ES, ED = G["ES"], G["ED"]
    N = len(G["X"])
    idx = np.arange(N)
    p = np.nan_to_num(ps)
    q = np.nan_to_num(pf)
    leg = np.nan_to_num(G["EF"][:, ec.index("rule_legitimization")])
    suc = np.nan_to_num(G["EF"][:, ec.index("success_claim")])
    F = {}
    for name, w in [("in_ps", p[ES]), ("in_ps_leg", p[ES] * leg), ("in_ps_suc", p[ES] * suc), ("in_pf", q[ES])]:
        s = pd.Series(w).groupby(ED)
        F[f"nb_{name}_sum"] = s.sum().reindex(idx).fillna(0).values
        F[f"nb_{name}_max"] = s.max().reindex(idx).fillna(0).values
    s = pd.Series(p[ED]).groupby(ES)
    F["nb_out_ps_sum"] = s.sum().reindex(idx).fillna(0).values
    F["nb_n_in_likely"] = pd.Series((p[ES] > 0.5).astype(float)).groupby(ED).sum().reindex(idx).fillna(0).values
    for c in ["nb_in_ps_sum", "nb_in_ps_leg_sum", "nb_n_in_likely"]:
        cm, em = run_memory(F[c], S)
        F[f"cmax_{c}"], F[f"ema_{c}"] = cm, em
    F["self_ps"] = p
    F["self_pf"] = q
    cm, em = run_memory(p, S)
    F["self_ps_cmax"] = cm
    # snapshot context: estimated number of violators in the swarm (excluding self)
    snap = G["node_snap"]
    tot = pd.Series(p).groupby(snap).transform("sum").values
    F["ctx_est_count_others"] = tot - p
    return pd.DataFrame(F)


def node_stage_ica(NT, cols, node_lab, S, G, tr_snaps, pred_snaps, seed=0, rounds=1, return_models=False):
    ps, pf, mods = node_stage(NT, cols, node_lab, S, tr_snaps, pred_snaps, seed=seed)
    models = [mods]
    for _ in range(rounds):
        NB = neighbor_feats(ps, pf, G, S)
        NT2 = pd.concat([NT.reset_index(drop=True), NB], axis=1)
        ps, pf, mods = node_stage(NT2, cols + list(NB.columns), node_lab, S, tr_snaps, pred_snaps, seed=seed)
        models.append(mods)
    return (ps, pf, models) if return_models else (ps, pf)


def apply_node_models(models, NT, cols, G, S):
    """Apply trained stage-1 (+ICA) node models to a new dataset; externals get NaN."""
    agent = NT.ext.values == 0
    ps = np.full(len(NT), np.nan)
    pf = np.full(len(NT), np.nan)
    X = NT[cols].values
    ms, mf = models[0]
    ps[agent] = ms.predict_proba(X[agent])[:, 1]
    pf[agent] = mf.predict_proba(X[agent])[:, 1]
    for ms, mf in models[1:]:
        NB = neighbor_feats(ps, pf, G, S)
        X2 = np.concatenate([X, NB.values], 1)
        ps = np.full(len(NT), np.nan)
        pf = np.full(len(NT), np.nan)
        ps[agent] = ms.predict_proba(X2[agent])[:, 1]
        pf[agent] = mf.predict_proba(X2[agent])[:, 1]
    return ps, pf
