import json, glob, collections
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
files = sorted(glob.glob(base + "/core-night_*/rep*/labels.json"))
td = collections.Counter(); rows = 0; elig = 0; pos = 0; tw_none = 0; posR=0
dup_elig = dup_pos = 0
for f in files:
    j = json.load(open(f))
    td[(j["theta_agents"], j["delta"])] += 1
    arm = "-" in f.split("/")[-2]
    for r in j["per_round"]:
        rows += 1
        if r["tip_within_delta"] is None: tw_none += 1
        if r["risk_count_t"] < 8:
            elig += 1
            if r["tip_within_delta"]: pos += 1
            if arm and r["round"] <= 5:
                dup_elig += 1; dup_pos += bool(r["tip_within_delta"])
        if r["round"] == 30 and r["tip_within_delta"]: posR += 1
print("files", len(files), td)
print("rows", rows, "eligible (risk<8)", elig, "pos", pos, "tw None", tw_none, "pos at t=R", posR)
print("dup prefix eligible rows", dup_elig, "pos", dup_pos, "-> unique", elig - dup_elig)
