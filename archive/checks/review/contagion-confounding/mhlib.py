"""Mantel-Haenszel OR/RR within strata, bootstrap over configs (same estimator as analysis/contagion.py:mh/summarize,
vectorised; strata keys can be extended by confounder columns)."""
import numpy as np
import pandas as pd

BASE = ["run", "t", "stuck"]


def mh_table(df, x, keys=BASE, mask=None):
    """Per-config MH sums. x: exposure column name. mask: boolean Series/array or None."""
    d = df if mask is None else df[np.asarray(mask, bool)]
    d = d[keys + ["cfg", "Y", x]].copy() if "cfg" not in keys else d[keys + ["Y", x]].copy()
    d["_a"] = ((d[x] == 1) & (d.Y == 1)).astype(int)
    d["_b"] = ((d[x] == 1) & (d.Y == 0)).astype(int)
    d["_c"] = ((d[x] == 0) & (d.Y == 1)).astype(int)
    d["_d"] = ((d[x] == 0) & (d.Y == 0)).astype(int)
    gk = keys if "cfg" in keys else keys + ["cfg"]
    # run determines cfg, so adding cfg to the group keys never splits a stratum
    s = d.groupby(gk, sort=False, observed=True)[["_a", "_b", "_c", "_d"]].sum().reset_index()
    s = s[((s._a + s._b) > 0) & ((s._c + s._d) > 0) & ((s._a + s._c) > 0)]
    n = s._a + s._b + s._c + s._d
    s["or_num"] = s._a * s._d / n
    s["or_den"] = s._b * s._c / n
    s["rr_num"] = s._a * (s._c + s._d) / n
    s["rr_den"] = s._c * (s._a + s._b) / n
    s["one"] = 1
    acc = s.groupby("cfg")[["or_num", "or_den", "rr_num", "rr_den", "_a", "one"]].sum()
    return acc


def summarize(acc, nboot=2000, seed=0):
    if len(acc) == 0 or acc.or_den.sum() == 0:
        return None
    M = acc[["or_num", "or_den", "rr_num", "rr_den", "_a", "one"]].to_numpy()
    o = M[:, 0].sum() / M[:, 1].sum()
    r = M[:, 2].sum() / M[:, 3].sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(M), (nboot, len(M)))
    S = M[idx].sum(1)   # nboot x 6
    ok = (S[:, 1] > 0) & (S[:, 3] > 0)
    bo = S[ok, 0] / S[ok, 1]
    brr = S[ok, 2] / S[ok, 3]
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return {"OR": float(o), "OR_ci": q(bo), "RR": float(r), "RR_ci": q(brr), "configs_informative": int(len(M)),
            "strata_used": int(M[:, 5].sum()), "exposed_adoptions_in_strata": int(M[:, 4].sum()),
            "p_boot_or_le_1": float(np.mean(bo <= 1.0))}


def est(df, x, keys=BASE, mask=None, nboot=2000, seed=0):
    return summarize(mh_table(df, x, keys, mask), nboot, seed)


def fmt(r):
    if r is None:
        return "n/a"
    return (f"OR {r['OR']:.2f} [{r['OR_ci'][0]:.2f}; {r['OR_ci'][1]:.2f}]  RR {r['RR']:.2f}  "
            f"cfg {r['configs_informative']}  strata {r['strata_used']}  expAdopt {r['exposed_adoptions_in_strata']}  "
            f"P(OR<=1) {r['p_boot_or_le_1']:.3f}")
