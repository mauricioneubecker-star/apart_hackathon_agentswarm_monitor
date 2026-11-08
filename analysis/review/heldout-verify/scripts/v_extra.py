"""Extra checks (own code): hybrid = logit blend of frozen files; GNN team's harness CIs (seed 0, B = 1000,
rng.choice over configs in order of appearance); AUPRC; row-level DeLong (anti-conservative contrast); within mixed
cfg x rounds-to-cut bin; Spearman with round."""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
V = f"{SCR}/heldout-verify"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
R = pd.read_csv(f"{V}/heldout_rows.csv", low_memory=False)
y = R.y3.values.astype(int)
n = len(R)

def att(P):
    d = R[["run", "round"]].merge(P[["run", "round", "score"]], on=["run", "round"], how="left")
    assert d.score.notna().all()
    return d.score.values
def f(p):
    return att(pd.read_csv(p))
def zs(v):
    return att(pd.read_csv(f"{LLM}/{v}/snapshots.csv", usecols=["episode_id", "t", "zs_tip"]).rename(
        columns={"episode_id": "run", "t": "round", "zs_tip": "score"}))
SC = {"clock": f(f"{V}/preds/refit/hgb_clock.csv"), "bag+graph": f(f"{V}/preds/refit/hgb_bag+graph.csv"),
      "zs:pairwise": zs("pairwise"), "zs:global_full": zs("global_full"),
      "gnn5": f(f"{V}/preds/eval/cloud_final_gnn.csv"), "hybrid": f(f"{V}/preds/eval/cloud_final.csv"),
      "tab_mem": f(f"{V}/preds/eval/hgb_bag+graph+mem__allsplits.csv"),
      "edge": f(f"{V}/preds/eval/edge_monitor_top3__allsplits.csv")}

# 1. hybrid = sigmoid(0.5 logit(gnn5) + 0.5 logit(tab_mem))?
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
bl = 1 / (1 + np.exp(-(0.5 * lg(SC["gnn5"]) + 0.5 * lg(SC["tab_mem"]))))
print("hybrid eval == logit blend 0.5 (gnn5, tab_mem): max|diff|", float(np.abs(bl - SC["hybrid"]).max()))

# 2. GNN team's harness bootstrap (metrics.boot_ci semantics, re-implemented)
cfg_order = R.cfg.unique()          # order of appearance (rows are in snapshots.csv order)
idx = {c: np.where(R.cfg.values == c)[0] for c in cfg_order}
rng = np.random.default_rng(0)
draws = [np.concatenate([idx[c] for c in rng.choice(cfg_order, len(cfg_order))]) for _ in range(1000)]
for k in ("hybrid", "gnn5", "tab_mem", "edge"):
    v = [roc_auc_score(y[s], SC[k][s]) for s in draws if 0 < y[s].sum() < len(s)]
    print(f"  harness-style CI {k:8s} AUROC {roc_auc_score(y, SC[k]):.3f} [{np.quantile(v, .025):.3f}, {np.quantile(v, .975):.3f}]"
          f"  AUPRC {average_precision_score(y, SC[k]):.3f}")
for b in ("gnn5", "tab_mem", "edge"):
    d = [roc_auc_score(y[s], SC["hybrid"][s]) - roc_auc_score(y[s], SC[b][s]) for s in draws if 0 < y[s].sum() < len(s)]
    print(f"  harness-style hybrid - {b:8s} {np.quantile(d, .025):+.3f} / {np.quantile(d, .5):+.3f} / {np.quantile(d, .975):+.3f}"
          f"  share>0 {np.mean(np.array(d) > 0):.3f}")

# 3. row-level DeLong (fast structural components), labelled anti-conservative
def delong_parts(yy, ss):
    pos, neg = ss[yy == 1], ss[yy == 0]
    m, k = len(pos), len(neg)
    allv = np.concatenate([pos, neg])
    r_all = stats.rankdata(allv)
    r_pos = stats.rankdata(pos); r_neg = stats.rankdata(neg)
    v10 = (r_all[:m] - r_pos) / k          # per positive: share of negatives below (+ties/2)
    v01 = 1 - (r_all[m:] - r_neg) / m      # per negative: share of positives above (+ties/2)
    return v10.mean(), v10, v01
def delong_diff(yy, a, b):
    A, a10, a01 = delong_parts(yy, a); Bv, b10, b01 = delong_parts(yy, b)
    m, k = len(a10), len(a01)
    s10 = np.cov(np.vstack([a10, b10])); s01 = np.cov(np.vstack([a01, b01]))
    var = (s10[0, 0] + s10[1, 1] - 2 * s10[0, 1]) / m + (s01[0, 0] + s01[1, 1] - 2 * s01[0, 1]) / k
    return A - Bv, var
RB = pd.cut(R.rounds_to_cut, [-99, -9, -5, -1, 3, 99], labels=False).values
fam = [("a1", "bag+graph", "clock", "tm"), ("a2", "zs:pairwise", "clock", "tm"), ("a3", "zs:global_full", "clock", "tm"),
       ("a4", "gnn5", "clock", "tm"), ("a5", "hybrid", "clock", "tm"), ("b1", "gnn5", "bag+graph", "p"),
       ("b2", "hybrid", "bag+graph", "p"), ("b3", "zs:pairwise", "bag+graph", "p"), ("b4", "zs:pairwise", "gnn5", "p"),
       ("b5", "zs:pairwise", "hybrid", "p"), ("b6", "zs:global_full", "bag+graph", "p")]
nsig = 0
for lab, a, b, st in fam:
    if st == "p":
        d, var = delong_diff(y, SC[a], SC[b])
    else:   # pairs-weighted combination of per-bin DeLong estimates (bins with both classes)
        num = den = vv = 0.0
        ws, ds, vs = [], [], []
        for bb in np.unique(RB):
            m = RB == bb
            p1, p0 = y[m].sum(), (1 - y[m]).sum()
            if p1 >= 2 and p0 >= 2:
                dd, v_ = delong_diff(y[m], SC[a][m], SC[b][m])
                ws.append(p1 * p0); ds.append(dd); vs.append(v_)
        ws = np.array(ws, float)
        d = float((ws * np.array(ds)).sum() / ws.sum()); var = float((ws ** 2 * np.array(vs)).sum() / ws.sum() ** 2)
    p = 2 * stats.norm.sf(abs(d) / np.sqrt(var))
    nsig += p < 0.05
    print(f"  DeLong (row-level, anti-conservative) {lab} {a} - {b}: d {d:+.3f} se {np.sqrt(var):.4f} p {p:.2g}")
print("  DeLong p < 0.05 in", nsig, "of 11")

# 4. within mixed cfg x rounds-to-cut bin (pairs-weighted), mixed = held-out runs of the cfg tipped and untipped
mx = R.groupby("cfg").tipped.agg(lambda v: v.min() == 0 and v.max() == 1)
mixed = R.cfg.isin(mx[mx].index).values
strata = (R.cfg + "|" + RB.astype(str)).values
for k in ("clock", "bag+graph", "zs:pairwise", "zs:global_full", "gnn5", "hybrid"):
    num = den = 0.0
    for s_ in np.unique(strata[mixed]):
        m = mixed & (strata == s_)
        p1, p0 = y[m].sum(), (1 - y[m]).sum()
        if p1 and p0:
            num += p1 * p0 * roc_auc_score(y[m], SC[k][m]); den += p1 * p0
    print(f"  within mixed cfg x bin {k:15s} {num / den:.3f}")
print("  mixed cfgs", int(mx.sum()), "rows", int(mixed.sum()), "pos", int(y[mixed].sum()))

# 5. Spearman with round
for k in ("zs:global_full", "clock", "zs:pairwise", "hybrid"):
    print(f"  Spearman(score, round) {k:15s} {stats.spearmanr(SC[k], R['round']).correlation:.2f}")
