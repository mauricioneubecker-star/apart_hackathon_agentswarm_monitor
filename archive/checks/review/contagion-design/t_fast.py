import sys, time; sys.path.insert(0, '.')
from fastmh import load_cache, prep, mh_all
C = load_cache(); P = [prep(r) for r in C]
t0 = time.time(); o = mh_all(P, [p["f"] for p in P]); print("true:", o.round(3), f"{time.time()-t0:.1f}s")
