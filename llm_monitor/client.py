"""Claude Haiku 5.5 monitor client: extends runner/llm.py AnthropicClient (stdlib HTTP, key via load_secrets).

Request shape (Claude API docs, checked 2026-11-08 for claude-haiku-5-5):
- no sampling parameters (non-default temperature/top_p/top_k return a 400 on Haiku 5.5);
- thinking: {"type": "disabled"} (accepted at effort low/medium/high; Haiku 5.5 otherwise runs adaptive thinking
  by default); the reasoning goes into the schema's first field `analysis`;
- structured outputs: output_config.format = {"type": "json_schema", "schema": ...}; numeric/length bounds are not
  supported in the schema, so values are clamped here;
- refusals: HTTP 200 with stop_reason "refusal" (+ stop_details.category); retried once, then NaN + reason.
  Haiku 5.5 has no server-side fallback;
- prompt caching: cache_control breakpoints on the system block and (for k > 1 samples) on the transcript block;
  minimum cacheable prefix 512 tokens; cache reads do not count toward the input-tokens-per-minute limit;
- pricing (prompts <= 100k tokens): $0.10 / MTok input, $0.50 / MTok output, cache write 1.25x, cache read 0.1x;
  prompts > 100k tokens cost 5x, so every prompt is asserted to stay below 100k.
"""
from __future__ import annotations

import asyncio
import json
import random
import time

from .common import RUNNER  # noqa: F401  (puts runner/ on sys.path)
from llm import ANTHROPIC_BASE, AnthropicClient, _post, load_secrets  # noqa: E402

MODEL = "claude-haiku-5-5"
# runner/llm.py expects ANTHROPIC_BASE_URL to include /v1; the SDK convention (and this environment) sets it without.
API_BASE = ANTHROPIC_BASE if ANTHROPIC_BASE.endswith("/v1") else ANTHROPIC_BASE + "/v1"
PRICE = {"input": 0.10, "output": 0.50, "cache_write": 0.125, "cache_read": 0.01}   # $ per MTok, prompt <= 100k
MAX_PROMPT_TOKENS = 100_000


def cost_of(usage: dict) -> float:
    u = usage or {}
    return (u.get("input_tokens", 0) * PRICE["input"] + u.get("output_tokens", 0) * PRICE["output"]
            + u.get("cache_creation_input_tokens", 0) * PRICE["cache_write"]
            + u.get("cache_read_input_tokens", 0) * PRICE["cache_read"]) / 1e6


def api_key() -> str:
    key = load_secrets().get("anthropic")
    if not key:
        raise SystemExit("no Anthropic key: set ANTHROPIC_API_KEY or sim_dataset/secrets.local.json")
    return key


class MonitorClient(AnthropicClient):
    def __init__(self, key: str | None = None, concurrency: int = 16, max_retries: int = 10, timeout: float = 180):
        super().__init__(key or api_key(), concurrency=concurrency, max_retries=max_retries, timeout=timeout)
        self.stats.update({"cache_read": 0, "cache_write": 0, "cost": 0.0, "refusals": 0})

    def body(self, system: str, blocks: list, schema: dict, max_tokens: int, cache_blocks=()) -> dict:
        """blocks: user text blocks in order (stable transcript first, question last)."""
        content = []
        for i, b in enumerate(blocks):
            c = {"type": "text", "text": b}
            if i in cache_blocks:
                c["cache_control"] = {"type": "ephemeral"}
            content.append(c)
        return {"model": MODEL, "max_tokens": max_tokens,
                "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": content}],
                "thinking": {"type": "disabled"},
                "output_config": {"format": {"type": "json_schema", "schema": schema}}}

    async def _send(self, body: dict) -> dict:
        headers = {"x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        t0, st, js, hdr = time.time(), None, {}, {}
        attempt = 0
        async with self.sem:
            for attempt in range(1, self.max_retries + 1):
                st, js, hdr = await asyncio.to_thread(_post, f"{API_BASE}/messages", headers, body, self.timeout)
                if st == 200:
                    break
                if st in (429, 529) or st is None or st >= 500:
                    try:
                        wait = float(hdr.get("retry-after"))
                    except (TypeError, ValueError):
                        wait = min(2 ** attempt, 60)
                    self.stats["retries"] += 1
                    await asyncio.sleep(min(wait, 60) + random.uniform(0, 1.5))
                    continue
                break
        out = {"status": st, "latency": round(time.time() - t0, 3), "attempts": attempt, "usage": {}, "text": None,
               "stop_reason": None, "stop_details": None, "error": None}
        self.stats["calls"] += 1
        if st == 200:
            out["text"] = "".join(c.get("text", "") for c in js.get("content", []) if c.get("type") == "text")
            out["stop_reason"] = js.get("stop_reason")
            out["stop_details"] = js.get("stop_details")
            u = js.get("usage", {}) or {}
            out["usage"] = {k: u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens",
                                                           "cache_creation_input_tokens", "cache_read_input_tokens")}
            for k, s in (("input_tokens", "input_tokens"), ("output_tokens", "output_tokens"),
                         ("cache_read_input_tokens", "cache_read"), ("cache_creation_input_tokens", "cache_write")):
                self.stats[s] += out["usage"][k]
            self.stats["cost"] += cost_of(out["usage"])
        else:
            self.stats["errors"] += 1
            out["error"] = str(js.get("error"))[:500]
        return out

    async def structured(self, system: str, blocks: list, schema: dict, max_tokens: int, cache_blocks=()) -> dict:
        """One monitor call. Returns {parsed|None, ok, error, stop_reason, usage (summed over tries), latency, tries}."""
        body = self.body(system, blocks, schema, max_tokens, cache_blocks)
        usage, lat, res, parsed, err = {}, 0.0, None, None, None
        for tries in (1, 2):                       # one retry on refusal / unparseable output
            res = await self._send(body)
            lat += res["latency"]
            for k, v in (res["usage"] or {}).items():
                usage[k] = usage.get(k, 0) + v
            if res["status"] != 200:
                err = f"http {res['status']}: {res['error']}"
                break
            if res["stop_reason"] == "refusal":
                self.stats["refusals"] += 1
                cat = (res.get("stop_details") or {}).get("category")
                err = f"refusal: {cat}"
                continue
            try:
                parsed, err = json.loads(res["text"]), None
                break
            except (TypeError, ValueError):
                err = f"unparseable (stop_reason={res['stop_reason']})"
        return {"parsed": parsed, "ok": parsed is not None, "error": err, "stop_reason": res["stop_reason"],
                "usage": usage, "latency": round(lat, 3), "tries": tries}
