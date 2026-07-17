# CJ — Foundation Readiness Closeout Discovery

## Executive Summary

The repository currently appears closest to **Mixed Development**.

This is provisional. The strongest evidence for mixed development is that recent CE/CF/CG/CH/CI work reduced several high-risk monoliths into focused modules, registries, and contract tests, and the targeted non-registry readiness slice passes. The strongest evidence against feature-first development is that `tests/test_ownership_registry.py` still fails as a broad governance hub and remains a default landing zone for unrelated architecture locks.

## Evidence Sources

- `CD_ownership_registry_concentration_audit_discovery.md`
- `CE_golden_replay_concentration_audit_discovery.md`
- `CE1_replay_maintenance_metrics_summary.md`
- `CE2_3_recurrence_module_extraction_summary.md`
- `CE3_replay_bug_recurrence_decomposition_summary.md`
- `CE4_fallback_projection_test_decomposition_summary.md`
- `CE5_acceptance_projection_ownership_split_summary.md`
- `CE6_generated_replay_artifact_churn_reduction_summary.md`
- `docs/audits/CF_replay_projection_responsibility_discovery.md`
- `docs/audits/CF1_projection_precedence_matrix.md`
- `docs/audits/CF2_protected_field_source_default_matrix.md`
- `docs/audits/CF3_raw_normalized_fem_field_matrix.md`
- `docs/audits/CF4_trace_nest_dotted_path_contract.md`
- `docs/audits/CF5_projection_test_failure_locality.md`
- `docs/audits/CF6_generated_projection_artifact_governance.md`
- `docs/audits/CF7_synthetic_row_classifier_evidence_bridge.md`
- `docs/audits/CG_failure_classification_synchronization_discovery.md`
- `docs/audits/CG_failure_classification_cost_closeout.md`
- `docs/audits/CG_failure_classification_authority_registry.md`
- `docs/audits/CG_recurrence_taxonomy_registry.md`
- `docs/audits/CG_attribution_contract_registry.md`
- `docs/audits/CG_recurrence_key_stability_review.md`
- `docs/audits/CH_governance_hub_redistribution_discovery.md`
- `docs/audits/CH1_ownership_registry_contract_extraction_summary.md`
- `docs/audits/CH2_ownership_guard_locality_pilot_summary.md`
- `docs/audits/CH3_bn_gate_context_extraction_summary.md`
- `docs/audits/CH4_bv_read_cluster_guard_extraction_summary.md`
- `docs/audits/CH5_bv_compat_guard_wiring_cleanup_summary.md`
- `docs/audits/CH6_bd6_dependency_compression_extraction_summary.md`
- `docs/audits/CH7_gate_magnet_guard_extraction_summary.md`
- `docs/audits/CH8_bv16c_terminal_monkeypatch_extraction_summary.md`
- `docs/audits/CH9_bi8_golden_replay_boundary_extraction_summary.md`
- `docs/audits/CH10_inventory_governance_orchestration_extraction_summary.md`
- `docs/audits/CH11_delegate_closeout_lock_extraction_summary.md`
- `docs/audits/CH12_post_extraction_hotspot_remeasurement.md`
- `docs/audits/CH13_ownership_helper_wiring_closeout_summary.md`
- `CI_corrective_cohort_validation_2_discovery.md`
- `docs/audits/CI_corrective_cohort_validation_2_closeout.md`
- `CI_6_hotspot_compression_operational_readiness_closeout.md`
- `CI_8_hotspot_compression_measurement_workflow_refinement.md`
- `CI_9_hotspot_compression_workflow_closeout.md`
- `docs/audits/CK_hotspot_compression_watch.md`
- `docs/processes/hotspot_compression_measurement_standard.md`
- `docs/processes/hotspot_compression_watch_process.md`
- `artifacts/ck1_hotspot_compression_report.json`
- Recent commits reviewed with `git log --oneline -20` and `git show --stat --name-only --oneline 1f3899b 1bc28f7 3709523 85855df 5ea6608 c98dfa6 66b8b32 ba8b29a 247e634`.
- Targeted test commands listed in the Test Results section.

## Area 1 — Governance Concentration

- Risk rating: **High**
- Main files:
  - `tests/test_ownership_registry.py`
  - `tests/ownership_registry_contract.py`
  - `tests/ownership_inventory_governance.py`
  - `tests/ownership_closeout_delegate_locks.py`
  - `tests/ownership_guard_bd_dependency_compression.py`
  - `tests/ownership_guard_bi8_golden_replay_boundary.py`
  - `tests/ownership_guard_bn_gate_context.py`
  - `tests/ownership_guard_bv16c_terminal_monkeypatch.py`
  - `tests/ownership_guard_bv_compatibility.py`
  - `tests/ownership_guard_gate_magnet.py`
  - `tests/test_inventory_governance.json`
  - `tools/test_audit.py`
  - `docs/architecture_ownership_ledger.md`
  - `game/final_emission_ownership_schema.py`
  - `game/ownership_projection_views.py`
  - `game/attribution_read_views.py`
  - `game/final_emission_owner_bucket_views.py`
- Evidence:
  - CD classified ownership governance as mildly over-centralized, with `tests/test_ownership_registry.py` at 5,959 lines, 22 commits, and several 600-1,800 line cycle expansions.
  - CH ranked `tests/test_ownership_registry.py` as the top governance hub with Severe local risk, despite overall CH hotspot concentration being High rather than Severe.
  - CH redistributed much of the registry surface into helper modules (`ownership_registry_contract.py`, `ownership_inventory_governance.py`, and focused guard helpers), so recent work reduced concentration rather than only measuring it.
  - The current registry test still fails: 10 failures and 12 setup errors in the targeted run. Failures include dependency-compression import violations, compatibility-barrel FI cap locks, undocumented intentional hubs, a stale gate harness fragment, and BU write-path/stamp pairing locks.
- Remaining concern:
  - The registry has become both policy source and broad architecture lock runner. Even after CH extraction, the central test remains a high-blast-radius gate.
  - The internal full-inventory collection errors also show that registry validation still depends on broad suite collection state.
- Feature-readiness implication:
  - This is **blocking feature-first development**. Feature work can proceed only in mixed mode if it avoids ownership/governance surfaces or includes narrow governance fixes as part of the same block.

## Area 2 — Replay Concentration

- Risk rating: **Medium**
- Main files:
  - `tests/test_golden_replay.py`
  - `tests/test_golden_replay_structural_invariants.py`
  - `tests/test_golden_replay_projection.py`
  - `tests/test_golden_replay_fallback_projection.py`
  - `tests/test_golden_replay_fallback_opening_projection.py`
  - `tests/test_golden_replay_fallback_sealed_projection.py`
  - `tests/test_golden_replay_fallback_visibility_projection.py`
  - `tests/test_golden_replay_fallback_sanitizer_projection.py`
  - `tests/test_golden_replay_fallback_upstream_projection.py`
  - `tests/test_golden_replay_fallback_upstream_fast_projection.py`
  - `tests/helpers/golden_replay.py`
  - `tests/helpers/golden_replay_api.py`
  - `tests/helpers/golden_replay_fixtures.py`
  - `tests/helpers/golden_replay_profiles.py`
  - `tests/helpers/protected_replay_registry.py`
  - `docs/testing/protected_replay_manifest.md`
  - `tools/refresh_protected_replay_manifest.py`
  - `artifacts/golden_replay/artifact_manifest.md`
- Evidence:
  - CE found historical replay concentration in `tests/test_golden_replay.py`, but the current file is a small redirect stub after decomposition.
  - Current protected scenario ownership is distributed across structural invariants, direct seam, long-session, scenario-spine, projection, fallback projection, helper contracts, bridge, and trend tests.
  - CE still identified residual hubs: `tests/helpers/golden_replay.py`, `tests/helpers/failure_dashboard_report.py`, `tests/helpers/golden_replay_projection.py`, `game/final_emission_replay_projection.py`, and the protected manifest/refresh pair.
  - CE4 split fallback projection tests into family-specific files, and CE6 classified replay artifacts into retention families, reducing review noise for generated outputs.
- Remaining concern:
  - Replay is no longer a single-test bottleneck, but helper, diagnostics, manifest, and artifact-generation surfaces remain coordinated.
  - Generated replay artifacts can still obscure semantic review if not separated from advisory output refreshes.
- Feature-readiness implication:
  - Replay foundation work can continue alongside careful feature work. New features touching protected replay fields or generated artifacts should run through mixed development and include the relevant projection/replay contract tests.

## Area 3 — Projection Concentration

- Risk rating: **Medium-High**
- Main files:
  - `tests/helpers/golden_replay_projection.py`
  - `tests/helpers/golden_replay_projection_fields.py`
  - `tests/helpers/golden_replay_projection_extractors.py`
  - `tests/helpers/golden_replay_projection_fallbacks.py`
  - `tests/helpers/golden_replay_projection_manifest.py`
  - `tests/helpers/golden_replay_projection_speaker.py`
  - `game/final_emission_replay_projection.py`
  - `game/final_emission_meta.py`
  - `game/final_emission_speaker_observation.py`
  - `game/runtime_lineage_telemetry.py`
  - `tests/test_golden_replay_projection.py`
  - `tests/test_golden_replay_projection_modules.py`
  - `tests/test_cf1_fallback_family_precedence.py`
  - `tests/test_cf1_route_and_trace_precedence.py`
  - `tests/test_cf1_runtime_lineage_precedence.py`
  - `tests/test_cf1_speaker_projection_precedence.py`
  - `tests/test_cf2_protected_field_routing.py`
  - `tests/test_cf3_raw_normalized_fem_field_matrix.py`
  - `tests/test_cf4_trace_nest_dotted_path_contract.py`
  - `tests/test_cf6_generated_projection_artifact_governance.py`
  - `tests/test_cf7_synthetic_row_classifier_evidence_bridge.py`
- Evidence:
  - CF found replay projection centralized at the acceptance assembly boundary but fragmented across input owners.
  - CE5 split the former large acceptance projection into field, extractor, fallback, manifest, speaker, and facade modules.
  - The extractor remained a major policy owner, and runtime/acceptance dual projection still requires careful separation.
  - CF follow-up artifacts and tests now exist for precedence, field source/default routing, raw/normalized FEM fields, trace nesting, generated projection artifacts, and synthetic classifier evidence.
  - The targeted projection tests passed in the non-registry slice.
- Remaining concern:
  - `project_turn_observation` remains the acceptance assembler. That is acceptable API concentration, but a new protected field still fans into schema, extraction, defaults, manifest, classifier evidence, and tests.
  - Runtime projection remains broad because source-family maps, mutation classification, owner projection, and event assembly share `game/final_emission_replay_projection.py`.
- Feature-readiness implication:
  - Projection work should remain mixed-mode. Features that add or rename projected fields need source/default ownership and generated-artifact classification in the same block.

## Area 4 — Classification Concentration

- Risk rating: **Medium**
- Main files:
  - `tests/failure_classification_contract.py`
  - `tests/helpers/failure_classifier.py`
  - `tests/helpers/failure_classification_sync.py`
  - `tests/helpers/failure_classification_alignment.py`
  - `tests/helpers/failure_classification_builders.py`
  - `tests/helpers/failure_classification_dashboard_expectations.py`
  - `tests/helpers/failure_classification_split_owner.py`
  - `tests/helpers/failure_dashboard_fixtures.py`
  - `tests/helpers/failure_dashboard_report.py`
  - `tests/helpers/failure_dashboard_recurrence.py`
  - `tests/helpers/replay_bug_recurrence_events.py`
  - `tests/helpers/replay_bug_recurrence_history.py`
  - `tests/helpers/replay_bug_recurrence_statistics.py`
  - `tests/helpers/replay_bug_recurrence_serialization.py`
  - `tests/helpers/attribution_contract.py`
  - `tests/test_failure_classification_contract.py`
  - `tests/test_failure_classifier.py`
  - `tests/test_failure_dashboard_controlled_failures.py`
  - `tests/test_failure_dashboard_recurrence.py`
  - `tests/test_replay_bug_class_recurrence.py`
  - `artifacts/golden_replay/bug_recurrence_history.json`
  - `artifacts/golden_replay/bug_recurrence_history.md`
- Evidence:
  - CG measured 18 core files and 25,575 LOC participating in failure-classification contracts.
  - Ordinary taxonomy changes historically fan out across 3-7 core files; split-owner changes can touch 6+ surfaces plus runtime and generated reports.
  - CG and later closeout artifacts clarified authority across failure rows, classifier behavior, protected evidence, runtime owner vocabulary, attribution, recurrence identity, and recurrence analytics.
  - CE/CG split recurrence and sync responsibilities into focused modules, reducing raw monolith concentration while keeping compatibility facades.
  - The targeted classification tests passed in the non-registry slice.
- Remaining concern:
  - Recurrence analytics remain large and sensitive; `recurrence:v1` identity still embeds mutable `field_path` and `investigate_first` values.
  - Some dashboard and recurrence fixtures remain intentionally exact and can amplify otherwise small taxonomy changes.
- Feature-readiness implication:
  - Classification is no longer an obvious full-stop blocker, but changes to taxonomy, owner routing, or recurrence identity must be treated as foundation-adjacent mixed work.

## Area 5 — Corrective Locality

- Risk rating: **Medium**
- Main files:
  - `docs/audits/CA_corrective_change_locality_cohort.csv`
  - `docs/audits/CA_corrective_change_locality_candidates.csv`
  - `docs/baselines/ca_corrective_locality_baseline.md`
  - `docs/baselines/ca_corrective_locality_baseline.json`
  - `artifacts/ca3_corrective_locality_report.json`
  - `artifacts/ca3_corrective_locality_report.md`
  - `artifacts/ca7_corrective_fix_absence_report.json`
  - `artifacts/ca8_corrective_fix_availability_report.json`
  - `artifacts/ca9_embedded_corrective_attribution_report.json`
  - `artifacts/ca10_corrective_prevention_effectiveness_report.json`
  - `artifacts/ca11_corrective_fix_watch_report.json`
  - `tools/corrective_change_locality.py`
  - `tools/corrective_change_locality_report.py`
  - `tools/corrective_change_candidate_inventory.py`
  - `tools/corrective_fix_watch.py`
  - `tools/corrective_prevention_effectiveness_report.py`
  - `tests/helpers/corrective_change_locality_cohort.py`
  - `tests/helpers/corrective_change_locality_classifier.py`
  - `tests/test_corrective_locality_report.py`
  - `tests/test_corrective_change_locality_cohort.py`
  - `tests/test_corrective_fix_watch.py`
  - `tests/test_corrective_prevention_effectiveness.py`
- Evidence:
  - CI corrective validation inspected the strict post-CA range and found zero qualifying real corrective fixes after `5f0ad53`.
  - That means recent audit/governance/decomposition commits cannot prove corrective locality improved or worsened; they were excluded by the corrective-fix rules.
  - CI still identified burden patterns in the excluded range: replay/projection churn, attribution/contract synchronization, golden replay artifact churn, and governance registry involvement.
  - Corrective locality tests passed in the targeted non-registry slice.
- Remaining concern:
  - The evidence is insufficient to declare corrective locality solved because the strict post-CA window lacks qualifying corrective-fix intake.
  - The next true corrective fixes should be measured against the CA baseline and CK hotspot process.
- Feature-readiness implication:
  - Corrective locality does not block all feature work, but feature work should remain mixed until at least a few real corrective fixes demonstrate local edits rather than broad governance/replay/classification fanout.

## Hotspot Summary

| File / area | Cycles involved | Why it matters | Current risk | Recommendation |
|---|---|---|---|---|
| `tests/test_ownership_registry.py` | CD, CH, CI, CK | Central responsibility registry, inventory validator, import/fan-in guard, and historical architecture lock surface | High | Continue foundation work on registry failure locality before feature-first mode. |
| Ownership guard helper family | CH | Recent extraction reduced central-file size and improved routing | Medium | Keep the focused helpers; fix current registry failures without re-centralizing. |
| `tools/test_audit.py` + `tests/test_inventory_governance.json` | CD, CH | Registry inventory relies on full pytest collection and committed governance JSON parity | Medium-High | Treat inventory collection errors as governance-locality evidence; isolate collection diagnostics. |
| `tests/helpers/golden_replay.py` | CE, CF, CH | Replay orchestration and assertion hub after monolith split | Medium | Continue facade adoption and family-specific assertions. |
| `tests/helpers/failure_dashboard_report.py` and extracted dashboard modules | CE, CG, CH | Diagnostic/report fanout and generated artifacts | Medium | Keep family extraction and generated-output retention classes. |
| `tests/helpers/golden_replay_projection_*` | CE, CF, CH | 41-field protected observation schema and acceptance projection | Medium-High | Continue field source/default and precedence matrix work. |
| `game/final_emission_replay_projection.py` | CD, CE, CF, CG, CH | Runtime lineage/source/owner projection feeds replay, classification, attribution, and transcript tooling | Medium-High | Split map contracts from event assembly once registry failures are contained. |
| `game/final_emission_meta.py` | CD, CF, CG, CH | Runtime metadata authority with broad downstream projection/classification impact | High | Keep feature changes narrow and paired with first-owner tests. |
| Failure classification contract/classifier/sync family | CG, CH | Taxonomy changes historically fan out across contract, classifier, fixtures, dashboard, recurrence, and artifacts | Medium | Use authority registries and derived expectations; avoid ad hoc taxonomy growth. |
| Recurrence history/statistics/test family | CE, CG, CH | Large residual analytics and recurrence-key sensitivity | Medium-High latent | Build recurrence taxonomy manifest and v1 migration detector before major recurrence changes. |
| CK hotspot compression process | CI, CK | Operational measurement now exists and tests pass | Low-Medium | Use it at qualifying maintenance closeouts; no immediate feature blocker. |
| Corrective cohort intake | CA, CI | No strict post-CA corrective fixes, so locality trend is not yet measured | Medium | Continue watch; evaluate the next real corrective fixes against CA baseline. |

## Test Results

Commands run:

1. `$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_golden_replay_projection_modules.py tests/test_cf6_generated_projection_artifact_governance.py tests/test_failure_classification_contract.py tests/test_failure_classifier.py tests/test_corrective_locality_report.py tests/test_corrective_change_locality_cohort.py tests/test_ck_hotspot_compression_report.py -q --tb=short --basetemp=codex_pytest_tmp_cj_verify1`
   - Result: **Passed**, 210 tests.
   - Readiness relevance: supports that projection packaging, generated projection artifact governance, failure classification, corrective locality, corrective cohort, and CK hotspot compression contracts are currently healthy outside the central ownership registry.

2. `$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_ownership_registry.py -q --tb=short --basetemp=codex_pytest_tmp_cj_verify2`
   - Result: **Failed**.
   - Failures captured:
     - `test_governance_rejects_duplicate_direct_owner`
     - `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`
     - `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`
     - `test_bv12c_compat_barrel_fi_cap_locked`
     - `test_bv13c_text_compat_fi_cap_locked`
     - `test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities`
     - `test_bv14c_social_exchange_compat_fi_cap_locked`
     - `test_bj127_ownership_registry_global_stale_gate_harness_scan`
     - `test_bu8_bu4_production_ownership_write_paths_parity_locked`
     - `test_bu9_visibility_fallback_producer_stamp_pairing_locked`
   - Setup errors captured:
     - `test_governance_committed_files_exclude_non_registry_paths`
     - `test_derived_registry_paths_present_in_inventory`
     - `test_inventory_block_b_schema_v2_coherence`
     - `test_evaluator_neighbor_may_have_general_inventory_layer`
     - `test_governance_rejects_sharp_direct_owner_layer_mismatch`
     - `test_inventory_per_test_rows_include_marker_set`
     - `test_governance_registry_paths_have_derived_marker_sets`
     - `test_governance_registry_paths_have_derived_architecture_layers`
     - `test_governance_registry_paths_have_derived_duplicate_base_names`
     - `test_governance_registry_paths_have_live_collected_counts`
     - `test_cross_file_duplicate_allowlist_from_derived_full_audit`
     - `test_ownership_registry_governance`
   - Short failure reasons:
     - gate dependency compression-guard import violations;
     - BV2C final-emission-meta direct-import violations;
     - intentional domain hubs not documented in registry;
     - BV14C social-exchange compatibility import violations;
     - `tests/ownership_closeout_delegate_locks.py` newly imports `social_exchange_emission`;
     - stale final-emission-gate monkeypatch fragment still present;
     - internal inventory setup raises `RuntimeError` from full pytest collection output.
   - Readiness relevance: directly related to foundation readiness. This is the clearest reason not to recommend feature-first development.

## Readiness Recommendation Options

### Option A — Continue Foundation Work

Evidence supporting this would be:

- `tests/test_ownership_registry.py` continues to fail.
- Registry failures require broad edits across unrelated governance, gate, final-emission, social-exchange, and BU write-path surfaces.
- Projection/classification/corrective tests begin failing outside the registry slice.
- CK hotspot reports show repeated high fanout in the same coordination hubs.
- The next true corrective fixes require broad governance/replay/classification edits rather than local patches.

### Option B — Mixed Development

Evidence supporting this is currently strongest:

- Non-registry projection, classification, corrective-locality, corrective-cohort, and CK tests pass.
- CE, CF, CG, CH, and CI reduced or operationalized major concentration risks.
- Replay scenario ownership and fallback projection tests are much more distributed than the historical monolith state.
- Classification authority is documented and split, even though taxonomy changes remain coordinated.
- Governance registry failures remain active and feature-relevant, preventing a clean feature-first recommendation.

### Option C — Feature-First Development

Evidence that would support this later:

- `tests/test_ownership_registry.py` passes with a clean full-inventory collection.
- CK measurements over multiple qualifying closeouts show stable or falling hotspot fanout.
- At least a few real corrective fixes land locally against the CA baseline.
- Protected replay/projection changes can be made without touching broad helper, manifest, classifier, recurrence, and governance surfaces together.
- Governance edits become rare, localized, and mostly generated/registry updates rather than broad policy debugging.

## Provisional Recommendation

**Mixed Development**

- The non-registry foundation contracts tested here pass, which is enough to allow guarded feature work.
- Governance concentration is still too active and too central to recommend feature-first development.
- Replay concentration has been materially reduced at the scenario/test level, but helper/projection/artifact hubs still need watch discipline.
- Projection and classification work are no longer raw monolith problems, but they remain cross-contract domains where feature changes can easily become foundation changes.
- Corrective locality is not yet proven after CA because no strict post-CA corrective fixes qualified for measurement.
- CK operational measurement exists and passes its targeted contracts, so hotspot work can continue as an operational track alongside carefully scoped features.

## Recommended Next Blocks

1. **CJ-1 — Ownership registry failure-locality closeout**
   - Fix or reclassify the current `tests/test_ownership_registry.py` failures without re-centralizing extracted CH helpers.
   - Success: the registry test passes with an explicit basetemp and failure messages route to focused helper/domain owners.

2. **CJ-2 — Registry inventory collection diagnostic**
   - Isolate why `tools/test_audit.py` full collection is surfacing as a setup `RuntimeError` inside registry tests.
   - Success: inventory failures report concise collection diagnostics rather than dumping the full node list.

3. **CJ-3 — First post-CA corrective locality sample**
   - Wait for or select the next real corrective fix and measure files touched, hub involvement, replay/classification/projection fanout, and CA-baseline delta.
   - Success: at least one real corrective fix demonstrates local or intentionally bounded edits.

4. **CJ-4 — CK measurement at next qualifying closeout**
   - Run `tools/ck_hotspot_compression_report.py` per the CK runbook after the next maintenance cycle closes.
   - Success: CK-GIT/CK-FI values are appended to `docs/audits/CK_hotspot_compression_watch.md` and compared against current hotspot claims.

5. **CJ-5 — Feature guardrail pilot**
   - Choose one low-risk feature block that avoids ownership registry, protected projection schema, recurrence identity, and split-owner taxonomy.
   - Success: the feature lands with local tests and no broad governance/replay/classification edits, giving evidence toward eventual feature-first readiness.
