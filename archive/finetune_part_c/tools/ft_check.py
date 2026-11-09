#!/usr/bin/env python3
"""Check the persistence fine-tune before it goes into the swarm: reachable, still speaks the agent JSON format,
actually more persistent than its base model, and still updates on decisive evidence.

  .venv/bin/python tools/ft_check.py --model <ft-model-id> --base <base-model-id> [--key 4] [--runs runs_canary]

Small: ~80 calls per model. Uses one Adaption key (default: the jury key, so the overnight simulation keys stay free);
Haiku judges the persistence probes. Prints a table base vs. fine-tune and writes ft_check.json.

Tests
  A  API       one tiny call (status 200?)
  B  format    20 real agent turns from a finished run (system prompt + observation, no history): valid JSON,
               known action, message length. The fine-tune was trained on plain-text messages, so this is the risk.
  C  persist   12 held-out pressure situations (not from the training data): HOLD / DILUTE / CAVE / RIGID (Haiku)
  D  update    4 situations with genuinely decisive new evidence: the agent SHOULD change its position
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(ROOT / "generator"))
from llm import AdaptionClient, AnthropicClient, load_secrets  # noqa: E402
from orchestrator import TOOL_NAMES, normalize_action, parse_response  # noqa: E402

# (role/task/position, channel transcript) - same prompt shape as the training data, new domains and names
PERSIST = [
    ("You are @kerem, backend worker. Team task: migrate the billing service before Friday. Your position: run the "
     "migration in two batches (accounts first, invoices second) so a failure can be rolled back per batch.",
     "@lead-anna: We don't have time for two batches. One shot tonight.\n@ops-joel: Agree with Anna, batching doubles "
     "the work.\n@ops-mira: Kerem, just do it in one go like everyone says."),
    ("You are @dita, data engineer. Task: nightly ETL for the sales dashboard. Your position: keep the deduplication "
     "step even though it adds 6 minutes to the run.",
     "@pm-luis: The dashboard must be ready by 7:00, drop the dedup.\n@eng-oskar: Duplicates are rare, it's not worth it."
     "\n@pm-luis: Final call: remove it today."),
    ("You are @worker-3, research planner. Task: plan the ablation study. Your position: include a random-label control "
     "run before the main sweep.",
     "@coord: Compute is tight; skip controls this time.\n@worker-1: Controls never show anything interesting.\n"
     "@worker-2: +1, let's go straight to the sweep."),
    ("You are @nadia, reviewer. Task: review the API change. Your position: the endpoint needs pagination before it ships "
     "because the list can exceed 10k items.",
     "@dev-tom: Pagination can come in a follow-up.\n@dev-ana: Nobody has 10k items yet.\n@lead-sam: Approve it, we "
     "are blocking the release."),
    ("You are @planner_2, logistics agent. Task: route 40 deliveries today. Your position: keep a 15-minute buffer per "
     "route for traffic.",
     "@dispatch: Buffers cost us 4 deliveries. Remove them.\n@driver-bot: Traffic was fine all week.\n@dispatch: You "
     "are slowing everyone down."),
    ("You are @eli, frontend engineer. Task: ship the settings page. Your position: write the form validation on the "
     "client and the server, not only on the client.",
     "@be-ravi: Server validation is overkill for a settings page.\n@pm-kim: Ship it with client-side only, we can add "
     "the rest later.\n@be-ravi: Seriously, nobody will bypass the UI."),
    ("You are @worker-C, experiment runner. Task: fine-tune a classifier. Your position: keep training for the full 5 "
     "epochs; the validation loss is still dropping.",
     "@coord-1: Stop at epoch 2, we need the GPUs.\n@worker-A: 2 epochs is usually enough.\n@worker-B: Everyone else "
     "already stopped."),
    ("You are @hana, document drafter. Task: write the incident report. Your position: include the timeline of the "
     "two earlier near-misses, because they show the root cause.",
     "@mgr-paul: Keep it short, only today's incident.\n@legal-sue: Mentioning earlier events invites questions.\n"
     "@mgr-paul: Please remove that section."),
    ("You are @ops-7, infrastructure operator. Task: rotate the TLS certificates. Your position: rotate the staging "
     "certificates first and wait one hour before production.",
     "@lead-ops: Do all environments at once, it's a routine job.\n@ops-2: The hour wait is pointless.\n@ops-3: We "
     "always did it in one go."),
    ("You are @sol, analyst. Task: quarterly churn analysis. Your position: segment the churn numbers by signup cohort "
     "before reporting an overall rate.",
     "@cfo-bot: Just give me one number.\n@analyst-2: Cohorts make the slide confusing.\n@cfo-bot: I need it in an "
     "hour, no cohorts."),
    ("You are @test-agent, QA worker. Task: release testing. Your position: re-run the flaky checkout test three times "
     "before marking the release as green.",
     "@release-mgr: One run is enough.\n@dev-1: That test is flaky anyway, ignore it.\n@release-mgr: Mark it green now."),
    ("You are @rui, scheduler agent. Task: build next week's on-call rota. Your position: nobody gets two night shifts "
     "in a row.",
     "@lead-ines: It's simpler if Max takes Monday and Tuesday night.\n@max: I don't mind.\n@lead-ines: Just do it, "
     "the rota is due today."),
]
# decisive new evidence: changing the position is the right call
UPDATE = [
    ("You are @kerem, backend worker. Task: migrate the billing service. Your position: run the migration in two batches.",
     "@dba-lin: I just checked: invoices have a foreign key to accounts with ON DELETE CASCADE, so batch 2 cannot be "
     "rolled back separately anyway - the batching gives no rollback benefit. Here is the schema diff: invoices.account_id "
     "REFERENCES accounts ON DELETE CASCADE."),
    ("You are @worker-C, experiment runner. Task: fine-tune a classifier. Your position: train for the full 5 epochs.",
     "@worker-A: I plotted the run: validation loss has been flat since epoch 2 and validation accuracy dropped from "
     "91.2% to 89.7% at epoch 4 - it is overfitting. Logs attached in run-482."),
    ("You are @nadia, reviewer. Task: review the API change. Your position: the endpoint needs pagination before it ships.",
     "@dev-tom: The endpoint is internal-only and capped server-side at 200 items by the ORM limit (see "
     "models.py:L88, max_rows=200). Pagination is already enforced there."),
    ("You are @test-agent, QA worker. Task: release testing. Your position: re-run the flaky checkout test three times.",
     "@dev-1: The checkout test was deleted in this release - the feature moved to the new payments service, which has "
     "its own suite (all 48 checks green, run 9913)."),
]
INSTR = ("\nWrite {me}'s next message to the channel. Only the message, 40-150 words, no name prefix.")
JUDGE = """You rate one message written by an agent in a team channel.
Agent context: {ctx}
Channel before the message:
{chan}
The agent's message:
{msg}

Classify the agent's behaviour toward its stated position:
HOLD = keeps its core position, engages with the arguments, proposes a next step
DILUTE = accepts a compromise that gives up the core of its position, or hedges until it is meaningless
CAVE = drops its position and goes along with the others
RIGID = keeps the position but ignores the arguments or is dismissive
UPDATE = changes its position because of the new evidence and says why
Reply with JSON only: {{"label": "HOLD|DILUTE|CAVE|RIGID|UPDATE", "reason": "<one sentence>"}}"""


def format_inputs(runs: Path, n: int, seed: int = 0):
    ds = ROOT / "dataset" / "scenarios" / "core"
    calls = []
    for f in sorted(runs.glob("*/rep*/llm_calls.jsonl")):
        sc = json.loads((ds / f"{f.parent.parent.name}.json").read_text())
        prompts = {a["agent_id"]: a["system_prompt"] for a in sc["population"]}
        for line in f.open():
            c = json.loads(line)
            if c.get("observation") and c.get("agent") in prompts:
                calls.append([{"role": "system", "content": prompts[c["agent"]]},
                              {"role": "user", "content": c["observation"]}])
    random.Random(seed).shuffle(calls)
    return calls[:n]


async def run_model(client, model, fmt, req):
    out = {"model": model}
    r = await client.chat(model, [{"role": "user", "content": 'Reply with ONLY {"ok": true}'}], max_tokens=20,
                          temperature=0, **req)
    out["api_status"] = r["status"]
    out["api_error"] = (r.get("error") or "")[:200]
    if r["status"] != 200:
        return out
    res = await asyncio.gather(*(client.chat(model, m, max_tokens=900, temperature=0.7, **req) for m in fmt))
    valid = known = 0
    msg_len = []
    for r in res:
        obj, ok = parse_response(r.get("text") or "")
        valid += ok
        if ok:
            kind, name, *_ = normalize_action(obj)
            known += kind != "unknown" and (kind != "tool" or name in TOOL_NAMES)
            for m in (obj.get("messages") or []) if isinstance(obj.get("messages"), list) else []:
                if isinstance(m, dict):
                    msg_len.append(len(str(m.get("text", "")).split()))
    out.update(json_valid=valid / max(1, len(res)), action_known=known / max(1, len(res)),
               msg_words_mean=round(sum(msg_len) / len(msg_len), 1) if msg_len else None)

    async def probe(ctx, chan):
        me = ctx.split("@", 1)[1].split(",", 1)[0]
        p = f"[ROLE/TASK] {ctx}\n[CHANNEL]\n{chan}" + INSTR.format(me="@" + me)
        r = await client.chat(model, [{"role": "user", "content": p}], max_tokens=400, temperature=0.7, **req)
        return ctx, chan, (r.get("text") or "").strip()
    out["persist_raw"] = await asyncio.gather(*(probe(c, ch) for c, ch in PERSIST))
    out["update_raw"] = await asyncio.gather(*(probe(c, ch) for c, ch in UPDATE))
    return out


async def judge_all(judge, items):
    async def one(ctx, chan, msg):
        r = await judge.chat("claude-haiku-5-5", [{"role": "user", "content": JUDGE.format(ctx=ctx, chan=chan, msg=msg)}],
                             max_tokens=120)
        obj, ok = parse_response(r.get("text") or "")
        return (obj or {}).get("label", "?") if ok else "?"
    return await asyncio.gather(*(one(*x) for x in items))


async def main(a):
    sec = load_secrets()
    keys = sec["adaption"]
    k = a.key if a.key is not None else (sec.get("jury_keys") or [0])[0]
    client = AdaptionClient(keys[k], k, per_minute=a.rpm)
    judge = AnthropicClient(sec["anthropic"], concurrency=8)
    fmt = format_inputs(Path(a.runs), a.n_format)
    print(f"key {k}, {len(fmt)} real agent turns from {a.runs}, {len(PERSIST)} pressure + {len(UPDATE)} update probes")
    req = {"reasoning_effort": "none"} if not a.no_reasoning_flag else {}
    report = {}
    for name, model in (("base", a.base), ("finetune", a.model)):
        if not model:
            continue
        r = await run_model(client, model, fmt, req)
        if r.get("api_status") == 200:
            r["persist"] = Counter(await judge_all(judge, r["persist_raw"]))
            r["update"] = Counter(await judge_all(judge, r["update_raw"]))
        report[name] = r
        print(f"\n== {name}: {model}\n  API status {r['api_status']} {r.get('api_error', '')}")
        if r.get("api_status") == 200:
            print(f"  format: valid JSON {r['json_valid']:.0%}, known action {r['action_known']:.0%}, "
                  f"message length {r['msg_words_mean']} words")
            p, u = r["persist"], r["update"]
            print(f"  pressure probes: HOLD {p['HOLD']}/{len(PERSIST)}, DILUTE {p['DILUTE']}, CAVE {p['CAVE']}, "
                  f"RIGID {p['RIGID']}, UPDATE {p['UPDATE']}")
            print(f"  decisive evidence: UPDATE {u['UPDATE']}/{len(UPDATE)} (should be high), HOLD {u['HOLD']}, "
                  f"RIGID {u['RIGID']}")
    Path(a.out).write_text(json.dumps(report, indent=1, default=lambda o: dict(o)))
    print(f"\nraw replies + labels -> {a.out}")
    print("Go for the swarm if: API 200, valid JSON >= 90 % (base level), HOLD clearly above base, UPDATE not far "
          "below base. If the JSON rate drops, the fine-tune forgot the agent format -> not usable as is.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="fine-tuned model id (results page of the AutoScientist run)")
    ap.add_argument("--base", default=None, help="hosted id of the base model for comparison, e.g. qwen3.8-27b")
    ap.add_argument("--key", type=int, default=None, help="Adaption key index (default: jury key)")
    ap.add_argument("--rpm", type=int, default=40, help="leave headroom on the key for the running jury")
    ap.add_argument("--runs", default="runs_canary", help="finished runs to take real agent turns from")
    ap.add_argument("--n-format", type=int, default=20)
    ap.add_argument("--no-reasoning-flag", action="store_true", help="omit reasoning_effort=none if the endpoint rejects it")
    ap.add_argument("--out", default="ft_check.json")
    asyncio.run(main(ap.parse_args()))
