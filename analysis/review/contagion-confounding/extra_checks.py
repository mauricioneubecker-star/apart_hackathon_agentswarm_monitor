"""Additional MH checks (strata run,t,stuck [+ extra]; bootstrap over configs) used in the verdict.
  python extra_checks.py <dir with rows6_w3.pkl, rows2_w1.pkl, rows2_w5.pkl>
"""
import sys

import numpy as np
import pandas as pd

D = sys.argv[1]
sys.path.insert(0, D)
from mhlib import BASE, est, fmt  # noqa: E402


def both(df, name, x, keys=BASE, mask=None):
    DM = (df.dm_any == 1).to_numpy()
    m = np.ones(len(df), bool) if mask is None else mask
    print(f"{name:58s} {x:10s} all  {fmt(est(df, x, keys, m))}")
    print(f"{name:58s} {x:10s} dm>0 {fmt(est(df, x, keys, m & DM))}")


def restricted(df, name, e, p, extra=None):
    for full, col in (("E_dir", e), ("P_dir", p)):
        keep = ~((df[full] == 1) & (df[col] == 0)).to_numpy()
        if extra is not None:
            keep &= extra
        both(df, name, col, mask=keep)


print("=== heterogeneity by window (K2/K4, board/non-board) ===")
for w, f in ((1, "rows2_w1.pkl"), (3, "rows6_w3.pkl"), (5, "rows2_w5.pkl")):
    df = pd.read_pickle(f"{D}/{f}")
    K2 = df.category.str.startswith("K2").to_numpy()
    B = (df.channels == "board").to_numpy()
    for nm, m in (("K2", K2), ("K4", ~K2), ("board", B), ("non-board", ~B), ("K4 board", ~K2 & B),
                  ("K4 non-board", ~K2 & ~B), ("K2 board", K2 & B)):
        for x in ("E_dir", "P_dir"):
            both(df, f"w={w} {nm}", x, mask=m)

df = pd.read_pickle(f"{D}/rows6_w3.pkl")
K2 = df.category.str.startswith("K2").to_numpy()
B = (df.channels == "board").to_numpy()
print("\n=== K2 / K4 shortcut-naming DMs ===")
both(df, "K2", "E_mech", mask=K2)
both(df, "K4", "E_mech", mask=~K2)

print("\n=== sender types ===")
restricted(df, "tech-lead senders only", "E_lead", "P_lead")
restricted(df, "reviewer-role senders only", "E_reviewerrole", "P_reviewerrole")
restricted(df, "info_asym senders only", "E_infoasym", "P_infoasym")
ex, pl = df[df.E_dir == 1], df[df.P_dir == 1]
for e, p in (("E_instr", "P_instr"), ("E_lead", "P_lead"), ("E_samemodel", "P_samemodel"), ("E_sameteam", "P_sameteam"),
             ("E_anyrel", "P_anyrel"), ("E_sol2", "P_sol2")):
    print(f"share of exposed agent-rounds with {e:12s}: E {ex[e].mean():.3f} (exposed adopters {ex[ex.Y == 1][e].mean():.3f}) | "
          f"placebo {pl[p].mean():.3f}")

print("\n=== solicited vs unsolicited (refined: receiver addressed the sender in [r-3, r-1]) ===")
restricted(df, "unsolicited", "E_unsol2", "P_unsol2")
restricted(df, "solicited", "E_sol2", "P_sol2")
restricted(df, "K4 unsolicited", "E_unsol2", "P_unsol2", ~K2)
restricted(df, "non-board unsolicited", "E_unsol2", "P_unsol2", ~B)

print("\n=== further receiver-state strata ===")
for k in (["rx_mech_prewin"], ["ext_seen"], ["ext_seen_prewin"], ["saw_team_viol"], ["saw_team_viol", "team"],
          ["since_red_bin"], ["since_esc_bin"], ["credits_bin"], ["since_red_bin", "credits_bin"], ["qa_fixed"],
          ["proxy_q"], ["n_viol_team_before"], ["rx_contacted_violator_prewin"]):
    for x in ("E_dir", "P_dir"):
        both(df, "+" + "+".join(k), x, BASE + k)
both(df, "configs without injected instruction", "E_dir", mask=(df.inj_carrier == "none").to_numpy())
both(df, "receivers never saw a team violation in check_status", "E_dir", mask=(df.saw_team_viol == 0).to_numpy())
