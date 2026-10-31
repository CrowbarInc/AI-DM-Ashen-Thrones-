# 08 — Comparative Evaluation

PR-PLAY-12 · 2026-10-31 America/New_York. Offline investigation and isolated prototypes only.

Scores are ordinal 0–5 (higher is better); simplicity and migration safety invert cost/risk. They are engineering assessments backed by source and finite tests, not measured live reliability or numerical safety probabilities. C/H scores describe the proposed constrained emission boundary, not guarantees for all current gameplay. Unknown catalog completeness, implementation reliability, cost and migration behavior are explicitly **uncertain**. Four is used instead of five for conditional safety designs; implementation-sensitive entries may reasonably vary by at least one point.

| Dimension | A score / evidence | B score / evidence | C score / evidence | H score / evidence |
| --- | --- | --- | --- | --- |
| Deterministic authority 25% | 2 — E8–E10/E12/E20 delivered without authority | 1 — Structured-only accepts unauthorized prose | 4 — Closed plan disallows unrepresented outcomes; public-catalog correctness unproved | 4 — Same closed guarantee in migrated lane; other operations remain legacy |
| Hidden protection 20% | 3 — Exact E11 repaired; semantic pass and paraphrases unproved | 1 — Arbitrary secret string accepted by prototype | 4 — No hidden ID/free text; positive catalog precondition uncertain | 4 — Reuse visibility owner plus closed plan; integration uncertain |
| Narrative flexibility 15% | 1 — E3/E4 rejected; exact-copy pressure | 5 — Arbitrary wording possible; no truth guarantee | 1 — Finite alternatives only, repetitive engine text | 2 — Ordering/style/variants flexible within finite grammar |
| Reliability 15% | 2 — Four histories replay; live latest rejected after prompt repair | 1 — Unsupported text accepted; no proof of complete detector | 4 — Pure deterministic plan; grammatical/integration reliability uncertain | 4 — Operation-scoped migration limits impact; integration uncertain |
| Implementation simplicity 10% | 5 — Existing path; diagnostics/normalization relatively small | 3 — Claims/segment contract and checks require nontrivial changes | 2 — Catalog, grammar, outcomes and content rendering substantial | 3 — Opening-first, reuse current state/contracts; smaller than whole-runtime C |
| Performance/token economy 10% | 4 — No judge; current large prompt and duplicated claim/prose cost | 4 — No judge but claim/segment metadata still needed | 5 — Compact IDs; could eliminate duplicated factual prose; estimate only | 4 — One existing call, compact plan; no measured token reduction |
| Migration safety 5% | 5 — Smallest delta, existing limitations retained | 2 — Changes meaning of accepted free prose and temporal premises | 2 — Broad renderer migration touches many operations | 3 — Opening-first additive switch and rollback; legacy behavior contained but unchanged |


| Weight scenario | A / 5 | B / 5 | C / 5 | H / 5 |
| --- | --- | --- | --- | --- |
| Required | 2.7 | 2.15 | 3.35 | 3.55 |
| Safety emphasis | 2.55 | 1.7 | 3.55 | 3.7 |
| Narration emphasis | 2.4 | 2.95 | 2.75 | 3.15 |
| Implementation emphasis | 3.3 | 2.3 | 3.1 | 3.45 |


Weights for each sensitivity case are in architecture_scores.json in the listed dimension order. H leads under the required weights and the three stated alternatives. This is not robust dominance: reduce H's authority and hidden scores by one each for an integration mistake and its required-weight total falls by 0.45, below C. With much greater emphasis on unrestricted prose, B can win an aesthetic score while failing the safety objective. Safety minimums therefore remain gates, not compensable score points. C and H are variants of the same positive-construction direction; the recommendation for H is a bounded migration decision, not statistically proved superiority.

| Design | False positives / negatives | Worst plausible failure and containment | Recovery / observability |
| --- | --- | --- | --- |
| A | Supported synonyms rejected; unrecognized outcomes missed | Player believes a death/resource/movement outcome absent from state. Engine state checks contain direct changes, not belief; retain final guards and add diagnostic probes. | Opening rollback on detected invalidity; accepted false negatives can log misleading text. Nested audits needed; aggregate reason is insufficient. |
| B | Claim links could be valid yet wording changes truth; strict detectors recreate A friction | An approved claim ID launders a hidden identity or outcome in its linked prose. IDs alone do not detect it; retain guards, but complete deterministic containment is unproved. | Fail closed when unsupported; no retry/judge expansion. If classifier misses prose, observability may show structurally clean unsafe text. |
| C | Unknown variants rejected; catalog omissions reduce coverage; incorrect templates misstate facts | Hidden fact incorrectly placed in public catalog is faithfully disclosed. Positive publication filtering, catalog review, reveal-receipt tests and final visibility checks are mandatory. | Reject bad plan before commit; do not silently render unvalidated raw text. Plan/anchor lineage is observable, semantic quality still human-reviewed. |
| H | Finite expression limits and operation classification mistakes; legacy gaps outside migrated lane | Capability error routes a consequential turn through an insufficient renderer or legacy lane. Bind operation/capabilities to engine resolution, disallow model selection, keep legacy policy and tests. | Opening scope remains atomic; default-off reversible rollout. Diagnostics identify operation, allowed IDs, rendering and final-selection provenance. |


No design should treat declarations or logged prose as canonical truth. A/B are rejected as the next primary direction because better opening acceptance does not prove safety, and arbitrary prose cannot be verified by source IDs alone. Broad C is deferred because replacing ordinary gameplay rendering would exceed the smallest justified pass. H permits an independently testable opening implementation while retaining current domain owners, persistence and operation-specific boundaries.
