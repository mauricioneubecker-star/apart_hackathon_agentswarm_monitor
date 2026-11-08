"""Training / prediction for the numpy GNN monitor on the harness dataset (graphs.npz + snapshots.csv)."""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd

import ag
from model import Monitor, sigmoid

FEATS = {
    # headline (generic) inputs
    "gen": {"edge": ["volume", "direct_volume", "bcast_volume", "responsiveness", "reciprocity", "new_contact",
                     "rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption",
                     "verification", "goal_shift", "unverified_authority", "secrecy", "frustration",
                     "legitimization_trend", "jury_disagreement", "escalation_lex"],
            "node": ["unanswered_share", "role_external", "bcast_legitimization", "stance_drift", "frustration_own"]},
}
FEATS["gen+lex"] = {"edge": FEATS["gen"]["edge"] + ["mech_ref", "mech_ref_ema", "pressure_lex"],
                    "node": FEATS["gen"]["node"] + ["bcast_mech_ref", "exposure_breadth"]}
FEATS["gen+tool"] = {"edge": FEATS["gen"]["edge"], "node": FEATS["gen"]["node"] + ["tests_failed",
                                                                                     "escalated_unresolved"]}
FEATS["S0"] = {"edge": ["volume", "direct_volume", "bcast_volume", "responsiveness", "reciprocity", "new_contact"],
               "node": ["unanswered_share", "role_external"]}
FEATS["S1"] = {"edge": FEATS["S0"]["edge"] + ["escalation_lex"], "node": FEATS["S0"]["node"]}
FEATS["S2"] = {"edge": FEATS["S1"]["edge"] + ["success_claim", "workaround_request", "verification", "frustration"],
               "node": FEATS["S1"]["node"] + ["frustration_own"]}
CLIP = 6.0
NAN_FLAG = ["responsiveness", "reciprocity", "unanswered_share", "stance_drift", "frustration_own"]


class Data:
    """Holds model-ready arrays for one dataset directory."""

    def __init__(self, data_dir, feats="gen", G=None, S=None, control=None, ctrl_seed=0):
        nt = feats.endswith("+nt")          # + engineered causal node table (nodefeat.py) as extra node inputs
        feats = feats[:-3] if nt else feats
        if G is None:
            z = np.load(os.path.join(data_dir, "graphs.npz"), allow_pickle=False)
            G = {k: z[k] for k in z.files}
        if S is None:
            S = pd.read_csv(os.path.join(data_dir, "snapshots.csv"), low_memory=False)
        self.S = S
        ec, nc = list(G["ecols"]), list(G["ncols"])
        F = FEATS[feats]
        EF = G["EF"][:, [ec.index(c) for c in F["edge"]]].astype(np.float64)
        XN = G["X"][:, [nc.index(c) for c in F["node"]]].astype(np.float64)
        eflag = [np.isnan(G["EF"][:, ec.index(c)])[:, None] for c in F["edge"] if c in NAN_FLAG]
        nflag = [np.isnan(G["X"][:, nc.index(c)])[:, None] for c in F["node"] if c in NAN_FLAG]
        ES, ED = G["ES"].copy(), G["ED"].copy()
        self.node_snap = G["node_snap"]
        esnap = self.node_snap[ES]
        rng = np.random.default_rng(ctrl_seed)
        if control == "shuffle_edges":
            # permute edge feature rows across all edges (keeps structure, destroys edge semantics)
            p = rng.permutation(len(EF))
            EF = EF[p]
            eflag = [f[p] for f in eflag]
        if control == "rewire":
            ES, ED = rewire(ES, ED, esnap, rng)
        EF = np.concatenate([np.nan_to_num(EF)] + [f.astype(np.float64) for f in eflag], 1)
        # structural node degrees (log1p in/out, direct/broadcast) from the snapshot edges
        n = len(XN)
        dv = G["EF"][:, ec.index("direct_volume")] > 0
        deg = np.stack([np.bincount(ED, minlength=n), np.bincount(ES, minlength=n),
                        np.bincount(ED[dv], minlength=n), np.bincount(ES[dv], minlength=n)], 1)
        XN = np.concatenate([np.nan_to_num(XN)] + [f.astype(np.float64) for f in nflag] + [np.log1p(deg)], 1)
        if nt:
            import nodefeat
            NT, cols = nodefeat.build_node_table(G, S, lex=(feats == "gen+lex"))
            XN = np.concatenate([XN, NT[cols].values.astype(np.float64)], 1)
        self.EF, self.XN, self.ES, self.ED, self.esnap = EF, XN, ES, ED, esnap
        self.node_lab = G["node_lab"].astype(np.float64)
        self.agent = (~G["node_ext"]).astype(np.float64)
        self.prev = G["prev"]
        self.fe, self.fn = EF.shape[1], XN.shape[1]
        # run index structures
        S = self.S
        self.runs = list(dict.fromkeys(S.run.values))
        rs = S.groupby("run", sort=False)
        self.run_snaps = {r: g.snap.values for r, g in rs}
        self.mu_e = self.sd_e = self.mu_n = self.sd_n = None
        self._cache = {}

    def fit_scaler(self, runs):
        snaps = np.concatenate([self.run_snaps[r] for r in runs])
        nm = np.isin(self.node_snap, snaps)
        em = np.isin(self.esnap, snaps)
        # std floor: a feature that is constant in training (e.g. role_external when external-seed configs are
        # held out) must not explode at test time; standardized inputs are additionally clipped to [-CLIP, CLIP]
        sdn, sde = self.XN[nm].std(0), self.EF[em].std(0)
        self.mu_n, self.sd_n = self.XN[nm].mean(0), np.where(sdn > 1e-3, sdn, 1.0)
        self.mu_e, self.sd_e = self.EF[em].mean(0), np.where(sde > 1e-3, sde, 1.0)
        self._cache = {}

    def run_block(self, r):
        if r in self._cache:
            return self._cache[r]
        S = self.S
        sn = self.run_snaps[r]
        s0, s1 = sn[0], sn[-1] + 1
        n0 = S.n0.values[s0]
        n1 = S.n0.values[s1 - 1] + S.n_nodes.values[s1 - 1]
        e0 = S.e0.values[s0]
        e1 = S.e0.values[s1 - 1] + S.n_edges.values[s1 - 1]
        blk = {"n0": n0, "n1": n1, "e0": e0, "e1": e1, "s0": s0, "s1": s1,
               "xn": np.clip((self.XN[n0:n1] - self.mu_n) / self.sd_n, -CLIP, CLIP),
               "xe": np.clip((self.EF[e0:e1] - self.mu_e) / self.sd_e, -CLIP, CLIP),
               "src": self.ES[e0:e1] - n0, "dst": self.ED[e0:e1] - n0, "esnap": self.esnap[e0:e1] - s0,
               "nsnap": self.node_snap[n0:n1] - s0, "prev": np.where(self.prev[n0:n1] >= 0, self.prev[n0:n1] - n0, -1)}
        self._cache[r] = blk
        return blk

    def batch(self, runs, target="y3", train_mask=None):
        """Concatenate whole runs (all 30 snapshots, needed for causal memory). train_mask (per snapshot) masks the
        graph loss; node losses are masked to the same snapshots."""
        S = self.S
        xs, es, srcs, dsts, ess, nss, prevs, snaps = [], [], [], [], [], [], [], []
        no = so = 0
        for r in runs:
            b = self.run_block(r)
            xs.append(b["xn"]); es.append(b["xe"])
            srcs.append(b["src"] + no); dsts.append(b["dst"] + no)
            ess.append(b["esnap"] + so); nss.append(b["nsnap"] + so)
            prevs.append(np.where(b["prev"] >= 0, b["prev"] + no, -1))
            snaps.append(np.arange(b["s0"], b["s1"]))
            no += b["n1"] - b["n0"]; so += b["s1"] - b["s0"]
        snaps = np.concatenate(snaps)
        N, nS = no, so
        B = {"xn": np.concatenate(xs), "xe": np.concatenate(es), "src": np.concatenate(srcs).astype(np.int64),
             "dst": np.concatenate(dsts).astype(np.int64), "esnap": np.concatenate(ess), "N": N, "S": nS,
             "snaps": snaps}
        nsnap = np.concatenate(nss)
        prev = np.concatenate(prevs)
        B["seg_in"], B["seg_out"] = ag.Seg(B["dst"], N), ag.Seg(B["src"], N)
        B["seg_esnap"], B["seg_nsnap"] = ag.Seg(B["esnap"], nS), ag.Seg(nsnap, nS)
        # dense temporal layout: sequence id per node chain, position = round - 1
        t_of = S.t.values[snaps][nsnap] - 1
        Tn = int(S.t.values[snaps].max())
        seq = np.empty(N, np.int64)
        nseq = 0
        for k in range(N):
            if prev[k] < 0:
                seq[k] = nseq; nseq += 1
            else:
                seq[k] = seq[prev[k]]
        dense = np.full((nseq, Tn), N, np.int64)
        dense[seq, t_of] = np.arange(N)
        B.update({"T": Tn, "n_seq": nseq, "dense_idx": dense, "flat_pos": seq * Tn + t_of})
        # graph-level dense layout (runs x T)
        run_of = np.repeat(np.arange(len(runs)), [len(self.run_snaps[r]) for r in runs])
        ts = S.t.values[snaps] - 1
        assert all(len(self.run_snaps[r]) == Tn for r in runs), "all runs in a batch need the same length"
        B["R"] = len(runs)
        B["snap_dense"] = np.argsort(run_of * Tn + ts)        # dense row k <- snapshot index
        inv = np.empty(nS, np.int64)
        inv[B["snap_dense"]] = np.arange(nS)
        B["snap_inv"] = inv
        B["log_ne"] = np.log1p(np.bincount(B["esnap"], minlength=nS)) / 5.0
        B["agent_mask"] = np.concatenate([self.agent[self.run_block(r)["n0"]:self.run_block(r)["n1"]] for r in runs])
        y = S[target].values[snaps].astype(np.float64)
        ok = (S["eval"].values[snaps] == 1)
        if train_mask is not None:
            ok &= train_mask[snaps]
        y[~ok] = np.nan
        B["y"] = y
        risk = S.risk.values[snaps].astype(np.float64)
        risk[~ok] = np.nan
        B["risk"] = risk
        nl = np.concatenate([self.node_lab[self.run_block(r)["n0"]:self.run_block(r)["n1"]] for r in runs])
        okn = ok[nsnap]
        B["n_state"] = np.where(okn, nl[:, 0], np.nan)
        B["n_fut"] = np.where(okn, nl[:, 1], np.nan)
        return B


def rewire(ES, ED, esnap, rng, n_swap=10):
    """Degree-preserving rewiring within each snapshot (directed double-edge swaps; self loops avoided)."""
    ES, ED = ES.copy(), ED.copy()
    order = np.argsort(esnap, kind="stable")
    bounds = np.flatnonzero(np.diff(np.r_[-1, esnap[order], -2]))
    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]
        m = len(idx)
        if m < 2:
            continue
        for _ in range(n_swap * m):
            i, j = idx[rng.integers(m)], idx[rng.integers(m)]
            if i == j or ES[i] == ED[j] or ES[j] == ED[i]:
                continue
            ED[i], ED[j] = ED[j], ED[i]
    return ES, ED


# ------------------------------------------------------------------------------------------------------- training
def fit(D: Data, train_runs, cfg, target="y3", train_mask=None, verbose=False, snapshot_ens=0):
    m = Monitor(D.fn, D.fe, cfg)
    c = m.cfg
    rng = np.random.default_rng(c["seed"] + 1000)
    opt = ag.Adam(m.params(), lr=c["lr"], wd=c["wd"])
    runs = list(train_runs)
    nb = int(np.ceil(len(runs) / c["batch_runs"]))
    total_steps = c["epochs"] * nb
    step = 0
    snaps_sd = []
    t0 = time.time()
    for ep in range(c["epochs"]):
        rng.shuffle(runs)
        tl = 0.0
        for bi in range(nb):
            br = runs[bi * c["batch_runs"]:(bi + 1) * c["batch_runs"]]
            B = D.batch(br, target, train_mask)
            out = m.forward(B, train=True, rng=rng)
            L = m.loss(out, B)
            L.backward()
            lr = c["lr"] * (0.5 * (1 + np.cos(np.pi * step / total_steps)) if c["lr_decay"] else 1.0)
            opt.step(lr)
            step += 1
            tl += float(L.data)
        if snapshot_ens and ep >= c["epochs"] - snapshot_ens:
            snaps_sd.append({k: v.copy() for k, v in m.state_dict().items()})
        if verbose:
            print(f"   ep {ep} loss {tl / nb:.4f} ({time.time() - t0:.0f}s)", flush=True)
    m.snapshots = snaps_sd
    return m


def predict(D: Data, m, runs, bs=16):
    """Returns DataFrame(snap, score, count, ...) for all snapshots of the runs."""
    out = []
    sds = m.snapshots if getattr(m, "snapshots", None) else [None]
    base = m.state_dict()
    for sd in sds:
        if sd is not None:
            m.load_state_dict(sd)
        parts = []
        for i in range(0, len(runs), bs):
            br = runs[i:i + bs]
            B = D.batch(br)
            o = m.forward(B, train=False)
            parts.append(pd.DataFrame({"snap": B["snaps"], "score": sigmoid(o["tip"].data.ravel()),
                                       "count": o["count"].data.ravel()}))
        out.append(pd.concat(parts))
    m.load_state_dict(base)
    P = out[0].copy()
    if len(out) > 1:
        P["score"] = np.mean([o.score.values for o in out], 0)
        P["count"] = np.mean([o["count"].values for o in out], 0)
    return P


def node_predict(D: Data, m, runs, bs=16):
    parts = []
    for i in range(0, len(runs), bs):
        B = D.batch(runs[i:i + bs])
        o = m.forward(B, train=False)
        parts.append((sigmoid(o["state"].data.ravel()), sigmoid(o["fut"].data.ravel()), B["n_state"], B["n_fut"]))
    return [np.concatenate(x) for x in zip(*parts)]


def ensemble_fit_predict(D, train_runs, pred_runs, cfg, seeds=(0,), target="y3", train_mask=None, snapshot_ens=0):
    Ps, models = [], []
    for s in seeds:
        D.fit_scaler(train_runs)
        m = fit(D, train_runs, {**cfg, "seed": s}, target, train_mask, snapshot_ens=snapshot_ens)
        Ps.append(predict(D, m, pred_runs))
        models.append(m)
    P = Ps[0].copy()
    P["score"] = np.mean([p.score.values for p in Ps], 0)
    P["count"] = np.mean([p["count"].values for p in Ps], 0)
    return P, models
