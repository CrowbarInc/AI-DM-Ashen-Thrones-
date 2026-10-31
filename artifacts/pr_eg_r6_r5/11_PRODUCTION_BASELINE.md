# 11 — Production Baseline

Command: `python -m experiments.pr_eg_r6_r5.run --phase baseline`

The run used the real provider (`gpt-4.1-mini`, returned id `gpt-4.1-mini-2025-04-14`), unified semantic planning on, candidate selection off, expression on, SDK retries off. Each turn restored conversational state from the family seed and the previous delivered turns. A pre-turn snapshot was stored for interventions.

| Partition | Success |
|---|---:|
| Development c01–c04 | 20/55 (36.4%) |
| Validation c05–c08 | 18/54 (33.3%) |
| Holdout c09–c12 | 21/55 (38.2%) |
| All | 59/164 (36.0%) |

| Class | Success |
|---|---:|
| DIRECT | 23/62 (37.1%) |
| PARTIAL | 2/15 (13.3%) |
| UNKNOWN | 13/47 (27.7%) |
| CLARIFICATION_REQUIRED | 7/15 (46.7%) |
| RESTRICTED | 14/22 (63.6%) |
| RELATED_NONANSWER | 0/3 (0.0%) |

Correction-tagged turns: 0/25 (0.0%). Multi-role: 4/25 (16.0%). Follow-ups: 9/35 (25.7%).

False uncertainty: 10. False clarification: 9. Mean naturalness (0–2): 0.49.

Provider calls: 205 across 164 turns (1.25 per turn). Semantic plans: 158. Expression: 27. Live interpretation: 6. Contract interpretation: 13. Strict social: 1. Retries: 0.

Six turns never entered the planner (no semantic trace). Two of those are in validation (c05t13, c07t12). Gold semantic patches were not applied to them; the intervention rows copy the baseline reply and are marked `not_intercepted`.

Integrity: restricted hits 0, topic mutations 0, seal mismatches 0, history mismatches 0. Direct selections can still record a public clue. Observed clue ids on the baseline log are public topic ids.

An earlier process reused the provider ledger file, failed closed with `RuntimeError`, and wrote `baseline_ledger_collision.jsonl`. Those rows are not this baseline.

Rows: `artifacts/pr_eg_r6_r5/baseline.jsonl`.
