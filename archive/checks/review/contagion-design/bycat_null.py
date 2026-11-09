import sys, json; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, mh_all, NEVER
C = load_cache(); P = [prep(r) for r in C]
rng = np.random.default_rng(2024)
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
def shuf(p):
    f = p["f"].copy()
    for g in (p["stuck"], ~p["stuck"]):
        ad = np.flatnonzero(g & ~p["instr"] & (f < NEVER))
        if len(ad) > 1: f[ad] = rng.permutation(f[ad])
    return f
out = {}
names = ["E_dir all", "E_dir dm>0", "P_dir all", "P_dir dm>0"]
for cat in ("K2", "K4"):
    sub = [p for p in P if f"-{cat}-" in p["cfg"]]
    obs = mh_all(sub, [p["f"] for p in sub])
    nI = np.array([mh_all(sub, [iid(p) for p in sub]) for _ in range(150)])
    nS = np.array([mh_all(sub, [shuf(p) for p in sub]) for _ in range(150)])
    out[cat] = {"runs": len(sub)}
    for i, n in enumerate(names):
        out[cat][n] = {"obs": round(float(obs[i]), 3),
                       "iid_null_median": round(float(np.median(nI[:, i])), 3), "iid_null_95": [round(float(x), 2) for x in np.percentile(nI[:, i], [2.5, 97.5])],
                       "shuffle_null_median": round(float(np.median(nS[:, i])), 3), "shuffle_null_95": [round(float(x), 2) for x in np.percentile(nS[:, i], [2.5, 97.5])],
                       "p_le_shuffle": round(float((1 + np.sum(nS[:, i] <= obs[i])) / 151), 4), "p_ge_shuffle": round(float((1 + np.sum(nS[:, i] >= obs[i])) / 151), 4)}
    print(cat, json.dumps(out[cat], indent=1), flush=True)
json.dump(out, open("bycat_null.json", "w"), indent=1)
