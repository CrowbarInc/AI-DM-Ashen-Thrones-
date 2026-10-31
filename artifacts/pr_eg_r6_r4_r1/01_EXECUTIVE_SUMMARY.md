# 01 — Executive Summary

**C — INCONCLUSIVE / BELOW ACCEPTANCE. Do not integrate.** Reuse works as caching, but source anchoring does not establish semantic support. Human adjudication and defensible semantic extraction precision/recall are missing. No production migration or PR-EH work was performed.

| Arm | Strict case agreement | Class agreement | Exact content agreement | Rubric acceptance flags | Off-rubric positive predictions |
|---|---:|---:|---:|---:|---:|
| A | 48/170 (28.2%) | 58/170 (34.1%) | 75/170 (44.1%) | 18/30 (60.0%) | 4/30 (13.3%) |
| B | 58/170 (34.1%) | 128/170 (75.3%) | 83/170 (48.8%) | 96/134 (71.6%) | 85/134 (63.4%) |
| C | 64/170 (37.6%) | 123/170 (72.4%) | 87/170 (51.2%) | 76/120 (63.3%) | 71/120 (59.2%) |

Strict agreement requires frozen class, exact normalized answer values and required literal qualifiers. These are offline candidate predictions, never delivered facts. The frozen scorer flags full-sentence answers as extra values even when their source supports them: its false_acceptance/unsupported_inference fields are rubric flags, NOT measured semantic falsehood rates. No corrected scores replace frozen results. Zero canonical promotion and zero gameplay disclosures occur by construction, not evidence that predictions are safe to deploy. See 31 for metric limitations and 33 for dependence/label uncertainty.
