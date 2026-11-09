import pandas as pd, json, glob, os
I = pd.read_csv("/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/index.csv", low_memory=False)
vx = I[I.split.astype(str).str.startswith("night_vx")]
print(vx[vx.split == "night_vx_rep"][["scenario_id", "vx_base", "vx_source_split", "rounds", "deadline_round"]].to_string())
print(vx[vx.split == "night_vx_id"][["scenario_id", "vx_base"]].head(3).to_string())
print(vx[vx.split == "night_vx_time"][["scenario_id", "rounds", "deadline_round"]].head(3).to_string())
# replicates per scenario: look in scenario json
for sid in list(vx[vx.split == "night_vx_id"].scenario_id[:1]) + list(vx[vx.split == "night_vx_rep"].scenario_id[:1]) + list(vx[vx.split == "night_vx_enf"].scenario_id[:1]):
    p = f"/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/scenarios/core/{sid}.json"
    s = json.load(open(p))
    keys = [k for k in s.keys()]
    rep = {k: s[k] for k in keys if "rep" in k.lower() or "seed" in k.lower()}
    print(sid, "keys with rep/seed:", rep if len(str(rep)) < 400 else str(rep)[:400])
