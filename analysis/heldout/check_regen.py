import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
B = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
S = pd.read_csv(f"{B}/stat/data/night/snapshots.csv", low_memory=False)
L = S[(S["eval"]==1)]
HO = ["night_test_id","night_test_ood_family","night_test_ood_seed","night_branch"]
def au(f, splits):
    P = pd.read_csv(f); d = L[L.split.isin(splits)].merge(P, on=["run","round"], how="inner")
    return len(d), roc_auc_score(d.y3, d.score)
E = f"{B}/heldout/preds/eval"; R = f"{B}/heldout/preds/regen"
for n, f in [("bag+graph committed(val)", f"{E}/hgb_bag+graph.csv"), ("bag+graph regen", f"{R}/hgb_bag+graph.csv"),
             ("bgm gnnopt committed(val)", f"{E}/hgb_bag+graph+mem__gnnopt_val.csv"), ("bgm torch allsplits", f"{E}/hgb_bag+graph+mem__allsplits.csv"), ("bgm regen", f"{R}/hgb_bag+graph+mem.csv")]:
    print(f"{n:28s} val n,AUROC {au(f,['night_val'])}" + ("" if "val)" in n else f"  heldout n,AUROC {au(f, HO)}"))
a = pd.read_csv(f"{E}/hgb_bag+graph+mem__gnnopt_val.csv"); b = pd.read_csv(f"{E}/hgb_bag+graph+mem__allsplits.csv")
j = a.merge(b, on=["run","round"]); print("bgm: gnn-opt val file vs torch allsplits on val rows: n", len(j), "max|diff|", (j.score_x-j.score_y).abs().max())
import json
out = {}
for n, f in [("bag+graph_committed", f"{E}/hgb_bag+graph.csv"), ("bag+graph_refit", f"{R}/hgb_bag+graph.csv"),
             ("tab_mem_committed", f"{E}/hgb_bag+graph+mem__allsplits.csv"), ("tab_mem_refit", f"{R}/hgb_bag+graph+mem.csv")]:
    out[n] = {"val_auroc": au(f, ["night_val"])[1]}
    if not n.startswith("bag+graph_committed"):
        out[n]["heldout_auroc"] = au(f, HO)[1]
json.dump(out, open(f"{B}/heldout/out/check_regen.json", "w"), indent=1)
print(out)
