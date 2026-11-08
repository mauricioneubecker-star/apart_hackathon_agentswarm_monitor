"""Assemble the prediction files and thresholds for the one night_vx evaluation (ANALYSIS_PLAN.md §6, Nachtrag 2).

Inputs (all produced without evaluating anything):
  --gnn-night / --gnn-vx   frozen GNN (models/cloud_final_gnn.pt, 15 states) via gnn_opt_torch/predict.py --no-eval
  --baselines              output dir of make_baselines.py (night_train refits)
  --llm                    data/llm_monitor (llm_monitor.aggregate over runs_night and runs_vx)
  --night-data / --vx-data harness datasets (gnn_opt/build_dataset.py)
  --gnn-repo               checkout of origin/gnn-opt-torch (CV files for thresholds, committed eval files for checks)
Writes to --out: preds/<name>.csv (run, round, score), thresholds.json, manifest.json, snap/*.csv, run_eval.sh.

Checks (manifest.json):
  * hybrid formula: blend(committed GNN eval, committed tab_mem eval) == committed cloud_final eval;
  * coverage: every row vx_eval.py scores (night_vx without ft / ft_base / pop_bal, and Part B) has a finite score in
    [0, 1] for every predictor. Only keys and splits are read for this, no label.
Thresholds (5 % FPR, harness metrics.thr_at_fpr): trained models from their night_train ID-OOF (harness id_oof of the
CV file); zero-shot LLMs from the night_train + night_val eval rows (ANALYSIS_PLAN.md §4).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

# predictor name -> (prediction source, CV file for the threshold relative to the gnn repo)
TRAINED = {
    "clock": ("hgb_clock", "gnn_opt/preds/cv/hgb_clock.csv"),
    "struct": ("hgb_struct", "gnn_opt/preds/cv/hgb_struct.csv"),
    "feat_pairwise": ("hgb_pairwise", "gnn_opt/preds/cv/hgb_pairwise.csv"),
    "bag": ("hgb_bag", "gnn_opt/preds/cv/hgb_bag.csv"),
    "bag+graph": ("hgb_bag+graph", "gnn_opt/preds/cv/hgb_bag+graph.csv"),
    "tab_mem": ("hgb_bag+graph+mem", "gnn_opt/preds/cv/hgb_bag+graph+mem.csv"),
    "edge": ("edge_monitor_top3", "gnn_opt/preds/cv/edge_monitor_top3.csv"),
    "gnn": ("gnn", "gnn_opt_torch/preds/cv/cloud_final_gnn.csv"),
    "hybrid": ("hybrid", "gnn_opt_torch/preds/cv/cloud_final.csv"),
    "oracle": ("oracle_risk+clock", "gnn_opt/preds/cv/oracle_risk+clock.csv"),
}
ZS = {"zs:pairwise": "pairwise", "zs:global_full": "global_full"}
ORDER = ["clock", "struct", "feat_pairwise", "bag", "bag+graph", "tab_mem", "edge", "gnn", "hybrid", "zs:pairwise",
         "zs:global_full", "oracle"]
# 5 %-FPR thresholds of the held-out comparison (analysis/results/heldout_full.md §1.3), recomputed here as a check
HELDOUT_THR = {"clock": 0.1207, "bag+graph": 0.1363, "tab_mem": 0.1363, "edge": 0.3263, "gnn": 0.314, "hybrid": 0.1431,
               "zs:pairwise": 0.88, "zs:global_full": 0.65, "oracle": 0.1162}
EXCL = ["night_vx_ft", "night_vx_ft_base", "night_vx_pop_bal"]


def fname(n):
    return n.replace(":", "_") + ".csv"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("gnn-night", "gnn-vx", "baselines", "llm", "night-data", "vx-data", "gnn-repo", "index", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--blend-w", type=float, default=0.5, help="GNN weight (models/cloud_final_gnn.pt: blend_w = 0.5)")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.gnn_repo, "gnn_opt"))
    sys.path.insert(0, os.path.join(a.gnn_repo, "gnn_opt_torch"))
    import harness as H  # noqa: E402
    import metrics as M  # noqa: E402
    from blend import blend  # noqa: E402

    out = a.out
    os.makedirs(os.path.join(out, "preds"), exist_ok=True)
    os.makedirs(os.path.join(out, "snap"), exist_ok=True)
    SN = pd.read_csv(os.path.join(a.night_data, "snapshots.csv"), low_memory=False)
    SV = pd.read_csv(os.path.join(a.vx_data, "snapshots.csv"), low_memory=False)
    keys_night = SN.loc[SN.split != H.TRAIN_SPLIT, ["run", "round"]]
    keys_all = pd.concat([keys_night, SV[["run", "round"]]], ignore_index=True)
    man = {"preds": {}, "checks": {}}

    # ------------------------------------------------------------------ predictions
    P = {}
    for n, (src, _) in TRAINED.items():
        if src in ("gnn", "hybrid"):
            continue
        P[n] = pd.read_csv(os.path.join(a.baselines, f"{src}.csv"))
        man["preds"][n] = {"source": f"make_baselines.py {src} (refit on night_train)"}
    G = pd.concat([pd.read_csv(a.gnn_night), pd.read_csv(a.gnn_vx)], ignore_index=True)
    G = keys_all.merge(G[["run", "round", "score"]], on=["run", "round"], how="left")
    P["gnn"] = G
    man["preds"]["gnn"] = {"source": "gnn_opt_torch/predict.py --no-eval --blend '' --model models/cloud_final_gnn.pt "
                                     "(15 stored states = 5 seeds x last 3 snapshots)",
                           "gnn_night_sha256": sha(a.gnn_night), "gnn_vx_sha256": sha(a.gnn_vx)}
    HY = blend([G, P["tab_mem"]], [a.blend_w, 1 - a.blend_w], mode="logit")[["run", "round", "score"]]
    P["hybrid"] = HY
    man["preds"]["hybrid"] = {"source": f"blend.py logit, GNN weight {a.blend_w}, gnn + tab_mem (refit)"}
    for n, v in ZS.items():
        L = pd.read_csv(os.path.join(a.llm, v, "snapshots.csv"), low_memory=False)
        P[n] = L.rename(columns={"episode_id": "run", "t": "round", "zs_tip": "score"})[["run", "round", "score"]]
        man["preds"][n] = {"source": f"data/llm_monitor/{v}/snapshots.csv zs_tip (zero-shot, prompt lm1-2026-11-08)"}

    # ------------------------------------------------------------------ hybrid formula check on committed files
    ce = lambda f: pd.read_csv(os.path.join(a.gnn_repo, "gnn_opt_torch", "preds", "eval", f))  # noqa: E731
    Gc, Tc, Hc = ce("cloud_final_gnn.csv"), ce("hgb_bag+graph+mem__allsplits.csv"), ce("cloud_final.csv")
    Bc = blend([Tc[["run", "round"]].merge(Gc, on=["run", "round"]), Tc], [0.5, 0.5], mode="logit")
    j = Bc.merge(Hc, on=["run", "round"], suffixes=("_mine", "_ref"))
    d = (j.score_mine - j.score_ref).abs()
    man["checks"]["hybrid_formula_on_committed_files"] = {"rows": int(len(j)), "max_abs_diff": float(d.max())}
    chk = os.path.join(a.gnn_repo, "gnn_opt_torch", "preds", "new", "runs_check__cloud_final_gnn+hgb_bag+graph+mem.csv")
    if os.path.exists(chk):
        j = pd.read_csv(chk).merge(HY, on=["run", "round"], suffixes=("_team", "_mine"))
        d = (j.score_team - j.score_mine).abs()
        man["checks"]["hybrid_vs_team_predict_check_120"] = {
            "rows": int(len(j)), "max_abs_diff": float(d.max()),
            "spearman": float(j[["score_team", "score_mine"]].corr("spearman").iloc[0, 1]),
            "note": "team GBM refit on its own table.csv; differences = float32 table noise of tab_mem"}

    # ------------------------------------------------------------------ thresholds (training data only)
    lab = SN[(SN["eval"] == 1) & SN.y3.notna()][["run", "round", "split", "y3"]]
    thr = {}
    for n, (_, cvf) in TRAINED.items():
        oof = H.id_oof(pd.read_csv(os.path.join(a.gnn_repo, cvf))).merge(lab, on=["run", "round"])
        t = float(M.thr_at_fpr(oof.y3.values, oof.score.values))
        thr[n] = {"thr": t, "from": f"night_train ID-OOF of {cvf} (harness id_oof, repeat mean)", "rows": int(len(oof)),
                  "fpr_on_that_data": float((oof.score.values[oof.y3.values == 0] > t).mean())}
    for n in ZS:
        m = lab[lab.split.isin([H.TRAIN_SPLIT, "night_val"])].merge(P[n], on=["run", "round"])
        t = float(M.thr_at_fpr(m.y3.values, m.score.values))
        thr[n] = {"thr": t, "from": "night_train + night_val eval rows (raw zero-shot score)", "rows": int(len(m)),
                  "fpr_on_that_data": float((m.score.values[m.y3.values == 0] > t).mean())}
    for n, v in HELDOUT_THR.items():
        thr[n]["heldout_value"] = v
        thr[n]["matches_heldout_4sig"] = float(f"{thr[n]['thr']:.4g}") == v
    json.dump(thr, open(os.path.join(out, "thresholds.json"), "w"), indent=1)

    # ------------------------------------------------------------------ coverage on the rows vx_eval.py scores (keys only)
    I = pd.read_csv(a.index, low_memory=False).set_index("scenario_id")
    K = pd.concat([SV, SN], ignore_index=True)
    K = K[K["eval"] == 1][["run", "round", "cfg"]].copy()
    K["split"] = K.cfg.map(I["split"]).astype(str)
    vxb = K[K.split.str.startswith("night_vx") & ~K.split.isin(EXCL)]
    src = set(K[K.split == "night_vx_rep"].cfg.map(I["vx_base"]))
    pb = K[(K.split == "night_vx_rep") | K.cfg.isin(src)]
    cov = {"night_vx_rows": int(len(vxb)), "part_b_rows": int(len(pb)), "part_b_source_cfgs": sorted(src)}
    for n in ORDER:
        Q = P[n]
        assert not Q.duplicated(["run", "round"]).any(), n
        s = Q.score.values.astype(float)
        bad = {"nan_or_inf": int((~np.isfinite(s)).sum()), "out_of_01": int(((s < 0) | (s > 1)).sum())}
        miss = {b: int(D.merge(Q, on=["run", "round"], how="left").score.isna().sum()) for b, D in (("night_vx", vxb), ("part_b", pb))}
        cov[n] = {**bad, **{f"missing_{k}": v for k, v in miss.items()}, "rows_in_file": int(len(Q))}
        if bad["nan_or_inf"]:
            cov[n]["nonfinite_runs"] = sorted(Q.loc[~np.isfinite(s), "run"].unique().tolist())
        p = os.path.join(out, "preds", fname(n))
        Q.to_csv(p, index=False)
        man["preds"][n].update({"file": os.path.relpath(p, out), "sha256": sha(p), "rows": int(len(Q))})
    man["checks"]["coverage"] = cov
    ok = all(cov[n]["missing_night_vx"] == 0 and cov[n]["missing_part_b"] == 0 for n in ORDER)

    # ------------------------------------------------------------------ snapshot tables + the exact evaluation command
    for nm, d in (("runs_vx", a.vx_data), ("night", a.night_data)):
        shutil.copyfile(os.path.join(d, "snapshots.csv"), os.path.join(out, "snap", f"{nm}_snapshots.csv"))
        man["checks"][f"snap_{nm}_sha256"] = sha(os.path.join(out, "snap", f"{nm}_snapshots.csv"))
    rel = os.path.relpath(out, os.getcwd())
    preds = " \\\n  ".join(f"--pred '{n}={rel}/preds/{fname(n)}'" for n in ORDER)
    thrs = " \\\n  ".join(f"--thr '{n}={thr[n]['thr']!r}'" for n in ORDER)
    base = (f"\"$PY\" analysis/vx_eval.py --snap {rel}/snap/runs_vx_snapshots.csv {rel}/snap/night_snapshots.csv \\\n"
            f"  --index sim_dataset/dataset/index.csv \\\n  {preds} \\\n  {thrs} \\\n  --boot 2000 --seed 20261108")
    LOG = "analysis/results/vx_run.log"
    sh = ["#!/usr/bin/env bash",
          "# The one night_vx evaluation (ANALYSIS_PLAN.md §6 and Nachtrag 2). Run ONCE, from the repo root.",
          "# Call 2 only changes --ref (H3/H5 compare against bag); same seed, so all other numbers must be identical.",
          "# If one step fails, only that step is repeated with identical arguments (Nachtrag 2 item 8).",
          "set -euo pipefail", 'PY="${PY:-sim_dataset/.venv/bin/python}"',
          'if [ -e analysis/results/vx_eval.json ]; then echo "analysis/results/vx_eval.json exists: already ran"; exit 1; fi',
          f'{{ date -u "+start %Y-%m-%dT%H:%M:%SZ"; git rev-parse HEAD; shasum -a 256 analysis/vx_eval.py; '
          f'"$PY" -c "import sys,numpy,pandas,sklearn,scipy; print(sys.version.split()[0], numpy.__version__, '
          f'pandas.__version__, sklearn.__version__, scipy.__version__)"; }} > {LOG}',
          base + " \\\n  --ref bag+graph --out analysis/results/vx_eval > analysis/results/vx_eval.log 2>&1 &", "P1=$!",
          base + " \\\n  --ref bag --out analysis/results/vx_eval_refbag > analysis/results/vx_eval_refbag.log 2>&1 &",
          "P2=$!",
          '"$PY" analysis/vx_jury_ks.py --runs sim_dataset/runs_vx --index sim_dataset/dataset/index.csv '
          f'--out analysis/results/vx_jury_ks >> {LOG} 2>&1',
          'wait "$P1"', 'wait "$P2"',
          '"$PY" analysis/vx_verdicts.py --call1 analysis/results/vx_eval.json --call2 analysis/results/vx_eval_refbag.json '
          f'--ks analysis/results/vx_jury_ks.json --out analysis/results/vx_verdicts >> {LOG} 2>&1',
          f'date -u "+done %Y-%m-%dT%H:%M:%SZ" >> {LOG}', 'echo "night_vx evaluation done"']
    open(os.path.join(out, "run_eval.sh"), "w").write("\n".join(sh) + "\n")
    man["coverage_ok"] = bool(ok)
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(json.dumps({"coverage_ok": ok, "checks": {k: v for k, v in man["checks"].items() if k != "coverage"}}, indent=1))
    print(json.dumps({n: {k: cov[n][k] for k in cov[n]} for n in ORDER}, indent=0)[:3000])
    print(json.dumps({n: (round(v["thr"], 5), v.get("heldout_value"), v.get("matches_heldout_4sig")) for n, v in thr.items()}))


if __name__ == "__main__":
    main()
