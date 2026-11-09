import sys; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, run_rows, mh_parts, NEVER
C = load_cache(); P = [prep(r) for r in C]
print("self-DM edges:", sum(int((p["dm"][:, 1] == p["dm"][:, 2]).sum()) for p in P if len(p["dm"])))
rng = np.random.default_rng(11)
def iid(p):
    f = p["f"].copy()
    for g in (p["stuck"], ~p["stuck"]):
        U = np.flatnonzero(g & ~p["instr"])
        times = f[U][f[U] < NEVER]; q = len(times) / max(1, len(U))
        adopt = rng.random(len(U)) < q
        new = np.full(len(U), NEVER)
        if len(times): new[adopt] = rng.choice(times, adopt.sum(), replace=True)
        f[U] = new
    return f
# Variant A: shared f (as before). Variant B: Y from f1, exposures from independent f2 (but at-risk set from f1)
import fastmh
def rows_split(p, fY, fX, W=3):
    # exposures computed with fX for senders; at-risk & Y from fY
    n, R = p["n"], p["R"]
    maxF = np.zeros((n, R + 2), int); DM = np.zeros((n, R + 2), bool)
    dm = p["dm"]
    if len(dm):
        r, s, d = dm[:, 0], dm[:, 1], dm[:, 2]; fs = fX[s]; DM[d, r] = True
        pl = (fs > r) & (fs < NEVER); np.maximum.at(maxF, (d[pl], r[pl]), fs[pl])
    if len(p["dm_ext"]): DM[p["dm_ext"][:, 1], p["dm_ext"][:, 0]] = True
    out = []
    for a in np.flatnonzero(~p["instr"]):
        T = min(R, fY[a]); ts = np.arange(1, T + 1); lo = np.maximum(1, ts - W)
        cD = np.concatenate([[0], np.cumsum(DM[a])]); Dw = (cD[ts] - cD[lo]) > 0
        Pw = np.array([bool((maxF[a, l:t] > t).any()) for l, t in zip(lo, ts)])
        out.append(np.stack([ts, np.full(T, p["stuck"][a]), ts == fY[a], Pw, Pw, Dw], 1))
    return np.concatenate(out).astype(int) if out else np.zeros((0, 6), int)
accA = np.zeros(2); accB = np.zeros(2)
for rep in range(40):
    for p in P:
        f1 = iid(p); f2 = iid(p)
        ra = run_rows(p, f1); rb = rows_split(p, f1, f2)
        if len(ra):
            m = ra[:, 5] == 1; accA += mh_parts(ra, m, ra[:, 4])
        if len(rb):
            m = rb[:, 5] == 1; accB += mh_parts(rb, m, rb[:, 4])
print("P_dir dm>0 iid null, shared f:", round(accA[0] / accA[1], 3), " | independent sender draw:", round(accB[0] / accB[1], 3))
