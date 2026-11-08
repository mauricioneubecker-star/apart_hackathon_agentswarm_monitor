"""MH helpers identical to analysis/contagion.py (mh + summarize), plus a cluster-robust MH score test."""
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(w=3):
    z = np.load(os.path.join(HERE, "data", f"rows_w{w}.npz"), allow_pickle=False)
    A, cols = z["A"], list(z["cols"])
    D = {c: A[:, i] for i, c in enumerate(cols)}
    D["cfg"], D["run"], D["agent"] = z["cfg"], z["run"], z["agent"]
    return D


def strata_keys(D):
    return np.array([f"{a}|{int(b)}|{int(c)}" for a, b, c in zip(D["run"], D["t"], D["stuck"])])


def mh_acc(D, mask, x, keys=None, y=None):
    """Per-config MH numerators/denominators within strata (run, t, stuck) -- same as contagion.py mh()."""
    keys = strata_keys(D) if keys is None else keys
    Y = D["Y"] if y is None else y
    k, yy, e, cg = keys[mask], Y[mask], x[mask], D["cfg"][mask]
    order = np.argsort(k, kind="stable")
    k, yy, e, cg = k[order], yy[order], e[order], cg[order]
    bounds = np.flatnonzero(np.r_[True, k[1:] != k[:-1], True])
    acc = defaultdict(lambda: np.zeros(9))  # or_num, or_den, rr_num, rr_den, a, strata, O-E, var_hyp, n_exposed
    for i in range(len(bounds) - 1):
        s = slice(bounds[i], bounds[i + 1])
        ys, es = yy[s], e[s]
        n = len(ys)
        a_ = np.sum((es == 1) & (ys == 1)); b_ = np.sum((es == 1) & (ys == 0))
        c_ = np.sum((es == 0) & (ys == 1)); d_ = np.sum((es == 0) & (ys == 0))
        if (a_ + b_) == 0 or (c_ + d_) == 0 or (a_ + c_) == 0:
            continue
        m1, n1 = a_ + c_, a_ + b_
        exp_a = n1 * m1 / n
        var = n1 * (n - n1) * m1 * (n - m1) / (n * n * (n - 1)) if n > 1 else 0.0
        v = acc[cg[s][0]]
        v += [a_ * d_ / n, b_ * c_ / n, a_ * (c_ + d_) / n, c_ * (a_ + b_) / n, a_, 1, a_ - exp_a, var, n1]
    return acc


def summarize(acc, nboot=2000, seed=0):
    rng = np.random.default_rng(seed)
    cf = list(acc)
    M = np.array([acc[c] for c in cf])
    if len(M) == 0 or M[:, 1].sum() == 0:
        return None
    o = M[:, 0].sum() / M[:, 1].sum()
    r = M[:, 2].sum() / M[:, 3].sum()
    bo, brr = [], []
    for _ in range(nboot):
        Wm = M[rng.integers(0, len(M), len(M))]
        if Wm[:, 1].sum() > 0 and Wm[:, 3].sum() > 0:
            bo.append(Wm[:, 0].sum() / Wm[:, 1].sum()); brr.append(Wm[:, 2].sum() / Wm[:, 3].sum())
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    U = M[:, 6]
    z_cmh = U.sum() / np.sqrt(M[:, 7].sum()) if M[:, 7].sum() > 0 else np.nan
    z_rob = U.sum() / np.sqrt((U ** 2).sum()) if (U ** 2).sum() > 0 else np.nan  # cluster(config)-robust score
    from scipy.stats import norm
    return {"OR": float(o), "OR_ci": q(bo), "RR": float(r), "RR_ci": q(brr), "configs": len(cf),
            "strata": int(M[:, 5].sum()), "exp_adopt": int(M[:, 4].sum()), "O_minus_E": float(U.sum()),
            "z_cmh": float(z_cmh), "p_cmh": float(2 * norm.sf(abs(z_cmh))), "z_cluster": float(z_rob),
            "p_cluster": float(2 * norm.sf(abs(z_rob)))}


def fmt(s):
    if s is None:
        return "n/a"
    return (f"OR {s['OR']:.2f} [{s['OR_ci'][0]:.2f}, {s['OR_ci'][1]:.2f}]  cfg {s['configs']:3d} strata {s['strata']:4d} "
            f"expAd {s['exp_adopt']:4d}  p_cmh {s['p_cmh']:.3g} p_clu {s['p_cluster']:.3g}")
