# PR-PLAY-52 — Quarantined Investigation Narration Integration

## 1. Executive summary

Verdict: **A — PASS / READY**.

Actual gameplay investigations ran through the existing chat pipeline and exploration resolver. Experimental narration stayed quarantined. Mechanical outcomes, campaign state, and player-facing responses matched the baseline. Authorized discoveries stayed intact. Hidden information stayed out of the hook input. Narration did not write campaign state. Injected narration failures left the completed turn in place. No new relevant regression appeared.

The experiment entered through `POST /api/chat`. Live interpretation and provider calls were disabled. The existing exploration resolver decided both investigations. After that resolution, an opt-in hook replayed saved PR-PLAY-50 prose into the PR-PLAY-49 anchored preview and stored the result outside the player response.

Real provider requests: 0. Tokens: 0.

## 2. Source-level integration map

1. Player text arrives at `game.api.api_chat` and `game.api._chat_turn`.
2. With live interpretation disabled, `deterministic_conversational_decision` returns no execution for these sentences, and `parse_exploration_intent` classifies them.
3. `select_ordinary_resolver` selects the exploration resolver. `_resolve_engine_noncombat_seam` calls `game.exploration.resolve_exploration_action`. No second resolver was added.
4. `_apply_authoritative_resolution_state_mutation` commits the clue in memory.
5. `_build_gpt_narration_from_authoritative_state` builds the existing player-facing object. Successful `discover_clue` turns use `deterministic_provider_skip_line` and do not call the provider.
6. The quarantine hook then runs inside `_run_resolved_turn_pipeline`, after that object exists and before the pipeline returns it.
7. Finalization, logging, and the HTTP response continue on the original object. The hook's return value is discarded.
8. Diagnostics for the experiment are written only under the quarantine evidence directory, never into the player log.

The hook is in the shared pipeline, so `/api/action` would reach it too. This experiment exercised `/api/chat`.

## 3. Source change manifest

- `game/api.py`
- `game/quarantined_investigation_narration.py`
- `tests/test_pr_play_52_quarantined_integration.py`
- `tests/test_pr_play_49_anchored_narration.py`

Campaign content, model configuration, token budgets, and validator rules were not changed.

`tests/test_pr_play_49_anchored_narration.py` now allows `game/quarantined_investigation_narration.py` to name the anchored module. `game/api.py` still must not name that module, and it must not assign the quarantine result to the player response. The side-effect and allowlist assertions in that test are unchanged.

## 4. Experimental feature-gate documentation

- `ASHEN_QUARANTINE_INVESTIGATION_NARRATION=1` enables the hook. Any other value, including unset, leaves it off. The disabled path does not import the narration module.
- `ASHEN_QUARANTINE_NARRATION_SAMPLE` selects `stub`, `A1`, `A2`, `B1`, `B2`, `empty`, `malformed`, `unsafe`, or `missing`.
- `ASHEN_QUARANTINE_NARRATION_FAULT` injects `assembly_exception`, `invalid_projection`, `timeout`, `evidence_write`, or `unexpected`.
- `ASHEN_QUARANTINE_NARRATION_DIR` is the evidence directory. A path inside the campaign data directory is refused.
- The hook replays saved text or a fixed stub. It does not call a provider and it does not retry.

## 5. Notice-board baseline run

Action: `I examine the notice board.`.

Mechanical result: `{"kind": "discover_clue", "success": true, "action_id": "notice_board", "interactable_id": "notice_board", "clue_id": "notice_patrol_route", "clue_text": "The missing patrol was last seen taking the northwest mud track past the crates.", "discovered_clues": ["The missing patrol was last seen taking the northwest mud track past the crates."], "resolved_transition": false, "target_scene_id": null, "state_changes": {"clue_revealed": true, "already_searched": null, "skill_check_failed": null, "interactable_id": "notice_board"}}`.

Player-facing response: You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Resolver calls: `{'exploration': 1, 'social': 0}`. Elapsed test-client turn: 126.03 ms. Quarantine records: 0.

## 6. Notice-board experimental run

Same action and initial scene, with the gate on and saved response A1.

Mechanical result: `{"kind": "discover_clue", "success": true, "action_id": "notice_board", "interactable_id": "notice_board", "clue_id": "notice_patrol_route", "clue_text": "The missing patrol was last seen taking the northwest mud track past the crates.", "discovered_clues": ["The missing patrol was last seen taking the northwest mud track past the crates."], "resolved_transition": false, "target_scene_id": null, "state_changes": {"clue_revealed": true, "already_searched": null, "skill_check_failed": null, "interactable_id": "notice_board"}}`.

Player-facing response: You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Diagnostic: heuristic_pass_pending_review. Provider clients constructed: 0. Campaign writers entered from the hook: [].

Saved prelude:

The notice board stands weathered and crowded, its surface plastered with official decrees and hastily scrawled warnings. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s calls mingle with the restless shifting of watchers and refugees. The board’s messages draw a wary crowd, each line hinting at unease and unanswered questions.

Assembled experimental narration:

The notice board stands weathered and crowded, its surface plastered with official decrees and hastily scrawled warnings. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s calls mingle with the restless shifting of watchers and refugees. The board’s messages draw a wary crowd, each line hinting at unease and unanswered questions.

The missing patrol was last seen taking the northwest mud track past the crates.

## 7. Footprint baseline run

Action: `I examine the footprints.` Scene: `old_milestone`.

Mechanical result: `{"kind": "discover_clue", "success": true, "action_id": "prints", "interactable_id": "prints", "clue_id": "milestone_mud_prints", "clue_text": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "discovered_clues": ["Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."], "resolved_transition": false, "target_scene_id": null, "state_changes": {"clue_revealed": true, "already_searched": null, "skill_check_failed": null, "interactable_id": "prints"}}`.

Player-facing response: You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

Elapsed test-client turn: 277.313 ms.

## 8. Footprint experimental run

Same action, gate on, saved response B1.

Mechanical result: `{"kind": "discover_clue", "success": true, "action_id": "prints", "interactable_id": "prints", "clue_id": "milestone_mud_prints", "clue_text": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.", "discovered_clues": ["Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."], "resolved_transition": false, "target_scene_id": null, "state_changes": {"clue_revealed": true, "already_searched": null, "skill_check_failed": null, "interactable_id": "prints"}}`.

Player-facing response: You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

Diagnostic: heuristic_pass_pending_review. Provider clients: 0. Hook writer calls: []. Resolver calls: {'exploration': 1, 'social': 0}.

Saved prelude:

The damp earth near the leaning milestone bears the faint impression of footsteps, their edges softened by recent rain. The muddied ground tells a story of passage, yet the details remain elusive, leaving the trail’s origin and direction shrouded in uncertainty.

Assembled experimental narration:

The damp earth near the leaning milestone bears the faint impression of footsteps, their edges softened by recent rain. The muddied ground tells a story of passage, yet the details remain elusive, leaving the trail’s origin and direction shrouded in uncertainty.

Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

## 9. Paired state comparisons

Compared after removing only generated stamps, session and campaign run ids, the in-memory GM object id, timestamps, and latency fields. Clue ids and scene ids were not removed.

Notice board state differences: none.

Footprints state differences: none.

Both runs discovered the resolver's clue. That state change is the mechanical action, and it is the same in the baseline and the experimental run.

## 10. Saved provider-response replays

The four PR-PLAY-50 responses were read from `artifacts/pr_play_50/requests.json` and were not edited. The raw output text was the prelude. A saved response is accepted only when its stored authoritative discovery is the clue the resolver just produced.

- **A1** — heuristic_pass_pending_review; fallback=False; anchor starts `The missing patrol was last seen taking the northwest mud track past t`
- **A2** — heuristic_pass_pending_review; fallback=False; anchor starts `The missing patrol was last seen taking the northwest mud track past t`
- **B1** — heuristic_pass_pending_review; fallback=False; anchor starts `Faint overlapping prints mark the mud around the old milestone, but th`
- **B2** — heuristic_pass_pending_review; fallback=False; anchor starts `Faint overlapping prints mark the mud around the old milestone, but th`
- **A1_on_footprints** — incorrect_investigation_response_pairing; fallback=True; anchor starts `Faint overlapping prints mark the mud around the old milestone, but th`

## 11. Authorized narration projections

The hook receives a detached JSON object with the resolver kind, success, action id, interactable id, discovered clue text, already-searched or failed-check flags, public location, summary, visible facts, and player-known clue texts. It does not receive the scene catalog, hidden facts, GM notes, world object, quest journal, clue ids, hints, or skill-check rolls.

Notice-board projection status: `discovered`.

Footprint projection status: `discovered`.

Hidden-string hits inside those projections and hook inputs: none.

## 12. Immutable discovery-anchor evidence

Notice-board anchor: The missing patrol was last seen taking the northwest mud track past the crates.

Footprint anchor: Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

The anchor text is the resolver's `clue_text`. The tests assert that sentence; they do not pass it in as a chosen narration.

Second notice-board examination diagnostic: heuristic_pass_pending_review. Anchor statuses: [('known', 'The examination adds nothing new to what you already know.'), ('previously_known', 'The missing patrol was last seen taking the northwest mud track past the crates.')].

Rain-barrel examination, same session after the notice board:

- Resolver: `{"kind": "investigate", "success": true, "action_id": "i_examine_the_rain_barrel", "interactable_id": null, "clue_id": null, "clue_text": null, "discovered_clues": [], "resolved_transition": false, "target_scene_id": null, "state_changes": {"clue_revealed": null, "already_searched": null, "skill_check_failed": null, "interactable_id": null}}`.
- Player-facing: Provider calls are disabled for this run, so no live narration was generated.
- Quarantine diagnostic: heuristic_pass_pending_review.
- Quarantine anchors: [{'order': 0, 'source': 'player_knowledge', 'status': 'previously_known', 'text': 'The missing patrol was last seen taking the northwest mud track past the crates.'}].

The barrel resolver discovered nothing. The anchor that remains is the patrol sentence with status `previously_known`, because that clue was already in player knowledge. It is not marked newly revealed.

## 13. Hidden-information isolation results

Each gameplay scene copy carried canary GM notes, an undiscovered clue, a hidden destination string, an NPC motive, a quest twist, and an unrelated world string. The frontier scene's authored hidden facts and internal clue ids were also scanned.

Leaks in hook inputs, prelude requests, and projections: none.

The player-facing responses do not contain the saved preludes or the quarantine diagnostic.

## 14. Mechanical-authority isolation results

During the hook, campaign writers were wrapped. `save_session`, `save_world`, `save_character`, `save_combat`, `append_log`, `_save_json`, and `_atomic_save_json` raise if called while the hook is active.

Notice-board hook writer calls: []. Footprint hook writer calls: [].

An invalid projection carrying travel and `currency_gained` was rejected with `side_effects_outside_offline_slice` before any preview. The gameplay clue remained the resolver's clue.

Exploration resolver calls stayed at one per investigation. Provider client constructions: 0 and 0.

## 15. Failure-isolation results

Each fault ran a fresh investigation through `/api/chat`. The player-facing text, mechanical result, and scrubbed campaign state matched the baseline. The resolver ran once. No provider client was constructed.

- **failure_missing** — missing_saved_prelude; fallback=True; evidence_write=ok; error=None
- **failure_empty** — invalid_prelude; fallback=True; evidence_write=ok; error=None
- **failure_malformed** — invalid_prelude; fallback=True; evidence_write=ok; error=None
- **failure_unsafe** — semantic_rejection; fallback=True; evidence_write=ok; error=None
- **failure_assembly_exception** — generator_or_renderer_error; fallback=True; evidence_write=ok; error=None
- **failure_invalid_projection** — invalid_authorized_projection; fallback=True; evidence_write=ok; error=side_effects_outside_offline_slice
- **failure_A1** — incorrect_investigation_response_pairing; fallback=True; evidence_write=ok; error=None
- **failure_timeout** — simulated_timeout; fallback=True; evidence_write=ok; error=None
- **failure_evidence_write** — heuristic_pass_pending_review; fallback=False; evidence_write=failed; error=None
- **failure_unexpected** — unexpected_experimental_hook_exception; fallback=True; evidence_write=ok; error='simulated_unexpected_experimental_hook_exception'

## 16. Player-facing response comparisons

Notice board identical: True.

Footprints identical: True.

Notice board: You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Footprints: You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

The assembled experimental narration is not a substring of either player-facing response. The HTTP body does not contain a quarantine field.

## 17. Performance measurements

No provider latency is included. PR-PLAY-50's mean provider latency of about 2.22 seconds is context only.

One experimental notice-board turn, test client included: 213.466 ms. In-turn hook timings: `{"projection_build_ms": 0.072, "projection_ms": 0.312, "saved_lookup_ms": 0.021, "validation_ms": 4.01, "assembly_ms": 0.007, "serialization_ms": 0.102, "evidence_write_ms": 0.743, "hook_work_ms": 4.675, "total_hook_ms": 7.61}`.

Thirty-one repeats on the resolution and scene captured from that gameplay turn:

- Hook work, excluding evidence writing: mean 3.757 ms, median 3.971 ms, max 5.109 ms.
- Total including evidence writing: mean 6.063 ms, median 6.67 ms, max 8.158 ms.
- Evidence writing alone: mean 0.683 ms, median 0.751 ms, max 1.141 ms.
- Projection build: mean 0.05 ms. Saved lookup: mean 0.015 ms. Validation: mean 3.368 ms. Assembly: mean 0.005 ms.

Total-hook outlier under the recorded rule: None. The evidence-write maximum is a disk spike of 1.141 ms and is not required for a future player-facing integration.

## 18. Regression results

Collected: 405. Passed: 402. Failed: 3. Errors: 0. Skipped: 0.

Failed node ids: ['tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution', 'tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues', 'tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues'].

Pre-existing failures from the PR-PLAY-51 comparable suite: ['tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution', 'tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues', 'tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues'].

New failures: none.

Raw pytest output: `focused.txt`. JUnit: `focused.xml`.

The PR-PLAY-51 authority-suite seal-metadata failures were not re-run and were not repaired. They remain the recorded baseline.

Campaign files mutated by the focused run: none.

## 19. Known limitations

The hook is investigation-only and off unless the environment variable is exactly `1`. Combat, travel, inventory, currency, conditions, quests, dialogue, merchants, and general exploration are not narrated by it.

Successful clue discovery already skips the provider. A repeat search and the rain-barrel examination do not. With provider calls disabled, those turns use the existing disabled-provider sentence. This pass did not change that branch.

On the rain-barrel turn the resolver discovered nothing, and the quarantined anchor still appended the already-known patrol sentence as `previously_known`. The structured status is not `newly_revealed`. The assembled prose does not itself say that the clue was already known, so that string must stay out of the player response.

The validator is still a heuristic. `You find a silver key beneath the board` remains a known false accept from PR-PLAY-49 and was not used as proof of rejection. The failure case used `The hidden passage opens before you`, which the current validator rejects. Validator rules were not widened or narrowed.

A passing prelude is not approval to show it to a player. The quarantine output is evidence.

## 20. Integration readiness decision

- Gate 1_real_gameplay_path: **pass**
- Gate 2_mechanical_equivalence: **pass**
- Gate 3_player_facing_equivalence: **pass**
- Gate 4_discovery_integrity: **pass**
- Gate 5_hidden_information_isolation: **pass**
- Gate 6_narration_authority: **pass**
- Gate 7_failure_isolation: **pass**
- Gate 8_regression_stability: **pass**

## 21. PR-PLAY-53 recommendation

PR-PLAY-53 should be a narrow quarantined live-provider experiment after completed investigation actions. Use this same gameplay pipeline. Resolve the action before narration. Build the authorized projection already used here. Make a small, explicitly bounded number of provider requests. Keep the engine-owned discovery anchor. Measure combined gameplay and provider latency. Save the raw model prose. Compare it with the deterministic player response. Judge consequential fabrication separately. Leave the player-facing response deterministic. Do not enable player-facing AI narration in that pass either.

## 22. Final verdict

**A — PASS / READY**

Actual gameplay investigations ran through the existing chat pipeline and exploration resolver. Experimental narration stayed quarantined. Mechanical outcomes, campaign state, and player-facing responses matched the baseline. Authorized discoveries stayed intact. Hidden information stayed out of the hook input. Narration did not write campaign state. Injected narration failures left the completed turn in place. No new relevant regression appeared.

Real provider requests during this pass: 0. Tokens: 0.

