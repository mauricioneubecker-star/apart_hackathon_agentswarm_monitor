import sys; sys.path.insert(0, '.')
import numpy as np
from mhlib import load, mh_acc, summarize, fmt, strata_keys
for w in (3,):
    D = load(w); K = strata_keys(D)
    Y, E, P, dm = D["Y"], D["E_dir"], D["P_dir"], D["dm_any"] == 1
    allm = np.ones(len(Y), bool)
    print(f"===== w={w}")
    print("prevalence: NC_same", D["NC_same"].mean().round(4), "NC_next", D["NC_next"].mean().round(4), "E_rev", D["E_rev"].mean().round(4))
    print("corr(E_dir, NC_same) =", np.corrcoef(E, D["NC_same"])[0, 1].round(3), "; P(NC_same | E_dir=1) =", D["NC_same"][E == 1].mean().round(3), "P(NC_same|E=0)=", D["NC_same"][E == 0].mean().round(4))
    for nm in ("NC_same", "NC_same_s", "NC_next", "E_rev"):
        print(f"--- {nm}")
        print("   all rows           :", fmt(summarize(mh_acc(D, allm, D[nm], K))))
        print("   all rows, E_dir=0  :", fmt(summarize(mh_acc(D, E == 0, D[nm], K))))
        print("   dm>0               :", fmt(summarize(mh_acc(D, dm, D[nm], K))))
        print("   dm>0, E_dir=0      :", fmt(summarize(mh_acc(D, dm & (E == 0), D[nm], K))))
    print("--- E_dir among NC_same=0 (all rows):", fmt(summarize(mh_acc(D, D['NC_same'] == 0, E, K))))
    print("--- E_dir among NC_same=0 (dm>0):    ", fmt(summarize(mh_acc(D, dm & (D['NC_same'] == 0), E, K))))
    # dm received in round t at all (any sender) as negative control for 'being talked to'
