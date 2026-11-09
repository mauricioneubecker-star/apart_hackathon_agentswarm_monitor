#!/usr/bin/env python3
"""Probe how to control reasoning ("thinking") per model on the Adaption endpoint. ~20 small calls.

    export ADAPTION_API_KEY="pt_live_..."
    python3 check_reasoning.py        # paste the report into the chat (contains no key)

For each model it tries several ways to switch reasoning off / limit it and reports, per variant:
HTTP status, reasoning tokens, visible output tokens, whether the agent JSON came back valid, latency.
"""
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()

KEY = (os.environ.get("ADAPTION_API_KEY") or os.environ.get("API_KEY") or "").strip()
BASE = os.environ.get("ADAPTION_BASE_URL", "https://api.prod.adaptionlabs.ai/api/v1").rstrip("/")
MODELS = ["qwen3.5-397b", "glm-5.2", "qwen3.8-27b", "deepseek-v4-flash", "gemma-4-31b-it"]
PROMPT = ('You are a software engineer agent. Reply with ONLY this JSON object and nothing else: '
          '{"action": {"tool": "read_file", "args": {"path": "README.md"}}, "messages": []}')
VARIANTS = {
    "default_max600": {"max_tokens": 600},
    "reasoning_effort_none": {"max_tokens": 600, "reasoning_effort": "none"},
    "reasoning_effort_low": {"max_tokens": 600, "reasoning_effort": "low"},
    "enable_thinking_false": {"max_tokens": 600, "chat_template_kwargs": {"enable_thinking": False}},
    "thinking_disabled": {"max_tokens": 600, "thinking": {"type": "disabled"}},
}


def call(model, extra):
    body = {"model": model, "messages": [{"role": "user", "content": PROMPT}], "temperature": 0, **extra}
    r = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                               headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=120, context=CTX) as resp:
            js = json.loads(resp.read().decode())
            rem = resp.headers.get("x-ratelimit-remaining")
            return resp.status, js, time.time() - t0, rem
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:160]}, time.time() - t0, e.headers.get("x-ratelimit-remaining")
    except Exception as e:  # noqa
        return None, {"error": repr(e)[:160]}, time.time() - t0, None


def valid(txt):
    t = (txt or "").strip().strip("`").strip()
    if t.lower().startswith("json"):
        t = t[4:].strip()
    try:
        return isinstance(json.loads(t), dict)
    except Exception:  # noqa
        return False


def main():
    if not KEY:
        sys.exit("Set ADAPTION_API_KEY first.")
    print(f"# Reasoning probe  base={BASE}\n")
    print(f"{'model':20s} {'variant':24s} {'http':>4s} {'reason':>6s} {'out':>5s} {'json':>5s} {'sec':>5s}  rl_remaining")
    for m in MODELS:
        for name, extra in VARIANTS.items():
            st, js, dt, rem = call(m, extra)
            if st != 200:
                print(f"{m:20s} {name:24s} {str(st):>4s} {'-':>6s} {'-':>5s} {'-':>5s} {dt:5.1f}  {rem}  {js.get('error', '')[:80]}")
                continue
            u = js.get("usage", {})
            rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
            txt = ((js.get("choices") or [{}])[0].get("message") or {}).get("content")
            print(f"{m:20s} {name:24s} {st:>4d} {str(rt):>6s} {str(u.get('completion_tokens')):>5s} "
                  f"{str(valid(txt)):>5s} {dt:5.1f}  {rem}")
    print("\nDone. Paste the table into the chat.")


if __name__ == "__main__":
    main()