"""Assemble the frozen prediction files for the one runs_vx3 evaluation (ANALYSIS_PLAN.md Nachtrag 3). Nothing is
evaluated here; labels are not read (only keys, cfg and the eval flag for the coverage check).

Inputs (same producers as analysis/vx_preds, see its README):
  --gnn-vx3    gnn_opt_torch/predict.py --no-eval --blend '' --model models/cloud_final_gnn.pt on runs_vx3
  --baselines  output dir of analysis/vx_preds/make_baselines.py --vx <runs_vx3 dataset> (night_train refits)
  --llm        llm_monitor.aggregate --runs sim_dataset/runs_vx3 --out <dir> (zero-shot global_full, pairwise)
  --vx3-data   harness dataset of runs_vx3 (gnn_opt/build_dataset.py)
  --gnn-repo   checkout of origin/gnn-opt-torch f7194430 (for blend.py)
Writes to --out: preds/<name>.csv (run, round, score) for the runs_vx3 rows, snap/runs_vx3_snapshots.csv,
manifest.json (sources, sha256, coverage), run_eval.sh (the one evaluation, with a guard against a second run).
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

BASELINE = {"clock": "hgb_clock", "struct": "hgb_struct", "feat_pairwise": "hgb_pairwise", "bag": "hgb_bag",
            "bag+graph": "hgb_bag+graph", "tab_mem": "hgb_bag+graph+mem", "edge": "edge_monitor_top3",
            "oracle": "oracle_risk+clock"}
ZS = {"zs:pairwise": "pairwise", "zs:global_full": "global_full"}
ORDER = ["clock", "struct", "feat_pairwise", "bag", "bag+graph", "tab_mem", "edge", "gnn", "hybrid", "zs:pairwise",
         "zs:global_full", "oracle"]


def fname(n):
    return n.replace(":", "_") + ".csv"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("gnn-vx3", "baselines", "llm", "vx3-data", "gnn-repo", "index", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--blend-w", type=float, default=0.5, help="GNN weight (models/cloud_final_gnn.pt: blend_w = 0.5)")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.gnn_repo, "gnn_opt_torch"))
    from blend import blend  # noqa: E402

    out = a.out
    os.makedirs(os.path.join(out, "preds"), exist_ok=True)
    os.makedirs(os.path.join(out, "snap"), exist_ok=True)
    SV = pd.read_csv(os.path.join(a.vx3_data, "snapshots.csv"), low_memory=False)
    keys = SV[["run", "round"]].drop_duplicates()
    I = pd.read_csv(a.index, low_memory=False).set_index("scenario_id")
    splits = sorted(set(SV.cfg.map(I["split"]).astype(str)))
    assert splits == ["night_vx_id"], f"runs_vx3 must only hold night_vx_id runs, found {splits}"
    reps = sorted(set(SV.run.str.split("/").str[-1]))
    assert set(reps) <= {"rep2", "rep3"}, f"unexpected replicates {reps}"
    man = {"preds": {}, "checks": {}, "data": {"runs": int(SV.run.nunique()), "rows": int(len(SV)),
                                                "eval_rows": int((SV["eval"] == 1).sum()), "replicates": reps,
                                                "bases": int(SV.cfg.nunique())}}

    P = {}
    for n, src in BASELINE.items():
        B = pd.read_csv(os.path.join(a.baselines, f"{src}.csv"))
        P[n] = keys.merge(B[["run", "round", "score"]], on=["run", "round"], how="left")
        man["preds"][n] = {"source": f"make_baselines.py {src} (refit on night_train), runs_vx3 rows"}
    G = pd.read_csv(a.gnn_vx3)
    P["gnn"] = keys.merge(G[["run", "round", "score"]], on=["run", "round"], how="left")
    man["preds"]["gnn"] = {"source": "gnn_opt_torch/predict.py --no-eval --blend '' --model models/cloud_final_gnn.pt "
                                     "(15 stored states)", "gnn_vx3_sha256": sha(a.gnn_vx3)}
    P["hybrid"] = blend([P["gnn"], P["tab_mem"]], [a.blend_w, 1 - a.blend_w], mode="logit")[["run", "round", "score"]]
    man["preds"]["hybrid"] = {"source": f"blend.py logit, GNN weight {a.blend_w}, gnn + tab_mem (refit)"}
    for n, v in ZS.items():
        L = pd.read_csv(os.path.join(a.llm, v, "snapshots.csv"), low_memory=False)
        L = L.rename(columns={"episode_id": "run", "t": "round", "zs_tip": "score"})[["run", "round", "score"]]
        P[n] = keys.merge(L, on=["run", "round"], how="left")
        man["preds"][n] = {"source": f"{v}/snapshots.csv zs_tip (zero-shot, prompt lm1-2026-11-08, Claude Haiku 5.5)"}

    K = SV[SV["eval"] == 1][["run", "round"]]
    cov = {"eval_rows": int(len(K))}
    for n in ORDER:
        Q = P[n]
        assert not Q.duplicated(["run", "round"]).any(), n
        j = K.merge(Q, on=["run", "round"], how="left")
        s = j.score.values.astype(float)
        cov[n] = {"missing_or_nonfinite_on_eval_rows": int((~np.isfinite(s)).sum()),
                  "out_of_01": int(((s < 0) | (s > 1)).sum()), "rows_in_file": int(len(Q))}
        p = os.path.join(out, "preds", fname(n))
        Q.to_csv(p, index=False)
        man["preds"][n].update({"file": os.path.relpath(p, out), "sha256": sha(p), "rows": int(len(Q))})
    man["checks"]["coverage"] = cov
    ok = all(cov[n]["missing_or_nonfinite_on_eval_rows"] == 0 and cov[n]["out_of_01"] == 0 for n in ORDER)
    man["coverage_ok"] = bool(ok)

    snap = os.path.join(out, "snap", "runs_vx3_snapshots.csv")
    shutil.copyfile(os.path.join(a.vx3_data, "snapshots.csv"), snap)
    man["checks"]["snap_runs_vx3_sha256"] = sha(snap)
    rel = os.path.relpath(out, os.getcwd())
    preds = " \\\n  ".join(f"--pred '{n}={rel}/preds/{fname(n)}'" for n in ORDER)
    LOG = "analysis/results/vx3_run.log"
    sh = ["#!/usr/bin/env bash",
          "# The one evaluation of runs_vx3 (ANALYSIS_PLAN.md Nachtrag 3). Run ONCE, from the repo root.",
          "# If it fails, only this call is repeated with identical arguments.",
          "set -euo pipefail", 'PY="${PY:-sim_dataset/.venv/bin/python}"',
          'if [ -e analysis/results/vx3_eval.json ]; then echo "analysis/results/vx3_eval.json exists: already ran"; exit 1; fi',
          f'{{ date -u "+start %Y-%m-%dT%H:%M:%SZ"; git rev-parse HEAD; shasum -a 256 analysis/vx3_eval.py analysis/vx_eval.py; '
          f'"$PY" -c "import sys,numpy,pandas,sklearn; print(sys.version.split()[0], numpy.__version__, '
          f'pandas.__version__, sklearn.__version__)"; }} > {LOG}',
          f'"$PY" analysis/vx3_eval.py --snap {rel}/snap/runs_vx3_snapshots.csv --index sim_dataset/dataset/index.csv \\\n'
          f'  {preds} \\\n  --vx-eval analysis/results/vx_eval.json --vx-snap analysis/vx_preds/snap/runs_vx_snapshots.csv \\\n'
          f'  --boot 10000 --seed 20261109 --out analysis/results/vx3_eval >> {LOG} 2>&1',
          f'date -u "+done %Y-%m-%dT%H:%M:%SZ" >> {LOG}', 'echo "runs_vx3 evaluation done"']
    open(os.path.join(out, "run_eval.sh"), "w").write("\n".join(sh) + "\n")
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(json.dumps({"coverage_ok": ok, "data": man["data"], "coverage": cov}, indent=1))


if __name__ == "__main__":
    main()
