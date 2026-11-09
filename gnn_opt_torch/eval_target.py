#!/usr/bin/env python3
"""evaluate.py for the robustness targets (y5, yrel3, yrel5): drops rows where the target is undefined first
(gnn_opt/metrics.auroc returns NaN when NaN labels are present; y3-defined rows include 80 training rows with
yrel3 = NaN). Usage: python3 gnn_opt_torch/eval_target.py --target yrel3 --preds a.csv b.csv [evaluate.py args]"""
import os, subprocess, sys, tempfile
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
args = sys.argv[1:]
t = args[args.index("--target") + 1]
data = args[args.index("--data") + 1] if "--data" in args else os.path.join(REPO, "gnn_opt_data", "night")
S = pd.read_csv(os.path.join(data, "snapshots.csv"), low_memory=False)
ok = S[S[t].notna()][["run", "round"]]
i = args.index("--preds") + 1
tmp = tempfile.mkdtemp()
while i < len(args) and not args[i].startswith("--"):
    P = pd.read_csv(args[i]).merge(ok, on=["run", "round"])
    out = os.path.join(tmp, os.path.basename(args[i]))
    P.to_csv(out, index=False); args[i] = out; i += 1
if "--data" not in args:
    args += ["--data", data]
subprocess.run([sys.executable, os.path.join(REPO, "gnn_opt", "evaluate.py")] + args, check=True)
