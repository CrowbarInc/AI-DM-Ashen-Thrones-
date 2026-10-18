# PR-DD Architecture Report

MODE: PROVIDER CONTEXT BUDGET ARCHITECTURE

IMPLEMENTATION: none

LIVE PROVIDER CALLS: 0

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The dirty worktree was preserved. Production save mtimes did not change.

## Decision

B — PARTIAL ARCHITECTURE

A safe first cycle is supported: stop sending exact duplicate contract objects in the provider JSON. Larger savings still depend on unresolved authority questions, especially hidden-fact exposure, semantic instruction compression, and the lack of authored combat and skill-check fixtures.

## What the measurements show

A normal provider request is two messages. Message 0 is the system prompt. Message 1 is one JSON object. First-pass requests contain no retry message.

The harmless preference request is byte-identical to the PR-DC measurement:

- 98,773 bytes
- sha256 `d8d6737d1bfa4f6d0928719c7e1d454b83ba46b1868434c5be71b13053c26e4f`
- narration-only envelope
- `harmless_social_incidental_dialogue_v1` selected
- estimated tokens `ceil(chars/4)` = 24,684
- exact tokenizer: unavailable

The consequential assassination question is also byte-identical to PR-DC, 108,362 bytes, sha256 `40e5408dc2cac4524faf2cc5a17182d92b67614e4a5d50822ed20591a8260f60`. Projection stays off.

Follow-up and third-turn byte counts match PR-DC (98,123 and 98,061) and projection stays on, but the hashes differ. Multi-turn reconstruction is not byte-identical. The differing field was not isolated.

## Largest contributors

On the reduced preference request, independently serialized top-level sections:

| Section | Bytes | Share of the 98,773-byte request |
|---|---:|---:|
| `response_policy` | 22,698 | 23.0% |
| `instructions` | 13,947 | 14.1% |
| `gm_resolution_decision` | 8,349 | 8.5% |
| `decision_facing_answer_recipe` | 6,707 | 6.8% |
| `referent_tracking` | 4,501 | 4.6% |
| `turn_packet` | 4,439 | 4.5% |
| system prompt, narration-only | 4,170 | 4.2% |
| `context_separation_contract` | 3,834 | 3.9% |
| `scene` | 3,788 | 3.8% |

Section percentages are not an additive partition. Each section size is a fresh JSON serialization of that key. The system prompt sits outside the user JSON.

The same two blocks lead every class. Policy is about 20–23% and instructions are about 11–16%. Envelope choice changes the system prompt from 4,170 bytes (narration-only social) to 9,568 bytes (structured realization for exploration, transition, and combat).

Exact JSON duplicates inside the preference payload, already present as `response_policy` children:

| Top-level copy | Bytes |
|---|---:|
| `context_separation_contract` | 3,801 |
| `interaction_continuity_contract` | 2,179 |
| `fallback_behavior` | 1,526 |
| `anti_railroading_contract` | 1,451 |
| `conversational_memory_window` | 992 |
| `social_response_structure_contract` | 625 |
| `player_facing_narration_purity_contract` | 373 |
| Sum | 10,947 |

That is about 11.1% of the preference request. Removing the top-level copies leaves the policy copies in place. This is the only saving that is an exact duplication with a clear surviving authority object.

## Authority split

Deterministic resolution finishes before `build_messages`. The provider does not decide the roll, the transition, the speaker, or the reply-plan kind.

Validation and finalization read the in-memory resolution, scene, and policy. They do not need a second serialized copy of those objects inside the prompt.

The provider does need: the player line, the public scene, the authorized outcome, the answer obligation, the speaker on social turns, and enough history to continue the conversation.

`scene.gm_only.hidden_facts` is sent on every authored frontier-gate request, including harmless preference and a hidden-information question whose reply plan is `genuine_refusal`. All four authored secrets appear only at that path. The list is 372 bytes. Token savings from removing it are small. Spoiler exposure is not small. Whether omission is safe is unresolved, because the layering rule currently tells the model to use those facts for implications.

## What is already bounded

Harmless projection already drops opening scaffolding and compacts the turn packet, mechanical resolution, and narrative plan. That is why preference, the rain follow-up, and the third turn sit near 98 KB while full-context social questions sit near 107–110 KB.

History is already capped at eight log entries and 200-character snippets. A probe that repeated an authored visible fact grew the preference request from 98,773 bytes to 102,509 at four entries and 103,039 at eight. Growth flattens.

A hypothetical `unresolved_question` retry instruction is 4,239 bytes. It is not part of the measured first-pass requests. Historical live retries were much more expensive because the API resends the whole prior request and then adds the retry text.

## Recommended sequence

1. Delete exact top-level contract copies when `response_policy` already holds an equal object. Measure bytes. Keep validators on the in-memory policy.
2. After that hash is stable, compress instruction lines that only name a surviving policy field. Keep answer-first, visibility, and no-hidden-reveal lines until a semantic diff and the existing validators pass.
3. Design a compact provider projection of `gm_resolution_decision` plus the answer recipe for turns that already pass the harmless projector. Do not create a second authority object.
4. Add the affordability benchmark before any live call.
5. Leave hidden-fact removal, combat budgets, and skill-check budgets for a later cycle with their own fixtures.

## Next step

Implement only cycle 1: exact provider-payload contract deduplication. No live calls in that cycle.
