"""Independent conditional logistic regression (Breslow ties) on rows from build_rows.py.
Strata (run, t, stuck) as in contagion.py; covariates built here from scenario population + labels.json:
  agent: model, persona, role, tech_lead, carry_over, info_asym, difficulty, DM degree (dm_neighbors, binned)
  dynamic: n direct msgs in window (0,1,2,3+), broadcast reading edge from a violator in window (E_bc),
           any private DM in window, a ticket-graph neighbour (dep / dep owner / dependent) violated before t.
Ridge 0.1 on nuisance coefficients only. CI: cluster bootstrap over configs.

  python clr_own.py rows_w3.npz <runs_night> <scenario_dir> [nboot]
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import minimize

Z = np.load(sys.argv[1])
runs_dir, scen_dir = sys.argv[2], sys.argv[3]
NB = int(sys.argv[4]) if len(sys.argv) > 4 else 200
cfg, run, cat, chan, agent = Z["cfg"], Z["run"], Z["cat"], Z["chan"], Z["agent"]
T, STUCK, Y = Z["t"], Z["stuck"], Z["Y"].astype(float)
n = len(Y)

# ---- agent-level and graph covariates
pop_cache, first_cache = {}, {}
for c in sorted(set(cfg)):
    sc = json.load(open(os.path.join(scen_dir, c + ".json")))
    pop_cache[c] = {a["agent_id"]: a for a in sc["population"]}
for r in sorted(set(run)):
    c, rep = r.split("/")
    L = json.load(open(os.path.join(runs_dir, c, rep, "labels.json")))
    first_cache[r] = L["first_violation_round"]
cats = {k: [] for k in ("model", "persona", "role", "difficulty")}
num = {k: np.zeros(n) for k in ("tech_lead", "carry_over", "info_asym", "deg_hi", "nb_viol")}
for i in range(n):
    a = pop_cache[cfg[i]][agent[i]]
    for k in ("model", "persona", "role"):
        cats[k].append(str(a.get(k)))
    cats["difficulty"].append(str(a["ticket"].get("difficulty")))
    f = a["flags"]
    num["tech_lead"][i] = float(bool(f.get("tech_lead")))
    num["carry_over"][i] = float(bool(f.get("carry_over")))
    num["info_asym"][i] = float(bool(f.get("info_asym")))
    num["deg_hi"][i] = float(len(a.get("dm_neighbors") or []) >= 6)
    tk = a["ticket"]
    pop = pop_cache[cfg[i]]
    nb = set(tk.get("dep_owners") or [])
    fn2owner = {p["ticket"]["function"]: q for q, p in pop.items()}
    nb |= {fn2owner[d] for d in (tk.get("dependents") or []) if d in fn2owner}
    fv = first_cache[run[i]]
    num["nb_viol"][i] = float(any(fv.get(b, 99) < T[i] for b in nb))


def dummies(v):
    v = np.array(v)
    lv = sorted(set(v))
    return np.stack([(v == x).astype(float) for x in lv[1:]], 1) if len(lv) > 1 else np.zeros((len(v), 0))


ndm = np.minimum(Z["ndm"], 3)
COV = np.hstack([dummies(cats[k]) for k in cats] + [num[k][:, None] for k in num] +
                [dummies(ndm), Z["E_bc"][:, None].astype(float), Z["dm_priv_any"][:, None].astype(float)])
skey = np.array([f"{a}|{b}|{c}" for a, b, c in zip(run, T, STUCK)])


def fit(X, y, sid, lam=0.1):
    S = sid.max() + 1
    d_s = np.bincount(sid, weights=y, minlength=S)
    pen = np.full(X.shape[1], lam); pen[0] = 0.0

    def f(b):
        eta = X @ b
        mx = eta.max()
        e = np.exp(eta - mx)
        den = np.bincount(sid, weights=e, minlength=S)
        numr = np.stack([np.bincount(sid, weights=e * X[:, j], minlength=S) for j in range(X.shape[1])], 1)
        ll = (y * eta).sum() - (d_s * (np.log(den) + mx)).sum()
        g = (y[:, None] * X).sum(0) - (d_s[:, None] * numr / den[:, None]).sum(0)
        return -(ll - 0.5 * (pen * b * b).sum()), -(g - pen * b)

    return minimize(f, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x


def run_clr(mask, x, nboot=NB, seed=0):
    m = mask.copy()
    # keep strata with >= 1 event
    _, sid_all = np.unique(skey[m], return_inverse=True)
    ev = np.bincount(sid_all, weights=Y[m])
    idx = np.flatnonzero(m)[ev[sid_all] > 0]
    X = np.hstack([x[idx, None].astype(float), COV[idx]])
    keep_col = np.r_[True, X[:, 1:].std(0) > 0]
    X = X[:, keep_col]
    y = Y[idx]
    _, sid = np.unique(skey[idx], return_inverse=True)
    b0 = fit(X, y, sid)[0]
    cg = cfg[idx]
    uc = np.unique(cg)
    rows_of = {c: np.flatnonzero(cg == c) for c in uc}
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        pick = rng.choice(uc, len(uc), replace=True)
        ii, ss, off = [], [], 0
        for c in pick:
            r = rows_of[c]
            _, inv = np.unique(sid[r], return_inverse=True)
            ii.append(r); ss.append(inv + off); off += inv.max() + 1
        ii = np.concatenate(ii); ss = np.concatenate(ss)
        if X[ii, 0].std() == 0:
            continue
        bs.append(fit(X[ii], y[ii], ss)[0])
    bs = np.array(bs)
    return (f"{np.exp(b0):5.2f} [{np.exp(np.percentile(bs, 2.5)):.2f}; {np.exp(np.percentile(bs, 97.5)):.2f}] "
            f"P(OR<=1) {np.mean(bs <= 0):.3f} events {int(y.sum())} exposed events {int(((X[:, 0] == 1) & (y == 1)).sum())}")


ALL = np.ones(n, bool)
DM = Z["dm_any"] == 1
K4, B = cat == "K4", chan == "board"
for g, m in (("pooled", ALL), ("K2", ~K4), ("K4", K4), ("board", B), ("non-board", ~B), ("K2&board", ~K4 & B),
             ("K4&board", K4 & B)):
    for k in ("E_dir", "P_dir"):
        print(f"{g:10s} {k} all : {run_clr(m, Z[k])}", flush=True)
        print(f"{g:10s} {k} dm>0: {run_clr(m & DM, Z[k])}", flush=True)
