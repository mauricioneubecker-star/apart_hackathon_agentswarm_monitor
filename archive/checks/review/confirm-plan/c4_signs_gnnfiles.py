"""Issue 4: committed (b) per-split signs (exact values) and coverage of the committed GNN eval files."""
import io, json, subprocess
import pandas as pd
R = "/Users/mauricio/sim_local/apart_ana"
fz = json.load(open(f"{R}/results/llm_monitor/frozen/results.json"))
S = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]
for a, b in [("zs:pairwise", "clock"), ("zs:global_full", "clock"), ("zs:pairwise", "bag+graph"), ("zs:global_full", "bag+graph"),
             ("zs:global_full", "zs:pairwise")]:
    d = [fz["splits"][s]["metrics"][a]["auroc"] - fz["splits"][s]["metrics"][b]["auroc"] for s in S]
    print(f"{a} - {b}: " + " ".join(f"{x:+.3f}" for x in d), "signs", "".join("+" if x > 0 else "-" for x in d))
print("(b) predictors in committed frozen:", len(fz["splits"]["night_test_id"]["metrics"]))
first = subprocess.run(["git", "-C", R, "show", "a6c1d8a:results/llm_monitor/frozen/results.json"], capture_output=True, text=True).stdout
f1 = json.loads(first)
print("(b) predictors in a6c1d8a:", len(f1["splits"]["night_test_id"]["metrics"]), sorted(f1["splits"]["night_test_id"]["metrics"])[:20])
base = pd.read_csv(f"{R}/data/llm_monitor/_base/snapshots.csv", low_memory=False)
for ref in ["origin/gnn-opt-torch:gnn_opt_torch/preds/eval/final.csv", "origin/gnn-opt:gnn_opt/preds/eval/final_hybrid.csv",
            "origin/gnn-opt-torch:gnn_opt_torch/preds/eval/final+hgb_bag+graph+mem.csv"]:
    F = pd.read_csv(io.StringIO(subprocess.run(["git", "-C", R, "show", ref], capture_output=True, text=True).stdout))
    M = F.merge(base[["episode_id", "t", "split"]], left_on=["run", "round"], right_on=["episode_id", "t"], how="left")
    print(ref.split(":")[1], len(F), M.split.value_counts().to_dict())
