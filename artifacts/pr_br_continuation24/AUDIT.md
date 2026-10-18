## PR-BR Continuation 24 — Contract-First Unparsed Resolution

Bounded implementation. The unparsed adjudication arm now builds the existing Resolution Contract from the full player utterance before any specialized resolver runs. Peer parsers were not rewritten. This is not a full contract-first reconciliation.

### 1. Purpose

Close the demonstrated hole where ordinary gameplay reached adjudication and emission with no Resolution Contract.

### 2. Authorization basis

C23 showed the C22 live failure was a contract bypass. The trailing clause containing "could" and "nearby" was adjudicated as earshot. No contract, no C18 seal, no C22 addressee check. Anti-reset then spoke as "The guard".

### 3. C23 architectural boundary

C24 changes only the unparsed arm in `game.api.chat`. Social, exploration, travel, generic intent, world-action recovery, and dialogue-first still choose meaning and then attach a contract. Off-scene social text and pending check prompts still emit without a contract. Those remain for a possible C25.

### 4. Exact C22 failure replay

Captured before the production edit: `artifacts/pr_br_continuation24/c22_failure_replay_before.json`.

Raw utterance: the nod, the thanks, "Have you heard anything about who or what might be causing trouble there?", then "Any chance I could find shelter or supplies nearby before investigating further?"

Segmentation stored the social question in `declared_action_text` and the supplies question in `adjudication_question_text`. Social entry reason `no_addressable_target`. Classifier on the extracted clause: `perception_query`. Kind `adjudication_query`. Route `procedural_perception_query`. Contract absent. Visible text: The guard says, "I do not know enough to answer that." Accepted false. Tags included `final_emission_gate:anti_reset_continuation_fallback`.

The first point where `contract == None` was accepted was the unparsed branch: `parsed is None` and `resolve_adjudication_query` on the extracted clause returned a result, and the turn emitted without `attach_interaction_obligation`.

### 5. Ordinary gameplay / Category A

Named exclusions in `game.contract_adjudication_bridge.CATEGORY_A_EXCLUSIONS`:

- `session_administration` — HTTP snapshot, load, reset, editors. Not `/api/chat`.
- `initiative_status_line` — typed `roll_initiative`.
- `end_turn_status_line` — typed `end_turn` with no enemy.
- `campaign_start_cue` — `_is_campaign_start_turn_request`.

Natural-language questions, social talk, exploration, movement, perception, mechanics, and world interaction are ordinary gameplay even when a deterministic handler exists. An OOC sentence inside chat is not Category A.

### 6. Implementation architecture

`game/contract_adjudication_bridge.py` selects a resolver from the existing contract. `game/api.py` on the unparsed arm:

1. `attach_interaction_obligation` on the full `req.text`, deterministic fast path first.
2. `select_resolver_family`.
3. If a family is selected, `resolve_adjudication_query(..., resolver_family=family)` using the contract's recorded utterance.
4. `run_preserve_if_valid` with no regeneration. Failure becomes the existing contract-aware nonresolution.
5. If no family is selected, the existing freeform generation path runs. A model interpretation call happens only when that path's fast path abstained and the existing policy says a model proposal is appropriate.

No second contract type. Adjudication does not overwrite `operation` or `interlocutor_id`.

### 7. Full-utterance contract construction

The contract is built from `req.text`, not from `adjudication_question_text`. The existing constructor still stores up to its current raw-input limit. The social opening of the C22 sentence is inside that text, so the trailing supplies clause is not the only input.

### 8. Discourse preservation

Construction receives session, scene, world, and visible turns. A follow-up that says "have you heard" inherits the active interlocutor under existing C22 rules. The repaired C22 replay keeps operation `ask` and does not speak as the guard.

### 9. Resolver selection

Families, using repository names: `earshot`, `nearby_presence`, `place_location`, `feasibility`, `state_query`, `roll_mechanical`, `generic_adjudication`.

Selection uses operation, commitment, and the utterance stored on the contract. Bare "nearby" is not a family. An explicit ask ("I ask", "have you heard", "thank you") blocks presence, place, and feasibility. Roll and state questions can still be answered without replacing the addressee.

### 10. "Nearby" contrast

- "Who is nearby?" → `nearby_presence`.
- "Can I find supplies nearby?" → `place_location`, not earshot.
- "I ask the runner if there are supplies nearby." → no specialized family. Operation stays ask.
- "Is there shelter nearby?" → `place_location`.
- "I listen for anyone nearby." → perceive / sound, family `earshot`.

### 11. Resolver failure

`resolve_selected_family` returns None when there is no contract, or when the family would contradict an explicit social ask. The caller then uses generation or the existing safe nonresolution. Operation, target, and addressee on the contract are not reset.

### 12. Generic-speaker fallback

`local_exchange_continuation_fallback_line` no longer calls `minimal_social_emergency_fallback_line` for `adjudication_query`. That catalog's empty speaker is "The guard". Anti-reset still replaces opener-like text during a real social exchange. It does not invent a guard for a procedural answer.

### 13. C18

A resolver result is passed through `run_preserve_if_valid` before persistence. `restore_accepted_text` still runs in the emission finalizer. The repaired C22 path and the live turns have accepted text equal to emitted text.

### 14. C19

Validation is the existing `validate_generated_response`, including proposition authority. The authority check was not loosened.

### 15. C20 / C21

The roster resolver reads the existing scene roster. It does not create people. The place resolver does not manufacture NPCs from the word "nearby". Entity binding remains inside `attach_interaction_obligation`.

### 16. C22

Uncommitted act/follow is not given an executing resolver. "If the guard refuses, I'll look for shelter nearby." selects no family and does not change scene. An explicit ask keeps its addressee; a contradicting earshot call is refused.

### 17. Model-call economy

The unparsed arm builds the deterministic contract first. Interpretation runs only on the generation path when the fast path abstained and model interpretation is already appropriate. Live session: 4 deterministic contracts, 0 interpretation calls, 4 gameplay generations, 0 retries.

### 18. P1–P8

P1, the exact C22 sentence after asking the tavern runner: contract present, operation ask, no earshot roster, no guard line, accepted equals emitted. PASS.

P2–P8: 7/7 in `tests/test_pr_br_continuation24_contract_first_unparsed.py`.

### 19. Adjudication-family matrix

PASS. Earshot, nearby presence, place/location, feasibility, state query, and roll each require a contract id before `resolve_selected_family`. Generic adjudication runs only when that family is passed explicitly, and it still requires a contract. The selector does not assign generic from "nearby".

### 20. No-contract invariant

`resolve_selected_family` returns None without `contract_id` and `operation`. The static test requires `attach_interaction_obligation(` before `select_resolver_family(` in the unparsed arm. Category A ids are the four names above.

### 21. S1–S8

8/8. Compound turns keep a contract. None emitted an earshot roster or the generic guard line. An adjudication family, when one ran, was not earshot.

### 22–26. C18–C22 regression

`tests/test_pr_br_continuation18_immutable_boundary.py` through `tests/test_pr_br_continuation22_commitment.py`: PASS.

### 27. C23 repaired-scope invariant

`tests/test_pr_br_continuation23_precontract_routes.py`: PASS. The old assertion that the C22 sentence has no contract now expects a contract and forbids the guard line and the earshot roster.

### 28. Broader PR-BR regression

Continuation 18–24 modules: PASS. Pipeline adjudication tests for roll, earshot, OOC roll, and covert concealment: PASS.

`tests/test_nearby_place_existence_knowledge_ownership.py` has three failures that do not enter the new arm (`contract_before_resolver` is absent; kind is `question` or the check never chats):

- "Who is nearby?" and "Night Porter, is there a tavern nearby?" are owned by the existing social/question parser, then generation. That parser-first path is unchanged by design.
- `test_question_rule_does_not_rewrite_resolved_place_existence` fails with the C24 files restored to the pre-edit tree as well. It is pre-existing.

Local-presence "What's nearby?" remains an observe parse. It does not enter the unparsed arm.

### 29. Fresh live transcript

`artifacts/pr_br_continuation24/live/20261003T123908Z/visible.md`. Four turns. Notice board, silent threadbare figure, tavern runner on the patrol, follow-up to the same runner.

### 30. Live contract / resolver telemetry

`turns.json` and `summary.json` in that session. Every turn has a contract. Construction source deterministic on all four. No specialized resolver ran, because the parser-owned asks and the inspection never reached the unparsed arm. No resolver ran before a contract.

### 31. Live state / discourse

Turn 1 inspects the notice board. Turns 3 and 4 bind `tavern_runner`. Turn 4 does not drop the runner when the player also looks toward the footprints. No scene transition. No uncommitted travel.

### 32. Manual review

4/4 PASS. See `MANUAL_REVIEW.md`.

### 33. API / model cost

Opening generation 1. Gameplay initial generation 4. Gameplay retry 0. Interpretation 0. Player-model calls 4 (`gpt-4.1-mini`). Evaluator 0. Repair/rerun: no.

### 34. Remaining parser-first owners

Unchanged: segmentation, directed social entry, social parser, dialogue-first, exploration, world-action recovery, generic intent, declared travel, in-chat attack. Still contract-less: off-scene social text, pending check prompt, and the four Category A commands.

### 35. Implementation-scope post-check

C24 closed only the total unparsed/adjudication contract bypass. Peer parser modules were not edited. The adjudication classifier function still classifies raw text for direct callers. The chat arm no longer lets that classification own the turn before a contract exists.

### 36. Residual defects

- Off-scene social lines and pending check prompts can still emit without a contract.
- Parsers still choose meaning before the contract is attached.
- "Who is nearby?" on the kiln fixture is still a parser-owned question, so a stubbed model sentence can appear there. That is outside this cycle's arm.
- The pre-existing question-resolution exemption test remains red.
- Turn 2's silent figure is a thin social answer. The ask was not handed to another speaker.

### 37. Readiness decision

C24 VALIDATED — UNPARSED/ADJUDICATION CONTRACT BYPASS CLOSED; REMAINING PARSER-FIRST OWNERSHIP REQUIRES EXTERNAL REVIEW.

### 38. PR-BR status

PR-BR remains OPEN. No completion commit. No push. No PR-BS. The second 4×10 gate is not authorized. Human playtest is not authorized.

HEAD at implementation: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.
