#!/usr/bin/env python3
"""Check the Adaption Responses API for this project. Stdlib only (certifi optional).

Usage (key stays on your machine, never paste it into chat):
    export ADAPTION_API_KEY="pt_live_..."
    python3 check_endpoint.py            # paste the printed report back into the chat

Docs: https://docs.adaptionlabs.ai/inference-stacks/models/  (base URL below is from the API reference)
Costs: one tiny call per model, a few hundred tokens in total.
"""
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

try:  # macOS python.org builds often lack root certificates -> use certifi if installed
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

KEY = (os.environ.get("ADAPTION_API_KEY") or os.environ.get("API_KEY") or "").strip()
BASE = os.environ.get("ADAPTION_BASE_URL", "https://api.prod.adaptionlabs.ai/api/v1").rstrip("/")
PROJECT_MODELS = {  # project role -> Adaption model id
    "agent (train)": ["qwen3.8-27b", "qwen3.5-397b", "gemma-4-31b-it", "gemma-4-26b-a4b-it"],
    "held-out backbone + jury": ["glm-5.2"],
    "jury": ["deepseek-v4-flash"],
    "optional (cheap GLM)": ["glm-53-flash"],
}
JSON_PROMPT = ('Reply with ONLY this JSON object and nothing else: '
               '{"action": {"tool": "read_file", "args": {"path": "README.md"}}, "messages": []}')


def req(method, path, body=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=SSL_CTX) as resp:
            hdr = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read().decode(errors="replace")
            try:
                return resp.status, json.loads(raw or "{}"), hdr, time.time() - t0
            except json.JSONDecodeError:
                return resp.status, {"error": f"non-JSON response from {resp.geturl()}: {raw[:150]!r}"}, hdr, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:300]}, {k.lower(): v for k, v in e.headers.items()}, time.time() - t0
    except Exception as e:  # noqa
        return None, {"error": repr(e)[:300]}, {}, time.time() - t0


def interesting(hdr):
    return {k: v for k, v in hdr.items() if any(x in k for x in ("ratelimit", "credit", "quota", "balance", "remaining"))}


def main():
    if not KEY:
        sys.exit("Set ADAPTION_API_KEY first.")
    print(f"# Adaption check  base={BASE}")
    st, js, hdr, dt = req("GET", "/models?type=hosted")
    print(f"\n## GET /models?type=hosted -> {st} ({dt:.1f}s)")
    if "CERTIFICATE_VERIFY_FAILED" in str(js.get("error")):
        sys.exit("SSL certificates missing in this Python: `pip3 install certifi`, then run again.")
    ids = []
    if st == 200 and "error" not in js:
        items = js.get("data", js if isinstance(js, list) else [])
        ids = sorted({m.get("id", "") for m in items if isinstance(m, dict)})
        print("available:", ", ".join(ids) or "-")
    else:
        print("error:", js.get("error"))
    if interesting(hdr):
        print("limit/credit headers:", interesting(hdr))

    print("\n## Test calls (Responses API, 1 per model)")
    for role, models in PROJECT_MODELS.items():
        for mid in models:
            if ids and mid not in ids:
                print(f"- {mid:20s} [{role}] NOT AVAILABLE for this key")
                continue
            st, js, hdr, dt = req("POST", "/responses", {
                "model": mid, "input": JSON_PROMPT, "max_output_tokens": 120, "temperature": 0})
            if st != 200 or js.get("status") not in (None, "completed"):
                print(f"- {mid:20s} [{role}] HTTP {st} {str(js.get('error'))[:200]}")
                continue
            txt = (js.get("output_text") or "").strip()
            body = txt.strip("`").strip()
            if body.lower().startswith("json"):
                body = body[4:].strip()
            try:
                ok = isinstance(json.loads(body), dict)
            except Exception:  # noqa
                ok = False
            u = js.get("usage", {})
            print(f"- {mid:20s} [{role}] OK {dt:.1f}s json_valid={ok} "
                  f"tokens in/out={u.get('input_tokens')}/{u.get('output_tokens')} {interesting(hdr) or ''}")
            if not ok:
                print(f"    output: {txt[:160]!r}")
    print("\nDone. Paste everything above into the chat (it contains no key).")


if __name__ == "__main__":
    main()
