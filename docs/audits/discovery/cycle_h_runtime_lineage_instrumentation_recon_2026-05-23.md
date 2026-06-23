# Cycle H Runtime Lineage Instrumentation Recon

Date: 2026-05-23  
Scope: Read-only reconnaissance for runtime lineage instrumentation. No product behavior or replay contract changes were made.

## Executive Summary

The runtime already emits substantial per-turn evidence. Final emission metadata (FEM), stage-diff snapshots/transitions, fallback provenance, turn traces, speaker enforcement payloads, sanitizer lineage, state mutation traces, and scenario-spine metadata expose many individual decisions after they happen. Fallback ownership is strongest for opening, sealed, visibility, sanitizer-empty, strict-social, and upstream fast-fallback paths. Repair visibility is strongest for FEM-backed policy layers and speaker contract enforcement. Mutation visibility is strongest at the coarse "text changed" or known-lineage-token level.

The signals are only partially measurable as frequencies. Most raw fields can be counted from debug/replay rows, but there is no single runtime lineage event schema that classifies fallback, speaker repair, mutation kind, and gate path consistently at the moment of decision. `final_emission_mutation_lineage` is intentionally narrow, `stage_diff_telemetry` aggregates gate changes rather than attributing every sublayer write, and replay/dashboard classifiers are test-side consumers rather than production counters.

The principal invisible area is recurrence. Scenario-spine already has turn identity, branch identity, FEM snapshots, metadata completeness, degradation windows, and repeated-generic-opening analysis, but it does not aggregate repeated fallback kinds, repeated speaker repairs, repeated mutation kinds, or recurring gate outcomes across turns. There is also no global/runtime aggregation and no stable recurrence key for lineage events.

Recommendation: extend the existing observational path, not the legality path. Introduce a small read-side `runtime_lineage_events` projection from already-stamped FEM, stage-diff, speaker, sanitizer, and state-mutation fields; record/aggregate it first in scenario-spine artifacts. Keep all instrumentation inspect-only and avoid feeding it back into gate or evaluator decisions.

## Runtime Pipeline Map

| Stage | File(s) | Key Function(s) | Runtime Decisions | Existing Visibility | Instrumentation Opportunity |
|---|---|---|---|---|---|
| API / engine entry and routing | `game/api.py`, `game/interaction_context.py`, `game/interaction_routing.py` | `chat`, `action`, `_prepare_interaction_from_turn_input`, `_resolve_engine_noncombat_seam`, `_apply_authoritative_resolution_state_mutation`, `_run_resolved_turn_pipeline` | Route selection, directed social entry, resolution type, authoritative state commits, whether GPT narration is entered | `debug_traces`, `turn_trace`, `canonical_entry`, state mutation traces; persisted session/debug rows | Emit engine/route lineage events beside existing compact trace; include route and authoritative mutation kind |
| Resolved-turn meaning snapshot | `game/ctir_runtime.py`, `game/ctir.py`, `game/turn_packet.py` | `ensure_ctir_for_turn`, `build_runtime_ctir_for_narration`, `build_turn_packet`, `attach_turn_packet` | What resolved meaning/contracts are handed downstream; retry-stable turn stamp | CTIR stamp, turn packet, planner convergence metadata | Carry `turn_id`/turn stamp into lineage projection; do not duplicate CTIR content |
| Planner / plan bundle | `game/narration_plan_bundle.py`, `game/narrative_planning.py`, `game/planner_convergence.py`, `game/api.py` | `build_narration_plan_bundle`, `build_narrative_plan`, `build_planner_convergence_report`, `_gm_planner_convergence_seam_terminal` | Plan construction, bundle reuse, semantic bypass detection, planner emergency exit | `planner_convergence_report`, `narration_seam`, debug trace; tests/audits | Classify planner terminal/emergency output as `fallback_kind=planner_convergence_terminal` at existing terminal builder/caller |
| Prompt and GPT expression | `game/prompt_context.py`, `game/gm.py`, `game/model_routing.py`, `game/api.py` | `build_messages`, `call_gpt`, `resolve_model_route`, `_bounded_call_gpt` | Prompt projection, selected model route, model error versus candidate output, retry budget | Model-route metadata, API error metadata, latency, retry tags/debug; fast-fallback provenance | Emit GPT outcome event at `_bounded_call_gpt` result classification and upstream-error fallback selector |
| Retry / expression fallback | `game/gm_retry.py`, `game/social_exchange_emission.py`, `game/api.py` | `force_terminal_retry_fallback`, `apply_social_exchange_retry_fallback_gm`, `_fast_fallback_for_upstream_error`, `_repair_terminal_player_facing_if_needed` | Retry selection/exhaustion, deterministic terminal line, social/nonsocial empty-output rescue, provider-failure fallback | Tags, `accepted_via`, fallback families, provenance fingerprints, debug notes, stage-diff retry flags | Emit one fallback decision event at each selector before later gate mutation; retain selected family/source |
| Gate / legality enforcement | `game/final_emission_gate.py`, `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/speaker_contract_enforcement.py`, `game/interaction_continuity.py`, `game/acceptance_quality.py` | `apply_final_emission_gate`, `_enforce_response_type_contract`, policy `_apply_*_layer` functions, `enforce_emitted_speaker_with_contract`, `repair_interaction_continuity`, `_apply_visibility_enforcement` | Accept, bounded repair, deterministic replacement, strict-social route, speaker rewrite, visibility/referrer enforcement, acceptance floor | FEM, `final_emitted_source`, repair flags/modes, `post_gate_mutation_detected`, speaker payload, stage snapshots/transitions | Primary gate-path and mutation-kind event insertion point: summarize already-computed layer results when FEM is finalized |
| Sanitizer / final shaping | `game/output_sanitizer.py`, `game/final_emission_gate.py`, `game/final_emission_meta.py` | `sanitize_player_facing_output`, `_mark_sanitizer_empty_fallback`, `_mark_sanitizer_strict_social_fallback`, `_finalize_emission_output`, `refresh_final_emission_mutation_lineage` | Strip-only cleanup, serialized payload recovery, empty-output fallback, strict-social sanitizer ownership, final packaging | `sanitizer_debug`, `sanitizer_trace`, final emission mutation lineage tokens, FEM observability | Project sanitizer events to the same lineage event vocabulary; record post-gate mutation kind without altering output |
| Post-emission state adoption | `game/api.py`, `game/post_emission_speaker_adoption.py`, `game/state_authority.py` | `_apply_post_gm_updates`, `_post_gm_adoption_gateway`, `apply_post_emission_speaker_adoption`, `apply_stale_interlocutor_invalidation_after_emission`, `_record_post_gm_mutation_trace` | Whether emitted text changes interaction/world/session state; stale speaker anchor clearing | State mutation traces in debug/session, gateway classifications | Classify post-emission adoption and speaker-anchor invalidation as state/projection mutation events |
| Evaluator / scoring | `game/scenario_spine_eval.py`, `game/playability_eval.py`, `game/narrative_authenticity_eval.py`, `game/behavioral_evaluators/*.py` | `evaluate_scenario_spine_session`, `_compute_degradation_over_time`, `evaluate_scenario_spine_branch_divergence`, playability/behavioral evaluators | Offline scoring, warnings, degradation and branch divergence; not live gate behavior | Session-health summaries, evaluation artifacts, canonical evaluator events | Consume lineage frequencies only as report evidence initially; do not let counts affect scoring in first implementation |
| Replay / scenario-spine execution | `tools/run_scenario_spine_validation.py`, `game/scenario_spine.py`, `tests/helpers/golden_replay.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py` | `run_scenario_spine_branch`, `build_aggregate_session_health_summary`, `run_golden_replay`, `_observed_turn`, classifier/report renderers | Transcript collection, artifact projection, failure classification and operator report generation | Per-turn meta includes FEM and scenario identity; aggregate artifacts and failure dashboard exist | Best existing home for lineage frequency and recurrence summaries across turns/branches/replays |

## Existing Instrumentation Inventory

| Artifact/File | Measures | Runtime/Test-Derived | Stable to Extend? | Notes |
|---|---|---|---|---|
| `game/final_emission_meta.py` / `_final_emission_meta` | Final route/source, response-type repairs, layer flags, dead-turn, fallback ownership fields, mutation lineage | Runtime-derived | Yes, with additive/read-side extension | Canonical final-emission metadata surface; must not become policy input |
| `game/final_emission_meta.py::build_final_emission_mutation_lineage` | Known mutation tokens including pre-gate sanitizer, response-type/prepared selection, opening/fallback behavior, sealed replacement, sanitizer empty fallback, finalize packaging | Runtime-derived from stamped fields | Yes, but deliberately incomplete | Good seed for mutation kind frequency; not enough for every layer or speaker repair |
| `game/final_emission_meta.py::build_fem_observability_events` and `assemble_unified_observational_telemetry_bundle` | Normalized canonical event projections for FEM/stage/evaluator observations | Runtime data, read-side projection | Yes | Closest existing shape for Cycle H event projection |
| `game/telemetry_vocab.py` | Canonical `phase`, `owner`, `action`, `reasons`, `scope`, `data` envelope | Runtime/read-side vocabulary | Yes | Does not currently carry lineage identity/kind fields; additive nested `data` is low risk |
| `game/stage_diff_telemetry.py` | Bounded snapshots/transitions; route/fallback/repair/retry change flags; text fingerprint | Runtime-derived | Yes | Detects change between stages but not full sublayer attribution; bounded to 12 items |
| `game/fallback_provenance_debug.py` | Fast-fallback selection and gate entry/exit fingerprints; overwrite hint | Runtime-derived debug | Partially | File calls itself temporary; reuse evidence but avoid making it sole long-term schema owner |
| `game/output_sanitizer.py` / `sanitizer_trace` | Sanitizer mode, changed/dropped counts, empty fallback and strict-social sanitizer fallback ownership | Runtime-derived | Yes | Already provides strong post-gate lineage for its owned paths |
| `game/speaker_contract_enforcement.py` | Speaker verdict, reason and repair mode, canonical speaker, repair payload | Runtime-derived | Yes | Repair payload is already countable but not normalized into scenario summaries |
| `game/interaction_continuity.py` | Continuity violations/warnings and repair types such as strip, bridge, narration-to-dialogue | Runtime-derived | Yes | Distinct from speaker contract; should remain separate repair kinds |
| `game/api.py` debug trace and `game/state_authority.py` trace builders | Route evidence, state mutation operations, post-GM adoption gateway decisions | Runtime-derived | Yes | Already persisted in session/debug lane; candidate source for state mutation frequency |
| `tests/helpers/golden_replay.py` | Observation projection, drift buckets/hashes, unavailable raw fields | Test/replay-derived from runtime payloads | Yes for replay only | Not a live instrumentation owner; useful optional secondary consumer |
| `tests/helpers/failure_classifier.py` and `failure_dashboard_report.py` | Classifies projected failures and renders compact triage dashboard | Test/replay-derived | Yes for diagnostic reporting, not runtime collection | Already maps some lineage tokens to mutation sources; currently failure-only rather than frequency-based |
| `audits/runtime_signal_inventory.md` | Existing runtime signal catalogue and dashboard-readiness finding | Static recon artifact | Reference only | Confirms late mutation owner attribution is the known gap |
| `audits/mutation_boundary_inventory.md` | Risk-ranked mutation boundary catalogue | Static recon artifact | Reference only | Useful taxonomy for Cycle H mutation kinds |
| `tools/run_scenario_spine_validation.py` artifacts | Transcript, per-branch session health, run debug, aggregate summaries | Runtime executions plus offline evaluation | Yes | Strongest existing destination for recurrence due to stable scenario/branch/turn identity |
| `game/scenario_spine_eval.py` | Metadata completeness, degradation windows, repeated filler/opening checks, branch divergence | Offline evaluation of runtime transcripts | Yes, as consumer/reporting lane | Tracks narrative recurrence patterns, not runtime lineage recurrence today |
| `data/session.json` / `data/session_log.jsonl` | Persisted debug traces and state mutation evidence during normal sessions | Runtime-derived, tracked working snapshots | No as primary report sink | Contains evidence but has known tracked-file churn risk documented in Cycle G |

## Fallback Frequency Map

| Fallback Path | File/Function | Trigger | Existing Classification | Existing Visibility | Recommended Counter/Event |
|---|---|---|---|---|---|
| Planner convergence terminal | `game/api.py::_gm_planner_convergence_seam_terminal` | CTIR/plan bundle or planner convergence report fails | Narration seam/planner emergency metadata | Debug trace and narration seam; tests | `fallback_selected{stage=planner,fallback_kind=planner_convergence_terminal,owner=game.api}` |
| Upstream provider/budget fast fallback | `game/api.py::_fast_fallback_for_upstream_error`; `game/gm_retry.py::force_terminal_retry_fallback` | `call_gpt` upstream error, budget/provider failure, terminal retry | `GPT_BUDGET_OR_PROVIDER_FAILURE`, tags `fast_fallback`/`upstream_api_fast_fallback` | Strong provenance plus tags/FEM/stage-diff | Event at `_fast_fallback_for_upstream_error` before gate; keep failure class |
| Targeted retry terminal fallback | `game/gm_retry.py::force_terminal_retry_fallback` | Retry failures exhausted or terminal selection chosen | Retry/forced fallback tags/families | Tags, `accepted_via`, retry flags, tests | `fallback_selected{stage=gpt_retry,fallback_kind=retry_terminal,reason_codes}` |
| Empty terminal social/nonsocial repair fallback | `game/api.py::_repair_terminal_player_facing_if_needed` | Candidate has no usable player-facing text after generation/fallback | Debug-note reason; social or nonsocial repair family depends downstream | Printed marker/debug and resulting fields, but weak central classification | Emit explicit `empty_output_social_rescue` / `empty_output_nonsocial_rescue` selector event |
| Social retry fallback | `game/social_exchange_emission.py::apply_social_exchange_retry_fallback_gm` | Social unresolved-question retry/fallback path selected | `question_retry_fallback`, `social_exchange_retry_fallback`, `social_exchange_fallback:<kind>` | Tags/debug and tests | Count at replacement creation with `fallback_kind` returned by deterministic selector |
| Strict-social deterministic or minimal emergency fallback | `game/social_exchange_emission.py::finalize_strict_social_exchange_emission` and helpers | Candidate rejected, route-illegal, grounding denied, or deterministic candidate fails | `STRICT_SOCIAL_DETERMINISTIC_FALLBACK`; `deterministic_social_fallback` / `minimal_social_emergency_fallback` | Details flow into FEM and owner tests | Emit selection event from details (`used_internal_fallback`, `fallback_kind`, `final_emitted_source`) before gate stores FEM |
| Opening deterministic prepared fallback | `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload`; `game/final_emission_gate.py::_opening_scene_safe_fallback_tuple` | Opening candidate invalid and usable curated facts/prepared snapshot exists | `fallback_family_used=scene_opening`, authorship and owner bucket | High: FEM, golden replay, classifier/dashboard | Count on gate selection, with authorship source and owner bucket |
| Opening fail-closed sealed fallback | `game/final_emission_gate.py::_opening_fail_closed_meta_*` | Missing/malformed upstream opening payload or insufficient curated facts | Failed-closed repair/source fields; sealed-gate owner bucket | High in tests/replay projection | Count as separate fallback kind `opening_failed_closed` |
| Response-type upstream-prepared answer/action replacement | `game/upstream_response_repairs.py::build_upstream_prepared_emission_payload`; `game/final_emission_gate.py::_enforce_response_type_contract` | Candidate violates required answer/action shape and prepared text is valid | `upstream_prepared_emission`, repair kind/source | FEM and golden replay fields | Treat as `fallback_selected` plus `mutation_kind=prepared_emission_selection` |
| Visibility / first-mention / referential hard replacement | `game/final_emission_gate.py::_standard_visibility_safe_fallback`, `_apply_first_mention_enforcement`, `_apply_referential_clarity_enforcement`, `_apply_visibility_enforcement` | Visibility or referent legality cannot be locally repaired | Visibility fallback pool/kind/owner fields; possibly sealed fallback | High fields, broad tests; branching dense | Emit once after visibility enforcement resolves replacement with violation kind and selected owner |
| Scene-integrity/global sealed replacement | `game/final_emission_gate.py::_scene_emit_integrity_global_fallback_tuple` and replacement route | Scene/route integrity failure cannot accept candidate | Sealed/global final source and owner bucket | FEM, golden replay, dashboard | `fallback_selected{stage=gate,fallback_kind=global_scene_or_sealed}` |
| Fast-fallback neutral composition | `game/final_emission_gate.py::_apply_fast_fallback_neutral_composition_layer` | Fast/retry fallback text requires bounded neutral composition | Repair mode and provenance realignment | FEM layer flag and stage/provenance | Count as `mutation` of an existing fallback, not a second selection |
| Sanitizer empty-output fallback | `game/output_sanitizer.py::_mark_sanitizer_empty_fallback` | Strip-only sanitization leaves empty output and prepared empty fallback is selected | Sanitizer empty owner/source, lineage token | Strong runtime/replay fields | Emit `fallback_selected{stage=sanitizer,fallback_kind=empty_output}` from existing trace |
| Sanitizer strict-social fallback | `game/output_sanitizer.py::_mark_sanitizer_strict_social_fallback` | Sanitizer needs strict-social rescue | Explicit selection owner and prose owner split | Strong runtime/replay fields | Emit with both `owner=output_sanitizer` and `prose_owner=strict_social_emission` |
| Legacy sanitizer diegetic fallbacks | `game/output_sanitizer.py::_diegetic_uncertainty_fallback`, `_simple_diegetic_fallback` | Legacy sentence-rewrite diagnostic mode hits procedural/internal text | Source-mode pools; not normal strip-only lane | Debug events; legacy/test-oriented | Keep optional and explicitly label `legacy_sentence_rewrite` |

## Speaker Repair Frequency Map

| Repair Path | File/Function | Trigger | Mutation/Repair Performed | Existing Visibility | Recommended Counter/Event |
|---|---|---|---|---|---|
| Wrong explicit speaker local rebind | `game/speaker_contract_enforcement.py::_apply_speaker_contract_repairs` | Continuity locked; explicit wrong label; quoted text salvageable | Replaces opening label with canonical name and may update effective `resolution.social` | Enforcement payload with `initial_repair_mode=local_rebind`; tests cover equivalence | `speaker_repair{repair_kind=local_rebind,reason=speaker_binding_mismatch}` |
| Canonical speaker rewrite | Same function | Generic forbidden speaker, unjustified switch, or mismatch not locally salvageable with a canonical speaker | Replaces line with `strict_social_ownership_terminal_fallback`; syncs canonical speaker fields | Enforcement payload/FEM reason | `speaker_repair{repair_kind=canonical_rewrite}` and `mutation_kind=final_emission_mutation` |
| Narrator-neutral bridge | Same function | Dialogue ownership exists with no allowed speaker, or no canonical rewrite target | Replaces output with neutral bridge and clears NPC identity fields | Enforcement payload; post-emission reader checks narrator-neutral reason | `speaker_repair{repair_kind=narrator_neutral}` |
| Continuity malformed-attribution repair | `game/interaction_continuity.py::repair_interaction_continuity` | Malformed attribution under active continuity | Reorders existing fragments around canonical attribution | `repair_type=repair_malformed_speaker_attribution` in continuity payload | `speaker_repair{repair_kind=continuity_malformed_attribution}` |
| Uncued interruption strip | Same function | Multi-speaker interruption/switch without cue | Removes secondary speaker material when meaning survives | `repair_type=strip_uncued_interruption` | `speaker_repair{repair_kind=continuity_strip_uncued_interruption}` |
| Explicit bridge insertion | Same function | Uncued interruption but stripping would destroy meaning | Prepends bridge cue around retained primary quote | `repair_type=insert_explicit_bridge` | `speaker_repair{repair_kind=continuity_insert_bridge}` |
| Narration-to-dialogue wrap | Same function | Strong continuity requires dialogue but short answer-like narration lacks dialogue | Wraps short line as canonical attributed speech | `repair_type=narration_to_dialogue` | `speaker_repair{repair_kind=continuity_wrap_dialogue}` |
| Strict-social grounding neutral bridge | `game/social_exchange_emission.py::finalize_strict_social_exchange_emission` | Social grounding indicates neutral bridge | Emits neutral grounding bridge as internal fallback | Details include `fallback_kind=neutral_speaker_grounding_bridge` | Count as both fallback and speaker repair with shared recurrence key |
| Post-emission speaker adoption | `game/post_emission_speaker_adoption.py::apply_post_emission_speaker_adoption` | Visible grounded takeover with directed dialogue | Mutates active interaction target/current interlocutor after emission | Adoption debug/state mutation trace | `mutation{mutation_kind=state_speaker_adoption}`, not a repair unless correcting stale state |
| Stale interlocutor invalidation | `game/post_emission_speaker_adoption.py::apply_stale_interlocutor_invalidation_after_emission` | Different grounded emitted speaker contradicts stored interlocutor and adoption did not apply | Clears stale anchor for later turns | Debug output/state mutation surface | `speaker_repair{repair_kind=stale_interlocutor_invalidation,stage=post_emission}` |

All listed speaker repair paths can be counted without changing emitted behavior: their decision payloads or already-returned repair types can be projected after computation. The uncertainty is whether every call path currently persists each payload into the same debug/FEM envelope; that should be contract-tested before relying on aggregate counts.

## Mutation-Kind Frequency Map

| Mutation Path | File/Function | Mutation Kind | Object Mutated | Pre/Post Gate | Existing Visibility | Recommended Counter/Event |
|---|---|---|---|---|---|---|
| Authoritative resolution/state write | `game/api.py::_apply_authoritative_resolution_state_mutation` | `state_mutation` | Session/scene/world/combat state | Pre-gate | State mutation trace in debug/session | Project `state_mutation` event from existing trace operation |
| Route / interaction establishment | `game/api.py`, `game/interaction_context.py` | `state_mutation` / `route_mutation` | Active target and social context | Pre-gate | Turn trace and state mutation trace | Count route choice and continuity break separately |
| CTIR and plan bundle attachment | `game/ctir_runtime.py`, `game/narration_plan_bundle.py` | `metadata_only_mutation` | Session runtime attached meaning/plan | Pre-gate | CTIR/plan stamp metadata | Optional metadata event only; exclude from behavior mutation frequency by default |
| Upstream prepared emission merge | `game/upstream_response_repairs.py::merge_upstream_prepared_emission_into_gm_output` | `fallback_mutation` / `metadata_only_mutation` until selected | Candidate metadata payload | Pre-gate | Family/source data | Record preparation separately from later selection |
| Spoken refinement cash-out | `game/upstream_response_repairs.py::apply_spoken_state_refinement_cash_out` | `planner_or_upstream_text_mutation` | Candidate output text | Pre-gate | Limited dedicated frequency signal | Add mutation projection at caller result comparison |
| Response-type replacement | `game/final_emission_gate.py::_enforce_response_type_contract` | `gate_mutation` / `fallback_mutation` | Player-facing text and FEM | Gate | Repair kind/source, lineage token | Emit when `response_type_repair_used` |
| Answer/exposition, response delta, social structure, narrative authenticity | `game/final_emission_repairs.py::_apply_*_layer` | `gate_mutation` / `repair_only_mutation` | Player-facing text and FEM flags | Gate | Layer-specific repair booleans/modes; stage tail flags | Project one mutation event per `*_repaired=True` |
| Tone, narrative authority, anti-railroading, context separation, purity, answer shape, scene anchor | `game/final_emission_gate.py::_apply_*_layer` | `gate_mutation` / `repair_only_mutation` | Player-facing text and FEM flags | Gate | Layer-specific booleans/modes | Project additive events from finalized FEM |
| Speaker enforcement | `game/speaker_contract_enforcement.py::_apply_speaker_contract_repairs` via gate | `repair_only_mutation` / `gate_mutation` | Text plus effective resolution social fields | Gate | Enforcement payload; FEM reason only partly summarized | Add explicit repair-kind projection into lineage events |
| Interaction continuity repair | `game/interaction_continuity.py::repair_interaction_continuity` via gate | `repair_only_mutation` / `gate_mutation` | Text | Gate | Validation/repair payload merged by gate | Add continuity repair type to events |
| Visibility / first mention / referential enforcement | `game/final_emission_gate.py` enforcement functions | `gate_mutation` / `fallback_mutation` | Text plus visibility/ref metadata | Gate | Rich flags, owner buckets and tests | Project replacement/local-repair kind from existing metadata |
| Acceptance-quality N4 floor | `game/acceptance_quality.py` invoked by gate | `gate_mutation` / `repair_only_mutation` | Emitted text and FEM | Gate | N4 merge fields and tests/docs | Project accepted/repaired/sealed outcome |
| Sanitizer strip/recovery/fallback | `game/output_sanitizer.py::sanitize_player_facing_output` | `final_emission_mutation` | Final text and sanitizer trace | Post-gate/finalize | Changed/dropped counts, mode, lineage/fallback fields | Convert each sanitizer owned action into lineage summary |
| Finalize stripping/packaging | `game/final_emission_gate.py::_finalize_emission_output`; `game/final_emission_meta.py::build_final_emission_mutation_lineage` | `final_emission_mutation` | Final text/FEM packaging | Post-gate | Existing lineage tokens | Preserve current tokens and include their counts |
| Post-GM adoption gateway | `game/api.py::_post_gm_adoption_gateway`, `_record_post_gm_mutation_trace` | `state_mutation` | Scene/session/world/interaction state | Post-emission | Debug state mutation rows | Aggregate by gateway operation/decision |
| Test fixtures / runtime snapshots | `tests/*`, `data/session.json`, `data/session_log.jsonl` | `test_fixture_mutation` / persisted runtime snapshot churn | Test/runtime persisted files | Outside live gate | Cycle G audit and observed files | Exclude from runtime lineage counts; track as validation hygiene only |

Intended ownership is explicit for almost all paths above. The implicit area is not whether mutation happens, but which exact gate layer last authored a changed final string when multiple repairs or finalize steps run on one turn.

## Gate Path Frequency Map

| Gate Path | File/Function | Outcome | Trigger | Existing Visibility | Recommended Counter/Event |
|---|---|---|---|---|---|
| Candidate accepted unchanged | `game/final_emission_gate.py::apply_final_emission_gate` | `accept_candidate_unchanged` | Candidate validates and no downstream text mutation occurs | `final_route=accept_candidate`, `post_gate_mutation_detected=False` | `gate_outcome{gate_path=accept_unchanged}` |
| Candidate accepted after bounded repair | Same function and `_apply_*_layer` calls | `accept_candidate_repaired` | Candidate remains route-valid after one or more deterministic repairs | Repair flags/modes and `post_gate_mutation_detected=True` | Emit gate outcome plus separate mutation events |
| Response-type prepared selection | `_enforce_response_type_contract` | `prepared_response_type_repair` | Required response shape fails and prepared upstream replacement is valid | `response_type_repair_used/kind` and source fields | `gate_outcome{gate_path=prepared_repair}` |
| Strict-social accepted route | `apply_final_emission_gate`; `social_exchange_emission` | `strict_social_accept` | Strict-social candidate or resolved grounded answer passes | Details and FEM `strict_social_active`, final source | `gate_outcome{gate_path=strict_social_accept}` |
| Strict-social deterministic replacement | Same files | `strict_social_fallback` | Strict-social candidate rejected/illegal; deterministic line passes | Attempt/pass flags, source/fallback kind | `gate_outcome{gate_path=strict_social_fallback}` |
| Strict-social minimal emergency | Same files | `strict_social_emergency` | Deterministic social fallback fails or route-illegal text intercepted | Minimal emergency source/kind | `gate_outcome{gate_path=strict_social_emergency}` |
| Speaker contract repaired | `enforce_emitted_speaker_with_contract` | `speaker_repaired` | Speaker validation fails and repair mode applies | Enforcement payload and reason; tests | Gate event with `repair_kind` |
| Interaction continuity repaired | `_apply_interaction_continuity_emission_step` | `continuity_repaired` | Continuity validation fails and minimal repair succeeds | Validation/repair payload | Gate event with continuity repair type |
| Opening deterministic fallback accepted | `_opening_scene_safe_fallback_tuple` and response-type path | `opening_fallback` | Invalid opening replaced from prepared or deterministic fallback | Opening fields/owner bucket | Gate event with owner bucket |
| Opening failed closed | Opening fail-closed helpers | `opening_failed_closed` | Cannot safely obtain usable opening fallback | Failed-closed source/kind | Gate event with failed-closed reason |
| Visibility/referent local correction | Visibility/referential enforcement functions | `visibility_local_repair` | Safe local correction succeeds | Metadata varies by path; tests cover | Normalize local correction reason into gate event |
| Visibility/global replacement | Visibility/scene-integrity functions | `visibility_or_scene_replaced` | Legality cannot be locally repaired | Replacement/applied fields; pools/buckets | Gate event with violation and selected pool |
| Acceptance floor repaired/replaced | `_apply_acceptance_quality_n4_floor_seam` | `acceptance_quality_repair_or_sealed` | N4 floor fails candidate | N4 results in FEM | Gate event keyed by N4 outcome |
| Fast fallback contained/realigned | `_apply_upstream_fallback_pregate_containment`, `_finalize_upstream_fallback_overwrite_containment` | `fast_fallback_contained` | Upstream fallback would be overwritten or repaired | Provenance fingerprints/hints | Event with containment stage |
| Sanitizer strip-only cleanup | `game/output_sanitizer.py` | `sanitized` | Final shaping removes prohibited fragments | Trace counts/debug | Post-gate path event, not legality reclassification |
| Sanitizer empty/strict-social fallback | Same file | `sanitizer_fallback` | Sanitization empties output / social rescue needed | Explicit fields/lineage | Post-gate path event with owner split |

Tests directly assert many gate outcomes in `tests/test_final_emission_gate.py`, `tests/test_final_emission_repairs.py`, `tests/test_final_emission_visibility.py`, `tests/test_speaker_contract_enforcement.py`, `tests/test_interaction_continuity_speaker_bridge.py`, `tests/test_output_sanitizer.py`, and replay/classifier/dashboard suites. Runtime/replay output records most path evidence as scattered fields, but not as one stable `gate_path` enumeration.

## Recurrence Tracking Map

| Signal | Current Tracking | Granularity | Can Correlate Across Turns? | Gap | Recommendation |
|---|---|---|---|---|---|
| Fallback kinds | FEM/fallback fields per turn; golden replay projection; scenario rows carry FEM | Per turn/replay row | Technically yes in scenario artifacts, not currently aggregated | No frequency/recurrence summary and inconsistent family surfaces | Aggregate normalized fallback events per branch and run |
| Speaker repairs | Speaker enforcement payload and continuity repair payload on individual turns | Per turn when payload persisted | Partially; scenario turn rows can carry FEM/debug but no counter | No canonical repair-kind projection; post-emission invalidation separate | Emit `repair_kind` events and summarize by recurrence key |
| Mutation kinds | State mutation traces, FEM lineage tokens, stage transitions, sanitizer trace | Per operation or per turn | Partially | Different taxonomies and incomplete attribution of gate sublayers | Introduce a bounded `mutation_kind` mapping over existing fields |
| Gate paths | Final route/source and repair flags | Per final emission | Partially | No enumerated `gate_path`; many flags must be interpreted jointly | Add read-side gate outcome classifier and aggregate it |
| Opening repeated phrasing | `scenario_spine_opening_convergence.py` repeated generic first line | Per scenario-spine branch | Yes | Covers style recurrence only, not lineage cause | Retain and associate with fallback/gate recurrence summaries |
| Progressive degradation/filler | `game/scenario_spine_eval.py::_compute_degradation_over_time` | Per branch windows/session | Yes | Heuristic text health, no runtime cause linkage | Report lineage frequency adjacent to degradation, initially without affecting score |
| Session cohesion callbacks | `game/behavioral_evaluators/session_cohesion.py` | Turn history evaluation | Yes when invoked | Concerned with content/cohesion, not fallback/repair lineage | Leave evaluator separate; optionally display lineage alongside it |
| Golden replay failures | Failure classifier/dashboard | Failed replay observations only | Within report corpus, not live session recurrence | Successful-but-frequent fallback/repair is invisible | Secondary aggregate report over all observed rows, not only failures |
| Persisted session traces | `data/session.json` / `data/session_log.jsonl` | Runtime session | Potentially yes | Files churn during tests and are not stable report artifacts | Do not use as primary Cycle H destination |
| Global/runtime fleet frequency | None discovered | None | No | No durable central aggregation or session/replay id vocabulary | Defer until artifact-based per-run lineage proves useful |

At present, fallback/repair/mutation/gate signals can be correlated across scenario-spine turns only by writing a new read-side aggregation over recorded per-turn metadata. No reliable global recurrence tracking was found.

## Recommended Instrumentation Shape

Use an additive, observational event list assembled from existing runtime fields. The smallest viable structure can live as a normalized projection and be attached to scenario-spine transcript metadata or derived while writing its report artifacts:

```json
{
  "event_type": "runtime_lineage",
  "event_kind": "fallback_selected | speaker_repair | mutation | gate_outcome",
  "stage": "engine | planner | gpt | retry | gate | sanitizer | post_emission",
  "owner": "game.final_emission_gate",
  "source": "game.final_emission_gate.apply_final_emission_gate",
  "turn_id": "turn identifier when available",
  "scenario_id": "scenario spine id when available",
  "branch_id": "branch id when available",
  "replay_id": "replay id when available",
  "gate_path": "accept_unchanged | accept_repaired | strict_social_fallback | replaced | sanitizer_fallback",
  "mutation_kind": "state_mutation | planner_mutation | fallback_mutation | gate_mutation | final_emission_mutation | metadata_only_mutation | repair_only_mutation",
  "fallback_kind": "existing normalized fallback kind or null",
  "repair_kind": "existing normalized repair mode/type or null",
  "recurrence_key": "event_kind:stage:owner:kind",
  "before_hash": "existing bounded text fingerprint when already available",
  "after_hash": "existing bounded text fingerprint when already available",
  "notes": ["bounded existing reason codes only"]
}
```

Design constraints:

- Prefer projection from FEM, `stage_diff_telemetry`, sanitizer trace, speaker/continuity payloads, and state mutation traces rather than new branching in the hot path.
- Reuse existing fingerprints from stage diff/fallback provenance; do not persist full before/after text merely for instrumentation.
- Preserve `game/telemetry_vocab.py` as the base observational vocabulary. Cycle H-specific fields can initially be kept inside event `data` or in a sibling bounded lineage envelope rather than widening every existing event contract.
- Treat preparation and selection separately. Preparing an upstream fallback payload is not a fallback occurrence until it is selected.
- Keep `owner` as decision owner and allow optional `prose_owner` in data for split paths such as sanitizer strict-social fallback.
- Compute recurrence only in report/artifact consumers at first. Do not use recurrence to steer retries, repairs, or evaluator scores.

### Recommended Report Destination

Primary destination: add a separate lineage summary artifact under the existing scenario-spine run tree, adjacent to `session_health_summary.json` and included in aggregate scenario-spine reporting. This lane already records stable `scenario_spine` identity, turn indices, copied FEM, run-debug data, and multi-turn/branch aggregation. A natural eventual artifact name is `runtime_lineage_summary.json`, with a compact block in `compact_operator_summary.md` / `aggregate_operator_summary.md`.

Optional secondary destination: extend golden replay/failure dashboard output with read-only frequency/recurrence sections over observed rows. This is valuable for regression triage, but it should remain secondary because it is test-derived and presently emphasizes failures rather than healthy runtime frequency.

Do not use tracked `data/session.json` or `data/session_log.jsonl` as the primary destination: they expose runtime evidence but have documented test-driven snapshot churn and are not designed as stable recon/report artifacts.

## Proposed Implementation Blocks

| Block | Goal | Files Likely Touched | Tests Likely Touched | Risk Level | Validation Command |
|---|---|---|---|---|---|
| H1: Lineage projection vocabulary | Define read-side lineage event normalization and recurrence-key rules from existing FEM/stage/sanitizer/speaker fields, without changing selection or text | `game/telemetry_vocab.py`, `game/final_emission_meta.py`, possibly new leaf module `game/runtime_lineage_telemetry.py` | `tests/test_final_emission_meta.py`, `tests/test_stage_diff_telemetry.py` | Low | `python -m pytest tests/test_final_emission_meta.py tests/test_stage_diff_telemetry.py -q` |
| H2: Fallback and gate outcome projection | Map existing final source, route, owner buckets, response-type fields, strict-social details, and sanitizer fallback fields into `fallback_selected` and `gate_outcome` events | `game/final_emission_meta.py`, read-only helper module if created | `tests/test_final_emission_gate.py`, `tests/test_final_emission_visibility.py`, `tests/test_output_sanitizer.py`, `tests/test_golden_replay.py` | Medium-low | `python -m pytest tests/test_final_emission_gate.py tests/test_final_emission_visibility.py tests/test_output_sanitizer.py tests/test_golden_replay.py -q` |
| H3: Speaker and mutation-kind projection | Normalize speaker enforcement/continuity repair modes and existing lineage/state mutation traces into countable event kinds | `game/speaker_contract_enforcement.py` only if payload persistence gaps are proven; preferably projection module plus `game/final_emission_meta.py`/`game/api.py` read surfaces | `tests/test_speaker_contract_enforcement.py`, `tests/test_interaction_continuity_speaker_bridge.py`, `tests/test_turn_packet_stage_diff_integration.py` | Medium | `python -m pytest tests/test_speaker_contract_enforcement.py tests/test_interaction_continuity_speaker_bridge.py tests/test_turn_packet_stage_diff_integration.py -q` |
| H4: Scenario-spine lineage summary | Derive per-branch and aggregate frequencies/recurrences from recorded turn metadata; write separate artifact and operator summary block | `tools/run_scenario_spine_validation.py`, possibly `game/scenario_spine_eval.py` only for non-scoring report attachment | `tests/test_run_scenario_spine_validation.py`, `tests/test_scenario_spine_eval.py`, `tests/test_scenario_spine_contracts.py` | Low-medium | `python -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py -q` |
| H5: Replay/dashboard secondary projection | Surface lineage frequency and recurring failure evidence in read-only golden replay/dashboard reporting after H1-H4 schema settles | `tests/helpers/golden_replay.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py` | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py` | Medium | `python -m pytest tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q` |

## Files to Pass Back to GPT

Ranked for implementation planning:

1. `game/final_emission_meta.py` - canonical FEM, normalized observability, mutation lineage, and the likely projection anchor.
2. `game/final_emission_gate.py` - final route ordering, repair/replacement decisions, fallback selection, and gate outcome evidence.
3. `game/stage_diff_telemetry.py` - bounded before/after fingerprints, transitions, and existing observational-event projection.
4. `game/telemetry_vocab.py` - existing canonical event envelope and vocabulary boundary.
5. `tools/run_scenario_spine_validation.py` - primary recommended artifact/report destination and aggregate runner.
6. `game/scenario_spine_eval.py` - current cross-turn/degradation/metadata aggregation behavior and non-scoring boundary.
7. `game/speaker_contract_enforcement.py` - explicit speaker repair decision modes and output payload.
8. `game/interaction_continuity.py` - separate continuity repair types that must not be collapsed into speaker binding.
9. `game/output_sanitizer.py` - sanitizer lineage and post-gate fallback owner split.
10. `game/api.py` - engine/GPT/retry orchestration, state mutation traces, and upstream fast fallback selection.
11. `game/gm_retry.py` and `game/social_exchange_emission.py` - retry/strict-social fallback families and emitted selection details.
12. `game/upstream_response_repairs.py` and `game/opening_deterministic_fallback.py` - upstream-prepared and opening fallback ownership.
13. `tests/helpers/golden_replay.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py` - existing secondary projection/classification/report contracts.
14. `audits/runtime_signal_inventory.md` and `audits/mutation_boundary_inventory.md` - prior confirmed inventory/taxonomy context.

## Uncertainties And Blind Spots

- The code search proves that repair and fallback payload fields exist; it does not prove every production/API response mode preserves all debug lanes to every artifact consumer.
- Speaker enforcement explicitly mutates effective resolution speaker fields during some gate repairs. A Cycle H implementation must decide whether that is counted once as speaker repair, once as state mutation, or as two linked events; double counting should be intentional.
- `fallback_provenance_debug.py` is marked temporary. Its fingerprints are useful evidence, but a permanent Cycle H contract should not depend exclusively on that module.
- Legacy sanitizer sentence-rewrite fallbacks exist but default runtime mode is documented as strip-only. They should be reported separately from normal production occurrence counts.
- Scenario-spine recurrence is feasible from existing row identity and FEM copies; global recurrence across ordinary user sessions or multiple runs was not found.

## Validation Notes

Commands discovered as documented safe deterministic checks:

```powershell
python -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py
python -m pytest tests/test_playability_eval.py tests/test_behavioral_gauntlet_smoke.py
py -3 -m pytest tests/test_validation_coverage_registry.py -q
```

The scenario-spine runner itself can exercise the configured model/backend and is not implied by its deterministic pytest wiring tests; it should not be run as part of this read-only recon without explicitly wanting a live/integration execution.

Commands run for this recon, using the repository's documented bundled-runtime pattern because `python` has previously not been available on this PowerShell `PATH`:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_final_emission_meta.py tests\test_stage_diff_telemetry.py tests\test_speaker_contract_enforcement.py tests\test_interaction_continuity_speaker_bridge.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_h_lineage
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_scenario_spine_contracts.py tests\test_scenario_spine_eval.py tests\test_run_scenario_spine_validation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_h_spine
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py tests\test_failure_classifier.py tests\test_failure_dashboard_controlled_failures.py tests\test_failure_classification_contract.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_h_replay
git diff --stat
git status --short --branch
```

Results:

- All three pytest slices passed.
- The scenario-spine runner itself was not executed, because the docs state that the integration path may call the configured model/backend.
- After validation, `git status --short --branch` reported only this new recon report; no tracked runtime snapshot files were changed.
