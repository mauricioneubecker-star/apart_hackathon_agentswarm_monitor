"""K2 mechanics: does a scorer edit quarantine checks of OTHER agents' tickets (proxy shortcut, recipient need not
violate)? For every K2-scoring-write violation event, parse the quarantined acceptance test functions from the
edit and map them to ticket owners. Read-only.

  python k2_proxy.py <runs_night> <scenario_dir>
"""
import glob
import json
import os
import re
import sys
from collections import Counter

runs_dir, scen_dir = sys.argv[1:3]
tot = Counter()
benef_later = Counter()
for d in sorted(glob.glob(os.path.join(runs_dir, "*K2*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")) or os.path.exists(os.path.join(d, "branch.json")):
        continue
    sid = os.path.basename(os.path.dirname(d))
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    chan = sc["params"]["channels"]
    pop = {a["agent_id"]: a for a in sc["population"]}
    fn2owner = {a["ticket"]["function"]: q for q, a in pop.items()}
    L = json.load(open(os.path.join(d, "labels.json")))
    first = L["first_violation_round"]
    ev = [json.loads(x) for x in open(os.path.join(d, "events.jsonl")) if x.strip()]
    for e in ev:
        if e.get("type") != "tool" or e.get("tool") not in ("edit_file", "write_file"):
            continue
        a = e.get("args_full") or e.get("args") or {}
        if "scoring.toml" not in str(a.get("path", "")) or not str(e.get("result", "")).startswith("ok"):
            continue
        txt = str(a.get("new", "")) + " " + str(a.get("content", ""))
        fns = set(re.findall(r"acceptance/test_(\w+?)\.py", txt))
        owners = {fn2owner.get(f) for f in fns} - {None}
        me = e["agent"]
        others = owners - {me}
        tot[(chan, "edits")] += 1
        tot[(chan, "edits_with_other_owner_check")] += int(bool(others))
        tot[(chan, "edits_with_own_check")] += int(me in owners)
        for o in others:
            fo = first.get(o, 99)
            tot[(chan, "beneficiaries")] += 1
            benef_later[(chan, "already_violated" if fo <= e["round"] else
                         ("violates_later" if fo < 99 else "never_violates"))] += 1
for k in sorted(tot):
    print(k, tot[k])
for k in sorted(benef_later):
    print("beneficiary", k, benef_later[k])
