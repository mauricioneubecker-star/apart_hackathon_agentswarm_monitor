"""Issue 1 side check: what does the placebo do under TRUE contagion? Sequential simulation on the real DM tensor:
hazard_a,t = 1-exp(-H(run,t,stuck) * k^{X_a,t}), X_a,t = 1 if some agent who DMed a in rounds t-3..t-1 has violated
by t-1 (whether or not before sending). k=1 is the iid null. Instructed agents keep their observed rounds."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, load, mh_or, win_any  # noqa: E402

runs = load()
rng = np.random.default_rng(5)
haz = []
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
WDs = [win_any(o["D"], 3, o["R"]) for o in runs]   # [s, a, t]


def draw(k):
    out = []
    for o, H, WD in zip(runs, haz, WDs):
        R = o["R"]
        f = np.where(o["instructed"], o["f"], 99)
        un = np.flatnonzero(~o["instructed"])
        for t in range(1, R + 1):
            atr = un[f[un] == 99]
            if len(atr) == 0:
                break
            viol = f <= t - 1
            X = (WD[:, atr, t] & viol[:, None]).any(0)
            p = 1 - np.exp(-H[o["stuck"][atr].astype(int), t] * np.where(X, k, 1.0))
            hit = rng.random(len(atr)) < p
            f[atr[hit]] = t
        out.append(f)
    return out


def stats(rows):
    dm = rows["dm"] == 1
    return [mh_or(rows, rows["E_dir"]), mh_or(rows, rows["E_dir"], dm), mh_or(rows, rows["P_dir"]), mh_or(rows, rows["P_dir"], dm), rows["Y"].sum()]


if __name__ == "__main__":
  for k in (1.0, 2.0, 4.0):
      S = np.array([stats(all_rows(runs, f_over=draw(k))) for _ in range(40)])
      mu = np.nanmedian(S, 0)
      print(f"k={k}: E_all {mu[0]:.2f} E_dm {mu[1]:.2f} P_all {mu[2]:.2f} P_dm {mu[3]:.2f} (P_dm 2.5-97.5%: {np.nanpercentile(S[:,3],2.5):.2f}-{np.nanpercentile(S[:,3],97.5):.2f}) adoptions {mu[4]:.0f}")
      sys.stdout.flush()
