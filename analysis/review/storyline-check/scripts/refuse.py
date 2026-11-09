import json, glob, collections
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
types = collections.Counter(); ref = []; actions = collections.Counter()
for f in glob.glob(base + "/core-night_*/rep*/events.jsonl"):
    for l in open(f):
        e = json.loads(l); types[e.get("type")] += 1
        if e.get("type") == "refuse" or e.get("action") == "refuse": ref.append((f.split("runs_night/")[1][:60], e.get("round"), e.get("agent")))
print(types.most_common(40))
print("refuse", len(ref), ref[:10])
