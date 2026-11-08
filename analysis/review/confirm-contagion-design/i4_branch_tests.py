"""Issue 4: inference for the 8 paired branch configs (numbers read from labels.json, not from contagion.json)."""
import glob
import itertools
import json
import os

import numpy as np
from scipy import stats

RUNS = "/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night"
data = {}
for cdir in sorted(glob.glob(os.path.join(RUNS, "core-night_branch-*"))):
    cfg = os.path.basename(cdir)[-6:]
    v = {}
    for arm, sub in (("control", "rep0"), ("inject", "rep0-inject_issue_comment"), ("fake", "rep0-fake_authority")):
        L = json.load(open(os.path.join(cdir, sub, "labels.json")))
        br = 5
        v[arm] = (sum(1 for r in L["first_violation_round"].values() if r > br), bool(L["tipped"]))
    data[cfg] = v


def signflip_p(d):
    d = np.asarray(d, float)
    obs = abs(d.mean())
    null = [abs((np.array(s) * d).mean()) for s in itertools.product([1, -1], repeat=len(d))]
    return float(np.mean(np.array(null) >= obs - 1e-12))


rng = np.random.default_rng(0)
pvals = {}
for arm in ("inject", "fake"):
    c = np.array([data[k]["control"][0] for k in data])
    a = np.array([data[k][arm][0] for k in data])
    d = a - c
    pos, neg = int((d > 0).sum()), int((d < 0).sum())
    p_sf = signflip_p(d)
    p_sign = stats.binomtest(pos, pos + neg, 0.5).pvalue
    p_wil = stats.wilcoxon(d, zero_method="wilcox", alternative="two-sided", method="exact").pvalue if (d != 0).sum() > 0 else None
    loo = {k: signflip_p(np.delete(d, i)) for i, k in enumerate(data)}
    bs_md, bs_ratio = [], []
    for _ in range(20000):
        idx = rng.integers(0, len(d), len(d))
        bs_md.append(d[idx].mean())
        if c[idx].mean() > 0:
            bs_ratio.append(a[idx].mean() / c[idx].mean())
    tc = np.array([data[k]["control"][1] for k in data]); ta = np.array([data[k][arm][1] for k in data])
    up, down = int((ta & ~tc).sum()), int((~ta & tc).sum())
    p_mcn = stats.binomtest(up, up + down, 0.5).pvalue if up + down else 1.0
    pvals[arm] = p_sf
    print(f"== {arm}: control {c.tolist()} arm {a.tolist()} diff {d.tolist()}")
    print(f"   mean control {c.mean():.3f} arm {a.mean():.3f} diff {d.mean():.3f}; ratio of means {a.mean()/c.mean():.2f}")
    print(f"   + {pos} / - {neg} / 0 {int((d==0).sum())}; exact sign-flip (mean) p = {p_sf:.4f}; plain sign test p = {p_sign:.4f}; exact Wilcoxon p = {p_wil:.4f}")
    print(f"   bootstrap(configs) mean diff 95% [{np.percentile(bs_md,2.5):.2f}, {np.percentile(bs_md,97.5):.2f}]; ratio 95% [{np.percentile(bs_ratio,2.5):.2f}, {np.percentile(bs_ratio,97.5):.2f}]")
    print(f"   t-interval mean diff: {stats.t.interval(0.95, len(d)-1, loc=d.mean(), scale=d.std(ddof=1)/np.sqrt(len(d)))}")
    print(f"   leave-one-config-out sign-flip p: { {k: round(v,4) for k,v in loo.items()} }")
    print(f"   tipping: control {int(tc.sum())}/8 arm {int(ta.sum())}/8, flips up {up} down {down}, exact McNemar p = {p_mcn:.3f}")
ps = sorted(pvals.items(), key=lambda x: x[1])
m = len(ps)
adj, prev = {}, 0
for i, (k, p) in enumerate(ps):
    prev = max(prev, min(1, (m - i) * p))
    adj[k] = prev
print("Holm-adjusted sign-flip p over the 2 arms:", adj)
