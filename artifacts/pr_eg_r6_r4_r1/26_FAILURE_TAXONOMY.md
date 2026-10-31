# 26 — Failure Taxonomy

- F01: Unsupported extracted fact.
- F02: Missing supported fact.
- F03: Wrong relationship.
- F04: Wrong semantic role.
- F05: Lost qualifier.
- F06: Lost negation.
- F07: Epistemic strengthening.
- F08: Source identity mismatch.
- F09: Evidence span mismatch.
- F10: Question interpretation error.
- F11: Semantic alignment error.
- F12: False direct answer.
- F13: False partial answer.
- F14: Related nonanswer accepted.
- F15: Valid answer rejected.
- F16: Unsupported inference.
- F17: Authorization failure.
- F18: Provenance failure.
- F19: Evaluation disagreement.
- F20: Excessive cost.

The frozen scorer assigns only observable coarse F05/F11/F15/F16 outcomes, not every requested root cause. These are earliest *detectable scoring failures*, not proven earliest semantic causes. Source/request role errors, reported-content promotion and missing arguments require manual causal audit. Per-case raw outputs and validation reasons are preserved; no invented comprehensive causal attribution is reported.
