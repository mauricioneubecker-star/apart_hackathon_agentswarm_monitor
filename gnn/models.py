"""GNN monitor: edge-aware message passing + graph / count / node heads. kind='none' = K0 (no message passing)."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import (GATv2Conv, GINEConv, ResGatedGraphConv, TransformerConv, global_add_pool,
                                global_max_pool, global_mean_pool)
from torch_geometric.utils import scatter


def make_conv(kind: str, h: int, heads: int = 4):
    if kind == "gine":
        mlp = nn.Sequential(nn.Linear(h, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Linear(h, h))
        return GINEConv(mlp, train_eps=True, edge_dim=h)          # per-layer edge projection
    if kind == "gated":
        return ResGatedGraphConv(h, h, edge_dim=h)
    if kind == "transformer":
        return TransformerConv(h, h // heads, heads=heads, edge_dim=h)
    if kind == "gatv2":
        return GATv2Conv(h, h // heads, heads=heads, edge_dim=h, add_self_loops=False)
    raise ValueError(kind)


class Monitor(nn.Module):
    def __init__(self, node_dim, edge_dim, kind="gine", h=64, layers=3, dropout=0.2, norm="batch",
                 readout="sum_max", edge_readout=False, residual=True, heads=4, n_aux=0):
        super().__init__()
        self.kind, self.dropout, self.residual = kind, dropout, residual
        self.readout, self.edge_readout = readout, edge_readout or kind == "none"
        self.node_enc = nn.Sequential(nn.Linear(node_dim, h), nn.ReLU())
        self.edge_enc = nn.Sequential(nn.Linear(edge_dim, h), nn.ReLU())
        n_layers = 0 if kind == "none" else layers
        self.convs = nn.ModuleList([make_conv(kind, h, heads) for _ in range(n_layers)])
        Norm = (lambda: nn.BatchNorm1d(h)) if norm == "batch" else (lambda: nn.LayerNorm(h))
        self.norms = nn.ModuleList([Norm() for _ in range(n_layers)])
        if kind == "none":   # K0: node MLP of equal depth instead of message passing
            self.node_mlp = nn.Sequential(*[m for _ in range(layers) for m in (nn.Linear(h, h), Norm(), nn.ReLU())])
        g_dim = h * (2 if readout in ("sum_max", "mean_max") else 1) + (2 * h + 1 if self.edge_readout else 0)
        if readout == "attention":
            from torch_geometric.nn import AttentionalAggregation
            self.att = AttentionalAggregation(nn.Linear(h, 1))
        head = lambda i, o=1: nn.Sequential(nn.Linear(i, h), nn.ReLU(), nn.Dropout(dropout), nn.Linear(h, o))
        self.head_graph, self.head_count = head(g_dim), head(g_dim)
        self.head_node = head(h + g_dim, 1 + n_aux)   # column 0 = node target, 1.. = auxiliary node targets

    def pool(self, x, batch):
        if self.readout == "sum_max":
            return torch.cat([global_add_pool(x, batch), global_max_pool(x, batch)], 1)
        if self.readout == "mean_max":
            return torch.cat([global_mean_pool(x, batch), global_max_pool(x, batch)], 1)
        if self.readout == "attention":
            return self.att(x, batch)
        return global_add_pool(x, batch)

    def forward(self, data, drop_edge: float = 0.0):
        ei, ea = data.edge_index, data.edge_attr
        if self.training and drop_edge > 0 and ei.size(1):
            keep = torch.rand(ei.size(1), device=ei.device) >= drop_edge
            ei, ea = ei[:, keep], ea[keep]
        x, e = self.node_enc(data.x), self.edge_enc(ea)
        if self.kind == "none":
            x = x + self.node_mlp(x)
        for conv, norm in zip(self.convs, self.norms):
            hx = F.relu(norm(conv(x, ei, e)))
            hx = F.dropout(hx, self.dropout, self.training)
            x = x + hx if self.residual else hx
        g = self.pool(x, data.batch)
        if self.edge_readout:
            n_graphs = g.size(0)
            eb = data.batch[ei[0]] if ei.size(1) else torch.zeros(0, dtype=torch.long, device=x.device)
            e_mean = scatter(e, eb, 0, dim_size=n_graphs, reduce="mean")
            e_max = scatter(e, eb, 0, dim_size=n_graphs, reduce="max")
            cnt = scatter(torch.ones_like(eb, dtype=torch.float), eb, 0, dim_size=n_graphs, reduce="sum")
            g = torch.cat([g, e_mean, e_max, torch.log1p(cnt)[:, None]], 1)
        out_g = self.head_graph(g).squeeze(-1)
        out_c = self.head_count(g).squeeze(-1)
        out_n = self.head_node(torch.cat([x, g[data.batch]], 1))
        self.aux_out = out_n[:, 1:]
        return out_g, out_c, out_n[:, 0]


def n_params(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)
