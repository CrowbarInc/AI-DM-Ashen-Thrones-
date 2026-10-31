# 07 — Recommended Implementation Scope

## Proposed ATGB-R2-02

**Bounded speech-role grounding for established NPC follow-ups (F1).** Earliest supported wrong runtime decision: shared host addressee rejection after a sensible NPC ASK interpretation. Primary development failure class: **implementation**, because existing PR-EB/PR-EF-R4 contracts already support active second-person follow-ups but their lexical grounding rejects the selected cases. Full semantic continuation remains unproven.

Representative reproducers: S03.3 (unambiguous current speaker) and S05.3 (same addressee defect, separately ambiguous topic). Source extraction returns `you again later` / `me more`; model target and existing active interaction both identify the runner. This is a bounded repair target, not an instruction to implement during R2-01.

## Exact permitted change boundary for a future pass

Correct grammatical speech participant handling inside the existing shared addressee owner and its nominal helper, so speaker/addressee grounding does not treat the player recipient or continuation modifiers as an unmatched NPC name. Prefer the smallest owner-local adjustment; change the extraction helper only when preserving its other callers can be demonstrated. Existing orchestration should consume the corrected authorization without a local exemption. No prompt/schema change is needed to fix the demonstrated host rejection.

Relevant modules: `game/ordinary_semantic_ownership.py` (`assess_addressee_grounding`, `_active_npc_id`, existing authorization), `game/interaction_completion.py` (`addressed_person_nominal`, complement/nominal extraction). Integration consumers to verify: `game/conversational_orchestration.py`, `game/live_chat_interpretation.py` bridge, `game/api.py` pre-tick gate and existing ordinary resolution contract. `game/conversational_continuity.py` remains owner of delivered-exchange precedence, not a new memory layer.

Use only existing current-scene roster, active social interaction, explicit text and relevant delivered ownership context. An active ID alone never proves topic, truth, disclosure or executable outcome. No unbounded persistence or new session keys.

## Deterministic acceptance criteria

1. Replay original S03.3 raw interpretation with original preceding speaker context. Host must not emit unresolved-addressee or create ambiguous-addressee pending ASK. It must retain the runner as the supported target and use existing bridge/resolver validation, without inventing a promise or new fact.
2. S05.3 must not ask which person because the grammatical recipient is “me”. Do not require a definitive rumor continuation; a genuine focused topic clarification after the GM refusal is acceptable. A patch that automatically answers the old topic fails this criterion.
3. Unrelated-name fixtures exercise second-person question and tell-to-player constructions with different verb/complement forms, multiple visible NPCs and a unique established speaker. No calibration nouns or production phrase lists. These fixtures are related variations, not independent held-out evidence.
4. Explicit new person overrides old focus; mismatched provider candidate cannot override that person. Unknown explicit addressee, either/one-of/someone, plural/unresolved reference and multiple plausible targets still clarify with no tick or resolver.
5. No active focus, departed/offscene NPC, scene transition, conversation exit, explicit GM address and third-person GM question do not inherit a stale speaker. A single visible NPC does not erase a genuinely nonunique nominal. First-person “me” alone is never an NPC target.
6. All consumers read the same authorization: conversational decision, bridge, ordinary contract and pre-tick gate. No caller bypass. Correctly grounded ASK still uses knowledge/disclosure and normal resolver/time authority; compare allowed effects to an equivalent explicit-address control, not a blanket no-mutation expectation.
7. Hidden facts remain undisclosed; unauthorized action, travel, inventory, combat and retcon remain impossible. No new facts from narration. Legitimate mechanical revisions, executed-action refusal, correction contract and genuine clarification retain their prior behavior.
8. Focused existing PR-EF-R4 authorization, PR-EB continuity, interpretation bridge, state-authority and R1-02/R1-07 regression slices must preserve entry behavior. Baseline failures are compared by identity; interrupted HTTP coverage is not a pass. No frozen ATGB edits.
9. No additional interpretation/classification/retry pathway or expanded persistent context. Capture admission counts for downstream resumed flow; stop on unexpected extra admission rather than authorizing it automatically.

## Separately authorized live acceptance criteria

Once connectivity is available, use a new bounded reviewed budget and isolated production entry with import-safe readiness from R1-04/05. Original reproductions, related variations, legitimate ambiguity and explicit speaker-switch controls remain distinct. Capture actual messages/schema, full raw model output, projected evidence, grounding authorization, routing, final accepted text, delivered history and before/after state; record all admissions, failed dispatches, tokens and latency. Existing downstream calls fit the cap or the trial stops.

Human reviewer must separately judge speaker continuity, topic binding, question adequacy, naturalness and authority. S03.3 must avoid wrong-person clarification and unsupported future commitment. S05.3 must manage the topic ambiguity coherently rather than blindly answering the old rumor. Related scenarios use unrelated characters/situations; independent generalization requires genuinely unseen fixtures chosen without tuning. No broad playability or updated ATGB score from deterministic replay, selected live trials or previously exposed held-out cases. Live R1-07 acceptance remains separately pending.

## Explicit exclusions

No S08.2 reopening, PR-EG bind/witness migration, proposition-coverage redesign, broad prompt rewrite, semantic classifier, new ACK schema, world content/curfew-hour authoring, hidden clue publication, generic expression rewrite, new conversation state, unbounded persistence, automatic provider calls, retries, frozen baseline/judgment changes, unrelated refactor or commit/push. No scenario-specific production fixes.

## Stop conditions

Stop and return for review if exact raw-record reproduction cannot demonstrate the diagnosed host rejection; if repair requires guessing a speaker without authorized context; if S05 topic ambiguity is silently converted to certainty; if caller-specific exceptions or a new owner become necessary; if explicit/ambiguous/offscene guards regress; if new unauthorized state/disclosure occurs; if provider admission expands; or if source evidence contradicts the causal boundary. Do not weaken deterministic authority to satisfy a transcript. Package the bounded result and await review before any scope expansion.
