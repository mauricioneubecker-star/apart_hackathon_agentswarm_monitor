#!/usr/bin/env python3
"""How diverse are the tipping dynamics? Checks that the GNN cannot get away with one pattern.

  python3 tools/dynamics_report.py runs_night            (pure Python, no pandas/sklearn needed)

1. Shortcut baselines for the per-round target tip_within_delta (AUROC, leave-one-config-out lookup tables):
   time only (cycle t), time to cut (t - cut), config only (factor levels), current risk count.
   A GNN result only means something well above these.
2. Dynamics diversity of the tipped episodes: tip cycle relative to cut and to the manager push, cascade speed,
   who started (instructed seed / organic / after injection), exposure channel of the adopters
   (direct DM/mention, broadcast post, merge feed, none), and how many distinct episodes/configs carry the positives.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORS = ["category", "seed_type", "release_freeze", "manager_push", "discoverability", "channels", "self_merge",
           "persistent_share", "prohibition_form", "n_impossible", "persona_mix", "sanctions", "seed_placement"]


def auroc(scores, labels):
    pairs = sorted(zip(scores, labels))
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if not n_pos or not n_neg:
        return None
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg = (i + j + 1) / 2
        rank_sum += avg * sum(1 for k in range(i, j) if pairs[k][1])
        i = j
    return (rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def loo_lookup(rows, key):
    """Score = positive rate of the same key value in all OTHER configs (no leakage within a config)."""
    tot, pos = defaultdict(lambda: Counter()), defaultdict(lambda: Counter())
    for r in rows:
        tot[key(r)][r["config"]] += 1
        pos[key(r)][r["config"]] += r["y"]
    out = []
    for r in rows:
        k = key(r)
        t = sum(tot[k].values()) - tot[k][r["config"]]
        p = sum(pos[k].values()) - pos[k][r["config"]]
        out.append(p / t if t else 0.0)
    return out


def main(out: Path):
    ds = ROOT / "dataset" / "scenarios" / "core"
    rows, eps = [], []
    for lab_f in sorted(out.glob("*/rep*/labels.json")):
        rd = lab_f.parent
        if not (rd / "meta.json").exists():
            continue
        sc = json.loads((ds / f"{rd.parent.name}.json").read_text())
        p, lab = sc["params"], json.loads(lab_f.read_text())
        cut = sc["spec"]["budget_time"]["deadline_round"]
        push = [t["round"] for t in sc["timeline"] for e in t["events"]
                if e.get("sender") == "ext:eng-manager" and "excuses" in str(e.get("text", ""))]
        inst = set(sc["labels_config"].get("instructed_agents", []))
        first = lab["first_violation_round"]
        organic = sorted(r for a, r in first.items() if a not in inst)
        br = rd / "branch.json"
        arm = json.loads(br.read_text())["arm"] if br.exists() else "control"
        cfg = rd.parent.name
        fac = tuple(str(p.get(f)) for f in FACTORS)
        for pr in lab["per_round"]:
            rows.append({"config": cfg, "t": pr["round"], "to_cut": pr["round"] - cut, "fac": fac,
                         "risk": pr["risk_count_t"], "y": int(bool(pr["tip_within_delta"]))})
        eps.append({"run": f"{cfg}/{rd.name}", "config": cfg, "arm": arm, "tipped": lab["tipped"],
                    "tip": lab["tip_round"], "cut": cut, "push": push[0] if push else None,
                    "first_any": min(first.values()) if first else None, "first_org": organic[0] if organic else None,
                    "starter": ("instructed" if first and min(first, key=first.get) in inst else
                                ("after_injection" if arm != "control" or p.get("seed_type") == "external" else "organic"))
                    if first else None,
                    "n": lab["n_violators"], "exp": lab.get("exposure_counts") or {},
                    "exp_dir": lab.get("exposure_counts_direct") or {}, "exp_feed": lab.get("exposure_counts_feed") or {},
                    "cat": p.get("category", "")[:2], "seed": p.get("seed_type")})
    if not eps:
        print("no finished episodes with labels")
        return
    print(f"# Dynamics report: {out.name}\n\n{len(eps)} episodes, {len({e['config'] for e in eps})} configs, "
          f"{sum(e['tipped'] for e in eps)} tipped, {len(rows)} (episode, cycle) rows, "
          f"{sum(r['y'] for r in rows)} positive rows (tip_within_delta)\n")
    y = [r["y"] for r in rows]
    print("## 1. Shortcut baselines (AUROC for tip_within_delta; GNN must clearly beat these)\n")
    per_factor = [loo_lookup(rows, lambda r, i=i: r["fac"][i]) for i in range(len(FACTORS))]
    config_score = [sum(v[k] for v in per_factor) / len(per_factor) for k in range(len(rows))]
    tcut = loo_lookup(rows, lambda r: r["to_cut"])
    for name, score in [("time only (cycle t)", loo_lookup(rows, lambda r: r["t"])), ("time to cut (t - cut)", tcut),
                        ("config only (mean of per-factor rates)", config_score),
                        ("time to cut + config", [a + b for a, b in zip(tcut, config_score)]),
                        ("current risk count (violation events, NOT a GNN input)", loo_lookup(rows, lambda r: r["risk"]))]:
        a = auroc(score, y)
        print(f"- {name}: {a:.3f}" if a is not None else f"- {name}: n/a")
    tipped = [e for e in eps if e["tipped"]]
    print("\n## 2. Diversity of the tipped episodes\n")
    if not tipped:
        print("no tipped episodes")
        return
    print(f"- carried by {len(tipped)} episodes from {len({e['config'] for e in tipped})} distinct configs "
          f"(branch arms share their prefix: count configs, not arms)")
    tc = [e["tip"] - e["cut"] for e in tipped]
    print(f"- tip cycle relative to the cut: median {st.median(tc)}, range {min(tc)}..{max(tc)}, "
          f"distinct values {len(set(tc))}; absolute tip cycles {sorted(Counter(e['tip'] for e in tipped).items())}")
    tp = [e["tip"] - e["push"] for e in tipped if e["push"]]
    if tp:
        print(f"- tip cycle relative to the manager push: median {st.median(tp)}, range {min(tp)}..{max(tp)}; "
              f"tipped without push: {sum(1 for e in tipped if not e['push'])}")
    sp = [e["tip"] - e["first_any"] for e in tipped if e["first_any"]]
    print(f"- cascade speed (first violation -> theta): median {st.median(sp)} cycles, range {min(sp)}..{max(sp)}")
    print(f"- who started: {dict(Counter(e['starter'] for e in tipped))}; category {dict(Counter(e['cat'] for e in tipped))}; "
          f"seed type {dict(Counter(e['seed'] for e in tipped))}")
    ex = Counter()
    for e in tipped:
        ex["adopters considered"] += e["exp"].get("considered", 0)
        ex["exposed via any message edge"] += e["exp"].get("exposed", 0)
        ex["exposed via direct DM/mention"] += e["exp_dir"].get("exposed", 0)
        ex["exposed via merge feed"] += e["exp_feed"].get("exposed", 0)
    print(f"- exposure channels of later adopters: {dict(ex)}")
    print("\nRead: if (a) the time/config baselines are close to 1, (b) tip cycles sit at one value relative to the cut,\n"
          "(c) one category/seed type/channel carries almost all positives, the GNN can learn one pattern. Then\n"
          "evaluate stratified (per category, seed type, push yes/no, channel) and leave-one-level-out.")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "runs_night"))
