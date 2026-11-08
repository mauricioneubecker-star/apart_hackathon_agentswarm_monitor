import pandas as pd, numpy as np, json
B = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
S = pd.read_csv(f"{B}/stat/data/night/snapshots.csv", low_memory=False)
print(S.shape); print(S.columns.tolist())
print(S.groupby("split").agg(rows=("snap","size"), runs=("run","nunique"), cfgs=("cfg","nunique")))
E = S[S["eval"]==1]
print(E.groupby("split").agg(rows=("snap","size"), pos=("y3","sum"), runs=("run","nunique"), cfgs=("cfg","nunique"), ynan=("y3", lambda v: v.isna().sum())))
HO = ["night_test_id","night_test_ood_family","night_test_ood_seed","night_branch"]
H = E[E.split.isin(HO)]
print("heldout rows", len(H), "pos", H.y3.sum(), "runs", H.run.nunique(), "cfgs", H.cfg.nunique())
print("eval==0 rows in heldout splits:", ((S["eval"]==0)&S.split.isin(HO)).sum(), " of which y3 notna:", ((S["eval"]==0)&S.split.isin(HO)&S.y3.notna()).sum())
print("t==round:", (S.t==S["round"]).all())
print(S.arm.value_counts())
print(S[S.split=="night_branch"].groupby(["cfg"]).run.nunique())
base = pd.read_csv("/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv")
print(base.shape, base.columns.tolist())
print("rtc == t - cut:", (base.rounds_to_cut == base.t - base.cut).all(), " cut values:", sorted(base.cut.unique()), " R:", base.R.unique())
print("rtc range", base.rounds_to_cut.min(), base.rounds_to_cut.max(), "nan", base.rounds_to_cut.isna().sum())
m = H.merge(base, left_on=["run","round"], right_on=["episode_id","t"], how="left", suffixes=("","_b"))
print("heldout rows matched in _base:", m.episode_id.notna().sum(), "/", len(H))
print("label agreement y3 vs tip:", (m.y3 == m.tip).mean(), " risk agree:", (m.risk==m.risk_count).mean(), " cfg==group_id:", (m.cfg==m.group_id).mean(), " split agree:", (m.split==m.split_b).mean())
print("tipped agree:", (m.tipped==m.tipped_b).mean(), " tip_round agree:", ((m.tip_round==m.tip_round_b)|(m.tip_round.isna()&m.tip_round_b.isna())).mean())
print("cut per cfg unique:", m.groupby("cfg").cut.nunique().max())
print(m.groupby("split").cut.value_counts().unstack())
