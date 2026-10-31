# 32 — Comparative Results

| Arm | Strict case agreement | Class agreement | Exact content agreement | Rubric acceptance flags | Off-rubric positive predictions |
|---|---:|---:|---:|---:|---:|
| A | 48/170 (28.2%) | 58/170 (34.1%) | 75/170 (44.1%) | 18/30 (60.0%) | 4/30 (13.3%) |
| B | 58/170 (34.1%) | 128/170 (75.3%) | 83/170 (48.8%) | 96/134 (71.6%) | 85/134 (63.4%) |
| C | 64/170 (37.6%) | 123/170 (72.4%) | 87/170 (51.2%) | 76/120 (63.3%) | 71/120 (59.2%) |

Paired outcomes (left-only/right-only/both successes):
```json
{
  "AB": {
    "left_only": 21,
    "right_only": 31,
    "both": 27
  },
  "AC": {
    "left_only": 22,
    "right_only": 38,
    "both": 26
  },
  "BC": {
    "left_only": 7,
    "right_only": 13,
    "both": 51
  }
}
```

Compare both raw candidate quality and candidate-gated quality. C gate-eligible strict successes and errors are in summary.json; A has no matching post-alignment gate, so gated A is not comparable. No arm is credited with factual delivery safety from the universal delivery block. Complexity/review burden increases with role and qualifier contracts. Open vocabulary works syntactically but no architectural winner satisfies the semantic/security/cost decision criteria.
