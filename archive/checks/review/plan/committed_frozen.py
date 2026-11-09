import json, subprocess
REPO = "/Users/mauricio/sim_local/apart_ana"
for c in ("a6c1d8a", "68744e2"):
    s = subprocess.run(["git", "-C", REPO, "show", f"{c}:results/llm_monitor/frozen/results.json"], capture_output=True, text=True).stdout
    d = json.loads(s)
    print("==", c, "top keys", list(d.keys()))
    for sp, v in d["splits"].items():
        m = v["metrics"]
        names = list(m)
        n0 = names[0]
        print(f"  {sp}: n_models={len(names)} rows={m[n0].get('n')} pos={m[n0].get('n_pos')}")
        print("     models:", names)
        if "clock" in m and "zs:global_full" in m:
            print("     clock auroc", m["clock"].get("auroc"), "zs:global_full auroc", m["zs:global_full"].get("auroc"))
    print("  vx_shift present:", d.get("vx_shift") is not None)
