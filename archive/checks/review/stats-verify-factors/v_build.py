"""Independent rebuild of the night-batch run table (verification of the factor analysis).
Reads labels.json of every run dir in runs_night and joins factors from index.csv.
Writes v_runs.csv (all runs incl. branch arms, with is_control flag) and v_configs.csv (112 configs)."""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/mauricio/sim_local/apart_ana/sim_dataset"
RUNS = os.path.join(ROOT, "runs_night")
OUT = os.path.dirname(os.path.abspath(__file__))

rows = []
for sc in sorted(os.listdir(RUNS)):
    d = os.path.join(RUNS, sc)
    if sc.startswith("_") or not os.path.isdir(d):
        continue
    for rep in sorted(os.listdir(d)):
        rd = os.path.join(d, rep)
        if not os.path.isdir(rd):
            continue
        lp = os.path.join(rd, "labels.json")
        if not os.path.exists(lp):
            rows.append(dict(scenario_id=sc, rep=rep, missing=True))
            continue
        with open(lp) as f:
            lab = json.load(f)
        # sanction events from events.jsonl (count lines whose type mentions sanction)
        n_sanc = 0
        ep = os.path.join(rd, "events.jsonl")
        types = {}
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    t = str(e.get("type", e.get("event", "")))
                    types[t] = types.get(t, 0) + 1
        rows.append(dict(scenario_id=sc, rep=rep, missing=False,
                         is_control=("-" not in rep),
                         tipped=bool(lab["tipped"]), theta=lab.get("theta_agents"), delta=lab.get("delta"),
                         n_violators=lab.get("n_violators"), lab_sid=lab.get("scenario_id"),
                         event_types=json.dumps(types, sort_keys=True)))

runs = pd.DataFrame(rows)
print("run dirs:", len(runs), "missing labels:", int(runs["missing"].sum()))
runs = runs[~runs["missing"]].copy()
print("sid mismatch labels vs dir:", int((runs["lab_sid"] != runs["scenario_id"]).sum()))
print("theta values:", runs["theta"].value_counts().to_dict(), "delta:", runs["delta"].value_counts().to_dict())
print("control runs:", int(runs["is_control"].sum()), "branch arms:", int((~runs["is_control"]).sum()))
print("rep names:", runs["rep"].value_counts().to_dict())

idx = pd.read_csv(os.path.join(ROOT, "dataset", "index.csv"), low_memory=False)
idx = idx[idx["scenario_id"].isin(runs["scenario_id"].unique())].copy()
print("configs in index:", len(idx), "unique sids in runs:", runs["scenario_id"].nunique())
assert idx["scenario_id"].is_unique

keep = ["scenario_id", "split", "category", "release_freeze", "manager_push", "discoverability", "channels",
        "self_merge", "persistent_share", "prohibition_form", "n_impossible", "persona_mix", "sanctions",
        "model_mix", "seed_type", "seed_status", "seed_placement", "detection_probability", "sanction",
        "enforcer", "push_offset", "family", "deadline_override"]
cfg = idx[keep].copy()
cfg["cat"] = cfg["category"].str[:2]
cfg["seed_tl"] = (cfg["seed_status"] == "tech_lead")

runs = runs.merge(cfg, on="scenario_id", how="left")
runs.to_csv(os.path.join(OUT, "v_runs.csv"), index=False)

ctl = runs[runs["is_control"]]
agg = ctl.groupby("scenario_id").agg(n_runs=("tipped", "size"), n_tip=("tipped", "sum"), rate=("tipped", "mean"))
cfgs = cfg.set_index("scenario_id").join(agg, how="inner").reset_index()
cfgs.to_csv(os.path.join(OUT, "v_configs.csv"), index=False)
print("configs:", len(cfgs), "control runs:", int(cfgs["n_runs"].sum()), "tipped:", int(cfgs["n_tip"].sum()),
      "run rate %.4f" % (cfgs["n_tip"].sum() / cfgs["n_runs"].sum()), "mean config rate %.4f" % cfgs["rate"].mean())
print("runs per config:", cfgs["n_runs"].value_counts().sort_index().to_dict())
print("all runs tipped:", int(runs["tipped"].sum()), "/", len(runs))
print(cfgs.groupby("split").agg(n=("rate", "size"), runs=("n_runs", "sum"), tip=("n_tip", "sum"), rate=("rate", "mean")))
for c in ["cat", "release_freeze", "manager_push", "discoverability", "channels", "self_merge", "persistent_share",
          "prohibition_form", "n_impossible", "persona_mix", "sanctions", "model_mix", "seed_type", "seed_tl"]:
    print(c, cfgs[c].value_counts(dropna=False).to_dict())
