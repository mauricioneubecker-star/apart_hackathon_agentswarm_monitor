import json, glob, collections
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
dup_calls = dup_msgs = 0
kinds = collections.Counter(); kinds_all = collections.Counter()
for arm in sorted(glob.glob(base + "/core-night_branch-*/rep0-*")):
    br = json.load(open(arm + "/branch.json"))["branch_round"]
    for l in open(arm + "/llm_calls.jsonl"):
        j = json.loads(l)
        if j.get("round") is not None and j["round"] <= br: dup_calls += 1
    for l in open(arm + "/messages.jsonl"):
        j = json.loads(l)
        if j.get("round") is not None and j["round"] <= br: dup_msgs += 1
print("duplicated prefix calls", dup_calls, "dup msgs", dup_msgs)
# message kinds over all runs
keys = collections.Counter()
for f in glob.glob(base + "/core-night_*/rep*/messages.jsonl"):
    for l in open(f):
        j = json.loads(l)
        kinds_all[(j.get("kind") or j.get("type") or j.get("channel_type") or "?")] += 1
        for k in j: keys[k]+=1
print(kinds_all.most_common(20))
print(keys.most_common(30))
