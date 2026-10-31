# 23 — Paired Results

Same validation turns, same pre-turn snapshots, cached semantic proposal. Holdout was not intervened on.

| Arm | Fixed | Lost | Net | Success |
|---|---:|---:|---:|---:|
| I10C | 35 | 0 | +35 | 53/54 (98.1%) |
| I10B | 28 | 1 | +27 | 45/54 (83.3%) |
| I8 | 27 | 1 | +26 | 44/54 (81.5%) |
| I9 | 14 | 0 | +14 | 32/54 (59.3%) |
| question_source | 8 | 0 | +8 | 26/54 (48.1%) |
| correspondence_sufficiency | 6 | 0 | +6 | 24/54 (44.4%) |
| intent_referent | 5 | 0 | +5 | 23/54 (42.6%) |
| I2 | 4 | 0 | +4 | 22/54 (40.7%) |
| I6 | 4 | 0 | +4 | 22/54 (40.7%) |
| retrieval_correspondence | 4 | 0 | +4 | 22/54 (40.7%) |
| I7 | 2 | 0 | +2 | 20/54 (37.0%) |
| I1 | 1 | 0 | +1 | 19/54 (35.2%) |
| I4 | 0 | 0 | +0 | 18/54 (33.3%) |
| I3 | 1 | 3 | -2 | 16/54 (29.6%) |
| I5 | 0 | 3 | -3 | 15/54 (27.8%) |

Reading rule: a net near zero on an isolated arm does not mean the stage is unimportant. I3 and I5 are negative alone and positive together. I4 stays zero even in combination with I6, which is evidence that id filtering is not the lever.

Full rows: `interventions.jsonl`, `expression_control.jsonl`, `summary.json`.
