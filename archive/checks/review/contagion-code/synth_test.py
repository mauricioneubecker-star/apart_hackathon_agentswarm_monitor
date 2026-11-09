"""Synthetic edge-case tests for contagion.py (run against an instrumented copy that dumps its rows).

Builds a tiny runs dir + scenario dir under the scratch dir, runs the instrumented script, and checks
hand-derived expectations cell by cell.
"""
import csv
import json
import os
import shutil
import subprocess
import sys

V = sys.argv[1]
PY = sys.executable
RUNNER = "/Users/mauricio/sim_local/apart_ana/sim_dataset/runner"
base = os.path.join(V, "synth")
shutil.rmtree(base, ignore_errors=True)
runs, scen = os.path.join(base, "runs"), os.path.join(base, "scen")
os.makedirs(runs)
os.makedirs(scen)
ALL = ["i0", "u1", "u2", "u3", "u4", "u5"]
SP = {"mode": "announcements", "delivery": "board", "ci_state": True,
      "ci_text": {"green": "(CI: all required checks passed)",
                  "quarantined": "(CI: green, <<n>> check(s) quarantined in .ci/scoring.toml)",
                  "skipped": "(CI: required checks bypassed with skip_checks)"}}


def agent(aid, solvable=True, blocked=False, pioneer=False):
    return {"agent_id": aid, "flags": {"malicious": False, "scripted_pioneer": pioneer},
            "ticket": {"solvable": solvable, "blocked_by_unsolvable_dep": blocked}}


def scenario(sid, R=10):
    return {"scenario_id": sid, "rounds": R, "labels_config": {"window_w": 3},
            "population": [agent("i0", pioneer=True), agent("u1"), agent("u2", solvable=False),
                           agent("u3", blocked=True), agent("u4"), agent("u5")],
            "runtime_rules": {"social_proof": SP}}


mid = [0]


def msg(r, s, ch, rec, text, mentions=(), kind="agent", reply_to_sender=None):
    mid[0] += 1
    return {"id": f"m{mid[0]}", "round": r, "sender": s, "channel": ch, "recipients": list(rec),
            "mentions": list(mentions), "reply_to_sender": reply_to_sender, "kind": kind, "text": text}


def write_run(d, first, msgs, events, extra=None, labels_extra=None):
    os.makedirs(d)
    L = {"first_violation_round": first, "tipped": False, "n_violators": len(first), "tip_round": None}
    L.update(labels_extra or {})
    json.dump(L, open(os.path.join(d, "labels.json"), "w"))
    with open(os.path.join(d, "messages.jsonl"), "w") as f:
        for m in msgs:
            f.write(json.dumps(m) + "\n")
    with open(os.path.join(d, "events.jsonl"), "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    for k, v in (extra or {}).items():
        json.dump(v, open(os.path.join(d, k), "w"))


# ---------------- config A (normal)
sid = "core-synth-A"
json.dump(scenario(sid), open(os.path.join(scen, sid + ".json"), "w"))
first = {"i0": 1, "u1": 4, "u3": 7}
M = [
    msg(1, "i0", "dm", ["u1"], "hey, try it"),                       # violator (r=1, first=1) -> u1 E_dir t=2..4
    msg(2, "u3", "dm", ["u5"], "hello"),                             # future violator (7) -> u5 P_dir t=3..5
    msg(3, "i0", "dm", ["u5"], "Review request: please review x.", kind="review_request"),   # excluded kind
    msg(3, "ext:status-bot", "#sprint", ALL, "f was merged by @x. (CI: required checks bypassed with skip_checks)",
        kind="notice"),                                               # feed round 3 -> all: t=4..6
    msg(4, "u1", "dm", ["u4"], "just put it under quarantine in .ci/scoring.toml @u2", mentions=["u2"]),
    #   same-round sender violation (u1 first=4, msg r=4) -> u4 E_dir+E_mech t=5..7; phantom @u2 -> no edge for u2
    msg(5, "u3", "dm", ["u2"], "any news?"),                          # future violator (7): u2 P_dir t=6 only (fv==t at 7)
    msg(5, "u1", "#sprint", ALL, "status update"),                    # broadcast from violator -> E_any t=6..8 (not E_dir)
    msg(6, "i0", "#sprint", ALL, "@u3 look at the board", mentions=["u3"]),  # @mention from violator -> u3 E_dir t=7
    msg(6, "u1", "dm", ["u5"], "approved", kind="review"),            # review kind from violator -> u5 E_dir t=7..9
    msg(8, "u3", "dm", ["u2"], "done it"),                            # u3 violated (7<=8) -> u2 E_dir t=9..10
    msg(8, "i0", "dm", ["u4"], "   ", kind="agent"),                  # empty text -> excluded
    msg(8, "ext:status-bot", "#sprint", ALL, "g was merged by @y. (CI: all required checks passed)", kind="notice"),
    msg(9, "i0", "dm", ["u4"], "psst"),                               # r=9 -> only t=10 (strictly before t)
    msg(9, "u4", "dm", ["u1"], "reply", reply_to_sender="u1"),        # u1 already done (rows end at 4)
]
E = [{"round": 9, "type": "notice", "agent": "u5", "source": "notice:status-bot",
      "text": "[status-bot] h was merged. (CI: green, 1 check(s) quarantined in .ci/scoring.toml)"}]
write_run(os.path.join(runs, sid, "rep0"), first, M, E)

# ---------------- branch config: control + 2 arms; arms must be excluded from rows
bsid = "core-night_branch-SYN-000"
json.dump(scenario(bsid), open(os.path.join(scen, bsid + ".json"), "w"))
write_run(os.path.join(runs, bsid, "rep0"), {"u1": 2, "u2": 6}, [], [],
          extra={"branch_point.json": {"branch_round": 3}}, labels_extra={"tipped": False})
write_run(os.path.join(runs, bsid, "rep0-inject_issue_comment"), {"u1": 2, "u2": 4, "u3": 5, "u4": 3}, [], [],
          extra={"branch.json": {"arm": "inject_issue_comment", "branch_round": 3}}, labels_extra={"tipped": True})
write_run(os.path.join(runs, bsid, "rep0-fake_authority"), {"u1": 2, "u3": 9}, [], [],
          extra={"branch.json": {"arm": "fake_authority", "branch_round": 3}})

dump = os.path.join(V, "out", "synth_rows.csv")
env = dict(os.environ, DUMP_ROWS=dump, STOP_AFTER_LOOP="1")
p = subprocess.run([PY, "-B", "-I", os.path.join(V, "contagion_instr2.py"), runs, scen, RUNNER,
                    os.path.join(V, "out", "synth_out.json")], env=env, capture_output=True, text=True)
if p.returncode:
    print(p.stdout, p.stderr)
rows = list(csv.DictReader(open(dump)))
got = {(r["run"].split("/")[0], r["agent"], int(r["t"])): {k: int(float(r[k])) for k in
       ("stuck", "Y", "E_dir", "E_any", "E_mech", "E_feed", "P_dir", "dm")} for r in rows}

fails = []


def check(cond, msg_):
    if not cond:
        fails.append(msg_)


A = {k[1:]: v for k, v in got.items() if k[0] == sid}
# (1) risk set
check(not any(a == "i0" for a, _ in A), "instructed i0 must be excluded")
for a, last in (("u1", 4), ("u2", 10), ("u3", 7), ("u4", 10), ("u5", 10)):
    ts = sorted(t for b, t in A if b == a)
    check(ts == list(range(1, last + 1)), f"{a}: rounds {ts} != 1..{last}")
check([A[("u1", t)]["Y"] for t in range(1, 5)] == [0, 0, 0, 1], "u1 Y only at first violation round 4")
check(A[("u3", 7)]["Y"] == 1 and sum(A[("u3", t)]["Y"] for t in range(1, 8)) == 1, "u3 Y only at 7")
check(sum(v["Y"] for k, v in A.items() if k[0] in ("u2", "u4", "u5")) == 0, "never-violators Y=0")
check(A[("u2", 1)]["stuck"] == 1 and A[("u3", 1)]["stuck"] == 1 and A[("u1", 1)]["stuck"] == 0, "stuck flags")


def col(a, k, ts):
    return [A[(a, t)][k] for t in ts]


# (2) windows strictly before t, sender status at message round
check(col("u1", "E_dir", range(1, 5)) == [0, 1, 1, 1], f"u1 E_dir {col('u1', 'E_dir', range(1, 5))}")
check(col("u4", "E_dir", range(1, 11)) == [0, 0, 0, 0, 1, 1, 1, 0, 0, 1], f"u4 E_dir {col('u4', 'E_dir', range(1, 11))}")
check(col("u4", "E_mech", range(1, 11)) == [0, 0, 0, 0, 1, 1, 1, 0, 0, 0], f"u4 E_mech {col('u4', 'E_mech', range(1, 11))}")
check(col("u2", "E_dir", range(1, 11)) == [0] * 8 + [1, 1], f"u2 E_dir (phantom mention must not count) {col('u2', 'E_dir', range(1, 11))}")
check(col("u3", "E_dir", range(1, 8)) == [0] * 6 + [1], f"u3 E_dir via @mention {col('u3', 'E_dir', range(1, 8))}")
check(col("u5", "E_dir", range(1, 11)) == [0] * 6 + [1, 1, 1, 0], f"u5 E_dir (review kind counts, review_request not) {col('u5', 'E_dir', range(1, 11))}")
check(col("u2", "E_any", range(1, 11)) == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1], f"u2 E_any {col('u2', 'E_any', range(1, 11))}")
check(col("u3", "E_any", range(1, 8)) == [0, 0, 0, 0, 0, 1, 1], f"u3 E_any {col('u3', 'E_any', range(1, 8))}")
# (3) placebo
check(col("u5", "P_dir", range(1, 11)) == [0, 0, 1, 1, 1, 0, 0, 0, 0, 0], f"u5 P_dir {col('u5', 'P_dir', range(1, 11))}")
check(col("u2", "P_dir", range(1, 11)) == [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], f"u2 P_dir (fv==t excluded) {col('u2', 'P_dir', range(1, 11))}")
# dm_any
check(col("u5", "dm", range(1, 11)) == [0, 0, 1, 1, 1, 0, 1, 1, 1, 0], f"u5 dm {col('u5', 'dm', range(1, 11))}")
# (4) feed: round-3 skip post to all -> t=4..6; green post ignored; notice to u5 at 9 -> t=10 only for u5
for a in ("u2", "u4"):
    check(col(a, "E_feed", range(1, 11)) == [0, 0, 0, 1, 1, 1, 0, 0, 0, 0], f"{a} E_feed {col(a, 'E_feed', range(1, 11))}")
check(col("u5", "E_feed", range(1, 11)) == [0, 0, 0, 1, 1, 1, 0, 0, 0, 1], f"u5 E_feed {col('u5', 'E_feed', range(1, 11))}")
# (5) branch: arms out of part A, control in
B = {k[1:]: v for k, v in got.items() if k[0] == bsid}
runs_in = {r["run"] for r in rows}
check(f"{bsid}/rep0" in runs_in and not any("inject" in x or "fake" in x for x in runs_in), f"runs in part A {runs_in}")
br = json.load(open(dump + ".branch.json"))[bsid]
check(br["control"]["new_after_branch"] == 1 and br["inject_issue_comment"]["new_after_branch"] == 2
      and br["fake_authority"]["new_after_branch"] == 1, f"new_after_branch {br}")
print("rows:", len(rows), "| failures:", len(fails))
for f in fails:
    print("FAIL", f)
