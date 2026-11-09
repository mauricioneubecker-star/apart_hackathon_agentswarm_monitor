# night_vx: Urteile zu H1–H5 (Regeln aus ANALYSIS_PLAN.md Nachtrag 2)

Aufruf 2 (--ref bag) reproduziert alle übrigen Zahlen von Aufruf 1: **True**

| H | Regel | Werte | Urteil |
|---|---|---|---|
| H1 | Teil B, GNN innerhalb Konfiguration: CI-Untergrenze > 0,5 und ≥ feat_pairwise | GNN 0.759 [0.450, 0.974], feat_pairwise 0.517; id-Paare 1.000 [1.000, 1.000] | nicht gestützt |
| H2 | Uhr: CI von M(time) − M(id rep1) < 0; GNN: abs(Δ_shift) ≤ abs(Δ_noise) | Uhr CI [-0.0857, 0.2668]; GNN Δ_shift +0.052, Δ_noise -0.054 | nicht gestützt |
| H3 | Δ_shift(GNN) ≥ Δ_shift(bag) | GNN -0.059, bag -0.047, Differenz -0.012 [-0.189, +0.203] (CI includes) | nicht gestützt |
| H5 | Δ_shift(GNN) ≥ Δ_shift(bag) | GNN +0.104, bag +0.007, Differenz +0.097 [-0.213, +0.609] (CI includes) | gestützt |
| H4 | (i) Δ_shift ≥ −abs(Δ_noise); (ii) Anteil ungekippter Läufe mit Alarm: enf ≤ 2 × id rep0 (§6.4) | Δ_shift +0.050 [-0.123, +0.216], Δ_noise -0.054; Lauf-Anteil enf 0.3333 vs id 0.125 (Zeilen-FPR 0.0333 vs 0.0042) | nicht gestützt |

## Dieselben Regeln für alle Monitore (beschreibend)

| Monitor | H1 Teil B [CI] | H2 stabil (Δ_shift / Δ_noise) | H3 Δ − Δ(bag) [CI] | H4 (i) / (ii) | H5 Δ − Δ(bag) [CI] |
|---|---|---|---|---|---|
| gnn | 0.759 [0.450, 0.974] | +0.052 / -0.054 | -0.012 [-0.189, +0.203] | True / False | +0.097 [-0.213, +0.609] |
| hybrid | 0.690 [0.412, 0.900] | +0.023 / -0.024 | -0.017 [-0.132, +0.116] | True / True | +0.051 [-0.151, +0.387] |
| zs:pairwise | 0.759 [0.480, 0.933] | -0.027 / -0.073 | -0.051 [-0.192, +0.085] | True / True | -0.056 [-0.330, +0.265] |
| zs:global_full | 0.776 [0.516, 0.970] | -0.018 / -0.053 | +0.011 [-0.094, +0.159] | True / True | +0.034 [-0.169, +0.347] |
| bag+graph | 0.690 [0.562, 0.857] | +0.009 / -0.017 | -0.022 [-0.056, +0.013] | True / True | -0.045 [-0.089, +0.007] |
| tab_mem | 0.586 [0.350, 0.826] | -0.024 / -0.014 | -0.000 [-0.056, +0.074] | False / True | +0.002 [-0.118, +0.160] |
| edge | 0.690 [0.500, 0.893] | +0.058 / -0.057 | +0.018 [-0.048, +0.092] | True / True | -0.099 [-0.252, +0.080] |
| bag | 0.552 [0.324, 0.800] | -0.013 / +0.034 | – | True / True | – |
| feat_pairwise | 0.517 [0.294, 0.750] | +0.070 / +0.045 | +0.070 [-0.120, +0.250] | True / True | +0.131 [-0.046, +0.375] |
| struct | 0.862 [0.730, 0.975] | +0.111 / +0.110 | +0.064 [-0.066, +0.208] | True / True | +0.174 [+0.019, +0.353] |
| clock | 0.500 [0.500, 0.500] | -0.112 / -0.196 | +0.090 [-0.068, +0.267] | True / True | -0.005 [-0.297, +0.315] |
| oracle | 0.552 [0.250, 0.768] | -0.151 / -0.115 | -0.022 [-0.170, +0.135] | True / True | -0.019 [-0.197, +0.237] |

## Reihenfolge feat_pairwise < bag ≤ bag+graph ≤ GNN (AUROC im Arm, beschreibend)

- time: feat_pairwise 0.798, bag 0.752, bag+graph 0.787, gnn 0.846 → False
- glm: feat_pairwise 0.751, bag 0.718, bag+graph 0.709, gnn 0.734 → False
- enf: feat_pairwise 0.844, bag 0.744, bag+graph 0.795, gnn 0.843 → False
- topo: feat_pairwise 0.764, bag 0.766, bag+graph 0.762, gnn 0.890 → False
