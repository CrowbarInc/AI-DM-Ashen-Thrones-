# PR-DD Implementation Options

None of these options are implemented.

Savings are estimated from this audit's serialized bytes using `ceil(chars/4)` unless a row says hypothetical. Live token savings are not claimed.

## 1. Further safe context projection

Estimated savings: the current harmless projector already removed the opening block. Extending that omission to factual, exploration, and transition turns is the difference between about 98 KB and 104–113 KB, roughly 5–15 KB, only where `opening_mode` is false and the turn is not an opening. Social-only keys on exploration are small relative to policy and instructions.

Implementation complexity: medium. The projector predicates are intentionally strict.

Authority risk: high if the predicate is widened to consequential, hidden, authored-fact, combat, or transition turns. Low if a new predicate only drops opening keys when `opening_mode` is false and the resolver kind is observe or discover_clue.

Regression risk: medium. Notice-board answers depend on the revealed clue, which is not an opening key.

Expected quality impact: small on ordinary continuations. Harmful if destination facts or revealed clues are classified as opening scaffolding.

Required tests: one fixture per class showing the omitted keys, the retained clue or destination, and the existing PR-CW adversarial cases still failing closed.

Dependency: do this after option 2 so the before/after hashes have a stable duplicate-free baseline. Do not combine with recipe compaction.

## 2. Response-policy consolidation

Estimated savings: 10,947 bytes on the preference payload, about 2,737 estimated tokens, about 11.1% of that request. The same equal pairs exist as keys on the other measured classes. Per-class byte totals were computed on the preference payload and should be remeasured after implementation for the others.

Implementation complexity: low. Omit the top-level key when its JSON equals the `response_policy` child. Leave the in-memory policy untouched.

Authority risk: low, provided validators keep reading the policy object they already receive, and a test proves the omitted object was equal.

Regression risk: medium if any validator or prompt assertion looks up `context_separation_contract` at the top level of the serialized payload. The in-memory contract must remain.

Expected quality impact: none if the surviving copy is byte-equal. The model still sees the contract once.

Required tests: equality assertion before deletion; preference hash changes only by the removed keys; PR-CW, PR-CX, and PR-DC validator fixtures; one exploration and one transition payload.

Dependency: none. This is the first cycle.

## 3. Resolver-specific context contracts

Estimated savings: not established as a large number. Key sets are nearly the same across classes. The bulky fields are shared. A social-only drop on a notice-board turn does not remove `response_policy` or `instructions`.

Implementation complexity: high if it becomes a new packet builder. Medium if it is another predicate in the existing projector.

Authority risk: high if each resolver grows its own authority object. Low if the packet is a view of `gm_resolution_decision`.

Regression risk: high for a new builder. Medium for another predicate.

Expected quality impact: better focus if social instructions disappear from an observation. Easy to lose speaker continuity if applied to follow-ups.

Required tests: the six contracts in `PR-DD_context_contracts.md`, each with a fallback test that a missing predicate restores the full payload.

Dependency: options 2 and 6 should land first so the shared bulk is measured cleanly. Do not start this as a parallel architecture.

## 4. Compact authoritative answer packets

Estimated savings: preference `gm_resolution_decision` is 8,349 bytes and `decision_facing_answer_recipe` is 6,707 bytes, together about 15% of that request. The unique remainder after compaction was not measured. A realistic packet might keep 2–4 KB. Unverified.

Implementation complexity: high. The recipe and the decision overlap semantically and differ in authority role.

Authority risk: high if the packet can say something the decision does not. The system prompt already says the recipe grants no new authority. The packet must be generated from the decision, not maintained beside it.

Regression risk: high for answer shape and for the harmless projector, which reads recipe fields as predicates.

Expected quality impact: better if the model sees one answer obligation. Worse if a compacted packet drops the uncertainty limit.

Required tests: projector predicates still see the same reply plan; claim-only, uncertainty, and refusal fixtures; a golden JSON projection with a hash.

Dependency: after option 2. Only for turns that already pass the harmless projector. Full-context classes keep the full decision until that projection has passed.

## 5. Stable system-instruction compression

Estimated savings: narration-only system prompt is 4,170 bytes. Structured is 9,568 bytes. Exact overlap with the instruction list is already zero. Further compression is a rewrite of reinforcement text. A 30% cut would be about 1,300–2,900 bytes. Unverified, and easy to overstate.

Implementation complexity: medium. The structured envelope's JSON schema is load-bearing.

Authority risk: medium. The schema tells the model which fields exist. Shortening the claim rules can widen what the model emits.

Regression risk: high. Envelope parsing tests and narration-only normalization are sensitive to the contract sentence.

Expected quality impact: unknown. PR-BT already showed that deleting an epistemic sentence changed behavior enough to require restoration.

Required tests: a semantic diff against the current prompts, envelope snapshot tests, and the PR-BT epistemic cases. No live call in the first pass.

Dependency: after option 2, and not in the same change as option 6.

## 6. Conversation-history budgeting

Estimated savings: from zero to eight probe entries the preference request grew 4,266 bytes, then flattened. The cap is already eight entries and 200 characters. Additional savings are a few hundred bytes unless the window itself (about 1 KB, and currently duplicated) is the target.

Implementation complexity: low for leaving the cap alone. Medium for a class-specific window.

Authority risk: low for the current cap. Medium if follow-up turns lose the prior answer.

Regression risk: medium for continuity. PR-DC's three-turn continuity depends on session state more than on a long log. The measured follow-ups still selected reduced context with a short window.

Expected quality impact: small at the current cap. Harmful if the cap drops the immediately previous answer.

Required tests: the three-turn Guard Captain replay with an explicit eight-entry log, checking interlocutor, speaker, and reply plan.

Dependency: the duplicate memory-window object is removed by option 2. No separate history project is justified until a real session exceeds the cap and the benchmark shows it.

## 7. Retry-specific context construction

Estimated savings: the hypothetical retry instruction measured here is 4,239 bytes. The historical PR-CY retry was a full second request at 39,262 input tokens. A retry that resends a deduplicated payload saves the option-2 amount on that second request. A retry that sends only the failure class, the decision projection, and the rejected narration would save much more. That larger design is unverified.

Implementation complexity: medium. `build_retry_prompt_for_failure` already builds a narrow instruction, and the API still resends the original messages underneath it.

Authority risk: medium. The retry must still name the failure class and the resolution contract. Dropping the decision lets the retry invent a new outcome.

Regression risk: medium. First-attempt traffic is unchanged if this path runs only when `retry_attempt >= 1`.

Expected quality impact: positive if the retry stops reintroducing the whole policy catalog. Negative if the failure reason is truncated.

Required tests: a deterministic retry append for `unresolved_question`, `validator_voice`, and an authority rejection, with hashes, and an assertion that first-pass `build_messages` output is unchanged.

Dependency: after option 2, so the resent body is already smaller. Independent of projection widening.

## 8. Structured field deduplication

This is the measurement name for option 2's mechanism, plus any later inner-field dedupe inside `turn_packet`.

Estimated savings: the exact 10,947-byte set is the evidenced part. `turn_packet` inner overlap with top-level contracts was not field-diffed. Preference turn packet is 4,439 bytes compacted and the factual packet is 10,809 bytes. Treat further inner savings as unresolved.

Implementation complexity: low for the seven exact mirrors. High for a general deduper that might drop unequal objects such as the small `interaction_continuity` snapshot, which is not equal to the policy child.

Authority risk: low for JSON-equal omission. High for a fuzzy deduper.

Regression risk: low if equality is checked at runtime and the original key is restored when unequal.

Expected quality impact: none for exact equality.

Required tests: unequal objects are retained; equal objects are omitted; a hash fixture per representative class.

Dependency: this is cycle 1. Options 1, 4, and 5 depend on the hashes it produces.
