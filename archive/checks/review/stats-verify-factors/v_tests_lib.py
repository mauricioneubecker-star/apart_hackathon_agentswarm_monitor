"""Independent re-computation of the marginal factor tests (config level).
Own implementation: vectorised within-block permutations, own seeds, own Holm, own stratified bootstrap."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-12
B_PERM = int(os.environ.get("B_PERM", 50000))
B_BOOT = int(os.environ.get("B_BOOT", 10000))


def perm_labels(codes, blocks, B, rng):
    """(B, n) matrix of codes permuted independently within each block."""
    n = len(codes)
    out = np.empty((B, n), dtype=np.int16)
    for b in np.unique(blocks):
        ib = np.where(blocks == b)[0]
        pr = np.argsort(rng.random((B, len(ib))), axis=1)
        out[:, ib] = codes[ib][pr]
    return out


def stat_binary(y, L):
    """L: (..., n) 0/1 codes; returns mean(y|1) - mean(y|0)."""
    L = np.asarray(L, dtype=float)
    n1 = L.sum(axis=-1)
    s1 = L @ y
    return s1 / n1 - (y.sum() - s1) / (len(y) - n1)


def stat_between(y, L, k):
    """n-weighted between-level sum of squares; L codes 0..k-1."""
    L = np.asarray(L)
    tot = 0.0
    S = y.sum()
    N = len(y)
    for g in range(k):
        ind = (L == g).astype(float)
        ng = ind.sum(axis=-1)
        sg = ind @ y
        tot = tot + sg ** 2 / ng
    return tot - S ** 2 / N


def perm_test(y, codes, blocks, k, B, seed, chunk=20000):
    rng = np.random.default_rng(seed)
    if k == 2:
        t0 = stat_binary(y, codes)
    else:
        t0 = stat_between(y, codes, k)
    cnt = 0
    done = 0
    while done < B:
        b = min(chunk, B - done)
        P = perm_labels(codes, blocks, b, rng)
        if k == 2:
            t = stat_binary(y, P)
            cnt += int(np.sum(np.abs(t) >= abs(t0) - EPS))
        else:
            t = stat_between(y, P, k)
            cnt += int(np.sum(t >= t0 - EPS))
        done += b
    return float(t0), (1 + cnt) / (B + 1)


def boot_diff(y, codes, blocks, lv, ref, B, seed):
    """stratified (by block) config bootstrap of mean(y|lv) - mean(y|ref); percentile CI."""
    rng = np.random.default_rng(seed)
    ub = np.unique(blocks)
    idx_by = [np.where(blocks == b)[0] for b in ub]
    res = np.empty(B)
    for r in range(B):
        ii = np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])
        c = codes[ii]
        yy = y[ii]
        a = yy[c == lv]
        bb = yy[c == ref]
        res[r] = (a.mean() - bb.mean()) if (len(a) and len(bb)) else np.nan
    res = res[~np.isnan(res)]
    return np.percentile(res, [2.5, 97.5]), len(res)


def boot_rate(y, codes, blocks, lv, B, seed):
    rng = np.random.default_rng(seed)
    ub = np.unique(blocks)
    idx_by = [np.where(blocks == b)[0] for b in ub]
    res = np.empty(B)
    for r in range(B):
        ii = np.concatenate([ib[rng.integers(0, len(ib), len(ib))] for ib in idx_by])
        a = y[ii][codes[ii] == lv]
        res[r] = a.mean() if len(a) else np.nan
    res = res[~np.isnan(res)]
    return np.percentile(res, [2.5, 97.5])


def holm(pd_):
    names = list(pd_)
    ps = np.array([pd_[k] for k in names])
    order = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * ps[i])
        adj[i] = min(1.0, run)
    return dict(zip(names, adj))


