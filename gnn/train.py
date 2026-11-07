"""Train/evaluate one GNN run (or dispatch to a baseline). CLI writes one JSON line to <out>/results.jsonl.

Example:
  python -m gnn.train --data DATA_DIR --model gine --graph-target innocent_ejected --node-target votes_innocent \
      --select node.auprc --seed 0 --out results/amx
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .data import DataConfig, load
from .metrics import evaluate_preds, get

_CACHE = {}


@dataclass
class RunConfig:
    data: DataConfig
    model: str = "gine"            # gine | gated | transformer | gatv2 | none (K0) | logreg | hgb | lgbm | time
    hidden: int = 64
    layers: int = 3
    dropout: float = 0.2
    norm: str = "batch"
    readout: str = "sum_max"
    edge_readout: bool = False
    residual: bool = True
    heads: int = 4
    lr: float = 1e-3
    weight_decay: float = 1e-4
    batch_size: int = 64
    epochs: int = 200
    patience: int = 30
    drop_edge: float = 0.1
    lam_graph: float = 1.0
    lam_count: float = 0.5
    lam_node: float = 1.0
    lam_aux: float = 0.5
    pos_weight: str = "none"       # none | sqrt
    select: str = "graph.auprc"    # val metric for early stopping / model selection
    seed: int = 0
    threads: int = 1
    strata: tuple = ()
    arm: str = ""                  # label for the report (default: derived)
    save_preds: bool = True
    out: str = "results"

    def run_id(self):
        d = asdict(self)
        d.pop("out"), d.pop("threads"), d.pop("save_preds")
        return hashlib.md5(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:12]


def get_bundle(dc: DataConfig):
    k = dc.key()
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = load(dc)
    return _CACHE[k]


def _set_seed(s):
    import torch
    random.seed(s), np.random.seed(s), torch.manual_seed(s)


def _predict(model, graphs, batch_size):
    import torch
    from torch_geometric.loader import DataLoader
    model.eval()
    pg, pc, pn, yn, sid_n, sid_g = [], [], [], [], [], []
    with torch.no_grad():
        for b in DataLoader(graphs, batch_size=256):
            og, oc, on = model(b)
            pg.append(torch.sigmoid(og)), pc.append(torch.sigmoid(oc)), pn.append(torch.sigmoid(on))
            yn.append(b.y_node), sid_n.append(b.sid[b.batch]), sid_g.append(b.sid)
    cat = lambda xs: torch.cat(xs).numpy() if xs else np.zeros(0)
    return cat(sid_g), cat(pg), cat(pc), cat(sid_n), cat(pn), cat(yn)


def _frames(bundle, model, splits, cfg):
    meta = bundle.meta
    G, N = [], []
    for s in splits:
        sid_g, pg, pc, sid_n, pn, yn = _predict(model, bundle.graphs[s], cfg.batch_size)
        ys = np.array([float(g.y_graph) for g in bundle.graphs[s]])
        yc = np.array([float(g.y_count) for g in bundle.graphs[s]])
        G.append(pd.DataFrame({"sid": sid_g, "split": s, "y_graph": ys, "p_graph": pg, "y_count": yc, "p_count": pc}))
        N.append(pd.DataFrame({"sid": sid_n, "split": s, "y": yn, "p": pn}))
    G, N = pd.concat(G), pd.concat(N)
    extra = ["episode_id", "t", "group_id"] + [c for c in cfg.strata if c in meta.columns]
    G = G.join(meta[extra], on="sid")
    N = N.join(meta[extra], on="sid")
    return G, N


def train_gnn(cfg: RunConfig, bundle):
    import torch
    import torch.nn.functional as F
    from torch_geometric.loader import DataLoader

    from .models import Monitor, n_params
    torch.set_num_threads(cfg.threads)
    _set_seed(cfg.seed)
    model = Monitor(bundle.node_dim, bundle.edge_dim, kind=cfg.model, h=cfg.hidden, layers=cfg.layers,
                    dropout=cfg.dropout, norm=cfg.norm, readout=cfg.readout, edge_readout=cfg.edge_readout,
                    residual=cfg.residual, heads=cfg.heads, n_aux=len(cfg.data.node_aux))
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    tr = bundle.graphs["train"]
    pw_g = pw_n = None
    if cfg.pos_weight == "sqrt":
        yg = np.array([float(g.y_graph) for g in tr])
        yg = yg[~np.isnan(yg)]
        pw_g = torch.tensor(np.sqrt((len(yg) - yg.sum()) / max(yg.sum(), 1)))
        yn = torch.cat([g.y_node for g in tr]).numpy()
        yn = yn[~np.isnan(yn)]
        pw_n = torch.tensor(np.sqrt((len(yn) - yn.sum()) / max(yn.sum(), 1))) if len(yn) else None
    gen = torch.Generator().manual_seed(cfg.seed)
    loader = DataLoader(tr, batch_size=cfg.batch_size, shuffle=True, generator=gen)

    def masked_bce(logit, y, pw=None):
        m = ~torch.isnan(y)
        if not m.any():
            return logit.sum() * 0.0
        return F.binary_cross_entropy_with_logits(logit[m], y[m], pos_weight=pw)

    best, best_state, best_ep, bad = -np.inf, None, 0, 0
    has_val = "val" in bundle.graphs
    for ep in range(cfg.epochs):
        model.train()
        for b in loader:
            opt.zero_grad()
            og, oc, on = model(b, drop_edge=cfg.drop_edge)
            loss = (cfg.lam_graph * masked_bce(og, b.y_graph, pw_g) if cfg.data.graph_target else 0.0) \
                + (cfg.lam_count * masked_bce(oc, b.y_count) if cfg.data.graph_count else 0.0) \
                + (cfg.lam_node * masked_bce(on, b.y_node, pw_n) if cfg.data.node_target else 0.0)
            for j in range(len(cfg.data.node_aux)):
                loss = loss + cfg.lam_aux * masked_bce(model.aux_out[:, j], b.y_aux[:, j]) / len(cfg.data.node_aux)
            if not torch.is_tensor(loss):
                raise ValueError("no target configured")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
        if not has_val:
            continue
        G, N = _frames(bundle, model, ["val"], cfg)
        score = get(evaluate_preds(G, N), "val", cfg.select)
        if cfg.select.endswith("mae"):
            score = -score
        if np.isnan(score):
            score = -np.inf if best_state is None else best
        if score > best + 1e-6 or best_state is None:
            best, best_ep, bad = score, ep, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= cfg.patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    G, N = _frames(bundle, model, list(bundle.graphs), cfg)
    return G, N, {"best_epoch": best_ep, "epochs_run": ep + 1, "n_params": n_params(model)}


def run(cfg: RunConfig) -> dict:
    t0 = time.time()
    bundle = get_bundle(cfg.data)
    if cfg.model in ("logreg", "hgb", "lgbm", "time"):
        from .baselines import run_baseline
        G, N, info = run_baseline(cfg, bundle)
    else:
        G, N, info = train_gnn(cfg, bundle)
    gmax = (bundle.schema.get("graph_labels", {}).get(cfg.data.graph_count) or {}).get("max", 1) \
        if cfg.data.graph_count else 1
    if not cfg.data.graph_target and G is not None:
        G = G.drop(columns=["p_graph"], errors="ignore")
    if not cfg.data.graph_count and G is not None:
        G = G.drop(columns=["p_count"], errors="ignore")
    if not cfg.data.node_target:
        N = None
    metrics = evaluate_preds(G, N, count_scale=gmax, strata=cfg.strata)
    rid = cfg.run_id()
    res = {"run_id": rid, "arm": cfg.arm or default_arm(cfg), "cfg": json.loads(json.dumps(asdict(cfg), default=str)),
           "metrics": metrics, "secs": round(time.time() - t0, 1), **info}
    os.makedirs(cfg.out, exist_ok=True)
    if cfg.save_preds:
        os.makedirs(os.path.join(cfg.out, "preds"), exist_ok=True)
        if G is not None:
            G.to_csv(os.path.join(cfg.out, "preds", f"{rid}_graph.csv.gz"), index=False)
        if N is not None:
            N.to_csv(os.path.join(cfg.out, "preds", f"{rid}_node.csv.gz"), index=False)
    with open(os.path.join(cfg.out, "results.jsonl"), "a") as f:
        f.write(json.dumps(res, default=str) + "\n")
    return res


def default_arm(cfg: RunConfig) -> str:
    d = cfg.data
    parts = [cfg.model, f"S{d.stage}"]
    if d.drop_groups:
        parts.append("-" + "-".join(d.drop_groups))
    if d.include_groups:
        parts.append("+" + "+".join(d.include_groups))
    if d.rewire:
        parts.append("rewired")
    if d.shuffle_labels:
        parts.append("shuffled")
    if d.jury:
        parts.append(f"jury={d.jury}")
    if d.node_aux:
        parts.append("aux=" + "+".join(d.node_aux))
    return " ".join(parts)


def build_cfg(a: dict) -> RunConfig:
    """Flat dict (CLI / sweep spec) -> RunConfig."""
    dkeys = set(DataConfig.__dataclass_fields__)
    dd = {k: v for k, v in a.items() if k in dkeys}
    for k in ("drop_groups", "include_groups", "node_aux"):
        if isinstance(dd.get(k), str):
            dd[k] = tuple(x for x in dd[k].split(",") if x)
        elif dd.get(k) is not None:
            dd[k] = tuple(dd[k])
    seed = a.get("seed", 0)
    dd["seed"] = seed if (dd.get("rewire") or dd.get("shuffle_labels")) else 0
    rk = {k: v for k, v in a.items() if k in RunConfig.__dataclass_fields__ and k != "data"}
    if isinstance(rk.get("strata"), str):
        rk["strata"] = tuple(x for x in rk["strata"].split(",") if x)
    elif rk.get("strata") is not None:
        rk["strata"] = tuple(rk["strata"])
    return RunConfig(data=DataConfig(**dd), **rk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", dest="data_dir", required=True)
    ap.add_argument("--model", default="gine")
    ap.add_argument("--stage", type=int, default=3)
    ap.add_argument("--drop-groups", default="")
    ap.add_argument("--include-groups", default="")
    ap.add_argument("--graph-target")
    ap.add_argument("--graph-count")
    ap.add_argument("--node-target")
    ap.add_argument("--node-aux", default="", help="comma-separated auxiliary node labels (training only)")
    ap.add_argument("--holdout", default="", help='JSON, e.g. {"matchup": ["selfplay-dataset/qwen3-4b"]}')
    ap.add_argument("--rewire", action="store_true")
    ap.add_argument("--shuffle-labels", action="store_true")
    ap.add_argument("--no-reverse", action="store_true")
    ap.add_argument("--jury")
    for k, t, dflt in (("hidden", int, 64), ("layers", int, 3), ("dropout", float, 0.2), ("lr", float, 1e-3),
                       ("weight_decay", float, 1e-4), ("batch_size", int, 64), ("epochs", int, 200),
                       ("patience", int, 30), ("drop_edge", float, 0.1), ("lam_graph", float, 1.0),
                       ("lam_count", float, 0.5), ("lam_node", float, 1.0), ("lam_aux", float, 0.5), ("seed", int, 0), ("threads", int, 1)):
        ap.add_argument("--" + k.replace("_", "-"), type=t, default=dflt)
    ap.add_argument("--norm", default="batch")
    ap.add_argument("--readout", default="sum_max")
    ap.add_argument("--edge-readout", action="store_true")
    ap.add_argument("--pos-weight", default="none")
    ap.add_argument("--select", default="graph.auprc")
    ap.add_argument("--strata", default="")
    ap.add_argument("--arm", default="")
    ap.add_argument("--out", default="results")
    a = vars(ap.parse_args())
    a["holdout"] = json.loads(a["holdout"]) if a["holdout"] else {}
    a["reverse_edges"] = not a.pop("no_reverse")
    res = run(build_cfg(a))
    short = {s: {k: (round(v.get("auprc", float("nan")), 3) if isinstance(v, dict) else None)
                 for k, v in m.items() if k in ("graph", "node")} for s, m in res["metrics"].items()}
    print(json.dumps({"arm": res["arm"], "secs": res["secs"], "best_epoch": res.get("best_epoch"), "auprc": short}))


if __name__ == "__main__":
    main()
