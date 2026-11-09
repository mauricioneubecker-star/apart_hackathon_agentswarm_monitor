import json
A = json.load(open("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/oof/results.json"))
B = json.load(open("/Users/mauricio/sim_local/apart_ana/results/llm_monitor/frozen/results.json"))
print("(a) keys:", list(A.keys()))
print("(a) rows", A["rows"], "rows_common", A["rows_common"], "configs", A["configs"])
main = ["clock", "bag+graph", "zs:pairwise", "zs:global_full", "oracle"]
for n in main:
    m = A["main"][n]
    print(f"(a) {n:16s} auroc {m['auroc']:.3f} ci {m.get('auroc_ci')} auprc {m['auprc']:.3f}  r@5 {m.get('recall_at_5fpr')}")
print("(a) time-matched:", {n: round(A['slices']['time_matched_auroc'][n], 3) for n in main if n in A['slices']['time_matched_auroc']})
print("(a) mixed cfg x time:", {n: round(A['slices']['mixed_cfg_x_time_auroc'][n], 3) for n in main if n in A['slices']['mixed_cfg_x_time_auroc']})
print("(a) before_announcement:", {n: A['slices']['before_announcement'][n].get('auroc') for n in main})
print("(a) paired diff keys involving clock:", [k for k in A["paired_diffs_common_rows"] if "clock" in k][:10])
print("(a) paired diff refs:", sorted({k.split(' - ')[1].split('|')[0] for k in A["paired_diffs_common_rows"]}))
for k in ["zs:pairwise - bag+graph|auroc", "zs:global_full - bag+graph|auroc", "clock - bag+graph|auroc"]:
    print("(a)", k, A["paired_diffs_common_rows"].get(k))
print()
print("(b) split keys:", list(B["splits"]["night_test_id"].keys()))
for s, v in B["splits"].items():
    m = v["metrics"]
    au = {n: m[n].get("auroc") for n in main}
    print(f"(b) {s:22s}", {n: round(x, 3) for n, x in au.items()})
    print("     zs:global_full - clock (point):", round(au["zs:global_full"] - au["clock"], 3), " zs:pairwise - clock:", round(au["zs:pairwise"] - au["clock"], 3),
          " zs:gf - zs:pw:", round(au["zs:global_full"] - au["zs:pairwise"], 3))
    for k in ["zs:pairwise - bag+graph|auroc", "zs:global_full - bag+graph|auroc", "clock - bag+graph|auroc"]:
        d = v["paired_diffs"].get(k)
        print("    ", k, None if d is None else (round(d["mean"], 3), [round(x, 3) for x in d["ci"]]))
print("(b) any clock ref diffs:", any(k.endswith(" - clock|auroc") for k in B["splits"]["night_test_id"]["paired_diffs"]))
print("(b) thresholds clock, zs:gf:", B["thresholds"].get("clock"), B["thresholds"].get("zs:global_full"))
