"""Re-run the dynamics_report.py logic (copied, read-only) over all night runs, plus extra breakdowns."""
import json
import statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/mauricio/sim_local/apart_ana/sim_dataset")
out = ROOT / "runs_night"
ds = ROOT / "dataset" / "scenarios" / "core"
eps = []
skipped = 0
for lab_f in sorted(out.glob("*/rep*/labels.json")):
    rd = lab_f.parent
    if not (rd / "meta.json").exists():
        skipped += 1
        continue
    sc = json.loads((ds / f"{rd.parent.name}.json").read_text())
    p, lab = sc["params"], json.loads(lab_f.read_text())
    cut = sc["spec"]["budget_time"]["deadline_round"]
    inst = set(sc["labels_config"].get("instructed_agents", []))
    first = lab["first_violation_round"]
    br = rd / "branch.json"
    arm = json.loads(br.read_text())["arm"] if br.exists() else "control"
    starter = None
    if first:
        fa = min(first, key=first.get)
        starter = ("instructed" if fa in inst else
                   ("after_injection" if arm != "control" or p.get("seed_type") == "external" else "organic"))
        # ties: several agents may share the minimum round
        mn = min(first.values())
        tied = [a for a, r in first.items() if r == mn]
        any_inst_at_min = any(a in inst for a in tied)
    else:
        any_inst_at_min = None
    eps.append(dict(cfg=rd.parent.name, run=rd.name, arm=arm, tipped=lab["tipped"], tip=lab["tip_round"], cut=cut,
                    starter=starter, any_inst_at_min=any_inst_at_min, seed=p.get("seed_type"), n_inst=len(inst),
                    exp=lab.get("exposure_counts") or {}, exp_dir=lab.get("exposure_counts_direct") or {},
                    exp_feed=lab.get("exposure_counts_feed") or {}))
print("episodes:", len(eps), "skipped (no meta):", skipped)
tipped = [e for e in eps if e["tipped"]]
print("tipped:", len(tipped), "configs:", len({e['cfg'] for e in tipped}))
c = Counter(e["starter"] for e in tipped)
print("who started (tipped):", dict(c), "organic share %.3f" % (c["organic"] / len(tipped)))
print("organic tipped by seed_type:", dict(Counter(e["seed"] for e in tipped if e["starter"] == "organic")))
print("organic tipped with n_instructed>0:", sum(1 for e in tipped if e["starter"] == "organic" and e["n_inst"] > 0))
print("organic tipped where an instructed agent tied for first round:",
      sum(1 for e in tipped if e["starter"] == "organic" and e["any_inst_at_min"]))
print("tipped by seed_type:", dict(Counter(e["seed"] for e in tipped)))
print("instructed counts by seed_type:", {s: Counter(e["n_inst"] for e in eps if e["seed"] == s) for s in
                                        sorted({e['seed'] for e in eps})})
# control-only tipped
tc = [e for e in tipped if e["arm"] == "control"]
cc = Counter(e["starter"] for e in tc)
print("control-only tipped:", len(tc), dict(cc), "organic share %.3f" % (cc["organic"] / len(tc)))
tcut = [e["tip"] - e["cut"] for e in tipped]
print("tip rel cut: median", st.median(tcut), "range", min(tcut), max(tcut), "distinct", len(set(tcut)))
ex = Counter()
for e in tipped:
    ex["considered"] += e["exp"].get("considered", 0)
    ex["any"] += e["exp"].get("exposed", 0)
    ex["direct"] += e["exp_dir"].get("exposed", 0)
    ex["direct_considered"] += e["exp_dir"].get("considered", 0)
    ex["feed"] += e["exp_feed"].get("exposed", 0)
    ex["feed_considered"] += e["exp_feed"].get("considered", 0)
print("exposure (tipped runs, dynamics_report convention):", dict(ex))
print("  direct/considered %.3f ; any/considered %.3f ; feed/considered %.3f ; feed/feed_considered %.3f" % (
    ex["direct"] / ex["considered"], ex["any"] / ex["considered"], ex["feed"] / ex["considered"],
    ex["feed"] / ex["feed_considered"]))
ex2 = Counter()
for e in eps:
    ex2["considered"] += e["exp"].get("considered", 0)
    ex2["direct"] += e["exp_dir"].get("exposed", 0)
    ex2["any"] += e["exp"].get("exposed", 0)
    ex2["feed"] += e["exp_feed"].get("exposed", 0)
    ex2["feed_considered"] += e["exp_feed"].get("considered", 0)
print("exposure (all runs):", dict(ex2), "direct share %.3f" % (ex2["direct"] / ex2["considered"]))
