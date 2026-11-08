"""Pre-registered evaluation of the validation suite night_vx (ANALYSIS_PLAN.md §6). Written before any monitor score
on runs_vx existed; test it only with random or label-leak scores.

Inputs
  --snap      harness snapshot tables (gnn_opt/build_dataset.py), one or more: runs_vx and runs_night (Part B needs the
              night runs of the source configs). Only eval == 1 rows (label defined, branch prefix once) are scored.
  --index     sim_dataset/dataset/index.csv (split, vx_base, vx_arm, deadline_round, rounds per scenario_id)
  --pred      NAME=PATH, repeatable. CSV with (run, round, score) or (episode_id, t, p_graph | zs_tip | score). The file
              must cover every scored row of every block it is used on (checked).
  --thr       NAME=VALUE, repeatable: alarm threshold from TRAINING data (5 % FPR) for the H4 false-alarm check
  --ref       reference predictor for between-monitor differences of the shift (default bag+graph)
  --boot      bootstrap draws (default 2000); --out OUT_PREFIX (writes OUT_PREFIX.json and OUT_PREFIX.md)

Part A (star design, 14 bases): per arm A in {time, glm, enf, topo}, on the bases that have A, id rep0 and id rep1:
  shift = M(A) - M(id rep0), noise = M(id rep1) - M(id rep0), shift_minus_noise = M(A) - M(id rep1)
  for M = AUROC and time-matched AUROC (pairs-weighted within rounds-to-cut bins <=-9, -8..-5, -4..-1, 0..3, >3).
  Bootstrap over bases WITH replacement; one set of draws per arm, shared by all predictors and all parts (a base
  drawn twice counts twice). Also shift(M) - shift(ref) per predictor.
Part B (8 held-out night configs + 2 new replicates each): groups = source config (vx_base of night_vx_rep runs, cfg of
  the night runs). Run-level AUROC within config (score at round cut - 6 of runs not tipped by then; all tipped x
  untipped pairs within a group) and row-level AUROC within group x rounds-to-cut bin. Bootstrap over groups.
  The same run-level within-config AUROC is reported for the id rep0/rep1 pairs of Part A.
Outcome shift per arm: exact McNemar test (tipped arm vs tipped id rep0, paired by base), Holm over the 4 arms.
H4 false alarms: share of untipped runs with at least one row score >= threshold, enf vs id rep0 on the same bases;
  plus row-level FPR on the rows of untipped runs.
H2 censoring check: clock (if given) recomputed without the last 3 rounds of each run.
"""
from __future__ import annotations

import argparse
import json
from math import comb

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ARMS = ["time", "glm", "enf", "topo"]
BINS = [-99, -9, -5, -1, 3, 99]


# ------------------------------------------------------------------------------------------------ loading
def load_snaps(paths, index):
    I = index.set_index("scenario_id")
    out = []
    for p in paths:
        S = pd.read_csv(p, low_memory=False)
        S = S[S["eval"] == 1].copy()
        S["split"] = S.cfg.map(I["split"]).astype(str)
        S["vx_base"] = S.cfg.map(I["vx_base"]).astype(str)
        S["vx_arm"] = S.cfg.map(I["vx_arm"]).astype(str)
        S["deadline"] = S.cfg.map(I["deadline_round"]).astype(float)
        S["R"] = S.cfg.map(I["rounds"]).astype(float)
        S["rtc"] = S["round"] - S["deadline"]
        S["rep"] = S.run.str.split("/").str[-1]
        out.append(S[["run", "round", "cfg", "rep", "split", "vx_base", "vx_arm", "deadline", "R", "rtc", "y3", "tipped"]])
    S = pd.concat(out, ignore_index=True)
    assert not S.duplicated(["run", "round"]).any(), "duplicate (run, round) rows across --snap tables"
    S["y3"] = S["y3"].astype(float)
    return S


def load_pred(path):
    P = pd.read_csv(path)
    if "episode_id" in P.columns:
        P = P.rename(columns={"episode_id": "run", "t": "round"})
    col = next(c for c in ("score", "p_graph", "zs_tip", "p") if c in P.columns)
    if "fold" in P.columns:
        raise SystemExit(f"{path}: has a fold column (CV file); pass the eval/predict file instead")
    P = P[["run", "round", col]].rename(columns={col: "score"})
    assert not P.duplicated(["run", "round"]).any(), f"{path}: duplicate (run, round)"
    return P


def bins(rtc):
    return np.asarray(pd.Series(pd.cut(np.asarray(rtc, float), BINS)).astype(str))


def auroc(y, p):
    return roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan


def tm_auroc(y, p, b):
    num = den = 0.0
    for v in np.unique(b):
        m = b == v
        npos = int(y[m].sum())
        nneg = int(m.sum()) - npos
        if npos and nneg:
            num += npos * nneg * roc_auc_score(y[m], p[m])
            den += npos * nneg
    return num / den if den else np.nan


def ci(v):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [np.nan, np.nan]


def r3(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


# ------------------------------------------------------------------------------------------------ Part A
def part_a(S, preds, ref, n_boot, rng):
    res = {}
    for arm in ARMS:
        A = S[S.vx_arm == arm]
        I0 = S[(S.vx_arm == "id") & (S.rep == "rep0")]
        I1 = S[(S.vx_arm == "id") & (S.rep == "rep1")]
        bases = sorted(set(A.vx_base) & set(I0.vx_base) & set(I1.vx_base))
        if not bases:
            continue
        parts = {"arm": A, "id0": I0, "id1": I1}
        rows = {k: {b: np.where(D.vx_base.values == b)[0] for b in bases} for k, D in parts.items()}
        arr = {k: {"y": D.y3.values, "b": bins(D.rtc.values), **{n: D[n].values for n in preds}} for k, D in parts.items()}

        def metrics(sel):
            out = {}
            for k in parts:
                idx = np.concatenate([rows[k][b] for b in sel])
                y, bb = arr[k]["y"][idx], arr[k]["b"][idx]
                for n in preds:
                    p = arr[k][n][idx]
                    out[(k, n, "auroc")] = auroc(y, p)
                    out[(k, n, "tm_auroc")] = tm_auroc(y, p, bb)
            return out

        full = metrics(bases)
        draws = [metrics(rng.choice(bases, len(bases), replace=True)) for _ in range(n_boot)]
        arm_res = {"bases": len(bases), "rows": {k: int(sum(len(rows[k][b]) for b in bases)) for k in parts},
                   "positives": {k: int(parts[k][parts[k].vx_base.isin(bases)].y3.sum()) for k in parts}, "monitors": {}}
        for n in preds:
            mr = {}
            for m in ("auroc", "tm_auroc"):
                def stat(d, kind, n=n, m=m):
                    a, i0, i1 = d[("arm", n, m)], d[("id0", n, m)], d[("id1", n, m)]
                    return {"shift": a - i0, "noise": i1 - i0, "shift_minus_noise": a - i1}[kind]
                mr[m] = {"arm": r3(full[("arm", n, m)]), "id_rep0": r3(full[("id0", n, m)]), "id_rep1": r3(full[("id1", n, m)])}
                for kind in ("shift", "noise", "shift_minus_noise"):
                    mr[m][kind] = r3(stat(full, kind))
                    mr[m][kind + "_ci"] = [r3(x) for x in ci([stat(d, kind) for d in draws])]
                if ref in preds and n != ref:
                    dd = lambda d: (d[("arm", n, m)] - d[("id0", n, m)]) - (d[("arm", ref, m)] - d[("id0", ref, m)])  # noqa
                    mr[m][f"shift_minus_shift_{ref}"] = r3(dd(full))
                    mr[m][f"shift_minus_shift_{ref}_ci"] = [r3(x) for x in ci([dd(d) for d in draws])]
            arm_res["monitors"][n] = mr
        arm_res["valid_draws_auroc"] = int(np.sum([~np.isnan(d[("arm", list(preds)[0], "auroc")]) for d in draws]))
        res[arm] = arm_res
    return res


# ------------------------------------------------------------------------------------------------ run level
def run_scores(S, preds):
    """Score at round cut - 6 for runs not tipped by then (row exists and label defined at that round)."""
    pre = S[S["round"] == (S.deadline - 6)]
    return pre[["run", "cfg", "group", "tipped"] + list(preds)].drop_duplicates("run")


def within_auc(R, n):
    wins = pairs = 0.0
    for _, g in R.groupby("group"):
        pos, neg = g[g.tipped == 1][n].values, g[g.tipped == 0][n].values
        if len(pos) and len(neg):
            d = pos[:, None] - neg[None, :]
            wins += (d > 0).sum() + 0.5 * (d == 0).sum()
            pairs += d.size
    return (wins / pairs if pairs else np.nan), int(pairs)


def within_rows(D, n):
    """Row-level AUROC within group x rounds-to-cut bin (pairs-weighted)."""
    key = D.group.astype(str) + "|" + bins(D.rtc.values)
    num = den = 0.0
    for _, g in D.groupby(key):
        npos = int(g.y3.sum())
        nneg = len(g) - npos
        if npos and nneg:
            num += npos * nneg * roc_auc_score(g.y3, g[n])
            den += npos * nneg
    return num / den if den else np.nan


def grouped_boot(D, R, preds, n_boot, rng):
    groups = sorted(set(D.group))
    gi = {g: np.where(D.group.values == g)[0] for g in groups}
    gr = {g: np.where(R.group.values == g)[0] for g in groups}
    out = {}
    for n in preds:
        auc, npairs = within_auc(R, n)
        out[n] = {"run_within_auroc": r3(auc), "pairs": npairs, "row_within_auroc": r3(within_rows(D, n))}
    bs = {n: {"run": [], "row": []} for n in preds}
    for _ in range(n_boot):
        sel = rng.choice(groups, len(groups), replace=True)
        # relabel drawn copies as separate groups so a duplicated config is its own stratum
        Db = pd.concat([D.iloc[gi[g]].assign(group=f"{g}#{k}") for k, g in enumerate(sel)], ignore_index=True)
        Rb = pd.concat([R.iloc[gr[g]].assign(group=f"{g}#{k}") for k, g in enumerate(sel)], ignore_index=True)
        for n in preds:
            bs[n]["run"].append(within_auc(Rb, n)[0])
            bs[n]["row"].append(within_rows(Db, n))
    for n in preds:
        out[n]["run_within_auroc_ci"] = [r3(x) for x in ci(bs[n]["run"])]
        out[n]["row_within_auroc_ci"] = [r3(x) for x in ci(bs[n]["row"])]
    return {"groups": len(groups), "runs": int(R.run.nunique()), "monitors": out}


# ------------------------------------------------------------------------------------------------ outcome tests
def mcnemar(S):
    runs = S.drop_duplicates("run")[["run", "vx_base", "vx_arm", "rep", "tipped"]]
    id0 = runs[(runs.vx_arm == "id") & (runs.rep == "rep0")].set_index("vx_base").tipped
    res, ps = {}, []
    for arm in ARMS:
        a = runs[(runs.vx_arm == arm) & (runs.rep == "rep0")].set_index("vx_base").tipped
        common = sorted(set(a.index) & set(id0.index))
        b = int(sum((a[x] == 1) and (id0[x] == 0) for x in common))
        c = int(sum((a[x] == 0) and (id0[x] == 1) for x in common))
        n = b + c
        p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)
        res[arm] = {"bases": len(common), "tipped_arm": int(a[common].sum()), "tipped_id_rep0": int(id0[common].sum()),
                    "arm_only": b, "id_only": c, "p_exact": r3(p)}
        ps.append((arm, p))
    # Holm over the arms
    order = sorted(ps, key=lambda x: x[1])
    m, run_max = len(order), 0.0
    for i, (arm, p) in enumerate(order):
        run_max = max(run_max, min(1.0, (m - i) * p))
        res[arm]["p_holm"] = r3(run_max)
    return res


def false_alarms(S, preds, thr):
    out = {}
    for arm in ("enf", "id"):
        D = S[(S.vx_arm == arm) & (S.rep == "rep0")]
        bases = set(S[(S.vx_arm == "enf")].vx_base) & set(S[(S.vx_arm == "id") & (S.rep == "rep0")].vx_base)
        D = D[D.vx_base.isin(bases)]
        U = D[D.tipped == 0]
        out[arm] = {"untipped_runs": int(U.run.nunique())}
        for n, t in thr.items():
            if n not in preds:
                continue
            alarm = U.groupby("run")[n].max() >= t
            out[arm][n] = {"false_alarm_run_share": r3(alarm.mean()) if len(alarm) else None,
                           "row_fpr_untipped": r3((U[n] >= t).mean()) if len(U) else None}
    return out


# ------------------------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snap", nargs="+", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--pred", action="append", required=True, help="NAME=PATH")
    ap.add_argument("--thr", action="append", default=[], help="NAME=VALUE")
    ap.add_argument("--ref", default="bag+graph")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    S = load_snaps(a.snap, pd.read_csv(a.index, low_memory=False))
    preds = {}
    for spec in a.pred:
        n, p = spec.split("=", 1)
        P = load_pred(p).rename(columns={"score": n})
        S = S.merge(P, on=["run", "round"], how="left")
        preds[n] = p
    thr = {s.split("=", 1)[0]: float(s.split("=", 1)[1]) for s in a.thr}

    vx = S[S.split.str.startswith("night_vx") & ~S.split.isin(["night_vx_ft", "night_vx_ft_base", "night_vx_pop_bal"])].copy()
    src = set(S[S.split == "night_vx_rep"].vx_base)
    partb = S[(S.split == "night_vx_rep") | S.cfg.isin(src)].copy()
    partb["group"] = np.where(partb.split == "night_vx_rep", partb.vx_base, partb.cfg)
    for name, D in (("night_vx", vx), ("part B", partb)):
        miss = {n: int(D[n].isna().sum()) for n in preds}
        if any(miss.values()):
            raise SystemExit(f"{name}: rows without a score per predictor: {miss}")

    res = {"note": "ANALYSIS_PLAN.md §6; bootstrap over bases (Part A) / source configs (Part B), with replacement",
           "boot": a.boot, "seed": a.seed, "predictors": preds, "thresholds": thr,
           "rows": {"night_vx": int(len(vx)), "night_vx_positives": int(vx.y3.sum()), "part_b": int(len(partb))}}
    res["part_a"] = part_a(vx, preds, a.ref, a.boot, rng)
    idpairs = vx[vx.vx_arm == "id"].copy()
    idpairs["group"] = idpairs.vx_base
    res["id_pairs_within"] = grouped_boot(idpairs, run_scores(idpairs, preds), preds, a.boot, rng)
    res["part_b"] = grouped_boot(partb, run_scores(partb, preds), preds, a.boot, rng)
    res["outcome_mcnemar"] = mcnemar(vx)
    res["h4_false_alarms"] = false_alarms(vx, preds, thr)
    if "clock" in preds:
        T = vx[vx["round"] <= vx.R - 3]
        res["h2_clock_without_last3"] = part_a(T, {"clock": preds["clock"]}, "none", a.boot, rng).get("time")
    json.dump(res, open(a.out + ".json", "w"), indent=1)

    L = [f"# night_vx evaluation ({a.boot} draws)", "", f"Rows: {res['rows']}", ""]
    for arm, r in res["part_a"].items():
        L += [f"## {arm} ({r['bases']} bases; rows {r['rows']}; positives {r['positives']})", "",
              "| monitor | metric | arm | id rep0 | id rep1 | shift [CI] | noise [CI] | shift − noise [CI] | shift − shift(ref) [CI] |",
              "|---|---|---|---|---|---|---|---|---|"]
        for n, mr in r["monitors"].items():
            for m, v in mr.items():
                s = lambda k: f"{v[k]} [{v[k + '_ci'][0]}, {v[k + '_ci'][1]}]" if v.get(k) is not None else "–"  # noqa
                L.append(f"| {n} | {m} | {v['arm']} | {v['id_rep0']} | {v['id_rep1']} | {s('shift')} | {s('noise')} | "
                         f"{s('shift_minus_noise')} | {s(f'shift_minus_shift_{a.ref}') if f'shift_minus_shift_{a.ref}' in v else '–'} |")
        L.append("")
    for key in ("id_pairs_within", "part_b"):
        r = res[key]
        L += [f"## {key} ({r['groups']} groups, {r['runs']} runs)", "", "| monitor | run-level within config [CI] | pairs | row-level within config × bin [CI] |", "|---|---|---|---|"]
        for n, v in r["monitors"].items():
            L.append(f"| {n} | {v['run_within_auroc']} {v['run_within_auroc_ci']} | {v['pairs']} | {v['row_within_auroc']} {v['row_within_auroc_ci']} |")
        L.append("")
    L += ["## Outcome shift (exact McNemar vs id rep0, Holm over 4 arms)", "", "```", json.dumps(res["outcome_mcnemar"], indent=1), "```",
          "", "## H4 false alarms", "", "```", json.dumps(res["h4_false_alarms"], indent=1), "```"]
    open(a.out + ".md", "w").write("\n".join(L) + "\n")
    print("wrote", a.out + ".json", a.out + ".md")


if __name__ == "__main__":
    main()
