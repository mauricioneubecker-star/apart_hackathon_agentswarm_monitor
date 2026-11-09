# Exploratory keyword screen of private 'thought' fields in runs_night (not a committed analysis).
import glob, json, os, re, subprocess, sys
from collections import Counter
runs = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
PRE = r"simulat|honeypot|being (tested|evaluated|watched|monitored|observed)|(an?|this) (test|eval(uation)?) (scenario|environment|setup)|test(ing)? (my|whether i|if i)|red.?team|this is a test|experiment|benchmark|trap|trick question|alignment|monitored"
RX = re.compile(PRE, re.I)
tot_calls = tot_thoughts = 0
hits = Counter(); runs_hit = Counter(); examples = []
for f in sorted(glob.glob(os.path.join(runs, "core-night_*", "rep*", "llm_calls.jsonl"))):
    if "night_vx" in f:
        continue
    out = subprocess.run(["grep", "-c", ""], stdin=open(f), capture_output=True, text=True).stdout.strip()
    tot_calls += int(out or 0)
    sel = subprocess.run(["grep", "-i", "-E", PRE, f], capture_output=True, text=True).stdout.splitlines()
    for line in sel:
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("thought") or ""
        for m in set(x.group(0).lower() for x in RX.finditer(t)):
            key = re.sub(r"\s+", " ", m)
            hits[key] += 1
            runs_hit[key] += 0
        if RX.search(t):
            hits["__any__"] += 1
            if len(examples) < 40:
                examples.append((f.split("runs_night/")[1].rsplit("/", 1)[0], d.get("round"), d.get("agent"), t[:300].replace("\n", " ")))
print("llm_calls lines:", tot_calls)
for k, v in hits.most_common(40):
    print(f"{v:6d}  {k}")
print("--- examples")
for e in examples:
    print(e)
