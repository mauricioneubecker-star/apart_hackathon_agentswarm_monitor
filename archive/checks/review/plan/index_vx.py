import pandas as pd
I = pd.read_csv("/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/index.csv", low_memory=False)
print("cols:", [c for c in I.columns if "vx" in c or c in ("split", "replicates", "n_reps", "reps")])
vx = I[I.split.astype(str).str.startswith("night_vx")]
print("vx scenario rows:", len(vx))
print(vx.groupby(["split", "vx_arm"]).size())
print("n distinct vx_base (part A):", vx[vx.split != "night_vx_rep"].vx_base.nunique(), " part B bases:", sorted(vx[vx.split == "night_vx_rep"].vx_base.unique()))
for c in ("replicates", "n_replicates", "reps"):
    if c in I.columns:
        print(c, vx.groupby("split")[c].unique())
print([c for c in I.columns][:60])
