"""Reference (non-LLM) baselines on the same rows and folds as the LLM monitors.

Feature definitions are a port of gnn_opt/tabular.py + data.py (branch gnn-opt @ f5803c2, itself a port of the team's
compare.py) reading graph_edges.csv / graph_nodes.csv directly:
  clock            t (round index) only
  pairwise         max / top-3 of the generic per-edge jury features + node maxima ("feature pairwise monitor")
  edge_monitor     per-edge HGB on single-edge generic features (label = snapshot label), max-pooled per snapshot
  bag              per-snapshot max/sum/mean/n>=2/top-3 of all generic edge features + node aggregates
                   (bag-of-edges: a tabular model, not a GNN)
  bag+graph        bag + hand-built 2-hop / spread aggregates and their 3-round deltas
  oracle           true violator count + clock (reference only, NOT observable)
Generic features only (no task lexicon, no tool events, no clock) except where named. HGB settings as gnn_opt.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

E_STRUCT = ["volume", "direct_volume", "bcast_volume", "responsiveness", "reciprocity", "new_contact"]
E_JURY = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
          "goal_shift", "unverified_authority", "secrecy", "frustration"]
E_DERIV = ["legitimization_trend", "jury_disagreement", "escalation_lex"]
E_GEN = E_STRUCT + E_JURY + E_DERIV
N_GEN = ["unanswered_share", "role_external", "bcast_legitimization", "stance_drift", "frustration_own"]
SEM_HI = ["rule_legitimization", "unverified_authority", "uncritical_adoption", "success_claim"]
PAIR_SEM = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
            "goal_shift", "unverified_authority", "secrecy", "frustration", "legitimization_trend"]
KEY = ["episode_id", "t"]


def load_graph(runs: list):
    from .common import episode_id
    E, V = [], []
    for d in runs:
        eid = episode_id(d)
        e = pd.read_csv(os.path.join(d, "graph_edges.csv")).rename(columns={"round": "t"})
        e.insert(0, "episode_id", eid)
        E.append(e)
        v = pd.read_csv(os.path.join(d, "graph_nodes.csv")).rename(columns={"round": "t"})
        v.insert(0, "episode_id", eid)
        V.append(v)
    return pd.concat(E, ignore_index=True), pd.concat(V, ignore_index=True)


def _top3(E, f):
    s = E[["episode_id", "t", f]].dropna().sort_values(f, ascending=False)
    return s.groupby(KEY).head(3).groupby(KEY)[f].mean()


def build_table(base: pd.DataFrame, runs: list) -> pd.DataFrame:
    """base: rows (episode_id, t). Returns the reference feature table aligned to base."""
    E, V = load_graph(runs)
    g = E.groupby(KEY)
    out = {}
    for f in E_GEN:
        out[f"max_{f}"] = g[f].max()
        out[f"sum_{f}"] = E[f].fillna(0).groupby([E.episode_id, E.t]).sum()
        out[f"mean_{f}"] = g[f].mean()
        out[f"n2_{f}"] = (E[f] >= 2).groupby([E.episode_id, E.t]).sum()
        out[f"top3_{f}"] = _top3(E, f)
    out["n_edges"] = g.size()
    gv = V.groupby(KEY)
    for f in N_GEN:
        out[f"nmax_{f}"] = gv[f].max()
        out[f"nmean_{f}"] = gv[f].mean()
        out[f"nn_{f}"] = (V[f] > (0 if f == "role_external" else 0.5)).groupby([V.episode_id, V.t]).sum()
    n_nodes = gv.size()
    # hand-built message passing (gnn_opt graph_aggs)
    for f in SEM_HI:
        hi = E[E[f] >= 2]
        gh = hi.groupby(KEY)
        out[f"g_{f}_receivers"] = gh.dst.nunique()
        out[f"g_{f}_senders"] = gh.src.nunique()
        per = hi.groupby(KEY + ["dst"]).src.nunique()
        out[f"g_{f}_max_srcs_per_node"] = per.groupby(level=[0, 1]).max()
        out[f"g_{f}_nodes_2plus_srcs"] = (per >= 2).groupby(level=[0, 1]).sum()
        out[f"g_{f}_receivers_who_send"] = gh.apply(lambda x: len(set(x.dst) & set(x.src)))
    hi = E[(E.rule_legitimization >= 2) | (E.unverified_authority >= 2)]
    out["g_legit_top_src_share"] = hi.groupby(KEY).apply(
        lambda x: x.groupby("src").dst.nunique().max() / max(1, x.dst.nunique()))
    out["g_active_nodes"] = g.apply(lambda x: len(set(x.src) | set(x.dst)))
    out["g_direct_edges"] = (E.direct_volume > 0).groupby([E.episode_id, E.t]).sum()
    T = pd.DataFrame(out)
    T = T.reindex(pd.MultiIndex.from_frame(base[KEY]))
    gcols = [c for c in T.columns if c.startswith("g_")]
    T[gcols] = T[gcols].fillna(0)
    nn = n_nodes.reindex(T.index).fillna(24).values
    T["g_density_direct"] = T.g_direct_edges / np.maximum(1, nn * (nn - 1))
    T = T.reset_index()
    agg_cols = [c for c in T.columns if c.split("_")[0] in ("max", "sum", "mean", "n2", "top3", "nmax", "nmean", "nn")]
    T[agg_cols + ["n_edges"]] = T[agg_cols + ["n_edges"]].fillna(0)
    run = T.episode_id
    for c in gcols + ["g_density_direct"]:
        T[f"d3_{c}"] = T[c] - T.groupby(run)[c].shift(3).fillna(0)
    return T


def feature_sets(cols) -> dict:
    bag = [c for c in cols if c.split("_")[0] in ("max", "sum", "mean", "n2", "top3", "nmax", "nmean", "nn")] + ["n_edges"]
    graph = [c for c in cols if c.startswith("g_") or c.startswith("d3_g_")]
    pairwise = [f"{a}_{f}" for f in PAIR_SEM for a in ("max", "top3")] + \
        ["nmax_bcast_legitimization", "nmax_stance_drift", "nmax_frustration_own"]
    return {"clock": ["t"], "pairwise": pairwise, "bag": bag, "bag+graph": list(dict.fromkeys(bag + graph)),
            "oracle": ["risk_count", "t"]}


def hgb(seed=0):
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_depth=3, max_iter=250, learning_rate=0.05, random_state=seed)


class EdgeMonitor:
    """Per-edge classifier on single-edge generic features; snapshot score = max over its edges (gnn_opt)."""

    def __init__(self, E: pd.DataFrame, seed=0):
        self.E, self.seed = E, seed

    def _edges(self, keys: pd.DataFrame):
        m = self.E.merge(keys.assign(_row=np.arange(len(keys))), on=KEY, how="inner")
        return np.nan_to_num(m[E_GEN].values, nan=-1.0), m["_row"].values

    def fit(self, keys, y):
        X, row = self._edges(keys)
        self.m = hgb(self.seed).fit(X, np.asarray(y)[row])
        has = np.zeros(len(keys), bool)
        has[row] = True
        self.empty = float(np.mean(np.asarray(y)[~has])) if (~has).any() else 0.0
        return self

    def predict(self, keys):
        X, row = self._edges(keys)
        p = self.m.predict_proba(X)[:, 1] if len(X) else np.zeros(0)
        out = np.full(len(keys), self.empty)
        s = pd.Series(p).groupby(row).max()
        out[s.index.values] = s.values
        return out
