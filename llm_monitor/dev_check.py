"""Prompt-development check on the 8 dev runs only: parse rate, refusal rate, sanity plot p_tip_3 vs rounds-to-theta.

  python -m llm_monitor.dev_check [--variants global_full global_window pairwise agent] [--tag r0]
Writes results/llm_monitor/dev/<tag>_summary.json and <tag>_sanity.png. Nothing here uses val, test or vx runs.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

from . import prompts as P
from .aggregate import GLOBAL_VARIANTS, base_frames, read_rows, variant_tables
from .common import HERE, REPO, find_runs, run_meta


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="*", default=["global_full", "global_window", "pairwise", "agent"])
    ap.add_argument("--tag", default="r0")
    a = ap.parse_args(argv)
    dev = set(json.load(open(os.path.join(HERE, "dev_runs.json")))["runs"])
    runs = [d for d in find_runs(os.path.join(REPO, "sim_dataset", "runs_night")) if run_meta(d)["episode_id"] in dev]
    base, _ = base_frames(runs)
    out_dir = os.path.join(REPO, "results", "llm_monitor", "dev")
    os.makedirs(out_dir, exist_ok=True)
    summ = {}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_auc_score
    fig, axes = plt.subplots(1, len(a.variants), figsize=(4 * len(a.variants), 3.4), squeeze=False)
    for ax, v in zip(axes[0], a.variants):
        rows = [r for d in runs for r in read_rows(d, v)]
        n = len(rows)
        ok = sum(bool(r.get("ok")) for r in rows)
        ref = sum(str(r.get("error", "")).startswith("refusal") for r in rows)
        errs = pd.Series([str(r.get("error"))[:60] for r in rows if not r.get("ok")]).value_counts().head(5).to_dict()
        S, _, _ = variant_tables(base, runs, v)
        s = {"prompt_version": P.version(v), "calls": n, "parse_ok_rate": ok / n if n else None,
             "refusal_rate": ref / n if n else None, "errors": errs}
        if S is not None:
            M = base.merge(S[["episode_id", "t", "zs_tip", "zs_count"]], on=["episode_id", "t"])
            m = M.tip.notna() & M.zs_tip.notna()
            if m.any() and 0 < M.tip[m].sum() < m.sum():
                s["dev_auroc_zs_tip"] = float(roc_auc_score(M.tip[m], M.zs_tip[m]))
            s["dev_count_mae"] = float((M.zs_count - M.risk_count).abs().mean())
            s["mean_zs_tip_pos"] = float(M.zs_tip[m & (M.tip == 1)].mean())
            s["mean_zs_tip_neg"] = float(M.zs_tip[m & (M.tip == 0)].mean())
            # rounds to theta (tipped runs) / to the cut (untipped)
            M["rel"] = np.where(M.tipped == 1, M.t - M.tip_round, M.t - M.cut)
            for tipped, g in M.groupby("tipped"):
                gg = g.groupby("rel").zs_tip.mean()
                ax.plot(gg.index, gg.values * 100, "-o" if tipped else "--", ms=3,
                        label="tipped (x = t - tip round)" if tipped else "not tipped (x = t - cut)")
            ax.axvline(0, color="grey", lw=0.6)
            ax.set_title(f"{v} (dev)", fontsize=9)
            ax.set_xlabel("rounds relative to tip / cut")
            ax.set_ylabel("p_tip_3" if v in GLOBAL_VARIANTS else "max suspicion")
            ax.legend(fontsize=6)
        summ[v] = s
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"{a.tag}_sanity.png"), dpi=130)
    json.dump(summ, open(os.path.join(out_dir, f"{a.tag}_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
