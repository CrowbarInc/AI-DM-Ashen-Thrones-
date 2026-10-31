# 04 — Conversational and Gameplay Evaluation

All product-level ratings below concern representative post-repair gameplay. Green deterministic checks cannot change them to Pass.

| Dimension | Rating | Evidence / limit |
|---|---|---|
| P1 Startup reliability | Blocked | DNS prevents live opening; six reset tests validate the reset owner only |
| P2 Conversational comprehension | Blocked | Corrected request wording/routing/participant controls pass; no actual new model interpretation |
| P3 Answer usefulness | Blocked | Evidence authorization and controlled honest-limit/clarification branches pass; model selection and answer relevance unobserved |
| P4 Gameplay progression | Blocked | No representative noncombat action completed; deterministic resolver/grounding controls are narrower |
| P5 State continuity | Blocked | Local state preservation and reset isolation pass; no live multi-turn continuity |
| P6 Authority integrity | Blocked | Deterministic restricted-evidence/offscene/pending guards pass; live disclosure/mutation untested |
| P7 Responsiveness | Blocked | DNS 6.839 ms; no provider, host-turn or UI timing |
| P8 Interaction friction | Blocked | UI source inspected; real rephrasing/restart/input burden not observed |

**Deterministically validated:** 204 tests, zero failures/errors/skips: reset 6, R1-02 revision boundary 105, R1-07 correction contract 29, R2-02 speech participant 46, R2-04 question evidence 18. Isolated direct production chat cases, captured interpretations and injected records exercise current boundaries; no HTTP transport exercised. Existing global live-model guard forbids accidental inference. Main suite runtime 3.869 s is not conversational latency.

**Inspected only:** Normal launch, interface controls, orchestration, persistence and diagnostic seams. **Blocked:** Question understanding, answer usefulness, NPC coherence, live action outcome and natural continuation after provider interpretation. No new independent generalization, repair-effect, authenticated human review, ATGB score or full regression result. Existing 39-case HTTP limitation remains separate from this completed offline slice.

No percentage or overall playability score assigned. Historical ATGB weakness in answers and follow-ups remains a reason to test, not a newly observed post-repair failure.
