"""Private DM vs public @mention/reply exposures, by channel setting. python priv_pub.py rows7_w3.pkl"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from mhlib import BASE, est, fmt  # noqa: E402
df = pd.read_pickle(sys.argv[1])
DM = (df.dm_any == 1).to_numpy()
assert (df.E_dir == ((df.E_priv + df.E_pub) > 0).astype(int)).all()
B = (df.channels == "board").to_numpy()
K2 = df.category.str.startswith("K2").to_numpy()
for nm, m0 in (("all", np.ones(len(df), bool)), ("board", B), ("board K4", B & ~K2), ("board K2", B & K2), ("non-board", ~B)):
    for full, col in (("E_dir", "E_priv"), ("E_dir", "E_pub"), ("P_dir", "P_priv"), ("P_dir", "P_pub")):
        keep = m0 & ~((df[full] == 1) & (df[col] == 0)).to_numpy()
        print(f"{nm:10s} {col:7s} all  {fmt(est(df, col, BASE, keep))}")
        print(f"{nm:10s} {col:7s} dm>0 {fmt(est(df, col, BASE, keep & DM))}")
ex = df[df.E_dir == 1]
print("board: share of E_dir agent-rounds via private DM", round(ex[ex.channels == "board"].E_priv.mean(), 3),
      "| non-board", round(ex[ex.channels != "board"].E_priv.mean(), 3))
