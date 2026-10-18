# PR-DD Redundancy Analysis

Labels: exact duplication, semantic repetition, intentional reinforcement, different consumers, or apparent duplication with different authority.

No removal was performed.

## A. Exact duplication

`game.gm._dedupe_provider_payload_instructions` already removes instruction strings that occur verbatim inside the selected system prompt. On every measured request that remainder is zero.

The remaining exact duplicates are structured objects shipped twice in the user JSON. On the preference payload these `response_policy` children are JSON-equal to a top-level key:

- `response_policy.anti_railroading` and `anti_railroading_contract`
- `response_policy.context_separation` and `context_separation_contract`
- `response_policy.player_facing_narration_purity` and `player_facing_narration_purity_contract`
- `response_policy.social_response_structure` and `social_response_structure_contract`
- `response_policy.interaction_continuity` and `interaction_continuity_contract`
- `response_policy.fallback_behavior` and top-level `fallback_behavior`
- `response_policy.conversational_memory_window` and top-level `conversational_memory_window`

Combined object size of the top-level copies: 10,947 bytes. About 11.1% of the 98,773-byte preference request.

`response_policy.interaction_continuity` is not equal to the smaller top-level `interaction_continuity` snapshot (261 bytes). Those two are different objects. Only the `interaction_continuity_contract` match is an exact duplicate.

`prompt_debug` is not in the provider payload.

## B. Semantic repetition

The preference request carries 84 instruction lines, 13,583 bytes of instruction text, 13,947 bytes with the JSON wrapper.

Those lines restate material already present in the system prompt and in `response_policy`:

- rule-priority obedience
- no validator voice
- answer first
- anti-railroading by policy name
- context separation by policy name
- narration purity by policy name
- do not restate the player's line, which appears as two adjacent instruction lines and again in the system prompt

This is semantic repetition after the exact-substring deduper. It is not safe to delete as a block. A later cycle needs a line-by-line semantic diff of the kind used in PR-BT, plus the existing narration validators.

## C. Intentional reinforcement

These repeats should stay until a test shows the model still obeys them with one copy:

- answer the player's question in the first sentence
- visibility: assert only `narration_visibility.visible_facts`
- do not reveal hidden or undiscovered facts
- do not invent dice or override an app-resolved result
- incidental subjective speech is claim-only and is not world truth
- the answer recipe grants no new authority

The hidden-fact reinforcement is especially important because the same payload also contains `scene.gm_only.hidden_facts`. The instruction and the secret text pull in opposite directions. That pair is not a deduplication candidate.

## D. Different consumers

`response_policy` is built once and then used by prompt rendering and by post-generation enforcement. The in-memory object can serve validators and finalization. The provider needs one serialized copy. The second serialized copy is not a second consumer.

`mechanical_resolution` in the engine includes `metadata.gm_resolution_decision` and `metadata.resolution_contract`. `_provider_mechanical_resolution` already removes those two blobs from the provider copy because the compact contract, the decision, and the recipe are top-level. That split is the right shape: engine retains the full object, provider receives one projection.

## E. Apparent duplication with different authority

`gm_resolution_decision`, `decision_facing_answer_recipe`, and `mechanical_resolution.social` describe one decision at three levels. The recipe is derived from the decision and is marked as guidance. The social block carries reply-plan kind, speech authority, and mutation flags that the projector treats as predicates.

Collapsing all three into an untested summary would create ambiguity about which object is authoritative. A compact provider packet is allowed only as a projection of the existing decision, with the engine object unchanged.

`referent_tracking` (4,501 bytes on the preference request) overlaps speaker selection and scene addressables. It is not an exact duplicate. Dropping it can change which entity the model addresses. It stays conditional.

## History is capped, not duplicated

`recent_log` on an empty session is 18 bytes. The memory window is a separate selection, 1,026 bytes on the preference request, and that window object is one of the exact duplicates above. Adding four and then eight authored-fact log rows grew the whole request by 3,736 bytes and then by another 530 bytes. The eight-entry, 200-character cap is already doing the history budget's main job.

## Verification required before any deletion

For the exact contract mirrors: assert JSON equality before omission, assert the surviving `response_policy` child is unchanged, and rerun the PR-CW, PR-CX, and PR-DC validator fixtures. Do not remove a reinforcement line in that same change.
