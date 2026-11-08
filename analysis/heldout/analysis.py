"""Primary held-out comparison on identical rows (ANALYSIS_PLAN.md §4 / §4b), GNN harness rows.

  python -I -B heldout/scripts/analysis.py            -> heldout/out/results.json + CSV tables + analysis.log

Rows: harness snapshots.csv, eval == 1 (y3 defined, branch prefixes once), split in the 4 held-out splits.
Inference: paired cluster bootstrap over configs (B = 10,000, identical draws for all predictors), exact via
per-config pair-count matrices (hlib). p = 2 min(P(d <= 0), P(d >= 0)), floored at 1/B; Holm over the 11 primary
tests. Row-level DeLong only as a labelled anti-conservative contrast.
"""
from __future__ import annotations

import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402

import hlib as L  # noqa: E402
import evaluate as EV  # noqa: E402  (harness evaluate.py: lead_time)

T0 = time.time()
OUT = f"{L.HO_DIR}/out"
os.makedirs(OUT, exist_ok=True)
B = 10_000
SEED = 20261108
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


# ===================================================================================== 1. rows and predictors
S, lab = L.load_snapshots()
R = lab[lab.split.isin(L.HO)].reset_index(drop=True)
y = R.y.values.astype(int)
n = len(R)
cfgs = np.array(sorted(R.cfg.unique()))
C = len(cfgs)
cix = {c: i for i, c in enumerate(cfgs)}
g = R.cfg.map(cix).values
log(f"held-out rows {n}, positives {y.sum()}, prevalence {y.mean():.4f}, configs {C}, runs {R.run.nunique()}")
assert n == 2338 and y.sum() == 156, "does not match the GNN team's 2338 / 156"

res = {"meta": {"B": B, "seed": SEED, "n_rows": int(n), "n_pos": int(y.sum()), "n_cfgs": int(C),
                "n_runs": int(R.run.nunique())}}
# per split counts
runs = R.groupby("run").agg(cfg=("cfg", "first"), split=("split", "first"), tipped=("tipped", "first"),
                            tip_round=("tip_round", "first"), arm=("arm", "first"))
split_rows = {}
for sp in L.HO + ["pooled"]:
    m = np.ones(n, bool) if sp == "pooled" else (R.split == sp).values
    rr = runs if sp == "pooled" else runs[runs.split == sp]
    split_rows[L.SHORT.get(sp, sp)] = {
        "rows": int(m.sum()), "pos": int(y[m].sum()), "prev": float(y[m].mean()), "cfgs": int(R.cfg[m].nunique()),
        "runs": int(len(rr)), "tipped_runs": int(rr.tipped.sum()), "cfgs_with_pos": int(R[m & (y == 1)].cfg.nunique()),
        "excluded_branch_prefix_rows_eval0_labelled": int(((S["eval"] == 0) & S.y3.notna() & (
            S.split.isin(L.HO) if sp == "pooled" else (S.split == sp))).sum())}
res["rows"] = split_rows
log("rows per split:", json.dumps(split_rows))

# mixed configs (task definition: held-out runs of the config include tipped and untipped ones)
mix_cfg = runs.groupby("cfg").tipped.agg(lambda v: (v.max() == 1) and (v.min() == 0))
mixed_cfgs = sorted(mix_cfg[mix_cfg].index)
schema = json.load(open(f"{L.DATA}/schema.json"))
harness_mixed_ho = sorted(set(schema["mixed_cfgs"]) & set(cfgs))
llm_mixed_ho = sorted(R[R.mixed_llm == 1].cfg.unique())
res["mixed"] = {"n_mixed_cfgs": len(mixed_cfgs), "mixed_cfgs": mixed_cfgs,
                "per_split": {L.SHORT[s]: int(sum(c.startswith(f"core-{s}-") for c in mixed_cfgs)) for s in L.HO},
                "n_rows": int(R.cfg.isin(mixed_cfgs).sum()), "n_pos": int(y[R.cfg.isin(mixed_cfgs).values].sum()),
                "harness_schema_mixed_in_heldout": harness_mixed_ho, "llm_base_mixed_in_heldout": llm_mixed_ho}
log(f"mixed configs (held-out runs tipped and untipped): {len(mixed_cfgs)} -> {res['mixed']['per_split']}; "
    f"harness schema (control arms only): {len(harness_mixed_ho)}; llm _base: {len(llm_mixed_ho)}")

# predictors
scores, cover = {}, {}
for name, (src, _) in {**L.PREDICTORS, **L.SENS}.items():
    P = L.read_pred(src)
    s, miss, nan = L.attach(R, P)
    cover[name] = {"source": src if isinstance(src, str) else f"{L.LLM}/{src[1]}/snapshots.csv:zs_tip",
                   "file_rows": int(len(P)), "missing": miss, "nan": nan, "distinct_values": int(len(np.unique(s[~np.isnan(s)])))}
    scores[name] = s
    log(f"  {name:20s} missing {miss}  NaN {nan}  distinct {cover[name]['distinct_values']}  <- {cover[name]['source']}")
assert all(v["missing"] == 0 and v["nan"] == 0 for v in cover.values()), "a predictor does not cover every row"
# exploratory combination: mean of ranks (no fitting, label-free; ranks over the held-out rows)
scores["comb:pairwise+hybrid"] = (stats.rankdata(scores["zs:pairwise"]) + stats.rankdata(scores["hybrid"])) / (2 * n)
res["coverage"] = cover
MAIN = list(L.PREDICTORS) + ["comb:pairwise+hybrid"]
ALL = MAIN + list(L.SENS)

# ===================================================================================== 2. thresholds
thr = {}
for name, (_, spec) in {**L.PREDICTORS, **L.SENS}.items():
    thr[name] = L.threshold(name, spec, lab)
res["thresholds"] = thr
for k, v in thr.items():
    log(f"  thr {k:20s} {v['thr']:.6g}  from {v['src']}  (n={v['n_rows']}, train FPR {v['train_fpr']:.4f})")

# ===================================================================================== 3. statistic matrices
rtc = R.rtc_bin.values
rb = R.round_bin.values
mixed_m = R.cfg.isin(mixed_cfgs).values
preann_m = (R.before_announce == 1).values
strata_mixed = (R.cfg + "|" + R.rtc_bin).values
mats = {}
for name in ALL:
    s = scores[name]
    mats[name] = {
        "pooled": L.pair_mats(y, s, g, np.zeros(n, int), C),
        "tm_plan": L.pair_mats(y, s, g, rtc, C),
        "tm_harness": L.pair_mats(y, s, g, rb, C),
        "mixed": L.pair_mats(y[mixed_m], s[mixed_m], g[mixed_m], strata_mixed[mixed_m], C),
        "preann": L.pair_mats(y[preann_m], s[preann_m], g[preann_m], np.zeros(preann_m.sum(), int), C)}
STAT = {"pooled": L.stat_pooled, "tm_plan": L.stat_pairs, "tm_harness": L.stat_posw, "mixed": L.stat_pairs,
        "preann": L.stat_pooled}


def stat(name, key, K):
    return STAT[key](K, mats[name][key])


# full-sample checks against sklearn / harness / llm_monitor implementations
one = np.ones((1, C))
chk = {}
for name in ALL:
    s = scores[name]
    ref = {"pooled": roc_auc_score(y, s), "tm_plan": L.stratified_auroc(y, s, rtc),
           "tm_harness": L.MH.time_matched_auroc(y, s, R["round"].values),
           "mixed": L.stratified_auroc(y[mixed_m], s[mixed_m], strata_mixed[mixed_m]),
           "preann": roc_auc_score(y[preann_m], s[preann_m])}
    chk[name] = max(abs(stat(name, k, one)[0] - v) for k, v in ref.items())
log(f"engine vs sklearn/harness/llm_monitor on the full sample: max |diff| {max(chk.values()):.2e}")
assert max(chk.values()) < 1e-10

# bootstrap draws (identical for all predictors)
K = L.draws(C, B, SEED)
K_strat = L.draws(C, B, SEED + 1, strata_groups=[np.array([cix[c] for c in cfgs if R[R.cfg == c].split.iloc[0] == sp])
                                                  for sp in L.HO])
split_of_cfg = R.groupby("cfg").split.first().reindex(cfgs).values
ood_idx = np.where(np.isin(split_of_cfg, ["night_test_ood_family", "night_test_ood_seed", "night_branch"]))[0]
tid_idx = np.where(split_of_cfg == "night_test_id")[0]
K_ood = L.draws(C, B, SEED + 2, members=ood_idx)
K_tid = L.draws(C, B, SEED + 3, members=tid_idx)
SPLITK = {L.SHORT[sp]: (split_of_cfg == sp).astype(float)[None, :] for sp in L.HO}
OODK = np.isin(np.arange(C), ood_idx).astype(float)[None, :]
TIDK = np.isin(np.arange(C), tid_idx).astype(float)[None, :]

# explicit-resample check of the engine (3 draws, materialised rows)
rng = np.random.default_rng(1)
mx = 0.0
for _ in range(3):
    pick = rng.integers(0, C, C)
    k = np.bincount(pick, minlength=C).astype(float)[None, :]
    rows = np.concatenate([np.where(g == c)[0] for c in pick])
    for name in ["hybrid", "zs:pairwise", "clock"]:
        s = scores[name]
        yy, ss = y[rows], s[rows]
        mx = max(mx, abs(stat(name, "pooled", k)[0] - roc_auc_score(yy, ss)),
                 abs(stat(name, "tm_plan", k)[0] - L.stratified_auroc(yy, ss, rtc[rows])),
                 abs(stat(name, "tm_harness", k)[0] - L.MH.time_matched_auroc(yy, ss, R["round"].values[rows])),
                 abs(stat(name, "mixed", k)[0] - L.stratified_auroc(yy[mixed_m[rows]], ss[mixed_m[rows]],
                                                                   strata_mixed[rows][mixed_m[rows]])),
                 abs(L.ap_weighted_batch(y, s, k[:, g])[0] - average_precision_score(yy, ss)))
log(f"engine vs materialised resamples (AUROC, both time-matched, mixed, AUPRC): max |diff| {mx:.2e}")
assert mx < 1e-10
res["engine_checks"] = {"full_sample_max_abs_diff": float(max(chk.values())), "resample_max_abs_diff": float(mx)}

# ===================================================================================== 4. reproduce the GNN team
# (a) their published numbers (RESULTS.md step 9)
pub = {"hybrid": [0.832, 0.922, 0.823, 0.785, 0.728], "gnn5": [0.817, 0.921, 0.794, 0.744, 0.731],
       "tab_mem": [0.811, 0.895, 0.807, 0.780, 0.699], "edge": [0.800, 0.837, 0.812, 0.780, 0.728]}
pub_ci = {"hybrid": (0.782, 0.885), "gnn5": (0.756, 0.877), "tab_mem": (0.760, 0.861), "edge": (0.757, 0.847)}
pub_other = {"hybrid": (0.301, 0.752, 0.372), "gnn5": (0.309, 0.739, 0.417), "tab_mem": (0.252, 0.718, 0.250),
             "edge": (0.211, 0.682, 0.288)}
pub_lead = {"hybrid": (0.54, 5.5, 0.31), "gnn5": (0.54, 5.0, 0.29), "tab_mem": (0.52, 5.0, 0.29),
            "edge": (0.56, 4.0, 0.29)}
rep = {}
# harness bootstrap draws (seed 0, 1000, rng.choice over cfgs in order of appearance) reproduced exactly
order = pd.unique(R.cfg.values)
rng0 = np.random.default_rng(0)
K0 = np.zeros((1000, C))
for i in range(1000):
    for c in rng0.choice(order, len(order)):
        K0[i, cix[c]] += 1
for name in pub:
    s = scores[name]
    mine = [roc_auc_score(y, s)] + [roc_auc_score(y[R.split.values == sp], s[R.split.values == sp]) for sp in L.HO]
    a0 = stat(name, "pooled", K0)
    q = np.quantile(a0[~np.isnan(a0)], [0.025, 0.975])
    t = thr[name]["thr"]
    lt = EV.lead_time(R, s, t)
    rep[name] = {"pooled_and_splits_mine": mine, "published": pub[name],
                 "max_abs_diff_3dp": float(max(abs(round(a, 3) - b) for a, b in zip(mine, pub[name]))),
                 "ci_seed0_B1000": [float(q[0]), float(q[1])], "ci_published": pub_ci[name],
                 "auprc_tauroc_r5_mine": [average_precision_score(y, s), L.MH.time_matched_auroc(y, s, R["round"].values),
                                          float((s[y == 1] > t).mean())], "auprc_tauroc_r5_published": pub_other[name],
                 "lead_mine": [lt["alarmed_before_tip"], lt["median_lead"], lt["false_alarm_runs"]],
                 "lead_published": pub_lead[name]}
    log(f"  repro {name:8s} pooled+splits {np.round(mine, 3).tolist()} vs {pub[name]}; CI(seed0,1000) "
        f"[{q[0]:.3f}, {q[1]:.3f}] vs {pub_ci[name]}; AUPRC/tAUROC/R@5 {np.round(rep[name]['auprc_tauroc_r5_mine'], 3).tolist()} "
        f"vs {pub_other[name]}; lead {np.round(rep[name]['lead_mine'], 3).tolist()} vs {pub_lead[name]}")
# their pair differences (base = hybrid, same draws)
for other, pubv in [("gnn5", (-0.007, 0.016, 0.041)), ("tab_mem", (-0.006, 0.021, 0.051)), ("edge", (-0.011, 0.032, 0.078))]:
    d = stat("hybrid", "pooled", K0) - stat(other, "pooled", K0)
    q = np.quantile(d, [0.025, 0.5, 0.975])
    rep[f"hybrid-{other}"] = {"mine_q": q.tolist(), "share_gt0": float((d > 0).mean()), "published": pubv}
    log(f"  repro hybrid-{other}: {np.round(q, 3).tolist()} share>0 {(d > 0).mean():.3f} vs published {pubv}")
# (b) the harness evaluate.py output written by the same run of their code (out/harness_repro_y3.csv)
hp = pd.read_csv(f"{OUT}/harness_repro_y3.csv")
nm = {"hybrid": "hybrid", "gnn5": "gnn5", "hgb": "tab_mem", "edge_top3": "edge"}
mxd = 0.0
for _, r in hp.iterrows():
    nme = nm[r.model]
    m = np.ones(n, bool) if r.split == "pooled" else (R.split == r.split).values
    s = scores[nme]
    t = thr[nme]["thr"]
    mine = [roc_auc_score(y[m], s[m]), average_precision_score(y[m], s[m]),
            L.MH.time_matched_auroc(y[m], s[m], R["round"].values[m]), float((s[m][y[m] == 1] > t).mean())]
    mxd = max(mxd, *[abs(a - b) for a, b in zip(mine, [r.AUROC, r.AUPRC, r.tAUROC, r["R@5%FPR"]])])
rep["max_abs_diff_vs_harness_evaluate_py"] = float(mxd)
log(f"  my AUROC/AUPRC/tAUROC/R@5%FPR vs harness evaluate.py (pooled + 4 splits, 4 models): max |diff| {mxd:.2e}")
res["reproduction"] = rep

# ===================================================================================== 5. per-predictor table
table = {}
APB = {}
for name in ALL:
    s = scores[name]
    ap_draws = np.concatenate([L.ap_weighted_batch(y, s, K[i:i + 500][:, g]) for i in range(0, B, 500)])
    APB[name] = ap_draws
    row = {}
    for key in ["pooled", "tm_plan", "tm_harness", "mixed", "preann"]:
        v = stat(name, key, K)
        row[key] = {"est": float(stat(name, key, one)[0]), "ci": L.ci(v), "n_valid": int((~np.isnan(v)).sum())}
    row["auprc"] = {"est": float(average_precision_score(y, s)), "ci": L.ci(ap_draws), "prev": float(y.mean())}
    row["brier_raw"] = float(np.mean((s - y) ** 2)) if name not in ("comb:pairwise+hybrid",) else None
    for sp in L.HO:
        m = (R.split == sp).values
        ks = SPLITK[L.SHORT[sp]]
        row[L.SHORT[sp]] = {"auroc": float(roc_auc_score(y[m], s[m])), "tm_plan": float(stat(name, "tm_plan", ks)[0]),
                            "tm_harness": float(stat(name, "tm_harness", ks)[0]),
                            "auprc": float(average_precision_score(y[m], s[m])), "prev": float(y[m].mean())}
    row["ood_pooled"] = {"auroc": float(stat(name, "pooled", OODK)[0]), "tm_plan": float(stat(name, "tm_plan", OODK)[0])}
    if name in thr:
        t = thr[name]["thr"]
        row["r5"] = {"thr": t, "recall": float((s[y == 1] > t).mean()), "fpr_heldout": float((s[y == 0] > t).mean()),
                     "per_split_recall": {L.SHORT[sp]: float((s[(R.split == sp).values & (y == 1)] > t).mean()) for sp in L.HO}}
        lt = EV.lead_time(R, s, t)
        # IQR of leads among alarmed tipped runs (same definition as harness lead_time)
        leads = []
        for run, gg in R.assign(s=s).groupby("run"):
            if gg.tipped.iloc[0] == 1 and gg.tip_round.notna().iloc[0]:
                al = gg[gg.s > t]["round"]
                pre = al[al < gg.tip_round.iloc[0]]
                if len(pre):
                    leads.append(gg.tip_round.iloc[0] - pre.min())
        lt["lead_iqr"] = [float(np.percentile(leads, 25)), float(np.percentile(leads, 75))] if leads else None
        lt["n_alarmed_before_tip"] = len(leads)
        lt["n_untipped_false_alarm"] = int(round(lt["false_alarm_runs"] * lt["untipped_runs"]))
        row["lead"] = {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in lt.items()}
    table[name] = row
    log(f"  {name:20s} AUROC {row['pooled']['est']:.3f} [{row['pooled']['ci'][0]:.3f},{row['pooled']['ci'][1]:.3f}]  "
        f"tm_plan {row['tm_plan']['est']:.3f}  tm_harness {row['tm_harness']['est']:.3f}  mixed {row['mixed']['est']:.3f}  "
        f"AUPRC {row['auprc']['est']:.3f}  " + "  ".join(f"{L.SHORT[sp]} {row[L.SHORT[sp]]['auroc']:.3f}" for sp in L.HO)
        + (f"  R@5 {row['r5']['recall']:.3f} (FPR {row['r5']['fpr_heldout']:.3f})" if "r5" in row else ""))
res["table"] = table

# ===================================================================================== 6. comparisons
def compare(a, b, key, Kb=K, Kfull=one, signs=True, strat=None, delong=True, extra_K=None):
    d = stat(a, key, Kb) - stat(b, key, Kb)
    est = float(stat(a, key, Kfull)[0] - stat(b, key, Kfull)[0])
    out = {"a": a, "b": b, "metric": key, "est": est, "ci": L.ci(d), "p": L.pval(d), "n_valid": int((~np.isnan(d)).sum()),
           "share_gt0": float((d[~np.isnan(d)] > 0).mean())}
    if signs:
        sg = {}
        for sp, ks in SPLITK.items():
            v = float(stat(a, key, ks)[0] - stat(b, key, ks)[0])
            sg[sp] = v
        out["split_diffs"] = sg
        ps = np.sign(est)
        out["n_agree"] = int(sum(np.sign(v) == ps for v in sg.values()))
    if delong:
        if key == "pooled":
            out["delong_p"] = L.delong_diff(y, scores[a], scores[b])[1]
        elif key == "tm_plan":
            out["delong_p"] = L.delong_diff(y, scores[a], scores[b], strata=rtc)[1]
    if extra_K is not None:
        for lab_, KK in extra_K.items():
            dd = stat(a, key, KK) - stat(b, key, KK)
            out[f"p_{lab_}"] = L.pval(dd)
            out[f"ci_{lab_}"] = L.ci(dd)
    return out


PRIMARY = [("bag+graph", "clock", "tm_plan"), ("zs:pairwise", "clock", "tm_plan"), ("zs:global_full", "clock", "tm_plan"),
           ("gnn5", "clock", "tm_plan"), ("hybrid", "clock", "tm_plan"),
           ("gnn5", "bag+graph", "pooled"), ("hybrid", "bag+graph", "pooled"), ("zs:pairwise", "bag+graph", "pooled"),
           ("zs:pairwise", "gnn5", "pooled"), ("zs:pairwise", "hybrid", "pooled"), ("zs:global_full", "bag+graph", "pooled")]
prim = [compare(a, b, k, extra_K={"split_stratified": K_strat}) for a, b, k in PRIMARY]
adj = L.holm([c["p"] for c in prim])
for c, h in zip(prim, adj):
    c["p_holm"] = float(h)
    sig = h < 0.05
    if sig and c["n_agree"] >= 3:
        c["verdict"] = f"real: Holm p < 0.05 and sign in {c['n_agree']}/4 splits"
    elif sig:
        c["verdict"] = f"tie by plan rule: Holm p < 0.05 but sign in only {c['n_agree']}/4 splits"
    else:
        c["verdict"] = f"tie (gleichauf): Holm p = {h:.3f} >= 0.05" + (f"; sign in {c['n_agree']}/4 splits")
    # sensitivity for (a): harness tAUROC instead of the plan bins
    if c["metric"] == "tm_plan":
        s2 = compare(c["a"], c["b"], "tm_harness", delong=False)
        c["sens_tm_harness"] = {k: s2[k] for k in ("est", "ci", "p", "n_agree", "split_diffs")}
res["primary"] = prim
log("PRIMARY")
for c in prim:
    log(f"  {c['a']:>15s} - {c['b']:<10s} {c['metric']:8s} {c['est']:+.3f} [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] "
        f"p {c['p']:.4f} Holm {c['p_holm']:.4f} | strat-boot p {c['p_split_stratified']:.4f} | DeLong p {c['delong_p']:.2g} | "
        f"splits " + " ".join(f"{k}:{v:+.3f}" for k, v in c["split_diffs"].items()) + f" -> {c['n_agree']}/4 | {c['verdict']}")

# ----- secondary (uncorrected)
SEC = []


def sec(a, b, key, label, Kb=K, Kfull=one, signs=True):
    c = compare(a, b, key, Kb=Kb, Kfull=Kfull, signs=signs, delong=(Kb is K))
    c["label"] = label
    SEC.append(c)
    return c


for a in ["gnn5", "hybrid", "zs:pairwise"]:
    sec(a, "tab_mem", "pooled", "post hoc: tab_mem (hgb_bag+graph+mem) in place of bag+graph")
sec("tab_mem", "clock", "tm_plan", "post hoc: tab_mem vs clock, time-matched (not in the family)")
for b in ["zs:pairwise", "hybrid"]:
    sec("zs:agent", b, "pooled", "post hoc: zs:agent (agent-level LLM variant, not in the main set)")
    sec("zs:agent", b, "tm_plan", "post hoc: zs:agent, time-matched")
sec("zs:pairwise", "zs:global_full", "pooled", "secondary (RQ3, not in the Holm family)")
sec("zs:pairwise", "zs:global_full", "tm_plan", "secondary (RQ3), time-matched")
for a, b, k in PRIMARY:
    sec(a, b, k, "secondary: primary difference on the OOD splits pooled (ood_family+ood_seed+branch; 24 configs)",
        Kb=K_ood, Kfull=OODK, signs=False)
for a, b, k in PRIMARY:
    sec(a, b, k, "secondary: primary difference on test_id alone (12 configs)", Kb=K_tid, Kfull=TIDK, signs=False)
for b in ["zs:pairwise", "hybrid"]:
    sec("comb:pairwise+hybrid", b, "pooled", "exploratory, post hoc: mean-of-ranks combination, no fitting")
    sec("comb:pairwise+hybrid", b, "tm_plan", "exploratory, post hoc: combination, time-matched")
for a in ["edge", "zs:global_window", "zs:agent", "oracle"]:
    sec(a, "clock", "tm_plan", "extra: other predictors vs clock, time-matched (not in the family)")
sec("tab_mem(refit here)", "tab_mem", "pooled", "check: refit noise (same tab_mem model refit in this environment)")
sec("bag+graph", "tab_mem", "pooled", "context: bag+graph vs tab_mem (memory features)")
res["secondary"] = SEC
log("SECONDARY")
for c in SEC:
    extra = (" splits " + " ".join(f"{k}:{v:+.3f}" for k, v in c["split_diffs"].items()) + f" -> {c['n_agree']}/4") \
        if "split_diffs" in c else ""
    log(f"  [{c['label'][:40]:40s}] {c['a']:>20s} - {c['b']:<14s} {c['metric']:8s} {c['est']:+.3f} "
        f"[{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] p {c['p']:.4f} (valid draws {c['n_valid']}){extra}")

# AUPRC differences for the (b) pairs (descriptive)
apd = {}
for a, b, k in PRIMARY:
    if k == "pooled":
        d = APB[a] - APB[b]
        apd[f"{a} - {b}"] = {"est": table[a]["auprc"]["est"] - table[b]["auprc"]["est"], "ci": L.ci(d), "p": L.pval(d)}
res["auprc_diffs"] = apd

# config-level dependence diagnostic: bootstrap SE vs DeLong SE for the pooled (b) differences
dep = {}
for a, b, k in PRIMARY:
    if k != "pooled":
        continue
    d = stat(a, k, K) - stat(b, k, K)
    aucs, cov = L.delong_cov(y, np.vstack([scores[a], scores[b]]))
    se_dl = float(np.sqrt(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]))
    dep[f"{a} - {b}"] = {"se_boot": float(np.nanstd(d)), "se_delong": se_dl, "ratio": float(np.nanstd(d) / se_dl)}
res["se_ratio"] = dep
log("SE ratio cluster bootstrap / DeLong:", {k: round(v["ratio"], 2) for k, v in dep.items()})

res["runtime_s"] = time.time() - T0
json.dump(res, open(f"{OUT}/results.json", "w"), indent=1, default=float)
open(f"{OUT}/analysis.log", "w").write("\n".join(LOG) + "\n")

# flat CSVs
rows = []
for name in ALL:
    r = table[name]
    rows.append({"predictor": name, "AUROC": r["pooled"]["est"], "AUROC_lo": r["pooled"]["ci"][0], "AUROC_hi": r["pooled"]["ci"][1],
                 "AUPRC": r["auprc"]["est"], "AUPRC_lo": r["auprc"]["ci"][0], "AUPRC_hi": r["auprc"]["ci"][1], "prev": r["auprc"]["prev"],
                 "tm_plan": r["tm_plan"]["est"], "tm_plan_lo": r["tm_plan"]["ci"][0], "tm_plan_hi": r["tm_plan"]["ci"][1],
                 "tm_harness": r["tm_harness"]["est"], "tm_harness_lo": r["tm_harness"]["ci"][0], "tm_harness_hi": r["tm_harness"]["ci"][1],
                 **{f"AUROC_{L.SHORT[sp]}": r[L.SHORT[sp]]["auroc"] for sp in L.HO},
                 **{f"tm_plan_{L.SHORT[sp]}": r[L.SHORT[sp]]["tm_plan"] for sp in L.HO},
                 "AUROC_ood_pooled": r["ood_pooled"]["auroc"],
                 "within_mixed": r["mixed"]["est"], "within_mixed_lo": r["mixed"]["ci"][0], "within_mixed_hi": r["mixed"]["ci"][1],
                 "before_announce": r["preann"]["est"], "brier_raw": r["brier_raw"],
                 "R@5%FPR": r.get("r5", {}).get("recall"), "FPR_heldout@thr": r.get("r5", {}).get("fpr_heldout"),
                 "thr": r.get("r5", {}).get("thr"),
                 "lead_alarmed_before_tip": r.get("lead", {}).get("alarmed_before_tip"),
                 "lead_median": r.get("lead", {}).get("median_lead"),
                 "false_alarm_untipped": r.get("lead", {}).get("false_alarm_runs")})
pd.DataFrame(rows).to_csv(f"{OUT}/table_predictors.csv", index=False)
pd.DataFrame([{k: (json.dumps(v) if isinstance(v, (dict, list, tuple)) else v) for k, v in c.items()} for c in prim]).to_csv(
    f"{OUT}/table_primary.csv", index=False)
pd.DataFrame([{k: (json.dumps(v) if isinstance(v, (dict, list, tuple)) else v) for k, v in c.items()} for c in SEC]).to_csv(
    f"{OUT}/table_secondary.csv", index=False)
log(f"done in {time.time() - T0:.1f}s")
