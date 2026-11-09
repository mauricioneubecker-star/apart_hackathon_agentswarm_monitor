"""Post-hoc, exploratory numbers quoted in analysis/results/vx.md (NOT part of the pre-registered evaluation).

Everything here was chosen after the one night_vx evaluation (bb3f665d) had been read. It only reads the frozen inputs
(analysis/vx_preds/) and the evaluation outputs (analysis/results/vx_eval.json); nothing feeds back into the
pre-registered verdicts. Purpose: make every number in vx.md that is not in vx_eval.json reproducible from the repo.

  python analysis/vx_posthoc.py --out analysis/results/vx_posthoc
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from math import comb

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.metrics import roc_auc_score

P = "analysis/vx_preds"
FILES = {"clock": "clock", "struct": "struct", "bag+graph": "bag+graph", "gnn": "gnn", "hybrid": "hybrid",
         "zs:pairwise": "zs_pairwise", "zs:global_full": "zs_global_full", "oracle": "oracle"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261109)
    a = ap.parse_args()
    res = {"note": "post hoc, exploratory; chosen after reading the night_vx evaluation", "boot": a.boot, "seed": a.seed}
    E = json.load(open("analysis/results/vx_eval.json"))
    A = E["part_a"]

    # 1. resolution of the shift tests
    hw = {"shift": {"auroc": [], "tm_auroc": []}, "shift_minus_noise": {"auroc": [], "tm_auroc": []}}
    gnn_hw = {k: {"auroc": [], "tm_auroc": []} for k in hw}
    below = 0
    for arm, r in A.items():
        for n, mr in r["monitors"].items():
            for m in ("auroc", "tm_auroc"):
                for k in hw:
                    lo, hi = mr[m][k + "_ci"]
                    hw[k][m].append((hi - lo) / 2)
                    if n == "gnn":
                        gnn_hw[k][m].append((hi - lo) / 2)
                below += mr[m]["shift_minus_noise_ci"][1] < 0
    res["resolution"] = {
        "shift_minus_noise_cis_entirely_below_0": f"{below} of {sum(len(v) for v in hw['shift_minus_noise'].values())}",
        "median_half_width": {k: {m: float(np.median(v)) for m, v in d.items()} for k, d in hw.items()},
        "gnn_half_width_range": {k: {m: [float(min(v)), float(max(v))] for m, v in d.items()} for k, d in gnn_hw.items()},
        "note": "a drop equal to the half-width is detected about half the time; about 80 % needs ~1.43 x the half-width"}
    noise = {n: {"noise": A["time"]["monitors"][n]["auroc"]["noise"], "ci": A["time"]["monitors"][n]["auroc"]["noise_ci"]}
             for n in A["time"]["monitors"]}
    res["replicate_noise_auroc_14_bases"] = noise
    res["monitors_with_negative_noise"] = f"{sum(v['noise'] < 0 for v in noise.values())} of {len(noise)}"

    # 2. tip timing and run order
    I = pd.read_csv("sim_dataset/dataset/index.csv", low_memory=False).set_index("scenario_id")
    S = pd.read_csv(f"{P}/snap/runs_vx_snapshots.csv", low_memory=False)
    R = S.groupby("run").agg(cfg=("cfg", "first"), tipped=("tipped", "max"), tip=("tip_round", "max")).reset_index()
    R["arm"], R["base"] = R.cfg.map(I["vx_arm"]), R.cfg.map(I["vx_base"])
    R["rep"] = R.run.str.split("/").str[-1]
    timing = {}
    for lab, (arm, rep) in {"id_rep0": ("id", "rep0"), "id_rep1": ("id", "rep1"), "time": ("time", "rep0")}.items():
        t = R[(R.arm == arm) & (R.rep == rep) & (R.tipped == 1)]
        timing[lab] = {"tipped": int(len(t)), "mean_tip_round": float(t.tip.mean()), "range": [int(t.tip.min()), int(t.tip.max())]}
    piv = R[R.arm.isin(["id", "time"])].assign(key=lambda d: d.arm + "_" + d.rep).pivot_table(index="base", columns="key", values="tip")
    both = piv.dropna(subset=["id_rep0", "id_rep1"])
    later = int((both.id_rep1 > both.id_rep0).sum())
    n_disc = int((both.id_rep1 != both.id_rep0).sum())
    timing["rep1_minus_rep0_paired"] = {"bases_tipped_in_both": int(len(both)), "rep1_later": later,
                                        "mean_diff": float((both.id_rep1 - both.id_rep0).mean()),
                                        "sign_test_p": float(min(1.0, 2 * sum(comb(n_disc, k) for k in range(min(later, n_disc - later) + 1)) / 2 ** n_disc))}
    for ref in ("id_rep0", "id_rep1"):
        b = piv.dropna(subset=["time_rep0", ref])
        timing[f"time_minus_{ref}_paired"] = {"bases": int(len(b)), "mean_diff": float((b.time_rep0 - b[ref]).mean())}
    dl = I[I.index.isin(R[R.arm == "id"].cfg)]["deadline_round"]
    timing["deadline_id_mean"] = float(dl.mean())
    timing["deadline_time_arm"] = sorted(set(I[I.index.isin(R[R.arm == "time"].cfg)]["deadline_round"].astype(int)))
    starts = []
    for f in glob.glob("sim_dataset/runs_vx/*/rep*/meta.json"):
        m = json.load(open(f))
        cfg, rep = f.split(os.sep)[-3], f.split(os.sep)[-2]
        st = m.get("started") or m.get("start_time") or m.get("t_start") or m.get("created")
        starts.append({"cfg": cfg, "rep": rep, "arm": I.at[cfg, "vx_arm"] if cfg in I.index else None, "start": st})
    St = pd.DataFrame(starts)
    if St.start.notna().all():
        St = St.sort_values("start")
        blocks = []
        for _, r in St.iterrows():
            lab = ("id rep1" if (r.arm == "id" and r.rep == "rep1") else
                   f"Part B {r.rep}" if r.arm == "rep" else "Part A rep0 + arms (+ gate canaries)")
            if not blocks or blocks[-1]["block"] != lab:
                blocks.append({"block": lab, "n": 0, "first": str(r.start), "last": str(r.start)})
            blocks[-1]["n"] += 1
            blocks[-1]["last"] = str(r.start)
        timing["run_order_blocks_by_start_time"] = blocks
    res["timing"] = timing

    # 3. pooled Part A level contrasts (paired bootstrap over bases)
    D = S[S["eval"] == 1].copy()
    D["arm"], D["base"] = D.cfg.map(I["vx_arm"]), D.cfg.map(I["vx_base"])
    D = D[D.arm.isin(["id", "time", "glm", "enf", "topo"])]
    for n, f in FILES.items():
        D = D.merge(pd.read_csv(f"{P}/preds/{f}.csv").rename(columns={"score": n}), on=["run", "round"], how="left")
    y = D.y3.values.astype(int)
    bases = np.array(sorted(D.base.unique()))
    idx = {b: np.where(D.base.values == b)[0] for b in bases}
    rng = np.random.default_rng(a.seed)
    draws = [np.concatenate([idx[b] for b in rng.choice(bases, len(bases))]) for _ in range(a.boot)]
    pairs = [("zs:global_full", "gnn"), ("zs:pairwise", "gnn"), ("zs:global_full", "zs:pairwise"), ("zs:global_full", "hybrid"),
             ("zs:global_full", "bag+graph"), ("hybrid", "bag+graph"), ("gnn", "clock"), ("zs:global_full", "clock"),
             ("zs:pairwise", "clock")]
    aucs = {n: roc_auc_score(y, D[n].values) for n in FILES}
    bs = {n: np.array([roc_auc_score(y[r], D[n].values[r]) for r in draws]) for n in {x for p in pairs for x in p}}
    res["pooled_part_a"] = {"rows": int(len(D)), "positives": int(y.sum()), "bases": int(len(bases)),
                            "auroc": {n: float(v) for n, v in aucs.items()},
                            "contrasts": {f"{p} - {q}": {"diff": float(aucs[p] - aucs[q]),
                                                         "ci": [float(np.percentile(bs[p] - bs[q], 2.5)), float(np.percentile(bs[p] - bs[q], 97.5))]}
                                          for p, q in pairs}}

    # 4. Part B pair composition and pairs with at least one new run
    SN = pd.read_csv(f"{P}/snap/night_snapshots.csv", low_memory=False)
    src = set(I[I.split == "night_vx_rep"].vx_base)
    B = pd.concat([S[S.cfg.map(I["split"]) == "night_vx_rep"].assign(new=1), SN[SN.cfg.isin(src)].assign(new=0)])
    B = B[B["eval"] == 1].copy()
    B["group"] = np.where(B.new == 1, B.cfg.map(I["vx_base"]), B.cfg)
    B["deadline"] = B.cfg.map(I["deadline_round"])
    pre = B[B["round"] == B.deadline - 6]
    for n, f in FILES.items():
        pre = pre.merge(pd.read_csv(f"{P}/preds/{f}.csv").rename(columns={"score": n}), on=["run", "round"], how="left")
    rows = []
    for g, d in pre.groupby("group"):
        for _, p in d[d.tipped == 1].iterrows():
            for _, q in d[d.tipped == 0].iterrows():
                kind = {2: "new-new", 1: "night-new", 0: "night-night"}[int(p.new) + int(q.new)]
                rows.append({"kind": kind, "tipped_is_new": int(p.new), **{n: float(np.sign(p[n] - q[n])) for n in FILES}})
    Q = pd.DataFrame(rows)
    win = lambda d, n: float(((d[n] > 0) + 0.5 * (d[n] == 0)).mean())  # noqa: E731
    res["part_b_pairs"] = {"composition": Q.kind.value_counts().to_dict(), "rows_night_only": int((B.new == 0).sum()),
                           "rows_total": int(len(B)),
                           "with_new_run": {n: win(Q[Q.kind != "night-night"], n) for n in FILES},
                           "night_night": {n: win(Q[Q.kind == "night-night"], n) for n in FILES},
                           "struct_night_new_by_direction": {f"tipped_is_new={k}": f"{int((d.struct > 0).sum())}/{len(d)}"
                                                             for k, d in Q[Q.kind == "night-new"].groupby("tipped_is_new")}}

    # 5. H4 details: violators in alarmed untipped runs (gnn), Fisher test
    thr = json.load(open(f"{P}/thresholds.json"))
    Sg = S[S["eval"] == 1].merge(pd.read_csv(f"{P}/preds/gnn.csv"), on=["run", "round"])
    Sg["arm"], Sg["rep"] = Sg.cfg.map(I["vx_arm"]), Sg.run.str.split("/").str[-1]
    enf_b = set(Sg[Sg.arm == "enf"].cfg.map(I["vx_base"]))
    al = {}
    for arm in ("enf", "id"):
        U = Sg[(Sg.arm == arm) & (Sg.rep == "rep0") & (Sg.tipped == 0) & Sg.cfg.map(I["vx_base"]).isin(enf_b)]
        mx = U.groupby("run").agg(score=("score", "max"), risk=("risk", "max"))
        hit = mx[mx.score >= thr["gnn"]["thr"]]
        al[arm] = {"alarmed": int(len(hit)), "untipped": int(len(mx)), "max_violators_of_alarmed": hit.risk.astype(int).tolist()}
    al["fisher_p"] = float(fisher_exact([[al["enf"]["alarmed"], al["enf"]["untipped"] - al["enf"]["alarmed"]],
                                         [al["id"]["alarmed"], al["id"]["untipped"] - al["id"]["alarmed"]]])[1])
    res["h4_gnn_alarms"] = al

    # 6. rounds in which the frozen clock is at or above its alarm threshold
    C = pd.read_csv(f"{P}/preds/clock.csv").merge(S[["run", "round"]], on=["run", "round"])
    res["clock_alarm_rounds"] = sorted(C[C.score >= thr["clock"]["thr"]]["round"].unique().astype(int).tolist())

    # 7. time-matched companions of the verdict rules (from vx_eval.json / vx_eval_refbag.json)
    E2 = json.load(open("analysis/results/vx_eval_refbag.json"))["part_a"]
    tm = lambda arm, n, k: A[arm]["monitors"][n]["tm_auroc"][k]  # noqa: E731
    res["tm_companions"] = {
        "H2_gnn_shift_noise": [tm("time", "gnn", "shift"), tm("time", "gnn", "noise")],
        "H3_gnn_bag_shift": [tm("glm", "gnn", "shift"), tm("glm", "bag", "shift"), E2["glm"]["monitors"]["gnn"]["tm_auroc"]["shift_minus_shift_bag"]],
        "H4i_gnn_shift_noise": [tm("enf", "gnn", "shift"), tm("enf", "gnn", "noise")],
        "H5_gnn_bag_shift": [tm("topo", "gnn", "shift"), tm("topo", "bag", "shift"), E2["topo"]["monitors"]["gnn"]["tm_auroc"]["shift_minus_shift_bag"],
                             E2["topo"]["monitors"]["gnn"]["tm_auroc"]["shift_minus_shift_bag_ci"]],
        "H2_clock_without_last3": E["h2_clock_without_last3"]["monitors"]["clock"]["auroc"]}
    json.dump(res, open(a.out + ".json", "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
