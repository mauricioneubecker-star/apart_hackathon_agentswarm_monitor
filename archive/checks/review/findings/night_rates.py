"""Recount night-batch tip rates over all run dirs (read-only)."""
import glob
import json
import os

import pandas as pd

ROOT = "/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night"
rows = []
for p in sorted(glob.glob(os.path.join(ROOT, "*", "*", "labels.json"))):
    rel = os.path.relpath(p, ROOT)
    scen, rep = rel.split(os.sep)[:2]
    d = json.load(open(p))
    rows.append(dict(cfg=scen, rep=rep, tipped=bool(d.get("tipped")), tip_round=d.get("tip_round"),
                     nv=d.get("n_violators"), theta=d.get("theta_agents"), delta=d.get("delta"),
                     exp_considered=d.get("exposure_counts_direct", {}).get("considered"),
                     exp_direct=d.get("exposure_counts_direct", {}).get("exposed"),
                     exp_feed=d.get("exposure_counts_feed", {}).get("exposed"),
                     exp_feed_considered=d.get("exposure_counts_feed", {}).get("considered"),
                     exp_any=d.get("exposure_counts", {}).get("exposed"),
                     exp_any_considered=d.get("exposure_counts", {}).get("considered")))
lab = pd.DataFrame(rows)
print("runs:", len(lab), "configs:", lab.cfg.nunique(), "tipped:", lab.tipped.sum(),
      "rate: %.4f" % lab.tipped.mean())
print("theta/delta values:", lab.theta.unique(), lab.delta.unique())
print("tipped configs:", lab[lab.tipped].cfg.nunique())
print("exposure sums (labels.json): direct %s / %s ; feed %s / %s ; any %s / %s" % (
    lab.exp_direct.sum(), lab.exp_considered.sum(), lab.exp_feed.sum(), lab.exp_feed_considered.sum(),
    lab.exp_any.sum(), lab.exp_any_considered.sum()))

ar = pd.read_csv(os.path.join(ROOT, "_logs", "analysis_runs.csv"))
print("analysis_runs rows:", len(ar), "tipped:", ar.tipped.sum())
m = ar.merge(lab[["cfg", "rep", "tipped"]], on=["cfg", "rep"], how="outer", suffixes=("_ar", "_lab"), indicator=True)
print(m._merge.value_counts().to_dict())
print("tipped mismatches:", int((m.tipped_ar.astype(bool) != m.tipped_lab.astype(bool)).sum()))

for f in ["split", "category", "release_freeze", "manager_push", "discoverability", "channels", "sanctions",
          "seed_type", "n_impossible", "prohibition_form", "arm", "self_merge", "persistent_share", "model_mix"]:
    g = ar.groupby(f).agg(n=("tipped", "size"), tip_rate=("tipped", "mean"), tipped=("tipped", "sum"))
    print("\n##", f)
    print(g.round(3).to_string())

# controls only (exclude branch arms) for factor effects
ctrl = ar[ar.arm == "control"]
print("\ncontrol runs:", len(ctrl), "tipped:", ctrl.tipped.sum(), "rate %.3f" % ctrl.tipped.mean())
print("exp sums analysis_runs: dir mean", ar.exp_dir.mean(), "feed mean", ar.exp_feed.mean())
