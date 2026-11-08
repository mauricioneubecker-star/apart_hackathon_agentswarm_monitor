#!/usr/bin/env python3
"""Twin check for the validation star design: every arm must equal its in-distribution twin except the shifted factor.

  python3 tools/vx_check.py            # exit code 1 on any unexpected difference

Compared per agent: handle, team, role, persona, ticket (function, solvability, variant, deps, reviewers), flags;
per scenario: package, unsolvable/instructed agents, acceptance variants, early adopters, malicious script, and
(where the shift does not touch them) DM graph, models, system prompts, timeline, sanctions.
Expected differences per arm:
  time  rounds/cut/credits/reminders -> prompts and timeline differ; graph, models, sanctions identical
  glm   12 agents on glm-5.2 (one train model replaced); prompts, graph, timeline identical
  bal   models rebalanced 6/6/6/6; prompts, graph, timeline identical
  enf   sanction revert / detection 0.7 / public; graph, models identical
  topo  scale-free DM graph. Every draw that depends on the graph is redrawn (reviewers and clarification holders by
        graph distance, seeds by degree, scattered ticket placement), so this arm is a factor-level twin only:
        same factors, package, handles, models; differences are reported as notes, not errors.
  ft4/b4  the agents flagged `persistent` (persistent_share 0.5) on the 4B model (fine-tune / base), persona
        sentence removed; unflagged agents identical in model and prompt; the two arms identical to each other.
Also checks the replicate copies: identical to their source except id/split/phase/replicate seeds/params.vx_*.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SC = ROOT / "dataset" / "scenarios" / "core"
sys.path.insert(0, str(ROOT / "generator"))
import generate as G  # noqa: E402


ARM_KEYS = {   # params an arm may change (plus the vx bookkeeping)
    "time": {"deadline_override", "credits_override", "memory_window_rounds", "reminder_rounds_override"},
    "glm": {"model_mix"}, "bal": {"model_mix"},
    "enf": {"sanction", "detection_probability", "sanction_visibility", "sanctions", "enforcer"},
    "topo": {"topology"},
    "ft4": {"persistent_share", "vx_n_on_4b"}, "b4": {"persistent_share", "vx_n_on_4b"},
}
FT_ARMS = ("ft4", "b4")
for _k in ARM_KEYS.values():
    _k |= {"vx_arm", "replicates_planned"}


def agent_core(a):
    t = a["ticket"]
    return (a["handle"], a["team"], a["role"], a["persona"], t["function"], t["solvable"], t["acceptance_variant"],
            tuple(t["deps"]), tuple(t["reviewers"]), json.dumps(a["flags"], sort_keys=True))


def main():
    sel = json.loads(G.VX_SELECTION.read_text())
    errs, notes = [], []
    for b in sel["bases"]:
        base = b["base"]
        tw = json.loads((SC / f"{base}-id.json").read_text())
        for arm in G.VX_ARMS:
            if arm == "id":
                continue
            f = SC / f"{base}-{arm}.json"
            if not f.exists():
                if arm == "topo" and tw["params"]["channels"] != "board":
                    errs.append(f"{base}: topo arm missing for a local-channel base")
                continue
            sc = json.loads(f.read_text())
            same = lambda k, x, y: x == y or errs.append(f"{base}-{arm}: {k} differs")  # noqa: E731
            same("package", sc["refs"], tw["refs"])
            same("factors", {k: v for k, v in sc["params"].items() if k not in ARM_KEYS[arm]},
                 {k: v for k, v in tw["params"].items() if k not in ARM_KEYS[arm]})
            if arm == "topo":   # graph-dependent draws (reviewers, clarification holders, scattered placement) redraw
                if sc["labels_config"]["unsolvable_agents"] != tw["labels_config"]["unsolvable_agents"]:
                    notes.append(f"{base}-topo: unsolvable tickets placed on other agents (graph-dependent draw)")
            else:
                same("unsolvable", sc["labels_config"]["unsolvable_agents"], tw["labels_config"]["unsolvable_agents"])
                same("acceptance", sc["env"]["acceptance_variant"], tw["env"]["acceptance_variant"])
            moved = [i for i, (a, c) in enumerate(zip(sc["population"], tw["population"])) if agent_core(a) != agent_core(c)]
            if arm in FT_ARMS:
                flagged = [i for i, a in enumerate(sc["population"]) if a["flags"].get("persistent")]
                if not 8 <= len(flagged) <= 12:
                    errs.append(f"{base}-{arm}: {len(flagged)} flagged agents")
                if set(moved) - set(flagged):
                    errs.append(f"{base}-{arm}: unflagged agents differ {sorted(set(moved) - set(flagged))[:5]}")
                for i, (a, c) in enumerate(zip(sc["population"], tw["population"])):
                    if i in flagged:
                        if a["model"] != ("ft4-persistent" if arm == "ft4" else "base4"):
                            errs.append(f"{base}-{arm}: flagged agent {i} on {a['model']}")
                        if "You are persistent:" in a["system_prompt"]:
                            errs.append(f"{base}-{arm}: persona sentence left in ({i})")
                    elif (a["model"], a["system_prompt"]) != (c["model"], c["system_prompt"]):
                        errs.append(f"{base}-{arm}: unflagged agent {i} model/prompt differs")
                same("dm_edges", sc["communication"]["dm_edges"], tw["communication"]["dm_edges"])
                same("timeline", sc["timeline"], tw["timeline"])
            elif arm == "topo":
                if moved:
                    notes.append(f"{base}-topo: {len(moved)} agent(s) with other ticket/reviewer/flag draws")
                same("handles", [a["handle"] for a in sc["population"]], [a["handle"] for a in tw["population"]])
                same("dm_edges differ", sc["communication"]["dm_edges"] != tw["communication"]["dm_edges"], True)
                same("models", [a["model"] for a in sc["population"]], [a["model"] for a in tw["population"]])
            else:
                if moved:
                    errs.append(f"{base}-{arm}: agents {moved[:5]} differ")
                same("dm_edges", sc["communication"]["dm_edges"], tw["communication"]["dm_edges"])
            if arm in ("glm", "bal"):
                same("prompts", [a["system_prompt"] for a in sc["population"]], [a["system_prompt"] for a in tw["population"]])
                same("timeline", sc["timeline"], tw["timeline"])
                models = [a["model"] for a in sc["population"]]
                if arm == "glm" and models.count("glm-5.2") != 12:
                    errs.append(f"{base}-glm: {models.count('glm-5.2')} glm agents")
                if arm == "bal" and sorted(models.count(m) for m in set(models)) != [6, 6, 6, 6]:
                    errs.append(f"{base}-bal: not 6/6/6/6")
                if set(sc["models"]) != set(models):
                    errs.append(f"{base}-{arm}: models dict does not match the population")
            if arm == "time":
                same("rounds", (sc["rounds"], sc["spec"]["budget_time"]["deadline_round"]), (G.VX_TIME["rounds"], G.VX_TIME["cut"]))
                same("models", [a["model"] for a in sc["population"]], [a["model"] for a in tw["population"]])
            if arm == "enf":
                r = sc["runtime_rules"]["sanction"]
                same("sanction", (r["type"], r["detection_probability"], r["visibility"]), ("revert", 0.7, "public"))
                same("models", [a["model"] for a in sc["population"]], [a["model"] for a in tw["population"]])
    for b in sel["bases"]:   # the two 4B arms are exact twins of each other (only the model key differs)
        f4, b4 = (json.loads((SC / f"{b['base']}-{x}.json").read_text()) for x in FT_ARMS)
        for a, c in zip(f4["population"], b4["population"]):
            if agent_core(a) != agent_core(c):
                errs.append(f"{b['base']}: ft4 vs b4 agents differ")
                break
        if [a["system_prompt"] for a in f4["population"]] != [a["system_prompt"] for a in b4["population"]]:
            errs.append(f"{b['base']}: ft4 vs b4 prompts differ")
    for src in G.VX_REPLICATE_SOURCES:
        o = json.loads((SC / f"{src}.json").read_text())
        c = json.loads((SC / f"core-night_vx_rep-{src.removeprefix('core-')}.json").read_text())
        if c["replicate_seeds"][:2] != [o["replicate_seeds"][i] for i in G.VX_REPLICATE_SEEDS]:
            errs.append(f"{src}: replicate seeds")
        for k in ("population", "timeline", "env", "communication", "runtime_rules", "models", "labels_config"):
            if c[k] != o[k]:
                errs.append(f"{src}: copy differs in {k}")
    for n in notes:
        print("note:", n)
    for e in errs:
        print("ERROR:", e)
    n_arms = len(list(SC.glob("core-night_vx-*.json")))
    print(f"{len(sel['bases'])} bases, {n_arms} arm files, {len(G.VX_REPLICATE_SOURCES)} replicate copies: "
          f"{len(errs)} error(s)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
