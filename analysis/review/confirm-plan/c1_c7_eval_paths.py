"""Issue 1 (bootstrap crash on empty common rows) and issue 7 (vx_shift uses boolean masks -> no replacement).
Imports the real functions from the analysis worktree; synthetic data only, writes nothing."""
import sys, types, traceback
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, "/Users/mauricio/sim_local/apart_ana")
import llm_monitor.evaluate as E

# ---------------- issue 1: empty common mask (a predictor all-NaN on the vx split) ----------------
rng = np.random.default_rng(1)
n = 200
base = pd.DataFrame({"group_id": np.repeat([f"g{i}" for i in range(10)], 20),
                     "vx_base": np.repeat([f"b{i}" for i in range(10)], 20)})
D = types.SimpleNamespace(base=base, y=(rng.random(n) < 0.2).astype(float))
preds = {"clock": rng.random(n), "zs:pairwise": np.full(n, np.nan)}   # zero-shot not run on vx
rows = np.ones(n, bool)
common = rows & np.all([~np.isnan(preds[k]) for k in preds], 0)
print("common rows:", int(common.sum()))
try:
    E.bootstrap(D, common, preds, ["pairwise", "bag", "bag+graph"], 50, unit="vx_base")
    print("bootstrap: no error")
except Exception as e:
    print("bootstrap raised:", type(e).__name__, e)

# ---------------- issue 7: vx_shift resampling ----------------
def make_vx(seed, n_bases=14, rows_per_run=30):
    r = np.random.default_rng(seed)
    recs, ys, sc = [], [], []
    for bi in range(n_bases):
        u = r.normal(0, 1.0)            # base effect on difficulty of ranking
        for arm, rep in (("id", "rep0"), ("id", "rep1"), ("glm", "rep0")):
            t = np.arange(rows_per_run)
            p_tip = 1 / (1 + np.exp(-(t - 22) / 2.5 + 0.8 * u))
            y = (r.random(rows_per_run) < p_tip * 0.5).astype(float)
            s = 0.9 * y + r.normal(0, 1, rows_per_run) * (1.0 + 0.5 * abs(u)) + (0.4 if arm == "glm" else 0) * r.normal()
            for k in range(rows_per_run):
                recs.append({"split": "night_vx_id" if arm == "id" else "night_vx_pop", "vx_arm": arm, "rep": rep,
                             "vx_base": f"B{bi}"})
            ys += list(y); sc += list(s)
    b = pd.DataFrame(recs)
    return types.SimpleNamespace(base=b, y=np.array(ys)), {"m": np.array(sc)}

def proper(D, scores, n, arm, n_boot, seed):
    b = D.base
    am = (b.vx_arm == arm).values if arm != "noise" else ((b.vx_arm == "id") & (b.rep == "rep1")).values
    i0 = ((b.vx_arm == "id") & (b.rep == "rep0")).values
    bases = sorted(set(b.vx_base[am]) & set(b.vx_base[i0]))
    RA = {x: np.where(am & (b.vx_base == x).values)[0] for x in bases}
    R0 = {x: np.where(i0 & (b.vx_base == x).values)[0] for x in bases}
    rg = np.random.default_rng(seed); out = []
    for _ in range(n_boot):
        pick = rg.choice(bases, len(bases), replace=True)
        ia = np.concatenate([RA[x] for x in pick]); i_0 = np.concatenate([R0[x] for x in pick])
        ya, y0 = D.y[ia], D.y[i_0]
        if 0 < ya.sum() < len(ya) and 0 < y0.sum() < len(y0):
            out.append(roc_auc_score(ya, scores[n][ia]) - roc_auc_score(y0, scores[n][i_0]))
    return np.percentile(out, [2.5, 97.5])

ratios = []
for sd in range(6):
    D, sc = make_vx(sd)
    res = E.vx_shift(D, sc, ["m"], 1000, seed=sd)
    lo, hi = res["glm"]["m"]["ci"]
    plo, phi = proper(D, sc, "m", "glm", 1000, sd + 100)
    ratios.append((hi - lo) / (phi - plo))
    print(f"seed {sd}: vx_shift CI width {hi-lo:.3f}  proper cluster bootstrap width {phi-plo:.3f}  ratio {ratios[-1]:.2f}")
print("mean ratio %.2f  range %.2f-%.2f" % (np.mean(ratios), min(ratios), max(ratios)))
print("expected distinct bases per draw (14 with replacement): %.2f" % (14 * (1 - (13 / 14) ** 14)))
print("vx_shift output keys per arm/name:", list(res["glm"]["m"].keys()), "arms:", list(res.keys()))
