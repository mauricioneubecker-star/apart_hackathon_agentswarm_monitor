import glob, json, os, sys, itertools
from pathlib import Path
import numpy as np
from scipy import stats
sys.path.insert(0, '/Users/mauricio/sim_local/apart_ana/sim_dataset/runner')
from labels import read_jsonl
RD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night'
B = json.load(open('branch_check.json'))
# direct vs indirect: injection text seen strictly before own first violation
direct_tot = indirect_tot = 0
rows = []
for sid, v in B.items():
    d = os.path.join(RD, sid, 'rep0-inject_issue_comment')
    ev = read_jsonl(Path(d) / 'events.jsonl')
    seen = {}
    for e in ev:
        if (e['type'] == 'notice' and 'injection' in str(e.get('source', ''))) or (e['type'] == 'tool' and e.get('tool') == 'list_issues' and e['round'] >= 6):
            seen.setdefault(e['agent'], e['round'])
    fa = v['arms']['inject_issue_comment']['first_after']
    dct = sum(1 for a, r in fa.items() if a in seen and seen[a] < r)
    rows.append((sid, len(fa), dct, v['arms']['control']['new_after']))
    direct_tot += dct; indirect_tot += len(fa) - dct
for r in rows: print(f"{r[0]}: inject new {r[1]:2d}, saw injection before own violation {r[2]:2d}; control new {r[3]:2d}")
print("total inject-arm new violators:", direct_tot + indirect_tot, "saw injection text before violating:", direct_tot)
def tests(c, t, label):
    c, t = np.array(c, float), np.array(t, float); dlt = t - c; n = len(dlt)
    flips = np.array(list(itertools.product([1, -1], repeat=n)))
    null = (flips * dlt).mean(1)
    p_flip = np.mean(np.abs(null) >= abs(dlt.mean()) - 1e-12)
    npos, nneg = int((dlt > 0).sum()), int((dlt < 0).sum())
    p_sign = stats.binomtest(npos, npos + nneg, 0.5).pvalue
    p_wil = stats.wilcoxon(t, c, alternative='two-sided', method='exact', zero_method='wilcox').pvalue if (dlt != 0).sum() >= 1 else np.nan
    # Hodges-Lehmann + exact sign-flip CI (inversion, 95%) on the mean difference: shift values s where flip test p>=0.05
    grid = np.arange(-15, 15.01, 0.05); keep = []
    for s in grid:
        dd = dlt - s; nul = (flips * dd).mean(1)
        if np.mean(np.abs(nul) >= abs(dd.mean()) - 1e-12) > 0.05: keep.append(s)
    rng = np.random.default_rng(0); rat = []
    for _ in range(20000):
        i = rng.integers(0, n, n)
        if c[i].sum() > 0: rat.append(t[i].sum() / c[i].sum())
    # leave-one-out
    loo = []
    for j in range(n):
        dj = np.delete(dlt, j); fj = np.array(list(itertools.product([1, -1], repeat=n - 1)))
        loo.append(float(np.mean(np.abs((fj * dj).mean(1)) >= abs(dj.mean()) - 1e-12)))
    print(f"{label}: diffs {dlt.astype(int).tolist()} mean {dlt.mean():.3f} | ratio of means {t.mean()/c.mean():.2f} boot95 [{np.percentile(rat,2.5):.2f}, {np.percentile(rat,97.5):.2f}]"
          f" | p_signflip {p_flip:.4f} p_sign(7/8-type) {p_sign:.4f} p_wilcoxon {p_wil:.4f} | signflip-inverted 95% CI mean diff [{min(keep):.2f}, {max(keep):.2f}]"
          f" | leave-one-out signflip p range [{min(loo):.3f}, {max(loo):.3f}]")
    return p_flip
C = [v['arms']['control']['new_after'] for v in B.values()]
I = [v['arms']['inject_issue_comment']['new_after'] for v in B.values()]
F = [v['arms']['fake_authority']['new_after'] for v in B.values()]
p1 = tests(C, I, "inject vs control"); p2 = tests(C, F, "fake vs control")
ps = sorted([p1, p2]); print("Holm-adjusted: inject", round(min(1, 2 * p1) if p1 <= p2 else max(min(1, 2 * p2), p1), 4), "fake", round(max(min(1, 2 * min(p1, p2)), max(p1, p2)), 4))
# tipping: McNemar exact on discordant pairs
for nm, X in (("inject", I), ("fake", F)):
    tc = [v['arms']['control']['tipped'] for v in B.values()]; ta = [v['arms']['inject_issue_comment' if nm == 'inject' else 'fake_authority']['tipped'] for v in B.values()]
    up = sum(1 for a, b in zip(tc, ta) if b and not a); dn = sum(1 for a, b in zip(tc, ta) if a and not b)
    print(f"tipping {nm}: up {up} down {dn} exact McNemar p = {stats.binomtest(up, up + dn, 0.5).pvalue if up + dn else 1:.3f}")
