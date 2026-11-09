import glob, json, os, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, '/Users/mauricio/sim_local/apart_ana/sim_dataset/runner')
from labels import read_jsonl
RD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/runs_night'; SD = '/Users/mauricio/sim_local/apart_ana/sim_dataset/dataset/scenarios/core'
c = Counter(); firstc = Counter(); disc = Counter(); dec = Counter()
helped_never = 0; helped_total = 0
for d in sorted(glob.glob(os.path.join(RD, '*', 'rep*'))):
    sid = os.path.basename(os.path.dirname(d))
    if '-K4-' not in sid or not os.path.exists(os.path.join(d, 'labels.json')): continue
    if 'night_branch' in sid and os.path.exists(os.path.join(d, 'branch.json')): continue
    sc = json.load(open(os.path.join(SD, sid + '.json')))
    disc[sc['spec']['shortcut']['discoverability']] += 1; dec[sc['params'].get('decision_mechanism')] += 1
    owner = {a['ticket']['function']: a['agent_id'] for a in sc['population']}
    L = json.load(open(os.path.join(d, 'labels.json'))); first = L['first_violation_round']
    seen = set(); merged_by_other = set()
    for e in read_jsonl(Path(d) / 'events.jsonl'):
        if e['type'] == 'violation' and e.get('rule') == 'K4-skip-checks':
            own = owner.get(e.get('ticket')) == e['agent']
            c['own' if own else 'other'] += 1
            if not own: merged_by_other.add(owner.get(e.get('ticket')))
            if e['agent'] not in seen:
                seen.add(e['agent']); firstc['own' if own else 'other'] += 1
    for o in merged_by_other:
        helped_total += 1; helped_never += o not in first
print('K4 skip-check violation events by ticket ownership:', dict(c))
print('first violations by ownership:', dict(firstc))
print('owners whose ticket was skip-merged by someone else:', helped_total, '; of these never violated themselves:', helped_never)
print('discoverability:', dict(disc), 'decision:', dict(dec))
