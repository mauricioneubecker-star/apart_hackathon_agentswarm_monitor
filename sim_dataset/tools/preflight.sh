#!/usr/bin/env bash
# Pre-flight for an overnight batch (DECISIONS.md section 15). Run once before tools/night_run.sh; every step must
# print OK. Takes ~15 min (most of it the real 1-episode canary at the end; skip it with CANARY=0).
#   PY=.venv/bin/python bash tools/preflight.sh
set -u -o pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
WHERE=${WHERE:-"split.str.startswith('night')"}
CANARY=${CANARY:-1}
fail() { echo "FAIL: $*"; exit 1; }
step() { echo; echo "== $*"; }

step "python + packages"
$PY -c "import sys; assert sys.version_info >= (3, 11), sys.version; import pytest, networkx, pandas; print('OK', sys.version.split()[0])" || fail "python >= 3.11 with pytest/networkx/pandas needed ($PY)"

step "scenarios up to date (deterministic regeneration, no diff expected after applying the branch)"
$PY generator/generate.py core > /dev/null || fail "generate.py core"
N=$($PY -c "import sys; sys.path.insert(0,'generator'); from query import Dataset; print(len(Dataset().where(\"$WHERE\")))")
[ "$N" -gt 0 ] || fail "no scenarios match $WHERE"
echo "OK $N configs match"

step "static checks + engine smoke in the macOS sandbox (night + pilot5 only)"
$PY - <<'EOF' || fail "validation"
import sys, json, glob
sys.path.insert(0, "generator")
import validate as V
bad, n = {}, 0
for f in sorted(glob.glob("dataset/scenarios/core/core-*.json")):
    if "night" not in f and "pilot5" not in f:
        continue
    sc = json.load(open(f))
    e = V.static_checks(sc) + V.smoke(sc)
    n += 1
    if e:
        bad[sc["scenario_id"]] = e
print(f"{n} checked, errors: {bad or 'none'}")
sys.exit(1 if bad else 0)
EOF
echo OK

step "API: every key, every agent model of the night batch, both judges (tiny calls, must all be 200)"
$PY - <<'PYEOF' || fail "API check (see lines above)"
import asyncio, sys
sys.path.insert(0, "runner"); sys.path.insert(0, "generator")
from llm import AdaptionClient, AnthropicClient, load_secrets
from config import MODELS, TRAIN_MODELS
sec = load_secrets()
msg = [{"role": "user", "content": 'Reply with ONLY {"ok": true}'}]


async def main():
    bad = []
    if not sec["adaption"]:
        print("no Adaption keys")
        return ["keys"]
    jury = set(sec.get("jury_keys", []))
    sim = [i for i in range(len(sec["adaption"])) if i not in jury]
    print(f"{len(sec['adaption'])} Adaption keys: {len(sim)} for simulation, jury keys {sorted(jury) or 'none'}")
    for i, k in enumerate(sec["adaption"]):
        c = AdaptionClient(k, i)
        r = await c.chat("qwen3.8-27b", msg, max_tokens=20, temperature=0, reasoning_effort="none")
        print(f"  key {i}: status {r['status']}, limit {c.server_limit}/min")
        if r["status"] != 200:
            bad.append(f"key {i}")
    c = AdaptionClient(sec["adaption"][0], 0)
    for m in [MODELS[x]["provider_model_id"] for x in TRAIN_MODELS] + ["deepseek-v4-flash"]:
        r = await c.chat(m, msg, max_tokens=20, temperature=0, reasoning_effort="none")
        print(f"  model {m}: status {r['status']} {str(r['error'])[:80] if r['status'] != 200 else ''}")
        if r["status"] != 200:
            bad.append(m)
    if sec["anthropic"]:
        r = await AnthropicClient(sec["anthropic"]).chat("claude-haiku-5-5", msg, max_tokens=20)
        print(f"  claude-haiku-5-5: status {r['status']}")
        if r["status"] != 200:
            bad.append("haiku")
    else:
        bad.append("anthropic key missing")
    return bad

bad = asyncio.run(main())
print("FAILED: " + ", ".join(bad) if bad else "all 200")
sys.exit(1 if bad else 0)
PYEOF
echo OK

step "fake end-to-end (3 configs incl. one branched): simulate -> jury -> labels -> features"
rm -rf runs_preflight_fake
$PY runner/run.py simulate --fake --where "$WHERE and (scenario_id.str.contains('night_branch-K4-000') or scenario_id.str.contains('night_train-K2-001') or scenario_id.str.contains('night_train-K4-000'))" \
    --replicates 1 --out runs_preflight_fake --workers 3 | tail -4 || fail "fake simulate"
$PY runner/run.py jury --fake --out runs_preflight_fake > /dev/null || fail "fake jury"
$PY runner/run.py labels --out runs_preflight_fake > /dev/null || fail "labels"
$PY runner/run.py features --no-nli --out runs_preflight_fake > /dev/null || fail "features"
[ -z "$(ls runs_preflight_fake/*/rep*/error.txt 2>/dev/null)" ] || fail "error.txt in fake run"
rm -rf runs_preflight_fake
echo OK

step "disk + power"
df -h . | tail -1
pmset -g batt 2>/dev/null | head -2 || true
echo "(plug the Mac in; night_run.sh keeps it awake with caffeinate)"

if [ "$CANARY" = "1" ]; then
  step "real canary: 1 short episode on the real API (limit 1, separate out dir)"
  rm -rf runs_canary
  $PY runner/run.py simulate --where "$WHERE and scenario_id.str.contains('night_train-K2-001')" --replicates 1 \
      --limit 1 --out runs_canary | tail -3 || fail "canary simulate"
  [ -z "$(ls runs_canary/*/rep*/error.txt 2>/dev/null)" ] || fail "canary error.txt: $(cat runs_canary/*/rep*/error.txt | tail -5)"
  $PY - <<'EOF' || fail "canary quality"
import json, glob
m = json.load(open(glob.glob("runs_canary/*/rep0/meta.json")[0]))
print("invalid_json_rate", m["invalid_json_rate"], "messages", m["n_messages"], "merged", m["merged"])
assert m["invalid_json_rate"] < 0.15 and m["n_messages"] > 20
EOF
  echo "OK (runs_canary/ can be deleted)"
fi
echo; echo "PREFLIGHT OK -> bash tools/night_run.sh"
