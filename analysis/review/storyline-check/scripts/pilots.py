import json, subprocess, collections, sys
REPO = "/Users/mauricio/sim_local/apart_vx"
def ls(branch, path):
    out = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", f"origin/{branch}", path], capture_output=True, text=True).stdout.split()
    return out
def show(branch, path):
    return subprocess.run(["git", "-C", REPO, "show", f"origin/{branch}:{path}"], capture_output=True, text=True).stdout
for branch, d in [("night-vx-validation", "sim_dataset/runs"), ("night-vx-validation", "sim_dataset/runs_pilot2"), ("night-vx-validation", "sim_dataset/runs_pilot3"), ("main", "sim_dataset/runs_pilot4")]:
    files = [f for f in ls(branch, d + "/") if f.endswith("/labels.json") and f.count("/") == 4]
    tipped = 0; nv = 0; maxnv = 0; rounds = collections.Counter(); arms = 0; th = collections.Counter(); refuse = 0; nev = 0
    for f in files:
        j = json.loads(show(branch, f))
        tipped += bool(j["tipped"]); nv += j["n_violators"]; maxnv = max(maxnv, j["n_violators"])
        rounds[len(j["per_round"])] += 1; th[(j["theta_agents"], j["delta"])] += 1
        arms += "-" in f.split("/")[-2]
        ev = show(branch, f.replace("labels.json", "events.jsonl"))
        for l in ev.splitlines():
            if not l.strip(): continue
            e = json.loads(l); nev += 1
            if e.get("type") == "refuse": refuse += 1
    print(branch, d, "runs", len(files), "branch arms", arms, "tipped", tipped, "violators", nv, "max", maxnv, "rounds", dict(rounds), "theta/delta", dict(th), "refuse events", refuse, "events", nev)
