"""Issue 5: E_dir (and P_dir, E_mech) by exposure window incl. cumulative (all earlier rounds = agent memory 29-30
cycles), with config bootstrap CI and config-level sign-flip p on per-config sum(O-E)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, fmt, load, mh_parts, signflip_cfg, summarize  # noqa: E402

runs = load()
for w in (1, 2, 3, 5, 8, 12, 29):
    rows = all_rows(runs, w=w)
    dm = rows["dm"] == 1
    for k in ("E_dir", "E_mech", "P_dir"):
        for nm, sel in (("all", None), ("dm>0", dm)):
            u, M = mh_parts(rows, rows[k], sel)
            print(f"w={w:2d} {k:6s} {nm:5s}", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
    # the dm>0 restriction itself changes with w: report its size
    print(f"      share of rows with dm>0 in window: {dm.mean():.3f}")
