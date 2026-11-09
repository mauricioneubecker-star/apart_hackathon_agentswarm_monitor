"""Per at-risk row: for each DM in window, the signed lag d = (sender first violation) - t. Bucket exposures."""
import glob, json, os, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
runs_dir, scen_dir, runner_dir, out = sys.argv[1:5]
W = 3
sys.path.insert(0, runner_dir)
from labels import message_edges_typed, read_jsonl
BUCKETS = ["Ebefore_le-4", "Ebefore_-3..-1", "btw_d<0", "btw_d0", "fut_+1", "fut_+2..3", "fut_+4..6", "fut_>=7", "never"]
rows = []; cfg = []; run = []
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")): continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_branch" in sid and os.path.exists(os.path.join(d, "branch.json")): continue
    sc = json.load(open(os.path.join(scen_dir, sid + ".json"))); L = json.load(open(os.path.join(d, "labels.json")))
    R = sc["rounds"]; pop = sc["population"]; agents = {a["agent_id"] for a in pop}
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in agents}
    dm_in = defaultdict(list)
    for m in read_jsonl(Path(d) / "messages.jsonl"):
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip(): continue
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct" and m["sender"] in agents:
                dm_in[dst].append((m["round"], m["sender"]))
    for a in sorted(agents - instructed):
        fa = first.get(a, 99)
        for t in range(1, min(R, fa) + 1):
            win = [x for x in dm_in[a] if max(1, t - W) <= x[0] < t]
            b = dict.fromkeys(BUCKETS, 0)
            for r, s in win:
                fs = first.get(s)
                if fs is None: b["never"] = 1; continue
                dd = fs - t
                if fs <= r:  # violator at message time (E_dir)
                    b["Ebefore_le-4" if dd <= -4 else "Ebefore_-3..-1"] = 1
                elif fs <= t:  # violates after message, by t
                    b["btw_d0" if dd == 0 else "btw_d<0"] = 1
                else:
                    b["fut_+1" if dd == 1 else "fut_+2..3" if dd <= 3 else "fut_+4..6" if dd <= 6 else "fut_>=7"] = 1
            rows.append([t, int(a in stuck), int(fa == t), int(bool(win))] + [b[k] for k in BUCKETS]); cfg.append(sid); run.append(f"{sid}/{rep}")
A = np.array(rows, float)
np.savez_compressed(out, A=A, cols=np.array(["t", "stuck", "Y", "dm_any"] + BUCKETS), cfg=np.array(cfg), run=np.array(run))
print(A.shape)
