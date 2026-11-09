"""Hostile confounding checks of the contagion claim (analysis/results/contagion.md, part A).
  python confound.py rows.pkl out.json
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from mhlib import BASE, est, fmt  # noqa: E402

df = pd.read_pickle(sys.argv[1])
out = {}
DM = (df.dm_any == 1).to_numpy()
df["ndm_bin"] = np.minimum(df.n_dm, 3)
df["nsend_bin"] = np.minimum(df.n_dm_senders, 3)
df["nsent_bin"] = np.minimum(df.n_sent_win, 2)
df["tbin"] = df.t  # placeholder


def block(name, keys=BASE, mask=None, expo=("E_dir", "P_dir", "E_mech"), dm=True):
    res = {}
    for x in expo:
        res[x] = est(df, x, keys, mask)
        print(f"{name:55s} {x:14s} all   {fmt(res[x])}")
        if dm:
            m = DM if mask is None else (np.asarray(mask, bool) & DM)
            res[x + "|dm>0"] = est(df, x, keys, m)
            print(f"{name:55s} {x:14s} dm>0  {fmt(res[x + '|dm>0'])}")
    out[name] = res


print("=== 1. extra strata (receiver confounders) ===")
block("base (run,t,stuck)")
STRATA = {
    "+receiver model": BASE + ["model"],
    "+receiver persona": BASE + ["persona"],
    "subtype instead of stuck (own/dep/both/free)": ["run", "t", "subtype"],
    "+role (member/reviewer/auditor)": BASE + ["role"],
    "+tech_lead flag": BASE + ["lead"],
    "+info_asym flag": BASE + ["info_asym"],
    "+carry_over flag": BASE + ["carry_over"],
    "+team": BASE + ["team"],
    "+active,own_status (dynamic, before t)": BASE + ["active", "own_status"],
    "+red_seen before t": BASE + ["red_seen"],
    "+escalated before t": BASE + ["esc_before"],
    "+attempt before window": BASE + ["att_prewin"],
    "+n direct msgs in window (1,2,3+)": BASE + ["ndm_bin"],
    "+n distinct DM senders in window": BASE + ["nsend_bin"],
    "+receiver sent msgs in window (0,1,2+)": BASE + ["nsent_bin"],
    "+dep-neighbour already violated": BASE + ["depnb_viol_before"],
    "+model+persona+subtype": ["run", "t", "subtype", "model", "persona"],
    "+subtype+model+red_seen+esc+own_status": ["run", "t", "subtype", "model", "red_seen", "esc_before", "own_status"],
    "+subtype+model+persona+red+esc+status+att+ndm": ["run", "t", "subtype", "model", "persona", "red_seen", "esc_before",
                                                     "own_status", "att_prewin", "ndm_bin"],
}
for k, v in STRATA.items():
    block(k, v)

print("\n=== 2. pair-type restrictions (exposure only through pairs of a given type) ===")


def restricted(name, e_col, p_col, keys=BASE):
    """Exposure = violator DM through the allowed pair type. Rows exposed ONLY through disallowed pairs are dropped
    (they are neither exposed-by-allowed nor clean unexposed). Same for the placebo."""
    res = {}
    for tag, full, col in (("E", "E_dir", e_col), ("P", "P_dir", p_col)):
        keep = ~((df[full] == 1) & (df[col] == 0))
        r_all = est(df, col, keys, keep)
        r_dm = est(df, col, keys, keep & DM)
        res[tag] = r_all
        res[tag + "|dm>0"] = r_dm
        print(f"{name:55s} {tag}:{col:16s} all   {fmt(r_all)}")
        print(f"{name:55s} {tag}:{col:16s} dm>0  {fmt(r_dm)}")
    out["restrict: " + name] = res


for nm, (e, p) in {
    "no dependency relation (dep owner/dependent)": ("E_nodep", "P_nodep"),
    "ONLY dependency relation": ("E_dep", "P_dep"),
    "no dep/review/clarification relation": ("E_norel", "P_norel"),
    "ONLY dep/review/clarification relation": ("E_anyrel", "P_anyrel"),
    "different backbone model": ("E_diffmodel", "P_diffmodel"),
    "same backbone model": ("E_samemodel", "P_samemodel"),
    "different team": ("E_diffteam", "P_diffteam"),
    "same team": ("E_sameteam", "P_sameteam"),
    "uninstructed (organic) senders only": ("E_uninstr", "P_uninstr"),
    "instructed (seed) senders only": ("E_instr", "P_instr"),
    "plain senders (no seed/lead/auditor/reviewer/info_asym)": ("E_plainsender", "P_plainsender"),
    "strict: no rel, diff model, diff team, uninstructed": ("E_strict", "P_strict"),
    "unsolicited (receiver did not message sender before)": ("E_unsolicited", "P_unsolicited"),
    "solicited (receiver messaged sender before)": ("E_solicited", "P_solicited"),
}.items():
    restricted(nm, e, p)

print("\n=== 3. subgroups ===")
for col in ("channels", "category", "discoverability", "seed_kind", "decision", "model", "subtype"):
    for v in sorted(df[col].dropna().unique()):
        m = (df[col] == v).to_numpy()
        block(f"subgroup {col}={v}", mask=m, expo=("E_dir", "P_dir"))

json.dump(out, open(sys.argv[2], "w"), indent=1)
