import json, glob, os, collections
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
metas = sorted(glob.glob(base + "/core-night_*/rep*/meta.json"))
print("meta files", len(metas))
S = collections.Counter()
for m in metas:
    j = json.load(open(m))
    for k in ["llm_calls","invalid_json","json_retries","invalid_json_final","n_messages","n_violation_events","rounds"]:
        v = j.get(k)
        if isinstance(v,(int,float)): S[k]+=v
    S["rounds30"] += (j.get("rounds")==30)
print(dict(S))
print("invalid rate before retry", S["invalid_json"]/S["llm_calls"], "final", S["invalid_json_final"]/S["llm_calls"])
br = sorted(glob.glob(base + "/core-night_branch-*/rep0-*/branch.json"))
print("branch.json", len(br), collections.Counter(json.load(open(b))["branch_round"] for b in br), collections.Counter(json.load(open(b))["arm"] for b in br))
bp = sorted(glob.glob(base + "/core-night_branch-*/rep0/branch_point.json"))
print("branch_point", len(bp))
for b in bp[:2]: print(open(b).read()[:600])
