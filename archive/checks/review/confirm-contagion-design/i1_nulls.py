"""Issue 1: what is the null value of the placebo P_dir (and of E_dir)?
 null_iid   : uninstructed agents adopt iid with the observed per-(run, t, stuck) hazard; real DM tensor; instructed f fixed
 null_indep : as null_iid, but sender status (E_dir / P_dir) taken from an INDEPENDENT second draw -> breaks coupling
 shuffle    : permute first-violation rounds among uninstructed adopters within run x stuck (keeps who adopts)
Prints mean and 2.5/97.5% of the simulated MH ORs and the one-sided p of the observed value."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, load, mh_or  # noqa: E402

runs = load()
rng = np.random.default_rng(12345)
NS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
NP = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

# observed per-(run, t, stuck) hazards among uninstructed at-risk agents
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
    haz.append(h)


def draw_iid():
    out = []
    for o, h in zip(runs, haz):
        f = o["f"].copy()
        R = o["R"]
        for a in np.flatnonzero(~o["instructed"]):
            s = int(o["stuck"][a])
            u = rng.random(R + 1)
            fa = 99
            for t in range(1, R + 1):
                if u[t] < h[s, t]:
                    fa = t
                    break
            f[a] = fa
        out.append(f)
    return out


def draw_shuffle():
    out = []
    for o in runs:
        f = o["f"].copy()
        for s in (0, 1):
            idx = np.flatnonzero((~o["instructed"]) & (o["stuck"] == s) & (o["f"] < 99))
            if len(idx) > 1:
                f[idx] = f[rng.permutation(idx)]
        out.append(f)
    return out


cat = np.array([o["cat"][:2] for o in runs])


def stats(rows):
    dm = rows["dm"] == 1
    k4 = cat[rows["run_i"]] == "K4"
    k2 = ~k4
    return {"E_all": mh_or(rows, rows["E_dir"]), "E_dm": mh_or(rows, rows["E_dir"], dm),
            "P_all": mh_or(rows, rows["P_dir"]), "P_dm": mh_or(rows, rows["P_dir"], dm),
            "E_dm_K2": mh_or(rows, rows["E_dir"], dm & k2), "E_dm_K4": mh_or(rows, rows["E_dir"], dm & k4),
            "P_dm_K2": mh_or(rows, rows["P_dir"], dm & k2), "P_dm_K4": mh_or(rows, rows["P_dir"], dm & k4),
            "E_all_K2": mh_or(rows, rows["E_dir"], k2), "E_all_K4": mh_or(rows, rows["E_dir"], k4)}


obs = stats(all_rows(runs))
res = {"observed": obs}


def run_null(name, n, gen):
    sims = []
    for i in range(n):
        sims.append(gen())
    keys = list(obs)
    arr = {k: np.array([s[k] for s in sims]) for k in keys}
    summ = {}
    for k in keys:
        v = arr[k][np.isfinite(arr[k])]
        summ[k] = {"mean": float(np.mean(v)), "median": float(np.median(v)), "lo": float(np.percentile(v, 2.5)),
                   "hi": float(np.percentile(v, 97.5)),
                   "p_le_obs": float((np.sum(v <= obs[k]) + 1) / (len(v) + 1)),
                   "p_ge_obs": float((np.sum(v >= obs[k]) + 1) / (len(v) + 1)), "n": int(len(v))}
    res[name] = summ
    print(f"== {name} (n={n})")
    for k in keys:
        s = summ[k]
        print(f"  {k:9s} obs {obs[k]:.3f} | null mean {s['mean']:.3f} med {s['median']:.3f} [{s['lo']:.3f}, {s['hi']:.3f}]  p(<=obs) {s['p_le_obs']:.4f}  p(>=obs) {s['p_ge_obs']:.4f}")
    sys.stdout.flush()


run_null("null_iid", NS, lambda: stats(all_rows(runs, f_over=draw_iid())))


def indep():
    f_out, f_snd = draw_iid(), draw_iid()
    parts = []
    from core import run_rows
    rws = []
    for i, o in enumerate(runs):
        r = run_rows(o, f=f_snd[i], outcome_f=f_out[i])
        r["run_i"] = np.full(len(r["t"]), i)
        r["cfg"] = np.full(len(r["t"]), o["sid"], dtype=object)
        rws.append(r)
    rows = {k: np.concatenate([p[k] for p in rws]) for k in rws[0]}
    return stats(rows)


run_null("null_indep_sender", NS, indep)
run_null("shuffle_run_stuck", NP, lambda: stats(all_rows(runs, f_over=draw_shuffle())))
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i1_nulls.json"), "w"), indent=1)
