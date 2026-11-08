"""Count tipped runs per validation arm. Reads ONLY runs_vx/*/rep*/labels.json (plus os.stat of those files)
and the scenario index outside runs_vx. Writes nothing into the run dirs."""
import csv
import datetime as dt
import glob
import json
import os
from collections import defaultdict

VX = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_vx"
IDX = "/Users/mauricio/sim_local/apart_vx/sim_dataset/dataset/index.csv"
arm_of = {}
base_of = {}
for r in csv.DictReader(open(IDX)):
    if "vx" in r["scenario_id"]:
        arm_of[r["scenario_id"]] = r.get("vx_arm") or ("rep" if "vx_rep" in r["scenario_id"] else "?")
        base_of[r["scenario_id"]] = r.get("vx_base")

files = sorted(glob.glob(os.path.join(VX, "*", "rep*", "labels.json")))
cut1720 = dt.datetime(2026, 11, 8, 17, 20).timestamp()
now = dt.datetime.now()
print("now:", now.strftime("%Y-%m-%d %H:%M"), "labels files:", len(files))
recs = []
for p in files:
    scen = os.path.basename(os.path.dirname(os.path.dirname(p)))
    rep = os.path.basename(os.path.dirname(p))
    try:
        d = json.load(open(p))
    except Exception as e:  # file may be mid-write
        print("unreadable", p, e)
        continue
    arm = arm_of.get(scen, "rep" if "vx_rep" in scen else "?")
    recs.append(dict(scen=scen, rep=rep, arm=arm, base=base_of.get(scen), tipped=bool(d.get("tipped")),
                     nv=d.get("n_violators"), mtime=os.stat(p).st_mtime, theta=d.get("theta_agents")))


def table(rs, title):
    agg = defaultdict(lambda: [0, 0, []])
    for r in rs:
        k = (r["arm"], r["rep"])
        agg[k][0] += 1
        agg[k][1] += r["tipped"]
        agg[k][2].append(r["nv"])
    print("\n==", title)
    for k in sorted(agg):
        n, t, nv = agg[k]
        print("  %-6s %-5s n=%2d tipped=%2d (%.0f%%)  mean violators %.1f" % (k[0], k[1], n, t, 100 * t / n,
                                                                          sum(nv) / len(nv)))


table(recs, "all labels.json present now")
table([r for r in recs if r["mtime"] <= cut1720], "labels.json written by 17:20")
print("\nlast labels mtime:", dt.datetime.fromtimestamp(max(r["mtime"] for r in recs)).strftime("%H:%M"))
print("theta values:", sorted({r['theta'] for r in recs}))

# paired comparison per base for rep0: arm vs id rep0, id rep1 vs id rep0
by = {(r["base"], r["arm"], r["rep"]): r for r in recs}
bases = sorted({r["base"] for r in recs if r["arm"] in ("id", "glm", "enf", "time", "topo")})
print("\nper base (rep0 tipped flags; '.' = missing):")
arms = ["id", "id1", "time", "glm", "enf", "topo"]
print("  %-24s " % "base" + " ".join("%5s" % a for a in arms))
for b in bases:
    cells = []
    for a in arms:
        key = (b, "id", "rep1") if a == "id1" else (b, a, "rep0")
        r = by.get(key)
        cells.append("%5s" % ("." if r is None else ("T" if r["tipped"] else "-")))
    print("  %-24s " % b + " ".join(cells))
for a in ["time", "glm", "enf", "topo"]:
    pairs = [(by[(b, "id", "rep0")], by[(b, a, "rep0")]) for b in bases if (b, "id", "rep0") in by and (b, a, "rep0") in by]
    up = sum(1 for x, y in pairs if y["tipped"] and not x["tipped"])
    down = sum(1 for x, y in pairs if x["tipped"] and not y["tipped"])
    print("  paired %-5s vs id rep0: pairs=%d, id tipped=%d, arm tipped=%d, flips up=%d down=%d" % (
        a, len(pairs), sum(x["tipped"] for x, _ in pairs), sum(y["tipped"] for _, y in pairs), up, down))
pairs = [(by[(b, "id", "rep0")], by[(b, "id", "rep1")]) for b in bases if (b, "id", "rep0") in by and (b, "id", "rep1") in by]
print("  noise id rep1 vs rep0: pairs=%d, rep0 tipped=%d, rep1 tipped=%d, flips=%d" % (
    len(pairs), sum(x["tipped"] for x, _ in pairs), sum(y["tipped"] for _, y in pairs),
    sum(1 for x, y in pairs if x["tipped"] != y["tipped"])))
