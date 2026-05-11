# Runtime Signal Inventory

Goal: determine whether the future dashboard can classify failures without major new instrumentation.

| Signal | Source File | Signal Name | Emitted When | Reliability | Stable Enough? |
|---|---|---|---|---|---|
| Golden drift bucket | `tests/helpers/golden_replay.py` | `exact_drift`, `structural_drift`, `semantic_drift` | Replay expectation/classifier runs. | High | yes |
| Golden observed text hash | `tests/helpers/golden_replay.py` | `observed_text_hash`, `expected_text_hash` | Replay classification. | High | yes |
| Replay unavailable fields | `tests/helpers/golden_replay.py` | `unavailable` | Observation projection cannot find route/FEM/trace field. | High for absence; medium for owner. | yes |
| Assertion field path | `tests/helpers/golden_replay.py` | `field_path`, expected/actual/reason | Assertion/classifier failure. | High | yes |
| Canonical entry | `game/api.py` | `trace.canonical_entry` | Chat route selection records directed social entry. | Medium-high | yes |
| Canonical entry path/reason/target | `game/api.py` | `canonical_entry_path`, `canonical_entry_reason`, `canonical_entry_target_actor_id` | After route prepass. | Medium-high | yes |
| Compact turn trace | `game/api.py` | `turn_trace` | API builds per-turn compact trace. | Medium | yes |
| Social contract trace | `game/api.py`, `game/interaction_context.py` | `turn_trace.social_contract_trace` | Social route/contract present. | Medium; sometimes unavailable. | yes |
| Route selected | `game/interaction_context.py` | `social_turn_contract.route_selected` / trace copy | Social route finalized. | Medium | yes |
| Reply owner | `game/interaction_context.py` | `reply_owner_actor_id`, `final_reply_owner`, `visible_grounded_speaker` | Social contract finalization. | Medium | yes |
| Declared switch metadata | `game/interaction_context.py` | `declared_switch_detected`, `declared_switch_target_actor_id`, `continuity_overridden_by_declared_switch` | Explicit actor switch parsed. | Medium-high | yes |
| Spoken vocative metadata | `game/interaction_context.py` | `spoken_vocative_detected`, `spoken_vocative_target_actor_id`, `continuity_overridden_by_spoken_vocative` | Vocative target parsed. | Medium-high | yes |
| Speaker contract | `game/speaker_contract_enforcement.py` | `speaker_selection_contract` | Contract read from metadata/resolution/trace. | Medium | yes |
| Speaker enforcement reason | `game/speaker_contract_enforcement.py` | `speaker_contract_enforcement_reason`, repair mode fields | Emitted speaker validation/repair. | Medium-high | yes |
| Dialogue social plan validation | `game/dialogue_social_plan.py` | `dialogue_plan_valid`, validation errors | Plan built/attached and validated. | Medium | yes |
| Interaction continuity validation | `game/interaction_continuity.py` | `continuity_strength`, `violations`, `warnings`, `repair_type` | Continuity layer validates/repairs candidate text. | Medium | yes |
| Final emission meta | `game/final_emission_meta.py` | `_final_emission_meta` | Gate/repairs stamp final output. | High | yes |
| Final emitted source | `game/final_emission_gate.py` | `final_emitted_source` | Final emission source resolved. | High | yes |
| Final route | `game/final_emission_meta.py` | `final_route` | Some FEM/read paths expose route/source fallback. | Medium | yes |
| Fallback family | `game/final_emission_gate.py`, `game/diegetic_fallback_narration.py` | `fallback_family_used`, `realization_fallback_family`, `fallback_temporal_frame` | Fallback selection/classification. | High when present | yes |
| Deterministic social fallback flags | `game/final_emission_gate.py` | `deterministic_social_fallback_attempted`, `deterministic_social_fallback_passed` | Strict-social fallback path. | High | yes |
| Post-gate mutation | `game/final_emission_gate.py` | `post_gate_mutation_detected` | Gate compares pre/post normalized text. | High at boolean level; low for exact layer owner. | yes |
| Response-type metadata | `game/final_emission_validators.py`, `game/final_emission_meta.py` | `response_type_required`, `response_type_candidate_ok`, `response_type_repair_used`, `response_type_repair_kind`, rejection reasons | Response type contract enforced. | High | yes |
| Opening fallback telemetry | `game/final_emission_validators.py`, `game/opening_deterministic_fallback.py` | `opening_recovered_via_fallback`, `opening_fallback_authorship_source`, `opening_fallback_context_source`, `opening_fallback_failed_closed` | Opening repair/fallback path. | High | yes |
| Upstream opening attach telemetry | `game/upstream_response_repairs.py` | `opening_upstream_prepare_attach_*` | Upstream opening fallback payload attach attempted/skipped/failed. | Medium-high | yes |
| Fallback provenance fingerprints | `game/fallback_provenance_debug.py` | `stage_diff_gate_stage`, entry/exit fingerprints | Gate entry/exit/fallback realignment. | Medium | yes |
| Stage snapshots | `game/stage_diff_telemetry.py` | `metadata.stage_diff_telemetry.snapshots` | Gate/retry records compare-ready snapshot. | Medium-high | yes |
| Stage transitions | `game/stage_diff_telemetry.py` | `metadata.stage_diff_telemetry.transitions`, `stage_diff_last_transition` | Meaningful stage diff. | Medium-high | yes |
| Stage-diff events | `game/stage_diff_telemetry.py` | `build_stage_diff_observability_events` output | Read-side event projection. | Medium | yes |
| FEM observability events | `game/final_emission_meta.py` | `build_fem_observability_events` output | Read-side normalized FEM projection. | High | yes |
| Unified telemetry bundle | `game/final_emission_meta.py` | `assemble_unified_observational_telemetry_bundle` | Read-side bundling of FEM/stage/evaluator events. | Medium-high | yes |
| Dead turn classification | `game/final_emission_meta.py` | `dead_turn_*`, `gameplay_validation` summary | FEM/gm_output classified as dead/infra/transport failure. | Medium | yes |
| Sanitizer debug | `game/output_sanitizer.py` | `sanitizer_debug` events | Internal/template/splice collision detected during sanitize. | Medium; context-dependent. | yes |
| Scaffold leakage predicate | `tests/helpers/golden_replay.py`, `game/output_sanitizer.py` | `scaffold_leakage`, `resembles_serialized_response_payload` | Replay scans final text. | High for leakage; not root owner. | yes |
| Scene validation issues | `game/validation.py` | Issue strings / `SceneValidationError` | Scene validation runs. | High | yes |
| Schema reason codes | `game/schema_contracts.py` | `schema_contracts:<domain>:<reason>` | Schema validation/adaptation. | High | yes |
| State mutation trace | `game/state_authority.py` | `build_state_mutation_trace` output | Owner/domain mutation trace built. | High when used | yes |
| Narration seam metadata | `game/narration_seam_guards.py` | `metadata.narration_seam`, planner bypass/emergency rows | CTIR/plan/prompt invariant fails or emergency path records. | Medium-high | yes |
| Scenario-spine failures | `game/scenario_spine_eval.py` | `detected_failures`, `warnings`, `classification`, `score` | Scenario-spine evaluator runs. | High for offline evaluation | yes |
| Scenario-spine metadata completeness | `game/scenario_spine_eval.py` | Metadata completeness block | Transcript rows evaluated. | High | yes |
| Playability failures/warnings | `game/playability_eval.py` | `summary.failures`, `summary.warnings`, axis scores | Playability evaluator runs. | Medium heuristic | yes |
| Narrative authenticity events | `game/narrative_authenticity_eval.py` | `build_evaluator_observability_events` output | Evaluator result projected. | Medium heuristic | yes |
| Behavioral evaluator notes | `game/behavioral_evaluators/*.py` | `notes`, `score`, `memory_failures`, `missed`, `instances` | Optional behavioral evaluators run/attach. | Medium heuristic | yes |

## Dashboard Readiness Finding

The dashboard can classify most failures without major new instrumentation if it consumes:

- golden replay drift rows,
- `trace.canonical_entry` and `turn_trace.social_contract_trace`,
- raw FEM via `read_final_emission_meta_from_turn_payload`,
- normalized FEM/stage/evaluator observability events,
- replay `unavailable` fields.

Main gap: late-stage mutation owner is not always pinpointed to a specific gate sublayer. `post_gate_mutation_detected` and stage-diff transitions tell that a mutation happened, but not always which individual repair layer changed text unless corresponding FEM layer flags are present.

