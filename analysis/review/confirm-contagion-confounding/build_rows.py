"""Independent rebuild of the contagion.py part-A rows, extended with per-row covariates.

Logic of the row construction is copied 1:1 from apart_vx/analysis/contagion.py (same at-risk set, same window,
same exposure definitions). Added columns: shortcut category (from sc['params']['category']), channel setting
(sc['params']['channels']), split of E_dir into private DM (channel == 'dm') vs public addressing (mention/reply in a
channel post), and the number of direct messages received in the window. Read-only on run dirs; writes one .npz.

  python build_rows.py <runs_night> <scenario_dir> <runner_dir> <out_npz> [w]
"""
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

runs_dir, scen_dir, runner_dir, out_npz = sys.argv[1:5]
W_OVERRIDE = int(sys.argv[5]) if len(sys.argv) > 5 else None
sys.path.insert(0, runner_dir)
from features import MECH_PATTERNS, lex_count  # noqa: E402
from labels import message_edges_typed, read_jsonl  # noqa: E402

cols = defaultdict(list)
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    if "night_branch" in sid:
        if os.path.exists(os.path.join(d, "branch.json")):
            continue   # branch arms duplicate the control prefix (same as contagion.py)
    R = sc["rounds"]
    w = W_OVERRIDE or int(sc["labels_config"]["window_w"])
    pop = sc["population"]
    agents = {a["agent_id"] for a in pop}
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in agents}
    msgs = read_jsonl(Path(d) / "messages.jsonl")
    seen = {k: defaultdict(set) for k in ("E_dir", "E_any", "E_mech", "dm_any", "E_dir_priv", "E_dir_pub",
                                           "dm_priv_any", "E_bc")}
    ndm = defaultdict(lambda: defaultdict(int))   # reader -> round -> number of direct msgs
    P_src = defaultdict(list)
    P_src_priv = defaultdict(list)
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        s_viol = first.get(s, 99) <= r
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        priv = m["channel"] == "dm"
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct":
                seen["dm_any"][dst].add(r)
                ndm[dst][r] += 1
                if priv:
                    seen["dm_priv_any"][dst].add(r)
                if s_viol:
                    seen["E_dir"][dst].add(r)
                    seen["E_dir_priv" if priv else "E_dir_pub"][dst].add(r)
                    if mech:
                        seen["E_mech"][dst].add(r)
                elif s in first:
                    P_src[dst].append((r, first[s]))
                    if priv:
                        P_src_priv[dst].append((r, first[s]))
            else:
                if s_viol:
                    seen["E_bc"][dst].add(r)
            if s_viol:
                seen["E_any"][dst].add(r)
    run = f"{sid}/{rep}"
    cat = sc["params"]["category"][:2]
    chan = sc["params"]["channels"]
    for a in sorted(agents - instructed):
        fa = first.get(a, 99)
        for t in range(1, min(R, fa) + 1):
            win = range(max(1, t - w), t)
            hit = lambda k: int(any(r in seen[k][a] for r in win))  # noqa: E731
            cols["cfg"].append(sid); cols["run"].append(run); cols["agent"].append(a)
            cols["cat"].append(cat); cols["chan"].append(chan)
            cols["t"].append(t); cols["stuck"].append(int(a in stuck)); cols["Y"].append(int(fa == t))
            for k in ("E_dir", "E_any", "E_mech", "dm_any", "E_dir_priv", "E_dir_pub", "dm_priv_any", "E_bc"):
                cols[k].append(hit(k))
            cols["P_dir"].append(int(any(r in win and fv > t for r, fv in P_src[a])))
            cols["P_dir_priv"].append(int(any(r in win and fv > t for r, fv in P_src_priv[a])))
            cols["ndm"].append(sum(ndm[a][r] for r in win))

out = {k: np.array(v) for k, v in cols.items()}
np.savez_compressed(out_npz, **out)
Y = out["Y"]
print(f"rows {len(Y)} adoptions {int(Y.sum())} runs {len(set(out['run']))} configs {len(set(out['cfg']))}")
