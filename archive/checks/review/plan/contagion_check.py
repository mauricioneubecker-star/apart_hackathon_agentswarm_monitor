import json
from scipy.stats import binomtest
d = json.load(open("/Users/mauricio/sim_local/apart_vx/analysis/results/contagion.json"))
print("top keys:", list(d.keys()))
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if any(s in k.lower() for s in ("sign", "p_", "pval", "branch", "more", "less")):
                print(path + "/" + k, ":", str(v)[:300])
            walk(v, path + "/" + k)
walk(d)
for k, n in ((7, 8), (5, 7)):
    print(f"{k}/{n}: one-sided {binomtest(k, n, 0.5, alternative='greater').pvalue:.4f}  two-sided {binomtest(k, n, 0.5).pvalue:.4f}")
