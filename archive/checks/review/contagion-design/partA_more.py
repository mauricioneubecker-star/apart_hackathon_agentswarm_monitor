import sys, json; sys.path.insert(0, '.')
import numpy as np
from mhlib import load, mh_acc, summarize, fmt, strata_keys
D = load(3); K = strata_keys(D)
Y, E, P, dm = D["Y"], D["E_dir"], D["P_dir"], D["dm_any"] == 1
allm = np.ones(len(Y), bool)
cat = np.array(["K2" if "-K2-" in c else "K4" for c in D["cfg"]])
print("== per category with bootstrap CI")
for c in ("K2", "K4"):
    print(c, "all  E_dir", fmt(summarize(mh_acc(D, cat == c, E, K))))
    print(c, "dm>0 E_dir", fmt(summarize(mh_acc(D, (cat == c) & dm, E, K))))
    print(c, "dm>0 P_dir", fmt(summarize(mh_acc(D, (cat == c) & dm, P, K))))
print("== solicited vs unsolicited E_dir (reader had DMed that violator in the 3 rounds before his message)")
sol = D["E_dir_resp"] == 1; uns = (E == 1) & ~sol
print("share of E_dir rows solicited:", round(float(sol[E == 1].mean()), 3), "; reply-to-reader share:", round(float(D['E_dir_reply'][E == 1].mean()), 3))
print("  unsolicited vs unexposed (dm>0, solicited rows dropped):", fmt(summarize(mh_acc(D, dm & ~sol, uns.astype(float), K))))
print("  solicited   vs unexposed (dm>0, unsolicited rows dropped):", fmt(summarize(mh_acc(D, dm & ~uns, sol.astype(float), K))))
print("== reader's own shortcut mention in window (intent) and E_dir")
print("  R_mech among E_dir=1 adopters:", round(float(D['R_mech'][(E == 1) & (Y == 1)].mean()), 3), "; among E_dir=0 adopters:", round(float(D['R_mech'][(E == 0) & (Y == 1)].mean()), 3))
print("  E_dir dm>0 among R_mech=0:", fmt(summarize(mh_acc(D, dm & (D['R_mech'] == 0), E, K))))
print("== placebo content: share of P_dir rows where the future violator named the shortcut:", round(float(D['P_mech'][P == 1].mean()), 3))
print("  P_mech (named shortcut, not yet violated) dm>0:", fmt(summarize(mh_acc(D, dm, D['P_mech'], K))))
print("  P_dir from instructed senders share:", round(float(D['P_instr'][P == 1].mean()), 3), "; E_dir from instructed share:", round(float(D['E_instr'][E == 1].mean()), 3))
org = (E == 1) & (D["E_instr"] == 0)
print("  E_dir organic-senders-only (drop rows exposed only to instructed) dm>0:", fmt(summarize(mh_acc(D, dm & ~((E == 1) & (D['E_instr'] == 1) & ~org), org.astype(float), K))))
print("== leave-one-config-out, dm>0 E_dir")
acc = mh_acc(D, dm, E, K); cf = list(acc); M = np.array([acc[c] for c in cf])
o = M[:, 0].sum() / M[:, 1].sum(); loo = [(M[:, 0].sum() - M[i, 0]) / (M[:, 1].sum() - M[i, 1]) for i in range(len(cf))]
top = sorted(zip(cf, M[:, 0] - o * M[:, 1]), key=lambda x: -x[1])[:5]
print("  OR", round(o, 3), "LOO range", round(min(loo), 3), round(max(loo), 3), "| top contributors (num - OR*den):", [(c, round(v, 2)) for c, v in top])
drop5 = [c for c, _ in top]
keep = ~np.isin(D["cfg"], drop5)
print("  dropping the 5 most influential configs:", fmt(summarize(mh_acc(D, dm & keep, E, K))))
print("== cluster sign-flip randomization test on per-config O-E (dm>0 E_dir, w=3)")
U = M[:, 6]; rng = np.random.default_rng(1)
null = np.array([(U * rng.choice([-1, 1], len(U))).sum() for _ in range(100000)])
print("  configs", len(U), "sum O-E", round(U.sum(), 2), "p two-sided", round(float(np.mean(np.abs(null) >= abs(U.sum()))), 4))
for w in (1, 5):
    Dw = load(w); Kw = strata_keys(Dw); a = mh_acc(Dw, Dw["dm_any"] == 1, Dw["E_dir"], Kw); Uw = np.array([a[c][6] for c in a])
    nw = np.array([(Uw * rng.choice([-1, 1], len(Uw))).sum() for _ in range(100000)])
    print(f"  w={w}: configs {len(Uw)} p two-sided {np.mean(np.abs(nw) >= abs(Uw.sum())):.4f}")
print("== within-stratum exposure permutation (exact conditional, ignores clustering), dm>0 E_dir w=3")
m = dm; k = K[m]; y = Y[m]; e = E[m]; cg = D['cfg'][m]
order = np.argsort(k, kind='stable'); k, y, e = k[order], y[order], e[order]
b = np.flatnonzero(np.r_[True, k[1:] != k[:-1], True])
segs = [(b[i], b[i + 1]) for i in range(len(b) - 1)]
inf = [(s0, s1) for s0, s1 in segs if 0 < e[s0:s1].sum() < s1 - s0 and y[s0:s1].sum() > 0]
def mhor(ee):
    num = den = 0.0
    for s0, s1 in inf:
        ys, es = y[s0:s1], ee[s0:s1]; n = s1 - s0
        a_ = np.sum((es == 1) & (ys == 1)); b_ = np.sum((es == 1) & (ys == 0)); c_ = np.sum((es == 0) & (ys == 1)); d_ = n - a_ - b_ - c_
        num += a_ * d_ / n; den += b_ * c_ / n
    return num / den
obs = mhor(e); cnt = 0; NP = 2000
for _ in range(NP):
    ee = e.copy()
    for s0, s1 in inf: ee[s0:s1] = rng.permutation(ee[s0:s1])
    cnt += mhor(ee) >= obs
print(f"  observed {obs:.3f}; permutation p (one-sided) = {(cnt + 1) / (NP + 1):.4f}")
