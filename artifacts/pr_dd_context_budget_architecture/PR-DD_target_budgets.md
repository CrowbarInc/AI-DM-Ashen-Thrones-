# PR-DD Target Budgets

Targets are provisional `ceil(chars/4)` input-token budgets for the `build_messages` payload. They are not promises about live tokenizer counts. They are not a single budget for every class.

Output tokens on the two accepted historical turns were 109 and 116. Output is not the cost center. These targets are input budgets.

## Simple NPC dialogue

Current: preference 98,773 bytes, estimate 24,684. Follow-up 98,123 bytes, estimate 24,521. Third turn 98,061 bytes, estimate 24,506. Projection already on.

Historical live comparison, different payload: PR-CY T1 accepted at 27,442 input tokens.

Proposed target: 22,000 estimated input tokens, about 88,000 serialized bytes.

Expected reduction: about 11% from exact contract deduplication (10,947 bytes on the preference payload). Reaching 22,000 also assumes a later, separately tested trim of roughly 2,000 estimated tokens from pointer-style instruction lines.

Assumptions: narration-only envelope stays; speaker, reply plan, and public scene stay; history cap stays.

Authority risk: low for the exact-duplicate half. Higher if instruction reinforcement is removed in the same change.

Quality risk: low if the answer-first and claim-only lines remain. The player should still hear a specific preference.

Verification: before/after hashes, PR-DC three-turn continuity, PR-CX rejection cases, and a deterministic narration fixture that still accepts a claim-only preference.

## Authored factual answers

Current: 110,114 bytes, estimate 27,518. Projection off. `genuine_uncertainty` on the missing-patrol question.

Proposed target: 24,500 estimated input tokens.

Expected reduction: the same 11% exact-duplicate removal, and no harmless projection. 27,518 minus about 2,700 is about 24,800. The target allows that and a small amount of opening-scaffold review only when `opening_mode` is false.

Assumptions: the known fact or the uncertainty plan remains in the payload. Hidden facts are not removed in this target.

Authority risk: projecting this class with the harmless predicate would hide the uncertainty plan's surrounding context. That is out of scope for the target.

Quality risk: the answer can become a generic refusal if the authorized fact or the limit sentence is trimmed. Do not trim those fields to hit the number.

Verification: the existing authored patrol tests, including the three focused failures inherited from before PR-DD, must be understood before any factual trim. This audit did not repair them.

## Exploration

Current: notice board 106,771 bytes, estimate 26,683. "I look around." 103,854 bytes, estimate 25,953. Structured system prompt is 9,568 bytes.

Proposed target: 23,000 estimated input tokens for ordinary observation and notice-board inspection.

Expected reduction: exact-duplicate removal plus leaving the structured envelope in place. The envelope itself is about 5,400 bytes larger than narration-only. Switching envelopes to chase the target is not part of this budget.

Assumptions: the revealed clue text and public visible facts stay.

Authority risk: dropping `scene.gm_only.hidden_facts` is an authority decision, not a budget decision. It is excluded here.

Quality risk: observation replies get worse if public visible facts are shortened. Keep them.

Verification: notice-board narration must be able to state the engine-revealed patrol-route clue and must still fail if it states a hidden fact.

## Consequential social interactions

Current: 108,362 bytes, estimate 27,080. Hash matches PR-DC. Projection off.

Proposed target: 24,000 estimated input tokens.

Expected reduction: exact-duplicate removal only. About 2,700 estimated tokens.

Assumptions: `genuine_uncertainty` or a stronger refusal remains. No compact social projection.

Authority risk: high if the consequential payload is forced through the harmless projector. The target forbids that.

Quality risk: low. These replies are supposed to be short limits, not long tactical answers.

Verification: the assassination line and the other PR-DC negative controls stay off `harmless_subjective_response_permitted`, and hard validators still reject a method, a concession, or a state change.

## Combat

Current authored usage: unavailable. Authored scenes have empty `enemies` arrays.

Synthetic fixture: 121,416 bytes, estimate 30,336, with `roll_die` fixed at 10. This is a shape sample, not a campaign baseline.

Proposed target: no numeric campaign target until an authored encounter exists. On the synthetic shape, a later target of 26,000 estimated tokens is plausible only after exact-duplicate removal and after the attack roll, hit, damage, and target id are shown to survive.

Authority risk: any trim that omits the roll lets the model invent one.

Quality risk: combat narration needs the outcome more than it needs the social policy catalog. A combat-specific packet is future work, not this target.

Verification: an authored fixture with a stable die, plus a narration check that restates hit or miss and damage.

## Scene transitions

Current: "Enter Cinderwatch" 113,279 bytes, estimate 28,310. Destination binding and `scene_transition_already_occurred` are present.

Proposed target: 25,000 estimated input tokens.

Expected reduction: exact-duplicate removal. The structured envelope stays. Destination public facts stay.

Assumptions: unresolved movement such as "I walk closer to the notice board." (104,643 bytes, no destination) does not use this budget. That line still needs the full payload until travel resolution binds a target.

Authority risk: omitting the destination or the already-occurred flag makes the model choose the scene.

Quality risk: arrival narration needs the destination's public facts. Cutting them to meet a token cap makes the crossing generic.

Verification: the narration's location is `market_quarter` after "Enter Cinderwatch", and `activate_scene_id` in the model output cannot point elsewhere.

## Shared rule

A class that cannot meet its target keeps the useful narration and the authority fields. The benchmark records the miss. It does not authorize another cut.
