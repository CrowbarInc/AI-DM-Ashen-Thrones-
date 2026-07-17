# CN - Final-Emission Adjacency Compression Discovery

Date: 2026-06-27

## Executive Summary

The final-emission gate has been compressed from a very large policy module into a thin orchestrator, but the pressure did not disappear. It is now concentrated in adjacent modules that build FEM metadata, run terminal enforcement, normalize/sanitize final text, project replay observations, and preserve ownership/lineage diagnostics.

The strongest current pressure magnets are:

- `game/final_emission_meta.py` - metadata, ownership buckets, lineage, observability normalization, compatibility reads.
- `game/final_emission_replay_projection.py` - replay-facing projection of FEM lineage and fallback ownership.
- `tests/helpers/golden_replay_projection*.py` - protected observation schema, extraction registry, projection engine, and facade compatibility.
- `game/final_emission_visibility_fallback.py` - visibility fallback routing, metadata stamping, selection contexts, and enforcement entrypoints.
- `game/output_sanitizer.py` - sanitizer logic plus producer attribution and lineage stamping.
- `game/upstream_response_repairs.py` - upstream-prepared fallback/answer/action repair payloads that feed the gate.

Recent churn supports this shift. In the 90-day window, `game/final_emission_gate.py` is still the largest source hotspot among candidate files with 69 touches, but in the 30-day window it drops to 10 touches while `tests/helpers/golden_replay_projection.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, opening/sealed/visibility fallback modules, and replay tests dominate the final-emission-adjacent surface.

## 1. Candidate Gate-Adjacent Files

### Validators

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/final_emission_validators.py` | Validates answer completeness, response delta, fallback behavior, social response structure, opening output, response type, referent clarity. | Final gate repair layers call these to decide whether accepted/replaced output can ship. | Imports `final_emission_text_formatting`, `final_emission_text_policy`, `response_policy_contracts`, `referent_tracking`, `social_exchange_validation`; functions include `validate_answer_completeness`, `validate_fallback_behavior`, `validate_response_delta`, `validate_social_response_structure`, `validate_referent_clarity`, `validate_opening_output`. | validation, some diagnostic shaping |
| `game/social_exchange_validation.py` | Strict-social legality and malformed social output checks. | Strict-social final emission and sanitizer/fallback decisions depend on it. | Functions include `replacement_is_route_legal_social`, `is_route_illegal_global_or_sanitizer_fallback_text`, `social_final_emission_malformed_player_echo`. | validation, policy |
| `game/acceptance_quality.py` via `game/final_emission_acceptance_quality.py` | Acceptance-quality floor validation and repair seam. | N4 floor is wired into terminal/final emission metadata. | `validate_and_repair_acceptance_quality`, `apply_acceptance_quality_n4_floor_seam`. | validation, repair |
| `game/context_separation.py`, `game/anti_railroading.py`, `game/narration_visibility.py`, `game/narrative_authority.py` through final-emission layer wrappers | Domain validators for visibility, authority, anti-railroading, public/debug separation. | Their wrappers are applied as final-emission layers or terminal checks. | Wrapped by `final_emission_context_separation.py`, `final_emission_anti_railroading.py`, `final_emission_visibility_fallback.py`, `final_emission_narrative_authority.py`. | validation, policy |

### Repair Logic

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/final_emission_repairs.py` | Applies narrow final-emission repair layers for answer completeness, response delta, social response structure, narrative authenticity, fallback behavior, referent clarity. | Called by generic exits and terminal pipeline after gate branch selection. | Imports validators, metadata stamping, boundary contract; functions include `_apply_answer_completeness_layer`, `_apply_answer_exposition_plan_layer`, `_apply_response_delta_layer`, `_apply_social_response_structure_layer`, `repair_fallback_behavior`, `_apply_fallback_behavior_layer`, `_apply_referent_clarity_layer`. | repair, validation orchestration, diagnostic metadata |
| `game/upstream_response_repairs.py` | Builds upstream-prepared opening fallback and minimal answer/action repair payloads. | Feeds gate preflight with prepared payloads that can replace weak final output. | Functions include `build_minimal_answer_contract_repair_text`, `build_minimal_action_outcome_contract_repair_text`, `build_upstream_prepared_opening_fallback_payload`, `maybe_attach_upstream_prepared_opening_fallback_payload`, `merge_upstream_prepared_emission_into_gm_output`, `apply_spoken_state_refinement_cash_out`. | repair, metadata derivation, compatibility |
| `game/final_emission_opening_fallback.py` | Opening fallback selection and preservation logic. | Gate/terminal paths preserve accepted openings and project fallback ownership. | Used by `final_emission_finalize.py`, `final_emission_terminal_pipeline.py`, `final_emission_meta.py`. | repair, projection metadata, policy |
| `game/final_emission_sealed_fallback.py` | Sealed replacement fallback selection and attribution. | Generic replace/terminal fallback paths use it when output cannot be accepted. | Class `SealedFallbackSelection`; functions include `select_visibility_safe_fallback`, `select_non_strict_replace_path_terminal_sealed_fallback_selection`, `stamp_sealed_fallback_realization_family`, `finalize_n4_sealed_replace_fem_route_meta`. | repair, metadata derivation, ownership |
| `game/final_emission_visibility_fallback.py` | Visibility fallback candidate selection, routing contexts, metadata payloads, enforcement chain. | It can choose and stamp hard replacements after failed visibility validation. | Many dataclasses including `VisibilitySelectedFallback`, `VisibilityHardReplacementContext`; functions include `standard_visibility_safe_fallback`, `apply_visibility_enforcement`, `apply_first_mention_enforcement`, `apply_referential_clarity_enforcement`, `stamp_visibility_fallback_metadata`. | validation, repair, metadata, ownership |

### Metadata Helpers

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/final_emission_meta.py` | FEM dictionary lifecycle, ownership buckets, mutation lineage, telemetry packaging, observability normalization, compatibility surfaces. | Nearly every final-emission path reads or writes FEM through this module. | Imports ownership schema/views, validators, telemetry vocab, replay projection; functions include `ensure_final_emission_meta_dict`, `build_final_emission_mutation_lineage`, `refresh_final_emission_mutation_lineage`, `patch_final_emission_meta`, `stamp_producer_repair_kind`, `stamp_opening_fallback_owner_bucket`, `apply_sanitizer_producer_attribution_to_fem`, `normalize_final_emission_meta_for_observability`, `normalized_observational_telemetry_bundle`. | metadata derivation, projection, ownership policy, diagnostic formatting, compatibility shim |
| `game/final_emission_ownership_schema.py` | Canonical owner-bucket constants/taxonomies. | Metadata and fallback modules classify ownership through it. | Imported by `final_emission_meta.py`, `final_emission_visibility_fallback.py`, `final_emission_sealed_fallback.py`. | ownership policy |
| `game/final_emission_owner_bucket_views.py` | Read-side owner bucket classifiers. | Helps keep classification out of writer modules, but still influences FEM ownership stamps. | Functions include owner bucket classifiers for opening/visibility fallback fields. | metadata derivation, compatibility |
| `game/ownership_projection_views.py` | Projection owner constants, especially sanitizer trace ownership. | Used by sanitizer and replay projection tests to keep ownership fields stable. | Imported by `output_sanitizer.py`, `final_emission_replay_projection.py`, projection metadata tests. | projection, ownership |

### Replay Projection

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/final_emission_replay_projection.py` | Runtime-side read projection of FEM for replay and lineage events. | Turns final-emission metadata into protected replay/event observations. | Imports `ownership_projection_views`, `runtime_lineage_telemetry`, `telemetry_vocab`; functions include `build_fem_runtime_lineage_events`, `normalize_fem_for_replay_acceptance`, `read_fem_from_turn_for_replay`, `read_opening_fallback_owner_bucket_for_replay`. | replay projection, metadata derivation |
| `tests/helpers/golden_replay_projection.py` | Test facade for golden replay projection. | Downstream tests import this as the protected projection surface. | Imports runtime projection plus helper submodules; function `project_turn_observation`; reexports many symbols. | replay projection, compatibility shim |
| `tests/helpers/golden_replay_projection_engine.py` | Projects flat protected observed fields. | Currently imports the facade, creating a cycle; this is direct evidence of adjacency pressure. | Functions include `_extract_fem_flat_observed_fields`, `_extract_sanitizer_trace_flat_observed_fields`, `_project_flat_protected_observed_fields`. | replay projection, validation |
| `tests/helpers/golden_replay_projection_extractors.py` | Extracts nested, semantic, lineage, trace, fallback, and status projections. | Reads final-emission and sanitizer metadata from replay payloads. | Imports `game.final_emission_replay_projection`, engine, registry, presence, semantic helpers. | replay projection, metadata derivation |
| `tests/helpers/golden_replay_projection_registry.py` | Registry of protected extraction specs. | Locks source ownership for each protected field. | Classes `_FlatObservedFieldExtractor`, `_SanitizerLineageObservedExtractor`, `_ProtectedExtractionSpec`; functions `protected_observation_extraction_registry`, `protected_observation_extraction_source_by_path`. | replay projection, ownership |
| `tests/helpers/golden_replay_projection_fields.py` | Protected field registry/defaults/text hashing. | Defines the observed replay schema that FEM/sanitizer fields must satisfy. | Class `ProtectedObservationField`; functions `protected_observation_field_registry`, `protected_observation_drift_bucket`, `normalize_golden_text`, `golden_text_hash`. | replay projection, normalization |
| `tests/helpers/golden_replay_projection_fallbacks.py` | Fallback-family projection helpers. | Encodes read precedence between FEM and realization fallback family fields. | Functions `project_replay_fallback_family_from_fem`, `dual_fallback_family_replay_precedence_surface`. | replay projection, ownership |
| `tests/helpers/golden_replay_projection_presence.py` | Presence/unavailable-path accounting. | Decides whether protected fields are represented or legitimately unavailable. | Functions `lookup_observation_path`, `protected_path_representation_errors`, `protected_path_covered_by_unavailable`. | replay projection, validation |
| `tests/helpers/golden_replay_projection_manifest.py` | Renders/parses protected replay manifest. | Keeps docs/manifest in lockstep with protected projection registry. | Functions `render_protected_observation_manifest_section`, `protected_observation_manifest_section_is_current`. | projection documentation, compatibility |

### Sanitizer / Normalization

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/output_sanitizer.py` | Post-GM player-facing hygiene: strip internal/debug fragments, rewrite or drop unsafe text under configured modes, stamp sanitizer lineage. | Gate docstring names it as final validation before API response; replay projection consumes its lineage. | Imports `final_emission_meta`, `attribution_read_views`, `ownership_projection_views`, social fallback/policy; function `sanitize_player_facing_output`; helpers `_ensure_sanitizer_lineage_trace`, `_record_sanitizer_lineage_event`, `_stamp_sanitizer_producer_attribution`. | sanitization, normalization, repair, metadata, ownership |
| `game/final_emission_text_formatting.py` | Shared formatting/normalization primitives. | Used by gate, repairs, finalize, fallback, upstream repairs, strict social, and sanitizer-adjacent layers. | Functions `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_sanitize_output_text`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`. | normalization/sanitization |
| `game/final_emission_finalize.py` | Final packaging, route-illegal contamination stripping, lineage refresh, speaker observation stamp. | Last mile before output is shipped. | Functions `finalize_emission_output`, `strip_appended_route_illegal_contamination_sentences`, `final_emission_fast_path_eligible`. | final emission, normalization, metadata, diagnostic telemetry |

### Final Emission / Gate Entrypoints

| Path | Apparent responsibility | Why gate-adjacent | Key imports/exports/functions/classes | Owns |
| --- | --- | --- | --- | --- |
| `game/final_emission_gate.py` | Thin branch orchestrator for final-emission gate. | Primary entrypoint. | Function `apply_final_emission_gate`; imports non-strict/strict stacks, gate context, generic exits, passive scene pressure, speaker enforcement, interaction continuity. | gate policy, orchestration |
| `game/final_emission_gate_context.py` | Gate preflight aggregation. | Centralizes branch flags, defaults, strict-social routing, telemetry, turn packet, upstream attach. | Class `GateExecutionContext`; function `initialize_gate_execution_context`. | metadata derivation, orchestration |
| `game/final_emission_generic_exit.py` | Generic accept/replace exits. | Builds FEM, applies late AEP layer, terminal pipeline, finalization. | Functions `run_generic_accept_exit`, `run_generic_replace_exit`. | final emission, repair orchestration, metadata |
| `game/final_emission_terminal_pipeline.py` | Terminal enforcement after branch choice. | Applies strict social patch, referent clarity, visibility fallback, opening/acceptance quality/NA terminal logic. | Function `run_gate_terminal_enforcement_pipeline`. | final emission, validation, repair, ownership |
| `game/final_emission_fem_assembly.py` | Builds and merges gate FEM metadata. | The bridge between layer results and final projected metadata. | Functions `build_gate_accept_fem_base`, `build_gate_replace_fem_base`, `merge_gate_layer_metas_into_fem`. | metadata derivation, projection |
| `game/final_emission_non_strict_stack.py`, `game/final_emission_strict_social_stack.py` | Layer-stack orchestration by route type. | Gate delegates branch-specific layer stacks to these modules. | `run_non_strict_layer_stack`, `run_strict_social_composition_trunk`. | gate policy, repair orchestration |

### Tests Covering These Paths

| Path | Behaviors covered | Modules under test | Style |
| --- | --- | --- | --- |
| `tests/test_final_emission_gate.py` | Gate branch outcomes, metadata, historical contract pins. | `final_emission_gate`, generic exits, terminal pipeline, meta. | Broad/integration-heavy, but recently decomposed. |
| `tests/test_final_emission_repairs.py` | Repair-layer behavior and no-semantic-repair boundary pins. | `final_emission_repairs`, validators, boundary contract. | Focused unit/mid-level. |
| `tests/test_final_emission_validators.py` | Validator contracts for answer, social, fallback, referent behavior. | `final_emission_validators`. | Focused unit-level. |
| `tests/test_final_emission_meta.py` | FEM shape, owner buckets, lineage, normalization, dead-turn snapshots. | `final_emission_meta`, replay projection. | Mixed; broad metadata contract. |
| `tests/test_final_emission_visibility.py` | Visibility, first mention, referential clarity, finalization contamination strip. | visibility fallback, finalization, gate. | Broad/integration-heavy. |
| `tests/test_final_emission_visibility_fallback.py` | Visibility fallback helpers, routing contexts, metadata payloads, module ownership locks. | `final_emission_visibility_fallback`, sealed fallback. | Focused but large. |
| `tests/test_output_sanitizer.py` | Sanitizer rewrite/strip modes and lineage stamping. | `output_sanitizer`. | Focused unit-level. |
| `tests/test_upstream_response_repairs.py` | Upstream-prepared opening/answer/action repair payloads. | `upstream_response_repairs`. | Focused unit-level. |
| `tests/test_golden_replay_projection*.py` | Protected observation schema, projection, metadata, registry, module boundaries. | `tests/helpers/golden_replay_projection*`, `final_emission_replay_projection`. | Mixed; strong contract surface. |
| `tests/test_golden_replay*.py` | End-to-end replay assertions and protected replay behavior. | replay helpers, final-emission metadata. | Broad/integration-heavy. |

## 2. Call Graph / Dependency Map

### Text Tree

```text
apply_final_emission_gate
  initialize_gate_execution_context
    resolve_gate_preflight_branch_flags
    initialize_gate_preflight_layer_meta_defaults
      default_*_meta helpers from final_emission_* layer modules
    resolve_gate_preflight_interaction_metadata
    resolve_gate_preflight_pregate_text
    resolve_gate_preflight_strict_social_routing
      sanitize_player_facing_output
      strict_social_* policy helpers
    apply_gate_preflight_telemetry_and_containment
    initialize_gate_preflight_turn_packet
    apply_gate_preflight_upstream_attach
      maybe_attach_upstream_prepared_opening_fallback_payload
      merge_upstream_prepared_emission_into_gm_output

  speaker contract validation / interaction continuity attach

  run_non_strict_layer_stack OR run_strict_social_composition_trunk
    final_emission_* layer modules
      validators: final_emission_validators, social_exchange_validation, domain validators
      repairs: final_emission_repairs, final_emission_* layer wrappers
      metadata: default/merge layer meta helpers

  run_generic_accept_exit OR run_generic_replace_exit
    build_gate_accept_fem_base OR build_gate_replace_fem_base
      project_strict_social_replace_realization_family
      infer_accept_path_final_emitted_source
      ownership / fallback family stamps
    _apply_answer_exposition_plan_layer
      validate_answer_exposition_plan_convergence
      assert_final_emission_mutation_allowed
    merge_gate_layer_metas_into_fem
      merge_*_meta helpers from final_emission_meta and final_emission_repairs
    run_gate_terminal_enforcement_pipeline
      apply_strict_social_emergency_fallback_patch
      _apply_referent_clarity_pre_finalize
      apply_visibility_enforcement
      apply_acceptance_quality_n4_floor_seam
      opening fallback reassertion / sealed fallback selection
    finalize_emission_output
      strip_appended_route_illegal_contamination_sentences
      reassert_scene_opening_accepted_candidate
      package_emission_channel_sidecar
      stamp_final_speaker_observation
      refresh_final_emission_mutation_lineage
      record_stage_snapshot

Replay/read side:
  final_emission_meta.normalized_observational_telemetry_bundle
    normalize_final_emission_meta_for_observability
    build_fem_runtime_lineage_events
      final_emission_replay_projection

  tests.helpers.golden_replay_projection.project_turn_observation
    golden_replay_projection_extractors
      final_emission_replay_projection
      golden_replay_projection_engine
      golden_replay_projection_registry
      golden_replay_projection_presence
      golden_replay_projection_semantic
    golden_replay_projection_fallbacks
    golden_replay_projection_fields
    golden_replay_projection_manifest
    golden_replay_projection_speaker
```

### Highest-Pressure Edges

- `final_emission_gate.py -> final_emission_generic_exit.py -> final_emission_terminal_pipeline.py -> final_emission_finalize.py`: this is the primary final-emission route. The gate is thin, but exit/terminal/finalize modules now coordinate branch state, repairs, metadata, and last-mile packaging.
- `final_emission_generic_exit.py -> final_emission_fem_assembly.py -> final_emission_meta.py`: metadata assembly is now the main cross-layer merge point. This edge absorbs much of the former gate metadata pressure.
- `final_emission_repairs.py -> final_emission_validators.py`: repair layers call validators before/after narrow repairs. This is appropriate but dense; the risk is duplicated policy checks between validator and repair.
- `output_sanitizer.py -> final_emission_meta.py` and `final_emission_replay_projection.py`: sanitizer logic now stamps producer attribution and lineage that replay projection treats as protected observable data.
- `tests/helpers/golden_replay_projection_engine.py -> tests/helpers/golden_replay_projection.py`: this is a pressure leak. The engine imports the facade, creating the failing cycle observed in tests.
- `final_emission_visibility_fallback.py -> final_emission_meta.py / ownership schema / sealed fallback`: visibility fallback is effectively a specialized mini-gate for selection, route metadata, hard replacement, and ownership attribution.

## 3. Touch / Churn Concentration

### 90-Day Top Files, Candidate Highlights

The requested 90-day command produced these gate-adjacent highlights:

| Touches | File |
| ---: | --- |
| 69 | `game/final_emission_gate.py` |
| 54 | `tests/test_final_emission_gate.py` |
| 36 | `game/final_emission_meta.py` |
| 29 | `tests/test_final_emission_meta.py` |
| 23 | `game/social_exchange_emission.py` |
| 23 | `tests/test_social_exchange_emission.py` |
| 20 | `game/final_emission_repairs.py` |
| 19 | `game/final_emission_validators.py` |
| 18 | `tests/helpers/golden_replay_projection.py` |
| 15 | `tests/test_final_emission_opening_fallback.py` |
| 15 | `tests/test_final_emission_visibility.py` |
| 13 | `tests/test_opening_fallback_owner_bucket.py` |
| 12 | `game/final_emission_replay_projection.py` |
| 12 | `game/upstream_response_repairs.py` |
| 12 | `tests/test_upstream_response_repairs.py` |
| 11 | `tests/test_final_emission_sealed_fallback.py` |
| 10 | `tests/test_final_emission_visibility_fallback.py` |
| 9 | `tests/test_output_sanitizer.py` |

### 30-Day Top Files, Candidate Highlights

| Touches | File |
| ---: | --- |
| 28 | `tests/test_golden_replay.py` |
| 18 | `tests/helpers/golden_replay_projection.py` |
| 18 | `tests/test_final_emission_gate.py` |
| 16 | `tests/test_final_emission_meta.py` |
| 13 | `game/final_emission_meta.py` |
| 13 | `tests/test_final_emission_opening_fallback.py` |
| 12 | `game/final_emission_replay_projection.py` |
| 11 | `tests/test_final_emission_sealed_fallback.py` |
| 11 | `tests/test_opening_fallback_owner_bucket.py` |
| 10 | `game/final_emission_gate.py` |
| 9 | `tests/test_final_emission_visibility_fallback.py` |
| 8 | `game/final_emission_opening_fallback.py` |
| 8 | `game/final_emission_sealed_fallback.py` |
| 8 | `tests/test_golden_replay_projection.py` |
| 7 | `game/final_emission_visibility_fallback.py` |
| 7 | `tests/test_upstream_response_repairs.py` |
| 7 | `tests/test_fallback_behavior_repairs.py` |
| 5 | `game/final_emission_terminal_pipeline.py` |
| 5 | `game/final_emission_finalize.py` |
| 5 | `game/upstream_response_repairs.py` |

### Same Files Dominating?

No. The 90-day history is gate-heavy because it includes the pre-extraction era and major gate decompositions. The 30-day history shows pressure moving into:

- Golden replay projection and protected observation helpers.
- FEM metadata and runtime lineage projection.
- Opening, sealed, and visibility fallback ownership modules.
- Focused tests that pin these new ownership/projection boundaries.

### New Pressure Magnets After Gate Simplification

Likely new or intensified magnets:

- `game/final_emission_meta.py`: repeated changes in commits `H`, `O`, `P`, `AJ`, `BK`, `BS`, `BU`, `CK`.
- `game/final_emission_replay_projection.py`: repeated changes in `O`, `P`, `AB`, `AO`, `AP`, `BS`, `BU`, `CG`.
- `tests/helpers/golden_replay_projection.py` and submodules: major decompositions in `CE`, `CF`, `CL`.
- `game/final_emission_visibility_fallback.py`, `game/final_emission_opening_fallback.py`, `game/final_emission_sealed_fallback.py`: 30-day pressure around fallback ownership and terminal replacement paths.
- `game/output_sanitizer.py`: touched by ownership convergence, fallback ownership compression, semantic replacement attribution, and fan-in/fan-out validation.

## 4. Test Pressure Map

### Relevant Test Files

| Path | Behaviors asserted | Modules under test | Broad or focused | Coupling pressure |
| --- | --- | --- | --- | --- |
| `tests/test_final_emission_gate.py` | Gate branch routing, metadata pins, fallback behavior, final emitted source, historical convergence locks. | Gate, generic exits, terminal pipeline, metadata. | Broad/integration-heavy. | High; failures may require coordinated changes across gate, meta, fallback modules. |
| `tests/test_final_emission_repairs.py` | Layer repairs, fallback behavior repair, semantic repair boundary. | Repairs, validators, boundary contract. | Focused. | Medium; helps isolate repair semantics from gate. |
| `tests/test_final_emission_validators.py` | Validation contracts for answer/social/fallback/referent rules. | Validators and social validation. | Focused. | Low to medium; protects validator extraction. |
| `tests/test_final_emission_meta.py` | FEM defaults, lineage, owner buckets, observability normalization. | Metadata and replay projection. | Mixed. | High; metadata changes ripple into replay and diagnostics. |
| `tests/test_final_emission_visibility.py` | Visibility validation/replacement, first mention, referent clarity, finalization strip behavior. | Visibility fallback, finalization, gate. | Broad. | High; combines validator, repair, fallback, and final output assertions. |
| `tests/test_final_emission_visibility_fallback.py` | Helper entrypoints, dataclass/context shapes, owner routing, sealed fallback delegation. | Visibility fallback and sealed fallback. | Focused but large. | Medium-high; pins decomposition boundaries. |
| `tests/test_output_sanitizer.py` | Sanitizer strip/rewrite modes, empty fallback, lineage/owner stamping. | Output sanitizer, ownership projection views, metadata. | Focused. | Medium; sanitizer metadata is replay-protected. |
| `tests/test_upstream_response_repairs.py` | Upstream-prepared payload selection and repair text. | Upstream response repairs, final-emission validators. | Focused. | Medium; upstream payloads influence gate replacement paths. |
| `tests/test_golden_replay_projection_modules.py` | Projection facade/submodule import graph, reexports, backup equivalence. | Golden replay projection helper modules. | Focused boundary/governance. | High; currently catches an import cycle. |
| `tests/test_golden_replay_projection_metadata.py` | Projected FEM/sanitizer metadata and lineage. | Replay projection helpers, final-emission metadata, sanitizer. | Focused projection. | High; protected fields make metadata names sticky. |
| `tests/test_golden_replay_projection_registry.py` | Registry/spec parity and per-field extraction ownership. | Projection registry/extractors/fields. | Focused. | Medium-high; protects extraction consolidation. |
| `tests/test_golden_replay_projection.py` | Projection facade smoke and selected locked behaviors. | Projection facade and replay API helpers. | Mixed. | Medium; facade remains compatibility surface. |

### Tests Run

Command:

```powershell
$env:PYTHONPATH='.;.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_final_emission_validators.py tests\test_final_emission_repairs.py tests\test_final_emission_meta.py tests\test_output_sanitizer.py tests\test_golden_replay_projection_modules.py tests\test_golden_replay_projection_metadata.py -q --tb=short --basetemp=codex_pytest_tmp_cn_discovery
```

Result: failed with 2 failures in `tests/test_golden_replay_projection_modules.py`; all other selected tests completed before those failures.

Failures:

- `test_projection_module_import_graph_has_no_cycles`: import cycle detected at `tests.helpers.golden_replay_projection_engine`.
- `test_focused_modules_do_not_import_facade`: `tests.helpers.golden_replay_projection_engine` imports the facade `tests.helpers.golden_replay_projection`.

Command:

```powershell
$env:PYTHONPATH='.;.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_final_emission_gate.py tests\test_final_emission_visibility_fallback.py tests\test_final_emission_boundary_contract.py -q --tb=short --basetemp=codex_pytest_tmp_cn_discovery3
```

Result: passed, exit code 0. The dot output corresponds to 161 passing tests.

Attempted command:

```powershell
$env:PYTHONPATH='.;.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_final_emission_gate.py tests\test_final_emission_terminal_pipeline.py tests\test_final_emission_visibility_fallback.py -q --tb=short --basetemp=codex_pytest_tmp_cn_discovery2
```

Result: not run; `tests\test_final_emission_terminal_pipeline.py` does not exist.

## 5. Responsibility Boundary Audit

| Module | Categories | Flagged? | Notes |
| --- | --- | --- | --- |
| `game/final_emission_gate.py` | ownership/gate policy, orchestration | No | Thin entrypoint after extraction. |
| `game/final_emission_gate_context.py` | metadata derivation, orchestration, telemetry | No | Preflight aggregator is appropriate if kept dumb. |
| `game/final_emission_generic_exit.py` | final emission, repair orchestration, metadata derivation | Yes | Accept/replace exits know about FEM construction, AEP layer, terminal pipeline, sealed fallback, finalization. Mixing is partly necessary, but a route-result object could reduce argument pressure. Protected by `test_final_emission_gate.py`, `test_final_emission_boundary_contract.py`. |
| `game/final_emission_terminal_pipeline.py` | validation, repair, replay/metadata stamping, ownership policy | Yes | Terminal enforcement coordinates strict-social patch, referent clarity, visibility fallback, opening fallback, sealed fallback, acceptance quality. Safe seam: split terminal route decisions from metadata stamping. Protected by gate, visibility, opening, sealed fallback tests. |
| `game/final_emission_fem_assembly.py` | metadata derivation, projection, diagnostic formatting | No | Central FEM merge helper; responsibilities are related. |
| `game/final_emission_finalize.py` | final emission, normalization/sanitization, metadata derivation, diagnostic telemetry | Yes | Last-mile packaging also strips route-illegal contamination and refreshes mutation lineage. Safe seam: keep text packaging separate from FEM lineage refresh. Protected by gate and visibility tests. |
| `game/final_emission_validators.py` | validation, diagnostic formatting | No | Large, but mostly single category. Could later split by validator family. |
| `game/final_emission_repairs.py` | repair, validation orchestration, metadata derivation, ownership/gate boundary policy | Yes | Repair layers run validators, mutate text, stamp repair metadata, and enforce semantic-repair boundaries. Safe seam: per-layer result dataclass or family modules. Protected by repairs/validators tests. |
| `game/final_emission_meta.py` | metadata derivation, replay projection, ownership policy, diagnostic formatting, compatibility shim | Yes | Biggest mixed module. Some mixing is historical compatibility; owner-bucket registry, FEM normalization, runtime-lineage projection compatibility, dead-turn packaging, and read-side bundles can be split. Protected by `test_final_emission_meta.py`, replay projection metadata tests. |
| `game/final_emission_replay_projection.py` | replay projection, metadata derivation | No | Reasonably focused, though ownership classification helpers are close to policy. |
| `game/final_emission_visibility_fallback.py` | validation, repair, metadata derivation, ownership/gate policy, diagnostic formatting | Yes | Acts as a specialized mini-gate for visibility failures. Safe seam: selection candidates, routing decision, and metadata stamping as separate modules. Protected by `test_final_emission_visibility_fallback.py`, `test_final_emission_visibility.py`. |
| `game/final_emission_sealed_fallback.py` | repair, metadata derivation, ownership policy | Yes | Smaller mini-gate for sealed replacements. Safe seam: selection vs stamping. Protected by sealed fallback and visibility fallback tests. |
| `game/output_sanitizer.py` | normalization/sanitization, repair, metadata derivation, ownership policy | Yes | Sanitizer now owns lineage and fallback attribution in addition to text hygiene. Safe seam: extract sanitizer lineage/stamping helpers. Protected by `test_output_sanitizer.py`, replay projection metadata tests. |
| `game/upstream_response_repairs.py` | repair, metadata derivation, compatibility shim, policy | Yes | Upstream payload builder mixes repair prose, opening fallback attribution, lead/clue cash-out. Safe seam: upstream prepared emission payload metadata vs text builders. Protected by `test_upstream_response_repairs.py`. |
| `tests/helpers/golden_replay_projection.py` | replay projection, compatibility shim | No | Facade is expected, but should not be imported by focused submodules. |
| `tests/helpers/golden_replay_projection_engine.py` | replay projection, validation, compatibility leak | Yes | It imports the facade, making the facade a dependency and causing a cycle. Safe seam: import concrete extractor/fallback functions directly. Protected by `test_golden_replay_projection_modules.py`. |
| `tests/helpers/golden_replay_projection_extractors.py` | replay projection, metadata derivation, validation/status | Yes | Extractor module still coordinates many projection families. Safe seam: keep semantic, lineage, fallback, presence extraction in separate files. Protected by registry/metadata tests. |
| `tests/helpers/golden_replay_projection_registry.py` | replay projection, ownership | No | Registry ownership is intentional. |
| `tests/helpers/golden_replay_projection_presence.py` | replay projection, validation | No | Presence accounting is focused. |

## 6. Former Gate Pressure Absorption

### Suspicious Mini-Gates

- `game/final_emission_visibility_fallback.py`: contains route contexts, hard-replacement decision inputs, fallback candidate selection, metadata stamping, and enforcement entrypoints. It is a visibility-specific gate.
- `game/final_emission_terminal_pipeline.py`: applies late-stage policy and replacement decisions after the primary gate branch. It behaves like a second terminal gate.
- `game/output_sanitizer.py`: final text hygiene now includes ownership attribution and fallback producer lineage, making it a post-gate mini-gate for output safety.
- `game/upstream_response_repairs.py`: upstream-prepared payloads can satisfy answer/action/opening contracts before final emission, so this module can absorb former gate repair pressure.
- `tests/helpers/golden_replay_projection_engine.py` plus facade: projection helpers now enforce architecture and protected field policy in tests, and the current import cycle shows pressure migrating into the projection layer.

### Policy Decisions Outside Expected Ownership Modules

- Owner bucket decisions appear in `final_emission_meta.py`, `final_emission_visibility_fallback.py`, `final_emission_sealed_fallback.py`, `output_sanitizer.py`, and replay projection helpers. Some are write-side stamps, some are read-side derivations, and some are protected projection rules.
- Sanitizer owner lineage is stamped in `output_sanitizer.py` but projected and tested through golden replay helpers.
- Fallback-family precedence is represented in both `game/final_emission_replay_projection.py` and `tests/helpers/golden_replay_projection_fallbacks.py`.
- `final_emission_meta.py` still imports `build_fem_runtime_lineage_events` as a compatibility surface, which keeps replay projection adjacent to metadata.

### Duplicate Checks Across Layers

- Text normalization appears in `final_emission_text_formatting.py`, `final_emission_repairs.py`, `output_sanitizer.py`, `upstream_response_repairs.py`, and projection text hashing/defaults.
- Fallback behavior is validated in `final_emission_validators.py`, repaired in `final_emission_repairs.py`, sanitized in `output_sanitizer.py`, and projected in replay helpers.
- Owner bucket derivation appears as write-side stamps (`final_emission_meta.py`, fallback modules), read-side views (`final_emission_owner_bucket_views.py`), and replay projection (`final_emission_replay_projection.py`, golden replay helpers).
- Protected-field defaults and presence handling are split across `golden_replay_projection_fields.py`, `registry.py`, `presence.py`, and `engine.py`, with tests enforcing parity.

### Diagnostics Implying Ownership Policy Outside Gate

- FEM fields such as `producer_repair_kind`, `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, `final_emission_mutation_lineage`, and sanitizer lineage fields are populated outside `apply_final_emission_gate`.
- Replay projection tests treat these diagnostics as protected behavior, so diagnostics are no longer passive; they constrain ownership boundaries.

## 7. Duplication / Overlap Findings

| Files/functions | Duplicated concept | Risk of changing | Suggested consolidation direction |
| --- | --- | --- | --- |
| `final_emission_meta.py`, `final_emission_owner_bucket_views.py`, `final_emission_visibility_fallback.py`, `final_emission_sealed_fallback.py`, `output_sanitizer.py` | Owner bucket classification and stamping. | High; replay and diagnostics depend on field names and values. | Keep `ownership_schema` as constants, move read classifiers to owner bucket views, and keep write stamps as thin wrappers. |
| `final_emission_repairs.py` and `final_emission_validators.py` | Repair layers repeatedly validate before/after and carry diagnostic flags. | Medium-high; repair behavior is user-visible. | Standardize a `LayerRepairResult` shape or per-family result builder, without changing text output. |
| `final_emission_text_formatting.py`, `output_sanitizer.py`, `upstream_response_repairs.py`, `golden_replay_projection_fields.py` | Text normalization, punctuation, hashing, strip/collapse behavior. | Medium; subtle output diffs can break snapshots. | Keep shipping normalization in `final_emission_text_formatting`; projection-only normalization should explicitly call it or document divergence. |
| `final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection_fallbacks.py` | Fallback-family read precedence. | High; protected replay semantics. | Move precedence description to one runtime helper and have tests import that helper or compare against a manifest. |
| `final_emission_meta.py` and `final_emission_replay_projection.py` | Runtime lineage projection and normalized observability bundles. | Medium-high; event surfaces are protected. | Keep event construction in replay projection; metadata module should only delegate through a narrow read-side facade. |
| `final_emission_visibility_fallback.py`, `final_emission_sealed_fallback.py`, `final_emission_terminal_pipeline.py` | Terminal fallback selection and metadata stamping. | High; replacement behavior is user-visible. | Split selection decision objects from metadata stampers; preserve existing public helper names as compatibility wrappers. |
| `tests/test_final_emission_gate.py`, `tests/test_final_emission_visibility.py`, `tests/test_final_emission_meta.py` | Broad final-emission assertions that cross many modules. | Medium; broad tests force coordinated edits. | Keep a small integration spine and move field-specific assertions to focused module tests. |
| `tests/helpers/golden_replay_projection_engine.py` and `tests/helpers/golden_replay_projection.py` | Projection facade dependency in focused engine. | Low behavior risk, high architecture value. | Replace facade import with direct imports from fields/registry/extractors or shared leaf helpers. |

## 8. Recommended Next Blocks

### Block CN1 - Replay Projection Cycle Removal

- Target: `tests/helpers/golden_replay_projection_engine.py`.
- Goal: remove its import of the facade and restore acyclic projection helper boundaries.
- Files likely touched: `tests/helpers/golden_replay_projection_engine.py`, possibly `tests/helpers/golden_replay_projection_extractors.py`, `tests/test_golden_replay_projection_modules.py`.
- Safety constraints: no protected observed-turn output changes; facade reexports remain intact.
- Exact tests to run: `pytest tests/test_golden_replay_projection_modules.py tests/test_golden_replay_projection_registry.py tests/test_golden_replay_projection_metadata.py -q`.
- Expected success metric: the two module-boundary failures disappear and byte-for-byte projection tests remain green.

### Block CN2 - FEM Metadata Facade Split

- Target: `game/final_emission_meta.py`.
- Goal: extract observability/read-side normalization and runtime lineage compatibility into a focused metadata read-view module.
- Files likely touched: `game/final_emission_meta.py`, new `game/final_emission_meta_observability.py` or similar, `game/final_emission_replay_projection.py`, metadata tests.
- Safety constraints: public import compatibility preserved; raw FEM field names unchanged.
- Exact tests to run: `pytest tests/test_final_emission_meta.py tests/test_golden_replay_projection_metadata.py tests/test_runtime_lineage_telemetry.py -q`.
- Expected success metric: `final_emission_meta.py` loses read-side bundle/projection weight with no projection output diffs.

### Block CN3 - Visibility Fallback Selection/Stamping Separation

- Target: `game/final_emission_visibility_fallback.py`.
- Goal: separate fallback selection decisions from metadata stamping/logging payload builders.
- Files likely touched: `game/final_emission_visibility_fallback.py`, optional new `game/final_emission_visibility_metadata.py`, `tests/test_final_emission_visibility_fallback.py`.
- Safety constraints: no fallback prose changes; dataclass compatibility preserved or wrapped.
- Exact tests to run: `pytest tests/test_final_emission_visibility_fallback.py tests/test_final_emission_visibility.py tests/test_final_emission_gate.py -q`.
- Expected success metric: enforcement entrypoints call smaller helpers; existing visibility/gate tests stay green.

### Block CN4 - Sanitizer Lineage Extraction

- Target: `game/output_sanitizer.py`.
- Goal: move sanitizer lineage trace initialization/stamping to a small owner module while keeping `sanitize_player_facing_output` behavior identical.
- Files likely touched: `game/output_sanitizer.py`, new `game/output_sanitizer_lineage.py`, `game/final_emission_meta.py`, `tests/test_output_sanitizer.py`, replay metadata tests.
- Safety constraints: sanitizer modes and returned text unchanged; lineage fields unchanged.
- Exact tests to run: `pytest tests/test_output_sanitizer.py tests/test_golden_replay_projection_metadata.py tests/test_final_emission_meta.py -q`.
- Expected success metric: sanitizer text tests and protected sanitizer lineage projections remain unchanged.

### Block CN5 - Repair Layer Result Shape Consolidation

- Target: `game/final_emission_repairs.py`.
- Goal: introduce a narrow internal result helper for repair layer `(text, meta, passed)` tuples and repeated meta merge patterns.
- Files likely touched: `game/final_emission_repairs.py`, `tests/test_final_emission_repairs.py`, maybe `tests/test_final_emission_gate.py`.
- Safety constraints: no emitted text diffs; no semantic repair expansion.
- Exact tests to run: `pytest tests/test_final_emission_repairs.py tests/test_final_emission_validators.py tests/test_final_emission_boundary_no_semantic_repair.py -q`.
- Expected success metric: less repeated per-layer boilerplate; repair tests green.

### Block CN6 - Golden Replay Protected Field Ownership Manifest Tightening

- Target: `tests/helpers/golden_replay_projection_registry.py`, `tests/helpers/golden_replay_projection_fields.py`, manifest tests.
- Goal: make ownership/source per protected field explicit in one registry path and reduce presence/default duplication.
- Files likely touched: projection registry/fields/presence helpers, `docs/testing/protected_replay_manifest.md`, registry/manifest tests.
- Safety constraints: no observed row schema changes unless explicitly approved.
- Exact tests to run: `pytest tests/test_golden_replay_projection_registry.py tests/test_golden_replay_projection_manifest.py tests/test_golden_replay_projection_presence_integration.py -q`.
- Expected success metric: one source of truth for protected field ownership and unchanged manifest output.

## Files To Pass To ChatGPT Next

For next implementation planning, pass:

- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_visibility_fallback.py`
- `game/output_sanitizer.py`
- `tests/helpers/golden_replay_projection_engine.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_extractors.py`
- `tests/helpers/golden_replay_projection_registry.py`
- `tests/test_golden_replay_projection_modules.py`

