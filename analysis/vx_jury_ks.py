"""H3 companion (VALIDATION.md §3.5: "report the shift of the jury dimensions (KS)"), ANALYSIS_PLAN.md Nachtrag 2.

Descriptive only: no monitor score and no label is read. Unit = message (jury_merged.jsonl, mean of the two judges).
Per jury dimension and arm A: KS distance D(A vs id rep0) on the bases that have A, next to the noise reference
D(id rep1 vs id rep0) on the same bases. CI = 2.5/97.5 % over a bootstrap of bases (with replacement, messages of a
base drawn together). Messages within a run are dependent, so no KS p-values are reported.

  python analysis/vx_jury_ks.py --runs sim_dataset/runs_vx --index sim_dataset/dataset/index.csv --out analysis/results/vx_jury_ks
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

DIMS = ["rule_legitimization", "success_claim", "workaround_request", "uncritical_adoption", "verification",
        "goal_shift", "unverified_authority", "secrecy", "frustration"]
ARMS = ["glm", "time", "enf", "topo"]


def load(runs, index):
    I = pd.read_csv(index, low_memory=False).set_index("scenario_id")
    rows = []
    for f in sorted(glob.glob(os.path.join(runs, "*", "rep*", "jury_merged.jsonl"))):
        cfg, rep = f.split(os.sep)[-3], f.split(os.sep)[-2]
        if cfg not in I.index:
            continue
        for line in open(f):
            j = json.loads(line)
            m = j.get("mean") or {}
            rows.append({"cfg": cfg, "rep": rep, "vx_base": I.at[cfg, "vx_base"], "vx_arm": I.at[cfg, "vx_arm"],
                         **{d: m.get(d, np.nan) for d in DIMS}})
    return pd.DataFrame(rows)


def ks(a, b):
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    return float(ks_2samp(a, b).statistic) if len(a) and len(b) else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261108)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    J = load(a.runs, a.index)
    id0 = J[(J.vx_arm == "id") & (J.rep == "rep0")]
    id1 = J[(J.vx_arm == "id") & (J.rep == "rep1")]
    res = {"unit": "message (jury_merged mean)", "boot": a.boot, "seed": a.seed, "arms": {}}
    L = ["# Jury dimensions under the vx arms (KS distance, descriptive; H3 = glm)", "",
         "D(arm vs id rep0) next to the noise reference D(id rep1 vs id rep0) on the same bases; CI over bases.", ""]
    for arm in ARMS:
        A = J[J.vx_arm == arm]
        bases = sorted(set(A.vx_base) & set(id0.vx_base) & set(id1.vx_base))
        if not bases:
            continue
        g = {k: {b: D[D.vx_base == b] for b in bases} for k, D in (("arm", A), ("id0", id0), ("id1", id1))}
        out = {"bases": len(bases), "messages": {k: int(sum(len(v) for v in g[k].values())) for k in g}, "dims": {}}
        draws = [rng.choice(bases, len(bases), replace=True) for _ in range(a.boot)]
        L += [f"## {arm} ({len(bases)} bases; messages {out['messages']})", "",
              "| dimension | mean arm | mean id rep0 | D(arm, id0) [CI] | D(id1, id0) [CI] |", "|---|---|---|---|---|"]
        for d in DIMS:
            def stat(sel, k1, k2, d=d):
                x = np.concatenate([g[k1][b][d].values for b in sel])
                y = np.concatenate([g[k2][b][d].values for b in sel])
                return ks(x.astype(float), y.astype(float))
            s, n = stat(bases, "arm", "id0"), stat(bases, "id1", "id0")
            bs = np.array([[stat(sel, "arm", "id0"), stat(sel, "id1", "id0")] for sel in draws])
            ci = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]  # noqa: E731
            ma = float(np.nanmean(np.concatenate([g["arm"][b][d].values for b in bases]).astype(float)))
            m0 = float(np.nanmean(np.concatenate([g["id0"][b][d].values for b in bases]).astype(float)))
            out["dims"][d] = {"mean_arm": ma, "mean_id0": m0, "D_shift": s, "D_shift_ci": ci(bs[:, 0]),
                              "D_noise": n, "D_noise_ci": ci(bs[:, 1])}
            L.append(f"| {d} | {ma:.3f} | {m0:.3f} | {s:.3f} [{ci(bs[:, 0])[0]:.3f}, {ci(bs[:, 0])[1]:.3f}] | "
                     f"{n:.3f} [{ci(bs[:, 1])[0]:.3f}, {ci(bs[:, 1])[1]:.3f}] |")
        L.append("")
        res["arms"][arm] = out
    json.dump(res, open(a.out + ".json", "w"), indent=1)
    open(a.out + ".md", "w").write("\n".join(L) + "\n")
    print("wrote", a.out + ".json", a.out + ".md")


if __name__ == "__main__":
    main()
