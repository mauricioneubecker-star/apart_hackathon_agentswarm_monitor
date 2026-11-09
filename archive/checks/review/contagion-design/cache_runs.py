"""Cache per-run structures (read-only on run dirs) for fast re-labelling experiments (shuffle tests etc.)."""
import glob
import json
import os
import pickle
import sys
from collections import defaultdict, Counter
from pathlib import Path

runs_dir, scen_dir, runner_dir, out = sys.argv[1:5]
sys.path.insert(0, runner_dir)
from features import MECH_PATTERNS, lex_count  # noqa: E402
from labels import message_edges_typed, read_jsonl  # noqa: E402

cache = []
rule_first = Counter()
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    if "night_branch" in sid and os.path.exists(os.path.join(d, "branch.json")):
        continue
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    pop = sc["population"]
    agents = sorted(a["agent_id"] for a in pop)
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in set(agents)}
    att = {a: r for a, r in (L.get("first_attempt_round") or {}).items() if a in set(agents)}
    # first-violation rule per agent (from events)
    seen = set()
    for e in read_jsonl(Path(d) / "events.jsonl"):
        if e["type"] == "violation" and e.get("agent") in set(agents) and e["agent"] not in seen:
            seen.add(e["agent"])
            rule_first[(e.get("rule"), e["agent"] in instructed)] += 1
    dms = []   # (round, sender, reader, mech, reply_to_reader)
    for m in read_jsonl(Path(d) / "messages.jsonl"):
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct":
                dms.append((m["round"], m["sender"], dst, mech, m.get("reply_to_sender") == dst))
    cache.append({"cfg": sid, "run": f"{sid}/{rep}", "R": sc["rounds"], "agents": agents, "instructed": instructed,
                  "stuck": stuck, "first": first, "att": att, "dms": dms,
                  "seeded": bool(instructed), "early_adopter_source": sc["params"].get("early_adopter_source")})
pickle.dump(cache, open(out, "wb"))
print("runs", len(cache))
print("first-violation rules (rule, instructed):", dict(rule_first))
