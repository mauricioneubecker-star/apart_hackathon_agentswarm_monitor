#!/usr/bin/env python3
"""Run many (config x fold) CV jobs through one process pool (keeps all cores busy across configs).

  python3 gnn_opt_torch/queue_cv.py --jobs experiments/arch.jsonl --cv all --workers 4
jobs file: one JSON object per line: {"name": ..., "cfg": {...}, "control": null|"rewire"|..., "data": optional}
Each config's CV file is written to preds/cv/<name>.csv when its last fold finishes; the summary (harness selection
score etc.) is appended to preds/cv_log.jsonl. Configs whose CV file exists are skipped (resumable; --force).
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--cv", default="all")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--data", default=os.path.join(T.REPO, "gnn_opt_data", "night"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--target", default="y3")
    a = ap.parse_args()
    specs = [json.loads(l) for l in open(a.jobs) if l.strip() and not l.startswith("#")]
    out_dir = os.path.join(HERE, "preds", "cv")
    os.makedirs(out_dir, exist_ok=True)
    pending, parts, t0 = {}, {}, {}
    jobs = []
    for sp in specs:
        name = sp["name"]
        if not a.force and os.path.exists(os.path.join(out_dir, f"{name}.csv")):
            print("skip", name, flush=True)
            continue
        data = sp.get("data", a.data)
        c = {**T.DEFAULT, **sp["cfg"]}
        D = T.get_data(data, c["feat"], c["clock"])
        folds = T.cv_jobs(D, sp.get("cv", a.cv))
        pending[name], parts[name], t0[name] = len(folds), [], time.time()
        for k, (fname, tr, te) in enumerate(folds):
            jobs.append((name, (data, sp["cfg"], tr, te, sp.get("seed", 0) + k, sp.get("control"), fname), sp))
    print(f"{len(jobs)} jobs, {len(pending)} configs", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        futs = {ex.submit(T._job, j[1]): j for j in jobs}
        for f in as_completed(futs):
            name, args, sp = futs[f]
            df, sec = f.result()
            parts[name].append(df)
            pending[name] -= 1
            if pending[name] == 0:
                P = pd.concat(parts[name], ignore_index=True)
                data = sp.get("data", a.data)
                S = T.get_data(data, "headline", False).S
                keep = S[(S.split == T.TRAIN_SPLIT) & (S["eval"] == 1) & S.y3.notna()][["run", "round"]]
                P = P.merge(keep, on=["run", "round"], how="inner")
                P.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)
                cvk = sp.get("cv", a.cv)
                s = T.summarize(data, P) if cvk in ("all", "id0+lodo", "lodo") else {}
                if cvk in ("id", "id0"):
                    from sklearn.metrics import average_precision_score, roc_auc_score
                    Q = P.groupby(["run", "round"], as_index=False).score.mean().merge(S[["run", "round", "y3"]])
                    s = {"id_auroc": roc_auc_score(Q.y3, Q.score), "id_auprc": average_precision_score(Q.y3, Q.score)}
                s.update({"name": name, "cv": cvk, "control": sp.get("control"),
                          "wall_s": round(time.time() - t0[name])})
                print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}), flush=True)
                with open(os.path.join(HERE, "preds", "cv_log.jsonl"), "a") as fh:
                    fh.write(json.dumps({**s, "cfg": sp["cfg"]}) + "\n")


if __name__ == "__main__":
    main()
