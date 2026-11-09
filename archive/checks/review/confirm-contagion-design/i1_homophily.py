"""Issue 1: does the placebo react to homophily? Zero-contagion simulation on the real DM tensor:
latent propensity z = eps + lam * mean_{DM partners} eps (partners = anyone with a direct msg either way in the run),
hazard_a,t = 1 - exp(-H(run,t,stuck) * exp(beta z_a) / mean_run(exp(beta z))), H from the observed per-stratum hazard.
beta = 0 is the pure iid null. Prints mean MH OR of E_dir / P_dir (all rows and dm>0) per setting."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, load, mh_or  # noqa: E402

runs = load()
rng = np.random.default_rng(99)
haz, adj = [], []
for o in runs:
    R, f, ins, st = o["R"], o["f"], o["instructed"], o["stuck"]
    h = np.zeros((2, R + 2))
    for s in (0, 1):
        m = (~ins) & (st == s)
        for t in range(1, R + 1):
            atr = m & (f >= t)
            if atr.sum():
                h[s, t] = ((f == t) & m).sum() / atr.sum()
    haz.append(-np.log(np.clip(1 - h, 1e-9, 1)))
    A = (o["D"].sum(-1) > 0)
    A = (A | A.T).astype(float)
    np.fill_diagonal(A, 0)
    deg = A.sum(1, keepdims=True)
    adj.append(np.divide(A, np.maximum(deg, 1)))


def draw(beta, lam):
    out = []
    for o, H, An in zip(runs, haz, adj):
        N, R = len(o["ids"]), o["R"]
        eps = rng.standard_normal(N)
        z = eps + lam * An @ eps
        z = (z - z.mean()) / (z.std() + 1e-9)
        m = np.exp(beta * z)
        m = m / m[~o["instructed"]].mean()
        f = o["f"].copy()
        for a in np.flatnonzero(~o["instructed"]):
            s = int(o["stuck"][a])
            p = 1 - np.exp(-H[s, 1:R + 1] * m[a])
            u = rng.random(R)
            hit = np.flatnonzero(u < p)
            f[a] = hit[0] + 1 if len(hit) else 99
        out.append(f)
    return out


def stats(rows):
    dm = rows["dm"] == 1
    return [mh_or(rows, rows["E_dir"]), mh_or(rows, rows["E_dir"], dm), mh_or(rows, rows["P_dir"]), mh_or(rows, rows["P_dir"], dm),
            float(rows["Y"].sum())]


NS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
obs = stats(all_rows(runs))
print(f"observed: E_all {obs[0]:.2f} E_dm {obs[1]:.2f} P_all {obs[2]:.2f} P_dm {obs[3]:.2f} adoptions {obs[4]:.0f}")
for beta, lam in ((0, 0), (1.0, 1.0), (1.5, 2.0), (2.0, 3.0), (2.5, 3.0)):
    S = np.array([stats(all_rows(runs, f_over=draw(beta, lam))) for _ in range(NS)])
    mu = np.nanmean(S, 0)
    lo, hi = np.nanpercentile(S, 2.5, 0), np.nanpercentile(S, 97.5, 0)
    print(f"beta {beta} lam {lam}: E_all {mu[0]:.2f} [{lo[0]:.2f},{hi[0]:.2f}]  E_dm {mu[1]:.2f} [{lo[1]:.2f},{hi[1]:.2f}]  "
          f"P_all {mu[2]:.2f} [{lo[2]:.2f},{hi[2]:.2f}]  P_dm {mu[3]:.2f} [{lo[3]:.2f},{hi[3]:.2f}]  adoptions {mu[4]:.0f}")
    sys.stdout.flush()
