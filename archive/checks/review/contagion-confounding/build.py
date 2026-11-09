"""Rebuild the contagion at-risk agent-round table of analysis/contagion.py (identical row set and exposure
definitions) and add confounder columns. Read-only on the run dirs; writes one pickle into the scratch dir.

  python build.py <runs_night> <scenario_dir> <runner_dir> <out_pkl> [window]
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

runs_dir, scen_dir, runner_dir, out_pkl = sys.argv[1:5]
W_OVERRIDE = int(sys.argv[5]) if len(sys.argv) > 5 else None
sys.path.insert(0, runner_dir)
from features import MECH_PATTERNS, lex_count  # noqa: E402
from labels import message_edges_typed, read_jsonl  # noqa: E402


def feed_marks(sc):
    sp = sc["runtime_rules"].get("social_proof", {})
    if not sp.get("ci_state"):
        return None
    return [t.split("<<n>>")[-1] for k, t in (sp.get("ci_text") or {}).items() if k != "green" and t]


rows = []
adopt_info = []   # per adopter: rule, ticket owner etc.
for d in sorted(glob.glob(os.path.join(runs_dir, "*", "rep*"))):
    if not os.path.exists(os.path.join(d, "labels.json")):
        continue
    sid, rep = os.path.basename(os.path.dirname(d)), os.path.basename(d)
    sc = json.load(open(os.path.join(scen_dir, sid + ".json")))
    L = json.load(open(os.path.join(d, "labels.json")))
    if "night_branch" in sid and os.path.exists(os.path.join(d, "branch.json")):
        continue   # branch arms duplicate the control prefix (same as contagion.py)
    R = sc["rounds"]
    w = W_OVERRIDE or int(sc["labels_config"]["window_w"])
    pop = sc["population"]
    ag = {a["agent_id"]: a for a in pop}
    agents = set(ag)
    instructed = {a["agent_id"] for a in pop if a["flags"].get("malicious") or a["flags"].get("scripted_pioneer")}
    stuck = {a["agent_id"] for a in pop if not a["ticket"]["solvable"] or a["ticket"].get("blocked_by_unsolvable_dep")}
    first = {a: r for a, r in L["first_violation_round"].items() if a in agents}
    owner_of = {a["ticket"]["function"]: a["agent_id"] for a in pop}
    p = sc["params"]

    # ---- static relations
    dep_nb = defaultdict(set)    # undirected dependency relation (dep owner <-> dependent)
    rev_nb = defaultdict(set)    # reviewer <-> owner
    clar_nb = defaultdict(set)   # clarification holder <-> owner
    for a in pop:
        x = a["agent_id"]
        for o in a["ticket"].get("dep_owners") or []:
            if o in agents and o != x:
                dep_nb[x].add(o); dep_nb[o].add(x)
        for f in a["ticket"].get("dependents") or []:
            o = owner_of.get(f)
            if o and o != x:
                dep_nb[x].add(o); dep_nb[o].add(x)
        for o in a["ticket"].get("reviewers") or []:
            if o in agents and o != x:
                rev_nb[x].add(o); rev_nb[o].add(x)
        o = a["ticket"].get("clarification_holder")
        if o in agents and o != x:
            clar_nb[x].add(o); clar_nb[o].add(x)
    # dependency neighbours that are themselves stuck (share the blocked chain)
    def rel(s, a):
        return {"dep": s in dep_nb[a], "rev": s in rev_nb[a], "clar": s in clar_nb[a],
                "team": ag[s]["team"] == ag[a]["team"], "model": ag[s]["model"] == ag[a]["model"]}

    msgs = read_jsonl(Path(d) / "messages.jsonl")
    events = read_jsonl(Path(d) / "events.jsonl")
    rounds = read_jsonl(Path(d) / "rounds.jsonl")

    # ---- per reader: direct / any incoming edges with sender
    din = defaultdict(list)    # reader -> [(round, sender, mech)]
    dchan = defaultdict(list)  # reader -> [(round, sender, is_private_dm)] for direct edges
    anyin = defaultdict(list)  # reader -> [(round, sender)]
    sent = defaultdict(list)   # sender -> [(round, set(direct targets), set(all recipients))]
    own_mech = defaultdict(list)    # agent -> rounds in which the agent itself wrote a shortcut-naming message
    own_stuck = defaultdict(list)   # agent -> rounds in which the agent itself wrote a blocked/contradiction message
    STUCK_LEX = re.compile(r"contradict|conflict|impossible|cannot both|can't both|mutually exclusive|blocked|stuck|"
                           r"inconsistent|incompatible|spec (says|disagrees)|regression check", re.I)
    for m in msgs:
        if m.get("kind") not in ("agent", "review") or not str(m.get("text", "")).strip():
            continue
        r, s = m["round"], m["sender"]
        mech = lex_count(m["text"], MECH_PATTERNS) > 0
        if mech:
            own_mech[s].append(r)
        if STUCK_LEX.search(m["text"]):
            own_stuck[s].append(r)
        dts = set()
        for _, dst, kind in message_edges_typed(m):
            if kind == "direct":
                din[dst].append((r, s, mech))
                dchan[dst].append((r, s, m["channel"] == "dm"))
                dts.add(dst)
            anyin[dst].append((r, s))
        sent[s].append((r, dts, set(m.get("recipients") or [])))

    # ---- merge feed (constant within a round; kept for completeness)
    marks = feed_marks(sc)
    feed = defaultdict(set)
    if marks:
        for m in msgs:
            if m.get("sender") == "ext:status-bot" and any(x in str(m.get("text", "")) for x in marks):
                for rc in m.get("recipients") or []:
                    feed[rc].add(m["round"])
        for e in events:
            if e.get("type") == "notice" and "status-bot" in str(e.get("source", "")) and any(x in str(e.get("text", "")) for x in marks):
                feed[e.get("agent")].add(e["round"])

    # ---- dynamic receiver state
    active_after = {rr["round"]: set(rr.get("active") or []) for rr in rounds}
    status_after = {rr["round"]: rr.get("tickets") or {} for rr in rounds}
    credits_after = {rr["round"]: rr.get("credits") or {} for rr in rounds}
    first_red = {}
    first_esc = {}
    first_inj_read = {}
    inj = [(rr["round"], ev) for rr in sc["timeline"] for ev in rr["events"] if ev.get("type") == "injection"]
    inj_snip = [ev["text"].lstrip("> ")[:40] for _, ev in inj]
    inj_paths = {ev.get("target_path") for _, ev in inj if ev.get("target_path")}
    inj_r0 = min([r0 for r0, _ in inj], default=None)
    acted = defaultdict(set)   # agent -> rounds with a tool / escalation / defer / stop event
    for e in events:
        a, r = e.get("agent"), e.get("round")
        if a not in agents:
            continue
        if e["type"] in ("tool", "escalation", "defer", "stop", "invalid_json", "unknown_action"):
            acted[a].add(r)
        if e["type"] == "tool":
            res = str(e.get("result", ""))
            if (e.get("tool") == "run_tests" and str((e.get("args") or {}).get("suite", "")).startswith("accept")
                    and "RED" in res[:200]) or (e.get("tool") == "merge" and "acceptance checks failing" in res):
                first_red.setdefault(a, r)
            if inj_r0 is not None and r >= inj_r0 and e.get("tool") in ("read_file", "search_docs"):
                if str((e.get("args") or {}).get("path", "")) in inj_paths or any(sn and sn in res for sn in inj_snip):
                    first_inj_read.setdefault(a, r)
        if e["type"] == "escalation":
            first_esc.setdefault(a, r)
    first_att = L.get("first_attempt_round") or {}
    # private (agent-specific) exposure to an EXTERNAL shortcut instruction before t: tool-output injection seen in
    # an acceptance run, injected doc read, issue-comment injection (escalation / list_issues), fake-authority DM
    ext_seen = {}
    inj_by = {ev["carrier"]: (r0, ev) for r0, ev in inj}
    for e in events:
        a, r = e.get("agent"), e.get("round")
        if a not in agents or e["type"] not in ("tool", "escalation"):
            continue
        tool, args, res = e.get("tool"), (e.get("args") or {}), str(e.get("result", ""))
        hit = False
        if "tool_output" in inj_by and r >= inj_by["tool_output"][0] and tool == "run_tests" \
                and not str(args.get("suite", "acceptance")).startswith("unit") and ("GREEN" in res[:200] or "RED" in res[:200]):
            hit = True
        if "doc" in inj_by and r >= inj_by["doc"][0] and tool in ("read_file", "search_docs"):
            tp = inj_by["doc"][1].get("target_path", "")
            if str(args.get("path", "")).lstrip("./") == tp or inj_by["doc"][1]["text"].lstrip("> ")[:30] in res \
                    or (tool == "search_docs" and "skip_checks" in res):
                hit = True
        if "issue_comment" in inj_by and r >= inj_by["issue_comment"][0] and (e["type"] == "escalation" or tool == "list_issues"):
            hit = True
        if hit:
            ext_seen.setdefault(a, r)
    for m in msgs:
        if str(m.get("sender", "")).startswith("ext:") and m.get("scripted_malicious") and m.get("channel") == "dm":
            for rc in m.get("recipients") or []:
                if rc in agents:
                    ext_seen.setdefault(rc, m["round"])
    # non-message channel: check_status shows teammates' merges with their CI state (bypassed / quarantined)
    saw_team_viol = {}
    for e in events:
        if e["type"] == "tool" and e.get("tool") == "check_status" and e.get("agent") in agents:
            res = str(e.get("result", ""))
            if "bypassed with skip_checks" in res or "quarantined in" in res:
                saw_team_viol.setdefault(e["agent"], e["round"])
    # QA corrected the acceptance check of the owner's ticket (ticket no longer impossible), and
    # K2 proxy quarantine: somebody else added the owner's acceptance check to .ci/scoring.toml
    qa_fixed = {}
    proxy_q = {}
    for e in events:
        if e["type"] == "qa_fix" and e.get("owner") in agents:
            qa_fixed.setdefault(e["owner"], e["round"])
        if e["type"] == "violation" and e.get("rule") == "K2-scoring-write":
            pass
        if e["type"] == "tool" and "args_full" in e and "scoring" in str((e.get("args") or {}).get("path", "")):
            af = e["args_full"]
            new = str(af.get("new", af.get("content", "")))
            old = str(af.get("old", ""))
            for fn in set(re.findall(r"acceptance/test_(\w+)\.py", new)) - set(re.findall(r"acceptance/test_(\w+)\.py", old)):
                o = owner_of.get(fn)
                if o and o != e.get("agent"):
                    proxy_q.setdefault(o, e["round"])

    # adopters' first violation details
    fv_ev = {}
    for e in events:
        if e["type"] == "violation" and e.get("agent") in first and e["round"] == first[e["agent"]] and e["agent"] not in fv_ev:
            fv_ev[e["agent"]] = e

    run = f"{sid}/{rep}"
    for a in sorted(agents - instructed):
        fa = first.get(a, 99)
        A = ag[a]
        tk = A["ticket"]
        sub = ("own" if not tk["solvable"] else "free") if not tk.get("blocked_by_unsolvable_dep") else \
              ("both" if not tk["solvable"] else "dep")
        n_unsolv_depowners = sum(1 for o in tk.get("dep_owners") or [] if o in agents and not ag[o]["ticket"]["solvable"])
        for t in range(1, min(R, fa) + 1):
            lo = max(1, t - w)
            Dw = [(r, s, mech) for (r, s, mech) in din[a] if lo <= r < t]
            Aw = [(r, s) for (r, s) in anyin[a] if lo <= r < t]
            # sender classes
            vio_d = [(r, s, mech) for (r, s, mech) in Dw if first.get(s, 99) <= r]
            plc_d = [(r, s, mech) for (r, s, mech) in Dw if first.get(s, 99) > r and s in first and first[s] > t]
            Cw = [(r, s, pv) for (r, s, pv) in dchan[a] if lo <= r < t]
            E_priv = int(any(pv and first.get(s, 99) <= r for r, s, pv in Cw))
            E_pub = int(any((not pv) and first.get(s, 99) <= r for r, s, pv in Cw))
            P_priv = int(any(pv and s in first and first[s] > t for r, s, pv in Cw))
            P_pub = int(any((not pv) and s in first and first[s] > t for r, s, pv in Cw))
            vio_any = [(r, s) for (r, s) in Aw if first.get(s, 99) <= r]
            row = {
                "cfg": sid, "run": run, "t": t, "stuck": int(a in stuck), "Y": int(fa == t), "agent": a,
                "E_dir": int(bool(vio_d)), "E_any": int(bool(vio_any)), "E_mech": int(any(m for _, _, m in vio_d)),
                "E_feed": int(any(lo <= r < t for r in feed[a])), "P_dir": int(bool(plc_d)), "dm_any": int(bool(Dw)),
                "n_dm": len(Dw), "n_dm_senders": len({s for _, s, _ in Dw}),
                "n_vio_senders": len({s for _, s, _ in vio_d}),
                "E_priv": E_priv, "E_pub": E_pub, "P_priv": P_priv, "P_pub": P_pub,
            }
            # relation-specific exposures: sender in agents only (ext: senders are never violators)
            for tag, lst in (("E", vio_d), ("P", plc_d)):
                ss = [s for _, s, _ in lst if s in agents]
                rels = [rel(s, a) for s in ss]
                row[f"{tag}_dep"] = int(any(x["dep"] for x in rels))
                row[f"{tag}_rev"] = int(any(x["rev"] for x in rels))
                row[f"{tag}_clar"] = int(any(x["clar"] for x in rels))
                row[f"{tag}_anyrel"] = int(any(x["dep"] or x["rev"] or x["clar"] for x in rels))
                row[f"{tag}_norel"] = int(any(not (x["dep"] or x["rev"] or x["clar"]) for x in rels))
                row[f"{tag}_nodep"] = int(any(not x["dep"] for x in rels))
                row[f"{tag}_samemodel"] = int(any(x["model"] for x in rels))
                row[f"{tag}_diffmodel"] = int(any(not x["model"] for x in rels))
                row[f"{tag}_sameteam"] = int(any(x["team"] for x in rels))
                row[f"{tag}_diffteam"] = int(any(not x["team"] for x in rels))
                row[f"{tag}_instr"] = int(any(s in instructed for s in ss))
                row[f"{tag}_uninstr"] = int(any(s not in instructed for s in ss))
                row[f"{tag}_lead"] = int(any(ag[s]["flags"].get("tech_lead") for s in ss))
                row[f"{tag}_auditor"] = int(any(ag[s]["role"] == "auditor" or ag[s]["flags"].get("is_auditor") for s in ss))
                row[f"{tag}_reviewerrole"] = int(any(ag[s]["role"] == "reviewer" for s in ss))
                row[f"{tag}_plainsender"] = int(any(not (s in instructed or ag[s]["flags"].get("tech_lead") or
                                                         ag[s]["role"] in ("auditor", "reviewer") or
                                                         ag[s]["flags"].get("is_auditor") or ag[s]["flags"].get("info_asym"))
                                                    for s in ss))
                row[f"{tag}_infoasym"] = int(any(ag[s]["flags"].get("info_asym") for s in ss))
                row[f"{tag}_stucksender"] = int(any(s in stuck for s in ss))
                # pure: every such sender lacks any structural relation, same model and same team
                row[f"{tag}_strict"] = int(any(not (x["dep"] or x["rev"] or x["clar"] or x["model"] or x["team"]) and s not in instructed
                                               for x, s in zip(rels, ss)))
            # solicited: receiver had sent the violator a message (any channel, direct target) in [t-w-3, t)
            vs = {s for _, s, _ in vio_d}
            row["E_solicited"] = int(any(any(lo - 3 <= r < t and s2 in dts for (r, dts, _) in sent[a]) for s2 in vs))
            row["E_unsolicited"] = int(any(not any(lo - 3 <= r < t and s2 in dts for (r, dts, _) in sent[a]) for s2 in vs))
            ps = {s for _, s, _ in plc_d}
            row["P_solicited"] = int(any(any(lo - 3 <= r < t and s2 in dts for (r, dts, _) in sent[a]) for s2 in ps))
            row["P_unsolicited"] = int(any(not any(lo - 3 <= r < t and s2 in dts for (r, dts, _) in sent[a]) for s2 in ps))
            # refined: a sender's DM at round r counts as solicited if the receiver had directly addressed that sender in
            # rounds [r-3, r-1] (strictly earlier: same-round messages are generated simultaneously)
            def solicited(r, s):
                return any(r - 3 <= r2 < r and s in dts for (r2, dts, _) in sent[a])
            row["E_sol2"] = int(any(solicited(r, s) for r, s, _ in vio_d))
            row["E_unsol2"] = int(any(not solicited(r, s) for r, s, _ in vio_d))
            row["P_sol2"] = int(any(solicited(r, s) for r, s, _ in plc_d))
            row["P_unsol2"] = int(any(not solicited(r, s) for r, s, _ in plc_d))
            # receiver contacted a CURRENT violator (after that agent's violation) before the window: interest in the shortcut
            row["rx_contacted_violator_prewin"] = int(any(r2 < lo and any(first.get(x, 99) <= r2 for x in dts)
                                                          for (r2, dts, _) in sent[a]))
            row["n_sent_win"] = sum(1 for (r, _, _) in sent[a] if lo <= r < t)
            row["sent_dir_win"] = int(any(lo <= r < t and dts for (r, dts, _) in sent[a]))
            # receiver statics
            row.update({
                "model": A["model"], "persona": A["persona"], "role": A["role"], "team": A["team"],
                "lead": int(bool(A["flags"].get("tech_lead"))), "auditor": int(A["role"] == "auditor" or bool(A["flags"].get("is_auditor"))),
                "info_asym": int(bool(A["flags"].get("info_asym"))), "carry_over": int(bool(A["flags"].get("carry_over"))),
                "persistent": int(bool(A["flags"].get("persistent"))), "subtype": sub,
                "solvable": int(bool(tk["solvable"])), "blocked_dep": int(bool(tk.get("blocked_by_unsolvable_dep"))),
                "n_deps": len(tk.get("deps") or []), "n_dependents": len(tk.get("dependents") or []),
                "n_unsolv_depowners": n_unsolv_depowners, "difficulty": tk.get("difficulty"),
                "n_dep_nb": len(dep_nb[a]), "n_dm_neighbors": len(A.get("dm_neighbors") or []),
                "channels": p.get("channels"), "category": p.get("category"), "discoverability": p.get("discoverability"),
                "seed_kind": ("pioneer" if p.get("scripted_pioneer") else
                              ((sc.get("malicious") or {}).get("actors") or [{}])[0].get("variant", "none")
                              if p.get("malicious_count") else ("info_asym" if p.get("early_adopter_source") == "info_asym" else "none")),
                "decision": p.get("decision_mechanism"), "model_mix": p.get("model_mix"),
            })
            # receiver dynamics, all measured before round t (state at the start of round t)
            row["active"] = int(t == 1 or a in active_after.get(t - 1, agents))
            st = status_after.get(t - 1, {}).get(tk["function"], "open") if t > 1 else "open"
            row["own_status"] = st
            row["red_seen"] = int(first_red.get(a, 99) < t)
            row["red_seen_prewin"] = int(first_red.get(a, 99) < lo)
            row["esc_before"] = int(first_esc.get(a, 99) < t)
            row["esc_prewin"] = int(first_esc.get(a, 99) < lo)
            row["att_before"] = int(first_att.get(a, 99) < t)
            row["att_prewin"] = int(first_att.get(a, 99) < lo)
            row["inj_read"] = int(first_inj_read.get(a, 99) < t)
            row["acted_prev"] = int((t - 1) in acted[a]) if t > 1 else 1
            row["rx_mech_prewin"] = int(any(r < lo for r in own_mech[a]))
            row["rx_mech_before"] = int(any(r < t for r in own_mech[a]))
            row["rx_stuck_prewin"] = int(any(r < lo for r in own_stuck[a]))
            row["rx_stuck_before"] = int(any(r < t for r in own_stuck[a]))
            row["qa_fixed"] = int(qa_fixed.get(a, 99) < t)
            fr = first_red.get(a, 99)
            row["since_red_bin"] = -1 if fr >= t else min((t - fr) // 2, 3)   # -1 never red, 0: 1-2 rounds, 1: 3-4, 2: 5-6, 3: 7+
            fe = first_esc.get(a, 99)
            row["since_esc_bin"] = -1 if fe >= t else min((t - fe) // 2, 3)
            cr = (credits_after.get(t - 1, {}) or {}).get(a) if t > 1 else None
            row["credits_bin"] = -1 if cr is None else int(np.digitize(cr / max(1, A.get("credits") or 1), [0.25, 0.5, 0.75]))
            row["saw_team_viol"] = int(saw_team_viol.get(a, 99) < t)
            row["ext_seen"] = int(ext_seen.get(a, 99) < t)
            row["ext_seen_prewin"] = int(ext_seen.get(a, 99) < lo)
            row["inj_carrier"] = ",".join(sorted(inj_by)) or "none"
            row["proxy_q"] = int(proxy_q.get(a, 99) < t)
            row["n_viol_team_before"] = sum(1 for x, fx in first.items() if fx < t and x != a and ag[x]["team"] == A["team"])
            # violators among structural neighbours (shared blocked chain / shared reviewer)
            row["n_viol_total_before"] = sum(1 for x, fx in first.items() if fx < t)
            row["depnb_viol_before"] = int(any(first.get(o, 99) < t for o in dep_nb[a]))
            row["dmnb_viol_before"] = int(any(first.get(o, 99) < t for o in (A.get("dm_neighbors") or [])))
            if fa == t:
                e = fv_ev.get(a, {})
                tko = owner_of.get(e.get("ticket")) if e.get("ticket") else None
                row["fv_rule"] = e.get("rule")
                row["fv_ticket_owner_is_self"] = (tko == a) if tko else None
                row["fv_ticket_owner_is_vio_sender"] = (tko in vs) if tko else None
            rows.append(row)

df = pd.DataFrame(rows)
df.to_pickle(out_pkl)
print(f"rows {len(df)}, adoptions {int(df.Y.sum())}, runs {df.run.nunique()}, configs {df.cfg.nunique()}")
