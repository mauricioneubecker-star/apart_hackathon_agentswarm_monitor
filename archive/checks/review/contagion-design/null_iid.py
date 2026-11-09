"""Pure null: every uninstructed agent independently adopts (or not) with its (run, stuck) group's empirical adoption
probability, at a round drawn from that group's empirical adoption-round distribution. No homophily, no contagion,
no fixed multiset. Real DMs kept. Reports the original estimators' null distribution."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, mh_all, NEVER
C = load_cache(); P = [prep(r) for r in C]
rng = np.random.default_rng(99)
ND = int(sys.argv[1]) if len(sys.argv) > 1 else 200
out = []
for _ in range(ND):
    fs = []
    for p in P:
        f = p["f"].copy()
        for g in (p["stuck"], ~p["stuck"]):
            U = np.flatnonzero(g & ~p["instr"])
            if len(U) == 0: continue
            times = f[U][f[U] < NEVER]
            q = len(times) / len(U)
            adopt = rng.random(len(U)) < q
            new = np.full(len(U), NEVER)
            if len(times):
                new[adopt] = rng.choice(times, adopt.sum(), replace=True)
            f[U] = new
        fs.append(f)
    out.append(mh_all(P, fs))
out = np.array(out)
names = ["E_dir all", "E_dir dm>0", "P_dir all", "P_dir dm>0"]
res = {n: {"median": round(float(np.median(out[:, i])), 3), "mean_logOR_exp": round(float(np.exp(np.mean(np.log(out[:, i])))), 3),
           "2.5_97.5": [round(float(x), 3) for x in np.percentile(out[:, i], [2.5, 97.5])]} for i, n in enumerate(names)}
print(json.dumps(res, indent=1))
json.dump(res, open("null_iid.json", "w"), indent=1)
