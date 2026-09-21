# CM - Ownership Registry Magnet Reduction Discovery

Date: 2026-06-26  
Scope: discovery/audit only. No production code changes made.

## Executive Summary

`tests/test_ownership_registry.py` is still a governance touch magnet, but its current shape is improved from the older pre-CH monolith. It is now 2,357 lines with 217 pytest entrypoints. CH extracted most pure logic into helper modules (`tests/ownership_*`), but the pytest collection identity, docstring policy, and new enforcement entrypoints still concentrate in the registry test.

The smallest safe stabilization path is to keep the direct-owner registry and inventory parity checks in this file, while moving cycle/domain-specific enforcement entrypoints into focused owner test files beside their helper modules. The highest-pressure candidates are BJ delegate closeout locks, BN gate-context preflight guards, BV compatibility/import guards, and smoke/projection policy locks.

## 1. File Identity and Role

Target file located at:

- `tests/test_ownership_registry.py`

Current role:

- Canonical test-responsibility governance test.
- Enforces one direct owner per governed responsibility slice via `tests/ownership_registry_contract.py`.
- Validates slim committed governance inventory `tests/test_inventory_governance.json` against derived full inventory from `tools/test_audit.py`.
- Locks allowed direct-owner and neighbor relationships for gate, replay, smoke, transcript, gauntlet, evaluator, and downstream consumer suites.
- Hosts pytest entrypoints for extracted guard helpers:
  - gate magnet guard
  - BD6 gate dependency compression
  - BI8 golden replay boundary
  - BN1-BN11 gate-context import/preflight guards
  - BV2C/BV7C/BV10C/BV12C/BV13C/BV14C/BV16C compatibility and import guards
  - BJ70-BJ129 delegate closeout locks
  - BU8/BU9 ownership write-path governance

Primary dependencies:

| Kind | Files |
|---|---|
| Registry/source of truth | `tests/ownership_registry_contract.py` |
| Inventory policy/orchestration | `tests/ownership_inventory_governance.py`, `tests/test_inventory_governance.json`, `tools/test_audit.py` |
| Gate/dependency guards | `tests/ownership_guard_gate_magnet.py`, `tests/ownership_guard_bd_dependency_compression.py`, `tests/ownership_guard_bn_gate_context.py`, `tests/helpers/gate_thin_boundary_locks.py` |
| Replay/projection boundary guards | `tests/ownership_guard_bi8_golden_replay_boundary.py`, `tests/helpers/golden_replay_projection.py`, `docs/testing/protected_replay_manifest.md` |
| BV compatibility guards | `tests/ownership_guard_bv_compatibility.py`, `tests/ownership_guard_bv16c_terminal_monkeypatch.py` |
| Delegate closeout locks | `tests/ownership_closeout_delegate_locks.py`, many `game/final_emission_*` owner modules, harness/helper tests named in scan allowlists |
| Runtime ownership/write policy | `game/final_emission_ownership_schema.py`, `game/final_emission_owner_bucket_views.py`, `tests/helpers/ownership_write_path_governance.py`, `docs/audits/BU4_ownership_write_paths.csv` |
| Policy docs | `tests/README_TESTS.md`, `docs/convergence_ci_inventory.md`, `docs/architecture_ownership_ledger.md`, CH closeout docs under `docs/audits/CH*.md` |

## 2. Touch-Frequency Causes

Recent git history for `tests/test_ownership_registry.py`:

| Commit | Date | Delta | Inferred reason | Classification |
|---|---:|---:|---|---|
| `9b62d17` CJ: Foundation Readiness Closeout | 2026-06-26 | +14/-3 | Foundation readiness and post-CH guardrail updates | governance edit |
| `85855df` CH: Governance Hub Redistribution | 2026-06-26 | +1036/-4649 | Extracted registry, inventory, guard, and delegate logic into helper modules | structural edit |
| `ce36d0c` CB: Feature Boundary Readiness Audit | 2026-06-23 | +22/-0 | Added feature-boundary/readiness evidence locks | governance edit |
| `7651237` BV: Maintenance Economics Validation Closeout | 2026-06-21 | +1337/-16 | Added BV compat barrel, read-cluster, smoke-monolith, and import-cap governance | structural edit |
| `22cd49a` BU: Post-BJ Fan-In / Fan-Out Validation | 2026-06-21 | +165/-67 | Added ownership write-path parity and producer-stamp pairing locks | governance edit |
| `b7c5b2c` BM: Large Test File Decomposition | 2026-06-17 | +14/-3 | Decomposition follow-up and file-size governance | structural edit |
| `b88a560` BN: Gate Fan-Out Reduction | 2026-06-17 | +667/-7 | Added BN1-BN11 gate-context/preflight import guards | structural edit |
| `97b1836` BL: Replay Projection Simplification | 2026-06-16 | +10/-10 | Replay projection boundary wording/alignment | diagnostic/string alignment edit |
| `11ff282` BJ: Final Emission Gate Responsibility Extraction | 2026-06-16 | +1798/-5 | Added many owner entrypoint/delegate-collapse locks | structural edit |
| `f7e73fb` BI: Golden Replay Ownership Isolation | 2026-06-13 | +215/-0 | Added replay-vs-gate ownership boundary guards | governance edit |
| `1603880` BG: Maintenance Hotspot Redistribution | 2026-06-12 | +19/-3 | Protected replay manifest parity | governance edit |
| `a534e5f` BF: Test Inventory De-Amplification | 2026-06-11 | +285/-72 | Slim governance inventory and derived-field checks | policy edit |
| `fc48d7a` BE: Assertion Economy Simplification | 2026-06-11 | +39/-2 | Scaffold phrase triple-layer policy lock | duplicate enforcement edit |
| `fde6598` BD: Gate Dependency Compression | 2026-06-10 | +206/-0 | Added non-owner gate/projection import compression guards | structural edit |
| `ca830c2` BB: Replay Surface Area Compression | 2026-06-10 | +184/-18 | Replay surface ownership locks | governance edit |
| `888d0fc` AQ: Test Inventory Compression | 2026-06-06 | +374/-24 | Derived registry/index/inventory policy | policy edit |
| `927dae2` AO: Replay Ownership Consolidation | 2026-06-03 | +30/-0 | Runtime/acceptance projection separation | governance edit |
| `a84075c` AL: Downstream Assertion Convergence | 2026-06-02 | +68/-4 | Legality owner vs smoke facade policy | duplicate enforcement edit |
| `49e4147` Cycle AG | 2026-05-31 | +22/-0 | Residual complexity burn-down locks | governance edit |
| `8cbea51` Cycle AD | 2026-05-31 | +101/-1 | Downstream smoke vs direct-owner restrictions | governance edit |
| `2274f26` Cycle AE | 2026-05-31 | +24/-1 | Meta projection ownership boundary | governance edit |
| `b54b311` Cycle AB | 2026-05-31 | +49/-1 | Fallback topology ownership updates | governance edit |
| `9cedc9a` Test Ownership & Coverage Consolidation | 2026-04-24 | +226/-21 | Registry refinement | governance edit |
| `64fe7c2` Test Ownership & Coverage Consolidation | 2026-04-24 | +359/-0 | Initial file creation | governance edit |

Dominant causes:

- New consolidation cycles add their final "do not regress" locks here.
- Exact path/symbol/source-fragment assertions follow structural refactors.
- Inventory/governance JSON policy is asserted both here and in `tools/test_audit.py` tests.
- Cross-domain duplicate prevention is easier to append here than to place beside each domain owner.

## 3. Enforcement Inventory

Current test count by enforcement family:

| Family | Count | Invariant | Referenced files/fields | Surface | Churn risk |
|---|---:|---|---|---|---|
| Registry/source-of-truth | 20 | Required group ids, direct owners, neighbor roles, layer compatibility, live legality owner restrictions | `RESPONSIBILITY_REGISTRY`, `_REQUIRED_GROUP_IDS`, `LIVE_LEGALITY_GROUP_IDS`, `DOWNSTREAM_INTEGRATION_SMOKE_ONLY` | ownership source-of-truth | Stable; should remain here |
| Inventory/schema governance | 31 | Slim committed JSON omits derived fields; full inventory derives counts, markers, duplicate names, layers, registry positions | `tests/test_inventory_governance.json`, `tools/test_audit.py`, `inventory_schema_version`, `files[]`, `summary` | source-of-truth + generated artifact policy | Medium; changes when inventory schema changes |
| Cross-file duplicate policy | 1 direct plus inventory checks | Duplicate test base names must be derived and allowlisted with reasons | `_CROSS_FILE_DUPLICATE_ALLOWLIST`, `cross_file_duplicate_test_names` | duplicate policy | Medium; allowlist grows with test suite |
| Gate magnet and BD6 compression | 3 | Gate owners avoid replay/classifier/dashboard projection imports and compressed gate dependencies | guard helpers, scan allowlists, facade constants | duplicate policy + structural dependency | Medium-high; import routing changes churn |
| BV compatibility/read-cluster/smoke guards | 17 | Non-owners route through facades, compat barrels stay capped, smoke monolith avoids regrowth | `ownership_guard_bv_compatibility.py`, facade/cap constants | projection/classification/duplicate policy | High; caps and allowlists drift with migrations |
| BN gate-context guards | 32 | Gate context and preflight helpers avoid direct imports/regrowth; runtime gate entry stays narrow | `ownership_guard_bn_gate_context.py`, BN1-BN11 constants | structural dependency | High; exact imports and helper splits churn |
| Replay/projection boundary | 3 | Golden replay is projection/diagnostic neighbor, not gate owner; protected manifest parity | BI8/BG1 helpers, replay docs | replay/projection behavior | Medium; projection fields and docs churn |
| Smoke facade / phrase-layer locks | 13 | AL/BE/BJ smoke facade remains weak bridge; phrase legality split stays three-layer | AL4 maps, BE6 owners, `emission_smoke_assertions.py` | duplicate policy + diagnostic wording | Medium-high; facade public names churn |
| BJ delegate closeout locks | 90 | Gate delegates/wrappers remain collapsed; stacks call owner modules directly | `ownership_closeout_delegate_locks.py`, `game/final_emission_*`, harness scan paths | structural dependency | Very high; largest magnet source |
| BU write-path governance | 3 | Ownership write-path CSV parity and producer-stamp pairing | `ownership_write_path_governance.py`, `BU4_ownership_write_paths.csv` | source-of-truth + generated artifact policy | Medium; CSV refresh churn |
| Misc direct entrypoint locks | 4 | Owner callable presence and removed gate re-export checks | `game/final_emission_*`, helper locks | structural dependency | Medium-high |

The individual tests are listed below by family. Stable means likely to change only when policy changes. Churn-prone means likely to change during ordinary refactors/import migrations.

| Test group | Test functions | Stability |
|---|---|---|
| Core registry/inventory | `test_registry_defines_all_required_groups`; `test_inventory_schema_version_matches_audit_tool`; all `test_governance_*`; `test_derived_registry_*`; `test_inventory_block_b_schema_v2_coherence`; `test_direct_owner_general_disallowed_when_declared_layer_set`; `test_ownership_registry_governance`; `test_allowlist_entries_have_non_empty_reasons` | Mostly stable; schema-version and derived-field assertions churn with inventory policy |
| Direct-owner boundary policy | `test_final_emission_meta_projection_read_side_ownership_boundaries`; `test_ad3_gate_orchestration_direct_owner_is_final_emission_gate`; `test_ad3_downstream_integration_smoke_suites_registered_as_neighbors`; `test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner` | Stable if registry remains the source of truth |
| Duplicate and smoke split policy | `test_cross_file_duplicate_allowlist_from_derived_full_audit`; `test_al4_legality_owners_and_smoke_facade_locked`; `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge`; `test_be6_scaffold_phrase_triple_layer_split_locked` | Churn-prone where exact helper names or public symbols are asserted |
| Gate/projection guard wrappers | `test_ba7_*`; `test_bd6_*`; `test_bi8_*`; `test_bg1_*`; `test_ao5_*` | Medium churn from scan allowlists, docs phrases, and projection routing |
| BV guard wrappers | `test_bv2c_*`; `test_bv7c_*`; `test_bv10_*`; `test_bv12c_*`; `test_bv13c_*`; `test_bv14c_*`; `test_bv16c_*` | High churn from compat barrel importer counts, facade names, and import allowlists |
| BN guard wrappers | `test_bn1_*` through `test_bn11_*` | High churn from gate-context/preflight import shape |
| BJ delegate locks | `test_bj27_*` through `test_bj129_*`, including BJ70-BJ129 wrappers around `verify_*` helpers | Highest churn; mostly structural/import/call-site locks, not registry ownership |
| BU write-path locks | `test_bu8_*`; `test_bu9_*` | Medium churn with ownership write-path ledger refreshes |

Exact entrypoint enumeration by the families above:

### Misc Structural Lock

`test_audit_module`, `test_derived_registry_index_matches_live_registry`, `test_canonical_validation_layers_importable`, `test_final_emission_gate_does_not_accumulate_read_side_projection_assertions`

### Registry/Source-of-Truth

`test_registry_defines_all_required_groups`, `test_governance_rejects_duplicate_direct_owner`, `test_direct_owner_general_disallowed_when_declared_layer_set`, `test_governance_rejects_sharp_direct_owner_layer_mismatch`, `test_ownership_registry_governance`, `test_allowlist_entries_have_non_empty_reasons`, `test_final_emission_meta_projection_read_side_ownership_boundaries`, `test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers`, `test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions`, `test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons`, `test_bv2c_final_emission_meta_direct_import_allowlist_entries_have_non_empty_reasons`, `test_bv10_read_cluster_direct_import_allowlist_entries_have_non_empty_reasons`, `test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons`, `test_ad3_gate_orchestration_direct_owner_is_final_emission_gate`, `test_ad3_downstream_integration_smoke_suites_registered_as_neighbors`, `test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner`, `test_bv7c_smoke_monolith_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv12c_compat_barrel_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv13c_text_compat_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv14c_social_exchange_compat_import_guard_allowlist_entries_have_non_empty_reasons`

### Inventory/Schema Governance

`test_inventory_schema_version_matches_audit_tool`, `test_governance_inventory_contains_required_fields`, `test_governance_summary_contains_stable_metadata_only`, `test_governance_omits_cross_file_duplicate_test_names`, `test_governance_rejects_stored_cross_file_duplicate_test_names`, `test_governance_file_rows_omit_committed_per_test_rows`, `test_governance_rejects_stored_per_test_rows`, `test_governance_file_rows_omit_marker_set`, `test_governance_rejects_stored_marker_set`, `test_governance_file_rows_omit_likely_architecture_layer`, `test_governance_rejects_stored_likely_architecture_layer`, `test_governance_file_rows_omit_collected_duplicate_base_names`, `test_governance_rejects_stored_collected_duplicate_base_names`, `test_governance_file_rows_omit_pytest_collected`, `test_governance_rejects_stored_pytest_collected`, `test_governance_file_rows_omit_registry_positions`, `test_governance_committed_files_exclude_non_registry_paths`, `test_governance_committed_files_include_all_registry_paths`, `test_governance_rejects_non_registry_committed_file_row`, `test_derived_registry_paths_present_in_inventory`, `test_governance_omits_triage_aggregates`, `test_governance_rejects_stored_triage_aggregates`, `test_inventory_block_b_schema_v2_coherence`, `test_evaluator_neighbor_may_have_general_inventory_layer`, `test_governance_rejects_stored_registry_positions`, `test_governance_rejects_missing_inventory_path`, `test_inventory_per_test_rows_include_marker_set`, `test_governance_registry_paths_have_derived_marker_sets`, `test_governance_registry_paths_have_derived_architecture_layers`, `test_governance_registry_paths_have_derived_duplicate_base_names`, `test_governance_registry_paths_have_live_collected_counts`

### Duplicate Policy

`test_cross_file_duplicate_allowlist_from_derived_full_audit`

### Gate Dependency Guard

`test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners`, `test_bd6_gate_dependency_compression_guard_detects_synthetic_violation`, `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`

### BV Compatibility/Import Guard

`test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation`, `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`, `test_bv10_read_cluster_direct_import_guard_detects_synthetic_violation`, `test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades`, `test_bv7c_smoke_monolith_import_guard_detects_synthetic_violation`, `test_bv7c_smoke_monolith_import_guard_non_owners_route_through_family_facades`, `test_bv7c_emission_smoke_assertions_concentration_locked`, `test_bv12c_compat_barrel_import_guard_detects_synthetic_violation`, `test_bv12c_compat_barrel_import_guard_non_owners_route_through_domain_facades`, `test_bv12c_compat_barrel_fi_cap_locked`, `test_bv13c_text_compat_import_guard_detects_synthetic_violation`, `test_bv13c_text_compat_import_guard_non_owners_route_through_authorities`, `test_bv13c_text_compat_fi_cap_locked`, `test_bv14c_social_exchange_compat_import_guard_detects_synthetic_violation`, `test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities`, `test_bv14c_social_exchange_compat_fi_cap_locked`, `test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance`

### BN Gate-Context Guard

`test_bn1_runtime_gate_entry_guard_detects_synthetic_violation`, `test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import`, `test_bn1_runtime_delegate_seam_remains_narrow`, `test_bn2_lazy_gate_namespace_allowlist_covers_scan_files`, `test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation`, `test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg`, `test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked`, `test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation`, `test_bn3_gate_context_avoids_direct_layer_meta_owner_imports`, `test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked`, `test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation`, `test_bn4_gate_context_avoids_direct_telemetry_provenance_imports`, `test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked`, `test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation`, `test_bn5_gate_context_avoids_direct_upstream_attach_imports`, `test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked`, `test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation`, `test_bn6_gate_context_avoids_direct_turn_packet_policy_imports`, `test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked`, `test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation`, `test_bn7_gate_context_avoids_direct_interaction_inspection_imports`, `test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked`, `test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation`, `test_bn8_gate_context_avoids_direct_strict_social_routing_imports`, `test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked`, `test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation`, `test_bn9_gate_context_avoids_direct_pregate_text_imports`, `test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked`, `test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation`, `test_bn10_gate_context_routes_branch_flags_through_helper`, `test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation`, `test_bn11_gate_context_preflight_only_import_allowlist_locked`

### Replay/Projection Boundary

`test_bi8_golden_replay_ownership_boundary_is_locked`, `test_bg1_protected_replay_manifest_registry_parity`, `test_ao5_runtime_and_acceptance_projection_modules_remain_separate`

### Smoke/Phrase Split Policy

`test_al4_legality_owners_and_smoke_facade_locked`, `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge`, `test_be6_scaffold_phrase_triple_layer_split_locked`, `test_bj42_terminal_enforcement_pipeline_owner_entrypoint_locked`, `test_bj43_non_strict_layer_stack_owner_entrypoint_locked`, `test_bj44_strict_social_composition_trunk_owner_entrypoint_locked`, `test_bj45_generic_exit_owner_entrypoints_locked`, `test_bj46_fem_assembly_owner_entrypoints_locked`, `test_bj47_fem_assembly_merge_gate_layer_metas_owner_entrypoint_locked`, `test_bj48_fast_fallback_neutral_composition_layer_owner_entrypoint_locked`, `test_bj49_gate_context_owner_entrypoint_locked`, `test_bj41_finalize_emission_output_owner_entrypoint_locked`, `test_bj40_acceptance_quality_n4_floor_seam_owner_entrypoint_locked`

### BJ Delegate/Owner Lock

`test_bj27_referential_clarity_enforcement_owner_entrypoint_locked`, `test_bj50_visibility_enforcement_gate_wrapper_collapsed`, `test_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly`, `test_bj28_speaker_contract_enforcement_owner_entrypoint_locked`, `test_bj29_interaction_continuity_emission_owner_entrypoint_locked`, `test_bj51_interaction_continuity_gate_wrappers_fully_collapsed`, `test_bj52_fallback_provenance_gate_wrappers_collapsed`, `test_bj53_referent_clarity_pre_finalize_gate_wrapper_collapsed`, `test_bj54_narration_constraint_debug_merge_gate_wrapper_collapsed`, `test_bj55_gate_fem_text_fingerprint_helper_collapsed`, `test_bj56_scene_opening_finalize_delegators_collapsed`, `test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_collapsed`, `test_bj30_dialogue_social_plan_strict_social_enforcement_owner_entrypoint_locked`, `test_bj59_dialogue_social_plan_gate_delegators_collapsed`, `test_bj60_sealed_fallback_selector_gate_delegator_collapsed`, `test_bj61_sealed_fallback_stamp_gate_delegators_collapsed`, `test_bj62_generic_exit_fem_assembly_calls_owner_directly`, `test_bj63_strict_social_stack_fem_assembly_calls_owner_directly`, `test_bj64_non_strict_stack_opening_rt_promotion_calls_owner_directly`, `test_bj65_stacks_opening_upstream_prepare_observability_merge_calls_owner_directly`, `test_bj31_tone_escalation_layer_owner_entrypoint_locked`, `test_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly`, `test_bj32_narrative_authority_layer_owner_entrypoint_locked`, `test_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly`, `test_bj58_contract_resolver_gate_delegators_collapsed`, `test_bj33_anti_railroading_layer_owner_entrypoint_locked`, `test_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly`, `test_bj34_context_separation_layer_owner_entrypoint_locked`, `test_bj82_ownership_registry_stacks_call_context_separation_owner_directly`, `test_bj35_player_facing_narration_purity_layer_owner_entrypoint_locked`, `test_bj83_ownership_registry_stacks_call_narration_purity_owner_directly`, `test_bj36_answer_shape_primacy_layer_owner_entrypoint_locked`, `test_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly`, `test_bj37_scene_state_anchor_layer_owner_entrypoint_locked`, `test_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly`, `test_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly`, `test_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly`, `test_bj69_ownership_registry_exit_stacks_call_terminal_finalize_owners_directly`, `test_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly`, `test_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly`, `test_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly`, `test_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly`, `test_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly`, `test_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly`, `test_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly`, `test_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly`, `test_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly`, `test_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly`, `test_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly`, `test_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly`, `test_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly`, `test_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly`, `test_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly`, `test_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly`, `test_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly`, `test_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly`, `test_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly`, `test_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly`, `test_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly`, `test_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly`, `test_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly`, `test_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly`, `test_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly`, `test_bj111_ownership_registry_callers_use_normalize_text_owner_directly`, `test_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly`, `test_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly`, `test_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly`, `test_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly`, `test_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly`, `test_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly`, `test_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate`, `test_bj119_ownership_registry_stage_diff_telemetry_not_on_gate`, `test_bj120_ownership_registry_harness_patches_canonical_owner_seams`, `test_bj121_ownership_registry_strict_social_build_patches_use_stack_seam`, `test_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings`, `test_bj123_ownership_registry_harness_patches_no_stale_feg_seams`, `test_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports`, `test_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate`, `test_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate`, `test_bj127_ownership_registry_global_stale_gate_harness_scan`, `test_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports`, `test_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked`, `test_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly`, `test_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly`, `test_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly`, `test_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly`, `test_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly`, `test_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly`, `test_bj39_response_type_contract_owner_entrypoint_locked`, `test_bj38_fallback_debug_merge_helpers_live_on_repairs_owner`

### BU Write-Path Governance

`test_bu8_bu4_production_ownership_write_paths_parity_locked`, `test_bu8_attach_realization_fallback_family_producer_stamp_pairing_locked`, `test_bu9_visibility_fallback_producer_stamp_pairing_locked`

## 4. Duplicate Enforcement Check

Overlapping enforcement found:

| Overlap area | Registry-side enforcement | Other enforcement | Duplication risk |
|---|---|---|---|
| Inventory JSON shape and drift | `tests/test_ownership_registry.py` inventory tests | `tests/test_test_audit_tool.py`, `tools/test_audit.py --check` | High. Same slim/derived-field policy is tested in both places. Keep registry integration, move synthetic mutation tests to tool tests. |
| Cross-file duplicate names | registry allowlist tests and governance errors | `tests/test_test_audit_tool.py::test_validate_derived_cross_file_duplicate_governance_uses_allowlist` | Medium. One should own allowlist semantics; registry should only consume result. |
| Replay projection boundary | BI8/BG1/AO5 registry locks | `tests/test_golden_replay_projection*.py`, `tests/test_golden_replay_projection_governance.py`, `docs/testing/protected_replay_manifest.md` checks | Medium-high. Projection tests should own projection schema/manifest; registry should only state neighbor status. |
| Diagnostic/classifier/dashboard ownership fields | BV10/BV2C read-cluster guards and replay notes | `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_*.py`, split-owner acceptance matrix tests | Medium. Registry currently protects import routing for consumers that have their own contract tests. |
| Smoke facade and phrase split | AL4/BE6/BJ4 registry locks | `tests/helpers/emission_smoke_assertions.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_output_sanitizer.py`, `tests/test_golden_replay_projection*.py` | High. The split is legitimate, but exact smoke facade symbol locks are not registry-specific. |
| Gate delegate/wrapper collapse | 90 BJ tests in registry file | focused owner tests such as `tests/test_final_emission_gate.py`, `tests/test_final_emission_meta.py`, `tests/test_final_emission_*` plus helper `gate_thin_boundary_locks.py` | High. These are structural owner locks, not direct-owner registry locks. |
| BN gate-context imports | BN tests in registry file | `tests/ownership_guard_bn_gate_context.py` pure helper only; relevant production files under `game/final_emission_gate_context.py` and preflight modules | Medium. Logic already extracted; pytest entrypoints could move to `tests/test_gate_context_ownership.py`. |
| BV compat caps | BV tests in registry file | focused facade/delegate tests such as `test_bv14a_social_exchange_emission_facade_delegates.py`, projection module tests | Medium-high. Cap enforcement belongs nearer compat/facade owner tests. |
| Ownership write paths | BU8/BU9 registry locks | `tests/helpers/ownership_write_path_governance.py`, BU4 CSV/docs | Medium. Registry need not own producer-stamp pairing details. |

## 5. Churn Pattern Diagnosis

| Diagnosis | Applies? | Evidence |
|---|---|---|
| True registry owner | Yes | `RESPONSIBILITY_REGISTRY`, group ids, direct-owner uniqueness, neighbor roles, live-legality owner restrictions, inventory path parity are legitimate registry duties. |
| Catch-all governance test | Yes | 217 tests span inventory schema, replay boundaries, smoke facade, import compression, compat barrels, delegate collapse, write-path ledgers, and docs phrase locks. |
| Proxy for missing policy/schema tests | Partly | Several synthetic mutation tests for inventory/duplicates could live in `tests/test_test_audit_tool.py`; BU write-path rules could live in a dedicated ownership-write-path test file. |
| Diagnostic wording lock | Partly | BI8 documentation phrase checks, AL/BE/BJ facade naming checks, and exact failure text fragments lock wording/source strings beyond registry identity. |
| Golden-file synchronization point | Partly | BG1 protected replay manifest parity and BU CSV parity make the registry test fail on generated artifact refreshes. |
| Structural dependency magnet | Strongly yes | BJ, BN, BD, BV tests assert exact imports, wrappers, call sites, facade caps, and scan allowlists. These are the largest and most churn-prone sections. |

Governance Magnet Pressure is therefore still high, but narrower than before CH. The pressure is now concentrated in pytest entrypoint ownership rather than implementation logic.

## 6. Candidate Stabilization Paths

1. Keep `tests/test_ownership_registry.py` to registry and inventory integration only.
   - Files affected: `tests/test_ownership_registry.py`, possibly `tests/ownership_registry_contract.py`, `tests/ownership_inventory_governance.py`.
   - Benefit: makes the file a stable governance owner instead of a universal lock host.
   - Risk: Low if moved tests retain names/coverage markers.
   - Own block: Yes.

2. Move BJ delegate closeout entrypoints to a focused test file.
   - Files affected: new `tests/test_gate_delegate_closeout_locks.py` or similar, `tests/ownership_closeout_delegate_locks.py`, `tests/test_ownership_registry.py`.
   - Benefit: removes the largest churn family, about 90 tests, from registry pressure.
   - Risk: Low-medium. Need preserve CI collection and marker behavior.
   - Own block: Yes.

3. Move BN gate-context guard entrypoints beside the BN helper.
   - Files affected: new `tests/test_gate_context_ownership_guards.py`, `tests/ownership_guard_bn_gate_context.py`, `tests/test_ownership_registry.py`.
   - Benefit: isolates import/preflight structural churn to the gate-context owner boundary.
   - Risk: Low. Logic is already extracted.
   - Own block: Yes.

4. Split BV/BD compatibility and import-cap entrypoints into focused governance tests.
   - Files affected: new `tests/test_compat_import_governance.py` or per-domain files, `tests/ownership_guard_bv_compatibility.py`, `tests/ownership_guard_bd_dependency_compression.py`, `tests/test_ownership_registry.py`.
   - Benefit: stops facade/cap/importer churn from touching the registry owner.
   - Risk: Medium. Some allowlists name `tests/test_ownership_registry.py`; update allowlists carefully.
   - Own block: Yes.

5. Move generated-artifact parity and diagnostic wording locks to artifact/projection owner suites.
   - Files affected: `tests/test_golden_replay_projection_governance.py`, `tests/test_test_audit_tool.py`, a possible `tests/test_ownership_write_path_governance.py`, `tests/test_ownership_registry.py`.
   - Benefit: reduces fixture/snapshot churn and diagnostic string alignment in the registry file.
   - Risk: Medium. Must keep one registry-level assertion that these owners are registered correctly.
   - Own block: Yes.

Recommended implementation sequence:

1. BJ delegate entrypoint move.
2. BN gate-context entrypoint move.
3. BV/BD compat entrypoint move.
4. Inventory synthetic mutation cleanup.
5. Replay/artifact wording cleanup.

## 7. Required Handoff Files

Minimum files to pass to ChatGPT for planning:

- `tests/test_ownership_registry.py`
- `tests/ownership_registry_contract.py`
- `tests/ownership_inventory_governance.py`
- `tests/test_inventory_governance.json`
- `tools/test_audit.py`
- `tests/test_test_audit_tool.py`
- `tests/ownership_closeout_delegate_locks.py`
- `tests/ownership_guard_bn_gate_context.py`
- `tests/ownership_guard_bv_compatibility.py`
- `tests/ownership_guard_bd_dependency_compression.py`
- `tests/ownership_guard_gate_magnet.py`
- `tests/ownership_guard_bi8_golden_replay_boundary.py`
- `tests/ownership_guard_bv16c_terminal_monkeypatch.py`
- `tests/helpers/gate_thin_boundary_locks.py`
- `tests/helpers/ownership_write_path_governance.py`
- `tests/test_golden_replay_projection_governance.py`
- `tests/test_golden_replay_projection*.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_*.py`
- `tests/test_split_owner_acceptance_matrix_contract.py`
- `tests/test_output_sanitizer.py`
- `tests/test_turn_pipeline_shared.py`
- `tests/test_final_emission_meta.py`
- `tests/test_social_exchange_emission.py`
- `tests/README_TESTS.md`
- `docs/convergence_ci_inventory.md`
- `docs/architecture_ownership_ledger.md`
- `docs/audits/CH_governance_hub_redistribution_discovery.md`
- `docs/audits/CH*_summary.md` or the specific CH1-CH13 extraction summaries

Useful recent git summaries:

- `git log --numstat --date=short --pretty=format:"COMMIT %h %ad %s" -- tests/test_ownership_registry.py`
- `git show --name-status --oneline --stat 85855df`
- `git show --name-status --oneline --stat 9b62d17`

## Accidental or Required Changes

None. This pass only adds this discovery report.
