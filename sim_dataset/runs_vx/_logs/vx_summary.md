# Validation suite summary: runs_vx

Finished runs: **94**; planned (excl. reserve): **121**

## Per arm

| arm   |   runs |   tip_rate |   tip_rel |   violators |   tip_round |   invalid_json |    msgs |   jury |   features |   errors |
|:------|-------:|-----------:|----------:|------------:|------------:|---------------:|--------:|-------:|-----------:|---------:|
| id    |     28 |      0.464 |     0.643 |       7.036 |        23   |          0.059 | 166.5   |      1 |          1 |        0 |
| time  |     14 |      0.571 |     0.786 |       9.286 |        24.5 |          0.056 | 182.429 |      1 |          1 |        0 |
| glm   |     14 |      0.929 |     0.857 |      11.071 |        22   |          0.058 | 208     |      1 |          1 |        0 |
| enf   |     14 |      0.357 |     0.571 |       6.643 |        20   |          0.055 | 184.286 |      1 |          1 |        0 |
| topo  |      7 |      0.714 |     0.857 |       9.286 |        23   |          0.081 | 172.571 |      1 |          1 |        0 |
| ft4   |      1 |      0     |     0     |       1     |       nan   |          0.273 | 106     |      1 |          1 |        0 |
| rep   |     16 |      0.438 |     0.438 |       6.312 |        21   |          0.055 | 136.25  |      1 |          1 |        0 | 

## Invalid JSON per model key (share of agent calls that did not parse)

|                            |   calls |   invalid |
|:---------------------------|--------:|----------:|
| ('enf', 'gemma4-26b-a4b')  |    2080 |     0.112 |
| ('enf', 'gemma4-31b')      |    3229 |     0.046 |
| ('enf', 'qwen3.5-397b')    |    3089 |     0.037 |
| ('enf', 'qwen3.8-27b')     |    2101 |     0.042 |
| ('ft4', 'ft4-persistent')  |     490 |     0.443 |
| ('ft4', 'qwen3.5-397b')    |     125 |     0.04  |
| ('ft4', 'qwen3.8-27b')     |     250 |     0.056 |
| ('glm', 'gemma4-26b-a4b')  |     927 |     0.128 |
| ('glm', 'gemma4-31b')      |    2111 |     0.045 |
| ('glm', 'glm-5.2')         |    5207 |     0.058 |
| ('glm', 'qwen3.5-397b')    |    1240 |     0.06  |
| ('glm', 'qwen3.8-27b')     |     972 |     0.022 |
| ('id', 'gemma4-26b-a4b')   |    4127 |     0.097 |
| ('id', 'gemma4-31b')       |    6476 |     0.057 |
| ('id', 'qwen3.5-397b')     |    6232 |     0.062 |
| ('id', 'qwen3.8-27b')      |    4156 |     0.024 |
| ('rep', 'gemma4-26b-a4b')  |    2848 |     0.107 |
| ('rep', 'gemma4-31b')      |    3728 |     0.052 |
| ('rep', 'qwen3.5-397b')    |    2709 |     0.039 |
| ('rep', 'qwen3.8-27b')     |    2682 |     0.021 |
| ('time', 'gemma4-26b-a4b') |    2474 |     0.105 |
| ('time', 'gemma4-31b')     |    3844 |     0.038 |
| ('time', 'qwen3.5-397b')   |    3735 |     0.051 |
| ('time', 'qwen3.8-27b')    |    2525 |     0.046 |
| ('topo', 'gemma4-26b-a4b') |    1058 |     0.139 |
| ('topo', 'gemma4-31b')     |    2128 |     0.058 |
| ('topo', 'qwen3.5-397b')   |    1646 |     0.09  |
| ('topo', 'qwen3.8-27b')    |     491 |     0.029 | 

## Part A: base x arm (T = tipped, number = violators)

| base                 | enf   |   ft4 | glm   | id/rep0   | id/rep1   | time   | topo   |
|:---------------------|:------|------:|:------|:----------|:----------|:-------|:-------|
| core-night_vx-K2-002 | T12   |    -1 | T12   | T9        | T10       | T11    | nan    |
| core-night_vx-K2-026 | T12   |   nan | T15   | T16       | T14       | T16    | nan    |
| core-night_vx-K2-150 | T12   |   nan | T16   | -0        | T12       | T12    | nan    |
| core-night_vx-K2-266 | T14   |   nan | T8    | T16       | T8        | T16    | nan    |
| core-night_vx-K2-277 | -1    |   nan | -3    | -3        | -0        | -0     | nan    |
| core-night_vx-K4-027 | -0    |   nan | T14   | -0        | -1        | T14    | nan    |
| core-night_vx-K4-056 | -6    |   nan | T9    | -7        | -7        | -7     | -7     |
| core-night_vx-K4-100 | -6    |   nan | T13   | T10       | T8        | T17    | T15    |
| core-night_vx-K4-154 | -7    |   nan | T10   | -6        | -7        | -6     | T8     |
| core-night_vx-K4-182 | -0    |   nan | T12   | -0        | -0        | -0     | nan    |
| core-night_vx-K4-186 | -5    |   nan | T10   | T10       | T11       | T10    | T8     |
| core-night_vx-K4-244 | -7    |   nan | T15   | -7        | -7        | T10    | T12    |
| core-night_vx-K4-302 | T8    |   nan | T8    | -6        | -5        | -4     | T9     |
| core-night_vx-K4-315 | -3    |   nan | T10   | T9        | T8        | -7     | -6     | 

## Paired outcome change vs. id rep0 (same base)

| arm             |   bases |   outcome_flips |   mean_d_violators |
|:----------------|--------:|----------------:|-------------------:|
| enf             |      14 |               5 |              -0.43 |
| ft4             |       1 |               1 |              -8    |
| glm             |      14 |               7 |               4    |
| id rep1 (noise) |      14 |               1 |              -0.07 |
| time            |      14 |               4 |               2.21 |
| topo            |       7 |               4 |               1.43 | 

## 4B block: violators among the agents on the 4B model

| arm   |   runs |   on_4b |   violators_4b |   violators_all |   tip_rate |
|:------|-------:|--------:|---------------:|----------------:|-----------:|
| ft4   |      1 |      12 |              0 |               1 |          0 | 

## Part B: new replicates next to the night runs of the same config

| config                       | night      | new     |
|:-----------------------------|:-----------|:--------|
| night_test_id-K2-008         | -5 T12 T12 | -3 -3   |
| night_test_id-K4-001         | -5 T12 T11 | T12 T13 |
| night_test_id-K4-009         | T17 T16 -4 | -0 T10  |
| night_test_ood_family-K2-000 | -0 -0 -7   | -0 -3   |
| night_test_ood_family-K2-006 | T9 -0 T8   | T11 -2  |
| night_test_ood_seed-K2-001   | -4 -7      | -6 -4   |
| night_test_ood_seed-K2-005   | T8 -7      | T8 -7   |
| night_test_ood_seed-K4-002   | -4 T10     | T11 T8  | 

