"""Independent check of the 5 %-FPR thresholds (training data only), recall / FPR on held-out rows, lead time.

Rule re-implemented from the harness definition (metrics.thr_at_fpr, read not imported): sort training negatives,
k = ceil(0.95 n_neg) - 1, thr = neg[k] + 1e-12, alarm iff score > thr.
Trained models: night_train ID out-of-fold CV predictions (folds id*, averaged over repeats per (run, round)).
Zero-shot: raw zs_tip on night_train + night_val labelled rows."""
import numpy as np
import pandas as pd

SCR = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
V = f"{SCR}/heldout-verify"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
HELD = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]

S = pd.read_csv(f"{SCR}/stat/data/night/snapshots.csv", low_memory=False)
LAB = S[(S["eval"] == 1) & S.y3.notna()][["run", "round", "split", "y3", "tipped", "tip_round", "cfg"]]
R = pd.read_csv(f"{V}/heldout_rows.csv", low_memory=False)

def thr_at(y, p, fpr=0.05):
    neg = np.sort(p[y == 0])
    k = int(np.ceil((1 - fpr) * len(neg))) - 1
    return neg[min(max(k, 0), len(neg) - 1)] + 1e-12

def cv_thr(path):
    P = pd.read_csv(path)
    allsplits = P.merge(S[["run", "round", "split"]], on=["run", "round"], how="left").split.value_counts().to_dict()
    Q = P[P.fold.astype(str).str.startswith("id")]
    oof = Q.groupby(["run", "round"], as_index=False).score.mean()
    m = oof.merge(LAB, on=["run", "round"], how="inner")
    assert set(m.split) == {"night_train"}
    return thr_at(m.y3.values, m.score.values), m, allsplits, sorted(Q.fold.unique())

def zs_scores(variant, rows):
    P = pd.read_csv(f"{LLM}/{variant}/snapshots.csv", usecols=["episode_id", "t", "zs_tip"]).rename(
        columns={"episode_id": "run", "t": "round", "zs_tip": "score"})
    d = rows[["run", "round"]].merge(P, on=["run", "round"], how="left")
    assert d.score.notna().all() and len(d) == len(rows)
    return d.score.values

def held_scores(path):
    P = pd.read_csv(path)[["run", "round", "score"]]
    d = R[["run", "round"]].merge(P, on=["run", "round"], how="left")
    assert d.score.notna().all()
    return d.score.values

def lead(score, thr):
    d = R.assign(s=score)
    leads, fa = [], []
    for run, g in d.groupby("run"):
        g = g.sort_values("round")
        al = g[g.s > thr]["round"]
        if g.tipped.iloc[0] == 1 and g.tip_round.notna().iloc[0]:
            tr = g.tip_round.iloc[0]
            pre = al[al < tr]
            leads.append(tr - pre.min() if len(pre) else 0)
        else:
            fa.append(int(len(al) > 0))
    leads = np.array(leads)
    return int((leads > 0).sum()), len(leads), float(np.median(leads[leads > 0])), int(np.sum(fa)), len(fa)

y = R.y3.values.astype(int)
print(f"{'model':16s} {'thr':>10s} {'src rows':>8s} {'trainFPR':>8s} | {'R@thr':>6s} {'FPR_ho':>6s} | lead: alarmed/tipped, median, FA runs | CV-file splits / folds")
TR = {"clock": ("cv/hgb_clock.csv", "refit/hgb_clock.csv"),
      "bag+graph": ("cv/hgb_bag+graph.csv", "refit/hgb_bag+graph.csv"),
      "gnn5": ("cv/cloud_final_gnn.csv", "eval/cloud_final_gnn.csv"),
      "hybrid": ("cv/cloud_final.csv", "eval/cloud_final.csv"),
      "tab_mem": ("cv/hgb_bag+graph+mem.csv", "eval/hgb_bag+graph+mem__allsplits.csv"),
      "edge": ("cv/edge_monitor_top3.csv", "eval/edge_monitor_top3__allsplits.csv")}
for k, (cvf, hf) in TR.items():
    t, m, allsp, folds = cv_thr(f"{V}/preds/{cvf}")
    fpr_tr = float((m.score.values[m.y3.values == 0] > t).mean())
    s = held_scores(f"{V}/preds/{hf}")
    rec, fpr = (s[y == 1] > t).mean(), (s[y == 0] > t).mean()
    a, nt, med, f, nu = lead(s, t)
    print(f"{k:16s} {t:10.5g} {len(m):8d} {fpr_tr:8.4f} | {rec:6.3f} {fpr:6.3f} | {a}/{nt}, {med}, {f}/{nu} | {allsp} / {len(folds)} id folds")

POOL = LAB[LAB.split.isin(["night_train", "night_val"])]
assert not POOL.split.isin(HELD).any()
for v in ("pairwise", "global_full", "global_window", "agent"):
    p = zs_scores(v, POOL)
    t = thr_at(POOL.y3.values, p)
    fpr_tr = float((p[POOL.y3.values == 0] > t).mean())
    s = zs_scores(v, R)
    rec, fpr = (s[y == 1] > t).mean(), (s[y == 0] > t).mean()
    a, nt, med, f, nu = lead(s, t)
    # alternative: night_train only
    PT = POOL[POOL.split == "night_train"]
    t2 = thr_at(PT.y3.values, zs_scores(v, PT))
    print(f"zs:{v:13s} {t:10.5g} {len(POOL):8d} {fpr_tr:8.4f} | {rec:6.3f} {fpr:6.3f} | {a}/{nt}, {med}, {f}/{nu} | "
          f"(night_train-only thr would be {t2:.4g}: recall {(s[y == 1] > t2).mean():.3f})")
