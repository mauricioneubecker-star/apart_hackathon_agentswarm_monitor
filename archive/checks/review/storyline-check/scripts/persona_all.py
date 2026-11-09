# Descriptive: violation share by persona label among uninstructed agents with an own unsolvable ticket vs solvable (236 night control runs).
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
    for a in sc["population"]:
        if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer"):
            continue
        s = "own_unsolvable" if not a["ticket"]["solvable"] else ("dep" if a["ticket"].get("blocked_by_unsolvable_dep") else "solvable")
        c[(a.get("persona"), s, "n")] += 1; c[(a.get("persona"), s, "v")] += a["agent_id"] in first
ps = sorted({k[0] for k in c})
for p in ps:
    o = [f"{s}: {c[(p,s,'v')]}/{c[(p,s,'n')]}={c[(p,s,'v')]/c[(p,s,'n')]:.3f}" if c[(p,s,'n')] else f"{s}: -" for s in ("own_unsolvable", "solvable")]
    print(f"{str(p):18s}", " | ".join(o))
