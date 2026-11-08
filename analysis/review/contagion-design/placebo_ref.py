import sys; sys.path.insert(0, '.')
import numpy as np
from mhlib import load, mh_acc, summarize, fmt, strata_keys
for w in (3, 1, 5):
    D = load(w); K = strata_keys(D)
    Y, E, P, dm = D["Y"], D["E_dir"], D["P_dir"], D["dm_any"] == 1
    print(f"===== w={w}")
    # composition of the dm>0 reference group for P_dir
    ref = dm & (P == 0)
    print(f"dm>0 rows {dm.sum()}, P=1 {int((dm&(P==1)).sum())}, P=0 {int(ref.sum())}; among P=0: E_dir=1 share {E[ref].mean():.3f}"
          f" (n={int((ref&(E==1)).sum())}); crude adopt P=0&E=1 {Y[ref&(E==1)].mean():.4f}, P=0&E=0 {Y[ref&(E==0)].mean():.4f}, P=1 {Y[dm&(P==1)].mean():.4f}")
    refE = dm & (E == 0)
    print(f"   among E_dir=0 (dm>0): P=1 share {P[refE].mean():.3f}")
    # mutually exclusive categories within dm>0
    Eo, Po, Bo, Ne = (E == 1) & (P == 0), (P == 1) & (E == 0), (E == 1) & (P == 1), (E == 0) & (P == 0)
    print(f"   cells dm>0: E-only {int((dm&Eo).sum())} ({int(Y[dm&Eo].sum())} ad), P-only {int((dm&Po).sum())} ({int(Y[dm&Po].sum())} ad), "
          f"both {int((dm&Bo).sum())} ({int(Y[dm&Bo].sum())} ad), neither {int((dm&Ne).sum())} ({int(Y[dm&Ne].sum())} ad)")
    print("  P_dir vs neither (dm>0, E_dir=1 rows dropped):", fmt(summarize(mh_acc(D, dm & (E == 0), P, K))))
    print("  E_dir vs neither (dm>0, P_dir=1 rows dropped):", fmt(summarize(mh_acc(D, dm & (P == 0), E, K))))
    # strict reference: DMs only from never-violators (N_dir) -- no E, no P, no between
    Nb = (D["P_between"] == 1)
    strict_ref = dm & (E == 0) & (P == 0) & (~Nb)
    for name, ex in (("P-only", Po), ("E-only", Eo), ("between-only", Nb & (E == 0) & (P == 0))):
        m = strict_ref | (dm & ex)
        print(f"  {name:12s} vs DMs-only-from-never-violators:", fmt(summarize(mh_acc(D, m, ex.astype(float), K))))
    # unrestricted: P_dir excluding E rows
    allm = np.ones(len(Y), bool)
    print("  [all rows] P_dir among E_dir=0:", fmt(summarize(mh_acc(D, E == 0, P, K))))
    print("  [all rows] E_dir among P_dir=0:", fmt(summarize(mh_acc(D, P == 0, E, K))))
