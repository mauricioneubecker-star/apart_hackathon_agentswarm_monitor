"""Issue 6: scripted senders, solicited exposures, reversed edges, own prior mention of the shortcut."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import all_rows, fmt, load, mh_parts, signflip_cfg, summarize, win_any  # noqa: E402

runs = load()


def ex_org(o, a, ts, c):
    """DM in window from an UNINSTRUCTED agent who had violated when sending."""
    D, f, w, R = o["D"], c["f"], c["w"], o["R"]
    rr = np.arange(R + 2)
    v = (D[:, a, :] > 0) & (f[:, None] <= rr[None, :]) & (~o["instructed"])[:, None]
    return win_any(v.any(0)[None, :], w, R)[0, ts].astype(int)


def ex_scr(o, a, ts, c):
    D, f, w, R = o["D"], c["f"], c["w"], o["R"]
    rr = np.arange(R + 2)
    v = (D[:, a, :] > 0) & (f[:, None] <= rr[None, :]) & (o["instructed"])[:, None]
    return win_any(v.any(0)[None, :], w, R)[0, ts].astype(int)


def solicited_mask(o, a, f, R, lag=3):
    """[s, r]: violator DM s->a at r is solicited if a sent a direct msg to s in rounds r-lag..r-1."""
    D = o["D"]
    rr = np.arange(R + 2)
    viol = (D[:, a, :] > 0) & (f[:, None] <= rr[None, :])
    asked = win_any((D[a, :, :] > 0), lag, R)       # [s, r]: a->s within r-lag..r-1
    return viol & asked, viol & ~asked


def ex_sol(o, a, ts, c):
    sol, uns = solicited_mask(o, a, c["f"], o["R"])
    return win_any(sol.any(0)[None, :], c["w"], o["R"])[0, ts].astype(int)


def ex_uns(o, a, ts, c):
    sol, uns = solicited_mask(o, a, c["f"], o["R"])
    return win_any(uns.any(0)[None, :], c["w"], o["R"])[0, ts].astype(int)


def ex_rev(o, a, ts, c):
    """Reader a sent a direct msg to an agent who had already violated (reverse edge)."""
    D, f, R = o["D"], c["f"], o["R"]
    rr = np.arange(R + 2)
    v = (D[a, :, :] > 0) & (f[:, None] <= rr[None, :])
    return win_any(v.any(0)[None, :], c["w"], R)[0, ts].astype(int)


def self_mech_before(o, a, ts, c):
    sm = o["SelfMech"][a]
    cs = np.concatenate([[0], np.cumsum(sm)])
    return (cs[ts] > 0).astype(int)        # any own shortcut mention in rounds 0..t-1


def sent_dm_window(o, a, ts, c):
    return win_any((o["D"][a].sum(0) > 0)[None, :], c["w"], o["R"])[0, ts].astype(int)


rows = all_rows(runs, extra={"E_org": ex_org, "E_scr": ex_scr, "E_sol": ex_sol, "E_uns": ex_uns, "E_rev": ex_rev,
                             "self_mech": self_mech_before, "sent_dm": sent_dm_window})
dm = rows["dm"] == 1
E = rows["E_dir"] == 1
print("check E_dir == E_org | E_scr:", bool(np.all(rows["E_dir"] == (rows["E_org"] | rows["E_scr"]))))
for nm, sel in (("all", np.ones(len(dm), bool)), ("dm>0", dm)):
    ee = E & sel
    print(f"[{nm}] E_dir-exposed rows {ee.sum()}: with any scripted-sender DM {np.mean(rows['E_scr'][ee]==1):.3f}, "
          f"scripted-only {np.mean((rows['E_scr'][ee]==1)&(rows['E_org'][ee]==0)):.3f}; exposed ADOPTIONS {int((ee & (rows['Y']==1)).sum())}: "
          f"any scripted {np.mean(rows['E_scr'][ee & (rows['Y']==1)]==1):.3f}, scripted-only {np.mean(((rows['E_scr']==1)&(rows['E_org']==0))[ee & (rows['Y']==1)]):.3f}")
    sol_any = rows["E_sol"][ee] == 1
    print(f"   E_dir-exposed rows with a solicited exposure {sol_any.mean():.3f}; solicited-only {np.mean((rows['E_sol'][ee]==1)&(rows['E_uns'][ee]==0)):.3f}")
    for k in ("E_dir", "E_org", "E_scr", "E_sol", "E_uns", "E_rev"):
        u, M = mh_parts(rows, rows[k], sel)
        s = summarize(u, M)
        print(f"   {k:6s}", fmt(s), " signflip p", round(signflip_cfg(M), 4) if s else None)
    # organic exposure, dropping rows exposed only to scripted senders (clean comparison vs truly unexposed)
    keep = sel & ~((rows["E_scr"] == 1) & (rows["E_org"] == 0))
    u, M = mh_parts(rows, rows["E_org"], keep)
    print(f"   E_org (scripted-only rows dropped)", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
    # unsolicited only vs unexposed (drop rows with solicited exposures)
    keep = sel & ~(rows["E_sol"] == 1)
    u, M = mh_parts(rows, rows["E_uns"], keep)
    print(f"   E_uns (rows with solicited exposure dropped)", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
    keep = sel & ~(rows["E_sol"] == 1) & ~((rows["E_scr"] == 1) & (rows["E_org"] == 0))
    xx = ((rows["E_uns"] == 1) & (rows["E_org"] == 1)).astype(int)
    u, M = mh_parts(rows, xx, keep)
    print(f"   organic & unsolicited approx (rows with solicited or scripted-only exposure dropped)", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
    # E_rev controlling for E_dir: reverse edge among E_dir-unexposed rows
    u, M = mh_parts(rows, rows["E_rev"], sel & ~E)
    print(f"   E_rev among E_dir-unexposed rows", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4) if len(M) else None)
    # E_dir controlling for having sent any DM in window
    u, M = mh_parts(rows, rows["E_dir"], sel & (rows["sent_dm"] == 1))
    print(f"   E_dir among rows where the reader itself sent a DM in window", fmt(summarize(u, M)), " signflip p", round(signflip_cfg(M), 4))
    ad = sel & (rows["Y"] == 1)
    print(f"   adopters: exposed {int((ad & E).sum())} named shortcut before t {np.mean(rows['self_mech'][ad & E]):.3f} | "
          f"unexposed {int((ad & ~E).sum())} named before {np.mean(rows['self_mech'][ad & ~E]):.3f}")
    nad = sel & (rows["Y"] == 0)
    print(f"   non-adopter rows: exposed named before {np.mean(rows['self_mech'][nad & E]):.3f} | unexposed {np.mean(rows['self_mech'][nad & ~E]):.3f}")
    # E_dir stratified additionally on own prior shortcut mention
    for sm in (0, 1):
        u, M = mh_parts(rows, rows["E_dir"], sel & (rows["self_mech"] == sm))
        print(f"   E_dir | self_mech={sm}", fmt(summarize(u, M)))
np.savez_compressed(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_i6.npz"),
                    **{k: v for k, v in rows.items() if k != "cfg"}, cfg=rows["cfg"].astype(str))
