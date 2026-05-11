# Mutation Boundary Inventory

Tags: `SAFE` means deterministic/low semantic risk; `RISKY` means repair/normalization can obscure origin; `CRITICAL` means late semantic/speaker/fallback/output mutation after planning; `UNKNOWN` means search found the surface but ownership/effects need runtime tracing.

| Boundary | Before Object | After Object | Mutation Type | Deterministic | Intended | Upstream Caller | Downstream Consumer | Tag |
|---|---|---|---|---:|---:|---|---|---|
| Chat route trace assembly (`game/api.py::chat`) | Session/scene/world/player text | Payload `debug_traces`, `canonical_entry`, `turn_trace` | Metadata add | Yes | Yes | API chat orchestration | Replay helper, UI/debug | SAFE |
| Resolved turn pipeline (`game/api.py::_run_resolved_turn_pipeline`) | Resolution/normalized action/session | Scene/session/world/log updates and GM payload | State + metadata mutation | Yes | Yes | Chat/action route | Storage, final emission | RISKY |
| Canonical social entry (`game/interaction_context.py::resolve_directed_social_entry`) | Player text/session/scene/world | Route target dict | Route choice | Yes | Yes | API route selection | Turn trace, prompt, social emission | SAFE |
| Social continuity break (`apply_world_action_social_continuity_break`) | Session interaction context | Cleared/updated active target | Speaker/continuity metadata change | Yes | Yes | Route resolution | Future turns | CRITICAL |
| Dialogue interaction establishment (`establish_dialogue_interaction_from_input`) | Session | `interaction_context.active_interaction_target_id` | Speaker continuity state change | Yes | Yes | API after input | Future routing/speaker | CRITICAL |
| Routing contract finalization (`finalize_routing_social_turn_contract`) | Directed-entry dict | Adds `social_turn_contract` | Metadata normalization | Yes | Yes | `resolve_directed_social_entry` | API trace/prompt | SAFE |
| Destination reconciliation (`scene_destination_binding.reconcile_scene_transition_destination`) | Normalized action target | Reconciled target + metadata | Route/transition correction | Yes | Yes | Action resolution | Scene activation/storage | CRITICAL |
| Schema normalization (`schema_contracts.normalize_*`) | Raw object | Canonical dict | Metadata/content normalization | Yes | Yes | Storage/import/runtime adapters | Validators/world systems | SAFE |
| Legacy adapters (`schema_contracts.adapt_legacy_*`) | Legacy-shaped dict | Canonical normalized dict + metadata of unknowns | Repair/normalization | Yes | Yes | Import/runtime compatibility | Validators | RISKY |
| World clock/project/clue normalization | Raw world rows | Canonical rows | State normalization | Yes | Yes | Clocks/projects/clues modules | Storage/world progression | SAFE |
| Upstream prepared emission merge (`upstream_response_repairs.merge_upstream_prepared_emission_into_gm_output`) | GM output candidate | GM metadata prepared emission fields | Fallback/repair metadata add | Yes | Yes | Final emission gate entry | Gate response-type layer | CRITICAL |
| Opening fallback attach (`maybe_attach_upstream_prepared_opening_fallback_payload`) | GM output + curated facts | `upstream_prepared_opening_fallback` | Fallback substitution metadata | Yes | Yes | Gate entry | Response-type/opening selector | CRITICAL |
| Final emission gate entry (`fallback_provenance_debug.record_final_emission_gate_entry`) | GM output | Metadata stage/fingerprint | Metadata add | Yes | Yes | Gate | Stage diff/replay | SAFE |
| Response-type enforcement (`final_emission_gate` response-type layer) | Candidate text + contract | Candidate or repaired/fallback text + debug | Output repair/substitution | Yes | Yes | Gate | FEM, finalization | CRITICAL |
| Strict-social replacement path (`final_emission_gate` + `social_exchange_emission`) | Candidate text | Strict-social text/details/FEM | Speaker/fallback/text replacement | Yes | Yes | Gate strict-social branch | Final output/replay | CRITICAL |
| Speaker contract enforcement (`speaker_contract_enforcement.enforce_emitted_speaker_with_contract`) | Candidate text | Repaired text + enforcement payload | Speaker mutation | Yes | Yes | Gate/social emission | Final output/FEM | CRITICAL |
| Interaction continuity repair (`interaction_continuity.repair_interaction_continuity`) | Candidate text | Repaired continuity-safe text | Speaker/semantic text repair | Yes | Yes | Gate continuity step | Final output/FEM | CRITICAL |
| Fallback behavior repair (`final_emission_repairs._apply_fallback_behavior_layer`) | Candidate text | Fallback-compliant text + meta | Output repair | Yes | Yes | Gate repair stack | Final output/FEM | CRITICAL |
| Acceptance quality repair (`acceptance_quality.repair_acceptance_quality_minimal`) | Candidate text | Whitespace-normalized or terminal sentence dropped | Text repair | Yes | Yes | Gate N4 layer | Final output/FEM | RISKY |
| Player-facing narration purity repair (`minimal_repair_player_facing_narration_purity`) | Candidate text | Scaffold/header stripped text | Sanitizer-like text repair | Yes | Yes | Gate purity layer | Final output/FEM | CRITICAL |
| Anti-railroading/context/tone repair layers | Candidate text | Possibly altered text or repair hints/meta | Semantic compliance repair | Yes | Yes | Gate stack | Final output/FEM | CRITICAL |
| Fast fallback neutral composition (`final_emission_gate` layer) | Fallback-ish text | Neutralized fallback text | Fallback rewrite | Yes | Yes | Gate | Final output/FEM | CRITICAL |
| Output sanitizer strip-only (`output_sanitizer.sanitize_output_text`) | Final text | Stripped/sanitized text | Sanitizer transform | Yes | Yes | API/gate finalization | User-facing output | CRITICAL |
| Output sanitizer legacy sentence rewrite (`output_sanitizer._rewrite_line`) | Internal/procedural sentence | Diegetic fallback sentence | Semantic rewrite | Yes | Intended only in legacy/diagnostic mode | Sanitizer | User-facing output | CRITICAL |
| Serialized payload extraction (`extract_player_text_from_serialized_payload`) | JSON-ish output text | Extracted player-facing string | Sanitizer recovery | Yes | Yes | Sanitizer | Final text | RISKY |
| FEM creation (`final_emission_meta.ensure_final_emission_meta_dict`) | GM output | `_final_emission_meta` dict | Metadata add | Yes | Yes | Gate/repairs | Replay/evaluators | SAFE |
| FEM patch/merge (`patch_final_emission_meta`, layer merge helpers) | FEM dict | Layer flags/source/fallback data | Metadata mutation | Yes | Yes | Gate/repairs | Replay/evaluators | SAFE |
| FEM normalized observability (`normalize_final_emission_meta_for_observability`) | Raw FEM | Shallow normalized copy | Read-side normalization | Yes | Yes | Evaluators/dashboard | Observability events | SAFE |
| Stage snapshot (`stage_diff_telemetry.record_stage_snapshot`) | GM output | Metadata snapshots | Metadata observation | Yes | Yes | Gate/retry | Dashboard/evaluator | SAFE |
| Stage transition (`record_stage_transition`) | Before/after snapshots | Diff transition | Metadata observation | Yes | Yes | Gate/retry | Dashboard/evaluator | SAFE |
| Fallback provenance realignment (`realign_fallback_provenance_selector_to_current_text`) | Provenance metadata + current text | Updated selector/current fingerprint | Metadata correction | Yes | Yes | Gate after fallback repair | Stage diff/debug | RISKY |
| Debug trace append (`game/api.py` session debug traces) | Session | Appended compact trace | Metadata mutation | Yes | Yes | API chat | Replay/UI | SAFE |
| Behavioral evaluator attachment (`game/behavioral_evaluators.maybe_attach_*`) | Session/debug lane | Evaluator result attached | Metadata add | Yes | Yes, if enabled | Runtime/eval hooks | Debug/evaluator reports | SAFE |
| Public state projection (`api_ui_mode`, UI mode policy) | Internal state | Player/debug/author projected state | Projection/stripping | Yes | Yes | API state endpoint | UI | SAFE |
| Emergent enrollment from GM output (`interaction_context.apply_conservative_emergent_enrollment_from_gm_output`) | Final narration text + scene state | Scene addressability hints | Text-derived metadata change | Yes | Intended but text-derived | Post-GM update | Future routing | CRITICAL |
| Journal/narration consistency supplements | GM text/state | Journal/lead supplemental rows | Text-derived state mutation | Yes | Intended under current policy | Post-GM update | Journal/lead systems | CRITICAL |

## Highest-Risk Boundary Pattern

The most locality-destroying pattern is late, post-planning text mutation inside `game/final_emission_gate.py` and adjacent repair modules. The code is deterministic and well-instrumented, but a bad replay can surface as final text drift even when the root cause is route, contract, fallback selection, sanitizer rewrite, or speaker enforcement.

