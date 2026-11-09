import json, glob, collections
base = "/Users/mauricio/sim_local/apart_vx/sim_dataset/runs_night"
n = 0; rub = collections.Counter(); first = None
for f in glob.glob(base + "/core-night_*/rep*/jury_merged.jsonl"):
    for l in open(f):
        j = json.loads(l); n += 1
        rub[j.get("rubric")] += 1
        if first is None: first = j
print("jury_merged lines", n, rub)
print(json.dumps(first)[:900])
gm = collections.Counter(); stages = collections.Counter(); nli = collections.Counter(); cov = collections.Counter()
ex = None
for f in glob.glob(base + "/core-night_*/rep*/graph_meta.json"):
    j = json.load(open(f))
    gm[j.get("catalog")] += 1
    if ex is None: ex = j
    st = j.get("stages") or j.get("columns_by_stage") or {}
    stages[json.dumps({k: [len(v.get("edge", [])) if isinstance(v, dict) else len(v)] for k, v in st.items()} if isinstance(st, dict) else str(st))] += 1
    nli[str(j.get("nli") or j.get("nli_status"))] += 1
    cov[str(j.get("jury_coverage"))] += 1
print("catalog", gm); print("nli", nli); print("coverage", cov)
print(json.dumps(ex)[:3000])
