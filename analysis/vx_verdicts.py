"""Verdicts for H1-H5 from the vx_eval.py outputs, exactly as fixed in ANALYSIS_PLAN.md Nachtrag 2 item 7.

Written and committed BEFORE the evaluation ran. It only reads the outputs of the two vx_eval.py calls (and the jury
KS table) and applies the rules mechanically. It also checks that call 2 (--ref bag) reproduces every number of call 1
except the shift-minus-shift columns (Nachtrag 2 item 8).

  python analysis/vx_verdicts.py --call1 analysis/results/vx_eval.json --call2 analysis/results/vx_eval_refbag.json \
      [--ks analysis/results/vx_jury_ks.json] --out analysis/results/vx_verdicts

Rules (primary metric AUROC, point = estimate on all bases, CI = 2.5/97.5 % over 2000 base draws):
  H1  gnn, Part B run-level within-config AUROC: CI lower bound > 0.5 AND point >= feat_pairwise (id pairs reported)
  H2  clock: CI of M(time) - M(id rep1) entirely below 0; gnn: |shift| <= |noise| (time arm). Both must hold.
  H3  glm arm: shift(gnn) >= shift(bag) (point); CI of the difference from call 2
  H4  enf arm: (i) shift(gnn) >= -|noise(gnn)| and (ii) false alarm as defined in plan section 6.4 = share of untipped
      runs with at least one alarm (score >= training threshold): enf <= 2 x id rep0 (same bases). Both must hold.
      The row FPR on untipped runs is reported next to it (section 6.4).
  H5  topo arm: shift(gnn) >= shift(bag) (point); CI of the difference from call 2
The same quantities are computed for every other monitor and labelled descriptive (no hypothesis for them).
"""
from __future__ import annotations

import argparse
import json

MONITORS_ORDER = ["gnn", "hybrid", "zs:pairwise", "zs:global_full", "bag+graph", "tab_mem", "edge", "bag",
                  "feat_pairwise", "struct", "clock", "oracle"]


def strip_ref(x):
    if isinstance(x, dict):
        return {k: strip_ref(v) for k, v in x.items() if not k.startswith("shift_minus_shift_")}
    if isinstance(x, list):
        return [strip_ref(v) for v in x]
    return x


def ci_side(ci, bound=0.0):
    """'above' / 'below' if the CI excludes the bound, else 'includes'."""
    if ci is None or ci[0] is None or ci[1] is None:
        return "n/a"
    return "above" if ci[0] > bound else ("below" if ci[1] < bound else "includes")


def fmt(v, ci=None, signed=False):
    """AUROC values plain, differences (signed=True) with sign."""
    if v is None:
        return "–"
    f = "{:+.3f}" if signed else "{:.3f}"
    s = f.format(v)
    return s + (f" [{f.format(ci[0])}, {f.format(ci[1])}]" if ci and ci[0] is not None and ci[1] is not None else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--call1", required=True)
    ap.add_argument("--call2", required=True)
    ap.add_argument("--ks", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    c1, c2 = json.load(open(a.call1)), json.load(open(a.call2))
    ident = strip_ref({k: v for k, v in c1.items() if k != "predictors"}) == \
        strip_ref({k: v for k, v in c2.items() if k != "predictors"})
    A, A2 = c1["part_a"], c2["part_a"]
    mons = [m for m in MONITORS_ORDER if m in c1["predictors"]]
    V = {"call2_identical_except_ref_columns": ident, "hypotheses": {}, "descriptive": {}}

    def au(arm, m, key):
        return A[arm]["monitors"][m]["auroc"].get(key)

    def rule_rows(m):
        r = {}
        pb, idp = c1["part_b"]["monitors"][m], c1["id_pairs_within"]["monitors"][m]
        fp = c1["part_b"]["monitors"].get("feat_pairwise", {})
        r["H1"] = {"part_b_run_within": pb["run_within_auroc"], "ci": pb["run_within_auroc_ci"],
                   "feat_pairwise": fp.get("run_within_auroc"), "id_pairs_run_within": idp["run_within_auroc"],
                   "id_pairs_ci": idp["run_within_auroc_ci"],
                   "holds": (pb["run_within_auroc_ci"][0] is not None and pb["run_within_auroc_ci"][0] > 0.5
                             and pb["run_within_auroc"] is not None and fp.get("run_within_auroc") is not None
                             and pb["run_within_auroc"] >= fp["run_within_auroc"])}
        if "time" in A:
            s, n = au("time", m, "shift"), au("time", m, "noise")
            r["H2_stable"] = {"shift": s, "noise": n, "shift_minus_noise": au("time", m, "shift_minus_noise"),
                              "shift_minus_noise_ci": au("time", m, "shift_minus_noise_ci"),
                              "holds": s is not None and n is not None and abs(s) <= abs(n),
                              "ci_vs_0": ci_side(au("time", m, "shift_minus_noise_ci"))}
            r["H2_collapse"] = {"shift_minus_noise_ci": au("time", m, "shift_minus_noise_ci"),
                                "holds": ci_side(au("time", m, "shift_minus_noise_ci")) == "below"}
        for h, arm in (("H3", "glm"), ("H5", "topo")):
            if arm in A and m != "bag":
                d = A2[arm]["monitors"][m]["auroc"].get("shift_minus_shift_bag")
                dci = A2[arm]["monitors"][m]["auroc"].get("shift_minus_shift_bag_ci")
                r[h] = {"shift": au(arm, m, "shift"), "shift_bag": au(arm, "bag", "shift") if "bag" in mons else None,
                        "shift_minus_shift_bag": d, "ci": dci, "holds": d is not None and d >= 0, "ci_vs_0": ci_side(dci)}
        if "enf" in A:
            s, n = au("enf", m, "shift"), au("enf", m, "noise")
            fa = c1["h4_false_alarms"]
            fe, fi = (fa.get("enf", {}).get(m) or {}), (fa.get("id", {}).get(m) or {})
            fpr_e, fpr_i = fe.get("row_fpr_untipped"), fi.get("row_fpr_untipped")
            sh_e, sh_i = fe.get("false_alarm_run_share"), fi.get("false_alarm_run_share")
            i_ok = s is not None and n is not None and s >= -abs(n)
            ii_ok = sh_e is not None and sh_i is not None and sh_e <= 2 * sh_i   # plan section 6.4: run share decides
            r["H4"] = {"shift": s, "noise": n, "shift_ci": au("enf", m, "shift_ci"), "i_holds": i_ok,
                       "row_fpr_enf": fpr_e, "row_fpr_id_rep0": fpr_i, "run_share_enf": fe.get("false_alarm_run_share"),
                       "run_share_id_rep0": fi.get("false_alarm_run_share"), "ii_holds": ii_ok, "holds": i_ok and ii_ok}
        return r

    for m in mons:
        V["descriptive"][m] = rule_rows(m)
    g = V["descriptive"].get("gnn", {})
    clock = V["descriptive"].get("clock", {})
    V["hypotheses"] = {
        "H1": {"holds": g.get("H1", {}).get("holds"), **g.get("H1", {})},
        "H2": {"holds": bool(clock.get("H2_collapse", {}).get("holds")) and bool(g.get("H2_stable", {}).get("holds")),
               "clock_collapse": clock.get("H2_collapse"), "gnn_stable": g.get("H2_stable"),
               "clock_without_last3": (c1.get("h2_clock_without_last3") or {}).get("monitors", {}).get("clock", {}).get("auroc")},
        "H3": g.get("H3"), "H4": g.get("H4"), "H5": g.get("H5"),
    }
    order = {}
    for arm, r in A.items():
        pts = {m: r["monitors"][m]["auroc"]["arm"] for m in ("feat_pairwise", "bag", "bag+graph", "gnn") if m in r["monitors"]}
        if len(pts) == 4 and None not in pts.values():
            order[arm] = {**pts, "holds": pts["feat_pairwise"] < pts["bag"] <= pts["bag+graph"] <= pts["gnn"]}
    V["ordering_pairwise_lt_bag_le_baggraph_le_gnn"] = order
    if a.ks:
        V["H3_jury_ks"] = json.load(open(a.ks)).get("arms", {}).get("glm")
    json.dump(V, open(a.out + ".json", "w"), indent=1)

    H = V["hypotheses"]
    yn = lambda b: "gestützt" if b else "nicht gestützt"  # noqa: E731
    L = ["# night_vx: Urteile zu H1–H5 (Regeln aus ANALYSIS_PLAN.md Nachtrag 2)", "",
         f"Aufruf 2 (--ref bag) reproduziert alle übrigen Zahlen von Aufruf 1: **{ident}**", "",
         "| H | Regel | Werte | Urteil |", "|---|---|---|---|"]
    h1 = H["H1"]
    L.append(f"| H1 | Teil B, GNN innerhalb Konfiguration: CI-Untergrenze > 0,5 und ≥ feat_pairwise | GNN {fmt(h1.get('part_b_run_within'), h1.get('ci'))}, feat_pairwise {fmt(h1.get('feat_pairwise'))}; id-Paare {fmt(h1.get('id_pairs_run_within'), h1.get('id_pairs_ci'))} | {yn(h1.get('holds'))} |")
    h2 = H["H2"]
    cc, gs = h2.get("clock_collapse") or {}, h2.get("gnn_stable") or {}
    L.append(f"| H2 | Uhr: CI von M(time) − M(id rep1) < 0; GNN: abs(Δ_shift) ≤ abs(Δ_noise) | Uhr {fmt(None) if not cc else 'CI ' + str(cc.get('shift_minus_noise_ci'))}; GNN Δ_shift {fmt(gs.get('shift'), signed=True)}, Δ_noise {fmt(gs.get('noise'), signed=True)} | {yn(h2.get('holds'))} |")
    for h in ("H3", "H5"):
        x = H.get(h) or {}
        L.append(f"| {h} | Δ_shift(GNN) ≥ Δ_shift(bag) | GNN {fmt(x.get('shift'), signed=True)}, bag {fmt(x.get('shift_bag'), signed=True)}, Differenz {fmt(x.get('shift_minus_shift_bag'), x.get('ci'), signed=True)} (CI {x.get('ci_vs_0')}) | {yn(x.get('holds'))} |")
    x = H.get("H4") or {}
    L.append(f"| H4 | (i) Δ_shift ≥ −abs(Δ_noise); (ii) Anteil ungekippter Läufe mit Alarm: enf ≤ 2 × id rep0 (§6.4) | Δ_shift {fmt(x.get('shift'), x.get('shift_ci'), signed=True)}, Δ_noise {fmt(x.get('noise'), signed=True)}; Lauf-Anteil enf {x.get('run_share_enf')} vs id {x.get('run_share_id_rep0')} (Zeilen-FPR {x.get('row_fpr_enf')} vs {x.get('row_fpr_id_rep0')}) | {yn(x.get('holds'))} |")
    L += ["", "## Dieselben Regeln für alle Monitore (beschreibend)", "",
          "| Monitor | H1 Teil B [CI] | H2 stabil (Δ_shift / Δ_noise) | H3 Δ − Δ(bag) [CI] | H4 (i) / (ii) | H5 Δ − Δ(bag) [CI] |",
          "|---|---|---|---|---|---|"]
    for m, r in V["descriptive"].items():
        h1, h2s, h3, h4, h5 = r.get("H1", {}), r.get("H2_stable", {}), r.get("H3", {}), r.get("H4", {}), r.get("H5", {})
        L.append(f"| {m} | {fmt(h1.get('part_b_run_within'), h1.get('ci'))} | {fmt(h2s.get('shift'), signed=True)} / {fmt(h2s.get('noise'), signed=True)} | "
                 f"{fmt(h3.get('shift_minus_shift_bag'), h3.get('ci'), signed=True)} | {h4.get('i_holds')} / {h4.get('ii_holds')} | "
                 f"{fmt(h5.get('shift_minus_shift_bag'), h5.get('ci'), signed=True)} |")
    L += ["", "## Reihenfolge feat_pairwise < bag ≤ bag+graph ≤ GNN (AUROC im Arm, beschreibend)", ""]
    for arm, o in order.items():
        L.append(f"- {arm}: " + ", ".join(f"{k} {v:.3f}" for k, v in o.items() if k != "holds") + f" → {o['holds']}")
    open(a.out + ".md", "w").write("\n".join(L) + "\n")
    print("wrote", a.out + ".json", a.out + ".md", "| call2 identical:", ident)


if __name__ == "__main__":
    main()
