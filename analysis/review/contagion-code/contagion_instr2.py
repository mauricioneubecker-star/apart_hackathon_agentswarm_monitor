"""Contagion checks on the night batch (descriptive, read-only; never writes into run dirs).

A. Exposure -> adoption (discrete-time, agent-round level). At-risk = uninstructed agent that has not violated
   before round t. Y = first violation in round t. Exposures are measured in the w rounds strictly before t:
     E_dir   direct message (DM / @mention / reply) from an agent who had already violated when sending it
     E_any   direct or broadcast reading edge from such an agent
     E_mech  E_dir and the message names the shortcut (task lexicon)
     E_feed  merge-feed post that shows a shortcut merge (CI skipped / quarantined)
     P_dir   PLACEBO: direct message from an agent who has NOT violated yet but will after t (homophily check)
   Mantel-Haenszel odds ratio / risk ratio within strata (run, round, stuck), i.e. same run, same round, same
   ticket situation. Variant "dm>0": only agent-rounds that received >= 1 direct message in the window (controls
   for being talked to at all). CI: bootstrap over configs.
B. Branch counterfactuals (night_branch): same prefix up to the branch round, then control / injected issue
   comment / fake manager message. Paired per config.

  python contagion.py <runs_night> <scenario_dir> <runner_dir> <out_json>
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

runs_dir, scen_dir, runner_dir, out_json = sys.argv[1:5]
sys.path.insert(0, runner_dir)
from features import MECH_PATTERNS, lex_count  # noqa: E402
from labels import message_edges_typed, read_jsonl  # noqa: E402
from pathlib import Path  # noqa: E402

rng = np.random.default_rng(0)
EXPO = ["E_dir", "E_any", "E_mech", "E_feed", "P_dir"]


def feed_marks(sc):
    sp = sc["runtime_rules"].get("social_proof", {})
    if not sp.get("ci_state"):
        return None
    return [t.split("<<n>>")[-1] for k, t in (sp.get("ci_text") or {}).items() if k != "green" and t]


AGENTS = []
rows = []          # (cfg, run, t, stuck, Y, E_dir, E_any, E_mech, E_feed, P_dir, dm_any)
branch = defaultdict(dict)
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    if "night_branch" in sid:
        bj = os.path.join(d, "branch.json")
        b = json.load(open(bj)) if os.path.exists(bj) else None
        arm = b["arm"] if b else "control"
        br = b["branch_round"] if b else json.load(open(os.path.join(d, "branch_point.json")))["branch_round"]
        first = L["first_violation_round"]
        branch[sid][arm] = {"tipped": bool(L["tipped"]), "n_viol": L["n_violators"],
                            "new_after_branch": sum(1 for r in first.values() if r > br),
                            "tip_round": L["tip_round"], "branch_round": br}
        if b:          # branch arms duplicate the control prefix: keep them out of part A
            continue
    R = sc["rounds"]
    w = int(os.environ.get("CONTAGION_W") or sc["labels_config"]["window_w"])   # robustness: CONTAGION_W=1/5
    pop = sc["population"]
    agents = {a["agent_id"] for a in pop}
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in agents}
    msgs = read_jsonl(Path(d) / "messages.jsonl")
    # per reader: rounds with each exposure type
    seen = {k: defaultdict(set) for k in ("E_dir", "E_any", "E_mech", "P_dir_src", "dm_any")}
    P_src = defaultdict(list)   # reader -> [(round, sender)] direct msgs from not-yet violators
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        s_viol = first.get(s, 99) <= r
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct":
                seen["dm_any"][dst].add(r)
                if s_viol:
                    seen["E_dir"][dst].add(r)
                    if mech:
                        seen["E_mech"][dst].add(r)
                elif s in first:
                    P_src[dst].append((r, first[s]))
            if s_viol:
                seen["E_any"][dst].add(r)
    marks = feed_marks(sc)
    feed = defaultdict(set)
    if marks:
        for m in msgs:
            if m.get("sender") == "ext:status-bot" and any(x in str(m.get("text", "")) for x in marks):
                for rc in m.get("recipients") or []:
                    feed[rc].add(m["round"])
        for e in read_jsonl(Path(d) / "events.jsonl"):
            if e.get("type") == "notice" and "status-bot" in str(e.get("source", "")) and any(x in str(e.get("text", "")) for x in marks):
                feed[e.get("agent")].add(e["round"])
    run = f"{sid}/{rep}"
    for a in sorted(agents - instructed):
        fa = first.get(a, 99)
        for t in range(1, min(R, fa) + 1):
            win = range(max(1, t - w), t)
            hit = lambda k: int(any(r in seen[k][a] for r in win))  # noqa: E731
            p_dir = int(any(r in win and fv > t for r, fv in P_src[a]))
            rows.append((sid, run, t, int(a in stuck), int(fa == t), hit("E_dir"), hit("E_any"), hit("E_mech"),
                         int(any(r in feed[a] for r in win)), p_dir, hit("dm_any")))
            AGENTS.append(a)

import csv as _csv
with open(os.environ["DUMP_ROWS"], "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["cfg","run","t","stuck","Y","E_dir","E_any","E_mech","E_feed","P_dir","dm","agent"])
    for _r, _a in zip(rows, AGENTS): _w.writerow(list(_r) + [_a])
json.dump({k: v for k, v in branch.items()}, open(os.environ["DUMP_ROWS"] + ".branch.json", "w"), indent=1)
if os.environ.get("STOP_AFTER_LOOP"):
    sys.exit(0)
A = np.array([r[2:] for r in rows], dtype=float)
cfg = np.array([r[0] for r in rows])
run = np.array([r[1] for r in rows])
T, STUCK, Y = A[:, 0], A[:, 1], A[:, 2]
X = {k: A[:, 3 + i] for i, k in enumerate(EXPO)}
DM = A[:, 8]
print(f"at-risk agent-rounds {len(Y)}, adoptions {int(Y.sum())}, runs {len(set(run))}, configs {len(set(cfg))}")


def mh(mask, x):
    """Per-config MH numerators/denominators within strata (run, t, stuck)."""
    keys = np.array([f"{a}|{int(b)}|{int(c)}" for a, b, c in zip(run[mask], T[mask], STUCK[mask])])
    y, e, cg = Y[mask], x[mask], cfg[mask]
    order = np.argsort(keys, kind="stable")
    keys, y, e, cg = keys[order], y[order], e[order], cg[order]
    bounds = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1], True])
    acc = defaultdict(lambda: np.zeros(6))   # or_num, or_den, rr_num, rr_den, n_exposed_events, n_strata_used
    for i in range(len(bounds) - 1):
        s = slice(bounds[i], bounds[i + 1])
        ys, es = y[s], e[s]
        n = len(ys)
        a_ = np.sum((es == 1) & (ys == 1)); b_ = np.sum((es == 1) & (ys == 0))
        c_ = np.sum((es == 0) & (ys == 1)); d_ = np.sum((es == 0) & (ys == 0))
        if (a_ + b_) == 0 or (c_ + d_) == 0 or (a_ + c_) == 0:
            continue
        v = acc[cg[s][0]]
        v += [a_ * d_ / n, b_ * c_ / n, a_ * (c_ + d_) / n, c_ * (a_ + b_) / n, a_, 1]
    return acc


def summarize(acc, nboot=2000):
    cf = list(acc)
    M = np.array([acc[c] for c in cf])
    if len(M) == 0 or M[:, 1].sum() == 0:
        return None
    est = lambda W: (W[:, 0].sum() / W[:, 1].sum(), W[:, 2].sum() / W[:, 3].sum())  # noqa: E731
    o, r = est(M)
    bo, brr = [], []
    for _ in range(nboot):
        W = M[rng.integers(0, len(M), len(M))]
        if W[:, 1].sum() > 0 and W[:, 3].sum() > 0:
            bo.append(W[:, 0].sum() / W[:, 1].sum()); brr.append(W[:, 2].sum() / W[:, 3].sum())
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return {"OR": float(o), "OR_ci": q(bo), "RR": float(r), "RR_ci": q(brr), "configs_informative": len(cf),
            "strata_used": int(M[:, 5].sum()), "exposed_adoptions_in_strata": int(M[:, 4].sum())}


res = {"n_agent_rounds": int(len(Y)), "n_adoptions": int(Y.sum()), "n_runs": len(set(run)), "n_configs": len(set(cfg)),
       "crude": {}, "mh": {}, "mh_dm>0": {}}
for k in EXPO:
    x = X[k]
    res["crude"][k] = {"share_exposed": float(x.mean()),
                       "p_adopt_exposed": float(Y[x == 1].mean()) if (x == 1).any() else None,
                       "p_adopt_unexposed": float(Y[x == 0].mean())}
    res["mh"][k] = summarize(mh(np.ones(len(Y), bool), x))
    if k in ("E_dir", "E_mech", "P_dir"):
        res["mh_dm>0"][k] = summarize(mh(DM == 1, x))

# B. branch counterfactuals, paired per config
B = {"configs": len(branch), "arms": {}}
for arm in ("inject_issue_comment", "fake_authority"):
    pairs = [(v["control"], v[arm]) for v in branch.values() if "control" in v and arm in v]
    dt = [int(b["tipped"]) - int(a["tipped"]) for a, b in pairs]
    dn = [b["new_after_branch"] - a["new_after_branch"] for a, b in pairs]
    # exact paired sign-flip test on the new violators after the branch point
    obs = np.mean(dn)
    flips = np.array(np.meshgrid(*[[1, -1]] * len(dn))).reshape(len(dn), -1).T
    null = (flips * np.array(dn)).mean(1)
    B["arms"][arm] = {"pairs": len(pairs), "tipped_control": sum(int(a["tipped"]) for a, _ in pairs),
                      "tipped_arm": sum(int(b["tipped"]) for _, b in pairs),
                      "tip_flips_up": sum(1 for x in dt if x > 0), "tip_flips_down": sum(1 for x in dt if x < 0),
                      "new_viol_after_branch_control_mean": float(np.mean([a["new_after_branch"] for a, _ in pairs])),
                      "new_viol_after_branch_arm_mean": float(np.mean([b["new_after_branch"] for _, b in pairs])),
                      "mean_diff": float(obs), "p_two_sided_signflip": float(np.mean(np.abs(null) >= abs(obs) - 1e-12)),
                      "per_config": {c: [v["control"]["new_after_branch"], v[arm]["new_after_branch"]]
                                     for c, v in branch.items() if "control" in v and arm in v}}
res["branch"] = B
json.dump(res, open(out_json, "w"), indent=1)
print(json.dumps(res, indent=1))
