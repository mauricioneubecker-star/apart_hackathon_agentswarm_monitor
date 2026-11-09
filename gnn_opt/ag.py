"""Minimal reverse-mode autograd on numpy (float64), just the ops the GNN needs. Verified by gradcheck.py.

Tensor graph is built eagerly; backward() does a topological sweep. Segment ops take precomputed index structures
(Seg) so a batch is prepared once and reused by all layers.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp


class T:
    __slots__ = ("data", "grad", "parents", "back", "req")

    def __init__(self, data, parents=(), back=None, req=None):
        self.data = data
        self.grad = None
        self.parents = parents
        self.back = back
        self.req = any(p.req for p in parents) if req is None else req

    @property
    def shape(self):
        return self.data.shape

    def backward(self, g=None):
        order, seen = [], set()
        stack = [(self, False)]
        while stack:            # iterative DFS topological order
            n, done = stack.pop()
            if done:
                order.append(n)
                continue
            if id(n) in seen or not n.req:
                continue
            seen.add(id(n))
            stack.append((n, True))
            for p in n.parents:
                if id(p) not in seen and p.req:
                    stack.append((p, False))
        self.grad = np.ones_like(self.data) if g is None else g
        for n in reversed(order):
            if n.back is not None and n.grad is not None:
                gs = n.back(n.grad)
                for p, gp in zip(n.parents, gs):
                    if p.req and gp is not None:
                        p.grad = gp if p.grad is None else p.grad + gp
                n.grad = None            # free intermediate grads (Params have back=None and keep theirs)


class Param(T):
    __slots__ = ()

    def __init__(self, data):
        super().__init__(np.asarray(data, np.float64), (), None, True)


def const(x):
    return T(np.asarray(x, np.float64), (), None, False)


def _unbroadcast(g, shape):
    while g.ndim > len(shape):
        g = g.sum(0)
    for i, s in enumerate(shape):
        if s == 1 and g.shape[i] != 1:
            g = g.sum(i, keepdims=True)
    return g


def add(a, b):
    return T(a.data + b.data, (a, b), lambda g: (_unbroadcast(g, a.shape), _unbroadcast(g, b.shape)))


def sub(a, b):
    return T(a.data - b.data, (a, b), lambda g: (_unbroadcast(g, a.shape), -_unbroadcast(g, b.shape)))


def mul(a, b):
    return T(a.data * b.data, (a, b),
             lambda g: (_unbroadcast(g * b.data, a.shape), _unbroadcast(g * a.data, b.shape)))


def scale(a, c):
    return T(a.data * c, (a,), lambda g: (g * c,))


def matmul(a, W):
    return T(a.data @ W.data, (a, W), lambda g: (g @ W.data.T, a.data.T @ g))


def linear(a, W, b=None):
    out = a.data @ W.data
    if b is not None:
        out = out + b.data
        return T(out, (a, W, b), lambda g: (g @ W.data.T, a.data.T @ g, g.sum(0)))
    return T(out, (a, W), lambda g: (g @ W.data.T, a.data.T @ g))


def relu(a):
    m = a.data > 0
    return T(a.data * m, (a,), lambda g: (g * m,))


def leaky(a, s=0.1):
    m = np.where(a.data > 0, 1.0, s)
    return T(a.data * m, (a,), lambda g: (g * m,))


def sigmoid(a):
    s = 1 / (1 + np.exp(-np.clip(a.data, -40, 40)))
    return T(s, (a,), lambda g: (g * s * (1 - s),))


def tanh(a):
    t = np.tanh(a.data)
    return T(t, (a,), lambda g: (g * (1 - t * t),))


def concat(xs, axis=1):
    sizes = [x.shape[axis] for x in xs]
    cuts = np.cumsum(sizes)[:-1]

    def back(g):
        return tuple(np.split(g, cuts, axis=axis))
    return T(np.concatenate([x.data for x in xs], axis), tuple(xs), back)


def gather(a, idx, n_out=None):
    """rows a[idx]; backward scatter-adds (idx may repeat)."""
    n = a.shape[0]

    def back(g):
        if g.ndim == 2:
            M = sp.csr_matrix((np.ones(len(idx)), (idx, np.arange(len(idx)))), shape=(n, len(idx)))
            return (M @ g,)
        out = np.zeros(a.shape)
        np.add.at(out, idx, g)
        return (out,)
    return T(a.data[idx], (a,), back)


def permute(a, idx):
    """rows a[idx] where idx is a permutation (or injective): cheap backward."""
    def back(g):
        out = np.zeros(a.shape)
        out[idx] = g
        return (out,)
    return T(a.data[idx], (a,), back)


def reshape(a, shape):
    s0 = a.shape
    return T(a.data.reshape(shape), (a,), lambda g: (g.reshape(s0),))


class Seg:
    """Segment structure: item -> segment id (n_seg segments)."""

    def __init__(self, seg, n_seg):
        seg = np.asarray(seg, np.int64)
        self.seg, self.n = seg, n_seg
        self.cnt = np.bincount(seg, minlength=n_seg).astype(np.float64)
        self.S = sp.csr_matrix((np.ones(len(seg)), (seg, np.arange(len(seg)))), shape=(n_seg, len(seg)))
        self.ST = self.S.T.tocsr()
        self.order = np.argsort(seg, kind="stable")
        ss = seg[self.order]
        self.nonempty = np.unique(ss)
        self.starts = np.searchsorted(ss, self.nonempty) if len(ss) else np.zeros(0, np.int64)


def segsum(a, s: Seg):
    return T(np.asarray(s.S @ a.data), (a,), lambda g: (np.asarray(s.ST @ g),))


def segmean(a, s: Seg):
    inv = 1.0 / np.maximum(s.cnt, 1)[:, None]
    return T(np.asarray(s.S @ a.data) * inv, (a,), lambda g: (np.asarray(s.ST @ (g * inv)),))


def segmax(a, s: Seg, empty=0.0):
    out = np.full((s.n, a.shape[1]), empty)
    if len(s.seg):
        out[s.nonempty] = np.maximum.reduceat(a.data[s.order], s.starts, axis=0)
    mx = out[s.seg]
    mask = (a.data == mx).astype(np.float64)
    ties = np.asarray(s.S @ mask)
    ties[ties == 0] = 1

    def back(g):
        return ((g / ties)[s.seg] * mask,)
    return T(out, (a,), back)


def cummax_time(a):
    """a: [B, T, h] -> running max over T (causal). Gradient goes to the (first) argmax position."""
    x = a.data
    cm = np.maximum.accumulate(x, axis=1)
    B, Tn, h = x.shape
    # index of the position holding the running max (latest position that set a new max)
    is_new = np.concatenate([np.ones((B, 1, h), bool), x[:, 1:] > cm[:, :-1]], 1)
    pos = np.where(is_new, np.arange(Tn)[None, :, None], 0)
    pos = np.maximum.accumulate(pos, axis=1)

    def back(g):
        out = np.zeros_like(x)
        bi = np.arange(B)[:, None, None]
        hi = np.arange(h)[None, None, :]
        np.add.at(out, (np.broadcast_to(bi, pos.shape), pos, np.broadcast_to(hi, pos.shape)), g)
        return (out,)
    return T(cm, (a,), back)


def time_filter(a, K):
    """a: [B, T, h]; K: [T, T] constant causal (lower-triangular) filter; out[b,t] = sum_s K[t,s] a[b,s]."""
    B, Tn, h = a.shape

    def f(M, x):
        return (M @ x.transpose(1, 0, 2).reshape(Tn, B * h)).reshape(Tn, B, h).transpose(1, 0, 2)
    return T(f(K, a.data), (a,), lambda g: (f(K.T, g),))


def ema_kernel(Tn, alpha):
    """EMA m_t = alpha m_{t-1} + (1-alpha) x_t, m_0 = x_0 weight-normalised (so the start is not biased to 0)."""
    t = np.arange(Tn)
    K = np.where(t[:, None] >= t[None, :], alpha ** (t[:, None] - t[None, :]), 0.0)
    return K / K.sum(1, keepdims=True)


def lag_kernel(Tn, lag):
    K = np.zeros((Tn, Tn))
    for t in range(Tn):
        K[t, max(0, t - lag)] = 1.0
    return K


def layernorm(a, gamma, beta, eps=1e-3):
    x = a.data
    mu = x.mean(1, keepdims=True)
    var = x.var(1, keepdims=True)
    inv = 1 / np.sqrt(var + eps)
    xh = (x - mu) * inv
    out = xh * gamma.data + beta.data
    n = x.shape[1]

    def back(g):
        gxh = g * gamma.data
        gx = inv / n * (n * gxh - gxh.sum(1, keepdims=True) - xh * (gxh * xh).sum(1, keepdims=True))
        return gx, (g * xh).sum(0), g.sum(0)
    return T(out, (a, gamma, beta), back)


def dropout(a, p, rng, train=True):
    if not train or p <= 0:
        return a
    m = (rng.random(a.shape) >= p) / (1 - p)
    return T(a.data * m, (a,), lambda g: (g * m,))


# ------------------------------------------------------------------------------------------------- losses (scalar)
def bce_logits(z, y, w=None):
    """mean weighted BCE over entries where y is not NaN. z: [n] or [n,1]."""
    x = z.data.reshape(-1)
    yy = np.asarray(y, np.float64).reshape(-1)
    m = ~np.isnan(yy)
    ww = np.ones_like(x) if w is None else np.asarray(w, np.float64).reshape(-1)
    ww = ww * m
    yv = np.nan_to_num(yy)
    den = max(ww.sum(), 1e-9)
    l = (np.maximum(x, 0) - x * yv + np.log1p(np.exp(-np.abs(x)))) * ww
    p = 1 / (1 + np.exp(-np.clip(x, -40, 40)))
    shp = z.shape
    return T(np.array(l.sum() / den), (z,), lambda g: ((g * (p - yv) * ww / den).reshape(shp),))


def huber(z, y, d=1.0, w=None):
    x = z.data.reshape(-1)
    yy = np.asarray(y, np.float64).reshape(-1)
    m = ~np.isnan(yy)
    ww = (np.ones_like(x) if w is None else np.asarray(w, np.float64).reshape(-1)) * m
    r = x - np.nan_to_num(yy)
    a = np.abs(r)
    l = np.where(a <= d, 0.5 * r * r, d * (a - 0.5 * d)) * ww
    gr = np.where(a <= d, r, d * np.sign(r)) * ww
    den = max(ww.sum(), 1e-9)
    shp = z.shape
    return T(np.array(l.sum() / den), (z,), lambda g: ((g * gr / den).reshape(shp),))


def total(*terms):
    """weighted sum of scalar losses: total((w1, l1), (w2, l2), ...)."""
    terms = [(w, l) for w, l in terms if w]
    v = sum(w * float(l.data) for w, l in terms)
    return T(np.array(v), tuple(l for _, l in terms), lambda g: tuple(g * w for w, _ in terms))


# ------------------------------------------------------------------------------------------------------ optimiser
class Adam:
    def __init__(self, params, lr=3e-3, wd=0.0, b1=0.9, b2=0.999, eps=1e-8, clip=5.0):
        self.p = params
        self.lr, self.wd, self.b1, self.b2, self.eps, self.clip = lr, wd, b1, b2, eps, clip
        self.m = [np.zeros_like(p.data) for p in params]
        self.v = [np.zeros_like(p.data) for p in params]
        self.t = 0

    def step(self, lr=None):
        lr = self.lr if lr is None else lr
        self.t += 1
        gs = [p.grad if p.grad is not None else np.zeros_like(p.data) for p in self.p]
        nrm = np.sqrt(sum((g * g).sum() for g in gs))
        c = min(1.0, self.clip / (nrm + 1e-12)) if self.clip else 1.0
        for i, (p, g) in enumerate(zip(self.p, gs)):
            g = g * c
            self.m[i] = self.b1 * self.m[i] + (1 - self.b1) * g
            self.v[i] = self.b2 * self.v[i] + (1 - self.b2) * g * g
            mh = self.m[i] / (1 - self.b1 ** self.t)
            vh = self.v[i] / (1 - self.b2 ** self.t)
            p.data -= lr * (mh / (np.sqrt(vh) + self.eps) + self.wd * p.data)
            p.grad = None
