import json
from collections import Counter
from pathlib import Path
ROOT = Path("/Users/mauricio/sim_local/apart_ana/sim_dataset")
ds = ROOT / "dataset" / "scenarios" / "core"
res = Counter()
for lab_f in sorted((ROOT / "runs_night").glob("*/rep*/labels.json")):
    rd = lab_f.parent
    sc = json.loads((ds / f"{rd.parent.name}.json").read_text())
    p, lab = sc["params"], json.loads(lab_f.read_text())
    if not lab["tipped"]:
        continue
    br = rd / "branch.json"
    arm = json.loads(br.read_text())["arm"] if br.exists() else "control"
    inst = set(sc["labels_config"].get("instructed_agents", []))
    first = lab["first_violation_round"]
    fa = min(first, key=first.get)
    mn = first[fa]
    tied = {a for a, r in first.items() if r == mn}
    starter = ("instructed" if fa in inst else ("after_injection" if arm != "control" or p.get("seed_type") == "external" else "organic"))
    if starter != "organic":
        continue
    ea = sc.get("early_adopters") or {}
    def ids(x):
        out=set()
        for e in (x or []):
            if isinstance(e, dict):
                out.add(e.get("agent_id") or e.get("agent") or e.get("id"))
            else:
                out.add(e)
        return out
    seeded = ids(ea.get("info_asym")) | ids(ea.get("pressure_asym")) | ids(ea.get("scripted_pioneers"))
    seeded |= {a["agent_id"] for a in sc["population"] if a["flags"].get("info_asym") or a["flags"].get("pressure_asym")}
    st = p.get("seed_type")
    res[(st, "first violator is seeded (info/pressure asym)" if tied & seeded else "first violator not seeded")] += 1
for k, v in sorted(res.items()):
    print(k, v)
