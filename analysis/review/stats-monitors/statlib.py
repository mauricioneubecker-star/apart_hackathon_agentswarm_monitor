"""Shared code for the monitor comparison: data alignment, exact cluster-bootstrap AUROC, p-values, Holm, DeLong.

Cluster bootstrap over configs, computed exactly without materialising resampled rows:
for a resample with config multiplicities k (k_c = how often config c was drawn), the AUROC of the
row-duplicated resample is

    AUROC(k) = k' M k / ((k' n1) (k' n0)),   M[c, c'] = sum_{i pos in c, j neg in c'} 1[s_i > s_j] + 0.5 1[s_i = s_j]

(n1, n0 = positives / negatives per config). This equals sklearn's roc_auc_score on the concatenated resample
(checked in check_bootstrap_equivalence). All predictors use the same draws K -> paired differences.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import roc_auc_score

T_BINS = (1, 6, 11, 16, 21, 26, 31)                       # harness metrics.time_matched_auroc
RTC_EDGES = [-99, -9, -5, -1, 3, 99]                       # llm_monitor.evaluate.slices (rounds-to-cut bins)
RTC_LABELS = ["<=-9", "-8..-5", "-4..-1", "0..3", ">3"]


# --------------------------------------------------------------------------------------------- data alignment
def load_rows(data_dir, base_csv):
    """Harness eval rows on night_train (eval == 1, y3 defined), plus slice columns from the llm_monitor _base."""
    S = pd.read_csv(os.path.join(data_dir, "snapshots.csv"), low_memory=False)
    lab = S[(S.split == "night_train") & (S["eval"] == 1) & S.y3.notna()].copy()
    B = pd.read_csv(base_csv, low_memory=False).rename(columns={"episode_id": "run", "t": "round"})
    lab = lab.merge(B[["run", "round", "tip", "rounds_to_cut", "before_announce", "mixed"]].rename(
        columns={"mixed": "mixed_base"}), on=["run", "round"], how="left")
    assert lab.tip.notna().all() and (lab.tip.values == lab.y3.values).all(), "label mismatch harness vs llm base"
    assert (lab.mixed.values == lab.mixed_base.values).all()
    lab = lab.reset_index(drop=True)
    lab["y"] = lab.y3.astype(int)
    cfgs = np.array(sorted(lab.cfg.unique()))
    lab["ci"] = pd.Categorical(lab.cfg, categories=cfgs).codes.astype(int)
    lab["rtc_bin"] = pd.cut(lab.rounds_to_cut, RTC_EDGES, labels=RTC_LABELS).astype(str)
    return S, lab, cfgs


def load_cv(path, lab, folds):
    """Read a harness CV file; return repeat-averaged ID OOF (aligned to lab), per-repeat ID scores, LODO dict,
    and a key check against the folds (every eval row once per ID repeat, each LODO test row once)."""
    P = pd.read_csv(path)
    key = lab[["run", "round"]].assign(row=np.arange(len(lab)))
    Pm = P.merge(key, on=["run", "round"], how="inner")
    chk = {"file_rows": int(len(P)), "rows_on_eval": int(len(Pm)), "nan_scores": int(Pm.score.isna().sum())}
    out = {"lodo": {}, "rep": {}}
    idm = Pm.fold.str.startswith("id")
    # repeat-averaged OOF over all id folds (harness.id_oof): mean per (run, round)
    oof = Pm[idm].groupby("row").score.mean()
    out["oof"] = oof.reindex(np.arange(len(lab))).values
    chk["oof_missing"] = int(np.isnan(out["oof"]).sum())
    reps = Pm[idm].fold.str.split("_").str[0]
    for r, g in Pm[idm].groupby(reps):
        s = g.groupby("row").score.mean().reindex(np.arange(len(lab))).values
        out["rep"][r] = s
        chk[f"{r}_missing"] = int(np.isnan(s).sum())
        chk[f"{r}_dupkeys"] = int(g.row.duplicated().sum())
    # fold-membership check: every fold present in the file must hold exactly the eval rows of its test configs
    bad, present = 0, []
    for kind in ("id", "lodo"):
        for name, fc in folds[kind].items():
            g = Pm[Pm.fold == name]
            if not len(g):
                continue                                   # fold absent (e.g. id0-only control files)
            present.append(name)
            exp = set(np.where(lab.cfg.isin(fc).values)[0])
            bad += int(set(g.row) != exp) + int(g.row.duplicated().sum())
            if kind == "lodo":
                out["lodo"][name] = (g.row.values, g.score.values)
    chk["fold_mismatch"] = bad
    chk["folds_present"] = len(present)
    chk["id_folds"] = sorted(Pm[idm].fold.unique().tolist())
    return out, chk


# --------------------------------------------------------------------------------------------- AUROC machinery
def pair_matrix(s, y, ci, n_cfg, mask=None):
    """M (n_cfg x n_cfg), n1, n0 for the rows in mask."""
    idx = np.arange(len(s)) if mask is None else np.where(mask)[0]
    ss, yy, cc = s[idx], y[idx], ci[idx]
    n1 = np.bincount(cc[yy == 1], minlength=n_cfg).astype(float)
    n0 = np.bincount(cc[yy == 0], minlength=n_cfg).astype(float)
    M = np.zeros((n_cfg, n_cfg))
    ps, pc = ss[yy == 1], cc[yy == 1]
    if len(ps) == 0:
        return M, n1, n0
    for c2 in np.where(n0 > 0)[0]:
        neg = np.sort(ss[(yy == 0) & (cc == c2)])
        lo = np.searchsorted(neg, ps, side="left")
        hi = np.searchsorted(neg, ps, side="right")
        M[:, c2] = np.bincount(pc, weights=lo + 0.5 * (hi - lo), minlength=n_cfg)
    return M, n1, n0


def auc_from(K, mats):
    M, n1, n0 = mats
    num = ((K @ M) * K).sum(1)
    W1, W0 = K @ n1, K @ n0
    with np.errstate(invalid="ignore", divide="ignore"):
        a = num / (W1 * W0)
    return a, W1, W0


class Stat:
    """Pre-computed pair matrices for one predictor's score vector on the lab rows."""

    def __init__(self, s, lab, n_cfg):
        y, ci = lab.y.values, lab.ci.values
        self.all = pair_matrix(s, y, ci, n_cfg)
        t = lab.t.values
        self.tb = [pair_matrix(s, y, ci, n_cfg, (t >= a) & (t < b)) for a, b in zip(T_BINS[:-1], T_BINS[1:])]
        rb = lab.rtc_bin.values
        self.rb = [pair_matrix(s, y, ci, n_cfg, rb == L) for L in RTC_LABELS]
        self.ba = pair_matrix(s, y, ci, n_cfg, lab.before_announce.values == 1)
        # within mixed config x rtc-bin strata (plan: "innerhalb gleicher Setups"), per config
        w = np.zeros(n_cfg)
        aw = np.zeros(n_cfg)
        mixed = lab.mixed.values == 1
        for (c, L), g in lab[mixed].groupby(["ci", "rtc_bin"]):
            yy, pp = g.y.values, s[g.index.values]
            npos, nneg = yy.sum(), (1 - yy).sum()
            if npos and nneg:
                ww = npos * nneg
                w[c] += ww
                aw[c] += ww * roc_auc_score(yy, pp)
        self.mx = (w, aw)

    def auroc(self, K):
        return auc_from(K, self.all)[0]

    def tauroc(self, K):
        """harness time_matched_auroc: round bins 1-5, 6-10, ..., weights = #positives in the bin."""
        num = den = 0.0
        for mats in self.tb:
            a, W1, W0 = auc_from(K, mats)
            ok = (W1 > 0) & (W0 > 0)
            w = np.where(ok, W1, 0.0)
            num = num + w * np.nan_to_num(a)
            den = den + w
        with np.errstate(invalid="ignore", divide="ignore"):
            return num / den

    def tauroc_rtc(self, K):
        """llm_monitor time-matched AUROC: rounds-to-cut bins, weights = #pos x #neg (pairs)."""
        num = den = 0.0
        for mats in self.rb:
            a, W1, W0 = auc_from(K, mats)
            w = np.where((W1 > 0) & (W0 > 0), W1 * W0, 0.0)
            num = num + w * np.nan_to_num(a)
            den = den + w
        with np.errstate(invalid="ignore", divide="ignore"):
            return num / den

    def before_ann(self, K):
        return auc_from(K, self.ba)[0]

    def mixed_cfg_time(self, K):
        w, aw = self.mx
        with np.errstate(invalid="ignore", divide="ignore"):
            return (K @ aw) / (K @ w)


def tauroc_rows(y, p, t):
    num = den = 0.0
    for a, b in zip(T_BINS[:-1], T_BINS[1:]):
        m = (t >= a) & (t < b)
        if m.sum() and len(np.unique(y[m])) == 2:
            w = y[m].sum()
            num += w * roc_auc_score(y[m], p[m])
            den += w
    return num / den if den else np.nan


def tauroc_rtc_rows(y, p, rb):
    num = den = 0.0
    for L in RTC_LABELS:
        m = rb == L
        npos, nneg = y[m].sum(), (1 - y[m]).sum()
        if npos and nneg:
            num += npos * nneg * roc_auc_score(y[m], p[m])
            den += npos * nneg
    return num / den if den else np.nan


def draws(n_cfg, B, seed):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_cfg, size=(B, n_cfg))
    K = np.zeros((B, n_cfg))
    np.add.at(K, (np.repeat(np.arange(B), n_cfg), idx.ravel()), 1.0)
    return K


# --------------------------------------------------------------------------------------------- inference helpers
def boot_p(d):
    """two-sided bootstrap p = 2 min(P(d <= 0), P(d >= 0)), floored at 1/B, capped at 1."""
    d = d[~np.isnan(d)]
    B = len(d)
    p = 2 * min((d <= 0).mean(), (d >= 0).mean())
    return float(min(1.0, max(p, 1.0 / B))), B


def holm(pvals):
    p = np.asarray(pvals, float)
    o = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * p[i]))
        adj[i] = run
    return adj


def delong_paired(y, a, b):
    """Row-level DeLong (Sun & Xu 2014) for AUROC(a) - AUROC(b), rows treated as independent."""
    from scipy.stats import rankdata
    y = np.asarray(y)
    X = np.vstack([a, b])
    pos, neg = X[:, y == 1], X[:, y == 0]
    m, n = pos.shape[1], neg.shape[1]
    tx = np.vstack([rankdata(r) for r in pos])
    ty = np.vstack([rankdata(r) for r in neg])
    tz = np.vstack([rankdata(r) for r in np.hstack([pos, neg])])
    auc = (tz[:, :m].sum(1) - m * (m + 1) / 2) / (m * n)
    v10 = (tz[:, :m] - tx) / n
    v01 = 1.0 - (tz[:, m:] - ty) / m
    S = np.cov(v10) / m + np.cov(v01) / n
    var = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    d = auc[0] - auc[1]
    se = float(np.sqrt(var))
    z = d / se
    return {"auc_a": float(auc[0]), "auc_b": float(auc[1]), "diff": float(d), "se": se,
            "ci": [float(d - 1.959964 * se), float(d + 1.959964 * se)], "p": float(2 * norm.sf(abs(z)))}


def fmt(x, nd=3):
    return "nan" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.{nd}f}"


def dump(obj, path):
    def conv(o):
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    json.dump(obj, open(path, "w"), indent=1, default=conv)
