"""For K2 proxy quarantines (editor adds a check owned by an agent who never violates), was the beneficiary
directly addressed by the editor in the 3 rounds up to the edit? Read-only."""
import glob, json, os, re, sys
from pathlib import Path
from collections import Counter
runs_dir, scen_dir, runner_dir = sys.argv[1:4]
sys.path.insert(0, runner_dir)
from labels import message_edges_typed, read_jsonl  # noqa: E402
c = Counter()
for d in sorted(glob.glob(os.path.join(runs_dir, "*K2*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")) or os.path.exists(os.path.join(d, "branch.json")):
        continue
    sid = os.path.basename(os.path.dirname(d))
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    ch = sc["params"]["channels"]
    pop = {a["agent_id"]: a for a in sc["population"]}
    fn2owner = {a["ticket"]["function"]: q for q, a in pop.items()}
    first = json.load(open(os.path.join(d, "labels.json")))["first_violation_round"]
    msgs = read_jsonl(Path(d) / "messages.jsonl")
    direct = set()
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        for s, dst, kind in message_edges_typed(m):
            if kind == "direct":
                direct.add((m["round"], s, dst))
    seen = set()
    for e in read_jsonl(Path(d) / "events.jsonl"):
        if e.get("type") != "tool" or e.get("tool") not in ("edit_file", "write_file"):
            continue
        a = e.get("args_full") or e.get("args") or {}
        if "scoring.toml" not in str(a.get("path", "")) or not str(e.get("result", "")).startswith("ok"):
            continue
        txt = str(a.get("new", "")) + " " + str(a.get("content", ""))
        for f in set(re.findall(r"acceptance/test_(\w+?)\.py", txt)):
            o = fn2owner.get(f)
            if not o or o == e["agent"] or first.get(o, 99) < 99 or (d, o) in seen:
                continue
            seen.add((d, o))
            r, ed = e["round"], e["agent"]
            talked = any((rr, x, y) in direct for rr in range(r - 3, r + 1) for x, y in ((ed, o), (o, ed)))
            c[(ch, "proxy_beneficiaries_distinct")] += 1; print("PROXY", sid + "/" + os.path.basename(d), o)
            c[(ch, "editor<->beneficiary direct msg in [r-3, r]")] += int(talked)
for k in sorted(c):
    print(k, c[k])
