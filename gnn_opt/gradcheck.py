#!/usr/bin/env python3
"""Finite-difference gradient check of the numpy autograd ops and the full Monitor loss.
  python3 gnn_opt/gradcheck.py [--data gnn_opt_data/night]
Uses the real graph structure of two runs with random continuous features (avoids ties at max / relu kinks)."""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ag  # noqa: E402
from model import Monitor  # noqa: E402
from train import Data  # noqa: E402


def check_op(name, f, shapes, rng, eps=1e-6):
    xs = [ag.Param(rng.normal(size=s)) for s in shapes]
    out = f(*xs)
    w = rng.normal(size=out.shape)
    L = ag.T(np.array((out.data * w).sum()), (out,), lambda g: (g * w,))
    L.backward()
    worst = 0.0
    for x in xs:
        g = x.grad
        flat = x.data.reshape(-1)
        for i in rng.choice(flat.size, min(20, flat.size), replace=False):
            old = flat[i]
            flat[i] = old + eps; fp = (f(*xs).data * w).sum()
            flat[i] = old - eps; fm = (f(*xs).data * w).sum()
            flat[i] = old
            num = (fp - fm) / (2 * eps)
            worst = max(worst, abs(num - g.reshape(-1)[i]) / max(1e-6, abs(num) + abs(g.reshape(-1)[i])))
    print(f"  {name:14s} max rel err {worst:.2e}")
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="gnn_opt_data/night")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    seg = ag.Seg(rng.integers(0, 5, 17), 6)        # includes an empty segment
    idx = rng.integers(0, 7, 13)
    K = ag.ema_kernel(6, 0.7)
    errs = [
        check_op("linear", lambda x, W, b: ag.linear(x, W, b), [(5, 4), (4, 3), (3,)], rng),
        check_op("relu/mul", lambda x, y: ag.mul(ag.relu(x), y), [(6, 3), (6, 3)], rng),
        check_op("sigmoid", lambda x: ag.sigmoid(x), [(6, 3)], rng),
        check_op("concat", lambda x, y: ag.concat([x, y]), [(4, 2), (4, 3)], rng),
        check_op("gather", lambda x: ag.gather(x, idx), [(7, 3)], rng),
        check_op("segsum", lambda x: ag.segsum(x, seg), [(17, 3)], rng),
        check_op("segmean", lambda x: ag.segmean(x, seg), [(17, 3)], rng),
        check_op("segmax", lambda x: ag.segmax(x, seg), [(17, 3)], rng),
        check_op("cummax", lambda x: ag.cummax_time(x), [(3, 6, 2)], rng),
        check_op("time_filter", lambda x: ag.time_filter(x, K), [(3, 6, 2)], rng),
        check_op("layernorm", lambda x, g, b: ag.layernorm(x, g, b), [(5, 4), (4,), (4,)], rng),
        check_op("bce", lambda z: ag.bce_logits(z, np.array([1, 0, np.nan, 1, 0.0])), [(5, 1)], rng),
        check_op("huber", lambda z: ag.huber(z, np.array([1, 0, np.nan, 3, 0.2])), [(5, 1)], rng),
    ]
    # full model
    D = Data(a.data, "gen")
    runs = [r for r in D.runs if D.S[D.S.run == r].tipped.iloc[0] == 1][:2]
    D.fit_scaler(runs)
    B = D.batch(runs)
    B["xn"] = rng.normal(size=B["xn"].shape)
    B["xe"] = rng.normal(size=B["xe"].shape)
    m = Monitor(D.fn, D.fe, {"h": 8, "dropout": 0.0, "edge_drop": 0.0, "layers": 2})
    for p in m.params():      # general position: zero-init biases + all-zero rows put LayerNorm exactly on a kink
        p.data += rng.normal(0, 0.1, p.data.shape)
    L = m.loss(m.forward(B), B)
    L.backward()
    ps = m.params()
    grads = [p.grad.copy() for p in ps]
    worst = 0.0
    eps = 1e-6
    for p, g in zip(ps, grads):
        flat = p.data.reshape(-1)
        for i in rng.choice(flat.size, min(6, flat.size), replace=False):
            old = flat[i]
            flat[i] = old + eps; lp = float(m.loss(m.forward(B), B).data)
            flat[i] = old - eps; lm = float(m.loss(m.forward(B), B).data)
            flat[i] = old
            num = (lp - lm) / (2 * eps)
            an = g.reshape(-1)[i]
            worst = max(worst, abs(num - an) / max(1e-6, abs(num) + abs(an)))
    print(f"  full Monitor   max rel err {worst:.2e} over {len(ps)} parameter tensors")
    errs.append(worst)
    ok = max(errs) < 1e-4
    print("GRADCHECK", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
