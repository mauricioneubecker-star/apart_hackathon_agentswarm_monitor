"""Primary family re-computation with own cluster bootstrap (independent seed), Holm, LODO signs, DeLong contrast."""
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import binomtest

sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/stat/verify-monitors")
import vlib as L  # noqa

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 314159
B = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
S, lab, cfgs = L.load_rows()
F = json.load(open(L.FOLDS))
nC = len(cfgs); y = lab.y.values; t = lab.t.values
files = {"clock": "hgb_clock.csv", "bag+graph": "hgb_bag+graph.csv", "gnn_final": "final.csv",
         "gnn_hybrid": "final+hgb_bag+graph+mem.csv", "bag+graph+mem": "hgb_bag+graph+mem.csv",
         "e_ngru_4runs": "e_ngru_4runs.csv", "h_ngru4_hgb_logit55": "h_ngru4_hgb_logit55.csv",
         "final_hybrid_gnnopt": "final_hybrid.csv"}
preds = {n: L.cv_scores(f"{L.GIT}/{f}", lab) for n, f in files.items()}
for v in ("pairwise", "global_full"):
    s = L.zs_scores(v, lab)
    preds["zs:" + v] = {"oof": s, "rep": {"id0": s, "id1": s},
                        "lodo": {f2: (np.where(lab.cfg.isin(F["lodo"][f2]).values)[0],
                                      s[lab.cfg.isin(F["lodo"][f2]).values]) for f2 in F["lodo"]}}

t0 = time.time()
K = L.draws(nC, B, SEED)
one = np.ones((1, nC))
st = {}
for n, d in preds.items():
    P = L.Pred(d["oof"], lab, nC)
    P0 = L.Pred(d["rep"]["id0"], lab, nC); P1 = L.Pred(d["rep"]["id1"], lab, nC)
    st[n] = {"auroc": (P.auroc(one)[0], P.auroc(K)), "tauroc": (P.tauroc(one)[0], P.tauroc(K)),
             "rtc": (P.tauroc_rtc(one)[0], P.tauroc_rtc(K)),
             "repmean": ((P0.auroc(one)[0] + P1.auroc(one)[0]) / 2, (P0.auroc(K) + P1.auroc(K)) / 2),
             "rep0": (P0.auroc(one)[0], P0.auroc(K))}
print(f"bootstrap B={B} seed={SEED} done in {time.time() - t0:.1f}s; resamples without positives: "
      f"{int(((K @ np.bincount(lab.c, weights=y, minlength=nC)) == 0).sum())}")


def lodo_stat(n, f, metric):
    rows, sc = preds[n]["lodo"][f]
    yy = y[rows]
    if metric in ("auroc",):
        return L.mw_auc(yy, sc)
    if metric == "tauroc":
        tt = t[rows]; num = den = 0.0
        for a in (1, 6, 11, 16, 21, 26):
            m = (tt >= a) & (tt <= a + 4)
            if m.sum() and 0 < yy[m].sum() < m.sum():
                num += yy[m].sum() * L.mw_auc(yy[m], sc[m]); den += yy[m].sum()
        return num / den
    raise ValueError


def cmp(u, v, metric, lodo_metric=None):
    eu, bu = st[u][metric]; ev, bv = st[v][metric]
    d = bu - bv
    lo, hi = np.quantile(d[np.isfinite(d)], [0.025, 0.975])
    r = {"cmp": f"{u} - {v}", "metric": metric, "A": eu, "B": ev, "est": eu - ev, "lo": lo, "hi": hi,
         "p": L.pboot(d), "se_boot": np.nanstd(d), "share_le0": np.mean(d <= 0)}
    if lodo_metric:
        ld = {f.replace("hold_", ""): lodo_stat(u, f, lodo_metric) - lodo_stat(v, f, lodo_metric) for f in F["lodo"]}
        npos = sum(x > 0 for x in ld.values()); nnz = sum(x != 0 for x in ld.values())
        r["lodo_same"] = int(sum(np.sign(x) == np.sign(eu - ev) for x in ld.values()))
        r["sign_p"] = binomtest(npos, nnz, 0.5).pvalue
        r["lodo"] = ld
    return r


FAM_A = [(m, "clock") for m in ("bag+graph", "zs:pairwise", "zs:global_full", "gnn_final", "gnn_hybrid")]
FAM_B = [("gnn_final", "bag+graph"), ("gnn_hybrid", "bag+graph"), ("zs:pairwise", "bag+graph"),
         ("zs:pairwise", "gnn_final"), ("zs:pairwise", "gnn_hybrid"), ("zs:global_full", "bag+graph")]
prim = [cmp(u, v, "tauroc", "tauroc") for u, v in FAM_A] + [cmp(u, v, "auroc", "auroc") for u, v in FAM_B]
for r, h in zip(prim, L.holm([r["p"] for r in prim])):
    r["holm"] = h
print("\n== PRIMARY (Holm over 11), own bootstrap ==")
for r in prim:
    print(f"{r['cmp']:28s} {r['metric']:6s} {r['A']:.3f} vs {r['B']:.3f}  d={r['est']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}]"
          f"  p={r['p']:.4f}  holm={r['holm']:.4f}  LODO {r['lodo_same']}/8 sign p={r['sign_p']:.4f}  se_boot={r['se_boot']:.4f}")

# Plan-conform alternative for family (a): rounds-to-cut bins as the primary time matching
sensA = [cmp(u, v, "rtc") for u, v in FAM_A]
sensB = [cmp(u, v, "repmean") for u, v in FAM_B]
for r, h in zip(sensA + sensB, L.holm([r["p"] for r in sensA + sensB])):
    r["holm"] = h
print("\n== SENSITIVITY family: (a) rtc bins pairs-weighted, (b) per-repeat-mean AUROC ==")
for r in sensA + sensB:
    print(f"{r['cmp']:28s} {r['metric']:7s} d={r['est']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}]  p={r['p']:.4f}  holm={r['holm']:.4f}")
# extra: plan section 5 asks for repeat-0 OOF (each row once)
rep0 = [cmp(u, v, "rep0") for u, v in FAM_B]
rr = [cmp(u, v, "rtc") for u, v in FAM_A] + rep0
for r, h in zip(rr, L.holm([r["p"] for r in rr])):
    r["holm"] = h
print("\n== EXTRA: plan-conform variant: (a) rtc bins, (b) repeat-0 OOF only ==")
for r in rr:
    print(f"{r['cmp']:28s} {r['metric']:7s} {r['A']:.3f} vs {r['B']:.3f} d={r['est']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}]  p={r['p']:.4f}  holm={r['holm']:.4f}")

# DeLong contrast (row-level, anti-conservative here)
print("\n== DeLong (rows independent) vs cluster bootstrap ==")
for u, v in FAM_B:
    dl = L.delong(y, preds[u]["oof"], preds[v]["oof"])
    rb = [r for r in prim if r["cmp"] == f"{u} - {v}"][0]
    print(f"{u} - {v}: DeLong d={dl['d']:+.4f} se={dl['se']:.4f} p={dl['p']:.3g} | boot se={rb['se_boot']:.4f} "
          f"ratio={rb['se_boot'] / dl['se']:.2f} design effect={(rb['se_boot'] / dl['se']) ** 2:.1f}")

# Alternative GNN reference files (not pre-registered either; sensitivity of the (b) ties)
print("\n== ALTERNATIVE reference files for gnn_final / gnn_hybrid (AUROC, repeat-averaged OOF) ==")
alt = [("e_ngru_4runs", "bag+graph"), ("zs:pairwise", "e_ngru_4runs"), ("h_ngru4_hgb_logit55", "bag+graph"),
       ("zs:pairwise", "h_ngru4_hgb_logit55"), ("final_hybrid_gnnopt", "bag+graph"), ("zs:pairwise", "final_hybrid_gnnopt"),
       ("gnn_hybrid", "bag+graph+mem")]
for u, v in alt:
    r = cmp(u, v, "auroc")
    print(f"{r['cmp']:36s} {r['A']:.3f} vs {r['B']:.3f} d={r['est']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] p={r['p']:.4f}")

json.dump({"seed": SEED, "B": B, "primary": prim, "sens": sensA + sensB, "plan_variant": rr},
          open(f"{L.V}/step2_results_seed{SEED}.json", "w"), indent=1, default=float)
