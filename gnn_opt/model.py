"""Numpy temporal GNN monitor (autograd in ag.py).

Per round t: directed reading graph (src -> dst = dst read src's messages in [t-2, t]).
  1. encoders: node x -> h, edge e -> h
  2. L relational message-passing layers. Two relations per edge: 'in' (dst aggregates f(h_src, e): what a node
     read) and 'out' (src aggregates f'(h_dst, e): what a node said and to whom). Aggregation mean + max (robust to the
     density differences between board / team / dm channel modes), residual update.
  3. causal node memory over rounds (per agent): running max, EMA(0.5), EMA(0.85), lag-3 delta -> node state s_t
  4. node heads: agent has violated by t (state), agent violates within Delta
  5. graph readout per snapshot: mean/max of s_t, soft count = sum sigmoid(state logit), mean/max of edge messages,
     log #edges; temporal graph delta g_t - g_{t-3}
  6. heads: tip within Delta (primary), violator count (secondary)
No clock / round index enters; memory is causal (filters are lower-triangular).
"""
from __future__ import annotations

import numpy as np

import ag
from ag import Param

DEFAULT = dict(h=32, layers=2, mem=True, mem_alphas=(0.5, 0.85), lag=3, graph_delta=True, soft_count=True,
               edge_readout=True, dropout=0.1, edge_drop=0.1, feat_noise=0.0, node_mlp=True,
               w_tip=1.0, w_count=0.3, w_state=0.5, w_fut=0.3, pos_weight=4.0,
               lr=3e-3, wd=1e-4, epochs=40, batch_runs=8, seed=0, lr_decay=True, count_scale=8.0,
               rel="inout", agg="meanmax", mp_layernorm=True, readout="full", emb_k=4, gh=None)


def glorot(rng, i, o):
    return Param(rng.normal(0, np.sqrt(2.0 / (i + o)), (i, o)))


def zeros(o):
    return Param(np.zeros(o))


class Lin:
    def __init__(self, rng, i, o, bias=True):
        self.W = glorot(rng, i, o)
        self.b = zeros(o) if bias else None

    def __call__(self, x):
        return ag.linear(x, self.W, self.b)

    def params(self):
        return [self.W] + ([self.b] if self.b is not None else [])


class Monitor:
    def __init__(self, fn, fe, cfg=None):
        self.cfg = c = {**DEFAULT, **(cfg or {})}
        rng = np.random.default_rng(c["seed"])
        h = c["h"]
        self.mods = {}
        self.mods["nenc"] = Lin(rng, fn, h)
        self.mods["eenc"] = Lin(rng, fe, h)
        n_agg = 2 if c["agg"] == "meanmax" else 1
        n_rel = 2 if c["rel"] == "inout" else 1
        for l in range(c["layers"]):
            self.mods[f"msg_in{l}_n"] = Lin(rng, h, h)
            self.mods[f"msg_in{l}_e"] = Lin(rng, h, h, bias=False)
            if n_rel == 2:
                self.mods[f"msg_out{l}_n"] = Lin(rng, h, h)
                self.mods[f"msg_out{l}_e"] = Lin(rng, h, h, bias=False)
            self.mods[f"upd{l}"] = Lin(rng, h * (1 + n_agg * n_rel), h)
            if c["mp_layernorm"]:
                self.mods[f"ln{l}_g"] = Param(np.ones(h))
                self.mods[f"ln{l}_b"] = Param(np.zeros(h))
        n_mem = (2 + len(c["mem_alphas"]) + (1 if c["lag"] else 0)) if c["mem"] else 1
        self.mods["state"] = Lin(rng, h * n_mem, h)
        self.mods["head_state"] = Lin(rng, h, 1)
        self.mods["head_fut"] = Lin(rng, h, 1)
        if c["readout"] == "bottleneck":
            # low-dimensional graph summary: soft counts (+ a k-dim pooled embedding) -> small tip head
            self.mods["emb"] = Lin(rng, h, c["emb_k"])
            dg = 4 + 2 * c["emb_k"] + 1
        else:
            dg = 2 * h + (2 if c["soft_count"] else 0) + (2 * h if c["edge_readout"] else 0) + 1
        self.dg = dg * (2 if c["graph_delta"] else 1)
        gh = c["gh"] or h
        self.mods["g1"] = Lin(rng, self.dg, gh)
        self.mods["g_tip"] = Lin(rng, gh, 1)
        self.mods["g_cnt"] = Lin(rng, gh, 1)
        self._ker = {}

    def params(self):
        out = []
        for m in self.mods.values():
            out += m.params() if isinstance(m, Lin) else [m]
        return out

    def state_dict(self):
        d = {}
        for k, m in self.mods.items():
            if isinstance(m, Lin):
                d[k + ".W"] = m.W.data
                if m.b is not None:
                    d[k + ".b"] = m.b.data
            else:
                d[k] = m.data
        return d

    def load_state_dict(self, d):
        for k, m in self.mods.items():
            if isinstance(m, Lin):
                m.W.data = d[k + ".W"].copy()
                if m.b is not None:
                    m.b.data = d[k + ".b"].copy()
            else:
                m.data = d[k].copy()

    def kern(self, Tn, kind, a):
        key = (Tn, kind, a)
        if key not in self._ker:
            self._ker[key] = ag.ema_kernel(Tn, a) if kind == "ema" else ag.lag_kernel(Tn, a)
        return self._ker[key]

    # --------------------------------------------------------------------------------------------------- forward
    def forward(self, B, train=False, rng=None):
        c, M = self.cfg, self.mods
        h = c["h"]
        xn, xe = B["xn"], B["xe"]
        src, dst = B["src"], B["dst"]
        seg_in, seg_out = B["seg_in"], B["seg_out"]
        if train and c["edge_drop"] > 0 and len(src):
            keep = rng.random(len(src)) >= c["edge_drop"]
            src, dst, xe = src[keep], dst[keep], xe[keep]
            seg_in, seg_out = ag.Seg(dst, B["N"]), ag.Seg(src, B["N"])
            eseg = ag.Seg(B["esnap"][keep], B["S"])
        else:
            eseg = B["seg_esnap"]
        if train and c["feat_noise"] > 0:
            xn = xn + rng.normal(0, c["feat_noise"], xn.shape)
            xe = xe + rng.normal(0, c["feat_noise"], xe.shape)
        x = ag.relu(M["nenc"](ag.const(xn)))
        e = ag.relu(M["eenc"](ag.const(xe)))
        last_msg = e
        for l in range(c["layers"]):
            parts = [x]
            m_in = ag.relu(ag.add(M[f"msg_in{l}_n"](ag.gather(x, src)), M[f"msg_in{l}_e"](e)))
            parts += [ag.segmean(m_in, seg_in)] + ([ag.segmax(m_in, seg_in)] if c["agg"] == "meanmax" else [])
            if c["rel"] == "inout":
                m_out = ag.relu(ag.add(M[f"msg_out{l}_n"](ag.gather(x, dst)), M[f"msg_out{l}_e"](e)))
                parts += [ag.segmean(m_out, seg_out)] + ([ag.segmax(m_out, seg_out)] if c["agg"] == "meanmax" else [])
            u = M[f"upd{l}"](ag.concat(parts))
            if c["mp_layernorm"]:
                u = ag.layernorm(u, M[f"ln{l}_g"], M[f"ln{l}_b"])
            u = ag.dropout(ag.relu(u), c["dropout"], rng, train)
            x = ag.add(x, u)
            last_msg = m_in
        # temporal node memory
        if c["mem"]:
            Tn = B["T"]
            xz = ag.concat([x, ag.const(np.zeros((1, h)))], 0)
            dense = ag.reshape(ag.gather(xz, B["dense_idx"].reshape(-1)), (B["n_seq"], Tn, h))
            mems = [dense, ag.cummax_time(dense)]
            for a in c["mem_alphas"]:
                mems.append(ag.time_filter(dense, self.kern(Tn, "ema", a)))
            if c["lag"]:
                mems.append(ag.sub(dense, ag.time_filter(dense, self.kern(Tn, "lag", c["lag"]))))
            md = ag.concat(mems, 2)
            flat = ag.reshape(md, (B["n_seq"] * Tn, md.shape[2]))
            s = ag.relu(M["state"](ag.gather(flat, B["flat_pos"])))
        else:
            s = ag.relu(M["state"](x))
        s = ag.dropout(s, c["dropout"], rng, train)
        z_state = M["head_state"](s)
        z_fut = M["head_fut"](s)
        # graph readout
        nseg = B["seg_nsnap"]
        agent = ag.const(B["agent_mask"][:, None])
        if c["readout"] == "bottleneck":
            ps = ag.mul(ag.sigmoid(z_state), agent)
            pf = ag.mul(ag.sigmoid(z_fut), agent)
            em = ag.tanh(M["emb"](s))
            g = [ag.scale(ag.segsum(ps, nseg), 1 / c["count_scale"]), ag.scale(ag.segsum(pf, nseg), 1 / 3.0),
                 ag.segmax(pf, nseg), ag.segmax(ps, nseg), ag.segmean(em, nseg), ag.segmax(em, nseg),
                 ag.const(B["log_ne"][:, None])]
        else:
            g = [ag.segmean(s, nseg), ag.segmax(s, nseg)]
        if c["soft_count"] and c["readout"] != "bottleneck":
            ps = ag.mul(ag.sigmoid(z_state), agent)
            pf = ag.mul(ag.sigmoid(z_fut), agent)
            g += [ag.scale(ag.segsum(ps, nseg), 1 / c["count_scale"]), ag.scale(ag.segsum(pf, nseg), 1 / 3.0)]
        if c["edge_readout"] and c["readout"] != "bottleneck":
            g += [ag.segmean(last_msg, eseg), ag.segmax(last_msg, eseg)]
        if c["readout"] != "bottleneck":
            g += [ag.const(B["log_ne"][:, None])]
        g = ag.concat(g)
        if c["graph_delta"]:
            Tn = B["T"]
            dgs = g.shape[1]
            gd = ag.reshape(ag.permute(g, B["snap_dense"]), (B["R"], Tn, dgs))
            lagd = ag.time_filter(gd, self.kern(Tn, "lag", 3))
            delta = ag.reshape(ag.sub(gd, lagd), (B["R"] * Tn, dgs))
            g = ag.concat([g, ag.permute(delta, B["snap_inv"])])
        g1 = ag.dropout(ag.relu(M["g1"](g)), c["dropout"], rng, train)
        z_tip = M["g_tip"](g1)
        cnt = M["g_cnt"](g1)
        if c["soft_count"] or c["readout"] == "bottleneck":
            cnt = ag.add(cnt, ag.segsum(ps, nseg))
        return {"tip": z_tip, "count": cnt, "state": z_state, "fut": z_fut}

    def loss(self, out, B, target="y"):
        c = self.cfg
        y = B[target]
        w = np.where(y == 1, c["pos_weight"], 1.0)
        terms = [(c["w_tip"], ag.bce_logits(out["tip"], y, w))]
        if c["w_count"]:
            terms.append((c["w_count"], ag.huber(ag.scale(out["count"], 1 / c["count_scale"]),
                                                 B["risk"] / c["count_scale"], d=0.5)))
        if c["w_state"]:
            terms.append((c["w_state"], ag.bce_logits(out["state"], B["n_state"])))
        if c["w_fut"]:
            terms.append((c["w_fut"], ag.bce_logits(out["fut"], B["n_fut"], np.where(B["n_fut"] == 1, 3.0, 1.0))))
        return ag.total(*terms)


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -40, 40)))
