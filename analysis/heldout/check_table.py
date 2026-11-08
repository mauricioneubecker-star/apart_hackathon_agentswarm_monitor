"""Is the local table.csv a deterministic function of graphs.npz in this environment? (diagnostic only)"""
import sys, numpy as np, pandas as pd
B = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
sys.path.insert(0, f"{B}/stat/repo/gnn_opt")
import harness as H, tabular
D = H.load(f"{B}/stat/data/night", table=True, graphs=True)
D2 = {k: D[k] for k in ("X", "EF", "ES", "ED", "node_snap", "node_name")}
D2["ecols"] = list(D["ecols"]); D2["ncols"] = list(D["ncols"]); D2["snaps"] = D["S"]
T2 = tabular.build_table(D2, lex=True, tool=True)
T = D["T"].drop(columns=["snap"])
print("cols equal:", list(T.columns) == list(T2.columns), len(T.columns), len(T2.columns))
bad = []
for c in T.columns:
    a, b = T[c].values.astype(float), T2[c].values.astype(float)
    d = np.nanmax(np.abs(a - b)) if len(a) else 0
    nanmis = (np.isnan(a) != np.isnan(b)).sum()
    if (d > 1e-9) or nanmis:
        bad.append((c, d, nanmis))
print("columns differing:", len(bad)); print(bad[:30])
import json
allmax = max([d for _, d, _ in bad] + [0.0])
json.dump({"n_cols": len(T.columns), "n_cols_differing": len(bad), "max_abs_diff": float(allmax),
           "nan_mismatch": int(sum(m for _, _, m in bad))}, open(f"{B}/heldout/out/check_table.json", "w"), indent=1)
print("overall max |diff|", allmax)
