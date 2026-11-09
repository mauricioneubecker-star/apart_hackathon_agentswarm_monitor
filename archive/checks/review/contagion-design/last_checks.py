import sys; sys.path.insert(0, '.')
import numpy as np
from collections import defaultdict
from fastmh import load_cache, prep, run_rows, mh_parts, NEVER
C = load_cache(); P = [prep(r) for r in C]
rng = np.random.default_rng(3)
def boot(acc_by_cfg, nb=2000):
    M = np.array(list(acc_by_cfg.values())); o = M[:, 0].sum() / M[:, 1].sum(); b = []
    for _ in range(nb):
        W = M[rng.integers(0, len(M), len(M))]
        if W[:, 1].sum() > 0: b.append(W[:, 0].sum() / W[:, 1].sum())
    return round(o, 3), [round(float(np.percentile(b, 2.5)), 2), round(float(np.percentile(b, 97.5)), 2)], len(M)
# (i) cumulative exposure aligned with agent memory (30 cycles): window = all rounds before t
for W in (30,):
    accE, accEd, accPd = defaultdict(lambda: np.zeros(2)), defaultdict(lambda: np.zeros(2)), defaultdict(lambda: np.zeros(2))
    for p in P:
        rows = run_rows(p, p["f"], W)
        allm = np.ones(len(rows), bool); dmm = rows[:, 5] == 1
        accE[p["cfg"]] += mh_parts(rows, allm, rows[:, 3]); accEd[p["cfg"]] += mh_parts(rows, dmm, rows[:, 3]); accPd[p["cfg"]] += mh_parts(rows, dmm, rows[:, 4])
    f = lambda a: {k: v for k, v in a.items() if v[1] > 0}
    print(f"cumulative window (W={W}, = agent memory): E_dir all", boot(f(accE)), "| E_dir dm_ever>0", boot(f(accEd)), "| P_dir dm_ever>0", boot(f(accPd)))
# (ii) co-adoption bucket under an iid null: exposure = DM in window from sender with fs == t
def coadopt_or(fs_list):
    num = den = 0.0
    for p, f in zip(P, fs_list):
        n, R = p["n"], p["R"]; X = np.zeros((n, R + 2, ), int)
        rows = run_rows(p, f)
        if not len(rows): continue
        # rebuild exposure: any DM r in [t-3,t-1] from sender with f[s]==t
        dm = p["dm"]; ex = []
        agents = np.flatnonzero(~p["instr"])
        idx = 0; e = np.zeros(len(rows), int)
        for a in agents:
            T = min(R, f[a])
            if len(dm):
                mine = dm[dm[:, 2] == a]
                for j, t in enumerate(range(1, T + 1)):
                    w = mine[(mine[:, 0] >= max(1, t - 3)) & (mine[:, 0] < t)]
                    e[idx + j] = int(np.any(f[w[:, 1]] == t)) if len(w) else 0
            idx += T
        dmm = rows[:, 5] == 1
        nu, de = mh_parts(rows, dmm, e); num += nu; den += de
    return num / den
def iid(p):
    f = p["f"].copy()
    for g in (p["stuck"], ~p["stuck"]):
        U = np.flatnonzero(g & ~p["instr"]); times = f[U][f[U] < NEVER]; q = len(times) / max(1, len(U))
        ad = rng.random(len(U)) < q; new = np.full(len(U), NEVER)
        if len(times): new[ad] = rng.choice(times, ad.sum(), replace=True)
        f[U] = new
    return f
obs = coadopt_or([p["f"] for p in P])
nul = [coadopt_or([iid(p) for p in P]) for _ in range(30)]
print(f"co-adoption exposure (sender violates exactly at t), dm>0: observed OR {obs:.3f}; iid-null median {np.median(nul):.3f} [{np.percentile(nul,5):.2f}, {np.percentile(nul,95):.2f}]")
# (iii) attempt-inclusive outcome with config bootstrap
accY = {k: defaultdict(lambda: np.zeros(2)) for k in ("E all", "E dm>0", "P dm>0", "K2 E dm>0", "K4 E dm>0")}
for run, p in zip(C, P):
    f = p["f"]; att = np.array([run["att"].get(a, NEVER) for a in run["agents"]]); fy = np.minimum(f, att)
    n, R = p["n"], p["R"]; E_msg = np.zeros((n, R + 2), bool); DM = np.zeros((n, R + 2), bool); maxF = np.zeros((n, R + 2), int)
    dm = p["dm"]
    if len(dm):
        r, s, d = dm[:, 0], dm[:, 1], dm[:, 2]; fs = f[s]; DM[d, r] = True; ev = fs <= r; E_msg[d[ev], r[ev]] = True
        pl = (fs > r) & (fs < NEVER); np.maximum.at(maxF, (d[pl], r[pl]), fs[pl])
    if len(p["dm_ext"]): DM[p["dm_ext"][:, 1], p["dm_ext"][:, 0]] = True
    rows = []
    for a in np.flatnonzero(~p["instr"]):
        T = min(R, fy[a]); ts = np.arange(1, T + 1); lo = np.maximum(1, ts - 3)
        cE = np.concatenate([[0], np.cumsum(E_msg[a])]); cD = np.concatenate([[0], np.cumsum(DM[a])])
        Pw = np.array([bool((maxF[a, l:t] > t).any()) for l, t in zip(lo, ts)])
        rows.append(np.stack([ts, np.full(T, p["stuck"][a]), ts == fy[a], (cE[ts] - cE[lo]) > 0, Pw, (cD[ts] - cD[lo]) > 0], 1))
    rows = np.concatenate(rows).astype(int); allm = np.ones(len(rows), bool); dmm = rows[:, 5] == 1
    c = p["cfg"]; accY["E all"][c] += mh_parts(rows, allm, rows[:, 3]); accY["E dm>0"][c] += mh_parts(rows, dmm, rows[:, 3]); accY["P dm>0"][c] += mh_parts(rows, dmm, rows[:, 4])
    accY[("K2" if "-K2-" in c else "K4") + " E dm>0"][c] += mh_parts(rows, dmm, rows[:, 3])
for k, a in accY.items():
    a = {x: v for x, v in a.items() if v[1] > 0 or v[0] > 0}
    print(f"Y'=violation-or-attempt {k}:", boot(a))
