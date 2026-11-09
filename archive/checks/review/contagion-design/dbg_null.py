"""Why is P_dir biased under an iid null? Decompose per stratum: sum(a - E[a]) and check dependence sources."""
import sys; sys.path.insert(0, '.')
import numpy as np
from fastmh import load_cache, prep, run_rows, NEVER
C = load_cache(); P = [prep(r) for r in C]
rng = np.random.default_rng(5)
tot = {"OE_P": 0.0, "OE_E": 0.0, "n": 0}
# one-at-a-time diagnostics: for each at-risk row, is the reader itself a possible 'sender' of P to someone? no.
# Check: is P exposure correlated with the READER's own adoption round through the reader's outgoing-dm pattern?
res = []
for rep in range(40):
    oeP = oeE = 0.0; vP = 0.0
    for p in P:
        f = p["f"].copy()
        for g in (p["stuck"], ~p["stuck"]):
            U = np.flatnonzero(g & ~p["instr"])
            times = f[U][f[U] < NEVER]; q = len(times) / max(1, len(U))
            adopt = rng.random(len(U)) < q
            new = np.full(len(U), NEVER)
            if len(times): new[adopt] = rng.choice(times, adopt.sum(), replace=True)
            f[U] = new
        rows = run_rows(p, f)
        if not len(rows): continue
        m = rows[:, 5] == 1
        t, st, Y, E, Pp = rows[m, 0], rows[m, 1], rows[m, 2], rows[m, 3], rows[m, 4]
        k = t * 2 + st
        for kk in np.unique(k):
            s = k == kk
            n = s.sum(); m1 = Y[s].sum(); n1 = Pp[s].sum(); a = (Y[s] & Pp[s]).sum()
            if n > 1 and m1 > 0 and 0 < n1 < n:
                oeP += a - n1 * m1 / n
    res.append(oeP)
print("mean sum(a - E[a]) for P_dir in dm>0 under iid null over 40 draws:", np.mean(res).round(2), "+-", (np.std(res)/np.sqrt(len(res))).round(2))
