"""Issue 3: reproduce the 200x paired diffs, then 1000x (and 2000x, other seeds) for MC stability."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-mauricio-Desktop-Uni-Master-1-Semester-Hackathon-apart/6b604ad8-2b8f-4c9b-91f6-20738eb16ec2/scratchpad/verify/confirm-sensitivity")
from common_cs import TAGS, load, bootstrap

DIFFS = [("zs:pairwise", "bag+graph"), ("zs:global_full", "bag+graph"), ("clock", "bag+graph")]
NAMES = ["clock", "bag+graph", "zs:global_full", "zs:pairwise"]


def fmt(t):
    return f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}] p<=0 {t[3]:.3f}"


for tag in TAGS:
    D, names, R = load(tag)
    pd_ = R["paired_diffs_common_rows"]
    print(f"== {tag}")
    runs = {}
    for nb, seed in ((200, 0), (1000, 0), (2000, 0), (1000, 1), (1000, 2)):
        runs[(nb, seed)], _ = bootstrap(D, NAMES, nb, seed=seed, diffs=DIFFS)
    for a, r in DIFFS:
        k = f"{a} - {r}"
        j = pd_[k + "|auroc"]
        print(f"  {k}")
        print(f"    json(200,s0) {j['mean']:+.3f} [{j['ci'][0]:+.3f}, {j['ci'][1]:+.3f}] p<=0 {j['p_le_0']:.3f}")
        for key, v in runs.items():
            print(f"    mine{key} {fmt(v[k])}")
