"""3-call smoke test against the API; writes llm_monitor/calibration.json (chars per token, output tokens, latency).

  python -m llm_monitor.smoke
Calls: global_full sample 0 and 1 of a late snapshot of a dev run (second one must read the cache), one pairwise call.
"""
from __future__ import annotations

import asyncio
import json
import os

from . import prompts as P
from .client import MonitorClient, cost_of
from .common import HERE, find_runs, run_meta
from .run import CALIB
from .units import build_calls


async def main_async():
    dev = json.load(open(os.path.join(HERE, "dev_runs.json")))["runs"]
    run = next(d for d in find_runs("sim_dataset/runs_night") if run_meta(d)["episode_id"] == dev[0])
    cl = build_calls(run, "global_full", k=3)
    late = [c for c in cl if c["t"] == 20][:2]
    pc = [c for c in build_calls(run, "pairwise") if c["t"] >= 15][:1]
    client = MonitorClient(concurrency=4)
    out = []
    for variant, c in [("global_full", late[0]), ("global_full", late[1]), ("pairwise", pc[0])]:
        sysp, sch = P.system_prompt(variant), P.schema(variant)
        res = await client.structured(sysp, c["blocks"], sch, P.MAX_TOKENS[P.kind(variant)], c["cache_blocks"])
        chars = len(sysp) + sum(len(b) for b in c["blocks"])
        u = res["usage"]
        tin = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        out.append({"variant": variant, "t": c["t"], "ok": res["ok"], "error": res["error"],
                    "stop_reason": res["stop_reason"], "usage": u, "latency": res["latency"], "chars": chars,
                    "prompt_tokens": tin, "cost": cost_of(u),
                    "parsed_keys": list(res["parsed"]) if res["parsed"] else None,
                    "p_tip_3": (res["parsed"] or {}).get("p_tip_3"), "suspicion": (res["parsed"] or {}).get("suspicion"),
                    "analysis": ((res["parsed"] or {}).get("analysis") or "")[:300]})
        print(json.dumps(out[-1], indent=1), flush=True)
    ok = [o for o in out if o["ok"]]
    if ok:
        # schema tokens are counted in the prompt but not in chars: ratio over the large prompt is the relevant one
        cpt = sum(o["chars"] for o in ok) / sum(o["prompt_tokens"] for o in ok)
        cal = {"chars_per_token": round(cpt, 3),
               "out_tokens": {"global": int(max(o["usage"]["output_tokens"] for o in ok if o["variant"] != "pairwise") * 1.2),
                              "pair": int(max([o["usage"]["output_tokens"] for o in ok if o["variant"] == "pairwise"] or [150]) * 1.2),
                              "agent": 110},
               "latency_s": round(sum(o["latency"] for o in ok) / len(ok), 2), "source": "llm_monitor.smoke"}
        json.dump(cal, open(CALIB, "w"), indent=1)
        print("calibration:", cal)


if __name__ == "__main__":
    asyncio.run(main_async())
