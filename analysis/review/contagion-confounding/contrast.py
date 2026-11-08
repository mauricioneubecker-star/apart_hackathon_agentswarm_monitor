"""Joint config bootstrap: E_dir vs placebo contrast, K2 vs K4 and board vs non-board heterogeneity, leave-one-config-out
influence and concentration of the MH numerator.  python contrast.py rows.pkl"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from mhlib import BASE, mh_table  # noqa: E402

df = pd.read_pickle(sys.argv[1])
DM = (df.dm_any == 1).to_numpy()
K2 = df.category.str.startswith("K2").to_numpy()
B = (df.channels == "board").to_numpy()
cfgs = np.array(sorted(df.cfg.unique()))
rng = np.random.default_rng(1)
NB = 4000
IDX = rng.integers(0, len(cfgs), (NB, len(cfgs)))


def table(x, mask):
    acc = mh_table(df, x, BASE, mask).reindex(cfgs).fillna(0.0)
    return acc[["or_num", "or_den"]].to_numpy()


def boot_or(M):
    S = M[IDX].sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return S[:, 0] / S[:, 1]


def ci(v):
    v = v[np.isfinite(v)]
    return f"[{np.percentile(v, 2.5):.2f}; {np.percentile(v, 97.5):.2f}]"


for tag, m in (("all", None), ("dm>0", DM)):
    E, P = table("E_dir", m), table("P_dir", m)
    oe, op = E[:, 0].sum() / E[:, 1].sum(), P[:, 0].sum() / P[:, 1].sum()
    be, bp = boot_or(E), boot_or(P)
    r = be / bp
    print(f"{tag}: OR_E {oe:.2f}  OR_P {op:.2f}  ratio {oe / op:.2f} {ci(r)}  P(ratio<=1) {np.mean(r[np.isfinite(r)] <= 1):.3f}")

for nm, g1, g2 in (("K4 vs K2", ~K2, K2), ("non-board vs board", ~B, B)):
    for tag, m in (("all", np.ones(len(df), bool)), ("dm>0", DM)):
        A1, A2 = table("E_dir", m & g1), table("E_dir", m & g2)
        o1, o2 = A1[:, 0].sum() / A1[:, 1].sum(), A2[:, 0].sum() / A2[:, 1].sum()
        r = boot_or(A1) / boot_or(A2)
        print(f"{nm} {tag}: OR {o1:.2f} vs {o2:.2f}; ratio {o1 / o2:.2f} {ci(r)}  P(ratio<=1) {np.mean(r[np.isfinite(r)] <= 1):.3f}")

# leave-one-config-out and concentration
for tag, m in (("all", None), ("dm>0", DM)):
    acc = mh_table(df, "E_dir", BASE, m)
    tot_n, tot_d = acc.or_num.sum(), acc.or_den.sum()
    loo = {c: (tot_n - acc.loc[c, "or_num"]) / (tot_d - acc.loc[c, "or_den"]) for c in acc.index}
    s = pd.Series(loo).sort_values()
    share = (acc.or_num / tot_n).sort_values(ascending=False)
    print(f"\nE_dir {tag}: OR {tot_n / tot_d:.2f}; leave-one-config-out min {s.iloc[0]:.2f} ({s.index[0]}), max {s.iloc[-1]:.2f} ({s.index[-1]})")
    print(f"  share of MH numerator from top 3 / top 5 / top 10 configs: {share.iloc[:3].sum():.2f} / {share.iloc[:5].sum():.2f} / {share.iloc[:10].sum():.2f}")
    print("  top 5 configs by numerator share:", ", ".join(f"{c} {v:.2f}" for c, v in share.iloc[:5].items()))
    # drop top-k
    for k in (1, 3, 5):
        top = share.index[:k]
        n_, d_ = tot_n - acc.loc[top, "or_num"].sum(), tot_d - acc.loc[top, "or_den"].sum()
        print(f"  without top {k} configs: OR {n_ / d_:.2f}")
