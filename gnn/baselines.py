"""Structure-agnostic baselines on aggregated features (same feature selection as the GNN run).

logreg  K1: logistic regression on graph aggregates (graph target) / node + incident-edge aggregates (node target)
hgb     K2: histogram gradient boosting, same features (small grid, chosen on val)
lgbm    K2': LightGBM if installed
time    clock/size control: only time features (+ #nodes, #edges); must be clearly beaten
Count targets use Ridge regression on the same features.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

KEY = ["episode_id", "t"]


def _flat(df):
    df.columns = ["__".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in df.columns]
    return df


def graph_table(bundle, hop1=False):
    """Graph-level aggregates. hop1=True adds per-node in/out-edge aggregates (sum, max, degree), pooled per graph
    by max/mean - a structure-aware 1-hop baseline (sees e.g. 'some node has >= 2 risky senders')."""
    T = bundle.tables
    nodes, edges = T["nodes"], T["edges"]
    nc, ec = T["raw_node_cols"], T["raw_edge_cols"]
    parts = []
    if hop1 and len(edges):
        for side, col in (("in", "dst"), ("out", "src")):
            per = edges.groupby(KEY + [col])
            loc = _flat(per[ec].agg(["sum", "max"])) if ec else pd.DataFrame(index=per.size().index)
            loc[f"deg"] = per.size()
            parts.append(_flat(loc.groupby(level=[0, 1]).agg(["max", "mean"])).add_prefix(f"H1{side}_"))
    if nc:
        parts.append(_flat(nodes.groupby(KEY)[nc].agg(["mean", "max", "sum"])))
    if ec and len(edges):
        parts.append(_flat(edges.groupby(KEY)[ec].agg(["mean", "max", "sum"])).add_prefix("E_"))
    if len(edges):
        parts.append(edges.groupby(KEY + ["etype"]).size().unstack(fill_value=0).add_prefix("n_edges_"))
    X = pd.concat(parts, axis=1) if parts else pd.DataFrame(index=nodes.groupby(KEY).size().index)
    meta = bundle.meta.set_index(KEY)
    X = X.reindex(meta.index)
    ecount = [c for c in X.columns if c.startswith(("n_edges_", "E_", "H1"))]
    X[ecount] = X[ecount].fillna(0)
    for c in bundle.time_cols + ["n_nodes", "n_edges"]:
        X[f"time__{c}"] = meta[c].values
    return X.reset_index(drop=True)


def node_table(bundle):
    T = bundle.tables
    nodes, edges = T["nodes"], T["edges"]
    nc, ec = T["raw_node_cols"], T["raw_edge_cols"]
    X = nodes.set_index(KEY + ["node_id"])[nc].copy() if nc else nodes.set_index(KEY + ["node_id"])[[]].copy()
    if len(edges):
        for side, col in (("in", "dst"), ("out", "src")):
            e = edges.rename(columns={col: "node_id"})
            deg = e.groupby(KEY + ["node_id", "etype"]).size().unstack(fill_value=0).add_prefix(f"{side}_deg_")
            X = X.join(deg)
            if ec:
                agg = _flat(e.groupby(KEY + ["node_id"])[ec].agg(["sum", "max"])).add_prefix(f"{side}_")
                X = X.join(agg)
        fill = [c for c in X.columns if c.startswith(("in_", "out_"))]
        X[fill] = X[fill].fillna(0)
    G = graph_table(bundle)
    G.index = pd.MultiIndex.from_frame(bundle.meta[KEY])
    gcols = [c for c in G.columns if c.endswith("__mean") or c.startswith("time__") or c.startswith("n_edges_")]
    X = X.join(G[gcols].add_prefix("G_"), on=KEY)
    return X


def _fit_select(kind, Xtr, ytr, Xva, yva, seed, metric):
    kind = {"hgb1": "hgb", "logreg1": "logreg"}.get(kind, kind)
    if kind in ("logreg", "time"):
        grid = [dict(C=c) for c in (0.01, 0.1, 1.0)]
        mk = lambda p: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                     LogisticRegression(C=p["C"], max_iter=3000))
    elif kind == "lgbm":
        from lightgbm import LGBMClassifier
        grid = [dict(lr=lr, leaves=nl) for lr in (0.03, 0.1) for nl in (7, 15)]
        mk = lambda p: LGBMClassifier(n_estimators=300, learning_rate=p["lr"], num_leaves=p["leaves"],
                                      subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=seed,
                                      verbose=-1)
    else:
        grid = [dict(lr=lr, leaves=nl) for lr in (0.05, 0.1) for nl in (7, 15)]
        mk = lambda p: HistGradientBoostingClassifier(learning_rate=p["lr"], max_leaf_nodes=p["leaves"],
                                                      max_iter=300, early_stopping=True, random_state=seed)
    best, bm = -np.inf, None
    for p in grid:
        m = mk(p).fit(Xtr, ytr)
        if Xva is None or len(np.unique(yva)) < 2:
            return m
        pv = m.predict_proba(Xva)[:, 1]
        s = average_precision_score(yva, pv) if metric == "auprc" else roc_auc_score(yva, pv)
        if s > best:
            best, bm = s, m
    return bm


def _fit_count(Xtr, ytr, Xva, yva):
    best, bm = np.inf, None
    for a in (0.1, 1.0, 10.0):
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=a)).fit(Xtr, ytr)
        if Xva is None or not len(yva):
            return m
        s = np.abs(m.predict(Xva) - yva).mean()
        if s < best:
            best, bm = s, m
    return bm


def run_baseline(cfg, bundle):
    dc, meta = cfg.data, bundle.meta
    metric = "auprc" if cfg.select.endswith("auprc") else "auroc"
    G = pd.DataFrame({"sid": meta.index, "split": meta.split})
    for c in ("episode_id", "t", "group_id", *[s for s in cfg.strata if s in meta.columns]):
        G[c] = meta[c].values
    gl = bundle.tables["graph_labels"]
    idx = pd.MultiIndex.from_frame(meta[KEY])
    gmax = (bundle.schema.get("graph_labels", {}).get(dc.graph_count) or {}).get("max", 1) if dc.graph_count else 1
    G["y_graph"] = gl[dc.graph_target].reindex(idx).values.astype(float) if dc.graph_target else np.nan
    G["y_count"] = gl[dc.graph_count].reindex(idx).values.astype(float) / gmax if dc.graph_count else np.nan
    N = None
    if dc.graph_target or dc.graph_count:
        X = graph_table(bundle, hop1=cfg.model in ("hgb1", "logreg1"))
        if cfg.model == "time":
            X = X[[c for c in X.columns if c.startswith("time__")]]
        tr, va = (G.split == "train").values, (G.split == "val").values
        if dc.graph_target:
            m_tr, m_va = tr & G.y_graph.notna().values, va & G.y_graph.notna().values
            mdl = _fit_select(cfg.model, X[m_tr], G.y_graph[m_tr], X[m_va] if m_va.any() else None,
                              G.y_graph[m_va], cfg.seed, metric)
            G["p_graph"] = mdl.predict_proba(X)[:, 1]
        if dc.graph_count:
            m_tr, m_va = tr & G.y_count.notna().values, va & G.y_count.notna().values
            G["p_count"] = np.clip(_fit_count(X[m_tr], G.y_count[m_tr], X[m_va] if m_va.any() else None,
                                              G.y_count[m_va]).predict(X), 0, 1)
    if dc.node_target:
        Xn = node_table(bundle)
        nl = bundle.tables["node_labels"]
        y = nl[dc.node_target].reindex(Xn.index).values.astype(float)
        keys = Xn.index.to_frame(index=False)
        sid = pd.Series(meta.index, index=idx).reindex(pd.MultiIndex.from_frame(keys[KEY])).values
        split = meta.split.values[sid]
        if cfg.model == "time":
            Xn = Xn[[c for c in Xn.columns if c.startswith("G_time__")]]
        tr = (split == "train") & ~np.isnan(y)
        va = (split == "val") & ~np.isnan(y)
        mdl = _fit_select(cfg.model, Xn[tr], y[tr], Xn[va] if va.any() else None, y[va], cfg.seed, metric)
        N = pd.DataFrame({"sid": sid, "split": split, "y": y, "p": mdl.predict_proba(Xn)[:, 1]})
        for c in ("episode_id", "t", "group_id", *[s for s in cfg.strata if s in meta.columns]):
            N[c] = meta[c].values[sid]
        N["node_id"] = keys.node_id.values
    return G, N, {"n_features_graph": None}
