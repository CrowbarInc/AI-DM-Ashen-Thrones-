# 31 — Quality Metrics

| Arm | Strict case agreement | Class agreement | Exact content agreement | Rubric acceptance flags | Off-rubric positive predictions |
|---|---:|---:|---:|---:|---:|
| A | 48/170 (28.2%) | 58/170 (34.1%) | 75/170 (44.1%) | 18/30 (60.0%) | 4/30 (13.3%) |
| B | 58/170 (34.1%) | 128/170 (75.3%) | 83/170 (48.8%) | 96/134 (71.6%) | 85/134 (63.4%) |
| C | 64/170 (37.6%) | 123/170 (72.4%) | 87/170 (51.2%) | 76/120 (63.3%) | 71/120 (59.2%) |


Exact numerators/denominators for class strata, partitions, contexts, categories, false rejections and gate-eligible candidate errors are in summary.json. Direct recovery uses the expected DIRECT denominator; partial correctness uses PARTIAL; related-nonanswer rejection uses exact RELATED_NONANSWER class agreement. qualifier_preserved is vacuous on negative cases with no required qualifiers; do not interpret its all-case rate as qualifier fidelity. Unsupported inference counts positive candidate classes/values outside frozen answers; missing literal qualifiers is a separate false-acceptance cause. Frozen exact-match values/phrases can overstate semantic failures.

Extraction semantic precision/recall, fully general role preservation, implicit entailment and semantic generalization remain unmeasured pending adjudication. Reference exact-role-value/qualifier coverage is a transparent diagnostic, not a substitute. No denominator invents reviewed claims. Reuse is demonstrated structurally; successful semantic reuse is each family's 0–5 answer successes, not universal extraction correctness.
