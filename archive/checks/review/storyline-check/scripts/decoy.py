import json, glob, collections, pandas as pd
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset"
runs = pd.read_csv(base + "/runs_night/_logs/analysis_runs.csv")
cfgs = sorted(runs.cfg.unique())
dec = 0; dec_per = collections.Counter(); senders = collections.Counter(); mal = collections.Counter(); maltexts = collections.defaultdict(set)
evtypes = collections.Counter()
for c in cfgs:
    s = json.load(open(f"{base}/dataset/scenarios/core/{c}.json"))
    nd = 0
    for t in s["timeline"]:
        for ev in t["events"]:
            evtypes[ev.get("type")] += 1
            if ev.get("type") == "decoy_notice" or ev.get("decoy"):
                nd += 1; senders[ev.get("sender") or ev.get("from")] += 1
            if ev.get("malicious"):
                v = ev.get("variant") or ev.get("type")
                mal[v] += 1; maltexts[v].add(ev.get("text"))
    dec += nd; dec_per[nd] += 1
print("decoys", dec, dict(dec_per), dict(senders))
print("malicious timeline events", dict(mal), {k: len(v) for k, v in maltexts.items()})
print("event types", evtypes.most_common(25))
