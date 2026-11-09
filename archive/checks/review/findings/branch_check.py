"""Recompute branch counterfactual numbers from labels.json (read-only)."""
import glob
import itertools
import json
import os
from math import comb

ROOT = "/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night"
res = {}
for bp in sorted(glob.glob(os.path.join(ROOT, "*", "*", "branch_point.json"))):
    cdir = os.path.dirname(bp)
    cfg = os.path.basename(os.path.dirname(cdir))
    b = json.load(open(bp))
    br = b["branch_round"]
    out = {}
    for arm in ["control", "inject_issue_comment", "fake_authority"]:
        d = cdir if arm == "control" else cdir + "-" + arm
        lab = json.load(open(os.path.join(d, "labels.json")))
        fv = lab["first_violation_round"]
        before = sum(1 for r in fv.values() if r <= br)
        after = sum(1 for r in fv.values() if r > br)
        out[arm] = dict(before=before, after=after, tipped=lab["tipped"], nv=lab["n_violators"])
    res[cfg] = out
    print(cfg, "branch_round", br, {a: (v["before"], v["after"], v["tipped"]) for a, v in out.items()})


def signflip_p(diffs):
    obs = abs(sum(diffs))
    n = 0
    tot = 0
    for signs in itertools.product([1, -1], repeat=len(diffs)):
        s = abs(sum(x * y for x, y in zip(diffs, signs)))
        tot += 1
        if s >= obs - 1e-12:
            n += 1
    return n / tot


def sign_test_p(diffs):
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    k = min(pos, neg)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p), pos, neg


for arm in ["inject_issue_comment", "fake_authority"]:
    diffs = [res[c][arm]["after"] - res[c]["control"]["after"] for c in res]
    ctrl = [res[c]["control"]["after"] for c in res]
    trt = [res[c][arm]["after"] for c in res]
    pre_same = all(res[c][arm]["before"] == res[c]["control"]["before"] for c in res)
    print("\n", arm, "diffs", diffs, "ctrl mean %.3f arm mean %.3f ratio %.2f" % (
        sum(ctrl) / 8, sum(trt) / 8, (sum(trt) / 8) / (sum(ctrl) / 8)))
    print("  tipped control %d arm %d" % (sum(res[c]["control"]["tipped"] for c in res),
                                          sum(res[c][arm]["tipped"] for c in res)))
    print("  same pre-branch violators in all pairs:", pre_same)
    print("  sign-flip permutation p (two-sided): %.4f" % signflip_p(diffs))
    print("  classic exact sign test p (two-sided), pos/neg:", sign_test_p(diffs))
