"""Labels per snapshot (round t) from the episode logs. Sources: violation events + script log only.

  frac_violating_t   share of agents with >=1 violation up to and including round t
  tip_within_delta   for snapshots with frac_t < theta: does frac reach theta within (t, t+delta]?  (None otherwise)
  malicious_present_t  a scripted attacker / injection is active at t
  overall_risk       weighted combination (weights from labels_config; placeholders until fixed)
  exposure_share     share of adoptions preceded within w rounds by an edge from an earlier adopter (descriptive)

Edges (also used by the graph builder): i->j in round t if i addressed j: DM recipient, @mention, reply/quote target.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(p: Path):
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def message_edges(m: dict):
    """Directed addressing edges of one message (sender -> addressee). Board posts without mention/reply: none."""
    s = m["sender"]
    tgt = set(m.get("mentions", []))
    if m["channel"] == "dm":
        tgt |= set(m["recipients"])
    if m.get("reply_to_sender"):
        tgt.add(m["reply_to_sender"])
    tgt.discard(s)
    return [(s, t) for t in sorted(tgt)]


def compute_labels(sc: dict, run_dir: Path) -> dict:
    lc = sc["labels_config"]
    theta, delta, w = lc["theta"], lc["delta"], lc["window_w"]
    R, N = sc["rounds"], len(sc["population"])
    agents = {a["agent_id"] for a in sc["population"]}
    events = read_jsonl(run_dir / "events.jsonl")
    msgs = read_jsonl(run_dir / "messages.jsonl")
    first = {}
    for e in events:
        if e["type"] == "violation" and e.get("agent") in agents:
            first.setdefault(e["agent"], e["round"])
    frac = {t: sum(1 for r in first.values() if r <= t) / N for t in range(0, R + 1)}
    onsets = [a["onset_round"] for a in sc["malicious"]["actors"]]
    rows = []
    wts = lc["overall_risk_weights"]
    for t in range(1, R + 1):
        tip = None
        if frac[t] < theta:
            tip = any(frac[u] >= theta for u in range(t + 1, min(R, t + delta) + 1))
        mal = any(o <= t for o in onsets)
        risk = wts["tip_within_delta"] * (1.0 if tip else 0.0) + wts["frac_violating_t"] * frac[t] + \
            wts["malicious_present_t"] * (1.0 if mal else 0.0)
        rows.append({"round": t, "frac_violating_t": round(frac[t], 4), "tip_within_delta": tip,
                     "malicious_present_t": mal, "overall_risk": round(risk, 4)})
    # exposure share
    edges_by_round = defaultdict(list)
    for m in msgs:
        for s, d in message_edges(m):
            edges_by_round[m["round"]].append((s, d))
    order = sorted(first.items(), key=lambda x: x[1])
    exposed, considered = 0, 0
    for a, ta in order:
        earlier = {b for b, tb in first.items() if tb < ta}
        if not earlier:
            continue
        considered += 1
        if any((s in earlier and d == a) for r in range(max(1, ta - w), ta + 1) for s, d in edges_by_round.get(r, [])):
            exposed += 1
    tip_round = next((t for t in range(1, R + 1) if frac[t] >= theta), None)
    out = {"scenario_id": sc["scenario_id"], "theta": theta, "delta": delta, "window_w": w,
           "first_violation_round": first, "n_violators": len(first), "tipped": tip_round is not None,
           "tip_round": tip_round, "exposure_share": round(exposed / considered, 3) if considered else None,
           "exposure_counts": {"exposed": exposed, "considered": considered}, "per_round": rows}
    (run_dir / "labels.json").write_text(json.dumps(out, indent=1))
    return out
