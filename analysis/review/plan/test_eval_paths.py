"""Exercise llm_monitor.evaluate code paths on synthetic data (no repo writes: run with python -B)."""
import sys, types, io
sys.path.insert(0, "/Users/mauricio/sim_local/apart_ana")
import numpy as np, pandas as pd
from llm_monitor import evaluate as EV

rng = np.random.default_rng(1)

# ---------- 1) bootstrap() on a split where one predictor is all-NaN (LLM monitors not run on vx)
n = 200
base = pd.DataFrame({"group_id": [f"g{i%10}" for i in range(n)], "vx_base": [f"b{i%14}" for i in range(n)]})
D = types.SimpleNamespace(base=base, y=(rng.random(n) < 0.15).astype(float))
preds = {"clock": rng.random(n), "zs:global_full": np.full(n, np.nan), "ext:gnn_final": rng.random(n)}
rows = np.ones(n, bool)
common = rows & np.all([~np.isnan(preds[k]) for k in preds], 0)
print("common rows when zs all-NaN:", int(common.sum()))
try:
    EV.bootstrap(D, common, preds, ["ext:gnn_final"], 20, unit="vx_base")
    print("bootstrap on empty rows: no error")
except Exception as e:
    print("bootstrap on empty rows raises:", type(e).__name__, e)

# ---------- 2) refs_for_diff: which differences are produced
preds2 = {"clock": rng.random(n), "zs:global_full": rng.random(n), "zs:pairwise": rng.random(n),
          "bag+graph": rng.random(n), "ext:gnn_final": rng.random(n)}
_, diffs, _ = EV.bootstrap(D, rows, preds2, ["pairwise", "bag", "bag+graph", "ext:gnn_final"], 50)
ks = sorted({k.split("|")[0] for k in diffs})
print("diffs produced:", ks)
print("any '- clock':", any(k.endswith(" - clock") for k in ks), " zs:global_full - zs:pairwise:", "zs:global_full - zs:pairwise" in ks)

# ---------- 3) ext CSV with duplicated keys (e.g. both ID repeats exported)
key = pd.MultiIndex.from_frame(pd.DataFrame({"episode_id": ["a/rep0"] * 3, "t": [1, 2, 3]}))
csv = "episode_id,t,p_graph\na/rep0,1,0.1\na/rep0,1,0.2\na/rep0,2,0.3\na/rep0,3,0.4\n"
try:
    E = pd.read_csv(io.StringIO(csv)).set_index(["episode_id", "t"]).reindex(key)
    print("dup keys: no error", E.p_graph.values)
except Exception as e:
    print("dup keys raise:", type(e).__name__, e)
# float t keys silently -> NaN?
csv2 = "episode_id,t,p_graph\na/rep0,1.0,0.1\na/rep0,2.0,0.3\na/rep0,3.0,0.4\n"
E = pd.read_csv(io.StringIO(csv2)).set_index(["episode_id", "t"]).reindex(key)
print("float t keys ->", E.p_graph.values)

# ---------- 4) vx_shift bootstrap: boolean-mask collapse vs proper resampling with multiplicity
def make_vx(nb=14, rows_per=22, seed=0):
    r = np.random.default_rng(seed)
    recs, ys, ps = [], [], []
    for bi in range(nb):
        eff = r.normal(0, 1.0)            # base-level shift in score
        prev = r.uniform(0.02, 0.25)
        for arm, rep in (("id", "rep0"), ("id", "rep1"), ("time", "rep0")):
            for k in range(rows_per):
                y = float(r.random() < prev)
                s = 1.2 * y + 0.6 * eff + r.normal(0, 1) + (0.3 if arm == "time" else 0)
                recs.append({"split": f"night_vx_{arm}", "vx_arm": arm, "rep": rep, "vx_base": f"B{bi}"})
                ys.append(y); ps.append(s)
    b = pd.DataFrame(recs)
    return types.SimpleNamespace(base=b, y=np.array(ys)), {"m": np.array(ps)}

def proper(D, scores, n, n_boot, seed=0):
    b = D.base; yok = ~np.isnan(D.y)
    vx = yok & b.split.str.startswith("night_vx").values
    idr0 = vx & (b.vx_arm == "id").values & (b.rep == "rep0").values
    am = vx & (b.vx_arm == "time").values
    bases = sorted(set(b.vx_base[am]) & set(b.vx_base[idr0]))
    from sklearn.metrics import roc_auc_score
    r = np.random.default_rng(seed); out = []
    for _ in range(n_boot):
        pick = r.choice(bases, len(bases), replace=True)
        ia = np.concatenate([np.where(am & (b.vx_base == x).values)[0] for x in pick])
        i0 = np.concatenate([np.where(idr0 & (b.vx_base == x).values)[0] for x in pick])
        ya, y0 = D.y[ia], D.y[i0]
        if 0 < ya.sum() < len(ya) and 0 < y0.sum() < len(y0):
            out.append(roc_auc_score(ya, scores[n][ia]) - roc_auc_score(y0, scores[n][i0]))
    out = np.array(out)
    return np.percentile(out, 2.5), np.percentile(out, 97.5)

wid_c, wid_p = [], []
for sd in range(6):
    Dv, sc = make_vx(seed=sd)
    res = EV.vx_shift(Dv, sc, ["m"], 400, seed=sd)
    lo, hi = res["time"]["m"]["ci"]
    plo, phi = proper(Dv, sc, "m", 400, seed=sd)
    wid_c.append(hi - lo); wid_p.append(phi - plo)
    print(f"seed {sd}: vx_shift CI width {hi-lo:.3f}  proper bootstrap width {phi-plo:.3f}")
print(f"mean width ratio collapsed/proper: {np.mean(np.array(wid_c)/np.array(wid_p)):.3f}")
