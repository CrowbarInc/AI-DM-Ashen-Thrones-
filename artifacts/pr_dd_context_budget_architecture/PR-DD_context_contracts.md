# PR-DD Context Contracts

These are proposed provider-facing contracts. They are not implemented. They do not add a new authority system. The engine decision, the resolution contract, and the existing validators remain the authority. Each contract says what the provider may see.

Full-context fallback for every contract: if any required predicate is missing, contradictory, or not produced by the current resolver, send the current full `build_messages` payload.

## A. Harmless incidental social dialogue

Measured example: Guard Captain preference, 98,773 bytes, projection already selected.

Required authority facts:

- one `allowed_speaker_ids` entry, equal to `active_interlocutor.npc_id`, `primary_speaker_id`, and `resolution_contract.interlocutor`
- `reply_plan_kind = harmless_subjective_response_permitted`
- `npc_speech_authority = claim_only`
- `objective_world_fact_authority = none`
- `durable_state_mutation_allowed = false`
- empty `permitted_state_mutations` and empty `unresolved_qualifiers`
- `permitted_inference.allowed = false`
- `selected_resolver = social` and `ordinary_contract_established = true`
- no skill check, no state change, no world update, no discovered clue, no transition, `in_combat = false`

Required answer obligation: a bounded personal answer from that speaker. Lack of an authored preference is not a refusal.

Permitted narration scope: gesture, cadence, and a claim-only preference, opinion, or personal impression. No objective world fact, inventory change, relationship change, or quest evidence.

Relevant scene context: public scene identity and the facts needed to keep the reply physically in the scene. Opening-selector copies are already omitted by the current projector.

Relevant NPC context: the one speaker's id, name, and dialogue plan.

Permitted history: the existing memory window, at most eight snippets of 200 characters, plus the current player line.

Required response schema: narration-only `{"narration": "..."}`.

Forbidden authority expansion: `declared_claims`, new mechanics, hidden facts stated as truth, a second speaker, or a state mutation.

Validator responsibilities: reject objective facts, hidden-information disclosure, discovery, biography, geography, and state-change narration. The existing PR-CX and PR-DC checks cover this. Validators read the resolution, not a second prompt copy.

Full-context fallback: any failed projector predicate. The current function already returns the unprojected payload in that case.

## B. Authored factual dialogue

Measured example: "Captain, what do you know about the missing patrol?", 110,114 bytes, projection off, `reply_plan_kind = genuine_uncertainty`.

Required authority facts: the authored topic if the resolver revealed one, the uncertainty or refusal plan if it did not, the same single-speaker identity, and `known_answer_hint` when the engine resolved a known fact.

Required answer obligation: say the authorized fact, or the authorized limit. Do not upgrade uncertainty into a patrol route, culprit, or location.

Permitted narration scope: the speaker's delivery of that fact or limit, plus public scene grounding.

Relevant scene context: public facts that are the answer, including the notice-board text when it is the authorized source. Hidden facts are not part of this contract until a separate decision allows an implication.

Relevant NPC context: the addressed speaker and whether that speaker is allowed to know the topic.

Permitted history: the same capped window, including the prior answer when the question is a follow-up on an authored topic.

Required response schema: narration-only while the current envelope selector says narration-only. This audit did not change that selector. The measured factual question used narration-only.

Forbidden authority expansion: inventing the patrol's fate, a culprit, or a destination that is not in the authorized fact.

Validator responsibilities: reject unsupported certainty and any claim that is not in the decision's realization claims.

Full-context fallback: unresolved qualifiers, missing speaker, or any reply plan other than the harmless subjective plan. That is why this request stays on the full payload today.

## C. Ordinary exploration

Measured examples: notice-board inspection resolved as `discover_clue` / `inspect` / exploration, 106,771 bytes. "I look around." resolved as `observe` / `perceive` / exploration, 103,854 bytes. Both use the structured envelope. Projection stays off.

Required authority facts: the resolved kind, any discovered clue id and text the engine actually revealed, and public visible facts.

Required answer obligation: report the revealed clue or the visible scene. Do not add a new clue.

Permitted narration scope: the current scene's public facts and the engine-revealed clue text.

Relevant scene context: `scene.public`, discoverable clue text only when the resolver revealed it, and the interactable result.

Relevant NPC context: none unless the resolver selected a speaker. Social dialogue fields are not an answer source on these turns.

Permitted history: capped window. An observation does not need the social memory contract.

Required response schema: the structured envelope when `select_provider_response_envelope` selects it. Do not force narration-only onto exploration in this contract.

Forbidden authority expansion: hidden facts, unrevealed clues, new exits, and combat results.

Validator responsibilities: the narration may state the revealed clue and visible facts, and must not state hidden facts.

Full-context fallback: ambiguous target, no resolved kind, or a mixed social-and-exploration contract.

Limitation: "Describe what I can see around me here at the gate." resolved as `custom` / `generation` / `unresolved`, 103,622 bytes. It is not the contract example for ordinary observation. "I look around." is.

## D. Consequential world actions

Measured example: "Does rain make it easier to assassinate the captain?", 108,362 bytes, sha256 identical to PR-DC, `genuine_uncertainty`, projection off.

Required authority facts: the consequential classification, empty or denied mutation set, and the speaker if one is grounded.

Required answer obligation: preserve the limit. Do not supply a method, a weakness, or a committed outcome.

Permitted narration scope: in-character refusal, uncertainty, or a public-scene reaction. No tactical instruction.

Relevant scene context: public scene only.

Relevant NPC context: the addressed speaker's refusal or uncertainty plan.

Permitted history: capped window.

Required response schema: the envelope the current selector already chose. This measurement was narration-only.

Forbidden authority expansion: injury, access, faction allegiance, or a successful social concession.

Validator responsibilities: reject actionable harmful success, unauthorized NPC action, and state mutation. Existing negative controls stay in force.

Full-context fallback: this class does not use the harmless projector. Full context remains the default until a narrower consequential contract is tested on its own.

## E. Combat and mechanical resolution

Authored frontier-gate has `enemies: []` and no `skill_check` configuration in `data/scenes`. An authored search resolved as `investigate` with `skill_check_present = false`, 104,320 bytes.

Shape evidence comes from existing test fixtures, labeled synthetic:

- skill check from `tests/test_exploration_skill_checks.py`: 91,621 bytes, `skill_check` present, structured envelope
- combat from `tests/test_combat_resolution.py::_scene_with_goblin`, `roll_die` fixed at 10: 121,416 bytes, `resolved_combat_action` present, structured envelope

Required authority facts when a roll exists: skill or attack id, roll, total, difficulty or armor class, success, and damage or clue consequence already computed by the engine.

Required answer obligation: narrate that result. Do not roll again.

Permitted narration scope: the resolved swing, check, or investigation beat and the public scene.

Relevant scene context: the target that the engine selected. Do not send a hidden-fact list as a combat hint.

Relevant NPC context: the attack target's engine id and name. No social reply plan unless the resolver produced one.

Permitted history: the current round's prior beats inside the existing cap. Older social chat is not an attack authority.

Required response schema: structured realization, matching the measured fixtures.

Forbidden authority expansion: a different target, a different roll, healing, or a scene change the combat result does not contain.

Validator responsibilities: narration must match hit, miss, damage, and success flags.

Full-context fallback: any combat or check whose result object is missing a roll. The provider must not be asked to supply it.

## F. Scene transitions

Measured example: player line "Enter Cinderwatch", which matches the authored frontier-gate exit to `market_quarter`. Kind `scene_transition`, resolver `world_action`, 113,279 bytes, structured envelope. `resolved_exploration_action` and `scene_transition_already_occurred` are present.

Required authority facts: origin scene, destination scene id, and `scene_transition_already_occurred`.

Required answer obligation: narrate arrival in the destination. Do not offer another destination as if the move were still open.

Permitted narration scope: the destination's public facts. Do not restate the origin as the current location.

Relevant scene context: the destination public scene. Origin is context for the crossing sentence only.

Relevant NPC context: destination addressables if the destination scene ships them. The origin social plan is not the speaker for the arrival.

Permitted history: the player line that committed to the exit, inside the cap.

Required response schema: structured realization, as measured.

Forbidden authority expansion: a different `activate_scene_id`, a new scene draft, or a clue discovered by the crossing unless the resolver attached one.

Validator responsibilities: the narration's location must be the destination, and it must not contradict `scene_transition_already_occurred`.

Full-context fallback: an unresolved travel line. "I walk closer to the notice board." resolved as `custom` / `travel` / `act` with no `resolved_exploration_action`, 104,643 bytes. That line is not a completed transition and must not use this contract.

## Shared prohibitions

- The provider packet is a projection of the current decision. It does not override `gm_resolution_decision`.
- Validators keep their current inputs.
- Hidden facts stay out of these proposed packets until the unresolved implication question has its own test.
- If a predicate fails, the fallback is today's full payload, not a best-effort trim.
