"""Run a sweep spec (arms x seeds) in parallel with resume.

Spec (JSON):
{
  "out": "results/amx_phase1",
  "workers": 2,
  "seeds": [0, 1, 2],
  "base": {"data_dir": "...", "graph_target": "innocent_ejected", "node_target": "votes_innocent", ...},
  "arms": [{"arm": "GINE", "model": "gine"}, {"arm": "K0", "model": "none"}, ...]
}
Every key of an arm overrides "base" (flat keys of RunConfig / DataConfig). Finished run_ids in
<out>/results.jsonl are skipped, so an interrupted sweep can simply be restarted.
Usage: python -m gnn.sweep SPEC.json [--workers N] [--data DIR] [--dry]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import get_context


def expand(spec):
    runs = []
    for arm in spec["arms"]:
        for s in arm.get("seeds", spec.get("seeds", [0])):
            d = {**spec["base"], **{k: v for k, v in arm.items() if k != "seeds"}, "seed": s, "out": spec["out"],
                 "threads": 1}
            runs.append(d)
    return runs


def _work(d):
    import warnings
    warnings.filterwarnings("ignore")
    from .train import build_cfg, run
    try:
        r = run(build_cfg(d))
        return d.get("arm", ""), d["seed"], r["secs"], None
    except Exception as e:  # report and continue
        import traceback
        return d.get("arm", ""), d["seed"], 0, traceback.format_exc()[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--data", help="override base.data_dir")
    ap.add_argument("--out", help="override out")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    if a.data:
        spec["base"]["data_dir"] = a.data
    if a.out:
        spec["out"] = a.out
    from .train import build_cfg
    done = set()
    rp = os.path.join(spec["out"], "results.jsonl")
    if os.path.exists(rp):
        done = {json.loads(l)["run_id"] for l in open(rp) if l.strip()}
    todo = [d for d in expand(spec) if build_cfg(d).run_id() not in done]
    # group by data config so each worker reuses its loaded bundle
    todo.sort(key=lambda d: build_cfg(d).data.key())
    print(f"{len(todo)} runs to do ({len(done)} done) -> {spec['out']}", flush=True)
    if a.dry:
        for d in todo:
            print(d.get("arm"), d["seed"])
        return
    workers = a.workers or spec.get("workers", 1)
    t0 = time.time()
    ctx = get_context("fork")
    with ctx.Pool(workers, maxtasksperchild=None) as pool:
        for i, (arm, seed, secs, err) in enumerate(pool.imap_unordered(_work, todo, chunksize=1)):
            msg = f"[{i + 1}/{len(todo)}] {arm} seed={seed} {secs}s"
            if err:
                msg += f"\n  ERROR {err}"
            print(msg, f"(elapsed {time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
