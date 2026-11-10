# Failure inventory

Selection: the twelve modules named in `artifacts/pr_play_adjacent_regression/classification_matrix.json`. Result: 176 passed-or-failed tests, 12 failures, 0 errors, 0 skipped. Every failure below is HTTP 200. Every `resolution` object on the public body is `{}`. The engine fields come from the pre-projection payload and the session log. Current and pre-handoff captures match.

Machine-readable copy: `artifacts/pr_play_adjacent_regression/classification_matrix.json`.

## 1. Unknown player-named object

- Test: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`
- Assertion: `resolution.kind == "investigate"` at the ivory-metronome chat.
- Expected: `investigate`. Actual: `None`, because the public resolution is empty.
- Engine: kind `investigate`, authority `unsupported`. No state-change keys.
- Published: the frontier-gate observe stock, including the gate serjeant and the roster board.
- Route: `deterministic_conversational_decision` is `None`.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response. The player hears another scene's stock sentence. The missing kind is not what the player reads. Perception replacement was skipped.

## 2. Narration-only silver bell

- Test: `test_general_narration_only_object_does_not_gain_authority`
- Assertion: the look-around response has kind `observe`.
- Expected: `observe`. Actual: `None`.
- Engine: look-around kind `observe`. The following bell inspection is kind `investigate`, authority `unsupported`.
- Published on both turns: "I cannot provide a validated response to that request."
- The engraved Captain Marrow stub is not published. No silver bell is added.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response. A look around the loft does not describe the loft.

## 3. Abstract shipping ledger

- Test: `test_general_abstract_reference_does_not_become_physical`
- Assertion: `"glassport" not in` the published sentence.
- Expected: no Glassport claim. Actual: "The ledger lists eight named crews bound for Glassport."
- Engine: kind `investigate`, authority `authored_abstract_reference`. The unit classifier before the HTTP post is not the failing line.
- Route: conversational decision is `None`. Perception replacement is skipped, so the stub remains.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response and a publication failure. Invented crews and a place are shown for an abstract reference.

## 4. Tariff slate

- Test: `test_general_readable_surface_communicates_contents`
- Assertion: kind is `investigate` or `discover_clue`.
- Expected: one of those kinds. Actual: `None`.
- Engine: kind `discover_clue`, clue `tariff_slate_fees`. State changes: `clue_revealed`, `interactable_id`.
- Published: "In Mill Loft, a dry loft, a grain hopper, and a tariff slate Dock fees rise after the second horn."
- Class: B, preexisting. Confidence: high.
- Player-facing: the assertion is test infrastructure. The player receives the dock-fees clue. The public body does not carry the kind.

## 5. Hidden brass token

- Test: `test_general_hidden_object_is_not_revealed_by_naming`
- Assertion: the sentence contains "no such thing" or "nothing here matches".
- Expected: a refusal. Actual: "You pry up the hopper and pocket the brass token."
- Engine: kind `investigate`, authority `authored_hidden`. No state-change keys. The sealed-fact sentence is not in the published text. Asserts before this line, including the unrevealed fact, are not the failure.
- Route: conversational decision is `None`. Perception replacement is skipped.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response and a publication failure. The sentence narrates a retrieval that did not happen. This is the highest-risk finding in the twelve. It does not add the hidden fact to revealed state.

## 6. Failed inspection, then look around

- Test: `test_general_failed_inspection_then_observe_uses_current_scene`
- Assertion: the metronome response has kind `investigate`.
- Expected: `investigate`. Actual: `None`.
- Engine: kind `investigate`, authority `unsupported`. Published text is the same gate stock sentence as failure 1.
- The following look-around, which pytest does not reach, has engine kind `observe` and the maize sentence.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response on the failed inspection, same stock sentence as failure 1.

## 7. Feed-chute alias

- Test: `test_general_authored_alias_binds`
- Assertion: kind is `investigate` or `discover_clue`.
- Expected: one of those kinds. Actual: `None`.
- Engine: kind `investigate`, authority `authored_interactable`.
- Published: the gate observe stock, not a hopper examination.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response. The alias is bound in the engine and the player still hears the gate stock sentence.

## 8. Glass kiln schedule

- Test: `test_general_failed_inspection_creates_no_world_facts`
- Assertion: "four new overseers" is absent.
- Expected: no invented overseers. Actual: "The kiln schedule names four new overseers."
- Engine: kind `investigate`, authority `unsupported`. No state-change keys. Npc and lead asserts before this line are not the failure.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response and a publication failure. The unsupported object is narrated as a real schedule.

## 9. Frontier-gate roster

- Test: `test_frontier_gate_roster_http_does_not_use_observe_stock`
- Assertion: kind is `investigate`.
- Expected: `investigate`. Actual: `None`.
- Engine: kind `investigate`, authority `authored_visible_feature`.
- Published: the observe stock the test exists to replace. It names the roster board and does not say that closer looking yields nothing further.
- Class: B, preexisting. Confidence: high.
- Player-facing: incorrect response. The stock sentence is what the player reads.

## 10. Notice board read

- Test: `test_observe_stock_replacement_keeps_notice_board_working`
- Assertion: kind is `investigate` or `discover_clue`.
- Expected: one of those kinds. Actual: `None`.
- Engine: kind `discover_clue`, clue `notice_patrol_route`. State changes: `clue_revealed`, `interactable_id`.
- Published: "You read the notice board. The missing patrol was last seen taking the northwest mud track past the crates."
- Class: B, preexisting. Confidence: high.
- Player-facing: the assertion is test infrastructure. This isolated read publishes the authorized clue. It is not the twelve-turn T05 case, and it does not append the jab sentence.

## 11. Patrol travel

- Test: `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`
- Assertion: `body["resolution"]["resolved_transition"] is True`.
- Expected: `True`. Actual: `KeyError: resolved_transition`.
- Engine: kind `scene_transition`, `resolved_transition` true, target `old_milestone`. Exploration ran. Scene moves from `frontier_gate` to `old_milestone`.
- Published: "You arrive at Old Milestone."
- Class: B, preexisting. Confidence: high.
- Player-facing: no demonstrated wrong sentence or wrong scene. The test cannot see the transition flag on the public body.

## 12. Unsupported actions

- Test: `test_sequence_unsupported_actions_invent_nothing`
- Assertion: the Captain Voss response has `resolved_transition` false.
- Expected: `False`. Actual: `KeyError: resolved_transition`.
- Engine on that turn: kind `conversational_clarify`, transition false, reason `unresolved_addressee`.
- Published: "Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted."
- The observatory turn declines with `destination_not_established` and names the glass observatory. The footprints turn declines with `referent_not_in_scene`. Scene stays `frontier_gate`. Turn counter stays 1.
- Class: B, preexisting. Confidence: high.
- Player-facing: the sentences and the scene match the rest of the test. The failure is the missing public key.

## Shared evidence

The pre-handoff overlay produced the same projected body, the same engine fields, and the same conversational-decision results for every turn of these twelve tests. Details are in `BASELINE_RECONSTRUCTION.md`.
