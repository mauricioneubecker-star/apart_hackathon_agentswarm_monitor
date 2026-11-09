import json, glob, collections, pandas as pd
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset"
runs = pd.read_csv(base + "/runs_night/_logs/analysis_runs.csv")
nruns = runs.groupby('cfg').size().to_dict()
tot = collections.Counter(); cfgc = collections.Counter(); per_cfg_instr = collections.Counter()
noseed_cfgs = []
for cfg, k in nruns.items():
    s = json.load(open(f"{base}/dataset/scenarios/core/{cfg}.json"))
    pop = s['population']
    ni = sum(1 for a in pop if a['flags'].get('malicious') or a['flags'].get('scripted_pioneer'))
    nk = sum(1 for a in pop if a['flags'].get('info_asym'))
    npers = sum(1 for a in pop if a['flags'].get('persistent'))
    per_cfg_instr[ni] += 1
    tot['agent_runs'] += 24*k; tot['instr'] += ni*k; tot['know'] += nk*k; tot['pers'] += npers*k
    st = s['params'].get('seed_type')
    if st == 'none' and nk == 0 and ni == 0 and not s['malicious']['actors']:
        noseed_cfgs.append(cfg)
print(dict(tot), {k: round(v/tot['agent_runs'],4) for k,v in tot.items()})
print("configs by #instructed", dict(per_cfg_instr))
print("no-seed configs (seed none, no info_asym, no actors):", len(noseed_cfgs))
sub = runs[runs.cfg.isin(noseed_cfgs)]
print("runs", len(sub), "by arm", sub.arm.value_counts().to_dict())
ctrl = sub[sub.arm=='control']
print("control runs of no-seed cfgs", len(ctrl), "tipped", int(ctrl.tipped.sum()), "by cat/disc", ctrl[ctrl.tipped].groupby(['category','discoverability']).size().to_dict())
print("all arms tipped", int(sub.tipped.sum()))
