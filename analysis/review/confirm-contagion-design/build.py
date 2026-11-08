"""Independent re-build of the contagion.py Part-A inputs as per-run tensors (read-only on run dirs).

Per run we store, with agents indexed 0..N-1 (sorted ids) and rounds 1..R:
  D[s,a,r]    #direct msgs s->a in round r (kind agent/review, non-empty text, labels.message_edges_typed 'direct')
  Dm[s,a,r]   same, only messages naming the shortcut (MECH lexicon)
  Ball[s,a,r] #any reading edges s->a (direct+broadcast)
  DMany[a,r]  #direct msgs received from ANY sender (incl. non-agent senders)
  SelfMech[a,r] a sent >=1 agent/review message naming the shortcut in round r (any channel)
  feed[a,r]   merge-feed shortcut item seen
  f[a]        first violation round (99 = never), from labels.json (all agents)
  fatt[a]     first attempt round (99 = never), labels.json first_attempt_round
Output: runs.pkl in this directory.
"""
import glob
import json
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from labels import message_edges_typed, read_jsonl  # noqa: E402  (verbatim copy of runner/labels.py)
from mech import MECH_PATTERNS, lex_count  # noqa: E402            (verbatim copy of features.py lines 103-131)
from pathlib import Path  # noqa: E402

RUNS = "/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night"
SCEN = "/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/scenarios/core"


def feed_marks(sc):
    sp = sc["runtime_rules"].get("social_proof", {})
    if not sp.get("ci_state"):
        return None
    return [t.split("<<n>>")[-1] for k, t in (sp.get("ci_text") or {}).items() if k != "green" and t]


out = []
for d in sorted(glob.glob(os.path.join(RUNS, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_branch" in sid and os.path.exists(os.path.join(d, "branch.json")):
        continue
    sc = json.load(open(os.path.join(SCEN, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    R = sc["rounds"]
    pop = sc["population"]
    ids = sorted(a["agent_id"] for a in pop)
    ix = {a: i for i, a in enumerate(ids)}
    N = len(ids)
    byid = {a["agent_id"]: a for a in pop}
    instructed = np.array([bool(byid[a]["flags"].get("malicious") or byid[a]["flags"].get("scripted_pioneer")) for a in ids])
    stuck = np.array([bool((not byid[a]["ticket"]["solvable"]) or byid[a]["ticket"].get("blocked_by_unsolvable_dep")) for a in ids])
    f = np.full(N, 99, int)
    for a, r in L["first_violation_round"].items():
        if a in ix:
            f[ix[a]] = r
    fatt = np.full(N, 99, int)
    for a, r in (L.get("first_attempt_round") or {}).items():
        if a in ix:
            fatt[ix[a]] = r
    D = np.zeros((N, N, R + 2), np.int16)
    Dm = np.zeros((N, N, R + 2), np.int16)
    Ball = np.zeros((N, N, R + 2), np.int16)
    DMany = np.zeros((N, R + 2), np.int16)
    SelfMech = np.zeros((N, R + 2), bool)
    SelfMsg = np.zeros((N, R + 2), bool)
    msgs = read_jsonl(Path(d) / "messages.jsonl")
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        if s in ix:
            SelfMsg[ix[s], r] = True
            if mech:
                SelfMech[ix[s], r] = True
        for _, dst, kind in message_edges_typed(m):
            if dst not in ix:
                continue
            if kind == "direct":
                DMany[ix[dst], r] += 1
                if s in ix:
                    D[ix[s], ix[dst], r] += 1
                    if mech:
                        Dm[ix[s], ix[dst], r] += 1
            if s in ix:
                Ball[ix[s], ix[dst], r] += 1
    feed = np.zeros((N, R + 2), bool)
    marks = feed_marks(sc)
    if marks:
        for m in msgs:
            if m.get("sender") == "ext:status-bot" and any(x in str(m.get("text", "")) for x in marks):
                for rc in m.get("recipients") or []:
                    if rc in ix:
                        feed[ix[rc], m["round"]] = True
        for e in read_jsonl(Path(d) / "events.jsonl"):
            if e.get("type") == "notice" and "status-bot" in str(e.get("source", "")) and any(x in str(e.get("text", "")) for x in marks):
                if e.get("agent") in ix:
                    feed[ix[e.get("agent")], e["round"]] = True
    p = sc["params"]
    out.append(dict(sid=sid, run=f"{sid}/{rep}", R=R, w=int(sc["labels_config"]["window_w"]), ids=ids,
                    instructed=instructed, stuck=stuck, f=f, fatt=fatt, D=D, Dm=Dm, Ball=Ball, DMany=DMany,
                    SelfMech=SelfMech, SelfMsg=SelfMsg, feed=feed,
                    cat=sc["refs"]["category"], disc=p.get("discoverability"), split=sc.get("split"),
                    mem=p.get("memory_window_rounds"), channels=p.get("channels"),
                    params={k: v for k, v in p.items() if isinstance(v, (str, int, float, bool)) or v is None}))
pickle.dump(out, open(os.path.join(HERE, "runs.pkl"), "wb"))
print("runs", len(out), "configs", len({o["sid"] for o in out}))
