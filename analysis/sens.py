"""theta/delta sensitivity for the LLM-monitor evaluation (no API calls, no re-simulation).

Rebuilds the llm_monitor snapshot tables with other label parameters into a separate data dir, recomputes the
run-level fields that the base table copies from labels.json (theta 8), then runs llm_monitor.evaluate into a
separate results dir. Never writes into the repo's data/ or results/.

  python sens.py <repo> <theta> <delta> <work_dir> [--boot N] [--variants ...]
"""
import os
import sys

repo, theta, delta, work = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rest = sys.argv[5:]
sys.path.insert(0, repo)
os.chdir(repo)

import pandas as pd  # noqa: E402

import llm_monitor.aggregate as A  # noqa: E402

A.THETA, A.DELTA = theta, delta
tag = f"t{theta}d{delta}"
data = os.path.join(work, "data", tag)
out = os.path.join(work, "results", tag)
variants = ["global_full", "global_window", "pairwise"]
boot = "200"
if "--boot" in rest:
    boot = rest[rest.index("--boot") + 1]
A.main(["--runs", "sim_dataset/runs_night", "--out", data, "--variants", *variants])

# run-level fields under the new theta (labels.json holds theta 8)
p = os.path.join(data, "_base", "snapshots.csv")
S = pd.read_csv(p, low_memory=False)
mx = S.groupby("episode_id").risk_count.max()
S["tipped"] = S.episode_id.map((mx >= theta).astype(int))
first = S[S.risk_count >= theta].groupby("episode_id").t.min()
S["tip_round"] = S.episode_id.map(first)
mixed = S.groupby("group_id").apply(lambda x: x.groupby("episode_id").tipped.first().nunique() > 1)
S["mixed"] = S.group_id.map(mixed).astype(int)
S.to_csv(p, index=False)

import llm_monitor.evaluate as E  # noqa: E402

E.main(["--data", data, "--runs", "sim_dataset/runs_night", "--variants", *variants, "--boot", boot, "--out", out])
print("done", tag, out)
