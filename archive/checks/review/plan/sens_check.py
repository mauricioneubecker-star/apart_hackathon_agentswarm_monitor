import json, os
S = "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/sens/results"
for tag in ("t8d3", "t6d3", "t10d3", "t8d2", "t8d5"):
    d = json.load(open(os.path.join(S, tag, "frozen", "results.json")))
    sp = list(d["splits"])
    m = d["splits"][sp[0]]["metrics"]
    print(tag, "frozen splits:", sp, "| n models", len(m), "| has ext:", any(k.startswith("ext:") for k in m))
