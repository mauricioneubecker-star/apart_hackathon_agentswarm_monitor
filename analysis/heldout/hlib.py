"""Shared code for the held-out comparison: rows, predictors, thresholds, exact cluster-bootstrap engine, DeLong.

Exact paired cluster bootstrap: for one score vector and a partition of the rows into strata, precompute per stratum
the config x config pair-count matrix M[c, c'] = #(positive row in c, negative row in c', same stratum) with
s_pos > s_neg, ties counted 0.5, and the per-config class counts n1, n0. A bootstrap draw is a multiplicity vector
k over configs (config drawn k_c times = its rows duplicated k_c times). Then
    AUROC(k)               = k'Mk / ((k'n1)(k'n0))                         (one stratum = pooled)
    pairs-weighted strat.  = sum_b k'M_b k / sum_b (k'n1_b)(k'n0_b)        (plan / llm_monitor.stratified_auroc)
    positive-weighted      = sum_b w_b AUC_b / sum_b w_b, w_b = k'n1_b     (harness metrics.time_matched_auroc)
which equals the AUROC on the materialised resample (checked in analysis.py against sklearn on explicit resamples).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score

B_ = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad"
HO_DIR = f"{B_}/heldout"
REPO = f"{B_}/stat/repo/gnn_opt"
DATA = f"{B_}/stat/data/night"
LLM = "/Users/mauricio/sim_local/apart_ana/data/llm_monitor"
sys.path.insert(0, REPO)
import harness as H  # noqa: E402
import metrics as MH  # noqa: E402

HO = ["night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch"]
SHORT = {"night_test_id": "test_id", "night_test_ood_family": "ood_family", "night_test_ood_seed": "ood_seed",
         "night_branch": "branch"}
POOL = ["night_train", "night_val"]
RTC_EDGES = [-99, -9, -5, -1, 3, 99]
RTC_LABELS = ["<=-9", "-8..-5", "-4..-1", "0..3", ">3"]
ROUND_BINS = (1, 6, 11, 16, 21, 26, 31)  # harness metrics.time_matched_auroc

E = f"{HO_DIR}/preds/eval"
CV = f"{HO_DIR}/preds/cv"
RG = f"{HO_DIR}/preds/regen"
# name -> (held-out prediction source, threshold source)
PREDICTORS = {
    "clock": (f"{RG}/hgb_clock.csv", ("cv", f"{CV}/hgb_clock.csv")),
    "bag+graph": (f"{RG}/hgb_bag+graph.csv", ("cv", f"{CV}/hgb_bag+graph.csv")),
    "tab_mem": (f"{E}/hgb_bag+graph+mem__allsplits.csv", ("cv", f"{CV}/hgb_bag+graph+mem.csv")),
    "edge": (f"{E}/edge_monitor_top3__allsplits.csv", ("cv", f"{CV}/edge_monitor_top3.csv")),
    "gnn5": (f"{E}/cloud_final_gnn.csv", ("cv", f"{CV}/cloud_final_gnn.csv")),
    "hybrid": (f"{E}/cloud_final.csv", ("cv", f"{CV}/cloud_final.csv")),
    "zs:pairwise": (("llm", "pairwise"), ("pool", None)),
    "zs:global_full": (("llm", "global_full"), ("pool", None)),
    "zs:global_window": (("llm", "global_window"), ("pool", None)),
    "zs:agent": (("llm", "agent"), ("pool", None)),
    "oracle": (f"{RG}/oracle_risk+clock.csv", ("cv", f"{CV}/oracle_risk+clock.csv")),
}
# sensitivity only: the same tab_mem refit in this environment (shows the refit noise that bag+graph carries)
SENS = {"tab_mem(refit here)": (f"{RG}/hgb_bag+graph+mem.csv", ("cv", f"{CV}/hgb_bag+graph+mem.csv"))}


def load_snapshots():
    S = pd.read_csv(f"{DATA}/snapshots.csv", low_memory=False)
    lab = S[(S["eval"] == 1) & S.y3.notna()].copy()
    lab["y"] = lab.y3.astype(int)
    base = pd.read_csv(f"{LLM}/_base/snapshots.csv")
    b = base[["episode_id", "t", "cut", "rounds_to_cut", "before_announce", "group_id", "tip", "mixed"]].rename(
        columns={"episode_id": "run", "t": "round", "mixed": "mixed_llm"})
    lab = lab.merge(b, on=["run", "round"], how="left", validate="one_to_one")
    assert lab.rounds_to_cut.notna().all() and (lab.rounds_to_cut == lab["round"] - lab.cut).all()
    assert (lab.group_id == lab.cfg).all() and (lab.tip == lab.y3).all()
    lab["rtc_bin"] = pd.cut(lab.rounds_to_cut, RTC_EDGES, labels=RTC_LABELS).astype(str)
    lab["round_bin"] = np.digitize(lab["round"].values, ROUND_BINS[1:-1])  # 0..5 = [1,6),[6,11),...,[26,31)
    return S, lab


def read_pred(src):
    """Returns a frame run, round, score (one row per key)."""
    if isinstance(src, tuple) and src[0] == "llm":
        P = pd.read_csv(f"{LLM}/{src[1]}/snapshots.csv", usecols=["episode_id", "t", "zs_tip"])
        P = P.rename(columns={"episode_id": "run", "t": "round", "zs_tip": "score"})
    else:
        P = pd.read_csv(src)[["run", "round", "score"]]
    dup = int(P.duplicated(["run", "round"]).sum())
    assert dup == 0, f"duplicate keys in {src}"
    return P


def attach(rows, P):
    d = rows[["run", "round"]].merge(P, on=["run", "round"], how="left", validate="one_to_one", indicator=True)
    missing = int((d["_merge"] == "left_only").sum())
    nan = int(d.score.isna().sum()) - missing
    return d.score.values.astype(float), missing, nan


def threshold(name, spec, lab):
    """5 %-FPR threshold from training data only (harness metrics.thr_at_fpr: alarm iff score > thr)."""
    kind, f = spec
    if kind == "cv":
        oof = H.id_oof(pd.read_csv(f)).merge(lab[["run", "round", "y", "split"]], on=["run", "round"])
        assert set(oof.split) == {"night_train"}, name
        y, p, src = oof.y.values, oof.score.values, f"night_train ID-OOF ({os.path.basename(f)}, repeat mean)"
    else:
        pool = lab[lab.split.isin(POOL)]
        P = read_pred(PREDICTORS[name][0])
        p, miss, nan = attach(pool, P)
        assert miss == 0 and nan == 0
        y, src = pool.y.values, "night_train + night_val eval rows (raw zero-shot score)"
    thr = MH.thr_at_fpr(y, p)
    return {"thr": float(thr), "src": src, "n_rows": int(len(y)), "n_neg": int((y == 0).sum()),
            "train_fpr": float((p[y == 0] > thr).mean()), "train_recall": float((p[y == 1] > thr).mean())}


# ----------------------------------------------------------------------------------------- bootstrap engine
def pair_mats(y, s, g, strata, C):
    """dict stratum -> (M [C,C], n1 [C], n0 [C]) for rows with stratum label (None/'' excluded)."""
    out = {}
    for b in pd.unique(strata):
        m = strata == b
        yb, sb, gb = y[m], s[m], g[m]
        pos, neg = yb == 1, yb == 0
        n1 = np.bincount(gb[pos], minlength=C).astype(float)
        n0 = np.bincount(gb[neg], minlength=C).astype(float)
        M = np.zeros((C, C))
        sp, gp = sb[pos], gb[pos]
        for c in np.unique(gb[neg]):
            negs = np.sort(sb[neg & (gb == c)])
            lo = np.searchsorted(negs, sp, "left")
            hi = np.searchsorted(negs, sp, "right")
            M[:, c] = np.bincount(gp, weights=lo + 0.5 * (hi - lo), minlength=C)
        out[b] = (M, n1, n0)
    return out


def quad(K, M):
    return np.einsum("bi,ij,bj->b", K, M, K)


def stat_pooled(K, mats):
    (M, n1, n0), = mats.values()
    den = (K @ n1) * (K @ n0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, quad(K, M) / np.where(den > 0, den, 1), np.nan)


def stat_pairs(K, mats):
    num = np.zeros(len(K)); den = np.zeros(len(K))
    for M, n1, n0 in mats.values():
        num += quad(K, M); den += (K @ n1) * (K @ n0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)


def stat_posw(K, mats):
    num = np.zeros(len(K)); den = np.zeros(len(K))
    for M, n1, n0 in mats.values():
        a, b = K @ n1, K @ n0
        ok = (a > 0) & (b > 0)
        auc = np.where(ok, quad(K, M) / np.where(ok, a * b, 1), 0.0)
        num += np.where(ok, a * auc, 0.0); den += np.where(ok, a, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)


def draws(C, B, seed, members=None, strata_groups=None):
    """Multiplicity matrix K [B, C]. members: config indices to resample (others get 0). strata_groups: list of
    config-index arrays, resampled separately (split-stratified bootstrap)."""
    rng = np.random.default_rng(seed)
    K = np.zeros((B, C))
    groups = strata_groups if strata_groups is not None else [np.arange(C) if members is None else np.asarray(members)]
    for grp in groups:
        idx = grp[rng.integers(0, len(grp), size=(B, len(grp)))]
        np.add.at(K, (np.repeat(np.arange(B), len(grp)), idx.ravel()), 1.0)
    return K


def ap_weighted_batch(y, s, w_rows):
    """Average precision (sklearn definition) for many weight vectors at once. w_rows [B, n] (row weights =
    config multiplicities). Ties grouped like sklearn's precision_recall_curve."""
    o = np.argsort(-s, kind="mergesort")
    ys, ss = y[o], s[o]
    ends = np.r_[np.where(np.diff(ss) != 0)[0], len(ss) - 1]
    W = w_rows[:, o]
    tp = np.cumsum(W * ys, axis=1)[:, ends]
    fp = np.cumsum(W * (1 - ys), axis=1)[:, ends]
    P = tp[:, -1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        prec = np.where(tp + fp > 0, tp / np.where(tp + fp > 0, tp + fp, 1), 0.0)
        rec = np.where(P > 0, tp / np.where(P > 0, P, 1), np.nan)
    drec = np.diff(np.concatenate([np.zeros((len(W), 1)), rec], axis=1), axis=1)
    ap = (drec * prec).sum(1)
    return np.where(P[:, 0] > 0, ap, np.nan)


def pval(d):
    d = d[~np.isnan(d)]
    if not len(d):
        return np.nan
    p = 2 * min((d <= 0).mean(), (d >= 0).mean())
    return float(min(1.0, max(p, 1.0 / len(d))))


def holm(ps):
    ps = np.asarray(ps, float)
    o = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * ps[i]))
        adj[i] = run
    return adj


def ci(v):
    v = v[~np.isnan(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)


# ------------------------------------------------------------------------------------------------- DeLong
def delong_cov(y, preds):
    """Fast DeLong (Sun & Xu 2014). preds [k, n]. Returns aucs [k], cov [k, k]. Rows treated as independent."""
    y = np.asarray(y)
    pos, neg = preds[:, y == 1], preds[:, y == 0]
    m, n = pos.shape[1], neg.shape[1]
    tx = np.vstack([stats.rankdata(r) for r in pos])
    ty = np.vstack([stats.rankdata(r) for r in neg])
    tz = np.vstack([stats.rankdata(r) for r in np.hstack([pos, neg])])
    aucs = tz[:, :m].sum(1) / m / n - (m + 1.0) / 2.0 / n
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m
    cov = np.atleast_2d(np.cov(v01)) / m + np.atleast_2d(np.cov(v10)) / n
    return aucs, cov


def delong_diff(y, a, b, strata=None):
    """Row-level DeLong test of AUROC(a) - AUROC(b); with strata: pairs-weighted combination of independent
    within-stratum DeLong estimates (matches the pairs-weighted stratified AUROC). Anti-conservative here."""
    if strata is None:
        aucs, cov = delong_cov(y, np.vstack([a, b]))
        d, v = aucs[0] - aucs[1], cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    else:
        d = v = 0.0
        ws = []
        parts = []
        for s in pd.unique(strata):
            m = strata == s
            npos, nneg = int(y[m].sum()), int((1 - y[m]).sum())
            if npos >= 2 and nneg >= 2:
                aucs, cov = delong_cov(y[m], np.vstack([a[m], b[m]]))
                ws.append(npos * nneg); parts.append((aucs[0] - aucs[1], cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]))
        W = float(sum(ws))
        for w, (dd, vv) in zip(ws, parts):
            d += w / W * dd; v += (w / W) ** 2 * vv
    z = d / np.sqrt(v) if v > 0 else np.nan
    return float(d), float(2 * stats.norm.sf(abs(z))) if v > 0 else np.nan


def stratified_auroc(y, p, strata):
    """llm_monitor.evaluate.stratified_auroc (pairs-weighted mean of within-stratum AUROCs)."""
    df = pd.DataFrame({"y": y, "p": p, "s": strata}).dropna()
    num = den = 0.0
    for _, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            w = npos * nneg
            num += w * roc_auc_score(g.y, g.p); den += w
    return float(num / den) if den else float("nan")
