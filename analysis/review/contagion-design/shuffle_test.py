"""Shuffle test (Anagnostopoulos, Kumar & Mahdian 2008): permute first-violation rounds among uninstructed adopters
within (run, stuck). Keeps WHO adopts (homophily in who adopts preserved), destroys WHEN. Instructed agents fixed."""
import sys, json, time; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, mh_all, NEVER
C = load_cache(); P = [prep(r) for r in C]
obs = mh_all(P, [p["f"] for p in P])
rng = np.random.default_rng(12345)
NS = int(sys.argv[1]) if len(sys.argv) > 1 else 500
mode = sys.argv[2] if len(sys.argv) > 2 else "run_stuck"
res = []
t0 = time.time()
for it in range(NS):
    fs = []
    for p in P:
        f = p["f"].copy()
        groups = [p["stuck"], ~p["stuck"]] if mode == "run_stuck" else [np.ones(p["n"], bool)]
        for g in groups:
            ad = np.flatnonzero(g & ~p["instr"] & (f < NEVER))
            if len(ad) > 1:
                f[ad] = rng.permutation(f[ad])
        fs.append(f)
    res.append(mh_all(P, fs))
res = np.array(res)
names = ["E_dir all", "E_dir dm>0", "P_dir all", "P_dir dm>0"]
out = {"mode": mode, "n_shuffles": NS, "observed": dict(zip(names, obs.round(3).tolist()))}
for i, n in enumerate(names):
    v = res[:, i]
    out[n] = {"obs": round(float(obs[i]), 3), "shuffle_mean": round(float(np.mean(v)), 3), "shuffle_median": round(float(np.median(v)), 3),
              "shuffle_2.5_97.5": [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)],
              "p_one_sided_ge": round(float((1 + np.sum(v >= obs[i])) / (NS + 1)), 4),
              "p_one_sided_le": round(float((1 + np.sum(v <= obs[i])) / (NS + 1)), 4),
              "obs_over_shuffle_median": round(float(obs[i] / np.median(v)), 3)}
print(json.dumps(out, indent=1)); print(f"{time.time()-t0:.0f}s")
json.dump(out, open(f"shuffle_{mode}.json", "w"), indent=1)
