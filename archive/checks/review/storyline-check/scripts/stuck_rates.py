# Descriptive count: share of agents who ever violated, by ticket situation (night batch only).
import glob, json, os, sys
from collections import Counter
runs = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
scen = "/Users/mauricio/sim_local/apart_vx/sim_dataset/dataset/scenarios/core"
c = Counter()
for d in sorted(glob.glob(os.path.join(runs, "core-night_*", "rep*"))):
    lp = os.path.join(d, "labels.json")
    if not os.path.exists(lp):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_vx" in sid:
        continue
    arm = "control" if "-" not in rep else "arm"
    sc = json.load(open(os.path.join(scen, sid + ".json")))
    L = json.load(open(lp))
    first = L["first_violation_round"]
    tipped = bool(L["tipped"])
    for a in sc["population"]:
        aid = a["agent_id"]
        instr = bool(a["flags"].get("malicious") or a["flags"].get("scripted_pioneer"))
        own_unsolv = not a["ticket"]["solvable"]
        dep = bool(a["ticket"].get("blocked_by_unsolvable_dep"))
        stuck = own_unsolv or dep
        grp = "instructed" if instr else ("stuck_own" if own_unsolv else ("stuck_dep" if dep else "solvable"))
        v = aid in first
        for scope in (arm, "all"):
            c[(scope, grp, "n")] += 1
            c[(scope, grp, "v")] += v
            c[(scope, "stuck_any" if (stuck and not instr) else ("solvable_any" if not instr else "instr_any"), "n")] += 1
            c[(scope, "stuck_any" if (stuck and not instr) else ("solvable_any" if not instr else "instr_any"), "v")] += v
            if tipped:
                c[(scope + "_tipped", grp, "n")] += 1
                c[(scope + "_tipped", grp, "v")] += v
for scope in ("control", "all", "control_tipped", "arm"):
    for grp in ("solvable", "stuck_own", "stuck_dep", "stuck_any", "solvable_any", "instructed"):
        n, v = c[(scope, grp, "n")], c[(scope, grp, "v")]
        if n:
            print(f"{scope:15s} {grp:13s} agents={n:5d} violators={v:5d} share={v/n:.4f}")
