# Descriptive: violation share of persistent-persona vs other uninstructed agents, by ticket situation (236 night control runs).
import glob, json, os
from collections import Counter
runs = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
scen = "/Users/mauricio/sim_local/apart_vx/sim_dataset/dataset/scenarios/core"
c = Counter(); pers_runs = 0; persona_vals = Counter()
for d in sorted(glob.glob(os.path.join(runs, "core-night_*", "rep*"))):
    lp = os.path.join(d, "labels.json")
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_vx" in sid or "-" in rep or not os.path.exists(lp):
        continue
    sc = json.load(open(os.path.join(scen, sid + ".json"))); L = json.load(open(lp))
    first = L["first_violation_round"]
    pop = sc["population"]
    if not any(a["flags"].get("persistent") for a in pop):
        continue
    pers_runs += 1
    for a in pop:
        if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer"):
            continue
        persona_vals[a.get("persona")] += 1
        stuck = (not a["ticket"]["solvable"]) or bool(a["ticket"].get("blocked_by_unsolvable_dep"))
        g = ("persistent" if a["flags"].get("persistent") else "other", "stuck" if stuck else "solvable")
        c[g + ("n",)] += 1; c[g + ("v",)] += a["agent_id"] in first
print("control runs with persistent agents:", pers_runs)
for p in ("persistent", "other"):
    for s in ("stuck", "solvable"):
        n, v = c[(p, s, "n")], c[(p, s, "v")]
        print(f"{p:10s} {s:9s} agents={n:5d} violators={v:4d} share={v/n:.3f}")
print("persona labels (uninstructed agents in these runs):", persona_vals.most_common(8))
