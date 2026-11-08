"""Independent verification library (written from scratch; does not import the other analyst's code).

Exact weighted AUROC via score levels: for config multiplicities K (B x C), the AUROC of the row-duplicated
resample is sum_l P_l (Nbelow_l + 0.5 N_l) / (sum P)(sum N), with P = K @ Npos, N = K @ Nneg (per score level l).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

ST = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat"
V = ST + "/verify-monitors"
GIT = V + "/preds_git"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
FOLDS = ST + "/repo/gnn_opt/folds.json"


def load_rows():
    S = pd.read_csv(ST + "/data/night/snapshots.csv", low_memory=False)
    lab = S[(S.split == "night_train") & (S["eval"] == 1) & S.y3.notna()].copy().reset_index(drop=True)
    base = pd.read_csv(LLM + "/_base/snapshots.csv", low_memory=False)
    base = base.rename(columns={"episode_id": "run", "t": "round"})
    lab = lab.merge(base[["run", "round", "tip", "rounds_to_cut", "cut", "group_id"]], on=["run", "round"],
                    how="left", validate="one_to_one")
    lab["y"] = lab.y3.astype(int)
    cfgs = np.array(sorted(lab.cfg.unique()))
    lab["c"] = pd.Categorical(lab.cfg, categories=cfgs).codes
    return S, lab, cfgs


def mw_auc(y, s):
    """Mann-Whitney AUROC with midranks (own implementation)."""
    y = np.asarray(y).astype(int); s = np.asarray(s, float)
    r = rankdata(s)
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def zs_scores(variant, lab):
    Z = pd.read_csv(f"{LLM}/{variant}/snapshots.csv", low_memory=False)
    Z = Z.rename(columns={"episode_id": "run", "t": "round"})[["run", "round", "zs_tip"]]
    m = lab[["run", "round"]].merge(Z, on=["run", "round"], how="left", validate="one_to_one")
    return m.zs_tip.values.astype(float)


def cv_scores(path, lab):
    """Returns repeat-averaged ID OOF, per-repeat dict, LODO dict {fold: (row_idx, score)} aligned to lab."""
    P = pd.read_csv(path)
    key = lab[["run", "round"]].copy(); key["row"] = np.arange(len(lab))
    P = P.merge(key, on=["run", "round"], how="inner")
    out = {"rep": {}, "lodo": {}}
    idm = P.fold.str.startswith("id")
    oof = np.full(len(lab), np.nan)
    g = P[idm].groupby("row").score.mean()
    oof[g.index.values] = g.values
    out["oof"] = oof
    for r in sorted(set(P[idm].fold.str[:3])):
        q = P[P.fold.str.startswith(r + "_")]
        assert not q.row.duplicated().any()
        v = np.full(len(lab), np.nan); v[q.row.values] = q.score.values
        out["rep"][r] = v
    for f, q in P[~idm].groupby("fold"):
        out["lodo"][f] = (q.row.values, q.score.values)
    return out


def levels(s, y, c, nC, mask=None):
    idx = np.arange(len(s)) if mask is None else np.where(mask)[0]
    ss, yy, cc = s[idx], y[idx], c[idx]
    u, inv = np.unique(ss, return_inverse=True)
    Np = np.zeros((nC, len(u))); Nn = np.zeros((nC, len(u)))
    np.add.at(Np, (cc[yy == 1], inv[yy == 1]), 1.0)
    np.add.at(Nn, (cc[yy == 0], inv[yy == 0]), 1.0)
    return Np, Nn


def wauc_parts(K, lv, chunk=500):
    """num (concordant weight), Wp, Wn for each row of K."""
    Np, Nn = lv
    B = K.shape[0]
    num = np.empty(B); Wp = np.empty(B); Wn = np.empty(B)
    for a in range(0, B, chunk):
        k = K[a:a + chunk]
        P = k @ Np; N = k @ Nn
        below = np.cumsum(N, axis=1) - N
        num[a:a + chunk] = (P * (below + 0.5 * N)).sum(1)
        Wp[a:a + chunk] = P.sum(1); Wn[a:a + chunk] = N.sum(1)
    return num, Wp, Wn


class Pred:
    def __init__(self, s, lab, nC):
        y, c, t = lab.y.values, lab.c.values, lab.t.values
        assert not np.isnan(s).any()
        self.lv_all = levels(s, y, c, nC)
        self.lv_t = [levels(s, y, c, nC, (t >= a) & (t <= a + 4)) for a in (1, 6, 11, 16, 21, 26)]
        rtc = lab.rounds_to_cut.values
        edges = [(-99, -9), (-9, -5), (-5, -1), (-1, 3), (3, 99)]          # (lo, hi] like pd.cut
        self.lv_r = [levels(s, y, c, nC, (rtc > lo) & (rtc <= hi)) for lo, hi in edges]

    def auroc(self, K):
        n, p, q = wauc_parts(K, self.lv_all)
        return n / (p * q)

    def tauroc(self, K):
        """round bins 1-5,...,26-30, weight = (weighted) #positives in bin; bins need both classes."""
        num = np.zeros(K.shape[0]); den = np.zeros(K.shape[0])
        for lv in self.lv_t:
            n, p, q = wauc_parts(K, lv)
            ok = (p > 0) & (q > 0)
            a = np.where(ok, n / np.where(ok, p * q, 1), 0.0)
            num += np.where(ok, p, 0) * a; den += np.where(ok, p, 0)
        return num / den

    def tauroc_rtc(self, K):
        """rounds-to-cut bins, pairs-weighted = total within-bin concordance / total within-bin pairs."""
        num = np.zeros(K.shape[0]); den = np.zeros(K.shape[0])
        for lv in self.lv_r:
            n, p, q = wauc_parts(K, lv)
            num += n; den += p * q
        return num / den


def draws(nC, B, seed):
    rng = np.random.default_rng(seed)
    K = np.zeros((B, nC))
    for b in range(B):
        K[b] = np.bincount(rng.choice(nC, nC, replace=True), minlength=nC)
    return K


def pboot(d):
    d = d[np.isfinite(d)]
    B = len(d)
    p = 2 * min(np.mean(d <= 0), np.mean(d >= 0))
    return min(1.0, max(p, 1.0 / B))


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p, kind="stable")
    adj = np.empty(m); cur = 0.0
    for j, i in enumerate(o):
        cur = max(cur, min(1.0, (m - j) * p[i])); adj[i] = cur
    return adj


def delong(y, a, b):
    """Paired DeLong test with placement values (own implementation; rows independent)."""
    y = np.asarray(y).astype(int)
    out = []
    V10, V01 = [], []
    for s in (a, b):
        s = np.asarray(s, float)
        pos, neg = s[y == 1], s[y == 0]
        m, n = len(pos), len(neg)
        # placement values: for each positive, share of negatives below (ties 0.5)
        negs = np.sort(neg); poss = np.sort(pos)
        v10 = (np.searchsorted(negs, pos, "left") + 0.5 * (np.searchsorted(negs, pos, "right") - np.searchsorted(negs, pos, "left"))) / n
        # v01 = share of positives above each negative (ties 0.5)
        v01 = ((m - np.searchsorted(poss, neg, "right")) + 0.5 * (np.searchsorted(poss, neg, "right") - np.searchsorted(poss, neg, "left"))) / m
        out.append(v10.mean()); V10.append(v10); V01.append(v01)
    m, n = len(V10[0]), len(V01[0])
    S10 = np.cov(np.vstack(V10)); S01 = np.cov(np.vstack(V01))
    var = (S10[0, 0] + S10[1, 1] - 2 * S10[0, 1]) / m + (S01[0, 0] + S01[1, 1] - 2 * S01[0, 1]) / n
    d = out[0] - out[1]; se = np.sqrt(var)
    return {"auc_a": out[0], "auc_b": out[1], "d": d, "se": se, "p": 2 * norm.sf(abs(d / se))}
