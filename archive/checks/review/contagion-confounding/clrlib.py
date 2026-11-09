"""Conditional (stratified) logistic regression, Breslow tie approximation, strata = (run, t, stuck) as in the MH
analysis, but confounders enter as covariates instead of extra strata (no loss of informative strata).
Small ridge on the nuisance covariates only. CI: cluster bootstrap over configs.
  python clr.py rows.pkl out.json [nboot]
"""
import json
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

df = None
NB = 300

def set_df(d):
    global df
    df = d
    df["ndm_bin"] = np.minimum(df.n_dm, 3)
    df["nsent_bin"] = np.minimum(df.n_sent_win, 2)


def design(d, expo, covs):
    X = [d[expo].to_numpy(float)[:, None]]
    names = [expo]
    for c in covs:
        if d[c].dtype == object or c in ("ndm_bin", "nsent_bin", "own_status", "subtype", "model", "persona", "role"):
            dm = pd.get_dummies(d[c].astype(str), prefix=c, drop_first=True, dtype=float)
            X.append(dm.to_numpy()); names += list(dm.columns)
        else:
            X.append(d[c].to_numpy(float)[:, None]); names.append(c)
    return np.hstack(X), names


def prep(d, keys):
    sid = d.groupby(keys, sort=False, observed=True).ngroup().to_numpy()
    ev = np.bincount(sid, weights=d.Y.to_numpy())
    keep = ev[sid] > 0
    return keep


def fit(X, y, sid, lam):
    S = sid.max() + 1
    d_s = np.bincount(sid, weights=y, minlength=S)
    pen = np.full(X.shape[1], lam); pen[0] = 0.0

    def f(b):
        eta = X @ b
        e = np.exp(eta - eta.max())
        den = np.bincount(sid, weights=e, minlength=S)
        num = np.vstack([np.bincount(sid, weights=e * X[:, j], minlength=S) for j in range(X.shape[1])]).T
        ll = (y * eta).sum() - (d_s * (np.log(den) + eta.max())).sum()
        g = (y[:, None] * X).sum(0) - (d_s[:, None] * num / den[:, None]).sum(0)
        return -(ll - 0.5 * (pen * b * b).sum()), -(g - pen * b)

    r = minimize(f, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B")
    return r.x


def run(expo, covs, keys=("run", "t", "stuck"), mask=None, nboot=NB, lam=0.5, seed=0):
    d = df if mask is None else df[mask]
    keys = list(keys)
    keep = prep(d, keys)
    d = d[keep].reset_index(drop=True)
    X, names = design(d, expo, covs)
    y = d.Y.to_numpy(float)
    sid = d.groupby(keys, sort=False, observed=True).ngroup().to_numpy()
    b = fit(X, y, sid, lam)
    cfgs = d.cfg.to_numpy()
    uc = np.unique(cfgs)
    rows_of = {c: np.flatnonzero(cfgs == c) for c in uc}
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        pick = rng.choice(uc, len(uc), replace=True)
        idx, sids, off = [], [], 0
        for k, c in enumerate(pick):
            ii = rows_of[c]
            idx.append(ii)
            s = sid[ii]
            _, inv = np.unique(s, return_inverse=True)
            sids.append(inv + off); off += inv.max() + 1
        idx = np.concatenate(idx); sids = np.concatenate(sids)
        bb = fit(X[idx], y[idx], sids, lam)
        bs.append(bb[0])
    bs = np.array(bs)
    return {"OR": float(np.exp(b[0])), "OR_ci": [float(np.exp(np.percentile(bs, 2.5))), float(np.exp(np.percentile(bs, 97.5)))],
            "p_boot_or_le_1": float(np.mean(bs <= 0)), "n_rows_in_event_strata": int(len(d)), "n_events": int(y.sum()),
            "n_exposed_events": int(((X[:, 0] == 1) & (y == 1)).sum()), "covariates": covs}


