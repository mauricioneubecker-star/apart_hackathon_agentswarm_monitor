"""Issue 2/6: per-split AUROC of protocol (a) OOF preds vs committed protocol (b); time-matched clock; pool AUROC."""
import json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
R = "/Users/mauricio/sim_local/apart_ana"
b = pd.read_csv(f"{R}/data/llm_monitor/_base/snapshots.csv", low_memory=False)
P = pd.read_csv(f"{R}/results/llm_monitor/oof/preds.csv")
print("preds cols (first 12):", list(P.columns)[:12], "... n cols", P.shape[1])
M = b.merge(P, on=["episode_id", "t"], how="inner")
M = M[M.tip.notna()]
print("rows (a) with tip:", len(M), "pos", int(M.tip.sum()), "configs", M.group_id.nunique())
fz = json.load(open(f"{R}/results/llm_monitor/frozen/results.json"))
print("frozen top keys:", list(fz.keys())); s0 = list(fz["splits"])[0]
print("frozen split keys:", list(fz["splits"][s0].keys()))
for name in ["zs:pairwise", "zs:global_full", "bag+graph", "clock"]:
    out = []
    for s in ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]:
        m = M[M.split == s]
        a_auc = roc_auc_score(m.tip, m[name])
        b_auc = fz["splits"][s]["metrics"][name]["auroc"]
        out.append(f"{s.replace('night_','')}: a={a_auc:.3f} b={b_auc:.3f}")
    print(name, " | ".join(out))
held = M.split.isin(["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"])
print("held-out target rows in (a):", int(held.sum()), "pos", int(M.tip[held].sum()), "share rows %.3f share pos %.3f" % (held.mean(), M.tip[held].sum() / M.tip.sum()))
h3 = M.split.isin(["night_test_id", "night_test_ood_family", "night_test_ood_seed"])
print("test_id+ood_family+ood_seed: rows", int(h3.sum()), "pos", int(M.tip[h3].sum()), "cfgs", M.group_id[h3].nunique())
pool = M.split.isin(["night_train", "night_val"])
for name in ["zs:pairwise", "zs:global_full", "bag+graph", "clock"]:
    print("pool AUROC", name, round(roc_auc_score(M.tip[pool], M[name][pool]), 3))
oo = json.load(open(f"{R}/results/llm_monitor/oof/results.json"))
print("(a) time_matched:", {k: round(v, 3) for k, v in oo["slices"]["time_matched_auroc"].items() if k in ("clock", "bag+graph", "zs:pairwise", "zs:global_full", "oracle")})
print("(a) mixed cfg x time:", {k: round(v, 3) for k, v in oo["slices"]["mixed_cfg_x_time_auroc"].items() if k in ("clock", "bag+graph", "zs:pairwise", "zs:global_full", "oracle")})
print("(a) paired diff keys containing clock:", [k for k in oo["paired_diffs_common_rows"] if "clock" in k][:5])
refs = sorted({k.split(" - ")[1].split("|")[0] for k in oo["paired_diffs_common_rows"]})
print("(a) refs used in paired diffs:", refs)
fr = sorted({k.split(" - ")[1].split("|")[0] for s in fz["splits"] for k in fz["splits"][s]["paired_diffs"]})
print("(b) refs used in paired diffs:", fr)
k0 = list(oo["paired_diffs_common_rows"])[0]; print("diff entry example:", k0, oo["paired_diffs_common_rows"][k0])
