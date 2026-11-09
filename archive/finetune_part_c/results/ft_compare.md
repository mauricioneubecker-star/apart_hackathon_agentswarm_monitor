# Persistence fine-tune vs. base model (ANALYSIS_PLAN.md Nachtrag 4)

Models: `qwen3.5-4b-ft` vs. `qwen3.5-4b` (same endpoint, temperature 0.7). 12 pressure probes x 5, 4 decisive-evidence probes x 5, 60 real agent turns. Judge: Claude Haiku 5.5, blind to the model, max_tokens 1500. Note: all replies re-judged with max_tokens 1500 after the first judging returned empty texts (Haiku 5.5 spent the 120-token budget on thinking); label_first = old label.

| | base | fine-tune | test |
|---|---|---|---|
| HOLD under peer pressure | 36/60 (60%, CI [0.474, 0.714]) | 48/60 (80%, CI [0.682, 0.882]) | sign test over probes 5+/3-, p = 0.7266; Fisher p = 0.0277 |
| keeps position (HOLD + RIGID) | 68% | 82% | |
| gives in (CAVE + DILUTE) | 32% | 18% | |
| UPDATE on decisive evidence | 11/20 | 5/20 | Fisher p = 0.1053 |
| valid agent JSON (single turn, no history) | 54/60 | 51/60 | Fisher p = 0.5822 |
| known action | 90% | 80% | |
| message length (words) | 20.2 | 35.7 | |
| turns with a message (descriptive, not in Nachtrag 4) | 4/60 | 6/60 | |
| unjudged replies | 0 | 0 | |

Label counts, pressure probes: base {"HOLD": 36, "CAVE": 18, "DILUTE": 1, "RIGID": 5}, fine-tune {"HOLD": 48, "DILUTE": 10, "RIGID": 1, "CAVE": 1}.
