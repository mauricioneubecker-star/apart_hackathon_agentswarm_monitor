"""(3) t8d3 sensitivity run vs the committed results/llm_monitor/oof/results.json (and RESULTS.md text)."""
import json
import re
import sys

import numpy as np
import pandas as pd

SENS = sys.argv[1]
C = json.load(open("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/oof/results.json"))
T = json.load(open(f"{SENS}/results/t8d3/oof/results.json"))
print("rows / rows_common / configs: committed", C["rows"], C["rows_common"], C["configs"], "| t8d3", T["rows"], T["rows_common"], T["configs"])
common = sorted(set(C["main"]) & set(T["main"]))
only_t = sorted(set(T["main"]) - set(C["main"]))
print("predictors in t8d3 not in committed:", only_t)
rows = []
for n in common:
    c, t = C["main"][n], T["main"][n]
    rows.append({"pred": n, "auroc_c": c.get("auroc"), "auroc_t": t.get("auroc"), "auprc_c": c.get("auprc"), "auprc_t": t.get("auprc"),
                 "n_c": c["n"], "n_t": t["n"], "pos_c": c["n_pos"], "pos_t": t["n_pos"],
                 "ci_c": c.get("auroc_ci"), "ci_t": t.get("auroc_ci"),
                 "tm_c": C["slices"]["time_matched_auroc"].get(n), "tm_t": T["slices"]["time_matched_auroc"].get(n),
                 "mx_c": C["slices"]["mixed_cfg_x_time_auroc"].get(n), "mx_t": T["slices"]["mixed_cfg_x_time_auroc"].get(n)})
R = pd.DataFrame(rows)
for k in ("auroc", "auprc", "tm", "mx"):
    R[k + "_d"] = (R[k + "_c"] - R[k + "_t"]).abs()
pd.set_option("display.width", 250)
print(R[["pred", "auroc_c", "auroc_t", "auroc_d", "auprc_d", "tm_c", "tm_t", "tm_d", "mx_c", "mx_t", "mx_d", "n_c", "n_t", "pos_c", "pos_t"]].round(5).to_string())
print("max |diff| main AUROC", R.auroc_d.max(), "AUPRC", R.auprc_d.max(), "time-matched", R.tm_d.max(), "mixed", R.mx_d.max())
print("\nAUROC CI committed vs t8d3 (boot 1000 vs 200):")
for _, x in R.iterrows():
    if x.ci_c and x.ci_t:
        print(f"  {x.pred:18s} {np.round(x.ci_c, 3)}  {np.round(x.ci_t, 3)}")
# other slices (rows_common differ: 6467 vs 6468)
print("\nslice-by-slice max |diff| over common predictors:")
for s in C["slices"]:
    if s in ("time_matched_auroc", "mixed_cfg_x_time_auroc"):
        continue
    d = [abs(C["slices"][s][n]["auroc"] - T["slices"][s][n]["auroc"]) for n in common
         if n in C["slices"][s] and n in T["slices"][s] and "auroc" in C["slices"][s][n] and "auroc" in T["slices"][s][n]]
    nn = (C["slices"][s]["clock"]["n"], T["slices"][s]["clock"]["n"])
    print(f"  {s:22s} n {nn}  max|d| {max(d):.5f}")
# paired diffs
print("\npaired diffs (committed boot1000 on 6467 rows vs t8d3 boot200 on 6468 rows):")
for k in ("zs:pairwise - bag+graph|auroc", "zs:global_full - bag+graph|auroc", "clock - bag+graph|auroc"):
    c, t = C["paired_diffs_common_rows"].get(k), T["paired_diffs_common_rows"].get(k)
    print(f"  {k:35s} committed {c['mean']:+.4f} {np.round(c['ci'], 4)} | t8d3 {t['mean']:+.4f} {np.round(t['ci'], 4)}")
# selection specs
print("\nstack selection identical:", {k: (C['selection'].get(k, {}).get('spec') == T['selection'][k]['spec']) for k in T['selection']})
