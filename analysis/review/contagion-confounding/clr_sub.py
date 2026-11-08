"""Fully adjusted conditional logistic (strata run,t,stuck; ALL covariates) for subgroups and restricted exposures.
  python clr_sub.py rows.pkl out.json [nboot]
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
ALL = ["model", "persona", "subtype", "role", "lead", "info_asym", "carry_over", "own_status", "red_seen",
       "esc_before", "att_prewin", "ndm_bin", "nsent_bin", "depnb_viol_before", "dmnb_viol_before", "rx_mech_prewin"]
DM = (df.dm_any == 1).to_numpy()
K2 = df.category.str.startswith("K2").to_numpy()
B = (df.channels == "board").to_numpy()
out = {}


def go(name, expo_e, expo_p, mask=None, covs=ALL):
    for tag, full, col in (("E", "E_dir", expo_e), ("P", "P_dir", expo_p)):
        keep = ~((df[full] == 1) & (df[col] == 0)).to_numpy()
        if mask is not None:
            keep &= mask
        for dtag, m in (("all", keep), ("dm>0", keep & DM)):
            try:
                r = clrlib.run(col, covs, mask=m, nboot=NB)
            except Exception as ex:   # noqa: BLE001
                r = {"error": str(ex)}
            out[f"{name} | {tag}:{col} | {dtag}"] = r
            if "OR" in r:
                print(f"{name:45s} {tag}:{col:15s} {dtag:5s} OR {r['OR']:.2f} [{r['OR_ci'][0]:.2f}; {r['OR_ci'][1]:.2f}] "
                      f"P(OR<=1) {r['p_boot_or_le_1']:.3f} expEv {r['n_exposed_events']} ev {r['n_events']}", flush=True)
            else:
                print(name, tag, dtag, r, flush=True)


go("all configs", "E_dir", "P_dir")
go("K2 only", "E_dir", "P_dir", K2)
go("K4 only", "E_dir", "P_dir", ~K2)
go("board only", "E_dir", "P_dir", B)
go("team_channels+dm_only", "E_dir", "P_dir", ~B)
go("K4 board", "E_dir", "P_dir", ~K2 & B)
go("organic (uninstructed) senders", "E_uninstr", "P_uninstr")
go("organic senders, configs without instructed agent", "E_dir", "P_dir",
   ~df.seed_kind.isin(["pioneer", "side_task"]).to_numpy())
go("unsolicited", "E_unsolicited", "P_unsolicited")
go("no dep/review/clar relation", "E_norel", "P_norel")
go("different model", "E_diffmodel", "P_diffmodel")
go("different team", "E_diffteam", "P_diffteam")
json.dump(out, open(sys.argv[2], "w"), indent=1)
