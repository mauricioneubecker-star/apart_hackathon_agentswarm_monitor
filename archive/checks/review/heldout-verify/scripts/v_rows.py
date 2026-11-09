"""Independent verification, step 1: held-out row set, positives, configs, coverage of every predictor.

Own code; reads only data files (no import of the other analyst's scripts or the harness modules)."""
import os
import sys

import numpy as np
import pandas as pd

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
SNAP = f"{SCR}/stat/data/night/snapshots.csv"
BASE = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor/_base/snapshots.csv"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
OUT = f"{SCR}/heldout-verify"
HELD = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]

S = pd.read_csv(SNAP, low_memory=False)
print("snapshots:", S.shape, "splits:", S.split.value_counts().to_dict())
print("eval values:", S["eval"].value_counts(dropna=False).to_dict())
h = S[S.split.isin(HELD)]
print("held-out snapshots (all):", len(h), " eval==1:", int((h["eval"] == 1).sum()),
      " eval==0:", int((h["eval"] == 0).sum()))
print("held-out eval==0 with y3 defined:", int(((h["eval"] == 0) & h.y3.notna()).sum()),
      " by split:", h[(h["eval"] == 0) & h.y3.notna()].split.value_counts().to_dict())
print("eval==1 but y3 NaN:", int(((h["eval"] == 1) & h.y3.isna()).sum()))
L = h[(h["eval"] == 1) & h.y3.notna()].copy()
print(f"\nHELD-OUT ROWS: {len(L)}  positives: {int(L.y3.sum())}  prevalence {L.y3.mean():.4f}  configs {L.cfg.nunique()}"
      f"  runs {L.run.nunique()}")
for sp, g in L.groupby("split"):
    runs = g.groupby("run").tipped.first()
    cpos = g.groupby("cfg").y3.max()
    print(f"  {sp:24s} rows {len(g):4d} pos {int(g.y3.sum()):3d} cfgs {g.cfg.nunique():2d} cfg_with_pos {int(cpos.sum()):2d}"
          f" runs {g.run.nunique():2d} tipped_runs {int(runs.sum()):2d}")
runs = L.groupby("run").tipped.first()
print("  tipped runs total", int(runs.sum()), "untipped", int((runs == 0).sum()))
print("  configs with >=1 positive:", int(L.groupby("cfg").y3.max().sum()))
# duplicated keys?
print("duplicate (run, round) keys in held-out rows:", int(L.duplicated(["run", "round"]).sum()))
print("rounds range:", L["round"].min(), L["round"].max(), " t==round:", bool((L.t == L["round"]).all()))

# mixed configs: tipped and untipped runs among the held-out runs of a config
mix = L.groupby("cfg").tipped.agg(["min", "max"])
mixed = sorted(mix[(mix["min"] == 0) & (mix["max"] == 1)].index)
print("mixed configs (any arm):", len(mixed), "rows", int(L.cfg.isin(mixed).sum()), "pos", int(L[L.cfg.isin(mixed)].y3.sum()))

# _base comparison
B = pd.read_csv(BASE, low_memory=False).rename(columns={"episode_id": "run", "t": "round"})
M = L.merge(B[["run", "round", "group_id", "split", "tip", "tipped", "tip_round", "cut", "rounds_to_cut", "mixed", "R"]],
            on=["run", "round"], how="left", suffixes=("", "_b"))
print("\n_base coverage of held-out rows:", int(M.cut.notna().sum()), "/", len(M))
print("cfg==group_id:", bool((M.cfg == M.group_id).all()), " split equal:", bool((M.split == M.split_b).all()))
print("y3==tip:", bool((M.y3 == M.tip).all()), " tipped equal:", bool((M.tipped == M.tipped_b).all()),
      " tip_round equal:", bool(((M.tip_round == M.tip_round_b) | (M.tip_round.isna() & M.tip_round_b.isna())).all()))
print("rounds_to_cut == round - cut:", bool((M.rounds_to_cut == M["round"] - M.cut).all()),
      " cut values:", sorted(M.cut.unique()))
print("_base mixed flag configs:", sorted(M[M.mixed_b == 1].cfg.unique()) == mixed, M[M.mixed_b == 1].cfg.nunique())
L = M
L.to_csv(f"{OUT}/heldout_rows.csv", index=False)

# also train / val rows for zero-shot thresholds
TV = S[S.split.isin(["night_train", "night_val"]) & (S["eval"] == 1) & S.y3.notna()]
print("\nnight_train+night_val eval rows:", len(TV), " night_train only:", int((TV.split == "night_train").sum()))
