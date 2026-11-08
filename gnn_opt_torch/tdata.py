"""Torch-side data for the gnn_opt harness (gnn_opt_data/<name>/{snapshots.csv, graphs.npz, schema.json}).

Everything is pre-tensorised once:
  * node features  = headline node columns (schema.json) [+ ablation columns], NaN -> 0 plus a missing flag for the
                     columns that are NaN by construction (no direct messages, no own messages)
  * edge features  = headline edge columns [+ ablation], NaN -> 0 plus missing flags; edge relation type
                     0 = direct only, 1 = broadcast only, 2 = both (direct_volume / bcast_volume > 0)
  * per run: the snapshot index of each round (all runs have R = 30 here, but R may vary), node-row table
    [n_agents, R] (-1 = node absent) for node-level temporal memory
Standardisation statistics are computed on the training rows of each fold (fit_norm) -> no leakage from test folds.

Never loaded as input: round / t, labels, risk, config factors (only used for splitting / strata by the harness).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "gnn_opt"))

NAN_FLAG_E = ["responsiveness", "reciprocity"]
NAN_FLAG_N = ["unanswered_share", "stance_drift", "frustration_own"]


def feature_sets(schema, mode="headline"):
    """mode: headline | +lex | +tool | +lex+tool | S0 | S1 | S2 | S3 (stages restricted to allowed columns)."""
    he, hn = list(schema["headline_edge"]), list(schema["headline_node"])
    if mode.startswith("S"):
        st = set(schema["stages"][mode]) if isinstance(schema["stages"][mode], list) else set()
        return [c for c in he if c in st], [c for c in hn if c in st]
    e, n = he, hn
    if "+lex" in mode:
        e = e + list(schema["ablation_lexicon_edge"]); n = n + list(schema["ablation_lexicon_node"])
    if "+tool" in mode:
        n = n + list(schema["ablation_tool_node"])
    return e, n


class Data:
    def __init__(self, data_dir, feat_mode="headline", clock=False):
        self.dir = data_dir
        S = pd.read_csv(os.path.join(data_dir, "snapshots.csv"), low_memory=False)
        schema = json.load(open(os.path.join(data_dir, "schema.json")))
        z = np.load(os.path.join(data_dir, "graphs.npz"), allow_pickle=False)
        self.S, self.schema = S, schema
        e_use, n_use = feature_sets(schema, feat_mode)
        self.e_names, self.n_names = e_use, n_use
        self.feat_mode = feat_mode
        X, EF = self._feats(z, e_use, n_use, clock, S)
        self.alt = []                                  # judge-swap feature copies (same graphs, other judge)
        # relation type from the raw volume columns (always available in the npz)
        ecols = list(z["ecols"])
        dv = z["EF"][:, ecols.index("direct_volume")] > 0
        bv = z["EF"][:, ecols.index("bcast_volume")] > 0
        rel = np.where(dv & bv, 2, np.where(dv, 0, 1)).astype(np.int64)
        self.n_snap = len(S)
        self.node_snap = z["node_snap"].astype(np.int64)
        self.node_ext = z["node_ext"].astype(np.float32)
        self.node_lab = torch.from_numpy(z["node_lab"].astype(np.float32))  # [:,0] violated by t, [:,1] within D=3
        self.clock = clock
        self.X = torch.from_numpy(X)
        self.EF = torch.from_numpy(EF)
        self._init_rest(z, S, rel)

    @staticmethod
    def _feats(z, e_use, n_use, clock, S):
        ecols, ncols = list(z["ecols"]), list(z["ncols"])
        EF = z["EF"][:, [ecols.index(c) for c in e_use]].astype(np.float32)
        X = z["X"][:, [ncols.index(c) for c in n_use]].astype(np.float32)
        ef_flags = [np.isnan(EF[:, e_use.index(c)]).astype(np.float32) for c in NAN_FLAG_E if c in e_use]
        nf_flags = [np.isnan(X[:, n_use.index(c)]).astype(np.float32) for c in NAN_FLAG_N if c in n_use]
        EF = np.nan_to_num(EF, nan=0.0)
        X = np.nan_to_num(X, nan=0.0)
        if ef_flags:
            EF = np.concatenate([EF, np.stack(ef_flags, 1)], 1)
        if nf_flags:
            X = np.concatenate([X, np.stack(nf_flags, 1)], 1)
        if clock:                                                  # ablation only: round index as a node feature
            X = np.concatenate([X, (S.t.values[z["node_snap"]] / 30.0)[:, None].astype(np.float32)], 1)
        return X, EF.astype(np.float32)

    def add_judge(self, data_dir):
        """Judge-swap augmentation: same snapshots / edges, features from a single-judge build."""
        z = np.load(os.path.join(data_dir, "graphs.npz"), allow_pickle=False)
        assert len(z["ES"]) == len(self.ES) and (z["ES"] == self.ES.numpy()).all()
        X, EF = self._feats(z, self.e_names, self.n_names, self.clock, self.S)
        EF = torch.from_numpy(EF)
        # a single judge has no disagreement (all NaN there): keep the merged-jury value instead of a constant 0
        if "jury_disagreement" in self.e_names:
            i = self.e_names.index("jury_disagreement")
            EF[:, i] = self.EF[:, i]
        self.alt.append((torch.from_numpy(X), EF))

    def _init_rest(self, z, S, rel):
        self.ES = torch.from_numpy(z["ES"].astype(np.int64))
        self.ED = torch.from_numpy(z["ED"].astype(np.int64))
        self.REL = torch.from_numpy(rel)
        self.edge_snap = self.node_snap[z["ES"]]
        self.n0 = S.n0.values.astype(np.int64)
        self.nn_ = S.n_nodes.values.astype(np.int64)
        self.e0 = S.e0.values.astype(np.int64)
        self.ne = S.n_edges.values.astype(np.int64)
        # labels (targets only)
        self.y = {k: torch.tensor(S[k].values, dtype=torch.float32) for k in ("y3", "y5", "yrel3", "yrel5")}
        self.risk = torch.tensor(S.risk.values, dtype=torch.float32)
        # runs: ordered snapshot lists
        self.runs = []
        names = z["node_name"]
        for ri, g in S.groupby("run_i", sort=True):
            g = g.sort_values("t")
            snaps = g.snap.values
            agents = {}
            for k, s in enumerate(snaps):
                for r in range(self.n0[s], self.n0[s] + self.nn_[s]):
                    agents.setdefault(names[r], {})[k] = r
            tab = -np.ones((len(agents), len(snaps)), np.int64)
            for i, (a, d) in enumerate(sorted(agents.items())):
                for k, r in d.items():
                    tab[i, k] = r
            self.runs.append({"run_i": ri, "run": g.run.iloc[0], "cfg": g.cfg.iloc[0], "snaps": snaps, "tab": tab,
                              "split": g.split.iloc[0]})
        self.run_of_snap = S.run_i.values
        self.d_node, self.d_edge = self.X.shape[1], self.EF.shape[1]

    # ------------------------------------------------------------------ normalisation (per fold, train rows only)
    def fit_norm(self, train_runs):
        snaps = np.concatenate([r["snaps"] for r in train_runs])
        nm = np.isin(self.node_snap, snaps)
        em = np.isin(self.edge_snap, snaps)
        Xn, En = self.X[torch.from_numpy(nm)], self.EF[torch.from_numpy(em)]
        self.xm, self.xs = Xn.mean(0), Xn.std(0).clamp_min(1e-3)
        self.em_, self.es_ = En.mean(0), En.std(0).clamp_min(1e-3)

    # ------------------------------------------------------------------ batching
    def batch(self, runs, gen=None, edge_drop=0.0, feat_noise=0.0, rewire=False, shuffle_ef=False, judge=-1):
        """Collate whole runs. Returns dict of tensors; graph index g = position of the snapshot in `snaps`."""
        snaps = np.concatenate([r["snaps"] for r in runs])
        node_rows = np.concatenate([np.arange(self.n0[s], self.n0[s] + self.nn_[s]) for s in snaps])
        edge_rows = np.concatenate([np.arange(self.e0[s], self.e0[s] + self.ne[s]) for s in snaps])
        remap = np.full(len(self.X), -1, np.int64)
        remap[node_rows] = np.arange(len(node_rows))
        g_of_snap = np.full(self.n_snap, -1, np.int64)
        g_of_snap[snaps] = np.arange(len(snaps))
        er = torch.from_numpy(edge_rows)
        src = torch.from_numpy(remap[self.ES[er].numpy()])
        dst = torch.from_numpy(remap[self.ED[er].numpy()])
        Xsrc, EFsrc = (self.X, self.EF) if judge < 0 else self.alt[judge]
        ef = EFsrc[er]
        rel = self.REL[er]
        if rewire:      # control: random endpoints within the same snapshot (keeps edge features + counts)
            gs = torch.from_numpy(g_of_snap[self.edge_snap[edge_rows]])
            n0 = torch.from_numpy(np.cumsum(np.r_[0, self.nn_[snaps]])[:-1])
            nn = torch.from_numpy(self.nn_[snaps])
            u = torch.rand(len(er), generator=gen)
            v = torch.rand(len(er), generator=gen)
            src = n0[gs] + (u * nn[gs]).long()
            dst = n0[gs] + (v * nn[gs]).long()
        if shuffle_ef:  # control: permute edge feature rows across the whole batch
            p = torch.randperm(len(er), generator=gen)
            ef, rel = ef[p], rel[p]
        if edge_drop > 0:
            keep = torch.rand(len(er), generator=gen) >= edge_drop
            src, dst, ef, rel = src[keep], dst[keep], ef[keep], rel[keep]
        x = Xsrc[torch.from_numpy(node_rows)]
        x = (x - self.xm) / self.xs
        ef = (ef - self.em_) / self.es_
        if feat_noise > 0:
            x = x + feat_noise * torch.randn(x.shape, generator=gen)
            ef = ef + feat_noise * torch.randn(ef.shape, generator=gen)
        ngraph = torch.from_numpy(g_of_snap[self.node_snap[node_rows]])
        # sequence layout: per run [T] graphs; node tables for temporal memory
        T = max(len(r["snaps"]) for r in runs)
        seq = -np.ones((len(runs), T), np.int64)
        off = 0
        tabs = []
        for i, r in enumerate(runs):
            L = len(r["snaps"])
            seq[i, :L] = np.arange(off, off + L)
            off += L
            tb = r["tab"]
            t2 = -np.ones((tb.shape[0], T), np.int64)
            t2[:, :tb.shape[1]] = np.where(tb >= 0, remap[np.maximum(tb, 0)], -1)
            tabs.append(t2)
        ntab = np.concatenate(tabs, 0)
        st = torch.from_numpy(snaps)
        return {"x": x, "src": src, "dst": dst, "ef": ef, "rel": rel, "ngraph": ngraph, "G": len(snaps),
                "seq": torch.from_numpy(seq), "ntab": torch.from_numpy(ntab), "snaps": st,
                "y3": self.y["y3"][st], "y5": self.y["y5"][st], "yrel3": self.y["yrel3"][st],
                "risk": self.risk[st], "nlab": self.node_lab[torch.from_numpy(node_rows)], "next": torch.from_numpy(self.node_ext[node_rows])}
