"""Issue 9: Part B source configs; how run_level() would group night_vx_rep runs (group_id = new scenario id)."""
import sys
import pandas as pd
sys.path.insert(0, "/Users/mauricio/sim_local/apart_ana")
from llm_monitor.common import run_meta
R = "/Users/mauricio/sim_local/apart_ana"
i = pd.read_csv(f"{R}/sim_dataset/dataset/index.csv", low_memory=False)
rep = i[i.split == "night_vx_rep"][["scenario_id", "vx_base"]]
b = pd.read_csv(f"{R}/data/llm_monitor/_base/snapshots.csv", low_memory=False)
runs = b.groupby("episode_id").agg(group_id=("group_id", "first"), tipped=("tipped", "first"), mixed=("mixed", "first"))
tot_old = 0
for _, r in rep.iterrows():
    old = runs[runs.group_id == r.vx_base]
    tot_old += len(old)
    # what run_meta would assign to a (hypothetical) Part B run dir: group_id = its own scenario id
    m = run_meta(f"/nonexistent/{r.scenario_id}/rep0")
    print(f"{r.scenario_id}: run_meta group_id={m['group_id']==r.scenario_id and 'own new id' or m['group_id']}, vx_base={m['vx_base']}, "
          f"split={m['split']} | source night runs {len(old)} tipped {old.tipped.tolist()} mixed={int(old.mixed.max())}")
print("old source runs in total:", tot_old)
