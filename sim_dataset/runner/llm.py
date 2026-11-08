"""LLM clients (stdlib HTTP; certifi optional).

- AdaptionClient: OpenAI-compatible POST {base}/chat/completions, one client per API key, sliding-window rate
  limiter (default 95/min, the endpoint allows 100/min per key), retries on 429/5xx/network with backoff.
- AnthropicClient: POST https://api.anthropic.com/v1/messages (Haiku 5.5 judge), retries on 429/529/5xx.
- load_secrets(): keys come ONLY from secrets.local.json or environment variables - never from code or chat.

All clients return a dict: {text, usage, latency, status, error, attempts, key}.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # pragma: no cover
    SSL_CTX = ssl.create_default_context()

# Prefer IPv4: api.anthropic.com resolves to IPv6 first. On networks with broken IPv6 every new connection hung until
# the OS connect timeout (~75 s) before falling back to IPv4 - each Haiku call took 76 s (seen 8 Nov). urllib opens a
# new connection per request, so this hit every call. IPv6 is still tried if no IPv4 address works.
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4_first(*args, **kwargs):
    return sorted(_orig_getaddrinfo(*args, **kwargs), key=lambda r: r[0] != socket.AF_INET)


socket.getaddrinfo = _getaddrinfo_ipv4_first

ROOT = Path(__file__).resolve().parents[1]
ADAPTION_BASE = os.environ.get("ADAPTION_BASE_URL", "https://api.prod.adaptionlabs.ai/api/v1").rstrip("/")
ANTHROPIC_BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip("/")


def load_secrets(path: Path | None = None) -> dict:
    """secrets.local.json: {"adaption": ["pt_live_...", ...], "anthropic": "sk-ant-..."}
    or env: ADAPTION_API_KEYS="k1,k2,k3" (or ADAPTION_API_KEY), ANTHROPIC_API_KEY."""
    path = path or ROOT / "secrets.local.json"
    sec = {"adaption": [], "anthropic": None, "jury_keys": []}
    if path.exists():
        d = json.loads(path.read_text())
        sec["adaption"] = [k for k in d.get("adaption", []) if k and not k.startswith("pt_live_KEY")]
        anth = d.get("anthropic") or ""
        sec["anthropic"] = anth if anth.startswith("sk-ant-") and anth != "sk-ant-..." else None
        sec["jury_keys"] = [i for i in d.get("jury_keys", []) if isinstance(i, int) and i < len(sec["adaption"])]
    env_keys = os.environ.get("ADAPTION_API_KEYS") or os.environ.get("ADAPTION_API_KEY") or ""
    if env_keys and not sec["adaption"]:
        sec["adaption"] = [k.strip() for k in env_keys.split(",") if k.strip()]
    sec["anthropic"] = sec["anthropic"] or os.environ.get("ANTHROPIC_API_KEY")
    return sec


def _post(url: str, headers: dict, body: dict, timeout: float):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            hdr = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, json.loads(resp.read().decode() or "{}"), hdr
    except urllib.error.HTTPError as e:
        hdr = {k.lower(): v for k, v in e.headers.items()}
        return e.code, {"error": e.read().decode(errors="replace")[:500]}, hdr
    except Exception as e:  # network errors, timeouts, bad JSON
        return None, {"error": repr(e)[:300]}, {}


class RateLimiter:
    """Sliding 60-second window; also honours server back-off after a 429."""

    def __init__(self, per_minute: int, window: float = 60.0):
        self.per_minute, self.window = per_minute, window
        self.times: deque = deque()
        self.lock = asyncio.Lock()
        self.blocked_until = 0.0

    async def acquire(self):
        while True:
            async with self.lock:
                now = time.monotonic()
                while self.times and now - self.times[0] >= self.window:
                    self.times.popleft()
                if now >= self.blocked_until and len(self.times) < self.per_minute:
                    self.times.append(now)
                    return
                if now < self.blocked_until:          # server asked us to back off
                    wait = self.blocked_until - now
                else:                                  # window full: wait until the oldest call leaves it
                    wait = self.window - (now - self.times[0]) + 0.05
            await asyncio.sleep(max(wait, 0.05))

    def block_for(self, seconds: float):
        self.blocked_until = max(self.blocked_until, time.monotonic() + seconds)


class ApiUnavailable(RuntimeError):
    """A call still failed after all retries for a transient reason (network down, 5xx, 429). The orchestrator
    aborts the episode instead of continuing with lost agent turns; run.py re-queues it once the API is back."""


def is_transient_failure(out: dict) -> bool:
    st = out.get("status")
    return st is None or st == 429 or st >= 500


class AdaptionClient:
    def __init__(self, key: str, idx: int, per_minute: int = 95, max_retries: int = 6, timeout: float = 180,
                 net_patience: float = 600):
        self.key, self.idx, self.timeout, self.max_retries = key, idx, timeout, max_retries
        self.net_patience = net_patience  # seconds of network errors (DNS, connect, timeout) tolerated per call
        self.limiter = RateLimiter(per_minute)
        self.server_limit = None
        self.stats = {"calls": 0, "errors": 0, "retries": 0, "input_tokens": 0, "output_tokens": 0}

    def _adapt_rate(self, hdr: dict):
        """Keys have different limits (seen: 100 and 20 req/min). Pace each key at 95 % of the limit the server
        reports in x-ratelimit-limit instead of bursting into 429s."""
        try:
            lim = int((hdr or {}).get("x-ratelimit-limit") or 0)
        except (TypeError, ValueError):
            return
        if lim > 0:
            self.server_limit = lim
            self.limiter.per_minute = min(self.limiter.per_minute, max(1, int(lim * 0.95)))

    async def chat(self, model: str, messages: list, **params) -> dict:
        body = {"model": model, "messages": messages, **params}
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        t0, attempt, st, js, hdr = time.time(), 0, None, {}, {}
        tries, net_since = 0, None
        while True:
            attempt += 1
            await self.limiter.acquire()
            st, js, hdr = await asyncio.to_thread(_post, f"{ADAPTION_BASE}/chat/completions", headers, body, self.timeout)
            self._adapt_rate(hdr)
            if st == 200:
                break
            if st is None:  # network error: keep waiting up to net_patience (short outages stay invisible)
                net_since = net_since or time.time()
                if time.time() - net_since > self.net_patience:
                    break
                self.stats["retries"] += 1
                await asyncio.sleep(min(2 ** min(attempt, 5), 30))
                continue
            net_since = None
            tries += 1
            if tries >= self.max_retries:
                break
            if st == 429:
                reset = hdr.get("retry-after") or hdr.get("x-ratelimit-reset")
                try:
                    r = float(reset)
                    wait = r - time.time() if r > 1e9 else r
                except (TypeError, ValueError):
                    wait = 10
                self.limiter.block_for(max(1.0, min(wait, 65)))
            elif st is not None and st < 500 and st != 408:
                break  # 4xx: not retryable (e.g. unsupported field)
            else:
                await asyncio.sleep(min(2 ** attempt, 30))
            self.stats["retries"] += 1
        self.stats["calls"] += 1
        out = {"status": st, "latency": round(time.time() - t0, 3), "attempts": attempt, "key": self.idx,
               "text": None, "usage": {}, "error": None}
        if st == 200:
            ch = (js.get("choices") or [{}])[0]
            out["text"] = (ch.get("message") or {}).get("content") or ""
            out["finish_reason"] = ch.get("finish_reason")
            out["usage"] = js.get("usage", {})
            self.stats["input_tokens"] += out["usage"].get("prompt_tokens", 0) or 0
            self.stats["output_tokens"] += out["usage"].get("completion_tokens", 0) or 0
        else:
            self.stats["errors"] += 1
            out["error"] = str(js.get("error"))[:500]
        return out


class AnthropicClient:
    def __init__(self, key: str, concurrency: int = 8, max_retries: int = 6, timeout: float = 120):
        self.key, self.timeout, self.max_retries = key, timeout, max_retries
        self.sem = asyncio.Semaphore(concurrency)
        self.stats = {"calls": 0, "errors": 0, "retries": 0, "input_tokens": 0, "output_tokens": 0}

    async def chat(self, model: str, messages: list, max_tokens: int = 600, temperature: float = 0.0, **_) -> dict:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        msgs = [m for m in messages if m["role"] != "system"]
        # `temperature` is deprecated for current Claude models (400 if sent) -> accepted but not forwarded.
        body = {"model": model, "max_tokens": max_tokens, "messages": msgs}
        if system:
            body["system"] = system
        headers = {"x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        t0, attempt, st, js, hdr = time.time(), 0, None, {}, {}
        async with self.sem:
            for attempt in range(1, self.max_retries + 1):
                st, js, hdr = await asyncio.to_thread(_post, f"{ANTHROPIC_BASE}/messages", headers, body, self.timeout)
                if st == 200:
                    break
                if st in (429, 529) or st is None or st >= 500:
                    try:
                        wait = float(hdr.get("retry-after", 2 ** attempt))
                    except ValueError:
                        wait = 2 ** attempt
                    self.stats["retries"] += 1
                    await asyncio.sleep(min(wait, 60))
                    continue
                break
        self.stats["calls"] += 1
        out = {"status": st, "latency": round(time.time() - t0, 3), "attempts": attempt, "key": "anthropic",
               "text": None, "usage": {}, "error": None}
        if st == 200:
            out["text"] = "".join(c.get("text", "") for c in js.get("content", []) if c.get("type") == "text")
            out["usage"] = js.get("usage", {})
            self.stats["input_tokens"] += out["usage"].get("input_tokens", 0) or 0
            self.stats["output_tokens"] += out["usage"].get("output_tokens", 0) or 0
        else:
            self.stats["errors"] += 1
            out["error"] = str(js.get("error"))[:500]
        return out
