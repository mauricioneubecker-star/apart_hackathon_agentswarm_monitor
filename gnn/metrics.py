"""Shared metrics for GNN and baselines."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def threshold_at_fpr(y_val, p_val, fpr=0.05):
    neg = np.asarray(p_val)[np.asarray(y_val) == 0]
    return float(np.quantile(neg, 1 - fpr)) if len(neg) else 0.5


def binary(y, p, thr=None) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = ~np.isnan(y)
    y, p = y[m], p[m]
    out = {"n": int(len(y)), "n_pos": int(y.sum()), "prevalence": float(y.mean()) if len(y) else float("nan")}
    if len(y) and 0 < y.sum() < len(y):
        out["auroc"] = float(roc_auc_score(y, p))
        out["auprc"] = float(average_precision_score(y, p))
        out["brier"] = float(brier_score_loss(y, p))
        if thr is not None:
            out["recall_at_5fpr"] = float((p[y == 1] >= thr).mean())
            out["fpr_at_thr"] = float((p[y == 0] >= thr).mean())
    return out


def count(y, p, scale=1.0) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = ~np.isnan(y)
    if not m.any():
        return {}
    return {"mae": float(np.abs(y[m] - p[m]).mean() * scale), "n": int(m.sum())}


def evaluate_preds(pg: pd.DataFrame, pn: pd.DataFrame, count_scale=1.0, strata=()) -> dict:
    """pg: per-snapshot frame [split, y_graph, p_graph, y_count, p_count, *strata]; pn: per-node [split, y, p].
    Thresholds for recall@5%FPR come from val."""
    res = {}
    thr_g = thr_n = None
    if pg is not None and "p_graph" in pg and (pg.split == "val").any():
        v = pg[(pg.split == "val") & pg.y_graph.notna()]
        thr_g = threshold_at_fpr(v.y_graph, v.p_graph) if len(v) else None
    if pn is not None and len(pn) and (pn.split == "val").any():
        v = pn[(pn.split == "val") & pn.y.notna()]
        thr_n = threshold_at_fpr(v.y, v.p) if len(v) else None
    splits = sorted(set(pg.split) if pg is not None else set()) or sorted(set(pn.split))
    for s in splits:
        r = {}
        if pg is not None and "p_graph" in pg:
            g = pg[pg.split == s]
            r["graph"] = binary(g.y_graph, g.p_graph, thr_g)
            for col in strata:
                if col in g:
                    r[f"graph_by_{col}"] = {str(k): binary(x.y_graph, x.p_graph, thr_g).get("auprc")
                                            for k, x in g.groupby(col)}
        if pg is not None and "p_count" in pg:
            g = pg[pg.split == s]
            r["count"] = count(g.y_count, g.p_count, count_scale)
        if pn is not None and len(pn):
            n = pn[pn.split == s]
            r["node"] = binary(n.y, n.p, thr_n)
            for col in strata:
                if col in n:
                    r[f"node_by_{col}"] = {str(k): binary(x.y, x.p, thr_n).get("auprc") for k, x in n.groupby(col)}
        res[s] = r
    return res


def get(metrics: dict, split: str, path: str, default=float("nan")):
    """get(m, 'val', 'graph.auprc')"""
    cur = metrics.get(split, {})
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur
