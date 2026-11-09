#!/usr/bin/env python3
"""Step 2: zero-shot LLM monitors -> harness CV files, exactly like gnn_opt_torch/llm_monitor.py --to-cv.

The zero-shot monitor is untrained, so every fold (id and lodo) gets the same score. Logic copied from
llm_monitor.py --to-cv:
    for kind in ("id", "lodo"):
        for name, cfgs in F[kind].items():
            m = S[S.cfg.isin(cfgs) & (S.split == "night_train")][["run", "round"]]
            out.append(m.merge(done, on=["run", "round"]).assign(fold=name))
    pd.concat(out).dropna(subset=["score"]).to_csv(...)
where `done` = the scored rows (llm_monitor.py scores only eval == 1 rows of the requested splits), here
run = episode_id, round = t, score = zs_tip from data/llm_monitor/<variant>/snapshots.csv.

Then: key-coverage check against the harness eval == 1 night_train rows and against the GNN CV file.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="harness dataset dir (snapshots.csv)")
    ap.add_argument("--folds", required=True)
    ap.add_argument("--llm-root", required=True)
    ap.add_argument("--variants", default="pairwise,global_full,global_window")
    ap.add_argument("--ref-cv", required=True, help="a GNN CV file to compare key sets with (final.csv)")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    S = pd.read_csv(os.path.join(a.data, "snapshots.csv"), low_memory=False)
    F = json.load(open(a.folds))
    lab = S[(S.split == "night_train") & (S["eval"] == 1) & S.y3.notna()]
    print(f"harness eval rows on night_train: {len(lab)} rows, {int(lab.y3.sum())} positives, "
          f"{lab.cfg.nunique()} configs, {lab.run.nunique()} runs")
    # reference key set: every (run, round, fold) the harness scores
    ref = []
    for kind in ("id", "lodo"):
        for name, cfgs in F[kind].items():
            ref.append(lab[lab.cfg.isin(cfgs)][["run", "round"]].assign(fold=name))
    ref = pd.concat(ref, ignore_index=True)
    ref_keys = set(map(tuple, ref[["run", "round", "fold"]].values.tolist()))
    print(f"reference (run, round, fold) keys: {len(ref_keys)} "
          f"(id: {int(ref.fold.str.startswith('id').sum())}, lodo: {int((~ref.fold.str.startswith('id')).sum())})")
    G = pd.read_csv(a.ref_cv)
    g_ok = G.merge(lab[["run", "round"]], on=["run", "round"], how="inner")
    g_keys = set(map(tuple, g_ok[["run", "round", "fold"]].values.tolist()))
    print(f"GNN file {os.path.basename(a.ref_cv)}: {len(G)} rows, {len(g_keys)} keys on eval rows, "
          f"missing vs reference {len(ref_keys - g_keys)}, extra {len(g_keys - ref_keys)}")

    report = {}
    for v in a.variants.split(","):
        V = pd.read_csv(os.path.join(a.llm_root, v, "snapshots.csv"), low_memory=False)
        V = V.rename(columns={"episode_id": "run", "t": "round", "zs_tip": "score"})[["run", "round", "score"]]
        assert not V.duplicated(["run", "round"]).any()
        # rows llm_monitor.py would have scored: eval == 1 rows of night_train
        scored = S[(S.split == "night_train") & (S["eval"] == 1)][["run", "round"]]
        done = scored.merge(V, on=["run", "round"], how="left")
        n_nan_done = int(done.score.isna().sum())
        out = []
        for kind in ("id", "lodo"):
            for name, cfgs in F[kind].items():
                m = S[S.cfg.isin(cfgs) & (S.split == "night_train")][["run", "round"]]
                out.append(m.merge(done, on=["run", "round"]).assign(fold=name))
        C = pd.concat(out)
        n_nan_cv = int(C.score.isna().sum())
        C = C.dropna(subset=["score"])
        path = os.path.join(a.out_dir, f"zs_{v}.csv")
        C[["run", "round", "score", "fold"]].to_csv(path, index=False)
        c_keys = set(map(tuple, C[["run", "round", "fold"]].values.tolist()))
        # identical scores in every fold?
        sd = C.groupby(["run", "round"]).score.agg(lambda x: x.max() - x.min()).max()
        r = {"rows": len(C), "keys": len(c_keys), "missing_vs_harness": len(ref_keys - c_keys),
             "extra_vs_harness": len(c_keys - ref_keys), "missing_vs_gnn": len(g_keys - c_keys),
             "extra_vs_gnn": len(c_keys - g_keys), "nan_scores_on_eval_rows": n_nan_done,
             "nan_rows_dropped": n_nan_cv, "max_within_key_score_range_across_folds": float(sd),
             "score_min": float(C.score.min()), "score_max": float(C.score.max()),
             "distinct_scores": int(C.score.nunique())}
        report[v] = r
        print(f"zs_{v}: {json.dumps(r)}")
    json.dump(report, open(os.path.join(a.out_dir, "zs_cv_coverage.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
