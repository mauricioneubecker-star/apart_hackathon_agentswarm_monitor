"""Evaluate the LLM monitors against the reference baselines on the GNN rows.

  python -m llm_monitor.evaluate [--data data/llm_monitor] [--runs sim_dataset/runs_night] [--variants ...]
      [--compare ext.csv ...] [--combine ext.csv] [--boot 1000] [--out results/llm_monitor]

Protocols
  (a) pooled OOF over all night configs: GroupKFold(5, shuffled) by config, 3 seeds; zero-shot scores need no
      training (isotonic calibration is cross-fitted for the Brier score).
  (b) frozen: stacking config selected by grouped 5-fold CV over night_train + night_val (OOF AUPRC), 5 % FPR
      thresholds from those OOF predictions, refit on train + val, evaluated once on each held-out split
      (night_test_id, night_test_ood_family, night_test_ood_seed, night_branch, night_vx_* when present).
Predictors
  reference: clock, pairwise (feature pairwise monitor), edge_monitor, bag (bag-of-edges), bag+graph, oracle
  LLM      : zs:<variant> (zero-shot), lr:<variant> / hgb:<variant> (stacked heads on monitor outputs + deltas)
  external : ext:<name> from --compare (episode_id, t, p_graph), raw scores; comb:<variant>+<name> from --combine
CIs: bootstrap over configs (vx: over bases), 1000x, paired on identical rows and draws.
Everything is deterministic (fixed seeds); no API calls.
"""
from __future__ import annotations

import argparse
import json
import os

# HGB with OpenMP threads was >10x slower here (sandboxed macOS); single-threaded is also bit-for-bit deterministic
os.environ.setdefault("OMP_NUM_THREADS", "1")
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import prompts as P
from . import refbase
from .aggregate import GLOBAL_VARIANTS, OUT as DATA, STACK_BASE
from .common import REPO, find_runs, load_messages
from .client import cost_of

warnings.filterwarnings("ignore", category=UserWarning)
RES = os.path.join(REPO, "results", "llm_monitor")
SEEDS = (0, 1, 2)
POOL = ("night_train", "night_val")
HELDOUT = ("night_test_id", "night_test_ood_family", "night_test_ood_seed", "night_branch")
REFS = ["clock", "pairwise", "edge_monitor", "bag", "bag+graph", "oracle"]
FPR = 0.05
_T0 = [None]


def log(msg):
    import time
    _T0[0] = _T0[0] or time.time()
    print(f"[{time.time() - _T0[0]:7.1f}s] {msg}", flush=True)


# ------------------------------------------------------------------------------------------------------ metrics
def thr_at_fpr(y, p, fpr=FPR):
    """Lowest threshold with realised FPR <= fpr (scores >= thr alarm). Coarse integer LLM scores have many ties, so
    the plain quantile can alarm on far more than 5 % of negatives."""
    neg = np.asarray(p)[np.asarray(y) == 0]
    neg = neg[~np.isnan(neg)]
    if not len(neg):
        return 0.5
    q = float(np.quantile(neg, 1 - fpr))
    if (neg >= q).mean() > fpr:
        above = neg[neg > q]
        q = float(above.min()) if len(above) else float(np.nextafter(q, np.inf))
    return q


def bin_metrics(y, p, thr=None, calib=None):
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = ~np.isnan(y) & ~np.isnan(p)
    y, p = y[m], p[m]
    out = {"n": int(len(y)), "n_pos": int(y.sum())}
    if len(y) and 0 < y.sum() < len(y):
        out["auroc"] = float(roc_auc_score(y, p))
        out["auprc"] = float(average_precision_score(y, p))
        pc = calib(p) if calib is not None else p
        out["brier"] = float(brier_score_loss(y, np.clip(pc, 0, 1)))
        if thr is not None:
            out["recall_at_5fpr"] = float((p[y == 1] >= thr).mean())
            out["fpr_at_thr"] = float((p[y == 0] >= thr).mean())
    return out


def stratified_auroc(y, p, strata):
    """Pairs-weighted mean of within-stratum AUROCs (strata with both classes); a stratum-only predictor gets 0.5."""
    df = pd.DataFrame({"y": y, "p": p, "s": strata}).dropna()
    num = den = 0.0
    for _, g in df.groupby("s"):
        npos, nneg = int(g.y.sum()), int((1 - g.y).sum())
        if npos and nneg:
            w = npos * nneg
            num += w * roc_auc_score(g.y, g.p)
            den += w
    return float(num / den) if den else float("nan")


# ------------------------------------------------------------------------------------------------------ models
def make_lr(C):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=C, max_iter=5000))


def make_hgb(depth, seed=0):
    return HistGradientBoostingClassifier(max_depth=depth, max_iter=200, learning_rate=0.05, min_samples_leaf=40,
                                          random_state=seed)


STACK_GRID = {"lr": [("lr", {"C": c}, fs) for c in (0.01, 0.1, 1.0) for fs in ("level", "level+delta")],
              "hgb": [("hgb", {"depth": d}, fs) for d in (2, 3) for fs in ("level", "level+delta")]}


def stack_cols(df, variant, fs):
    base = STACK_BASE["global" if variant in GLOBAL_VARIANTS else "unit"]
    cols = [c for c in base if c in df]
    if fs == "level+delta":
        cols += [f"d{lag}_{c}" for c in base for lag in (1, 3) if f"d{lag}_{c}" in df]
    return cols


def fit_predict(spec, Xtr, ytr, Xte, seed=0):
    kind, par = spec[0], spec[1]
    if kind == "lr":
        m = make_lr(par["C"]).fit(Xtr, ytr)
    elif kind == "hgb":
        m = make_hgb(par["depth"], seed).fit(Xtr, ytr)
    elif kind == "ref_hgb":
        m = refbase.hgb(seed).fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]


def folds(groups, seed, k=5):
    return list(GroupKFold(n_splits=k, shuffle=True, random_state=seed).split(np.zeros(len(groups)), groups=groups))


# --------------------------------------------------------------------------------------------------- data
class Data:
    def __init__(self, a):
        self.data_dir = a.data
        self.base = pd.read_csv(os.path.join(a.data, "_base", "snapshots.csv"), low_memory=False)
        self.nodes = pd.read_csv(os.path.join(a.data, "_base", "nodes.csv"))
        self.key = pd.MultiIndex.from_frame(self.base[["episode_id", "t"]])
        self.runs = find_runs(a.runs)
        ref_path = os.path.join(a.data, "_ref", "table.csv.gz")
        T = pd.read_csv(ref_path) if os.path.exists(ref_path) and not a.rebuild_ref else None
        if T is None or set(T.episode_id) != set(self.base.episode_id):    # run set changed (e.g. vx added)
            T = refbase.build_table(self.base, self.runs)
            os.makedirs(os.path.dirname(ref_path), exist_ok=True)
            T.to_csv(ref_path, index=False, float_format="%.6g")
            T = pd.read_csv(ref_path)          # same (rounded) values whether the cache was just built or reused
        T = T.set_index(["episode_id", "t"]).reindex(self.key).reset_index()
        T["risk_count"] = self.base.risk_count.values
        self.ref = T
        self.var = {}
        self.var_nodes = {}
        for v in a.variants:
            p = os.path.join(a.data, v + a.suffix, "snapshots.csv")
            if os.path.exists(p):
                S = pd.read_csv(p).set_index(["episode_id", "t"]).reindex(self.key).reset_index()
                self.var[v] = S
                self.var_nodes[v] = pd.read_csv(os.path.join(a.data, v + a.suffix, "nodes.csv"))
        self.ext = {}
        for f in a.compare or []:
            nm = os.path.splitext(os.path.basename(f))[0]
            E = pd.read_csv(f).set_index(["episode_id", "t"]).reindex(self.key)
            self.ext[nm] = E["p_graph"].values
        self.combine = None
        if a.combine:
            E = pd.read_csv(a.combine).set_index(["episode_id", "t"]).reindex(self.key)
            self.combine = (os.path.splitext(os.path.basename(a.combine))[0], E["p_graph"].values)
        self.y = self.base.tip.values.astype(float)
        self.night = self.base.split.str.startswith("night_") & ~self.base.split.str.startswith("night_vx")
        self.groups = self.base.group_id.values


# ------------------------------------------------------------------------------------------- protocol (a): OOF
def oof_fit(D, X, rows, spec, seeds=SEEDS):
    """OOF predictions on `rows` (bool mask, y defined), averaged over seeds; also per-seed predictions."""
    idx = np.where(rows)[0]
    y = D.y[idx]
    per = []
    for s in seeds:
        p = np.full(len(idx), np.nan)
        for tr, te in folds(D.groups[idx], s):
            p[te] = fit_predict(spec, X[idx[tr]], y[tr], X[idx[te]], seed=s)
        per.append(p)
    out = np.full(len(D.y), np.nan)
    out[idx] = np.mean(per, 0)
    return out, per


def edge_oof(D, rows, seeds=SEEDS):
    E, _ = refbase.load_graph(D.runs)
    idx = np.where(rows)[0]
    keys = D.base.iloc[idx][["episode_id", "t"]].reset_index(drop=True)
    y = D.y[idx]
    per = []
    for s in seeds:
        p = np.full(len(idx), np.nan)
        for tr, te in folds(D.groups[idx], s):
            mdl = refbase.EdgeMonitor(E, s).fit(keys.iloc[tr].reset_index(drop=True), y[tr])
            p[te] = mdl.predict(keys.iloc[te].reset_index(drop=True))
        per.append(p)
    out = np.full(len(D.y), np.nan)
    out[idx] = np.mean(per, 0)
    return out, per, E


def iso_crossfit(D, score, rows, seed=0):
    """Cross-fitted isotonic calibration of a raw score (for the zero-shot Brier)."""
    idx = np.where(rows & ~np.isnan(score))[0]
    out = np.full(len(D.y), np.nan)
    for tr, te in folds(D.groups[idx], seed):
        ir = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(score[idx[tr]], D.y[idx[tr]])
        out[idx[te]] = ir.predict(score[idx[te]])
    return out


# -------------------------------------------------------------------------------------------------- bootstrap
def bootstrap(D, rows, preds: dict, refs_for_diff, n_boot, seed=0, unit="group_id"):
    """Paired bootstrap over configs on identical rows: CIs for AUROC/AUPRC and differences vs references."""
    names = [n for n in preds if not np.isnan(preds[n][rows]).any()]
    idx = np.where(rows)[0]
    g = D.base[unit].values[idx]
    ug = np.unique(g)
    members = {u: np.where(g == u)[0] for u in ug}
    rng = np.random.default_rng(seed)
    y = D.y[idx]
    res = {n: {"auroc": [], "auprc": []} for n in names}
    for _ in range(n_boot):
        pick = rng.choice(ug, len(ug), replace=True)
        b = np.concatenate([members[u] for u in pick])
        yb = y[b]
        if not (0 < yb.sum() < len(yb)):
            continue
        for n in names:
            pb = preds[n][idx][b]
            res[n]["auroc"].append(roc_auc_score(yb, pb))
            res[n]["auprc"].append(average_precision_score(yb, pb))
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [np.nan, np.nan]  # noqa
    out = {n: {f"{m}_ci": ci(res[n][m]) for m in ("auroc", "auprc")} for n in names}
    diffs = {}
    for n in names:
        for r in refs_for_diff:
            if r in res and r != n:
                for m in ("auroc", "auprc"):
                    d = np.array(res[n][m]) - np.array(res[r][m])
                    diffs[f"{n} - {r}|{m}"] = {"mean": float(d.mean()), "ci": ci(d), "p_le_0": float((d <= 0).mean())}
    return out, diffs, names


# ------------------------------------------------------------------------------------------------ slices
def slices(D, rows, preds, names):
    b = D.base
    rtc_bin = pd.cut(b.rounds_to_cut, [-99, -9, -5, -1, 3, 99], labels=["<=-9", "-8..-5", "-4..-1", "0..3", ">3"])
    sl = {"risk=0": b.risk_count == 0, "risk<=2": b.risk_count <= 2, "risk 3-7": b.risk_count.between(3, 7),
          "before_announcement": b.before_announce == 1, "K2": b.cat == "K2", "K4": b.cat == "K4"}
    for c in ("board", "team_channels", "dm_only"):
        sl[f"channel={c}"] = b.channels == c
    for lab in rtc_bin.cat.categories:
        sl[f"rtc {lab}"] = rtc_bin == lab
    out = {}
    for s, m in sl.items():
        mm = rows & m.values
        out[s] = {n: bin_metrics(D.y[mm], preds[n][mm]) for n in names}
    # time-matched (within rounds-to-cut bins), and within mixed configs conditional on config x time bin
    tm, mx = {}, {}
    mixed = rows & (b.mixed == 1).values
    strata_cfg = (b.group_id + "|" + rtc_bin.astype(str)).values
    for n in names:
        tm[n] = stratified_auroc(D.y[rows], preds[n][rows], rtc_bin.astype(str).values[rows])
        mx[n] = stratified_auroc(D.y[mixed], preds[n][mixed], strata_cfg[mixed])
    out["time_matched_auroc"] = tm
    out["mixed_cfg_x_time_auroc"] = mx
    return out


def run_level(D, scores: dict, names, mask_split=None):
    """AUROC of a run-level score at fixed prefixes -> final tipped; only runs not yet tipped at the prefix.
    Also within-config run-level AUROC among replicates of mixed configs (pairs-weighted)."""
    b = D.base
    out = {}
    first = b.groupby("episode_id").first()
    for pref in ("cut-6", "mech+2"):
        if pref == "cut-6":
            tp = (first.cut - 6)
        else:
            tp = first.first_mech_round + 2
        tp = tp.dropna().astype(int)
        res = {}
        for n in names:
            rows = []
            for eid, t in tp.items():
                if mask_split is not None and first.at[eid, "split"] not in mask_split:
                    continue
                if t < 1 or t > first.at[eid, "R"]:
                    continue
                r = b.index[(b.episode_id == eid) & (b.t == t)]
                if not len(r) or b.risk_count.iat[r[0]] >= 8:
                    continue
                rows.append((eid, first.at[eid, "group_id"], first.at[eid, "tipped"], scores[n][r[0]],
                             first.at[eid, "mixed"]))
            R = pd.DataFrame(rows, columns=["eid", "cfg", "y", "p", "mixed"]).dropna()
            m = bin_metrics(R.y, R.p)
            mixd = R[R.mixed == 1]
            m["within_config_auroc"] = stratified_auroc(mixd.y.values, mixd.p.values, mixd.cfg.values)
            m["n_mixed_runs"] = int(len(mixd))
            res[n] = m
        out[pref] = res
    return out


def lead_time(D, rows_split, score, thr):
    """First alarm (score >= thr) at a row before theta; lead = tip_round - t_alarm for tipped runs."""
    b = D.base
    leads, alarmed, fa, n_tip, n_neg = [], 0, 0, 0, 0
    for eid, g in b[rows_split].groupby("episode_id"):
        gi = g.index.values
        valid = gi[~np.isnan(D.y[gi])]
        s = score[valid]
        hit = valid[s >= thr]
        tipped = bool(g.tipped.iloc[0])
        if tipped:
            n_tip += 1
            if len(hit):
                alarmed += 1
                leads.append(int(g.tip_round.iloc[0] - b.t.values[hit[0]]))
        else:
            n_neg += 1
            fa += bool(len(hit))
    return {"tipped_runs": n_tip, "alarm_before_tip_share": alarmed / n_tip if n_tip else None,
            "median_lead_rounds": float(np.median(leads)) if leads else None,
            "lead_rounds_iqr": [float(np.percentile(leads, 25)), float(np.percentile(leads, 75))] if leads else None,
            "untipped_runs": n_neg, "false_alarm_run_share": fa / n_neg if n_neg else None}


def node_eval(D, variant, rows_split):
    """Zero-shot node score p_will among agents not yet violating: pooled AUROC and mean within-snapshot AUROC."""
    if variant not in D.var_nodes:
        return None
    N = D.nodes.merge(D.var_nodes[variant], on=["episode_id", "t", "node_id"], how="left")
    N = N.merge(D.base[["episode_id", "t", "split"]][rows_split], on=["episode_id", "t"])
    N = N[N.violates_within_delta.notna()]
    out = {}
    for nm, sub in (("all", N), ("stuck", N[N.stuck == 1])):
        s = sub.dropna(subset=["p_will"])
        m = bin_metrics(s.violates_within_delta, s.p_will)
        aucs, w = [], []
        for _, g in s.groupby(["episode_id", "t"]):
            npos = int(g.violates_within_delta.sum())
            if 0 < npos < len(g) and g.p_will.nunique() > 1:
                aucs.append(roc_auc_score(g.violates_within_delta, g.p_will))
                w.append(npos * (len(g) - npos))
        m["within_snapshot_auroc"] = float(np.average(aucs, weights=w)) if aucs else None
        m["n_snapshots_within"] = len(aucs)
        out[nm] = m
    return out


def count_eval(D, rows, preds_count):
    y = D.base.risk_count.values.astype(float)
    return {n: {"mae": float(np.nanmean(np.abs(p[rows] - y[rows]))), "n": int((~np.isnan(p[rows])).sum())}
            for n, p in preds_count.items()}


# ----------------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--runs", nargs="+", default=["sim_dataset/runs_night"])
    ap.add_argument("--variants", nargs="*", default=P.VARIANTS)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--compare", nargs="*", default=[])
    ap.add_argument("--combine", default=None)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--out", default=RES)
    ap.add_argument("--rebuild-ref", action="store_true")
    ap.add_argument("--write-ref-preds", action="store_true", help="write bag OOF preds as a --combine/--compare csv")
    a = ap.parse_args(argv)
    log("loading data")
    D = Data(a)
    log("data loaded")
    os.makedirs(os.path.join(a.out, "oof"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "frozen"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "preds"), exist_ok=True)
    b = D.base
    yok = ~np.isnan(D.y)
    variants = list(D.var)
    covered = np.ones(len(b), bool)
    for v in variants:
        covered &= D.var[v].zs_tip.notna().values
    print(f"variants with data: {variants}; night tip rows {int((D.night & yok).sum())}, covered by all "
          f"{int((D.night & yok & covered).sum())}", flush=True)

    # ---------------- protocol (b) model selection on the pool (train + val): used by both protocols
    pool = yok & b.split.isin(POOL).values
    sel = {}
    for v in variants:
        rows = pool & D.var[v].zs_tip.notna().values
        for head, grid in STACK_GRID.items():
            best = None
            for spec in grid:
                cols = stack_cols(D.var[v], v, spec[2])
                X = D.var[v][cols].values
                p, _ = oof_fit(D, X, rows, spec, seeds=(0,))
                s = average_precision_score(D.y[rows], p[rows])
                if best is None or s > best[0]:
                    best = (s, spec, cols)
            sel[(v, head)] = {"spec": best[1], "cols": best[2], "pool_oof_auprc": float(best[0])}
    if D.combine:
        cn, cp = D.combine
        for v in variants:
            cols = sel[(v, "lr")]["cols"]
            sel[(f"comb:{v}+{cn}", "lr")] = {"spec": sel[(v, "lr")]["spec"], "cols": cols + ["__ext"]}
            sel[(f"comb:{v}+{cn}", "hgb")] = {"spec": sel[(v, "hgb")]["spec"], "cols": cols + ["__ext"]}

    def Xof(v, cols):
        if v.startswith("comb:"):
            vv = v.split(":")[1].split("+")[0]
            X = D.var[vv][[c for c in cols if c != "__ext"]].values
            return np.column_stack([X, D.combine[1]])
        return D.var[v][cols].values

    fs = refbase.feature_sets(D.ref.columns)

    log("stack selection done")
    # ---------------- protocol (a): pooled OOF over all night configs
    rows_a = D.night.values & yok
    preds, per_seed = {}, {}
    for r in REFS:
        if r == "edge_monitor":
            preds[r], per_seed[r], E_all = edge_oof(D, rows_a)
        else:
            preds[r], per_seed[r] = oof_fit(D, D.ref[fs[r]].values, rows_a, ("ref_hgb", {}))
        print(f"(a) {r}: AUROC {roc_auc_score(D.y[rows_a], preds[r][rows_a]):.3f}", flush=True)
    for v in variants:
        zs = D.var[v].zs_tip.values
        preds[f"zs:{v}"] = np.where(rows_a, zs, np.nan)
        if "p_tip_3_s0" in D.var[v] and D.var[v].n_samples.max() > 1:
            preds[f"zs1:{v}"] = np.where(rows_a, D.var[v].p_tip_3_s0.values / 100, np.nan)
        rv = rows_a & ~np.isnan(zs)
        for head in ("lr", "hgb"):
            s_ = sel[(v, head)]
            preds[f"{head}:{v}"], per_seed[f"{head}:{v}"] = oof_fit(D, Xof(v, s_["cols"]), rv, s_["spec"])
    if D.combine:
        cn, cp = D.combine
        preds[f"ext:{cn}"] = np.where(rows_a, cp, np.nan)
        for v in variants:
            k = f"comb:{v}+{cn}"
            rv = rows_a & ~np.isnan(D.var[v].zs_tip.values) & ~np.isnan(cp)
            for head in ("lr", "hgb"):
                s_ = sel[(k, head)]
                preds[f"{head}:{k}"], per_seed[f"{head}:{k}"] = oof_fit(D, Xof(k, s_["cols"]), rv, s_["spec"])
    for nm, p in D.ext.items():
        preds[f"ext:{nm}"] = np.where(rows_a, p, np.nan)
    if a.write_ref_preds:
        for r in ("bag", "bag+graph", "pairwise"):
            pd.DataFrame({"episode_id": b.episode_id, "t": b.t, "p_graph": preds[r]})[rows_a].to_csv(
                os.path.join(a.out, "preds", f"oof_{r.replace('+', '_')}.csv"), index=False, float_format="%.6g")

    log("(a) predictions done")
    rows_common = rows_a & np.all([~np.isnan(preds[n]) for n in preds], 0)
    res_a = {"rows": int(rows_a.sum()), "rows_common": int(rows_common.sum()), "configs": int(b.group_id[rows_a].nunique()),
             "selection": {f"{k[0]}|{k[1]}": {"spec": [x if not isinstance(x, dict) else x for x in v_["spec"]],
                                               "n_cols": len(v_["cols"]), "pool_oof_auprc": v_.get("pool_oof_auprc")}
                           for k, v_ in sel.items()}, "main": {}}
    for n, p in preds.items():
        rr = rows_a & ~np.isnan(p)
        thr = thr_at_fpr(D.y[rr], p[rr])
        cal = None
        if n.startswith(("zs", "ext:")):
            pc = iso_crossfit(D, p, rr)
            m = bin_metrics(D.y[rr], p[rr], thr)
            m["brier"] = float(brier_score_loss(D.y[rr], pc[rr])) if not np.isnan(pc[rr]).any() else None
        else:
            m = bin_metrics(D.y[rr], p[rr], thr, cal)
        if n in per_seed:
            sa = [roc_auc_score(D.y[rr], s[~np.isnan(s)]) for s in per_seed[n]]
            m["auroc_seeds"] = [float(x) for x in sa]
        res_a["main"][n] = m
    ci, diffs, names = bootstrap(D, rows_common, preds, ["pairwise", "bag", "bag+graph"] + [f"ext:{x}" for x in D.ext],
                                 a.boot)
    for n in names:
        res_a["main"][n].update(ci[n])
    res_a["paired_diffs_common_rows"] = diffs
    log("(a) bootstrap done")
    res_a["slices"] = slices(D, rows_common, preds, names)
    res_a["run_level"] = run_level(D, {n: _run_score(D, n, preds) for n in names}, names)
    log("(a) slices + run level done")
    res_a["node"] = {v: node_eval(D, v, rows_a | D.night.values) for v in variants}
    # count (all rows of night runs, incl. after the tip)
    log("(a) node done")
    rows_cnt = D.night.values
    cnt = {}
    for v in variants:
        cnt[f"zs:{v}"] = np.where(rows_cnt, D.var[v].zs_count.values, np.nan)
        rv = rows_cnt & D.var[v].zs_tip.notna().values
        cols = stack_cols(D.var[v], v, "level+delta")
        cnt[f"ridge:{v}"] = _count_oof(D, D.var[v][cols].values, rv, "ridge")
        cnt[f"hgbreg:{v}"] = _count_oof(D, D.var[v][cols].values, rv, "hgb")
    cnt["bag(hgbreg)"] = _count_oof(D, D.ref[fs["bag"]].values, rows_cnt, "hgb")
    res_a["count"] = count_eval(D, rows_cnt, cnt)
    res_a["reliability"] = reliability(D, variants, rows_a)
    json.dump(_clean(res_a), open(os.path.join(a.out, "oof", "results.json"), "w"), indent=1)
    pd.DataFrame({"episode_id": b.episode_id, "t": b.t, **{n: p for n, p in preds.items()}})[rows_a].to_csv(
        os.path.join(a.out, "oof", "preds.csv"), index=False, float_format="%.5g")

    # ---------------- protocol (b): frozen
    log("(a) count + reliability done")
    res_b = frozen(D, a, variants, sel, fs, Xof)
    log("(b) done")
    json.dump(_clean(res_b), open(os.path.join(a.out, "frozen", "results.json"), "w"), indent=1)
    cost = cost_table(D, variants, a)
    json.dump(_clean(cost), open(os.path.join(a.out, "cost.json"), "w"), indent=1)
    from .report import write_report
    write_report(a.out, res_a, res_b, cost, D, preds, variants)
    print(f"wrote {a.out}", flush=True)


def _run_score(D, n, preds):
    """Run-level score: p_tip_end for LLM global variants (zero-shot), else the row score."""
    if n.startswith("zs:"):
        v = n[3:]
        return D.var[v].zs_tip_end.values
    if n.startswith("zs1:"):
        return preds[n]
    p = preds[n].copy()
    return p


def _count_oof(D, X, rows, kind):
    y = D.base.risk_count.values.astype(float)
    idx = np.where(rows)[0]
    out = np.full(len(y), np.nan)
    per = []
    for s in SEEDS:
        p = np.full(len(idx), np.nan)
        for tr, te in folds(D.groups[idx], s):
            if kind == "ridge":
                m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
            else:
                m = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05, random_state=s)
            p[te] = m.fit(X[idx[tr]], y[idx[tr]]).predict(X[idx[te]])
        per.append(p)
    out[idx] = np.clip(np.mean(per, 0), 0, 24)
    return out


def reliability(D, variants, rows):
    out = {}
    for v in variants:
        S = D.var[v]
        r = {}
        if "p_tip_3_sd" in S and S.n_samples.max() > 1:
            r["mean_sd_p_tip_3"] = float(S.p_tip_3_sd[rows].mean())
            m = rows & S.p_tip_3_s0.notna().values & S.p_tip_3.notna().values
            r["auroc_k1"] = float(roc_auc_score(D.y[m], S.p_tip_3_s0.values[m]))
            r["auroc_k3"] = float(roc_auc_score(D.y[m], S.p_tip_3.values[m]))
        out[v] = r
    return out


def frozen(D, a, variants, sel, fs, Xof):
    b = D.base
    yok = ~np.isnan(D.y)
    pool = yok & b.split.isin(POOL).values
    splits = [s for s in HELDOUT if (b.split == s).any()] + sorted(s for s in b.split.unique() if s.startswith("night_vx"))
    out = {"selection": {f"{k[0]}|{k[1]}": v_.get("pool_oof_auprc") for k, v_ in sel.items()}, "splits": {}}
    scores, thr = {}, {}
    # reference models: OOF on pool for thresholds, refit on pool, predict everything
    for r in REFS:
        if r == "edge_monitor":
            p_pool, _, E = edge_oof(D, pool, seeds=(0,))
            keys = b[["episode_id", "t"]]
            mdl = refbase.EdgeMonitor(E, 0).fit(keys[pool].reset_index(drop=True), D.y[pool])
            full = mdl.predict(keys.reset_index(drop=True))
        else:
            X = D.ref[fs[r]].values
            p_pool, _ = oof_fit(D, X, pool, ("ref_hgb", {}), seeds=(0,))
            full = fit_predict(("ref_hgb", {}), X[pool], D.y[pool], X)
        thr[r] = thr_at_fpr(D.y[pool], p_pool[pool])
        scores[r] = full
    cal = {}
    for v in variants:
        zs = D.var[v].zs_tip.values
        m = pool & ~np.isnan(zs)
        scores[f"zs:{v}"] = zs
        thr[f"zs:{v}"] = thr_at_fpr(D.y[m], zs[m])
        cal[f"zs:{v}"] = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(zs[m], D.y[m]).predict
        for head in ("lr", "hgb"):
            s_ = sel[(v, head)]
            X = Xof(v, s_["cols"])
            p_pool, _ = oof_fit(D, X, m, s_["spec"], seeds=(0,))
            thr[f"{head}:{v}"] = thr_at_fpr(D.y[m], p_pool[m])
            full = np.full(len(b), np.nan)
            ok = ~np.isnan(zs)
            full[ok] = fit_predict(s_["spec"], X[m], D.y[m], X[ok])
            scores[f"{head}:{v}"] = full
    for nm, p in D.ext.items():
        m = pool & ~np.isnan(p)
        scores[f"ext:{nm}"] = p
        thr[f"ext:{nm}"] = thr_at_fpr(D.y[m], p[m]) if m.any() else None
    names = list(scores)
    for s in splits:
        rows = yok & (b.split == s).values
        unit = "vx_base" if s.startswith("night_vx") else "group_id"
        res = {n: bin_metrics(D.y[rows], scores[n][rows], thr[n], cal.get(n)) for n in names}
        common = rows & np.all([~np.isnan(scores[n]) for n in names], 0)
        ci, diffs, nn = bootstrap(D, common, scores, ["pairwise", "bag", "bag+graph"] + [f"ext:{x}" for x in D.ext],
                                  a.boot, unit=unit)
        for n in nn:
            res[n].update(ci[n])
        lead = {n: lead_time(D, (b.split == s).values, scores[n], thr[n]) for n in names if thr[n] is not None}
        log(f"(b) split {s}")
        out["splits"][s] = {"metrics": res, "paired_diffs": diffs, "lead_time": lead,
                            "run_level": run_level(D, {n: _run_score(D, n, scores) for n in names}, names, {s}),
                            "node": {v: node_eval(D, v, (b.split == s).values) for v in variants}}
    out["thresholds"] = thr
    out["vx_shift"] = vx_shift(D, scores, names, a.boot) if any(x.startswith("night_vx") for x in splits) else None
    return out


def vx_shift(D, scores, names, n_boot, seed=0):
    """VALIDATION.md 3.4: Delta_shift(M) = M(arm) - M(id rep0) vs Delta_noise(M) = M(id rep1) - M(id rep0),
    pooled over the same bases, paired bootstrap over bases."""
    b = D.base
    yok = ~np.isnan(D.y)
    vx = yok & b.split.str.startswith("night_vx").values
    idr0 = vx & (b.vx_arm == "id").values & (b.rep == "rep0").values
    idr1 = vx & (b.vx_arm == "id").values & (b.rep == "rep1").values
    arms = sorted(set(b.vx_arm[vx]) - {"id", "rep", "nan", ""})
    rng = np.random.default_rng(seed)
    out = {}

    def auc(mask, n):
        y, p = D.y[mask], scores[n][mask]
        ok = ~np.isnan(p)
        return roc_auc_score(y[ok], p[ok]) if 0 < y[ok].sum() < ok.sum() else np.nan

    for arm in arms + ["noise"]:
        am = (vx & (b.vx_arm == arm).values) if arm != "noise" else idr1
        bases = sorted(set(b.vx_base[am]) & set(b.vx_base[idr0]))
        res = {}
        for n in names:
            pt = auc(am & b.vx_base.isin(bases).values, n) - auc(idr0 & b.vx_base.isin(bases).values, n)
            bs = []
            for _ in range(n_boot):
                pick = rng.choice(bases, len(bases), replace=True)
                ma = np.concatenate([np.where(am & (b.vx_base == x).values)[0] for x in pick])
                m0 = np.concatenate([np.where(idr0 & (b.vx_base == x).values)[0] for x in pick])
                mA = np.zeros(len(b), bool)
                m0b = np.zeros(len(b), bool)
                mA[ma], m0b[m0] = True, True
                bs.append(auc(mA, n) - auc(m0b, n))
            bs = np.array(bs)[~np.isnan(bs)]
            res[n] = {"delta_auroc": float(pt), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
                      if len(bs) else None, "n_bases": len(bases)}
        out[arm] = res
    return out


def cost_table(D, variants, a):
    from .aggregate import read_rows
    out = {}
    n_snap = D.base.groupby("episode_id").size().to_dict()
    for v in variants:
        U, lat, calls, runs = [], [], 0, 0
        for d in D.runs:
            rows = read_rows(d, v, a.suffix)
            if not rows:
                continue
            runs += 1
            for r in rows:
                calls += 1
                U.append(r.get("usage") or {})
                lat.append(r.get("latency") or np.nan)
        if not calls:
            continue
        U = pd.DataFrame(U).fillna(0)
        tot_tok = U.sum()
        cost = float(sum(cost_of(u) for u in U.to_dict("records")))
        snaps = sum(n_snap.get(e, 0) for e in set(D.base.episode_id)) if runs == len(D.runs) else runs * 30
        out[v] = {"calls": calls, "runs": runs, "snapshots": int(snaps), "cost_usd": cost,
                  "usd_per_snapshot": cost / snaps, "usd_per_run": cost / runs,
                  "tokens_per_snapshot": float((tot_tok.get("input_tokens", 0) + tot_tok.get("cache_read_input_tokens", 0)
                                                + tot_tok.get("cache_creation_input_tokens", 0)
                                                + tot_tok.get("output_tokens", 0)) / snaps),
                  "input_tokens": int(tot_tok.get("input_tokens", 0)), "output_tokens": int(tot_tok.get("output_tokens", 0)),
                  "cache_read_tokens": int(tot_tok.get("cache_read_input_tokens", 0)),
                  "cache_write_tokens": int(tot_tok.get("cache_creation_input_tokens", 0)),
                  "latency_p50": float(np.nanpercentile(lat, 50)), "latency_p95": float(np.nanpercentile(lat, 95))}
    # GNN feature cost: jury tokens (both judges) on the same runs
    jt = {"claude-haiku-5-5": [0, 0, 0], "deepseek-v4-flash": [0, 0, 0]}
    n_msgs = 0
    for d in D.runs:
        for j in jt:
            p = os.path.join(d, f"jury_{j}.jsonl")
            if not os.path.exists(p):
                continue
            seen = set()           # grouped calls repeat the call's usage on every message row: count each call once
            for line in open(p):
                r = json.loads(line)
                u = r.get("usage") or {}
                key = (r.get("round"), json.dumps(u, sort_keys=True))
                jt[j][2] += 1
                if key in seen:
                    continue
                seen.add(key)
                jt[j][0] += u.get("input_tokens", u.get("prompt_tokens", 0)) or 0
                jt[j][1] += u.get("output_tokens", u.get("completion_tokens", 0)) or 0
        n_msgs += len(load_messages(d))
    snaps = len(D.base)
    out["_gnn_jury"] = {j: {"rows": v_[2], "input_tokens": v_[0], "output_tokens": v_[1],
                            "tokens_per_snapshot": (v_[0] + v_[1]) / snaps,
                            "tokens_per_message": (v_[0] + v_[1]) / max(1, n_msgs)} for j, v_ in jt.items()}
    h = jt["claude-haiku-5-5"]
    out["_gnn_jury"]["haiku_usd_total"] = (h[0] * 0.10 + h[1] * 0.50) / 1e6
    out["_gnn_jury"]["haiku_usd_per_snapshot"] = out["_gnn_jury"]["haiku_usd_total"] / snaps
    out["_gnn_jury"]["note"] = ("jury usage rows may count grouped calls once per message (usage repeated per "
                                "message of a group); DeepSeek is billed by Adaption, tokens only")
    return out


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


if __name__ == "__main__":
    main()
