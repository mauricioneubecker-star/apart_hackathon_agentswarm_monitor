#!/usr/bin/env python3
"""Synthetic scaling testbed: complex contagion on small-world graphs, written in the canonical format.

Question: does the GNN gain over structure-agnostic baselines grow with graph size N when the signal lives in the
structure? Ground truth is known, so the test isolates the effect of graph size and topology.

Model (per episode):
  - Watts-Strogatz small world (N nodes, k neighbours, rewiring p); hidden susceptibility s_i ~ Beta(2,2).
  - n_seeds seed agents are "adopted" at t=0. Adopted agents send risky messages to each neighbour with prob q per round;
    every agent sends benign messages with prob b per neighbour and round.
  - Complex contagion (Centola): a susceptible agent j adopts at the end of round t with prob
        s_j * min(1, alpha * max(0, m_j - 1)),  m_j = #distinct adopted senders that messaged j in [t-w+1, t]
    -> one source is not enough, two or more are.
  - Observed (input): per directed pair and window the message volume and a noisy risky-content detector
    (TPR 0.8, FPR 0.05); per node a noisy susceptibility proxy. Adoption state itself is never observed.
Targets: graph `tip` (adopted >= theta*N within (t, t+delta], while below), `adopted_count` (count);
node `adopts_within_delta` (empty once adopted).

Usage: python -m gnn.adapters.synthetic --n 64 --episodes 400 --out data/synth_n64
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd


def small_world(n, k, p, rng):
    nb = [set() for _ in range(n)]
    for i in range(n):
        for d in range(1, k // 2 + 1):
            j = (i + d) % n
            nb[i].add(j), nb[j].add(i)
    for i in range(n):
        for d in range(1, k // 2 + 1):
            j = (i + d) % n
            if rng.random() < p and j in nb[i]:
                cand = [x for x in range(n) if x != i and x not in nb[i]]
                if cand:
                    new = int(rng.choice(cand))
                    nb[i].discard(j), nb[j].discard(i)
                    nb[i].add(new), nb[new].add(i)
    return [sorted(x) for x in nb]


def block_world(n, block, k, p, cross, rng):
    """n/block small-world communities (size `block`) + `cross` random cross-community edges per node."""
    nb = [set() for _ in range(n)]
    for o in range(0, n, block):
        for i, x in enumerate(small_world(block, k, p, rng)):
            nb[o + i] |= {o + j for j in x}
    if n > block:
        for i in range(n):
            if rng.random() < cross:
                j = int(rng.integers(n))
                if j // block != i // block:
                    nb[i].add(j), nb[j].add(i)
    return [sorted(x) for x in nb]


def episode(n, rng, R, k, p, q, b, alpha, w, n_seeds, seed_mode, block=0, cross=0.1):
    nb = block_world(n, block, k, p, cross, rng) if block else small_world(n, k, p, rng)
    s = rng.beta(2, 2, n)
    adopted = np.full(n, np.inf)
    if seed_mode == "near":      # seeds come in adjacent pairs (shared neighbourhood -> complex contagion can start)
        seeds = []
        for a in rng.choice(n, size=max(1, n_seeds // 2), replace=False):
            seeds += [int(a), int(rng.choice(nb[a]))]
        seeds = list(dict.fromkeys(seeds))[:n_seeds]
    else:                        # scattered singletons, evenly spaced on the ring (no shared neighbourhood at t=0)
        if block:                # far apart inside one community: no shared neighbourhood at t=0
            o = int(rng.integers(n // block)) * block
            off = int(rng.integers(block))
            seeds = [o + int((off + round(i * block / n_seeds)) % block) for i in range(n_seeds)]
        else:
            off = int(rng.integers(n))
            seeds = [int((off + round(i * n / n_seeds)) % n) for i in range(n_seeds)]
    adopted[seeds] = 0
    msgs = []                    # (t, src, dst, risky_true)
    for t in range(1, R + 1):
        for i in range(n):
            for j in nb[i]:
                if adopted[i] < t and rng.random() < q:
                    msgs.append((t, i, j, 1))
                elif rng.random() < b:
                    msgs.append((t, i, j, 0))
        senders = {}
        for (tm, i, j, rk) in msgs[-(len(msgs)):]:
            if rk and tm > t - w:
                senders.setdefault(j, set()).add(i)
        for j in np.where(~np.isfinite(adopted))[0]:
            m = len(senders.get(int(j), ()))
            if m >= 2 and rng.random() < s[j] * min(1.0, alpha * (m - 1)):
                adopted[j] = t
    return nb, s, adopted, np.array(msgs, dtype=int).reshape(-1, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--episodes", type=int, default=400)
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--p", type=float, default=0.1)
    ap.add_argument("--q", type=float, default=0.5)
    ap.add_argument("--b", type=float, default=0.3)
    ap.add_argument("--alpha", type=float, default=0.35)
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=0, help="number of seed agents (default max(2, round(N/12)))")
    ap.add_argument("--theta", type=float, default=0.3)
    ap.add_argument("--delta", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--block", type=int, default=0, help="community size; N = several communities (dilution test)")
    ap.add_argument("--cross", type=float, default=0.1, help="prob of one cross-community edge per node")
    ap.add_argument("--theta-abs", type=int, default=0, help="absolute tipping threshold (overrides theta*N)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    EP, SN, NO, ED, GL, NL = [], [], [], [], [], []
    theta_k = a.theta_abs or max(2, int(np.ceil(a.theta * a.n)))
    if not a.seeds:
        a.seeds = max(2, int(round(a.n / 12)))
    for e in range(a.episodes):
        mode = "near" if rng.random() < 0.5 else "any"
        nb, s, adopted, msgs = episode(a.n, rng, a.rounds, a.k, a.p, a.q, a.b, a.alpha, a.window, a.seeds, mode,
                                       a.block, a.cross)
        eid = f"n{a.n}_e{e}"
        split = "train" if e < 0.7 * a.episodes else ("val" if e < 0.85 * a.episodes else "test_id")
        EP.append({"episode_id": eid, "group_id": eid, "split": split, "seed_mode": mode, "n": a.n,
                   "final_adopted": int(np.isfinite(adopted).sum())})
        s_obs = np.clip(s + rng.normal(0, 0.2, a.n), 0, 1)
        obs_risky = np.where(msgs[:, 3] == 1, rng.random(len(msgs)) < 0.8, rng.random(len(msgs)) < 0.05).astype(int) \
            if len(msgs) else np.zeros(0, int)
        df = pd.DataFrame({"t": msgs[:, 0], "src": msgs[:, 1], "dst": msgs[:, 2], "obs": obs_risky}) \
            if len(msgs) else pd.DataFrame(columns=["t", "src", "dst", "obs"])
        cnt = {t: int((adopted <= t).sum()) for t in range(0, a.rounds + 1)}
        for t in range(1, a.rounds + 1):
            win = df[(df.t > t - a.window) & (df.t <= t)]
            agg = win.groupby(["src", "dst"]).agg(n=("obs", "size"), risky_max=("obs", "max"),
                                                  risky_sum=("obs", "sum")).reset_index()
            if len(agg):
                ED.append(pd.DataFrame({"episode_id": eid, "t": t, "src": "v" + agg.src.astype(str),
                                        "dst": "v" + agg.dst.astype(str), "etype": "msg",
                                        "volume": np.round(np.log1p(agg.n.values.astype(float)), 4),
                                        "risky_max": agg.risky_max.astype(int).values,
                                        "risky_frac": np.round(agg.risky_sum.values / agg.n.values, 4)}))
            for i in range(a.n):
                NO.append((eid, t, f"v{i}", round(float(s_obs[i]), 4)))
                f = adopted[i]
                NL.append((eid, t, f"v{i}", "" if f <= t else int(f <= t + a.delta)))
            hi = min(a.rounds, t + a.delta)
            tip = (int(any(cnt[u] >= theta_k for u in range(t + 1, hi + 1))) if cnt[t] < theta_k else "")
            GL.append((eid, t, tip, cnt[t]))
            SN.append((eid, t, t))
    pd.DataFrame(EP).to_csv(os.path.join(a.out, "episodes.csv"), index=False)
    pd.DataFrame(SN, columns=["episode_id", "t", "round"]).to_csv(os.path.join(a.out, "snapshots.csv"), index=False)
    pd.DataFrame(NO, columns=["episode_id", "t", "node_id", "susc_obs"]).to_csv(os.path.join(a.out, "nodes.csv"), index=False)
    pd.concat(ED).to_csv(os.path.join(a.out, "edges.csv"), index=False)
    gl = pd.DataFrame(GL, columns=["episode_id", "t", "tip", "adopted_count"])
    gl.to_csv(os.path.join(a.out, "graph_labels.csv"), index=False)
    pd.DataFrame(NL, columns=["episode_id", "t", "node_id", "adopts_within_delta"]).to_csv(
        os.path.join(a.out, "node_labels.csv"), index=False)
    tipv = pd.to_numeric(gl.tip, errors="coerce")
    stats = {"episodes": a.episodes, "n": a.n, "theta_k": theta_k, "tip_valid": int(tipv.notna().sum()),
             "tip_pos_rate": round(float(tipv.mean()), 3),
             "tipped_episodes": int(sum(1 for r in EP if r["final_adopted"] >= theta_k)),
             "mean_final_adopted_frac": round(float(np.mean([r["final_adopted"] for r in EP]) / a.n), 3)}
    schema = {"dataset": "synthetic-complex-contagion", "version": "synth-v1", "params": vars(a), "stats": stats,
              "node_features": [{"name": "susc_obs", "tier": 0, "groups": []}],
              "edge_features": [{"name": "volume", "tier": 0, "groups": []},
                                {"name": "risky_max", "tier": 1, "groups": ["content"]},
                                {"name": "risky_frac", "tier": 1, "groups": ["content"]}],
              "etypes": [{"name": "msg", "tier": 0, "groups": []}],
              "graph_labels": {"tip": {"type": "binary"}, "adopted_count": {"type": "count", "max": a.n}},
              "node_labels": {"adopts_within_delta": {"type": "binary"}},
              "time_features": ["round"], "strata": ["seed_mode"], "default_drop_groups": []}
    json.dump(schema, open(os.path.join(a.out, "schema.json"), "w"), indent=1)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
