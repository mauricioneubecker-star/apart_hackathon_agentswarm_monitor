#!/usr/bin/env python3
"""Paste your API keys once; they are stored locally in sim_dataset/secrets.local.json (chmod 600, in .gitignore).

    python3 runner/setup_keys.py

- Adaption keys: paste them one per line (or several separated by commas/spaces), then press Enter on an
  empty line. Input is hidden.
- The last key is reserved for the jury by default (so simulation and jury don't share a rate limit);
  simulation uses the others. Change with the prompt or edit "jury_keys" in the file.
- Anthropic key (Haiku judge): optional, hidden input.
Never paste keys into a chat or commit the file.
"""
import getpass
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "secrets.local.json"


def mask(k: str) -> str:
    return k[:8] + "…" + k[-4:] if len(k) > 14 else "***"


def main():
    old = json.loads(PATH.read_text()) if PATH.exists() else {}
    print("Paste your Adaption API keys (hidden). One per line or comma-separated; empty line to finish.")
    keys = []
    while True:
        line = getpass.getpass(f"Adaption key {len(keys) + 1}: ").strip()
        if not line:
            break
        for k in re.split(r"[,\s]+", line):
            if k and k not in keys:
                keys.append(k)
    if not keys:
        keys = old.get("adaption", [])
        if not keys:
            sys.exit("No keys entered.")
        print(f"Keeping {len(keys)} existing Adaption key(s).")
    for i, k in enumerate(keys):
        warn = "" if k.startswith("pt_") else "   <- does not look like an Adaption key (pt_...)"
        print(f"  [{i}] {mask(k)}{warn}")
    default_jury = [len(keys) - 1] if len(keys) >= 3 else []
    ans = input(f"Key indices reserved for the jury {default_jury} (Enter = accept, 'none' = share all): ").strip()
    if ans.lower() == "none":
        jury = []
    elif ans:
        jury = [int(x) for x in re.split(r"[,\s]+", ans) if x.isdigit() and int(x) < len(keys)]
    else:
        jury = default_jury
    anth = getpass.getpass("Anthropic API key for the Haiku judge (hidden, Enter = keep/skip): ").strip() or old.get("anthropic")
    data = {"adaption": keys, "jury_keys": jury, "anthropic": anth}
    PATH.write_text(json.dumps(data, indent=1))
    os.chmod(PATH, 0o600)
    sim = [i for i in range(len(keys)) if i not in jury] or list(range(len(keys)))
    print(f"\nSaved {PATH.name}: {len(keys)} Adaption key(s) -> simulation {sim}, jury {jury or sim}; "
          f"Anthropic: {'yes' if anth else 'no'}")
    print("Next: python3 runner/run.py selftest")


if __name__ == "__main__":
    main()
