import sys, os, json, glob
from collections import defaultdict
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1] + "/runner_copy")
from labels import message_edges_typed, read_jsonl
from pathlib import Path
V = sys.argv[1]; W = 3
ROOT = "/Users/mauricio/sim_local/apart_ana/sim_dataset"
rows = pd.read_csv(f"{V}/out/orig_rows_w3.csv")
key = {(r, a, t): i for i, (r, a, t) in enumerate(zip(rows.run, rows.agent, rows.t))}
Pb = np.zeros(len(rows), int); Pc = np.zeros(len(rows), int); Pa = np.zeros(len(rows), int)
rev_num = rev_den = 0
for run in rows.run.unique():
    d = f"{ROOT}/runs_night/{run}"
    sid = run.split("/")[0]
    sc = json.load(open(f"{ROOT}/dataset/scenarios/core/{sid}.json"))
    pop = {a["agent_id"] for a in sc["population"]}
    first = {a: r for a, r in json.load(open(d + "/labels.json"))["first_violation_round"].items() if a in pop}
    msgs = [m for m in read_jsonl(Path(d) / "messages.jsonl") if m.get("kind") in ("agent", "review") and str(m.get("text", "")).strip()]
    P = defaultdict(list); dm_edges = defaultdict(list)   # reader -> [(r, sender, fv)]
    for m in msgs:
        r, s = m["round"], m["sender"]
        for _, dst, kind in message_edges_typed(m):
            if kind != "direct": continue
            dm_edges[(s, dst)].append(r)
            if s in first and first[s] > r:
                P[dst].append((r, s, first[s]))
    for (rr, a, t), i in ((k, v) for k, v in key.items() if k[0] == run):
        win = [(r, s, fv) for r, s, fv in P[a] if t - W <= r <= t - 1 and r >= 1]
        Pa[i] = any(fv > t for _, _, fv in win)
        Pb[i] = any(fv >= t for _, _, fv in win)
        Pc[i] = bool(win)
        if Pa[i] and rows.Y[i] == 1:
            # reverse path: reader -> placebo sender direct message in [t, fv_s - 1]
            for _, s, fv in win:
                if fv > t:
                    rev_den += 1
                    rev_num += any(t <= r2 < fv for r2 in dm_edges.get((a, s), []))
assert (Pa == rows.P_dir.values).all(), "rebuilt P_dir must equal the script's"
rows["P_b"] = Pb; rows["P_c"] = Pc
def mh_boot(sub, x, nboot=2000):
    g = sub.assign(a=(sub[x]==1)&(sub.Y==1), b=(sub[x]==1)&(sub.Y==0), c=(sub[x]==0)&(sub.Y==1), d=(sub[x]==0)&(sub.Y==0))
    s = g.groupby(["cfg","run","t","stuck"])[["a","b","c","d"]].sum(); n = s.sum(axis=1)
    s = s.assign(orn=s.a*s.d/n, ord=s.b*s.c/n)
    P = s.groupby(level="cfg")[["orn","ord"]].sum(); P = P[(P.orn>0)|(P.ord>0)].values
    rng = np.random.default_rng(0); bo = []
    for _ in range(nboot):
        Wm = P[rng.integers(0, len(P), len(P))]
        if Wm[:,1].sum() > 0: bo.append(Wm[:,0].sum()/Wm[:,1].sum())
    return f"{P[:,0].sum()/P[:,1].sum():.2f} [{np.percentile(bo,2.5):.2f}; {np.percentile(bo,97.5):.2f}]"
dm = rows[rows.dm == 1]
for x, lab in (("P_dir","fv > t (as coded)"), ("P_b","fv >= t (incl. same-round co-adopters)"), ("P_c","fv > r (any not-yet violator)")):
    print(f"placebo {lab:42s} share {rows[x].mean():.4f} | MH all {mh_boot(rows,x)} | MH dm>0 {mh_boot(dm,x)}")
print(f"reverse path: placebo (Y=1) sender pairs where the reader DMed the sender in [t, fv_s): {rev_num}/{rev_den}")
print("--- E_dir in dm>0 against cleaner reference groups")
print("E_dir dm>0 as reported                          ", mh_boot(dm, "E_dir"))
print("E_dir dm>0, drop rows with any not-yet-violator DM (P_c==1 & E_dir==0 removed from reference)",
      mh_boot(dm[~((dm.P_c==1)&(dm.E_dir==0))], "E_dir"))
print("E_dir dm>0, drop all rows with P_c==1           ", mh_boot(dm[dm.P_c==0], "E_dir"))
print("E_dir all rows, drop all rows with P_c==1       ", mh_boot(rows[rows.P_c==0], "E_dir"))
c = dm.assign(cat=np.select([dm.E_dir==1, dm.P_dir==1, dm.P_c==1], ["E_dir", "P_dir(fv>t)", "gap(r<fv<=t)"], "never-violator DM only"))
print(c.groupby("cat").Y.agg(["size","sum","mean"]).to_string())
