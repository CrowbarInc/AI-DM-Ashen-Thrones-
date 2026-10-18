# 17 — Architectural Options


| Criterion | A: deterministic extension | B: compact bounded generation | C: dedicated dialogue agent |
| --- | --- | --- | --- |
| Player improvement | predictable known answers; narrow paraphrase variants; limited unseen follow-ups | flexible wording, preference reasons and refusals demonstrated; continuity errors remain | richer long-term behavior possible, not demonstrated |
| Safety | smallest surface, depends on correct authored reuse and classification | prompt compliance inadequate; existing semantic enforcement incomplete | same safety problem plus competing persistent goals/state |
| Changes required | templates, reuse rules and tests | task-specific authorized projection, semantic validation, final-projection compatibility, limited commitment metadata | new lifecycle/state, routing, memory, validation plus integration |
| Performance | zero-call follow-ups cheap; first narration still large unless separately changed | 350–630 input tokens in measured synthetic examples; production saving unqualified | extra calls/context likely; no measured comparison |
| Persistence | existing bounded records | reuse store; semantic contradiction/provenance improvement needed | state duplication, migration and synchronization burden |
| Regression risk | low per rule, growing interaction/special-case risk | moderate/high at routing and final emission, safety qualification required | high across authority, save/load and resolver ownership |
| Maintenance | special-case growth | fewer phrasing cases, more consequential-claim checking | highest operational and debugging burden |
| Compatibility | existing architecture; does not meet natural-dialogue objective broadly | compatible with one authority owner if host boundaries remain | risks second authority and duplicated canonical state |
| Evidence for | R1 zero-call continuity, 71 focused current passes | 14 paraphrases; cheap fluent elaborations; narration-only JSON formats | none demonstrating it is required |
| Evidence against | R1 stiffness and exact-follow-up absence replacement | repeated consequential invention, referent/payment errors, validator misses and overrejection | complexity does not repair semantic enforcement; no experiments of C |

**Choose D: further investigation required.** B is the smallest plausible candidate for a later, tightly scoped implementation if its gates pass; it is not recommended for implementation now. A remains a fallback, not a demonstrated route to the broad naturalness objective. C has no supporting necessity evidence. Provider capability, prompt design, authority context, enforcement and persistence are separate causes; adding templates or a new agent by default would conceal those distinctions.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
