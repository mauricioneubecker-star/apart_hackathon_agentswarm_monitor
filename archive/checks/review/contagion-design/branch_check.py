import glob, json, os, sys, hashlib
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, '/Users/mauricio/sim_local/apart_ana/sim_dataset/runner')
from labels import read_jsonl
RD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night'; SD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/scenarios/core'
out = {}
for cdir in sorted(glob.glob(os.path.join(RD, 'core-night_branch-*'))):
    sid = os.path.basename(cdir)
    sc = json.load(open(os.path.join(SD, sid + '.json')))
    instr = [a['agent_id'] for a in sc['population'] if a['flags'].get('malicious') or a['flags'].get('scripted_pioneer')]
    arms = {}
    for d in sorted(glob.glob(os.path.join(cdir, 'rep0*'))):
        arm = 'control' if d.endswith('rep0') else d.split('rep0-')[1]
        ev = read_jsonl(Path(d) / 'events.jsonl'); ms = read_jsonl(Path(d) / 'messages.jsonl')
        L = json.load(open(os.path.join(d, 'labels.json')))
        pre_ev = [json.dumps(e, sort_keys=True) for e in ev if e['round'] <= 5 and e['type'] not in ('branch_point', 'branch_start')]
        pre_ms = [json.dumps(m, sort_keys=True) for m in ms if m['round'] <= 5]
        r6_calls = None
        inj_notices = [e for e in ev if e['type'] == 'notice' and 'injection' in str(e.get('source', ''))]
        list_issues = [e for e in ev if e['type'] == 'tool' and e.get('tool') == 'list_issues' and e['round'] >= 6]
        escal = [e for e in ev if e['type'] == 'escalation' and e['round'] >= 6]
        fake_msgs = [m for m in ms if m.get('scripted_malicious') and m['round'] >= 6]
        first = L['first_violation_round']
        arms[arm] = {"h_ev": hashlib.md5('\n'.join(pre_ev).encode()).hexdigest()[:8], "n_pre_ev": len(pre_ev),
                     "h_ms": hashlib.md5('\n'.join(pre_ms).encode()).hexdigest()[:8], "n_pre_ms": len(pre_ms),
                     "viol_by_5": sum(1 for r in first.values() if r <= 5), "new_after": sum(1 for r in first.values() if r > 5),
                     "tipped": L['tipped'], "tip_round": L['tip_round'], "n_viol": L['n_violators'],
                     "inj_notices": len(inj_notices), "inj_notice_agents": len({e['agent'] for e in inj_notices}),
                     "inj_notice_rounds": sorted({e['round'] for e in inj_notices}),
                     "list_issues_calls_r6+": len(list_issues), "list_issues_agents": len({e['agent'] for e in list_issues}),
                     "escalations_r6+": len(escal), "fake_msgs": len(fake_msgs),
                     "first_after": {a: r for a, r in first.items() if r > 5},
                     "inj_reached": sorted({e['agent'] for e in inj_notices} | {e['agent'] for e in list_issues})}
    out[sid] = {"instructed": instr, "arms": arms}
    a = arms
    same = all(a[x]['h_ev'] == a['control']['h_ev'] and a[x]['h_ms'] == a['control']['h_ms'] for x in a)
    print(sid, "instr", instr, "prefix identical:", same, "| viol<=5:", [a[x]['viol_by_5'] for x in ('control', 'inject_issue_comment', 'fake_authority')],
          "| new>5:", [a[x]['new_after'] for x in ('control', 'inject_issue_comment', 'fake_authority')],
          "| tip_round:", [a[x]['tip_round'] for x in ('control', 'inject_issue_comment', 'fake_authority')])
    ia = a['inject_issue_comment']
    print("    inject: notices", ia['inj_notices'], "to", ia['inj_notice_agents'], "agents, rounds", ia['inj_notice_rounds'][:12],
          "| list_issues calls r>=6:", ia['list_issues_calls_r6+'], "by", ia['list_issues_agents'], "agents | escalations r>=6", ia['escalations_r6+'],
          "| reached agents:", len(ia['inj_reached']))
    reached = set(ia['inj_reached'])
    fa = ia['first_after']
    first_reached = {x: r for x, r in fa.items() if x in reached}
    print("    inject new violators:", len(fa), "of which reached by injection text (any time):", len(first_reached))
json.dump(out, open('branch_check.json', 'w'), indent=1, default=list)
