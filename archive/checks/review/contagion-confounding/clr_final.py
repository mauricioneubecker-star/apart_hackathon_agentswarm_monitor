"""Final fully adjusted conditional logistic runs (strata run,t,stuck; ALL+ covariates incl. external-instruction
exposure, recency of red, credits) for the main estimate and the key subgroups / sender restrictions.
  python clr_final.py rows5.pkl out.json [nboot]
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import clrlib  # noqa: E402

df = pd.read_pickle(sys.argv[1])
clrlib.set_df(df)
NB = int(sys.argv[3]) if len(sys.argv) > 3 else 300
for c in ("since_red_bin", "since_esc_bin", "credits_bin"):
    df[c] = df[c].astype(str)
ALLP = ["model", "persona", "subtype", "role", "lead", "info_asym", "carry_over", "own_status", "red_seen",
        "esc_before", "att_prewin", "ndm_bin", "nsent_bin", "depnb_viol_before", "dmnb_viol_before", "rx_mech_prewin",
        "ext_seen", "since_red_bin", "since_esc_bin", "credits_bin", "qa_fixed", "rx_contacted_violator_prewin"]
DM = (df.dm_any == 1).to_numpy()
K2 = df.category.str.startswith("K2").to_numpy()
B = (df.channels == "board").to_numpy()
out = {}


def go(name, expo_e, expo_p, mask=None):
    for tag, full, col in (("E", "E_dir", expo_e), ("P", "P_dir", expo_p)):
        keep = ~((df[full] == 1) & (df[col] == 0)).to_numpy()
        if mask is not None:
            keep &= mask
        for dtag, m in (("all", keep), ("dm>0", keep & DM)):
            r = clrlib.run(col, ALLP, mask=m, nboot=NB)
            out[f"{name} | {tag}:{col} | {dtag}"] = r
            print(f"{name:40s} {tag}:{col:12s} {dtag:5s} OR {r['OR']:.2f} [{r['OR_ci'][0]:.2f}; {r['OR_ci'][1]:.2f}] "
                  f"P(OR<=1) {r['p_boot_or_le_1']:.3f} expEv {r['n_exposed_events']} ev {r['n_events']}", flush=True)


go("all configs", "E_dir", "P_dir")
go("K2", "E_dir", "P_dir", K2)
go("K4", "E_dir", "P_dir", ~K2)
go("board", "E_dir", "P_dir", B)
go("non-board", "E_dir", "P_dir", ~B)
go("unsolicited (refined)", "E_unsol2", "P_unsol2")
go("K4 unsolicited (refined)", "E_unsol2", "P_unsol2", ~K2)
go("organic senders", "E_uninstr", "P_uninstr")
go("K4 organic senders", "E_uninstr", "P_uninstr", ~K2)
json.dump(out, open(sys.argv[2], "w"), indent=1)
