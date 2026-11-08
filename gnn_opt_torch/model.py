"""Spatio-temporal GNN monitor (pure torch scatter ops; PyG-equivalent layers, no extension modules needed).

  node/edge encoders -> L message-passing layers (GINE | relational GINE | GATv2 | graph-transformer, optional
  reverse-direction relations, virtual node, edge updates) with an optional node-level temporal block inserted after
  layer `tmem_at` (causal GRU over each agent's own history, or a causal temporal conv of width K = no clock beyond K)
  -> readout (mean / max / sum-norm over nodes + max / mean over edge embeddings [+ attention pool])
  -> optional graph-level temporal block (causal GRU / causal conv over the run's snapshot embeddings)
  -> heads: tip within D=3 (primary), tip within D=5, tip_rel within D=3, violator count (Poisson), node aux
     (agent violated by t, agent violates within D).
Relations: 0 direct, 1 broadcast, 2 both; with reverse=True also 3..5 = the same edges read dst -> src.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def seg_sum(v, idx, n):
    out = v.new_zeros((n,) + v.shape[1:])
    return out.index_add_(0, idx, v)


def seg_max(v, idx, n, fill=0.0):
    out = v.new_full((n,) + v.shape[1:], -1e9)
    out = out.scatter_reduce(0, idx.view(-1, *([1] * (v.dim() - 1))).expand_as(v), v, "amax", include_self=True)
    return torch.where(out <= -1e8, torch.full_like(out, fill), out)


def seg_softmax(a, idx, n):
    m = seg_max(a, idx, n)
    e = (a - m[idx]).exp()
    return e / (seg_sum(e, idx, n)[idx] + 1e-16)


def mlp(i, h, o, drop=0.0, layers=2):
    mods, d = [], i
    for _ in range(layers - 1):
        mods += [nn.Linear(d, h), nn.LayerNorm(h), nn.GELU(), nn.Dropout(drop)]
        d = h
    mods.append(nn.Linear(d, o))
    return nn.Sequential(*mods)


class MPLayer(nn.Module):
    def __init__(self, d, conv="rgine", n_rel=3, heads=4, aggr=("sum", "mean", "max"), drop=0.1, edge_update=True):
        super().__init__()
        self.conv, self.n_rel, self.heads, self.aggr, self.edge_update = conv, n_rel, heads, aggr, edge_update
        if conv in ("gine", "rgine"):
            nr = n_rel if conv == "rgine" else 1
            self.Wr = nn.Parameter(torch.randn(nr, d, d) / math.sqrt(d))
            self.br = nn.Parameter(torch.zeros(nr, d))
            self.We = nn.Linear(d, d)
            self.Wa = nn.Linear(d * len(aggr), d)
        elif conv in ("gatv2", "transformer"):
            assert d % heads == 0
            self.q = nn.Linear(d, d)
            self.k = nn.Linear(d, d)
            self.v = nn.Linear(d, d)
            self.e_k = nn.Linear(d, d)
            self.rel_emb = nn.Embedding(n_rel, d)
            if conv == "gatv2":
                self.att = nn.Parameter(torch.randn(heads, d // heads) / math.sqrt(d // heads))
            self.Wa = nn.Linear(d * (2 if "max" in aggr else 1), d)
        self.upd = mlp(2 * d, 2 * d, d, drop)
        self.norm = nn.LayerNorm(d)
        if edge_update:
            self.eupd = mlp(3 * d, 2 * d, d, drop)
            self.enorm = nn.LayerNorm(d)
        self.drop = nn.Dropout(drop)

    def forward(self, h, e, src, dst, rel):
        N = h.shape[0]
        if self.conv in ("gine", "rgine"):
            r = rel if self.conv == "rgine" else torch.zeros_like(rel)
            Hall = torch.einsum("nd,rdk->nrk", h, self.Wr) + self.br          # [N, R, d] (cheap: N << E)
            hs = Hall[src, r]
            m = F.gelu(hs + self.We(e))
            parts = []
            for a in self.aggr:
                if a == "sum":
                    parts.append(seg_sum(m, dst, N))
                elif a == "mean":
                    c = seg_sum(torch.ones_like(m[:, :1]), dst, N).clamp_min(1)
                    parts.append(seg_sum(m, dst, N) / c)
                elif a == "max":
                    parts.append(seg_max(m, dst, N))
            agg = self.Wa(torch.cat(parts, 1))
        else:
            H, dh = self.heads, h.shape[1] // self.heads
            ek = self.e_k(e) + self.rel_emb(rel)
            q = self.q(h)[dst].view(-1, H, dh)
            k = (self.k(h)[src] + ek).view(-1, H, dh)
            v = (self.v(h)[src] + ek).view(-1, H, dh)
            if self.conv == "gatv2":
                a = (F.leaky_relu(q + k, 0.2) * self.att).sum(-1)
            else:
                a = (q * k).sum(-1) / math.sqrt(dh)
            al = seg_softmax(a, dst, N)
            m = (v * al.unsqueeze(-1)).view(-1, H * dh)
            parts = [seg_sum(m, dst, N)]
            if "max" in self.aggr:
                parts.append(seg_max(v.view(-1, H * dh), dst, N))
            agg = self.Wa(torch.cat(parts, 1))
        h = self.norm(h + self.drop(self.upd(torch.cat([h, agg], 1))))
        if self.edge_update:
            e = self.enorm(e + self.drop(self.eupd(torch.cat([h[src], h[dst], e], 1))))
        return h, e


class TemporalBlock(nn.Module):
    """Causal temporal model over a [B, T, d] sequence (mask: valid steps). kind: gru | conv<K> | attn<K>."""

    def __init__(self, d, kind="gru", drop=0.1):
        super().__init__()
        self.kind = kind
        if kind == "gru":
            self.rnn = nn.GRU(d, d, batch_first=True)
        elif kind.startswith("conv"):
            self.K = int(kind[4:])
            self.conv = nn.Conv1d(d, d, self.K)
        elif kind.startswith("attn"):
            self.K = int(kind[4:])
            self.mha = nn.MultiheadAttention(d, 4, batch_first=True, dropout=drop)
        self.norm = nn.LayerNorm(d)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        B, T, d = x.shape
        if self.kind == "gru":
            y, _ = self.rnn(x)
        elif self.kind.startswith("conv"):
            y = self.conv(F.pad(x.transpose(1, 2), (self.K - 1, 0))).transpose(1, 2)
            y = F.gelu(y)
        else:
            i = torch.arange(T, device=x.device)
            mask = (i[None, :] > i[:, None]) | (i[:, None] - i[None, :] >= self.K)   # True = blocked
            y, _ = self.mha(x, x, x, attn_mask=mask)
        return self.norm(x + self.drop(y))


class STGNN(nn.Module):
    def __init__(self, d_node, d_edge, hid=64, layers=3, conv="rgine", reverse=True, vn=True, tmem="none",
                 tmem_at=1, gtemp="gru", drop=0.1, heads=4, aggr=("sum", "mean", "max"), edge_readout=True,
                 att_pool=True, edge_update=True, **_):
        super().__init__()
        self.reverse, self.vn, self.tmem_at, self.edge_readout, self.att_pool = reverse, vn, tmem_at, edge_readout, att_pool
        n_rel = 6 if reverse else 3
        self.nenc = mlp(d_node, hid, hid, drop)
        self.eenc = mlp(d_edge + n_rel, hid, hid, drop)
        self.n_rel = n_rel
        self.layers = nn.ModuleList([MPLayer(hid, conv, n_rel, heads, aggr, drop, edge_update) for _ in range(layers)])
        if vn:
            self.vn_mlp = nn.ModuleList([mlp(2 * hid, hid, hid, drop) for _ in range(layers)])
        self.tmem = TemporalBlock(hid, tmem, drop) if tmem != "none" else None
        ro = hid * 3 + (hid * 2 if edge_readout else 0) + (hid if att_pool else 0)
        if att_pool:
            self.gate = nn.Linear(hid, 1)
        self.proj = mlp(ro, hid * 2, hid, drop)
        self.gtemp = TemporalBlock(hid, gtemp, drop) if gtemp != "none" else None
        self.head_g = nn.Linear(hid, 4)          # y3, y5, yrel3, log-rate of risk count
        self.head_n = mlp(hid, hid, 2, drop)     # violated by t, violates within D

    def forward(self, b):
        x, src, dst, ef, rel, ng, G = b["x"], b["src"], b["dst"], b["ef"], b["rel"], b["ngraph"], b["G"]
        if self.reverse:
            src, dst = torch.cat([src, dst]), torch.cat([dst, src])
            ef = torch.cat([ef, ef])
            rel = torch.cat([rel, rel + 3])
        e = self.eenc(torch.cat([ef, F.one_hot(rel, self.n_rel).float()], 1))
        h = self.nenc(x)
        N = h.shape[0]
        cnt = seg_sum(h.new_ones(N, 1), ng, G).clamp_min(1)
        vn = h.new_zeros(G, h.shape[1])
        for li, layer in enumerate(self.layers):
            if self.vn:
                h = h + vn[ng]
            h, e = layer(h, e, src, dst, rel)
            if self.vn:
                vn = vn + self.vn_mlp[li](torch.cat([vn, seg_sum(h, ng, G) / cnt], 1))
            if self.tmem is not None and li + 1 == self.tmem_at:
                h = self._node_temporal(h, b["ntab"])
        parts = [seg_sum(h, ng, G) / cnt, seg_max(h, ng, G), seg_sum(h, ng, G) / 24.0]
        if self.att_pool:
            a = seg_softmax(self.gate(h).squeeze(-1), ng, G)
            parts.append(seg_sum(h * a[:, None], ng, G))
        if self.edge_readout:
            E2 = e.shape[0]
            eg = ng[dst]
            ce = seg_sum(e.new_ones(E2, 1), eg, G).clamp_min(1)
            parts += [seg_max(e, eg, G), seg_sum(e, eg, G) / ce]
        g = self.proj(torch.cat(parts, 1))
        if self.gtemp is not None:
            seq = b["seq"]
            B, T = seq.shape
            xs = g.new_zeros(B, T, g.shape[1])
            m = seq >= 0
            xs[m] = g[seq[m]]
            ys = self.gtemp(xs)
            g = g.clone()
            g[seq[m]] = ys[m]
        out_g = self.head_g(g)
        out_n = self.head_n(h)
        return out_g, out_n, g

    def _node_temporal(self, h, ntab):
        A, T = ntab.shape
        xs = h.new_zeros(A, T, h.shape[1])
        m = ntab >= 0
        xs[m] = h[ntab[m]]
        ys = self.tmem(xs)
        h2 = h.clone()
        h2[ntab[m]] = ys[m]
        return h2
