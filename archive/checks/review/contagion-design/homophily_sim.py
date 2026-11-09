"""Synthetic null with ZERO contagion: adoption depends only on a latent trait that is smoothed over the real DM graph
(homophily). Real messages (rounds, senders, readers) are kept; only who adopts and when is re-drawn.
Within each (run, stuck) group, the real number of uninstructed adopters and the real multiset of adoption rounds are
kept; agents with the highest latent score adopt (earliest round to the highest score). Instructed agents keep their
real rounds. Then the original E_dir / P_dir MH estimators are applied unchanged."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, mh_all, NEVER
C = load_cache(); P = [prep(r) for r in C]
rng = np.random.default_rng(7)
# undirected DM adjacency per run (whole run)
ADJ = []
for p in P:
    A = np.zeros((p["n"], p["n"]))
    if len(p["dm"]):
        np.add.at(A, (p["dm"][:, 1], p["dm"][:, 2]), 1)
    A = A + A.T
    np.fill_diagonal(A, 0)
    deg = A.sum(1, keepdims=True)
    ADJ.append(np.where(deg > 0, A / np.where(deg > 0, deg, 1), 0))
def draw(lam, noise, ndraw=60):
    out = []
    for _ in range(ndraw):
        fs = []
        for p, Wm in zip(P, ADJ):
            z = rng.standard_normal(p["n"])
            s = z + lam * (Wm @ z) + noise * rng.standard_normal(p["n"])
            f = p["f"].copy()
            for g in (p["stuck"], ~p["stuck"]):
                U = np.flatnonzero(g & ~p["instr"])
                times = np.sort(f[U][f[U] < NEVER])
                k = len(times)
                f[U] = NEVER
                if k:
                    order = U[np.argsort(-s[U])]
                    f[order[:k]] = times
            fs.append(f)
        out.append(mh_all(P, fs))
    out = np.array(out)
    return {"E_dir_all": [round(float(np.median(out[:, 0])), 2), [round(float(x), 2) for x in np.percentile(out[:, 0], [5, 95])]],
            "E_dir_dm>0": [round(float(np.median(out[:, 1])), 2), [round(float(x), 2) for x in np.percentile(out[:, 1], [5, 95])]],
            "P_dir_all": [round(float(np.median(out[:, 2])), 2), [round(float(x), 2) for x in np.percentile(out[:, 2], [5, 95])]],
            "P_dir_dm>0": [round(float(np.median(out[:, 3])), 2), [round(float(x), 2) for x in np.percentile(out[:, 3], [5, 95])]]}
res = {}
for lam, noise in ((0, 0), (1, 0.5), (2, 0.5), (4, 0.5), (4, 0), (8, 0.25)):
    res[f"lam={lam},noise={noise}"] = draw(lam, noise)
    print(f"lam={lam} noise={noise}", res[f"lam={lam},noise={noise}"], flush=True)
json.dump(res, open("homophily_sim.json", "w"), indent=1)
