"""Extended row builder for the contagion design review (read-only on run dirs).

Replicates analysis/contagion.py part A exactly (same at-risk set, same strata, same E_dir / P_dir / dm_any),
and adds alternative exposure definitions:
  P_between  DM in window from a sender who violates after the message but at or before t (dropped by original)
  P_eq_t     ... sender violates exactly at t (co-adoption, dropped by original)
  P_gt_r     DM from any sender who had not violated at message time but violates later (any time)
  P_near     DM from sender who violates in [t+1, t+3]
  P_far      DM from sender who violates at > t+3
  N_dir      DM from an agent who never violates in the run
  NC_same    DM sent IN round t (delivered only at t+1, so cannot affect round-t action) from a sender who had
             violated by t  (negative-control exposure)
  NC_same_s  same, sender violated by t-1
  NC_next    DM sent in round t+1 from a violator (future exposure; reverse causation possible)
  E_rev      reader SENT a direct message in the window to an agent who had violated by then (edge reversal)
  E_dir_reply  E_dir exposure where the violator's message is a reply to / quote of the reader
  E_dir_resp   E_dir exposure where the reader had sent that violator a direct msg in the 3 rounds before it
  R_mech     reader itself wrote a shortcut-lexicon message in the window (own intent)
  P_mech     placebo DM that names the shortcut
  P_instr    placebo DM from an instructed agent (pioneer / malicious)
  E_instr    E_dir DM from an instructed agent
Writes rows.npz (columns + names) into the out dir.
"""
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

runs_dir, scen_dir, runner_dir, out_dir = sys.argv[1:5]
W = int(sys.argv[5]) if len(sys.argv) > 5 else 3
sys.path.insert(0, runner_dir)
from features import MECH_PATTERNS, lex_count  # noqa: E402
from labels import message_edges_typed, read_jsonl  # noqa: E402

COLS = ["t", "stuck", "Y", "E_dir", "E_any", "E_mech", "P_dir", "dm_any",
        "P_between", "P_eq_t", "P_gt_r", "P_near", "P_far", "N_dir",
        "NC_same", "NC_same_s", "NC_next", "E_rev", "E_dir_reply", "E_dir_resp", "R_mech", "P_mech",
        "P_instr", "E_instr", "n_dm_in", "n_E_msgs", "n_P_msgs", "fa", "lag_min_E", "lag_P_min",
        "R_sent_dm", "instr_seeded"]
rows, cfgs, runs, agents_col = [], [], [], []
meta = {}
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_branch" in sid and os.path.exists(os.path.join(d, "branch.json")):
        continue
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    R = sc["rounds"]
    pop = sc["population"]
    agents = {a["agent_id"] for a in pop}
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in agents}
    msgs = read_jsonl(Path(d) / "messages.jsonl")
    dm_in = defaultdict(list)    # reader -> [(r, sender, fs, mech, reply_or_quote_to_reader)]
    dm_out = defaultdict(list)   # sender -> [(r, dst, fdst)]
    any_in = defaultdict(set)    # E_any rounds
    own_mech = defaultdict(set)  # agent -> rounds with own shortcut-lexicon message
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        s_viol = first.get(s, 99) <= r
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        if mech and s in agents:
            own_mech[s].add(r)
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct":
                rep_to = (m.get("reply_to_sender") == dst)
                dm_in[dst].append((r, s, first.get(s) if s in agents else None, mech, rep_to, s in agents, s in instructed))
                if s in agents:
                    dm_out[s].append((r, dst, first.get(dst)))
            if s_viol:
                any_in[dst].add(r)
    run = f"{sid}/{rep}"
    meta[run] = {"cfg": sid, "R": R, "n_instr": len(instructed)}
    for a in sorted(agents - instructed):
        fa = first.get(a, 99)
        ins = dm_in[a]
        outs = dm_out[a]
        for t in range(1, min(R, fa) + 1):
            lo = max(1, t - W)
            win = [x for x in ins if lo <= x[0] < t]
            E = [x for x in win if x[2] is not None and x[2] <= x[0]]
            P = [x for x in win if x[2] is not None and x[2] > t]
            Pb = [x for x in win if x[2] is not None and x[0] < x[2] <= t]
            Peq = [x for x in win if x[2] is not None and x[2] == t]
            Pgr = [x for x in win if x[2] is not None and x[2] > x[0]]
            Pn = [x for x in win if x[2] is not None and t + 1 <= x[2] <= t + 3]
            Pf = [x for x in win if x[2] is not None and x[2] > t + 3]
            Nd = [x for x in win if x[5] and x[2] is None]
            same = [x for x in ins if x[0] == t and x[2] is not None and x[2] <= t]
            same_s = [x for x in ins if x[0] == t and x[2] is not None and x[2] <= t - 1]
            nxt = [x for x in ins if x[0] == t + 1 and x[2] is not None and x[2] <= t + 1]
            rev = [x for x in outs if lo <= x[0] < t and x[2] is not None and x[2] <= x[0]]
            Ereply = [x for x in E if x[4]]
            # reader had DMed that violator in the 3 rounds before the violator's message
            # violator's msg at round x[0] could be a response to a reader DM sent in [x[0]-3, x[0]-1]
            Eresp = [x for x in E if any(o[1] == x[1] and x[0] - 3 <= o[0] <= x[0] - 1 for o in outs)]
            rmech = int(any(lo <= r_ < t for r_ in own_mech[a]))
            sent = int(any(lo <= o[0] < t for o in outs))
            lagE = min([x[2] - t for x in E], default=99)
            lagP = min([x[2] - t for x in P], default=99)
            rows.append([t, int(a in stuck), int(fa == t), int(bool(E)), int(any(lo <= r_ < t for r_ in any_in[a])),
                         int(any(x[3] for x in E)), int(bool(P)), int(bool(win)),
                         int(bool(Pb)), int(bool(Peq)), int(bool(Pgr)), int(bool(Pn)), int(bool(Pf)), int(bool(Nd)),
                         int(bool(same)), int(bool(same_s)), int(bool(nxt)), int(bool(rev)), int(bool(Ereply)),
                         int(bool(Eresp)), rmech, int(any(x[3] for x in P)),
                         int(any(x[6] for x in P)), int(any(x[6] for x in E)), len(win), len(E), len(P), fa, lagE, lagP,
                         sent, int(len(instructed) > 0)])
            cfgs.append(sid)
            runs.append(run)
            agents_col.append(a)
A = np.array(rows, dtype=float)
os.makedirs(out_dir, exist_ok=True)
np.savez_compressed(os.path.join(out_dir, f"rows_w{W}.npz"), A=A, cols=np.array(COLS), cfg=np.array(cfgs),
                    run=np.array(runs), agent=np.array(agents_col))
json.dump(meta, open(os.path.join(out_dir, "run_meta.json"), "w"))
print("rows", A.shape, "adoptions", int(A[:, 2].sum()), "runs", len(set(runs)), "cfgs", len(set(cfgs)))
