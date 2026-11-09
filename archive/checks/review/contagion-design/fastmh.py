"""Fast re-labelling engine: per-run arrays so exposures/outcomes can be recomputed under shuffled adoption times."""
import os
import pickle

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NEVER = 99


def load_cache():
    return pickle.load(open(os.path.join(HERE, "data", "runs.pkl"), "rb"))


def prep(run):
    ag = run["agents"]
    idx = {a: i for i, a in enumerate(ag)}
    R = run["R"]
    dm = np.array([(r, idx[s], idx[d]) for r, s, d, _, _ in run["dms"] if s in idx and d in idx], dtype=int).reshape(-1, 3)
    # external senders (not agents) only matter for dm_any
    dm_ext = np.array([(r, idx[d]) for r, s, d, _, _ in run["dms"] if s not in idx and d in idx], dtype=int).reshape(-1, 2)
    f = np.array([run["first"].get(a, NEVER) for a in ag], dtype=int)
    instr = np.array([a in run["instructed"] for a in ag])
    stuck = np.array([a in run["stuck"] for a in ag])
    return {"R": R, "dm": dm, "dm_ext": dm_ext, "f": f, "instr": instr, "stuck": stuck, "n": len(ag), "cfg": run["cfg"],
            "run": run["run"]}


def run_rows(p, f, W=3):
    """Return arrays (t, stuck, Y, E, P, DM) for at-risk rows of uninstructed agents under adoption rounds f."""
    n, R = p["n"], p["R"]
    E_msg = np.zeros((n, R + 2), bool)
    DM_msg = np.zeros((n, R + 2), bool)
    maxF = np.zeros((n, R + 2), int)
    dm = p["dm"]
    if len(dm):
        r, s, d = dm[:, 0], dm[:, 1], dm[:, 2]
        fs = f[s]
        DM_msg[d, r] = True
        ev = fs <= r
        E_msg[d[ev], r[ev]] = True
        pl = (fs > r) & (fs < NEVER)
        np.maximum.at(maxF, (d[pl], r[pl]), fs[pl])
    if len(p["dm_ext"]):
        DM_msg[p["dm_ext"][:, 1], p["dm_ext"][:, 0]] = True
    out = []
    for a in np.flatnonzero(~p["instr"]):
        T = min(R, f[a])
        ts = np.arange(1, T + 1)
        lo = np.maximum(1, ts - W)
        cE = np.concatenate([[0], np.cumsum(E_msg[a])])
        cD = np.concatenate([[0], np.cumsum(DM_msg[a])])
        Ewin = (cE[ts] - cE[lo]) > 0          # rounds lo..t-1
        Dwin = (cD[ts] - cD[lo]) > 0
        # placebo: any r in [lo, t-1] with maxF[a, r] > t
        Pw = np.array([bool((maxF[a, l:t] > t).any()) for l, t in zip(lo, ts)])
        Y = (ts == f[a])
        out.append(np.stack([ts, np.full(T, p["stuck"][a]), Y, Ewin, Pw, Dwin], 1))
    return np.concatenate(out).astype(int) if out else np.zeros((0, 6), int)


def mh_parts(rows, mask, x):
    """MH (OR num, OR den) for strata (t, stuck) within one run."""
    t, st, Y = rows[:, 0], rows[:, 1], rows[:, 2]
    k = (t * 2 + st)[mask]
    y, e = Y[mask], x[mask]
    if len(k) == 0:
        return 0.0, 0.0
    K = k.max() + 1
    a = np.bincount(k, (e == 1) & (y == 1), K); b = np.bincount(k, (e == 1) & (y == 0), K)
    c = np.bincount(k, (e == 0) & (y == 1), K); d = np.bincount(k, (e == 0) & (y == 0), K)
    n = a + b + c + d
    ok = ((a + b) > 0) & ((c + d) > 0) & ((a + c) > 0)
    return float(np.sum((a * d / np.where(n > 0, n, 1))[ok])), float(np.sum((b * c / np.where(n > 0, n, 1))[ok]))


def mh_all(preps, fs, W=3):
    """MH ORs for E (all), E (dm>0), P (all), P (dm>0) under adoption-round assignment fs (list of arrays)."""
    acc = np.zeros((4, 2))
    for p, f in zip(preps, fs):
        rows = run_rows(p, f, W)
        if len(rows) == 0:
            continue
        allm = np.ones(len(rows), bool)
        dmm = rows[:, 5] == 1
        for i, (m, col) in enumerate(((allm, 3), (dmm, 3), (allm, 4), (dmm, 4))):
            nu, de = mh_parts(rows, m, rows[:, col])
            acc[i] += [nu, de]
    return acc[:, 0] / acc[:, 1]
