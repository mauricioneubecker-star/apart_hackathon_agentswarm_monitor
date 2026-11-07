#!/usr/bin/env python3
"""AmongUs-X logs -> canonical snapshot format (see gnn/FORMAT.md). Stdlib only, Python >= 3.8.

Input layout (HF dataset Among-us-X/AmongUs-X), any depth below --root:
    <matchup>/<date>_exp_<N>/{summary.json, agent-logs-compact.json, game_<i>.log, experiment-details.txt}

Snapshot = one discussion round of one meeting: t = 3*meeting + round (round 0 TESTIMONY,
1 ACCUSATION/DEFENSE, 2 FINAL ARGUMENTS). Nodes = players alive in that meeting (speakers or voters).
Edges (cumulative over rounds <= r of the current meeting unless noted):
    mention   speaker -> mentioned player ("Player N"), sentence-level lexicon features   [public]
    vote_prev voter -> target in earlier meetings of the same game                          [public]
    coloc     same room at the same task step since the previous meeting (both directions)  [privileged]
Never used as input: identity, Thinking Process, World State Ledger, epistemic states, kills/vents.

Labels (identical for the 3 rounds of a meeting):
    graph: innocent_ejected, impostor_ejected, any_ejected, game_impostor_win, n_crew_votes_innocent
    node : votes_innocent / votes_skip (crewmates only, empty for impostors), is_impostor (control)

Usage: python3 amongus.py --root ~/data/AmongUs-X --out ~/data/AmongUs-X/_canonical [--ood-models a,b]
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

VERSION = "amongus-adapter-v2-2026-11-07"
PNUM = re.compile(r"Player (\d+)")
PNAME = re.compile(r"(Player \d+: [a-z]+)")


def pid(name: str) -> str:
    """'Player 3: cyan' -> 'P3'."""
    m = PNUM.search(name or "")
    return f"P{m.group(1)}" if m else ""


# ------------------------------------------------------------------------------------------------ lexicons (tier 1)
def _c(*ps):
    return [re.compile(p) for p in ps]


LEX = {
    "accuse": _c(r"\bsus\b", r"suspicio", r"suspect", r"\blying\b", r"\blie[sd]?\b", r"\bliar\b", r"inconsisten",
                 r"contradict", r"doesn't add up", r"impostor|imposter", r"\bfake\b", r"can't be (verified|confirmed)",
                 r"no one (saw|can confirm)", r"didn't see (you|them|him|her)"),
    "defend": _c(r"\btrust", r"innocent", r"\bclear(ed)?\b", r"vouch", r"with me\b", r"\bsafe\b",
                 r"confirm(s|ed)? (that|their|his|her)", r"believe (him|her|them|player)", r"not (the |an )?impostor"),
    "sighting": _c(r"\bsaw\b", r"\bseen\b", r"\bspotted\b", r"\bnoticed\b", r"heading (to|toward)", r"\bwatched\b"),
    "kill": _c(r"\bkill", r"\bbody\b", r"\bdead\b", r"\bvent", r"murder"),
    "vote": _c(r"\bvot(e|ing)", r"\beject", r"\bskip\b"),
    "uncertain": _c(r"not sure", r"no (direct )?evidence", r"\bcan't\b", r"\bcannot\b", r"unclear", r"don't know",
                    r"no information", r"not certain"),
    "alibi": _c(r"\bi was (in|at|doing)\b", r"\bmy tasks?\b", r"\bi (completed|finished|did)\b"),
}
EDGE_LEX = ["accuse", "defend", "sighting", "kill", "vote", "uncertain"]
NODE_LEX = ["accuse", "defend", "sighting", "kill", "uncertain", "alibi"]


def lex(text: str, key: str) -> int:
    return min(3, sum(1 for p in LEX[key] if p.search(text)))


def norm(text: str) -> str:
    return str(text).replace("’", "'").replace("‘", "'").lower()


SENT = re.compile(r"(?<=[.!?])\s+")

# ------------------------------------------------------------------------- claims about places (tier 1, public text)
ROOMS = ["cafeteria", "weapons", "navigation", "o2", "shields", "communications", "storage", "admin", "electrical",
         "lower engine", "upper engine", "security", "reactor", "medbay"]
_ROOM = "(" + "|".join(sorted(ROOMS, key=len, reverse=True)) + ")"
SELF_CLAIM = re.compile(r"\bi(?: was|'m| am| went| moved| stayed| headed| walked| came)(?: [\w']+){0,6}? "
                        r"(?:in|to|at|into|toward|towards|from|through) (?:the )?" + _ROOM + r"\b")
SIGHT = re.compile(r"player (\d+)(?::? [a-z]+)?(?: [\w']+){0,6}? (?:in|at|near|into|toward|towards|to|from|"
                   r"leaving|entering) (?:the )?" + _ROOM + r"\b")
VOTE_INTENT = re.compile(r"(?:vote|voting|eject|ejecting)(?: [\w']+){0,3}? player (\d+)")
SKIP_INTENT = re.compile(r"\b(?:vote|voting|i'll|i will|we should)(?: [\w']+){0,2}? skip\b")


def claims(sent: str):
    """(self-claimed rooms, {player_num: rooms placed}, {player_num explicitly voted against})."""
    selfr = set(m.group(1) for m in SELF_CLAIM.finditer(sent))
    sight = defaultdict(set)
    for m in SIGHT.finditer(sent):
        sight[m.group(1)].add(m.group(2))
    votes = set(VOTE_INTENT.findall(sent))
    return selfr, sight, votes


# ------------------------------------------------------------------------------------------------- schema (tiers)
EDGE_FEATURES = (
    [("m_count", 0, ["structure"]), ("m_current", 0, ["structure", "temporal"]), ("m_first_round", 0, ["temporal"])]
    + [(f"e_{k}", 1, ["lexicon"] + (["rule_near"] if k in ("accuse", "kill", "vote") else [])) for k in EDGE_LEX]
    + [("e_question", 1, ["lexicon"]),
       ("e_place", 1, ["claims"]), ("e_conflict", 1, ["claims"]), ("e_place_body", 1, ["claims"]),
       ("e_vote_intent", 1, ["claims"]),
       ("v_count", 0, ["vote_history"]), ("c_steps", 0, ["privileged"]), ("c_last", 0, ["privileged"])]
)
ETYPES = [("mention", 0, []), ("vote_prev", 0, ["vote_history"]), ("coloc", 0, ["privileged"])]
NODE_FEATURES = (
    [("reporter", 0, ["meeting_meta"]), ("caller", 0, ["meeting_meta"]), ("own_speeches", 0, ["structure"])]
    + [(f"own_{k}", 1, ["lexicon"] + (["rule_near"] if k in ("accuse", "kill") else [])) for k in NODE_LEX]
    + [("self_rooms", 1, ["claims"]), ("self_claim_change", 1, ["claims"]), ("self_body_room", 1, ["claims"]),
       ("contradicted_by", 1, ["claims"]), ("placed_at_body_by", 1, ["claims"]), ("skip_intent", 1, ["claims"]),
       ("prev_votes_received", 0, ["vote_history"]), ("prev_voted_rev_impostor", 0, ["vote_history"]),
       ("prev_voted_rev_innocent", 0, ["vote_history"]), ("prev_skips", 0, ["vote_history"]),
       ("n_coloc_partners", 0, ["privileged"])]
)
GRAPH_LABELS = {"innocent_ejected": {"type": "binary"}, "impostor_ejected": {"type": "binary"},
                "any_ejected": {"type": "binary"}, "game_impostor_win": {"type": "binary"},
                "n_crew_votes_innocent": {"type": "count", "max": 7}}
NODE_LABELS = {"votes_innocent": {"type": "binary", "note": "crewmates only"},
               "votes_skip": {"type": "binary", "note": "crewmates only"},
               "is_impostor": {"type": "binary", "note": "control target"},
               "is_ejected": {"type": "binary", "note": "ejected in this meeting (structured readout target)"},
               "votes_received": {"type": "count", "note": "votes received in this meeting"}}


# ---------------------------------------------------------------------------------------------------------- parsing
def cat_json(path):
    """Concatenated JSON objects (not an array, not JSON lines)."""
    s = open(path, encoding="utf-8", errors="replace").read()
    dec, i, out = json.JSONDecoder(), 0, []
    while i < len(s):
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            break
        o, i = dec.raw_decode(s, i)
        out.append(o)
    return out


def resolved_action(rec) -> str:
    resp = (rec.get("interaction") or {}).get("response")
    if isinstance(resp, dict):
        return str(resp.get("Resolved Action") or "")
    return ""


def phase_of(rec) -> str:
    info = str(((rec.get("interaction") or {}).get("prompt") or {}).get("All Info", ""))
    m = re.search(r"Current phase: ([A-Za-z ]+)", info)
    return m.group(1).strip() if m else ""


def parse_game_log(path):
    """Per meeting (in order): reporter, ejected name, forced-speech set {(round, pid)}."""
    meetings, cur, pending_reporter, pending_body = [], None, None, None
    rnd = 0
    for line in open(path, encoding="utf-8", errors="replace"):
        if "[FORCED REPORT]" in line:
            m = PNAME.search(line)
            pending_reporter = m.group(1) if m else None
            mb = re.search(r"dead body in ([A-Za-z0-9 ]+?)\s*(?:—|-|$)", line)
            pending_body = mb.group(1).strip().lower() if mb else None
        m = re.search(r"Discussion round (\d+)", line)
        if m:
            rnd = int(m.group(1))
            if rnd == 0:
                cur = {"reporter": pending_reporter, "body_room": pending_body, "ejected": None, "forced": set(),
                       "result": None}
                meetings.append(cur)
                pending_reporter = pending_body = None
            continue
        if cur is None:
            continue
        if "[SPEECH FALLBACK]" in line:
            m = PNAME.search(line)
            if m:
                cur["forced"].add((rnd, pid(m.group(1))))
        if "RESULT:" in line:
            cur["result"] = line.split("RESULT:", 1)[1].strip()
            m = re.search(r"RESULT: (Player \d+: [a-z]+) was EJECTED", line)
            if m:
                cur["ejected"] = m.group(1)
    return meetings


def split_of(episode_id: str, matchup: str, ood_models) -> str:
    if matchup.split("/")[-1] in ood_models or matchup in ood_models:
        return "test_ood_model"
    h = int(hashlib.md5(episode_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "train" if h < 0.70 else ("val" if h < 0.85 else "test_id")


# ------------------------------------------------------------------------------------------------------------ main
def process_experiment(exp_dir, root, ood_models, W, stats):
    rel = os.path.relpath(exp_dir, root).replace(os.sep, "/")
    matchup = rel.rsplit("/", 1)[0] if "/" in rel else rel
    summ = {}
    for o in cat_json(os.path.join(exp_dir, "summary.json")):
        summ.update(o)
    logs = cat_json(os.path.join(exp_dir, "agent-logs-compact.json"))
    by_game = defaultdict(list)
    for r in logs:
        by_game[str(r.get("game_index"))].append(r)

    for gname, g in summ.items():
        if not gname.startswith("Game"):
            continue
        gi = int(gname.split()[-1])
        cfg = g.get("config", {})
        ident = {pid(v["name"]): v["identity"] for k, v in g.items() if k.startswith("Player") and isinstance(v, dict)}
        models = sorted({v.get("model", "") for k, v in g.items() if k.startswith("Player") and isinstance(v, dict)})
        recs = by_game.get(gname, [])
        lp = os.path.join(exp_dir, f"game_{gi}.log")
        if not recs or not os.path.exists(lp):
            stats["skip_missing"] += 1
            continue
        glog = parse_game_log(lp)
        eid = f"{rel}/g{gi}"
        winner = str(g.get("winner_reason", ""))
        imp_win = int("impostor" in winner.lower())

        # order records as logged; group meeting-phase records by step
        meet_steps, step_recs = [], defaultdict(list)
        for r in recs:
            st = r.get("step")
            ra = resolved_action(r)
            if phase_of(r) == "Meeting phase" and (ra.startswith("SPEAK") or ra.startswith("VOTE")):
                if st not in step_recs:
                    meet_steps.append(st)
                step_recs[st].append(r)
        # compact log and game log must agree on the meetings, and steps must increase (no merged reruns)
        if len(meet_steps) != len(glog) or meet_steps != sorted(meet_steps):
            stats["skip_meeting_mismatch"] += 1
            stats[f"skip_mismatch::{matchup}"] += 1
            continue
        stats["games"] += 1
        W["episodes"].writerow({"episode_id": eid, "group_id": eid, "split": split_of(eid, matchup, ood_models),
                                "matchup": matchup, "models": "+".join(models), "num_players": cfg.get("num_players"),
                                "num_impostors": cfg.get("num_impostors"), "winner_reason": winner,
                                "n_meetings": len(glog)})
        n_meet = len(meet_steps)

        prev_votes = []          # (meeting, voter, target or 'SKIP')
        revealed = {}            # pid -> 'Impostor'/'Crewmate' once ejected
        prev_step = -1
        for k in range(n_meet):
            st = meet_steps[k]
            ml = glog[k]
            speeches, votes = [], {}
            seen = Counter()
            for r in step_recs[st]:
                p = pid(r["player"]["name"])
                ra = resolved_action(r)
                if ra.startswith("SPEAK"):
                    rd = seen[p]
                    seen[p] += 1
                    speeches.append((min(rd, 2), p, ra.split(":", 1)[1] if ":" in ra else ""))
                elif ra.startswith("VOTE"):
                    tgt = ra[4:].strip()
                    votes[p] = "SKIP" if tgt.upper().startswith("SKIP") else pid(tgt)
            alive = sorted(set(p for _, p, _ in speeches) | set(votes), key=lambda x: int(x[1:]))
            if len(alive) < 2:
                stats["skip_tiny_meeting"] += 1
                continue
            stats["meetings"] += 1
            ej = pid(ml["ejected"]) if ml["ejected"] else ""
            ej_ident = ident.get(ej, "") if ej else ""
            crew_alive = [p for p in alive if ident.get(p) == "Crewmate"]
            n_crew_inn = sum(1 for p in crew_alive if votes.get(p) not in (None, "SKIP")
                             and ident.get(votes[p]) == "Crewmate")
            # caller (emergency meeting) from compact logs between previous meeting and this one
            caller = ""
            for r in recs:
                if prev_step < (r.get("step") or 0) <= st and resolved_action(r).startswith("CALL"):
                    caller = pid(r["player"]["name"])
            reporter = pid(ml["reporter"]) if ml["reporter"] else ""

            # co-location since previous meeting (privileged)
            room_at = defaultdict(dict)   # step -> pid -> room
            for r in recs:
                s2 = r.get("step") or 0
                if prev_step < s2 < st and phase_of(r) == "Task phase":
                    room_at[s2][pid(r["player"]["name"])] = (r.get("player") or {}).get("location")
            coloc, last_step = Counter(), max(room_at) if room_at else None
            coloc_last = set()
            for s2, rooms in room_at.items():
                inv = defaultdict(list)
                for p, room in rooms.items():
                    if p in alive and room:
                        inv[room].append(p)
                for ps in inv.values():
                    for a in ps:
                        for b in ps:
                            if a != b:
                                coloc[(a, b)] += 1
                                if s2 == last_step:
                                    coloc_last.add((a, b))

            # vote history (public), with revealed identities of ejected targets
            v_recv, v_imp, v_inn, v_skip, v_edge = Counter(), Counter(), Counter(), Counter(), Counter()
            for _, v, tgt in prev_votes:
                if tgt == "SKIP":
                    v_skip[v] += 1
                    continue
                v_recv[tgt] += 1
                if revealed.get(tgt) == "Impostor":
                    v_imp[v] += 1
                elif revealed.get(tgt) == "Crewmate":
                    v_inn[v] += 1
                if v in alive and tgt in alive:
                    v_edge[(v, tgt)] += 1

            for rd in range(3):
                t = 3 * k + rd
                sp = [s for s in speeches if s[0] <= rd]
                forced = sum(1 for (r0, p, _) in sp if (r0, p) in ml["forced"])
                W["snapshots"].writerow({"episode_id": eid, "t": t, "meeting": k, "round": rd, "step": st,
                                         "n_alive": len(alive), "n_speeches": len(sp),
                                         "forced_share": round(forced / len(sp), 4) if sp else 0.0})
                # edges: mentions
                E = defaultdict(lambda: Counter())
                first = {}
                own = defaultdict(Counter)
                n_own = Counter()
                self_rooms = defaultdict(set)            # player -> rooms they claim to have been in
                self_rooms_r = defaultdict(lambda: defaultdict(set))   # player -> round -> rooms
                placed = defaultdict(set)                # (speaker, target) -> rooms speaker places target in
                skip_int = Counter()
                body = ml.get("body_room")
                for (r0, s, text) in sp:
                    tx = norm(text)
                    n_own[s] += 1
                    for key in NODE_LEX:
                        own[s][key] += lex(tx, key)
                    skip_int[s] += int(bool(SKIP_INTENT.search(tx)))
                    ment_speech = set()
                    for sent in SENT.split(tx):
                        ds = {f"P{x}" for x in PNUM.findall(sent.replace("player", "Player"))} - {s}
                        ds &= set(alive)
                        sr, sight, vint = claims(sent)
                        self_rooms[s] |= sr
                        self_rooms_r[s][r0] |= sr
                        for num, rooms in sight.items():
                            d = f"P{num}"
                            if d in alive and d != s:
                                placed[(s, d)] |= rooms
                        for d in ds:
                            ment_speech.add(d)
                            for key in EDGE_LEX:
                                E[(s, d)][f"e_{key}"] += lex(sent, key)
                            E[(s, d)]["e_question"] += int("?" in sent)
                            E[(s, d)]["e_vote_intent"] += int(d[1:] in vint)
                    for d in ment_speech:
                        E[(s, d)]["n"] += 1
                        if r0 == rd:
                            E[(s, d)]["cur"] = 1
                        first[(s, d)] = min(first.get((s, d), 9), r0)
                # claim consistency: speaker places target in a room the target never claimed
                contradicted, placed_body = Counter(), Counter()
                for (s, d), rooms in placed.items():
                    conflict = int(bool(self_rooms[d]) and bool(rooms - self_rooms[d]))
                    at_body = int(bool(body) and body in rooms)
                    E[(s, d)]["e_place"], E[(s, d)]["e_conflict"], E[(s, d)]["e_place_body"] = 1, conflict, at_body
                    contradicted[d] += conflict
                    placed_body[d] += at_body
                    E[(s, d)].setdefault("n", 0)
                    first.setdefault((s, d), 0)
                for (s, d), c in E.items():
                    row = {"episode_id": eid, "t": t, "src": s, "dst": d, "etype": "mention",
                           "m_count": round(math.log1p(c["n"]), 4), "m_current": c["cur"],
                           "m_first_round": first[(s, d)] / 2}
                    for key in EDGE_LEX + ["question"]:
                        row[f"e_{key}"] = round(math.log1p(c[f"e_{key}"]), 4)
                    row.update(e_place=c["e_place"], e_conflict=c["e_conflict"], e_place_body=c["e_place_body"],
                               e_vote_intent=round(math.log1p(c["e_vote_intent"]), 4))
                    W["edges"].writerow(row)
                for (s, d), n in v_edge.items():
                    W["edges"].writerow({"episode_id": eid, "t": t, "src": s, "dst": d, "etype": "vote_prev",
                                         "v_count": n})
                for (s, d), n in coloc.items():
                    W["edges"].writerow({"episode_id": eid, "t": t, "src": s, "dst": d, "etype": "coloc",
                                         "c_steps": round(math.log1p(n), 4), "c_last": int((s, d) in coloc_last)})
                # nodes
                for p in alive:
                    row = {"episode_id": eid, "t": t, "node_id": p, "reporter": int(p == reporter),
                           "caller": int(p == caller), "own_speeches": n_own[p] / 3,
                           "prev_votes_received": v_recv[p], "prev_voted_rev_impostor": v_imp[p],
                           "prev_voted_rev_innocent": v_inn[p], "prev_skips": v_skip[p],
                           "n_coloc_partners": len({b for (a, b) in coloc if a == p})}
                    for key in NODE_LEX:
                        row[f"own_{key}"] = round(own[p][key] / max(n_own[p], 1), 4)
                    rr = [self_rooms_r[p][x] for x in sorted(self_rooms_r[p]) if self_rooms_r[p][x]]
                    row.update(self_rooms=min(len(self_rooms[p]), 3) / 3,
                               self_claim_change=int(len(rr) > 1 and any(not (a & b) for a, b in zip(rr, rr[1:]))),
                               self_body_room=int(bool(body) and body in self_rooms[p]),
                               contradicted_by=contradicted[p], placed_at_body_by=placed_body[p],
                               skip_intent=min(skip_int[p], 3))
                    W["nodes"].writerow(row)
                    is_crew = ident.get(p) == "Crewmate"
                    vt = votes.get(p)
                    W["node_labels"].writerow({
                        "episode_id": eid, "t": t, "node_id": p,
                        "votes_innocent": (int(vt not in (None, "SKIP") and ident.get(vt) == "Crewmate")
                                           if is_crew and vt is not None else ""),
                        "votes_skip": int(vt == "SKIP") if is_crew and vt is not None else "",
                        "is_impostor": int(ident.get(p) == "Impostor"),
                        "is_ejected": int(p == ej),
                        "votes_received": sum(1 for v in votes.values() if v == p)})
                W["graph_labels"].writerow({"episode_id": eid, "t": t,
                                            "innocent_ejected": int(ej_ident == "Crewmate"),
                                            "impostor_ejected": int(ej_ident == "Impostor"),
                                            "any_ejected": int(bool(ej)), "game_impostor_win": imp_win,
                                            "n_crew_votes_innocent": n_crew_inn})
            stats["innocent_ejected"] += int(ej_ident == "Crewmate")
            for v, tgt in votes.items():
                prev_votes.append((k, v, tgt))
            if ej:
                revealed[ej] = ej_ident
            prev_step = st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ood-models", default="", help="comma-separated matchup folder names held out as test_ood_model")
    ap.add_argument("--limit", type=int, default=0, help="max experiments (debug)")
    a = ap.parse_args()
    root, out = os.path.expanduser(a.root), os.path.expanduser(a.out)
    os.makedirs(out, exist_ok=True)
    ood = {x.strip() for x in a.ood_models.split(",") if x.strip()}
    cols = {
        "episodes": ["episode_id", "group_id", "split", "matchup", "models", "num_players", "num_impostors",
                     "winner_reason", "n_meetings"],
        "snapshots": ["episode_id", "t", "meeting", "round", "step", "n_alive", "n_speeches", "forced_share"],
        "nodes": ["episode_id", "t", "node_id"] + [n for n, _, _ in NODE_FEATURES],
        "edges": ["episode_id", "t", "src", "dst", "etype"] + [n for n, _, _ in EDGE_FEATURES],
        "graph_labels": ["episode_id", "t"] + list(GRAPH_LABELS),
        "node_labels": ["episode_id", "t", "node_id"] + list(NODE_LABELS),
    }
    files = {k: open(os.path.join(out, f"{k}.csv"), "w", newline="", encoding="utf-8") for k in cols}
    W = {k: csv.DictWriter(files[k], fieldnames=cols[k], restval=0) for k in cols}
    for w in W.values():
        w.writeheader()
    stats = Counter()
    exps = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(root, "**", "summary.json"), recursive=True)
                  if "/." not in p.replace(os.sep, "/"))
    if a.limit:
        exps = exps[:a.limit]
    for i, e in enumerate(exps):
        try:
            process_experiment(e, root, ood, W, stats)
        except Exception as ex:  # keep going, report
            stats["exp_errors"] += 1
            print(f"ERROR {e}: {ex!r}", file=sys.stderr)
        if (i + 1) % 10 == 0:
            print(f"{i + 1}/{len(exps)} experiments, {stats['games']} games, {stats['meetings']} meetings", flush=True)
    for f in files.values():
        f.close()
    schema = {"dataset": "amongus-x", "version": VERSION,
              "snapshot": "t = 3*meeting + round; labels identical within a meeting",
              "node_features": [{"name": n, "tier": t, "groups": g} for n, t, g in NODE_FEATURES],
              "edge_features": [{"name": n, "tier": t, "groups": g} for n, t, g in EDGE_FEATURES],
              "etypes": [{"name": n, "tier": t, "groups": g} for n, t, g in ETYPES],
              "graph_labels": GRAPH_LABELS, "node_labels": NODE_LABELS,
              "time_features": ["meeting", "round", "n_alive"],
              "strata": ["matchup", "num_players", "num_impostors", "round"],
              "default_drop_groups": ["privileged"], "stats": dict(stats), "experiments": len(exps)}
    json.dump(schema, open(os.path.join(out, "schema.json"), "w"), indent=1)
    print(json.dumps(dict(stats)))


if __name__ == "__main__":
    main()
