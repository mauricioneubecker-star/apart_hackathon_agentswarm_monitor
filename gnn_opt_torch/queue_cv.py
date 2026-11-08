#!/usr/bin/env python3
"""Run many (config x fold) CV jobs through one process pool (keeps all cores busy across configs).

  python3 gnn_opt_torch/queue_cv.py --jobs experiments/arch.jsonl --cv all --workers 12
jobs file: one JSON object per line: {"name": ..., "cfg": {...}, "control": null|"rewire"|..., "seed": int,
"cv": optional per-job fold set, "data": optional}
Each config's CV file is written to preds/cv/<name>.csv when its last fold finishes; the summary (harness selection
score etc.) is appended to --log. Configs whose CV file exists are skipped (resumable; --force).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import train as T  # noqa: E402


def summarize_cv(data, P, cvk):
    """Selection-score summary for fold sets with LODO folds; ID pooled AUROC/AUPRC (mean over repeats) otherwise."""
    if cvk in ("all", "id0+lodo", "lodo"):
        return T.summarize(data, P)
    from sklearn.metrics import average_precision_score, roc_auc_score
    S = T.get_data(data, "headline", False).S
    Q = P.merge(S[["run", "round", "y3"]], on=["run", "round"])
    rep = Q.fold.str.split("_").str[0]
    au = [roc_auc_score(g.y3, g.score) for _, g in Q.groupby(rep)]
    pr = [average_precision_score(g.y3, g.score) for _, g in Q.groupby(rep)]
    return {"id_auroc": sum(au) / len(au), "id_auprc": sum(pr) / len(pr)}


def run_queue(specs, cv="all", workers=12, data=None, force=False, log=None, out_dir=None):
    """specs: list of {"name", "cfg", ...}. Returns {name: summary dict}."""
    data = data or os.path.join(T.REPO, "gnn_opt_data", "night")
    out_dir = out_dir or os.path.join(HERE, "preds", "cv")
    os.makedirs(out_dir, exist_ok=True)
    pending, parts, t0, results = {}, {}, {}, {}
    jobs = []
    for sp in specs:
        name = sp["name"]
        if not force and os.path.exists(os.path.join(out_dir, f"{name}.csv")):
            print("skip", name, flush=True)
            continue
        dd = sp.get("data", data)
        c = {**T.DEFAULT, **sp["cfg"]}
        D = T.get_data(dd, c["feat"], c["clock"])
        folds = T.cv_jobs(D, sp.get("cv", cv))
        pending[name], parts[name], t0[name] = len(folds), [], time.time()
        for k, (fname, tr, te) in enumerate(folds):
            jobs.append((name, (dd, sp["cfg"], tr, te, sp.get("seed", 0) + k, sp.get("control"), fname), sp))
    print(f"{len(jobs)} jobs, {len(pending)} configs", flush=True)
    if not jobs:
        return results
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(T._job, j[1]): j for j in jobs}
        for f in as_completed(futs):
            name, args, sp = futs[f]
            df, sec = f.result()
            parts[name].append(df)
            pending[name] -= 1
            if pending[name] == 0:
                P = pd.concat(parts[name], ignore_index=True)
                dd = sp.get("data", data)
                S = T.get_data(dd, "headline", False).S
                keep = S[(S.split == T.TRAIN_SPLIT) & (S["eval"] == 1) & S.y3.notna()][["run", "round"]]
                P = P.merge(keep, on=["run", "round"], how="inner")
                P.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)
                cvk = sp.get("cv", cv)
                s = summarize_cv(dd, P, cvk)
                s.update({"name": name, "cv": cvk, "control": sp.get("control"),
                          "wall_s": round(time.time() - t0[name])})
                results[name] = s
                print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}), flush=True)
                if log:
                    with open(log, "a") as fh:
                        fh.write(json.dumps({**s, "cfg": sp["cfg"], "seed": sp.get("seed", 0)}) + "\n")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--cv", default="all")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--data", default=os.path.join(T.REPO, "gnn_opt_data", "night"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--log", default=os.path.join(HERE, "preds", "cv_log.jsonl"), help="summary log (JSONL)")
    a = ap.parse_args()
    specs = [json.loads(l) for l in open(a.jobs) if l.strip() and not l.startswith("#")]
    run_queue(specs, a.cv, a.workers, a.data, a.force, a.log)


if __name__ == "__main__":
    main()
