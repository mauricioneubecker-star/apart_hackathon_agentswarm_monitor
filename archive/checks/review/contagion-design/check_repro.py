import sys; sys.path.insert(0, '.')
import numpy as np
from mhlib import load, mh_acc, summarize, fmt
for w in (3, 1, 5):
    D = load(w)
    allm = np.ones(len(D["Y"]), bool)
    dm = D["dm_any"] == 1
    print(f"--- w={w}")
    for k in ("E_dir", "E_any", "E_mech", "P_dir"):
        print(f"  all  {k:7s}", fmt(summarize(mh_acc(D, allm, D[k]))))
    for k in ("E_dir", "E_mech", "P_dir"):
        print(f"  dm>0 {k:7s}", fmt(summarize(mh_acc(D, dm, D[k]))))
