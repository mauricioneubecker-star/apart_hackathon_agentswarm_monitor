#!/usr/bin/env python3
"""Exploratory follow-up of the fine-tune gate (8 Nov): could a format repair have saved the swarm arm of Part C?

Reads the agent replies of the canary episode runs_vx/core-night_vx-K2-002-ft4/rep0 (llm_calls.jsonl, field raw) and,
per model, counts invalid replies (orchestrator.parse_response), what a mechanical repair rescues without changing any
character of content (first JSON object of concatenated objects; close open strings and brackets), and how many valid
or repaired turns carry at least one message. Agent replies only: no labels, no monitors.

  .venv/bin/python tools/ft_canary_repair.py --out ../analysis/results/ft_canary_repair
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(ROOT / "generator"))
from orchestrator import normalize_action, parse_response  # noqa: E402

CANARY = ROOT / "runs_vx" / "core-night_vx-K2-002-ft4" / "rep0" / "llm_calls.jsonl"


def repair(raw):
    """(obj, how). Never edits content: takes the first object, or appends the missing quote / closing brackets."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip())
    i = t.find("{")
    if i < 0:
        return None, "no_object"
    s = t[i:]
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
        if isinstance(obj, dict):
            return obj, "first_object"
    except json.JSONDecodeError:
        pass
    stack, in_str, esc = [], False, False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()
    fix = s + ('"' if in_str else "") + "".join("}" if c == "{" else "]" for c in reversed(stack))
    try:
        obj = json.loads(fix)
    except json.JSONDecodeError as e:
        return None, "failed: " + e.msg
    return (obj, "closed_truncated" if in_str else "closed") if isinstance(obj, dict) else (None, "not_a_dict")


def has_message(obj):
    m = obj.get("messages")
    return isinstance(m, list) and any(isinstance(x, dict) and str(x.get("text", "")).strip() for x in m)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = [json.loads(line) for line in CANARY.open()]
    res = {"source": str(CANARY.relative_to(ROOT)), "note": "exploratory, after the gate; agent replies only", "models": {}}
    for model in sorted({r.get("model") for r in rows}):
        R = [r for r in rows if r.get("model") == model]
        parsed = [parse_response(r.get("raw") or "") for r in R]
        good = [o for o, ok in parsed if ok]
        bad = [r for r, (_, ok) in zip(R, parsed) if not ok]
        how, rep_known, rep_msg = Counter(), 0, 0
        for r in bad:
            obj, h = repair(r.get("raw"))
            how[h] += 1
            if obj is not None:
                rep_known += normalize_action(obj)[0] != "unknown"
                rep_msg += has_message(obj)
        rescued = how["first_object"] + how["closed"] + how["closed_truncated"]
        res["models"][model] = {
            "calls": len(R), "invalid": len(bad), "invalid_share": round(len(bad) / len(R), 3),
            "repair": dict(how), "rescued": rescued, "rescued_truncated": how["closed_truncated"],
            "valid_after_repair_share": round((len(good) + rescued) / len(R), 3),
            "repaired_with_known_action": rep_known, "repaired_with_message": rep_msg,
            "valid_turns_with_message": sum(has_message(o) for o in good), "valid_turns": len(good),
            "message_share_valid_turns": round(sum(has_message(o) for o in good) / max(1, len(good)), 3)}
    Path(a.out + ".json").write_text(json.dumps(res, indent=1))
    L = ["# Fine-tune canary: could a format repair have saved Part C? (exploratory)", "",
         f"Source: `{res['source']}`. Mechanical repair only: first JSON object, or close the open string and brackets; "
         "no character of content is changed.", "",
         "| model | calls | invalid | rescued by repair (of them cut off) | valid after repair | turns with a message (valid) | repaired turns with a message |",
         "|---|---|---|---|---|---|---|"]
    for m, x in res["models"].items():
        L.append(f"| {m} | {x['calls']} | {x['invalid']} ({x['invalid_share']:.0%}) | {x['rescued']} "
                 f"({x['rescued_truncated']}) | {x['valid_after_repair_share']:.0%} | {x['valid_turns_with_message']}/"
                 f"{x['valid_turns']} ({x['message_share_valid_turns']:.0%}) | {x['repaired_with_message']} |")
    Path(a.out + ".md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
