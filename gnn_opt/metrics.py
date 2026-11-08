"""Metrics, strata, time-matched AUROC, bootstrap CIs over configs, CV fold definitions."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold


def auroc(y, p):
    y = np.asarray(y)
    return roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan


def auprc(y, p):
    y = np.asarray(y)
    return average_precision_score(y, p) if len(np.unique(y)) == 2 else np.nan


def thr_at_fpr(y, p, fpr=0.05):
    """Threshold such that FPR on (y, p) is <= fpr (computed on training-CV predictions)."""
    neg = np.sort(np.asarray(p)[np.asarray(y) == 0])
    if len(neg) == 0:
        return np.inf
    k = int(np.ceil((1 - fpr) * len(neg))) - 1
    return neg[min(max(k, 0), len(neg) - 1)] + 1e-12


def recall_at(y, p, thr):
    y = np.asarray(y); p = np.asarray(p)
    return float((p[y == 1] > thr).mean()) if (y == 1).any() else np.nan


def time_matched_auroc(y, p, t, bins=(1, 6, 11, 16, 21, 26, 31)):
    """Weighted mean of AUROC within bins of rounds elapsed (weights = #positives in bin)."""
    y, p, t = map(np.asarray, (y, p, t))
    num = den = 0.0
    for a, b in zip(bins[:-1], bins[1:]):
        m = (t >= a) & (t < b)
        if m.sum() and len(np.unique(y[m])) == 2:
            w = y[m].sum()
            num += w * roc_auc_score(y[m], p[m]); den += w
    return num / den if den else np.nan


def strata_masks(df, mixed_cfgs):
    return {"risk<=2": df.risk <= 2, "risk3-7": df.risk.between(3, 7), "mixed": df.cfg.isin(mixed_cfgs),
            "K2": df.cat == "K2", "K4": df.cat == "K4", "board": df.channels == "board",
            "team/dm": df.channels != "board",
            **{f"seed={s}": df.seed == s for s in sorted(df.seed.dropna().unique())}}


def full_report(df, p, thr=None, mixed_cfgs=(), count_pred=None, ycol="y"):
    """df needs columns y, risk, cfg, cat, channels, seed, t. Returns a flat dict."""
    y = df[ycol].values
    r = {"n": len(y), "pos": int(np.nansum(y)), "AUROC": auroc(y, p), "AUPRC": auprc(y, p),
         "Brier": float(np.mean((p - y) ** 2)), "tAUROC": time_matched_auroc(y, p, df.t.values)}
    if thr is not None:
        r["R@5%FPR"] = recall_at(y, p, thr)
        r["FPR@thr"] = float((p[y == 0] > thr).mean())
    if count_pred is not None:
        r["MAE_risk"] = float(np.mean(np.abs(count_pred - df.risk.values)))
    for k, m in strata_masks(df, mixed_cfgs).items():
        m = m.values
        r[k] = auroc(y[m], p[m]) if m.sum() else np.nan
    return r


def boot_ci(df, preds: dict, metric="AUROC", n=1000, seed=0, mask=None, pairs=()):
    """Bootstrap over configs. preds: name -> prediction array aligned with df. Returns {name: (lo, med, hi)} and
    pair differences."""
    rng = np.random.default_rng(seed)
    cfgs = df.cfg.unique()
    idx = {c: np.where(df.cfg.values == c)[0] for c in cfgs}
    y = df.y.values
    mk = np.ones(len(df), bool) if mask is None else np.asarray(mask)
    f = auroc if metric == "AUROC" else auprc
    vals = {k: [] for k in preds}
    dif = {f"{a}-{b}": [] for a, b in pairs}
    for _ in range(n):
        s = np.concatenate([idx[c] for c in rng.choice(cfgs, len(cfgs))])
        s = s[mk[s]]
        if len(np.unique(y[s])) < 2:
            continue
        cur = {k: f(y[s], v[s]) for k, v in preds.items()}
        for k in preds:
            vals[k].append(cur[k])
        for a, b in pairs:
            dif[f"{a}-{b}"].append(cur[a] - cur[b])
    q = lambda xs: tuple(np.quantile(xs, [0.025, 0.5, 0.975])) if xs else (np.nan,) * 3
    out = {k: q(v) for k, v in vals.items()}
    out.update({k: q(v) + (float(np.mean(np.array(v) > 0)),) for k, v in dif.items()})
    return out


# --------------------------------------------------------------------------------------------- CV fold definitions
LODO = [("hold_K2", "cat", ["K2"]), ("hold_K4", "cat", ["K4"]),
        ("hold_seed_external", "seed", ["external"]), ("hold_seed_pioneer", "seed", ["pioneer"]),
        ("hold_nonboard", "channels", ["team_channels", "dm_only"]),
        ("hold_mix_duo", "model_mix", ["duo"]), ("hold_mix_majority", "model_mix", ["majority"]),
        ("hold_topo_clustered", "topology", ["clustered"])]


def id_folds(runs_tr: pd.DataFrame, k=5, repeats=2, seed=0):
    """Grouped (by config) stratified (by tipped) k-fold on the training runs. Returns list of (name, test_cfgs)."""
    cfg = runs_tr.groupby("cfg").tipped.max()
    out = []
    for r in range(repeats):
        skf = StratifiedGroupKFold(k, shuffle=True, random_state=seed + r)
        for i, (_, te) in enumerate(skf.split(cfg.index, cfg.values, cfg.index)):
            out.append((f"id{r}_{i}", set(cfg.index[te])))
    return out


def lodo_folds(runs_tr: pd.DataFrame):
    out = []
    for name, col, levels in LODO:
        te = set(runs_tr[runs_tr[col].isin(levels)].cfg)
        if 0 < len(te) < runs_tr.cfg.nunique():
            out.append((name, te))
    return out


def selection_score(res):
    """res: dict with 'id_auroc' (pooled OOF over repeats, averaged), 'lodo' {fold: auroc}. Higher is better."""
    lod = np.array([v for v in res["lodo"].values() if v == v])
    return float(np.mean([res["id_auroc"], lod.mean(), lod.min()]))
