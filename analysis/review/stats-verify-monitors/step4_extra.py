"""Extra checks: ID fold membership, composition of final / hybrid, Holm family with alternative gnn_final."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/verify-monitors")
import vlib as L

S, lab, cfgs = L.load_rows(); F = json.load(open(L.FOLDS)); nC = len(cfgs); y = lab.y.values
# (1) ID fold membership + no config in two folds of the same repeat
for f in ("final.csv", "final+hgb_bag+graph+mem.csv", "hgb_bag+graph.csv", "hgb_clock.csv", "e_ngru_4runs.csv"):
    P = pd.read_csv(f"{L.GIT}/{f}").merge(lab[["run", "round", "cfg"]], on=["run", "round"], how="inner")
    bad = 0
    for name, fc in F["id"].items():
        g = P[P.fold == name]
        bad += int(set(g.cfg) != set(fc)) + int(len(g) != lab.cfg.isin(fc).sum())
    reps = {r: [c for n, fc in F["id"].items() if n.startswith(r) for c in fc] for r in ("id0", "id1")}
    print(f, "ID fold mismatches:", bad, "| each repeat partitions the 64 cfgs:",
          all(sorted(v) == sorted(cfgs) for v in reps.values()))
# (2) composition
key = ["run", "round", "fold"]
fin = pd.read_csv(f"{L.GIT}/final.csv")
mem = [pd.read_csv(f"{L.GIT}/{m}.csv")[key + ["score"]].rename(columns={"score": m})
       for m in ("m_noer_swa", "m_noer_swa_s1", "m_tmemgru", "m_tmemgru_s1")]
M = fin[key + ["score"]]
for m in mem:
    M = M.merge(m, on=key, how="left")
mean4 = M[["m_noer_swa", "m_noer_swa_s1", "m_tmemgru", "m_tmemgru_s1"]].mean(1)
print("final == mean of 4 members: max|diff|", float(np.abs(M.score - mean4).max()))
hy = pd.read_csv(f"{L.GIT}/final+hgb_bag+graph+mem.csv")[key + ["score"]].rename(columns={"score": "hy"})
gb = pd.read_csv(f"{L.GIT}/hgb_bag+graph+mem.csv")[key + ["score"]].rename(columns={"score": "gb"})
Q = hy.merge(fin[key + ["score"]], on=key).merge(gb, on=key)
lg = lambda p: np.log(np.clip(p, 1e-12, 1 - 1e-12) / (1 - np.clip(p, 1e-12, 1 - 1e-12)))
blend = 1 / (1 + np.exp(-(0.5 * lg(Q.score) + 0.5 * lg(Q.gb))))
print("hybrid == sigmoid(0.5 logit final + 0.5 logit hgb_bag+graph+mem): max|diff|", float(np.abs(Q.hy - blend).max()))
# (3) Holm family if gnn_final had been pinned to the node-GRU GNN e_ngru_4runs (+ its blend h_ngru4_hgb_logit55)
oof = {n: L.cv_scores(f"{L.GIT}/{f}", lab)["oof"] for n, f in
       {"clock": "hgb_clock.csv", "bag+graph": "hgb_bag+graph.csv", "gnn_final": "e_ngru_4runs.csv",
        "gnn_hybrid": "h_ngru4_hgb_logit55.csv"}.items()}
for v in ("pairwise", "global_full"):
    oof["zs:" + v] = L.zs_scores(v, lab)
P = {n: L.Pred(s, lab, nC) for n, s in oof.items()}
K = L.draws(nC, 10000, 314159)
c = {n: {"auroc": P[n].auroc(K), "tauroc": P[n].tauroc(K)} for n in P}
one = np.ones((1, nC)); full = {n: {"auroc": P[n].auroc(one)[0], "tauroc": P[n].tauroc(one)[0]} for n in P}
FAM = [(m, "clock", "tauroc") for m in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid")] + \
      [(u, v, "auroc") for u, v in [("gnn_final", "bag+graph"), ("gnn_hybrid", "bag+graph"), ("zs:pairwise", "bag+graph"),
                                    ("zs:pairwise", "gnn_final"), ("zs:pairwise", "gnn_hybrid"), ("zs:global_full", "bag+graph")]]
ps = [L.pboot(c[u][m] - c[v][m]) for u, v, m in FAM]
print("\n-- Holm family with gnn_final := e_ngru_4runs, gnn_hybrid := h_ngru4_hgb_logit55 (seed 314159, B=10000)")
for (u, v, m), p, h in zip(FAM, ps, L.holm(ps)):
    d = c[u][m] - c[v][m]
    print(f"{u:15s} - {v:10s} {m:6s} d={full[u][m] - full[v][m]:+.4f} [{np.quantile(d, .025):+.4f}, {np.quantile(d, .975):+.4f}] p={p:.4f} holm={h:.4f}")
