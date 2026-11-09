"""Re-run the primary family with the other analyst's draw scheme (rng.integers(0,C,(B,C)), seed 20261108)
but with my own AUROC/tAUROC code, to check their exact p-values; and a 2nd independent seed for MC error."""
import json, sys
import numpy as np
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/verify-monitors")
import vlib as L

S, lab, cfgs = L.load_rows(); F = json.load(open(L.FOLDS)); nC = len(cfgs); y = lab.y.values
files = {"clock": "hgb_clock.csv", "bag+graph": "hgb_bag+graph.csv", "gnn_final": "final.csv",
         "gnn_hybrid": "final+hgb_bag+graph+mem.csv"}
oof = {n: L.cv_scores(f"{L.GIT}/{f}", lab)["oof"] for n, f in files.items()}
for v in ("pairwise", "global_full"):
    oof["zs:" + v] = L.zs_scores(v, lab)
P = {n: L.Pred(s, lab, nC) for n, s in oof.items()}
FAM = [(m, "clock", "tauroc") for m in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid")] + \
      [(u, v, "auroc") for u, v in [("gnn_final", "bag+graph"), ("gnn_hybrid", "bag+graph"), ("zs:pairwise", "bag+graph"),
                                    ("zs:pairwise", "gnn_final"), ("zs:pairwise", "gnn_hybrid"), ("zs:global_full", "bag+graph")]]

def their_scheme(B, seed):
    idx = np.random.default_rng(seed).integers(0, nC, size=(B, nC))
    K = np.zeros((B, nC))
    for b in range(B):
        K[b] = np.bincount(idx[b], minlength=nC)
    return K

def run(K, tag):
    cache = {}
    for n in P:
        cache[n] = {"auroc": P[n].auroc(K), "tauroc": P[n].tauroc(K)}
    ps, out = [], []
    for u, v, m in FAM:
        d = cache[u][m] - cache[v][m]
        lo, hi = np.quantile(d, [0.025, 0.975])
        p = L.pboot(d); ps.append(p); out.append((f"{u} - {v}", m, lo, hi, p, np.mean(d <= 0)))
    h = L.holm(ps)
    print(f"--- {tag}")
    for (c, m, lo, hi, p, le0), hh in zip(out, h):
        print(f"{c:28s} {m:6s} CI [{lo:+.4f}, {hi:+.4f}] p={p:.4f} holm={hh:.4f} P(d<=0)={le0:.4f}")

run(their_scheme(10000, 20261108), "their draw scheme, seed 20261108, B=10000 (should equal their table exactly)")
run(L.draws(nC, 10000, 2718), "own scheme, seed 2718, B=10000")
run(L.draws(nC, 40000, 161803), "own scheme, seed 161803, B=40000")
