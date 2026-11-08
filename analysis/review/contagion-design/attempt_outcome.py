"""Outcome sensitivity: Y' = first violation OR first blocked/failed attempt (labels.first_attempt_round). Same exposures."""
import sys; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, NEVER, mh_parts
import fastmh
C = load_cache(); P = [prep(r) for r in C]
acc = {k: np.zeros(2) for k in ("E all", "E dm>0", "P dm>0")}
accK = {c: np.zeros(2) for c in ("K2", "K4")}
n_att_only = 0
for run, p in zip(C, P):
    f = p["f"].copy()
    att = np.array([run["att"].get(a, NEVER) for a in run["agents"]])
    fy = np.minimum(f, att)            # outcome & at-risk end: first violation or attempt
    n_att_only += int(((att < f) & ~p["instr"]).sum())
    # exposures still defined by real violation status of senders (f); outcome/at-risk from fy
    n, R = p["n"], p["R"]
    E_msg = np.zeros((n, R + 2), bool); DM = np.zeros((n, R + 2), bool); maxF = np.zeros((n, R + 2), int)
    dm = p["dm"]
    if len(dm):
        r, s, d = dm[:, 0], dm[:, 1], dm[:, 2]; fs = f[s]; DM[d, r] = True
        ev = fs <= r; E_msg[d[ev], r[ev]] = True
        pl = (fs > r) & (fs < NEVER); np.maximum.at(maxF, (d[pl], r[pl]), fs[pl])
    if len(p["dm_ext"]): DM[p["dm_ext"][:, 1], p["dm_ext"][:, 0]] = True
    rows = []
    for a in np.flatnonzero(~p["instr"]):
        T = min(R, fy[a]); ts = np.arange(1, T + 1); lo = np.maximum(1, ts - 3)
        cE = np.concatenate([[0], np.cumsum(E_msg[a])]); cD = np.concatenate([[0], np.cumsum(DM[a])])
        Pw = np.array([bool((maxF[a, l:t] > t).any()) for l, t in zip(lo, ts)])
        rows.append(np.stack([ts, np.full(T, p["stuck"][a]), ts == fy[a], (cE[ts] - cE[lo]) > 0, Pw, (cD[ts] - cD[lo]) > 0], 1))
    rows = np.concatenate(rows).astype(int)
    allm = np.ones(len(rows), bool); dmm = rows[:, 5] == 1
    acc["E all"] += mh_parts(rows, allm, rows[:, 3]); acc["E dm>0"] += mh_parts(rows, dmm, rows[:, 3]); acc["P dm>0"] += mh_parts(rows, dmm, rows[:, 4])
    accK["K2" if "-K2-" in p["cfg"] else "K4"] += mh_parts(rows, dmm, rows[:, 3])
print("agents whose first attempt precedes first violation (or who only attempted):", n_att_only)
for k, v in acc.items(): print(f"Y'=violation-or-attempt  {k}: OR {v[0]/v[1]:.3f}")
for k, v in accK.items(): print(f"Y'  {k} dm>0 E: OR {v[0]/v[1]:.3f}")
