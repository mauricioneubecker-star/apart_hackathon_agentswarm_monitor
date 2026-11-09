# Descriptive: ever-violated share by ticket situation and shortcut category (236 night control runs, uninstructed agents).
import glob, json, os
from collections import Counter
runs = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
scen = "/Users/mauricio/sim_local/apart_vx/sim_dataset/dataset/scenarios/core"
c = Counter()
for d in sorted(glob.glob(os.path.join(runs, "core-night_*", "rep*"))):
    lp = os.path.join(d, "labels.json")
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_vx" in sid or "-" in rep or not os.path.exists(lp):
        continue
    sc = json.load(open(os.path.join(scen, sid + ".json"))); first = json.load(open(lp))["first_violation_round"]
    cat = str(sc["params"]["category"])[:2]
    for a in sc["population"]:
        if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer"):
            continue
        s = "own_unsolvable" if not a["ticket"]["solvable"] else ("dep_blocked" if a["ticket"].get("blocked_by_unsolvable_dep") else "solvable")
        for k in (cat, "all"):
            c[(k, s, "n")] += 1; c[(k, s, "v")] += a["agent_id"] in first
for k in ("K2", "K4", "all"):
    print(k, " | ".join(f"{s}: {c[(k,s,'v')]}/{c[(k,s,'n')]}={c[(k,s,'v')]/c[(k,s,'n')]:.3f}" for s in ("own_unsolvable", "dep_blocked", "solvable")))
