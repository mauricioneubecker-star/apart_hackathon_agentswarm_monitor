import sys, json; sys.path.insert(0, '.')
import numpy as np
from mhlib import load, mh_acc, summarize, fmt, strata_keys
SD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/scenarios/core'
D = load(3); K = strata_keys(D)
cfgs = sorted(set(D["cfg"]))
disc = {c: json.load(open(f"{SD}/{c}.json"))["spec"]["shortcut"]["discoverability"] for c in cfgs}
chan = {c: json.load(open(f"{SD}/{c}.json"))["params"]["channels"] for c in cfgs}
dsc = np.array([disc[c] for c in D["cfg"]]); ch = np.array([chan[c] for c in D["cfg"]])
cat = np.array(["K2" if "-K2-" in c else "K4" for c in D["cfg"]])
dm = D["dm_any"] == 1
for cc in ("K2", "K4"):
    for dd in ("exploration", "peers_only"):
        m = (cat == cc) & (dsc == dd)
        if not m.any(): continue
        print(f"{cc} {dd:11s} rows {int(m.sum()):6d} adopt {int(D['Y'][m].sum()):4d} runs {len(set(D['run'][m])):3d}")
        for k in ("E_dir", "P_dir", "E_mech"):
            print(f"    all  {k:6s}", fmt(summarize(mh_acc(D, m, D[k], K))))
            print(f"    dm>0 {k:6s}", fmt(summarize(mh_acc(D, m & dm, D[k], K))))
print("channels:", dict(zip(*np.unique(ch, return_counts=True))))
for cc in ("K2", "K4"):
    for h in sorted(set(ch)):
        m = (cat == cc) & (ch == h)
        print(f"{cc} channels={h:8s}", "dm>0 E_dir", fmt(summarize(mh_acc(D, m & dm, D['E_dir'], K))))
