# Sum committed per-run exposure counts (labels.json) by discoverability x category, night control runs.
import json, os
import pandas as pd
R = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
d = pd.read_csv(os.path.join(R, "_logs", "analysis_runs.csv"))
rows = []
for _, x in d.iterrows():
    L = json.load(open(os.path.join(R, x.cfg, x.rep, "labels.json")))
    r = {"arm": x.arm, "cat": x.category[:2], "disc": x.discoverability, "seed": x.seed_type, "tipped": x.tipped,
         "nv": L["n_violators"], "nvu": L["n_violators_uninstructed"]}
    for k in ("exposure_counts", "exposure_counts_direct", "exposure_counts_advocate", "exposure_counts_feed"):
        c = L.get(k) or {}
        r[k + "_e"] = c.get("exposed", 0); r[k + "_n"] = c.get("considered", 0)
    rows.append(r)
t = pd.DataFrame(rows)
c = t[t.arm == "control"]
def show(g, lab):
    s = g.sum(numeric_only=True)
    f = lambda k: f"{int(s[k+'_e'])}/{int(s[k+'_n'])}={s[k+'_e']/s[k+'_n']:.3f}" if s[k+'_n'] else "n/a"
    print(f"{lab:28s} runs={len(g):3d} viol={int(s.nv):4d} | any {f('exposure_counts')} | direct {f('exposure_counts_direct')} | advocate(any src incl. seeds) {f('exposure_counts_advocate')} | feed {f('exposure_counts_feed')}")
show(c, "control all")
for k, g in c.groupby("disc"): show(g, f"disc={k}")
for k, g in c.groupby(["cat", "disc"]): show(g, f"{k}")
for k, g in c[c.disc == "peers_only"].groupby(["cat", "seed"]): show(g, f"peers_only {k}")
