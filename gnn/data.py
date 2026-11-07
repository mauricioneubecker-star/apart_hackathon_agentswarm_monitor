"""Load the canonical snapshot format (FORMAT.md) into PyG graphs plus flat tables for baselines."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

KEY = ["episode_id", "t"]


@dataclass
class DataConfig:
    data_dir: str
    stage: int = 3                      # max feature tier (Swarm S0-S3; Among Us 0/1)
    drop_groups: tuple = ()             # e.g. ("rule_near",), ("temporal",)
    include_groups: tuple = ()          # re-enable default-dropped groups, e.g. ("privileged",), ("tool_activity",)
    graph_target: str | None = None     # binary graph label
    graph_count: str | None = None      # count graph label (regression, scaled by schema max)
    node_target: str | None = None      # binary node label
    node_aux: tuple = ()                # extra node labels used only as auxiliary training targets
    holdout: dict = field(default_factory=dict)   # {episodes column: [values]} -> split "test_ood"
    reverse_edges: bool = True
    rewire: bool = False                # degree-preserving control: permute dst within snapshot and etype
    shuffle_labels: bool = False        # leakage control: permute targets within train
    seed: int = 0
    jury: str | None = None             # swarm judge-swap: use edges_<jury>.csv / nodes_<jury>.csv if present

    def key(self):
        return json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()},
                          sort_keys=True, default=str)


def _selected(items, stage, drop):
    out = []
    for it in items:
        tier = it.get("tier", 0)
        tier = 99 if isinstance(tier, str) else tier
        if tier <= stage and not set(it.get("groups", [])) & drop:
            out.append(it["name"])
    return out


class Bundle:
    """Everything a run needs: PyG graphs per split, flat tables for baselines, column names, metadata."""


def load(cfg: DataConfig, verbose: bool = True) -> Bundle:
    import torch
    from torch_geometric.data import Data

    d = cfg.data_dir
    schema = json.load(open(os.path.join(d, "schema.json")))
    drop = (set(cfg.drop_groups) | set(schema.get("default_drop_groups", []))) - set(cfg.include_groups)
    ncols = _selected(schema["node_features"], cfg.stage, drop)
    ecols = _selected(schema["edge_features"], cfg.stage, drop)
    etypes = _selected(schema["etypes"], cfg.stage, drop)

    sfx = f"_{cfg.jury}" if cfg.jury else ""
    ep = pd.read_csv(os.path.join(d, "episodes.csv"), dtype={"episode_id": str, "group_id": str})
    nodes = pd.read_csv(os.path.join(d, f"nodes{sfx}.csv" if os.path.exists(os.path.join(d, f"nodes{sfx}.csv"))
                                     else "nodes.csv"), dtype={"episode_id": str, "node_id": str})
    edges = pd.read_csv(os.path.join(d, f"edges{sfx}.csv" if os.path.exists(os.path.join(d, f"edges{sfx}.csv"))
                                     else "edges.csv"), dtype={"episode_id": str, "src": str, "dst": str})
    gl = pd.read_csv(os.path.join(d, "graph_labels.csv"), dtype={"episode_id": str})
    nl = pd.read_csv(os.path.join(d, "node_labels.csv"), dtype={"episode_id": str, "node_id": str})
    sp = os.path.join(d, "snapshots.csv")
    snaps = pd.read_csv(sp, dtype={"episode_id": str}) if os.path.exists(sp) else nodes[KEY].drop_duplicates()

    # splits (+ holdout)
    ep["split"] = ep["split"].astype(str)
    for col, vals in (cfg.holdout or {}).items():
        ep.loc[ep[col].astype(str).isin([str(v) for v in vals]), "split"] = "test_ood"
    split_of = dict(zip(ep.episode_id, ep.split))
    group_of = dict(zip(ep.episode_id, ep.group_id))

    edges = edges[edges.etype.isin(etypes)].copy()
    nodes["split"] = nodes.episode_id.map(split_of)
    edges["split"] = edges.episode_id.map(split_of)
    nodes = nodes[nodes.split.notna()]
    edges = edges[edges.split.notna()]

    # standardization from train only; NaN -> mean + missing flag
    def standardize(df, cols):
        tr = df[df.split == "train"]
        dead = [c for c in cols if not tr[c].notna().any()]          # all-NaN in train (e.g. no NLI): drop
        if dead and verbose:
            print(f"[data] dropping all-NaN columns: {dead}")
        cols = [c for c in cols if c not in dead]
        if not cols:
            return np.zeros((len(df), 0), np.float32), []
        out_cols = list(cols)
        X = df[cols].astype(float)
        mu = tr[cols].astype(float).mean()
        sd = tr[cols].astype(float).std().replace(0, 1).fillna(1)
        flags = {}
        for c in cols:
            if tr[c].isna().mean() > 0.01:
                flags[f"{c}__missing"] = df[c].isna().astype(float).values
        X = ((X - mu) / sd).fillna(0.0)
        for k, v in flags.items():
            X[k] = v
            out_cols.append(k)
        return X.values.astype(np.float32), out_cols

    Xn, ncols_out = standardize(nodes, ncols) if ncols else (np.zeros((len(nodes), 0), np.float32), [])
    if Xn.shape[1] == 0:
        Xn, ncols_out = np.ones((len(nodes), 1), np.float32), ["bias"]
    Xe, ecols_out = standardize(edges, ecols) if ecols else (np.zeros((len(edges), 0), np.float32), [])
    if len(etypes) > 1:
        oh = np.stack([(edges.etype.values == e).astype(np.float32) for e in etypes], 1)
        Xe = np.concatenate([Xe, oh], 1)
        ecols_out = ecols_out + [f"etype={e}" for e in etypes]
    if Xe.shape[1] == 0:  # structure-only: constant edge feature
        Xe = np.ones((len(edges), 1), np.float32)
        ecols_out = ["const"]

    # labels
    gmax = (schema.get("graph_labels", {}).get(cfg.graph_count) or {}).get("max", 1) if cfg.graph_count else 1
    gl = gl.set_index(KEY)
    nl = nl.set_index(KEY + ["node_id"])
    rng = np.random.default_rng(cfg.seed)

    node_idx = nodes.groupby(KEY, sort=False).indices
    edge_idx = edges.groupby(KEY, sort=False).indices
    time_cols = [c for c in schema.get("time_features", []) if c in snaps.columns] or ["t"]
    _keys = lambda df, cols: list(zip(*[df[c].values for c in cols]))
    snap_d = {c: dict(zip(_keys(snaps, KEY), snaps[c].values)) for c in time_cols if c in snaps.columns}
    glr = gl.reset_index()
    yg_d = dict(zip(_keys(glr, KEY), glr[cfg.graph_target].astype(float))) if cfg.graph_target else {}
    yc_d = dict(zip(_keys(glr, KEY), glr[cfg.graph_count].astype(float))) if cfg.graph_count else {}
    nlr = nl.reset_index()
    yn_d = dict(zip(_keys(nlr, KEY + ["node_id"]), nlr[cfg.node_target].astype(float))) if cfg.node_target else {}
    aux_d = [dict(zip(_keys(nlr, KEY + ["node_id"]), nlr[c].astype(float))) for c in cfg.node_aux]

    src_all, dst_all = edges.src.values.astype(str), edges.dst.values.astype(str)
    et_all, nid_all = edges.etype.values.astype(str), nodes.node_id.values.astype(str)
    graphs = {s: [] for s in ("train", "val", "test_id", "test_ood", "test_ood_family", "test_ood_seed",
                              "test_backbone", "test_ood_model", "pilot")}
    rows = []   # flat per-snapshot metadata for baselines/eval
    n_drop_edges = 0
    for key, ni in node_idx.items():
        eid, t = key
        split = split_of[eid]
        nid = nid_all[ni]
        pos = {n: i for i, n in enumerate(nid)}
        x = torch.from_numpy(Xn[ni])
        ei_rows = edge_idx.get(key, np.array([], dtype=int))
        src = [pos.get(s, -1) for s in src_all[ei_rows]]
        dst = [pos.get(s, -1) for s in dst_all[ei_rows]]
        keep = [i for i in range(len(ei_rows)) if src[i] >= 0 and dst[i] >= 0 and src[i] != dst[i]]
        n_drop_edges += len(ei_rows) - len(keep)
        src = np.array([src[i] for i in keep], dtype=np.int64)
        dst = np.array([dst[i] for i in keep], dtype=np.int64)
        ea = Xe[ei_rows[keep]] if len(keep) else np.zeros((0, Xe.shape[1]), np.float32)
        if cfg.rewire and len(keep) > 1:
            ets = et_all[ei_rows[keep]]
            for e in np.unique(ets):
                m = np.where(ets == e)[0]
                dst[m] = dst[m][rng.permutation(len(m))]
            ok = src != dst
            src, dst, ea = src[ok], dst[ok], ea[ok]
        if cfg.reverse_edges:
            flag = np.concatenate([np.zeros(len(src)), np.ones(len(src))]).astype(np.float32)[:, None]
            ea = np.concatenate([np.concatenate([ea, ea], 0), flag], 1)
            src, dst = np.concatenate([src, dst]), np.concatenate([dst, src])
        data = Data(x=x, edge_index=torch.from_numpy(np.stack([src, dst])).long(),
                    edge_attr=torch.from_numpy(ea.astype(np.float32)))
        # targets
        yg = yg_d.get(key, float("nan"))
        yc = yc_d.get(key, float("nan")) / gmax
        yn = np.array([yn_d.get((eid, t, n), np.nan) for n in nid], np.float32)
        ya = np.array([[d.get((eid, t, n), np.nan) for d in aux_d] for n in nid], np.float32).reshape(len(nid), -1)
        data.y_graph = torch.tensor([yg], dtype=torch.float32)
        data.y_count = torch.tensor([yc], dtype=torch.float32)
        data.y_node = torch.from_numpy(yn)
        data.y_aux = torch.from_numpy(ya)
        data.sid = torch.tensor([len(rows)])
        rows.append({"episode_id": eid, "t": t, "split": split, "group_id": group_of[eid], "n_nodes": len(nid),
                     "n_edges": len(keep), **{c: snap_d[c].get(key, np.nan) if c in snap_d else t
                                               for c in time_cols}})
        graphs.setdefault(split, []).append(data)

    meta = pd.DataFrame(rows)
    epi = ep.set_index("episode_id")
    for col in schema.get("strata", []):
        if col in epi.columns and col not in meta.columns:
            meta[col] = meta.episode_id.map(epi[col])
    if cfg.shuffle_labels:  # permute targets among train graphs (sanity: should collapse to chance)
        tr = graphs["train"]
        perm = rng.permutation(len(tr))
        yg = [g.y_graph.clone() for g in tr]
        yc = [g.y_count.clone() for g in tr]
        for g, j in zip(tr, perm):
            g.y_graph, g.y_count = yg[j], yc[j]
        # node labels: permute across ALL train nodes (a within-graph shuffle would keep graph-level signal)
        flat = torch.cat([g.y_node for g in tr])
        flat = flat[torch.from_numpy(rng.permutation(len(flat)))]
        flat_a = torch.cat([g.y_aux for g in tr])
        flat_a = flat_a[torch.from_numpy(rng.permutation(len(flat_a)))]
        i = 0
        for g in tr:
            n = len(g.y_node)
            g.y_node, g.y_aux, i = flat[i:i + n].clone(), flat_a[i:i + n].clone(), i + n

    b = Bundle()
    b.cfg, b.schema, b.graphs, b.meta = cfg, schema, {k: v for k, v in graphs.items() if v}, meta
    b.node_cols, b.edge_cols, b.etypes, b.time_cols = ncols_out, ecols_out, etypes, time_cols
    b.node_dim, b.edge_dim = Xn.shape[1], (Xe.shape[1] + (1 if cfg.reverse_edges else 0))
    b.tables = {"nodes": nodes, "edges": edges, "graph_labels": gl, "node_labels": nl, "episodes": ep,
                "raw_node_cols": ncols, "raw_edge_cols": ecols}
    if verbose:
        cnt = {k: len(v) for k, v in b.graphs.items()}
        print(f"[data] {os.path.basename(d.rstrip('/'))}: snapshots {cnt}; node feats {len(ncols_out)}, "
              f"edge feats {b.edge_dim} (etypes {etypes}); dropped edges {n_drop_edges}")
    return b
