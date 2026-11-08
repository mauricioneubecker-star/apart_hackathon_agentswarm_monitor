"""Vectorised re-implementation of contagion.py Part A (rows + MH + config bootstrap)."""
import os
import pickle

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    return pickle.load(open(os.path.join(HERE, "runs.pkl"), "rb"))


def win_any(X, w, R):
    """X[..., r] (r=0..R+1) -> W[..., t] = any(X[..., r] > 0 for r in range(max(1, t-w), t)), t=0..R+1."""
    c = np.concatenate([np.zeros(X.shape[:-1] + (1,), np.int32), np.cumsum(X > 0, axis=-1, dtype=np.int32)], axis=-1)
    # c[..., k] = #positive among X[..., 0..k-1]
    T = np.arange(X.shape[-1])
    lo = np.maximum(1, T - w)
    hi = T  # exclusive
    hi_ = np.maximum(hi, lo)
    return (np.take(c, hi_, axis=-1) - np.take(c, lo, axis=-1)) > 0


def run_rows(o, f=None, w=None, extra=None, outcome_f=None, cum=False):
    """Rows for one run. f overrides first-violation rounds (used for SENDER status and outcome unless outcome_f).
    Returns dict of 1-d arrays."""
    R = o["R"]
    w = o["w"] if w is None else w
    if cum:
        w = 10 ** 6
    f = o["f"] if f is None else f
    fo = f if outcome_f is None else outcome_f
    N = len(o["ids"])
    D, Dm, Ball = o["D"], o["Dm"], o["Ball"]
    rr = np.arange(R + 2)
    viol_at = f[:, None] <= rr[None, :]                         # [s, r] sender had violated by r
    Edir_r = ((D > 0) & viol_at[:, None, :]).any(0)              # [a, r]
    Emech_r = ((Dm > 0) & viol_at[:, None, :]).any(0)
    Eany_r = ((Ball > 0) & viol_at[:, None, :]).any(0)
    Edir = win_any(Edir_r, w, R)                                 # [a, t]
    Emech = win_any(Emech_r, w, R)
    Eany = win_any(Eany_r, w, R)
    Efeed = win_any(o["feed"], w, R)
    DM = win_any(o["DMany"], w, R)
    WD = win_any(D, w, R)                                        # [s, a, t] any direct s->a in window
    fut = (f[:, None] > rr[None, :]) & (f[:, None] < 99)         # [s, t] sender violates strictly after t
    Pdir = (WD & fut[:, None, :]).any(0)                         # [a, t]
    rows = {k: [] for k in ("t", "stuck", "Y", "E_dir", "E_any", "E_mech", "E_feed", "P_dir", "dm", "agent")}
    if extra:
        for k in extra:
            rows[k] = []
    for a in range(N):
        if o["instructed"][a]:
            continue
        fa = fo[a]
        ts = np.arange(1, min(R, fa) + 1)
        if len(ts) == 0:
            continue
        rows["t"].append(ts)
        rows["stuck"].append(np.full(len(ts), int(o["stuck"][a])))
        rows["Y"].append((ts == fa).astype(int))
        rows["E_dir"].append(Edir[a, ts].astype(int))
        rows["E_any"].append(Eany[a, ts].astype(int))
        rows["E_mech"].append(Emech[a, ts].astype(int))
        rows["E_feed"].append(Efeed[a, ts].astype(int))
        rows["P_dir"].append(Pdir[a, ts].astype(int))
        rows["dm"].append(DM[a, ts].astype(int))
        rows["agent"].append(np.full(len(ts), a))
        if extra:
            for k, fn in extra.items():
                rows[k].append(fn(o, a, ts, dict(f=f, w=w, WD=WD, viol_at=viol_at)))
    return {k: (np.concatenate(v) if v else np.zeros(0, int)) for k, v in rows.items()}


def all_rows(runs, f_over=None, **kw):
    parts = []
    for i, o in enumerate(runs):
        f = None if f_over is None else f_over[i]
        r = run_rows(o, f=f, **kw)
        n = len(r["t"])
        r["run_i"] = np.full(n, i)
        r["cfg"] = np.full(n, o["sid"], dtype=object)
        parts.append(r)
    keys = parts[0].keys()
    out = {k: np.concatenate([p[k] for p in parts]) for k in keys}
    return out


def mh_parts(rows, x, mask=None):
    """Per-stratum a,b,c,d -> per-config sums of [or_num, or_den, rr_num, rr_den, a, strata, O-E, Var]."""
    if mask is None:
        mask = np.ones(len(x), bool)
    run_i, t, st, y, e = rows["run_i"][mask], rows["t"][mask], rows["stuck"][mask], rows["Y"][mask], x[mask]
    cfg = rows["cfg"][mask]
    key = (run_i.astype(np.int64) * 100 + t) * 2 + st
    uk, inv = np.unique(key, return_inverse=True)
    K = len(uk)
    a = np.bincount(inv, weights=(e == 1) & (y == 1), minlength=K)
    b = np.bincount(inv, weights=(e == 1) & (y == 0), minlength=K)
    c = np.bincount(inv, weights=(e == 0) & (y == 1), minlength=K)
    d = np.bincount(inv, weights=(e == 0) & (y == 0), minlength=K)
    n = a + b + c + d
    ok = ((a + b) > 0) & ((c + d) > 0) & ((a + c) > 0)
    # config of each stratum
    first_idx = np.zeros(K, int)
    first_idx[inv[::-1]] = np.arange(len(inv))[::-1]
    scfg = cfg[first_idx]
    m1, n1 = a + c, a + b
    E = n1 * m1 / n
    V = np.where(n > 1, n1 * (n - n1) * m1 * (n - m1) / (n ** 2 * np.maximum(n - 1, 1)), 0)
    vals = np.stack([a * d / n, b * c / n, a * (c + d) / n, c * (a + b) / n, a, np.ones(K), a - E, V], 1)[ok]
    scfg = scfg[ok]
    ucfg, cinv = np.unique(scfg, return_inverse=True)
    M = np.zeros((len(ucfg), vals.shape[1]))
    np.add.at(M, cinv, vals)
    return ucfg, M


def summarize(ucfg, M, nboot=2000, seed=0):
    if len(M) == 0 or M[:, 1].sum() == 0:
        return None
    rng = np.random.default_rng(seed)
    o = M[:, 0].sum() / M[:, 1].sum()
    rr = M[:, 2].sum() / M[:, 3].sum()
    bo, brr = [], []
    for _ in range(nboot):
        W = M[rng.integers(0, len(M), len(M))]
        if W[:, 1].sum() > 0 and W[:, 3].sum() > 0:
            bo.append(W[:, 0].sum() / W[:, 1].sum())
            brr.append(W[:, 2].sum() / W[:, 3].sum())
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return {"OR": float(o), "OR_ci": q(bo), "RR": float(rr), "RR_ci": q(brr), "configs": int(len(ucfg)),
            "strata": int(M[:, 5].sum()), "exp_adopt": int(M[:, 4].sum())}


def mh_or(rows, x, mask=None):
    u, M = mh_parts(rows, x, mask)
    return M[:, 0].sum() / M[:, 1].sum() if len(M) and M[:, 1].sum() > 0 else np.nan


def signflip_cfg(M, nperm=20000, seed=1):
    """Config-level sign-flip test on per-config (O-E) sums: H0 symmetric around 0. Two-sided p."""
    rng = np.random.default_rng(seed)
    oe = M[:, 6]
    obs = oe.sum()
    s = rng.choice([-1, 1], size=(nperm, len(oe)))
    null = (s * oe).sum(1)
    return float((np.sum(np.abs(null) >= abs(obs) - 1e-12) + 1) / (nperm + 1))


def fmt(s):
    if s is None:
        return "None"
    return f"OR {s['OR']:.2f} [{s['OR_ci'][0]:.2f}, {s['OR_ci'][1]:.2f}]  RR {s['RR']:.2f}  cfg {s['configs']} strata {s['strata']} expAdopt {s['exp_adopt']}"
