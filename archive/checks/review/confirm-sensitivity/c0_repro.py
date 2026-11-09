"""Check that the reconstructed rows_common reproduces the published main AUROCs, slices and (200x) diffs."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/verify/confirm-sensitivity")
import numpy as np
from sklearn.metrics import roc_auc_score
from common_cs import TAGS, load, stratified_auroc, rtc_bin

KEYS = ["clock", "bag+graph", "zs:global_full", "zs:global_window", "zs:pairwise", "hgb:pairwise", "oracle"]
for tag in TAGS:
    D, names, R = load(tag)
    y = D.tip.values
    print(f"== {tag}: rows_common {len(D)} (json {R['rows_common']}), pos {int(y.sum())}, configs {D.group_id.nunique()}")
    rb = rtc_bin(D.rounds_to_cut)
    strata = (D.group_id + "|" + rb).values
    mx = D.mixed.values == 1
    for k in KEYS:
        a = roc_auc_score(y, D[k])
        tm = stratified_auroc(y, D[k].values, rb.values)
        mc = stratified_auroc(y[mx], D[k].values[mx], strata[mx])
        jm = R["main"][k]["auroc"]
        jtm = R["slices"]["time_matched_auroc"][k]
        jmc = R["slices"]["mixed_cfg_x_time_auroc"][k]
        print(f"  {k:18s} main {a:.4f} (json {jm:.4f})  tm {tm:.4f} (json {jtm:.4f})  mixed {mc:.4f} (json {jmc:.4f})")
