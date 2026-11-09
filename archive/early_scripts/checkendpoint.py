#!/usr/bin/env python3
"""Check what an OpenAI-compatible endpoint offers for this project. Stdlib only, no installs.

Usage (key stays on your machine, never paste it into chat):
    export API_KEY="..."                         # your Adaption key
    export BASE_URL="https://.../v1"             # base URL from Adaption's dashboard/docs
    python3 check_endpoint.py                    # paste the printed report back into the chat

What it does (costs a few hundred tokens in total):
  1. GET  /models                -> which models exist; which of our 6 models match
  2. POST /chat/completions      -> one tiny call per matched model: works? latency? token usage?
  3. JSON test                   -> can the model answer in the agent JSON format?
  4. Prints rate-limit / credit headers if the API sends them.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import ssl

try:  # macOS python.org builds often lack root certificates -> use certifi's bundle if installed
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

KEY = os.environ.get("API_KEY", "").strip()
BASE = os.environ.get("BASE_URL", "").strip().rstrip("/")
WANTED = {  # project role -> keywords that must all appear in the model id
    "agent qwen3.8-27b": ["qwen", "3.8", "27b"],
    "agent qwen3.5-397b": ["qwen", "3.5", "397b"],
    "agent gemma4-31b": ["gemma", "4", "31b"],
    "agent gemma4-26b-a4b": ["gemma", "4", "26b"],
    "heldout+jury glm-5.2": ["glm", "5"],
    "jury deepseek-v4-flash": ["deepseek", "v4"],
}
JSON_PROMPT = ('Reply with ONLY this JSON object and nothing else: '
               '{"action": {"tool": "read_file", "args": {"path": "README.md"}}, "messages": []}')


def req(method, path, body=None, timeout=60):
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
                return resp.status, {"error": (f"non-JSON response | final URL: {resp.geturl()} | "
                                               f"content-type: {hdr.get('content-type')} | "
                                               f"first 200 chars: {raw[:200]!r}")}, hdr, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}, {k.lower(): v for k, v in e.headers.items()}, time.time() - t0
    except Exception as e:  # noqa
        return None, {"error": repr(e)[:300]}, {}, time.time() - t0


def norm(s):
    return re.sub(r"[^a-z0-9.]", "", s.lower())


def main():
    if not KEY or not BASE:
        sys.exit("Set API_KEY and BASE_URL first (see docstring).")
    print(f"# Endpoint check  base={BASE}")
    st, js, hdr, dt = req("GET", "/models")
    print(f"\n## GET /models -> {st} ({dt:.1f}s)")
    ids = []
    if (st != 200 or "error" in js) and not BASE.endswith("/v1"):
        st2, js2, hdr2, dt2 = req("GET", "/v1/models")
        print(f"   (also tried {BASE}/v1/models -> {st2}: {str(js2.get('error', 'ok'))[:200]})")
        if st2 == 200 and "error" not in js2:
            st, js, hdr = st2, js2, hdr2
    if st == 200 and "error" not in js:
        items = js.get("data", js if isinstance(js, list) else [])
        ids = sorted({m.get("id", "") for m in items if isinstance(m, dict)})
        print(f"{len(ids)} models listed")
    else:
        print("error:", js.get("error"))
        if "CERTIFICATE_VERIFY_FAILED" in str(js.get("error")):
            sys.exit("\nSSL certificates missing in this Python. Fix: `pip3 install certifi` and run again "
                     "(or run 'Install Certificates.command' in /Applications/Python 3.x/).")
    lim ={k: v for k, v in hdr.items() if any(x in k for x in ("ratelimit", "credit", "quota", "balance", "remaining"))}
    if lim:
        print("limit/credit headers:", lim)

    print("\n## Project models")
    matches = {}
    for role, kws in WANTED.items():
        hits = [i for i in ids if all(k in norm(i) for k in kws)]
        matches[role] = hits
        print(f"- {role:28s} {'MISSING' if not hits else ', '.join(hits[:4])}")
    others = [i for i in ids if any(k in i.lower() for k in ("qwen", "gemma", "glm", "deepseek", "llama", "kimi", "mistral"))]
    print("\nOther open models listed (for substitutes):", ", ".join(others[:40]) or "-")

    print("\n## Test calls (1 per matched model)")
    for role, hits in matches.items():
        if not hits:
            continue
        mid = hits[0]
        st, js, hdr, dt = req("POST", "/chat/completions", {
            "model": mid, "messages": [{"role": "user", "content": JSON_PROMPT}],
            "max_tokens": 80, "temperature": 0})
        if st != 200:
            print(f"- {mid}: HTTP {st} {js.get('error', '')[:160]}")
            continue
        txt = (js.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        try:
            ok = isinstance(json.loads(txt.strip().strip("`").removeprefix("json").strip()), dict)
        except Exception:  # noqa
            ok = False
        u = js.get("usage", {})
        lim = {k: v for k, v in hdr.items() if any(x in k for x in ("ratelimit", "credit", "quota", "remaining"))}
        print(f"- {mid}: OK {dt:.1f}s  json_valid={ok}  usage={u}  {lim if lim else ''}")
    print("\nDone. Paste everything above into the chat (it contains no key).")


if __name__ == "__main__":
    main()