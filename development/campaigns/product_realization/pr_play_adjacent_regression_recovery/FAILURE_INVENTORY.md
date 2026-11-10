# Failure inventory

The 12 records below are the actual stopping failures, not every unexecuted assertion later in each test.
All are HTTP 200 call-phase failures; the two missing transition keys are KeyErrors, not collection/environment errors.
Full requests/responses, pre-projection bodies, routing and before/after session/character/world/log are in http_capture.json.
Complete traceback and fixture names are in failures.json and repeated in classification_matrix.json.

## F01 — test_general_unknown_player_named_object_is_not_instantiated

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`.
- Failing assertion: response resolution kind == investigate.
- Expected: 'investigate'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['incorrect_response']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I inspect the ivory metronome."}`; status 200; public resolution `{}`.
Published: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.
Routing: `[{"player_text": "I inspect the ivory metronome.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `unsupported`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_unknown_player_named_object_is_not_instantiated`; full text also in matrix row.

## F02 — test_general_narration_only_object_does_not_gain_authority

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority`.
- Failing assertion: first response resolution kind == observe.
- Expected: 'observe'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['incorrect_response']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I look around."}`; status 200; public resolution `{}`.
Published: I cannot provide a validated response to that request.
Routing: `[{"player_text": "I look around.", "reason": null, "decision": null}]`. Engine kind `observe`; authority `None`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_narration_only_object_does_not_gain_authority`; full text also in matrix row.

## F03 — test_general_abstract_reference_does_not_become_physical

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_abstract_reference_does_not_become_physical`.
- Failing assertion: glassport is not in the published sentence.
- Expected: "abstract reference text without the stub's Glassport claim". Actual: 'The ledger lists eight named crews bound for Glassport.'.
- Classification: **E — unresolved_origin**. Confidence: high that origin remains unresolved; high in current failure.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`, `game/perception_grounding.py`, `game/immutable_valid_response.py`.
- Supporting evidence: Fresh unchanged-test failure and full HTTP capture. Prior current/historical captures agree; documented overlay removes handoff symbols. game/perception_grounding.py exits when immutable acceptance forbids replacement.
- Contradictory evidence: Prior audit labels this B/high; overlay equality supports a preexisting hypothesis. No authenticated exact pre-repair dirty source snapshot or exact pre-repair run exists.
- Player significance: ['incorrect_response', 'publication_contract']. Exact historical origin and compatibility/provenance of reconstructed overlay cannot be established. Current publication defect is demonstrated; no evidence establishes it as new because of the repair.

HTTP event 1: `{"text": "I inspect the shipping ledger."}`; status 200; public resolution `{}`.
Published: The ledger lists eight named crews bound for Glassport.
Routing: `[{"player_text": "I inspect the shipping ledger.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `authored_abstract_reference`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_abstract_reference_does_not_become_physical`; full text also in matrix row.

## F04 — test_general_readable_surface_communicates_contents

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents`.
- Failing assertion: response resolution kind is investigate or discover_clue.
- Expected: 'investigate or discover_clue'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['test_infrastructure_only']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I read the tariff slate."}`; status 200; public resolution `{}`.
Published: In Mill Loft, a dry loft, a grain hopper, and a tariff slate Dock fees rise after the second horn.
Routing: `[{"player_text": "I read the tariff slate.", "reason": null, "decision": null}]`. Engine kind `discover_clue`; authority `authored_interactable`; state_changes `{"clue_revealed": true, "interactable_id": "tariff_slate"}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, clue_knowledge, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, lead_registry, last_saved_at, last_publication, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_readable_surface_communicates_contents`; full text also in matrix row.

## F05 — test_general_hidden_object_is_not_revealed_by_naming

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_hidden_object_is_not_revealed_by_naming`.
- Failing assertion: published sentence contains a no-such-thing or nothing-here-matches refusal.
- Expected: 'refusal that does not narrate taking the token'. Actual: 'You pry up the hopper and pocket the brass token.'.
- Classification: **E — unresolved_origin**. Confidence: high that origin remains unresolved; high in current failure.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`, `game/perception_grounding.py`, `game/immutable_valid_response.py`.
- Supporting evidence: Fresh unchanged-test failure and full HTTP capture. Prior current/historical captures agree; documented overlay removes handoff symbols. game/perception_grounding.py exits when immutable acceptance forbids replacement.
- Contradictory evidence: Prior audit labels this B/high; overlay equality supports a preexisting hypothesis. No authenticated exact pre-repair dirty source snapshot or exact pre-repair run exists.
- Player significance: ['incorrect_response', 'publication_contract']. Exact historical origin and compatibility/provenance of reconstructed overlay cannot be established. Current publication defect is demonstrated; no evidence establishes it as new because of the repair.

HTTP event 1: `{"text": "I inspect the brass token."}`; status 200; public resolution `{}`.
Published: You pry up the hopper and pocket the brass token.
Routing: `[{"player_text": "I inspect the brass token.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `authored_hidden`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_hidden_object_is_not_revealed_by_naming`; full text also in matrix row.

## F06 — test_general_failed_inspection_then_observe_uses_current_scene

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene`.
- Failing assertion: first response resolution kind == investigate.
- Expected: 'investigate'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['incorrect_response']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I inspect the ivory metronome."}`; status 200; public resolution `{}`.
Published: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.
Routing: `[{"player_text": "I inspect the ivory metronome.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `unsupported`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_then_observe_uses_current_scene`; full text also in matrix row.

## F07 — test_general_authored_alias_binds

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds`.
- Failing assertion: response resolution kind is investigate or discover_clue.
- Expected: 'investigate or discover_clue'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['incorrect_response']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I examine the feed chute."}`; status 200; public resolution `{}`.
Published: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.
Routing: `[{"player_text": "I examine the feed chute.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `authored_interactable`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_authored_alias_binds`; full text also in matrix row.

## F08 — test_general_failed_inspection_creates_no_world_facts

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_creates_no_world_facts`.
- Failing assertion: four new overseers is not in the published sentence.
- Expected: 'no invented overseers'. Actual: 'The kiln schedule names four new overseers.'.
- Classification: **E — unresolved_origin**. Confidence: high that origin remains unresolved; high in current failure.
- Fixture: Synthetic mill-loft scene/world, tariff slate, skylight, hidden token, abstract ledger; _seed_scene_runtime and stubbed generation in referenced-surface HTTP tests. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`, `game/perception_grounding.py`, `game/immutable_valid_response.py`.
- Supporting evidence: Fresh unchanged-test failure and full HTTP capture. Prior current/historical captures agree; documented overlay removes handoff symbols. game/perception_grounding.py exits when immutable acceptance forbids replacement.
- Contradictory evidence: Prior audit labels this B/high; overlay equality supports a preexisting hypothesis. No authenticated exact pre-repair dirty source snapshot or exact pre-repair run exists.
- Player significance: ['incorrect_response', 'publication_contract']. Exact historical origin and compatibility/provenance of reconstructed overlay cannot be established. Current publication defect is demonstrated; no evidence establishes it as new because of the repair.

HTTP event 1: `{"text": "I inspect the glass kiln schedule."}`; status 200; public resolution `{}`.
Published: The kiln schedule names four new overseers.
Routing: `[{"player_text": "I inspect the glass kiln schedule.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `unsupported`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_general_failed_inspection_creates_no_world_facts`; full text also in matrix row.

## F09 — test_frontier_gate_roster_http_does_not_use_observe_stock

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock`.
- Failing assertion: response resolution kind == investigate.
- Expected: 'investigate'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Authored frontier_gate fixture with roster/notice board. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['incorrect_response']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "If the watch already has a commander on this, I'll check the roster board the serjeant is watching."}`; status 200; public resolution `{}`.
Published: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.
Routing: `[{"player_text": "If the watch already has a commander on this, I'll check the roster board the serjeant is watching.", "reason": null, "decision": null}]`. Engine kind `investigate`; authority `authored_visible_feature`; state_changes `{}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, interaction_context, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_frontier_gate_roster_http_does_not_use_observe_stock`; full text also in matrix row.

## F10 — test_observe_stock_replacement_keeps_notice_board_working

- Test/file: `tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working`.
- Failing assertion: response resolution kind is investigate or discover_clue.
- Expected: 'investigate or discover_clue'. Actual: None.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: Authored frontier_gate fixture with roster/notice board. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['test_infrastructure_only']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I read the notice board."}`; status 200; public resolution `{}`.
Published: You read the notice board. The missing patrol was last seen taking the northwest mud track past the crates.
Routing: `[{"player_text": "I read the notice board.", "reason": null, "decision": null}]`. Engine kind `discover_clue`; authority `authored_interactable`; state_changes `{"clue_revealed": true, "interactable_id": "notice_board"}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, clue_knowledge, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, lead_registry, last_saved_at, last_publication, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_referenced_surface_grounding_inspection_resolution.py::test_observe_stock_replacement_keeps_notice_board_working`; full text also in matrix row.

## F11 — test_sequence_patrol_travel_reaches_the_movement_resolver

- Test/file: `tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`.
- Failing assertion: body['resolution']['resolved_transition'] is True.
- Expected: True. Actual: 'KeyError: resolved_transition'.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: PR-PLAY-38 recorded interpretation and persistent frontier-gate fixture; _install_frontier, _quiet_models. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['test_infrastructure_only']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I want to follow the trail connected to the missing patrol."}`; status 200; public resolution `{}`.
Published: You arrive at Old Milestone.
Routing: `[{"player_text": "I want to follow the trail connected to the missing patrol.", "reason": "grounded_movement_destination", "decision": "ConversationalDecision(category=<ConversationalDecisionCategory.EXECUTE: 'EXECUTE'>, primary_intention='Go to Follow the missing patrol rumor.', intent_family='movement', incidental_context=[], proposed_operation='MOVE', proposed_target='leave_for_follow_the_missing_patrol_rumor', proposed_record={'communication_mode': 'IN_WORLD_ACTION', 'interpretation_status': 'INTERPRETED', 'player_intent': {'summary': 'Go to Follow the missing patrol rumor.'}, 'action_components': [{'operation_class': 'MOVE', 'target_ref': 'leave_for_follow_the_missing_patrol_rumor', 'description': 'Go to Follow the missing patrol rumor.'}], 'references': {'resolved_references': [{'text': 'Follow the missing patrol rumor', 'entity_id': 'leave_for_follow_the_missing_patrol_rumor'}], 'unresolved_references': []}}, missing_information=[], context_references=[], requires_authoritative_execution=True, reason='grounded_movement_destination', confidence=0.86, ambiguity=None, player_facing_text='', context_update={'conversational_context': {'pending_clarification': None, 'focused_destination': None}}, intent_modality='committed', secondary_intentions=[], execution_policy='execute_primary', communication_owner='CHARACTER', communication_purpose='ACTION', authorization=None)"}]`. Engine kind `scene_transition`; authority `None`; state_changes `{"scene_changed": true, "scene_transition_occurred": true, "arrived_at_scene": true, "new_scene_context_available": true}`.
Changed persisted top-level fields: session: clocks, chat_history, runtime_scene_overlays, last_action_debug, active_scene_id, _runtime_canonical_ctir_stamp_v1, scene_runtime, _runtime_progression_nodes_fingerprint_v1, discourse_focus, turn_counter, last_turn_response_policy, visited_scene_ids, emergent_actor_debug, narration_temporal_provenance, _runtime_canonical_ctir_v1, conversational_context, bounded_improvisation, scene_state, interpretation_telemetry, last_bounded_improvisation_promotion, _runtime_narration_plan_bundle_stamp_v1, last_saved_at, last_publication, debug_traces, _runtime_narration_plan_bundle_v1, character: (none), world: factions, event_log. Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_pr_play_39_action_admission.py::test_sequence_patrol_travel_reaches_the_movement_resolver`; full text also in matrix row.

## F12 — test_sequence_unsupported_actions_invent_nothing

- Test/file: `tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing`.
- Failing assertion: npc response resolution resolved_transition is False.
- Expected: False. Actual: 'KeyError: resolved_transition'.
- Classification: **C — obsolete_expectation**. Confidence: high.
- Fixture: PR-PLAY-38 recorded interpretation and persistent frontier-gate fixture; _install_frontier, _quiet_models. Pytest fixtures: tmp_path_factory, _forbid_live_model_calls, monkeypatch, tmp_path, request.
- Production path: `game/api.py`, `game/conversational_orchestration.py`, `game/referenced_surface.py`, `game/exploration.py`, `game/player_http_projection.py`.
- Supporting evidence: PR-PLAY-67 explicitly defines resolution as an empty compatibility placeholder. PR-PLAY-67 migrated analogous assertions to persisted server logs. Fresh capture contains the engine resolution, while player response resolution is {}.
- Contradictory evidence: Older test expects internal resolver fields; prior adjacent audit labeled this B. Some tests also have later prose assertions; class C covers only the actual stopping assertion.
- Player significance: ['test_infrastructure_only']. Later assertions were not executed after this stopping assertion. Wrong scene stock in some captures remains a separate publication concern, not excused by this classification.

HTTP event 1: `{"text": "I ask Captain Voss what he knows about the gate."}`; status 200; public resolution `{}`.
Published: Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.
Routing: `[{"player_text": "I ask Captain Voss what he knows about the gate.", "reason": null, "decision": null}]`. Engine kind `conversational_clarify`; authority `None`; state_changes `{}`.
Changed persisted top-level fields: session: conversational_context, last_saved_at, character: (none), world: (none). Full old/new values remain in machine evidence.

HTTP event 2: `{"text": "I want to follow the trail to the glass observatory."}`; status 200; public resolution `{}`.
Published: You want to reach follow the trail to the glass observatory, but that is not an established destination from here. You stay where you are.
Routing: `[{"player_text": "I want to follow the trail to the glass observatory.", "reason": "destination_not_established", "decision": "ConversationalDecision(category=<ConversationalDecisionCategory.DECLINE: 'DECLINE'>, primary_intention='I want to follow the trail to the glass observatory.', intent_family='movement', incidental_context=[], proposed_operation=None, proposed_target=None, proposed_record=None, missing_information=[], context_references=[], requires_authoritative_execution=False, reason='destination_not_established', confidence=0.82, ambiguity=None, player_facing_text='You want to reach follow the trail to the glass observatory, but that is not an established destination from here. You stay where you are.', context_update=None, intent_modality='committed', secondary_intentions=[], execution_policy='decline_unauthorized_route', communication_owner='GM', communication_purpose='EXPLANATION', authorization=None)"}]`. Engine kind `conversational_decline`; authority `None`; state_changes `{}`.
Changed persisted top-level fields: session: conversational_context, last_saved_at, character: (none), world: (none). Full old/new values remain in machine evidence.

HTTP event 3: `{"text": "I want to investigate the footprints."}`; status 200; public resolution `{}`.
Published: Nothing here matches footprints. Nothing has been attempted.
Routing: `[{"player_text": "I want to investigate the footprints.", "reason": null, "decision": null}]`. Engine kind `conversational_decline`; authority `None`; state_changes `{}`.
Changed persisted top-level fields: session: conversational_context, last_saved_at, character: (none), world: (none). Full old/new values remain in machine evidence.

Traceback: `artifacts/pr_play_adjacent_regression_recovery/failures.json#tests/test_pr_play_39_action_admission.py::test_sequence_unsupported_actions_invent_nothing`; full text also in matrix row.
