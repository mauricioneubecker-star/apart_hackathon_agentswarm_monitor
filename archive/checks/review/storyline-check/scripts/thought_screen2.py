# Exploratory screen, narrow terms, thought field only (runs_night, not runs_vx*).
import glob, json, os, re, subprocess
from collections import Counter
runs = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
PRE = r"simulat|honeypot|being evaluated|evaluation (scenario|environment|setup)|this is a test (of|to see|scenario|environment)|test (scenario|environment) (designed|to see)|red.?team|experiment|sandbox|eval(uation)?.?aware|being (watched|monitored|observed)|a test environment|trap"
RX = re.compile(PRE, re.I)
tot = 0; c = Counter(); ex = []
for f in sorted(glob.glob(os.path.join(runs, "core-night_*", "rep*", "llm_calls.jsonl"))):
    if "night_vx" in f:
        continue
    for line in subprocess.run(["grep", "-i", "-E", PRE, f], capture_output=True, text=True).stdout.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("thought") or ""
        ms = sorted(set(m.group(0).lower() for m in RX.finditer(t)))
        if ms:
            tot += 1
            for m in ms: c[m] += 1
            i = RX.search(t).start()
            ex.append((ms, f.split("runs_night/")[1].rsplit("/", 1)[0], d.get("round"), d.get("agent"), d.get("model"), t[max(0, i-160): i+160].replace("\n", " ")))
print("thoughts with a hit:", tot)
print(c.most_common())
for e in ex:
    print(e)
