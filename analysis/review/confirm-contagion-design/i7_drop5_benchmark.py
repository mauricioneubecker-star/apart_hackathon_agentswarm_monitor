"""Issue 7 side check: what does 'drop the 5 most influential configs' give when the effect is HOMOGENEOUS by
construction (simulated contagion with hazard multiplier k=2 on every config, real DM tensor)?"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, load, mh_parts  # noqa: E402
import i1_contagion_sim as cs  # noqa: E402  (reuses its draw(); importing re-runs nothing heavy beyond setup)

runs = cs.runs
out = []
for _ in range(25):
    rows = all_rows(runs, f_over=cs.draw(2.0))
    u, M = mh_parts(rows, rows["E_dir"], rows["dm"] == 1)
    OR = M[:, 0].sum() / M[:, 1].sum()
    c = M[:, 0] - OR * M[:, 1]
    keep = np.ones(len(M), bool); keep[np.argsort(-c)[:5]] = False
    out.append((OR, M[keep, 0].sum() / M[keep, 1].sum(), len(M)))
out = np.array(out)
print(f"homogeneous k=2: full OR median {np.median(out[:,0]):.2f}; after dropping top-5 contributors median {np.median(out[:,1]):.2f} "
      f"[{np.percentile(out[:,1],5):.2f}, {np.percentile(out[:,1],95):.2f}]; ratio drop5/full median {np.median(out[:,1]/out[:,0]):.2f}; configs {np.median(out[:,2]):.0f}")
