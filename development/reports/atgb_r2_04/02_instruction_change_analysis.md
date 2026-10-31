# 02 — Instruction Change Analysis

One contiguous paragraph replacement inside the existing production system instruction; no standalone prompt section or new instruction surface. Exact old and replacement text follow. Full reviewable source/test diff is source.diff.

## Before

```text
Recover the underlying question or request from available conversation context using the corrected meaning. Select relevant authorized PUBLIC evidence_refs that support answering that corrected question; prefer a supported answer over redundant clarification. Subject describes the question, never a new fact. Restricted or unestablished information in internal world state is not disclosure authority; do not select it or infer unsupported facts. Select only supplied PUBLIC passages that support the answer. With insufficient evidence, state the limitation or continue with established information only. Ask a targeted question when meaningful ambiguity remains (such as competing people, a missing interlocutor or action parameter, or conflicting intentions); never guess to avoid clarification.
```

## After

```text
Recover the underlying question from preceding context, including elliptical follow-ups and corrections. Keep a uniquely established subject; do not adopt a rejected interpretation or a nearby alternative. For information requests, subject identifies the requested detail (time, location, identity, cause, sequence, description, relationship or explanation), not just the topic; it never asserts a new fact. Select relevant authorized PUBLIC evidence_refs supporting that detail, not merely the same topic, person, place or event. Background may support a partial answer, but must not stand in for missing detail. Restricted or unestablished information in internal world state is not disclosure authority; do not select it or infer unsupported facts. An understood question with no answer-bearing evidence uses empty evidence_refs and an honest limitation, not clarification solely because the answer is unavailable; prefer a supported answer over redundant clarification. Ask a targeted question when meaningful ambiguity remains: competing subjects, people, a missing interlocutor or action parameter, or conflicting intentions. Clarify the unresolved subject separately from an established addressee; never guess to avoid clarification.
```

Requested-detail wording links the existing subject and evidence_refs to the actual information request. This targets S02.2 timing and S02.4 last-seen location without hardcoding either scenario. Related-topic evidence is insufficient, while useful background may still support a partial answer; descriptive/explanatory requests remain valid.

Preceding-context, unique-subject and rejected-alternative wording targets S02.3: its rejected patrol interpretation must not displace the established curfew question. It covers elliptical follow-ups without forcing every demonstrative to resolve. S05.3's competing accounts remain genuine ambiguity; clarification concerns subject independently of established recipient.

Understood/no-answer wording permits empty evidence_refs plus the existing honest limitation. It does not manufacture an answer, require a player clarification for a missing fact, or categorically ban clarification. Genuine competing subjects/interlocutors/action parameters and conflicting intentions still require targeted clarification.

R1-07 conversational correction, GM/CORRECTION + legacy OTHER, correction.subject REFERENT, empty action components and eligible pending-action restrictions are unchanged. R2-02 grounding is unchanged. PUBLIC-only selection and no unsupported inference remain explicit. Schema semantics still carry meaning and control disposition through existing fields. No source/category-specific classifier, state store or provider stage was added.

The deterministic checks establish presence and host compatibility only. They cannot show that a future completion will obey the replacement or that wording caused the original model failure.
