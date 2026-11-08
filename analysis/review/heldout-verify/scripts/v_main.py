"""Independent verification of the held-out comparison (own code, no import of the other analyst's scripts or of
the harness modules).

Bootstrap engine: weighted AUROC with config multiplicities, computed from per-config x tie-group class counts
(Pw = K @ Npos, Nw = K @ Nneg; AUROC = sum_g Pw_g (cumNw_<g + Nw_g / 2) / (sum Pw * sum Nw)).
  python -I -B v_main.py [seed] [draw]     draw = mine (rng.choice per draw) | theirs (rng.integers (B, C))
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
V = f"{SCR}/heldout-verify"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
HELD = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]
SHORT = {"night_test_id": "test_id", "night_test_ood_family": "ood_family", "night_test_ood_seed": "ood_seed",
         "night_branch": "branch"}
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 777
DRAW = sys.argv[2] if len(sys.argv) > 2 else "mine"
B = 10_000

R = pd.read_csv(f"{V}/heldout_rows.csv", low_memory=False)
assert len(R) == 2338 and R.y3.sum() == 156
y = R.y3.values.astype(int)
n = len(R)

# ------------------------------------------------------------------ predictors (frozen files / own refit / zero-shot)
def load_file(path):
    P = pd.read_csv(path)[["run", "round", "score"]]
    assert not P.duplicated(["run", "round"]).any()
    return P

def load_zs(variant):
    P = pd.read_csv(f"{LLM}/{variant}/snapshots.csv", usecols=["episode_id", "t", "zs_tip"])
    P = P.rename(columns={"episode_id": "run", "t": "round", "zs_tip": "score"})
    assert not P.duplicated(["run", "round"]).any()
    return P

SRC = {
    "clock": ("file", f"{V}/preds/refit/hgb_clock.csv"),
    "bag+graph": ("file", f"{V}/preds/refit/hgb_bag+graph.csv"),
    "zs:pairwise": ("zs", "pairwise"),
    "zs:global_full": ("zs", "global_full"),
    "gnn5": ("file", f"{V}/preds/eval/cloud_final_gnn.csv"),
    "hybrid": ("file", f"{V}/preds/eval/cloud_final.csv"),
    "tab_mem": ("file", f"{V}/preds/eval/hgb_bag+graph+mem__allsplits.csv"),
    "edge": ("file", f"{V}/preds/eval/edge_monitor_top3__allsplits.csv"),
    "zs:global_window": ("zs", "global_window"),
    "zs:agent": ("zs", "agent"),
    "oracle": ("file", f"{V}/preds/refit/oracle_risk+clock.csv"),
}
SC = {}
cover = {}
for k, (kind, src) in SRC.items():
    P = load_file(src) if kind == "file" else load_zs(src)
    d = R[["run", "round"]].merge(P, on=["run", "round"], how="left")
    assert len(d) == n
    SC[k] = d.score.values.astype(float)
    cover[k] = int(np.isnan(SC[k]).sum())
print("missing/NaN per predictor on the 2338 rows:", cover)
assert all(v == 0 for v in cover.values())

# ------------------------------------------------------------------ strata
rtc = R.rounds_to_cut.values
def rtc_bin(x):
    # pd.cut(x, [-99, -9, -5, -1, 3, 99]) right-closed: (-99,-9], (-9,-5], (-5,-1], (-1,3], (3,99]
    return np.select([x <= -9, x <= -5, x <= -1, x <= 3], [0, 1, 2, 3], 4)
RB = rtc_bin(rtc)
chk = pd.cut(pd.Series(rtc), [-99, -9, -5, -1, 3, 99], labels=False).values
assert (chk == RB).all()
rnd = R["round"].values
HB = np.full(n, -1)
for i, (a, b) in enumerate(zip((1, 6, 11, 16, 21, 26), (6, 11, 16, 21, 26, 31))):
    HB[(rnd >= a) & (rnd < b)] = i
assert (HB >= 0).all()
cfgs = np.array(sorted(R.cfg.unique()))
C = len(cfgs)
gi = pd.Series(range(C), index=cfgs)[R.cfg.values].values
split = R.split.values

# ------------------------------------------------------------------ full-sample statistics (reference: sklearn)
def auc(yy, ss):
    return roc_auc_score(yy, ss) if 0 < yy.sum() < len(yy) else np.nan

def tm_plan(yy, ss, bb):
    num = den = 0.0
    for b in np.unique(bb):
        m = bb == b
        p1, p0 = yy[m].sum(), (1 - yy[m]).sum()
        if p1 and p0:
            num += p1 * p0 * roc_auc_score(yy[m], ss[m]); den += p1 * p0
    return num / den if den else np.nan

def tm_harness(yy, ss, hb):
    num = den = 0.0
    for b in np.unique(hb):
        m = hb == b
        if len(np.unique(yy[m])) == 2:
            w = yy[m].sum(); num += w * roc_auc_score(yy[m], ss[m]); den += w
    return num / den if den else np.nan

STAT = {"pooled": lambda m, s: auc(y[m], s[m]),
        "tm_plan": lambda m, s: tm_plan(y[m], s[m], RB[m]),
        "tm_harness": lambda m, s: tm_harness(y[m], s[m], HB[m])}
ALL = np.ones(n, bool)
full = {k: {st: f(ALL, s) for st, f in STAT.items()} for k, s in SC.items()}
persplit = {k: {SHORT[sp]: {st: f(split == sp, s) for st, f in STAT.items()} for sp in HELD} for k, s in SC.items()}

# ------------------------------------------------------------------ bootstrap engine (own)
def class_counts(s, mask):
    """per-config x tie-group counts of positives / negatives inside mask; groups sorted ascending by score."""
    u, inv = np.unique(s[mask], return_inverse=True)
    G = len(u)
    yy, cc = y[mask], gi[mask]
    Np = np.zeros((C, G)); Nn = np.zeros((C, G))
    np.add.at(Np, (cc[yy == 1], inv[yy == 1]), 1.0)
    np.add.at(Nn, (cc[yy == 0], inv[yy == 0]), 1.0)
    return Np, Nn

def wauc_parts(K, Np, Nn):
    Pw = K @ Np; Nw = K @ Nn
    below = np.cumsum(Nw, axis=1) - Nw
    num = (Pw * (below + 0.5 * Nw)).sum(1)
    return num, Pw.sum(1), Nw.sum(1)

def boot_stats(K, s):
    out = {}
    num, P, N = wauc_parts(K, *class_counts(s, ALL))
    with np.errstate(invalid="ignore", divide="ignore"):
        out["pooled"] = np.where(P * N > 0, num / (P * N), np.nan)
    nu = np.zeros(len(K)); de = np.zeros(len(K))
    for b in range(5):
        num, P, N = wauc_parts(K, *class_counts(s, RB == b))
        nu += num; de += P * N              # pairs-weighted: w_b * AUROC_b = num_b
    with np.errstate(invalid="ignore", divide="ignore"):
        out["tm_plan"] = np.where(de > 0, nu / de, np.nan)
    nu = np.zeros(len(K)); de = np.zeros(len(K))
    for b in range(6):
        num, P, N = wauc_parts(K, *class_counts(s, HB == b))
        ok = (P > 0) & (N > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            a = np.where(ok, num / np.where(ok, P * N, 1), 0.0)
        nu += np.where(ok, P * a, 0.0); de += np.where(ok, P, 0.0)   # positive-weighted
    with np.errstate(invalid="ignore", divide="ignore"):
        out["tm_harness"] = np.where(de > 0, nu / de, np.nan)
    return out

# multiplicity matrix
if DRAW == "theirs":
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, C, size=(B, C))
else:
    rng = np.random.default_rng(SEED)
    idx = np.stack([rng.choice(C, C, replace=True) for _ in range(B)])
K = np.zeros((B, C))
for j in range(C):
    K[:, j] = (idx == j).sum(1)
assert (K.sum(1) == C).all()

# sanity: engine == sklearn on the full sample and on 5 materialised resamples
ones = np.ones((1, C))
for k in ("hybrid", "zs:pairwise", "clock"):
    e = boot_stats(ones, SC[k])
    for st in STAT:
        assert abs(e[st][0] - full[k][st]) < 1e-12, (k, st, e[st][0], full[k][st])
for r in range(5):
    rows = np.concatenate([np.where(gi == c)[0] for c in idx[r]])
    for k in ("bag+graph", "zs:global_full"):
        s = SC[k]
        e = boot_stats(K[r:r + 1], s)
        ref = {"pooled": auc(y[rows], s[rows]), "tm_plan": tm_plan(y[rows], s[rows], RB[rows]),
               "tm_harness": tm_harness(y[rows], s[rows], HB[rows])}
        for st in STAT:
            assert abs(e[st][0] - ref[st]) < 1e-10, (r, k, st, e[st][0], ref[st])
print("engine check vs sklearn (full sample + 5 materialised resamples): OK")

BS = {}
for k, s in SC.items():
    parts = [boot_stats(K[i:i + 1000], s) for i in range(0, B, 1000)]
    BS[k] = {st: np.concatenate([p[st] for p in parts]) for st in STAT}

def pval(d):
    d = d[~np.isnan(d)]
    return float(min(1.0, max(2 * min((d <= 0).mean(), (d >= 0).mean()), 1.0 / len(d))))

def ci(v):
    v = v[~np.isnan(v)]
    return [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))]

FAM = [("a1", "bag+graph", "clock", "tm_plan"), ("a2", "zs:pairwise", "clock", "tm_plan"),
       ("a3", "zs:global_full", "clock", "tm_plan"), ("a4", "gnn5", "clock", "tm_plan"),
       ("a5", "hybrid", "clock", "tm_plan"), ("b1", "gnn5", "bag+graph", "pooled"),
       ("b2", "hybrid", "bag+graph", "pooled"), ("b3", "zs:pairwise", "bag+graph", "pooled"),
       ("b4", "zs:pairwise", "gnn5", "pooled"), ("b5", "zs:pairwise", "hybrid", "pooled"),
       ("b6", "zs:global_full", "bag+graph", "pooled")]
res = {"seed": SEED, "draw": DRAW, "B": B, "full": full, "persplit": persplit, "ci": {}, "family": []}
for k in SC:
    res["ci"][k] = {st: ci(BS[k][st]) for st in STAT}
for lab_, a, b, st in FAM:
    d = BS[a][st] - BS[b][st]
    est = full[a][st] - full[b][st]
    sp = {SHORT[x]: persplit[a][SHORT[x]][st] - persplit[b][SHORT[x]][st] for x in HELD}
    same = int(sum(np.sign(v) == np.sign(est) for v in sp.values()))
    res["family"].append({"id": lab_, "cmp": f"{a} - {b}", "stat": st, "est": est, "ci": ci(d), "p": pval(d),
                          "n_valid": int((~np.isnan(d)).sum()), "split": sp, "same_sign": same})
# Holm (step-down, monotone)
ps = np.array([f["p"] for f in res["family"]])
o = np.argsort(ps)
adj = np.empty_like(ps)
run = 0.0
for r, i in enumerate(o):
    run = max(run, min(1.0, (len(ps) - r) * ps[i]))
    adj[i] = run
for f, h in zip(res["family"], adj):
    f["p_holm"] = float(h)
# sensitivity: family (a) with harness tAUROC
res["sens_harness"] = []
for lab_, a, b, st in FAM[:5]:
    d = BS[a]["tm_harness"] - BS[b]["tm_harness"]
    est = full[a]["tm_harness"] - full[b]["tm_harness"]
    sp = {SHORT[x]: persplit[a][SHORT[x]]["tm_harness"] - persplit[b][SHORT[x]]["tm_harness"] for x in HELD}
    res["sens_harness"].append({"id": lab_, "cmp": f"{a} - {b}", "est": est, "ci": ci(d), "p": pval(d), "split": sp})

json.dump(res, open(f"{V}/out_main_{DRAW}_{SEED}.json", "w"), indent=1)

print(f"\n=== seed {SEED}, draws {DRAW}, B {B}")
print(f"{'predictor':18s} {'pooled [CI]':26s} {'tm_plan [CI]':26s} {'tm_harness [CI]':26s} | per split pooled AUROC")
for k in SC:
    f, c = full[k], res["ci"][k]
    print(f"{k:18s} " + " ".join(f"{f[st]:.3f} [{c[st][0]:.3f}, {c[st][1]:.3f}]   " for st in STAT) + "| " +
          " ".join(f"{persplit[k][s]['pooled']:.3f}" for s in SHORT.values()))
print("\nper-split plan time-matched:")
for k in SC:
    print(f"  {k:18s} " + " / ".join(f"{persplit[k][s]['tm_plan']:.3f}" for s in SHORT.values()))
print("\nprimary family:")
for f in res["family"]:
    print(f"  {f['id']} {f['cmp']:28s} {f['stat']:8s} {f['est']:+.3f} [{f['ci'][0]:+.3f}, {f['ci'][1]:+.3f}] p {f['p']:.4f}"
          f" holm {f['p_holm']:.4f}  splits " + " ".join(f"{v:+.4f}" for v in f["split"].values()) +
          f"  same {f['same_sign']}/4  valid {f['n_valid']}")
print("\nsensitivity, family (a) with harness tAUROC:")
for f in res["sens_harness"]:
    print(f"  {f['id']} {f['cmp']:28s} {f['est']:+.3f} [{f['ci'][0]:+.3f}, {f['ci'][1]:+.3f}] p {f['p']:.4f}  splits " +
          " ".join(f"{v:+.3f}" for v in f["split"].values()))
