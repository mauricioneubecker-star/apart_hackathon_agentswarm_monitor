"""Pre-registered confirmatory test on fresh replicates (ANALYSIS_PLAN.md Nachtrag 3). Written before any episode of
runs_vx3 existed; tested only with random scores.

Rows   eval == 1 rows of the harness snapshot table of runs_vx3 (rep2 and rep3 of the 14 night_vx_id configs), label y3.
H7     D = AUROC(zs:global_full) - AUROC(gnn) on all rows of rep2 + rep3. Paired bootstrap over the bases (vx_base) with
       replacement: a drawn base brings the rows of its new runs, both monitors are scored on the same draws. 10,000
       draws, seed 20261109, percentile 95 % CI; draws without both classes are dropped. H7 is supported if the lower CI
       bound is above 0. The only test of Nachtrag 3, no correction.
Second CIs from the same draws, no decision rule: (a) the same difference time-matched (tm_auroc, bins as vx_eval.py),
       (b) zs:global_full - hybrid, (c) zs:pairwise - gnn.
Descr. AUROC and time-matched AUROC of every predictor (all rows with CIs from the same draws, and per replicate);
       replicate spread over rep0-rep3 (rep0 / rep1 points read from vx_eval.json, part_a.time = all 14 bases, not
       recomputed); tipped runs and tip rounds per replicate (rep0 / rep1 from the frozen runs_vx snapshot table).

  python analysis/vx3_eval.py --snap <runs_vx3 snapshots.csv> --index sim_dataset/dataset/index.csv \
      --pred NAME=PATH ... --vx-eval analysis/results/vx_eval.json --vx-snap <runs_vx snapshots.csv> \
      --boot 10000 --seed 20261109 --out analysis/results/vx3_eval
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vx_eval import auroc, bins, ci, load_pred, r3, tm_auroc  # noqa: E402  (unchanged since 4e6e998)

CONTRASTS = {  # name -> (monitor a, monitor b, metric); D = a - b
    "H7": ("zs:global_full", "gnn", "auroc"),
    "sec_a_time_matched": ("zs:global_full", "gnn", "tm_auroc"),
    "sec_b_vs_hybrid": ("zs:global_full", "hybrid", "auroc"),
    "sec_c_pairwise_vs_gnn": ("zs:pairwise", "gnn", "auroc"),
}


def load_rows(path, index):
    I = index.set_index("scenario_id")
    S = pd.read_csv(path, low_memory=False)
    S = S[S["eval"] == 1].copy()
    S["split"] = S.cfg.map(I["split"]).astype(str)
    S["vx_base"] = S.cfg.map(I["vx_base"]).astype(str)
    S["vx_arm"] = S.cfg.map(I["vx_arm"]).astype(str)
    S["deadline"] = S.cfg.map(I["deadline_round"]).astype(float)
    S["rtc"] = S["round"] - S["deadline"]
    S["rep"] = S.run.str.split("/").str[-1]
    return S


def tip_table(S, reps):
    R = S[S.rep.isin(reps)].drop_duplicates("run")
    out = {}
    for rp in reps:
        Q = R[R.rep == rp]
        tr = Q.loc[Q.tipped.astype(bool), "tip_round"].astype(float)
        out[rp] = {"runs": int(len(Q)), "tipped": int(Q.tipped.astype(bool).sum()),
                   "tip_round_mean": r3(tr.mean()) if len(tr) else None,
                   "tip_round_median": r3(tr.median()) if len(tr) else None}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snap", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--pred", action="append", required=True, help="NAME=PATH, repeatable")
    ap.add_argument("--vx-eval", required=True)
    ap.add_argument("--vx-snap", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    index = pd.read_csv(a.index, low_memory=False)
    S = load_rows(a.snap, index)
    assert len(S), "no eval rows"
    assert (S.split == "night_vx_id").all() and (S.vx_arm == "id").all(), "rows outside night_vx_id"
    assert S.rep.isin(["rep2", "rep3"]).all(), f"unexpected replicates {sorted(set(S.rep) - {'rep2', 'rep3'})}"
    assert not S.duplicated(["run", "round"]).any(), "duplicate (run, round)"
    S["y3"] = S["y3"].astype(float)
    assert S.y3.notna().all() and S.y3.isin([0.0, 1.0]).all(), "label y3 missing or not binary on eval rows"

    preds = {}
    for spec in a.pred:
        n, p = spec.split("=", 1)
        sc = S[["run", "round"]].merge(load_pred(p), on=["run", "round"], how="left").score.values.astype(float)
        assert np.isfinite(sc).all(), f"{n}: {int((~np.isfinite(sc)).sum())} scored rows without a finite score"
        preds[n] = sc
    for need in {m for c in CONTRASTS.values() for m in c[:2]}:
        assert need in preds, f"--pred {need}=... is required"

    y, b, base, rep = S.y3.values, bins(S.rtc.values), S.vx_base.values, S.rep.values
    bases = sorted(set(base))
    rows = {k: np.where(base == k)[0] for k in bases}

    def metrics(idx):
        yy, bb = y[idx], b[idx]
        out = {}
        for n, p in preds.items():
            out[(n, "auroc")] = auroc(yy, p[idx])
            out[(n, "tm_auroc")] = tm_auroc(yy, p[idx], bb)
        return out

    full = metrics(np.arange(len(S)))
    rng = np.random.default_rng(a.seed)
    draws = [metrics(np.concatenate([rows[k] for k in rng.choice(bases, len(bases), replace=True)]))
             for _ in range(a.boot)]

    res = {"note": "ANALYSIS_PLAN.md Nachtrag 3; bootstrap over bases with replacement, paired across monitors",
           "boot": a.boot, "seed": a.seed,
           "data": {"bases": len(bases), "runs": int(S.run.nunique()),
                    "runs_per_rep": {r: int(S[S.rep == r].run.nunique()) for r in ("rep2", "rep3")},
                    "bases_per_rep": {r: int(S[S.rep == r].vx_base.nunique()) for r in ("rep2", "rep3")},
                    "rows": int(len(S)), "positives": int(y.sum())},
           "contrasts": {}, "monitors": {}, "per_replicate": {}, "replicate_spread": {}, "tipping": {}}

    for k, (m1, m2, met) in CONTRASTS.items():
        dv = np.array([d[(m1, met)] - d[(m2, met)] for d in draws], float)
        valid = dv[~np.isnan(dv)]
        lo, hi = ci(dv)
        res["contrasts"][k] = {"a": m1, "b": m2, "metric": met, "a_value": r3(full[(m1, met)]),
                               "b_value": r3(full[(m2, met)]), "diff": r3(full[(m1, met)] - full[(m2, met)]),
                               "ci": [r3(lo), r3(hi)], "ci_lower_unrounded": float(lo),
                               "valid_draws": int(len(valid)), "share_draws_le_0": r3(float(np.mean(valid <= 0)))}
    h = res["contrasts"]["H7"]
    res["H7_verdict"] = "supported" if np.isfinite(h["ci_lower_unrounded"]) and h["ci_lower_unrounded"] > 0 else "not supported"

    for n in preds:
        res["monitors"][n] = {}
        for met in ("auroc", "tm_auroc"):
            res["monitors"][n][met] = r3(full[(n, met)])
            res["monitors"][n][met + "_ci"] = [r3(x) for x in ci([d[(n, met)] for d in draws])]
    for rp in ("rep2", "rep3"):
        idx = np.where(rep == rp)[0]
        if len(idx):
            m = metrics(idx)
            res["per_replicate"][rp] = {n: {"auroc": r3(m[(n, "auroc")]), "tm_auroc": r3(m[(n, "tm_auroc")])}
                                        for n in preds}

    V = json.load(open(a.vx_eval))["part_a"]["time"]
    assert V["bases"] == 14, "vx_eval.json part_a.time is expected to cover all 14 bases"
    for n in preds:
        vals = {"rep0": V["monitors"].get(n, {}).get("auroc", {}).get("id_rep0"),
                "rep1": V["monitors"].get(n, {}).get("auroc", {}).get("id_rep1"),
                **{rp: res["per_replicate"].get(rp, {}).get(n, {}).get("auroc") for rp in ("rep2", "rep3")}}
        xs = [v for v in vals.values() if v is not None and np.isfinite(v)]
        pairs = [abs(x1 - x2) for x1, x2 in itertools.combinations(xs, 2)]
        res["replicate_spread"][n] = {**vals, "n_reps": len(xs), "range": r3(max(xs) - min(xs)) if xs else None,
                                      "sd": r3(float(np.std(xs, ddof=1))) if len(xs) > 1 else None,
                                      "mean_abs_pair_diff": r3(float(np.mean(pairs))) if pairs else None}

    vxs = load_rows(a.vx_snap, index)
    vxs = vxs[(vxs.split == "night_vx_id") & vxs.rep.isin(["rep0", "rep1"])]
    res["tipping"] = {**tip_table(vxs, ["rep0", "rep1"]), **tip_table(S, ["rep2", "rep3"])}

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out + ".json", "w"), indent=1)

    L = ["# runs_vx3: confirmatory test (ANALYSIS_PLAN.md Nachtrag 3)", "",
         f"Data: {res['data']['runs']} runs ({res['data']['runs_per_rep']}), {len(bases)} bases, {res['data']['rows']} rows, "
         f"{res['data']['positives']} positives. Bootstrap {a.boot} draws over bases, seed {a.seed}.", "",
         f"**H7: {res['H7_verdict']}.** AUROC zs:global_full {h['a_value']} vs gnn {h['b_value']}, difference "
         f"{h['diff']} [{h['ci'][0]}, {h['ci'][1]}] (valid draws {h['valid_draws']}, share of draws <= 0: "
         f"{h['share_draws_le_0']}).", "", "## Secondary contrasts (no decision rule)", "",
         "| contrast | a | b | difference [95 % CI] |", "|---|---|---|---|"]
    for k, c in res["contrasts"].items():
        if k != "H7":
            L.append(f"| {k} ({c['metric']}) | {c['a']} {c['a_value']} | {c['b']} {c['b_value']} | {c['diff']} "
                     f"[{c['ci'][0]}, {c['ci'][1]}] |")
    L += ["", "## All predictors (descriptive)", "",
          "| predictor | AUROC [CI] | time-matched [CI] | rep2 | rep3 | rep0 (vx) | rep1 (vx) | range rep0-3 |",
          "|---|---|---|---|---|---|---|---|"]
    for n in preds:
        m, sp = res["monitors"][n], res["replicate_spread"][n]
        L.append(f"| {n} | {m['auroc']} [{m['auroc_ci'][0]}, {m['auroc_ci'][1]}] | {m['tm_auroc']} "
                 f"[{m['tm_auroc_ci'][0]}, {m['tm_auroc_ci'][1]}] | {sp['rep2']} | {sp['rep3']} | {sp['rep0']} | "
                 f"{sp['rep1']} | {sp['range']} |")
    L += ["", "## Tipping per replicate (descriptive)", "", "| replicate | runs | tipped | tip round mean | median |",
          "|---|---|---|---|---|"]
    for rp, t in res["tipping"].items():
        L.append(f"| {rp} | {t['runs']} | {t['tipped']} | {t['tip_round_mean']} | {t['tip_round_median']} |")
    open(a.out + ".md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
