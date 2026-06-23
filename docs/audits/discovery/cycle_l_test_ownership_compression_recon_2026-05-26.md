# Cycle L - Test Ownership Compression Recon

Date: 2026-05-26
Scope: Read-only reconnaissance. No production code or test code changed.

## 1. Executive Summary

### Current test-suite shape

The repository currently collects **4,209 tests across 304 test modules**. It
already contains a partial ownership system:

- `tests/test_ownership_registry.py` declares direct owners and neighbor roles
  for core engine, planner, GPT/expression, gate, sanitizer, social, transcript,
  gauntlet, and evaluator responsibilities.
- Several high-value suites state their intended role in module comments:
  `tests/test_final_emission_gate.py` owns gate orchestration,
  `tests/test_final_emission_repairs.py` owns repair semantics,
  `tests/test_output_sanitizer.py` owns final string cleanup,
  `tests/test_failure_classifier.py` owns diagnostic locality, and
  `tests/test_golden_replay.py` treats repeated projection fields as replay
  contract locks.
- Cycle J introduced `tests/test_final_emission_opening_fallback.py` as a direct
  test surface for the extracted opening-selection/fail-closed adapter, but the
  older gate suite still contains deep assertions over the same prepared versus
  fail-closed results.
- Cycle K promoted protected golden replay to a CI acceptance lane and added
  failure-reporting policy and artifact work. Replay is therefore no longer a
  good first compression target unless coverage is clearly only diagnostic.

### Biggest ownership ambiguity seams

| Seam | Why attribution is ambiguous today | Primary evidence |
| --- | --- | --- |
| Opening fallback selection versus gate integration | The new six-test adapter-owner module asserts prepared payload selection and fail-closed metadata, while the 281-collected-test gate module retains earlier direct-tuple and full-gate variants asserting the same owner bucket and failure flags. | `tests/test_final_emission_opening_fallback.py`; opening block in `tests/test_final_emission_gate.py`; Cycle J closure |
| Runtime lineage and replay diagnostics | Runtime projection, replay observation, classifier routing, and dashboard probes intentionally repeat fields; comments clarify intent, but a failure still may appear first in any of four suites. | `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py` |
| Visibility and strict-social fallback ownership | Both are covered through helper/policy owners, gate sequencing, sanitizer interaction, and replay projections; strict-social in particular spans emission, gate, and sanitizer owners. | `tests/test_final_emission_visibility.py`; `tests/test_social_exchange_emission.py`; `tests/test_strict_social_emergency_fallback_dialogue.py`; `tests/test_output_sanitizer.py`; gate suite |
| Mutation boundary attribution | Response-policy mutation, gate mutation classification, stage-diff observability, and FEM runtime-lineage projection all inspect mutation effects through different surfaces. | `tests/test_response_policy_enforcement_mutation.py`; `tests/test_final_emission_gate.py`; `tests/test_stage_diff_telemetry.py`; `tests/test_final_emission_meta.py` |
| Registry and allowlist drift | Several valid but adjacent governance registries exist: public contract keys, emergency fallback registry, ownership registry, validation coverage registry, and validation-layer import allowlists. A failing "registry" test does not immediately identify which registry owns the change. | `tests/test_contract_registry*.py`; `tests/test_emergency_fallback_registry_static_drift.py`; `tests/test_ownership_registry.py`; `tests/test_validation_coverage_registry.py`; `tests/test_validation_layer_closeout.py` |

### Most duplicated or over-assertive areas

1. **Opening fallback** is the clearest present duplicate family. Cycle J made
   the adapter directly testable, but the gate suite still deeply validates
   adapter-owned prepared/fail-closed metadata in addition to legitimate gate
   orchestration and FEM integration.
2. **Final-emission/gate** is the largest concentration point:
   `tests/test_final_emission_gate.py` collects 281 tests and contains opening,
   visibility, source-family, mutation, sanitizer-adjacent, and social
   orchestration clusters.
3. **Replay/diagnostic projection** repeats fallback owner buckets, lineage
   fields, and classifier/dashboard evidence across modules. Much of this is
   explicitly intentional downstream contract locking; compression here has
   higher risk of degrading failure artifacts or CI acceptance evidence.
4. **Strict-social fallback** is broad rather than simply duplicated: 55 test
   modules mention `strict_social`, reflecting multiple legitimate owners and
   high compression risk.

### Where Cycle L should start

Cycle L should start with **final-emission/gate tests**, specifically the
**opening fallback adapter-versus-gate test-role boundary**. It is smaller and
lower-risk than replay, evaluator, or registry compression:

- The adapter owner already exists after Cycle J.
- The gate suite already declares that it owns orchestration rather than
  semantic composition.
- Narrowing or labeling gate assertions can improve attribution while preserving
  adapter, wrapper, full-gate, FEM, and replay coverage.
- Replay tests are newly promoted acceptance/diagnostic locks; evaluator tests
  are comparatively distinct; registries represent several different
  governance contracts rather than one obvious duplicate family.

## 2. Test Inventory By Probable Owner

This is an ownership-focused inventory of the suites implicated by Cycle L and
their principal neighboring surfaces. It is not an attempt to restate all 304
modules.

### Engine-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_save_load.py` | persistence tests named in ownership registry | Engine truth and persistence mechanics | `game.storage` / engine state persistence | owner |
| `tests/test_state_authority.py` | `test_registry_exactly_five_domains_no_extras_deterministic_order`; `test_wrong_module_cannot_mutate_domain`; `test_build_state_mutation_trace_compact_shape` | Mutation authority matrix and state-domain ownership | `game.state_authority` | owner |
| `tests/test_world_engine_updates.py` | `test_apply_resolution_world_updates_combined`; `test_exit_conditions_gate_transition` | Authoritative world updates and affordance/transition effects | world engine / resolution path | owner |
| `tests/test_lead_engine_upsert.py` | `test_identical_replay_is_idempotent`; `test_stronger_later_signal_promotes_same_lead` | Lead registry monotonicity and idempotence | lead engine | owner |
| `tests/test_scene_transition_authority.py` | `test_gpt_transition_proposal_does_not_apply_without_resolver_transition`; `test_no_double_scene_switch_when_resolver_transition_and_gpt_proposal_both_present` | Engine-resolver authority over scene changes | transition/resolution engine | owner/integration |
| `tests/test_response_policy_contracts.py`; `tests/test_prompt_context.py` | `test_prompt_contract_owner_canonical_public_home_preserves_compatibility_with_downstream_helpers` | Shipped contract materialization and prompt-context assembly | response-policy / prompt-context assembly | owner |

### Planner-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_narrative_plan_structural_readiness.py` | `test_readiness_social_follow_up`; `test_readiness_transition_reanchor`; `test_negative_no_duplicate_plan_blob_in_prompt_debug` | Planner bundle structural readiness; explicitly not downstream prose quality | narrative plan builder | owner |
| `tests/test_planner_convergence_contract.py` | `test_report_passes_with_ctir_plan_matching_stamp_and_prompt`; `test_fails_ctir_without_plan` | CTIR/plan/stamp/prompt convergence rules | planner convergence contract | owner |
| `tests/test_planner_ctir_projection.py` | `test_planner_head_state_imports_projection_not_prompt_context_helpers` | Planner projection import and cap boundary | planner projection surface | owner/boundary |
| `tests/test_planner_convergence_live_pipeline.py` | live-pipeline convergence checks identified by registry | Planner contract survival through pipeline | planner bundle owner above | smoke/downstream |

### GPT/expression-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_narrative_mode_output_validator.py` | `test_opening_fails_mid_thread_shape`; `test_continuation_fails_fresh_opening_reset`; `test_action_outcome_passes_early_result` | Thin normative output-shape checks before hard gate legality | narrative mode output validator | owner, deliberately thin |
| `tests/test_c4_narrative_mode_live_pipeline.py` | live pipeline output-mode cases | Output-shape survival in integrated execution | validator above | smoke/downstream |
| `tests/test_build_messages_projection.py`; `tests/test_prompt_and_guard.py` | projection/guard tests | GPT-facing message construction and guard presentation | GPT prompt/expression boundary | mixed |

### Gate-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_final_emission_gate.py` | `test_apply_final_emission_gate_runs_response_type_then_continuity_then_fallback`; `test_canonical_final_gate_opening_fallback_fem_is_upstream_prepared_not_compatibility_local`; visibility selector tests; mutation-fencing tests | Gate layer order, final integration, branch selection, and metadata propagation | `game.final_emission_gate` | owner, with mixed historical/sub-owner blocks |
| `tests/test_output_sanitizer.py` | `test_strip_only_mode_drops_scaffold_without_diegetic_template_substitution`; `test_strict_social_empty_output_fallback_records_sanitizer_selection_and_social_prose_owner` | Final output hygiene and sanitizer-owned selection | `game.output_sanitizer` | owner |
| `tests/test_social_exchange_emission.py` | strict-social terminal and ownership enforcement tests | Strict-social emitted legality/surface | `game.social_exchange_emission` | owner/downstream emission |
| `tests/test_fallback_behavior_gate.py` | `test_gate_runs_fallback_behavior_after_interaction_continuity_non_strict`; representative fallback repair path | Gate application and metadata propagation for fallback behavior | gate orchestration; direct semantics elsewhere | downstream orchestration, correctly labeled |
| `tests/test_dialogue_plan_final_emission_gate.py` | final-emission dialogue-plan gate tests | Dialogue-plan enforcement at gate boundary | gate/dialogue integration | owner-adjacent |

### Final-emission-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_final_emission_opening_fallback.py` | `test_adapter_selects_usable_upstream_prepared_payload_unchanged`; `test_adapter_unusable_upstream_stub_preserves_fail_closed_metadata`; `test_gate_opening_tuple_wrapper_delegates_to_adapter` | Opening prepared-payload selection and fail-closed adapter result; wrapper delegation | `game.final_emission_opening_fallback` | direct owner plus one integration pin |
| `tests/test_final_emission_meta.py` | `test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks`; `test_build_fem_runtime_lineage_events_projects_explicit_mutation_evidence_without_explosion` | FEM normalization and runtime-lineage event projection | `game.final_emission_meta` | owner |
| `tests/test_final_emission_validators.py` | social response structure and referent clarity tests | Final-emission validator semantics | `game.final_emission_validators` | owner for represented predicates |
| `tests/test_final_emission_repairs.py` | `test_repair_strips_meta_fallback_voice_while_preserving_grounded_content`; `test_fallback_behavior_layer_revalidates_once_after_repair` | Final-emission repair semantics | `game.final_emission_repairs` | owner |
| `tests/test_final_emission_visibility.py` | `test_pipeline_replaces_offscene_known_npc_reference`; `test_pipeline_first_mention_fallback_also_satisfies_gate_when_replacement_needed` | Visibility/first-mention/referential gate-facing pipeline behavior | visibility validation and final-emission visibility fallback owners | mixed owner/integration |
| `tests/test_upstream_response_repairs.py` | `test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family`; attach/replace tests | Construction/attachment of upstream prepared fallback payload | `game.upstream_response_repairs` | owner, upstream of emission |

### Evaluator-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_narrative_authenticity_eval.py` | `test_missing_telemetry_fails_closed`; `test_gate_failed_unrepaired_hard_fail`; `test_determinism_same_inputs_same_output` | Offline evaluator scoring and FEM consumption | narrative authenticity evaluator | owner |
| `tests/test_playability_eval.py` | `test_direct_answer_high_for_clear_question_and_answer`; `test_system_validator_leakage_hurts_immersion` | Turn-level playability evaluation | playability evaluator | owner |
| `tests/test_player_agency_evaluator.py`; `tests/test_intent_fulfillment_evaluator.py`; `tests/test_session_cohesion_evaluator.py` | axis-specific evaluations | Supporting evaluator axes | corresponding evaluator module | owner/neighbor |
| `tests/test_scenario_spine_eval.py` | `test_clean_twenty_five_turn_branch_has_no_progressive_degradation`; `test_near_identical_branch_transcripts_flagged` | Offline longitudinal/session-health evaluation | scenario-spine evaluator | owner, not required acceptance |
| `tests/test_evaluator_convergence_closeout.py` | closeout document lock | Documentation/architecture closure invariant | evaluator convergence governance | smoke/contract |

### Replay/CI-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_golden_replay.py` | `test_protected_golden_assertion_failure_records_canonical_report`; `test_golden_observed_turn_projects_canonical_upstream_prepared_opening_owner_bucket`; protected scenario invariant tests | Protected replay observations, assertion reporting, and canonical scenario acceptance | `tests/helpers/golden_replay.py` and protected replay lane | owner for replay projection/acceptance; downstream for runtime semantics |
| `tests/test_failure_classifier.py` | `test_failure_classifier_routes_opening_authorship_payload_symptom_to_upstream_repairs`; `test_failure_classifier_reduces_post_gate_unknown_from_final_emission_lineage` | Failure category/owner/investigation routing | `tests/helpers/failure_classifier.py` | owner for diagnostics |
| `tests/test_failure_dashboard_controlled_failures.py` | `test_controlled_failure_probe_classifies_known_bad_case`; dashboard columns test | Known-bad replay-shaped report output | failure-dashboard reporting | owner for controlled reporting probes |
| `tests/test_failure_classification_contract.py` | owner-bucket/taxonomy/renderer locks | Classification schema allowlists and contract vocabulary | `tests/failure_classification_contract.py` | owner/contract |
| `tests/test_run_scenario_spine_validation.py`; `tests/test_scenario_spine_opening_convergence.py` | artifact/operator summary and opening convergence cases | Scenario-spine artifacts and longitudinal observations | scenario-spine tool/evaluator | downstream/advisory |
| `tests/test_n1_continuity_analysis.py`; `tests/test_n1_scenario_spine_validation.py` | longitudinal analyzer/deterministic fixture cases | Synthetic longitudinal analysis | N1 analyzer/harness | owner for tooling, not CI replay acceptance |

### Contract/schema/registry-owned

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_contract_registry.py` | `test_registry_exports_frozenset_and_expected_keys_present`; `test_contract_registry_does_not_import_runtime_heavy_owners` | Public narrative-plan contract key registry | `game.contract_registry` | owner |
| `tests/test_contract_registry_static_drift.py` | `test_public_projection_top_level_keys_match_registry` | Consumers do not duplicate or drift from contract registry | contract registry | downstream drift guard |
| `tests/test_emergency_fallback_registry_static_drift.py` | `test_emergency_fallback_registry_static_drift_guard` | Emergency fallback registry is single source | emergency fallback registry | owner/drift guard |
| `tests/test_ownership_registry.py` | `test_governance_rejects_duplicate_direct_owner`; `test_ownership_registry_governance` | Direct-owner governance and neighbor role declarations | test ownership registry | owner |
| `tests/test_validation_coverage_registry.py`; `tests/test_validation_coverage_audit.py` | registry validity and duplicate pointer checks | Coverage declaration/audit governance | validation coverage registry | owner/tooling |
| `tests/test_validation_layer_contracts.py`; `tests/test_validation_layer_closeout.py` | canonical layer and evaluator allowlist tests | Validation-layer responsibility/import boundaries | validation-layer contract/audit policy | owner/architecture guard |
| `tests/test_schema_contracts.py`; `tests/test_project_schema.py` | schema contract tests | Data/schema shapes | corresponding schema owner | owner |

### Smoke/integration-only

| Test file path | Representative tests | Behavior asserted | Probable canonical owner | Current role |
| --- | --- | --- | --- | --- |
| `tests/test_transcript_runner_smoke.py` | `test_transcript_runner_smoke_single_begin_turn` | Transcript harness can execute a basic flow | transcript owners elsewhere | smoke |
| `tests/test_behavioral_gauntlet_smoke.py`; `tests/test_playability_smoke.py` | smoke scenarios | Broad behavior survives execution | gauntlet/playability owner suites | smoke |
| `tests/test_synthetic_smoke.py` | synthetic flows | Broad routed/social behavior signal | multiple direct owners | smoke/mixed |
| `tests/test_narration_transcript_regressions.py`; `tests/test_transcript_regression.py` | transcript incidents | Historical/end-to-end regressions | named feature owners and transcript suite | regression/integration |
| `tests/test_start_campaign_api.py` | `test_start_campaign_promotes_valid_upstream_prepared_scene_opening`; journal-seed fallback-basis tests | API-level start-campaign behavior | API and opening owners | integration/downstream |

## 3. Duplicated Assertion Families

| Family name | Files/tests involved | Common assertion repeated | Probable canonical owner | Tests to retain as downstream/smoke rather than deep owner | Risk of compression |
| --- | --- | --- | --- | --- | --- |
| Opening fallback prepared selection and fail-closed policy | `tests/test_final_emission_opening_fallback.py::test_adapter_selects_usable_upstream_prepared_payload_unchanged`, `::test_adapter_unusable_upstream_stub_preserves_fail_closed_metadata`; `tests/test_final_emission_gate.py::test_canonical_upstream_prepared_direct_tuple_has_no_compatibility_local_ownership`, `::test_canonical_direct_tuple_prefers_upstream_prepared_payload_over_compatibility_local`, `::test_gate_direct_tuple_text_only_stub_fails_closed_without_rebuild`, and full-gate opening cases | Usable prepared payload yields upstream-prepared ownership; malformed/missing data yields sealed fail-closed fields, never compatibility-local authorship | `tests/test_final_emission_opening_fallback.py` for adapter; `tests/test_final_emission_gate.py` only for wrapper/full-gate wiring | Gate direct-tuple cases should become wrapper/integration assertions; replay/API remain projection/end-to-end pins | **low** |
| Opening prose composition and prepared payload packaging | `tests/test_upstream_response_repairs.py::test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family`; `tests/test_final_emission_gate.py::test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot`; `tests/test_start_campaign_api.py` basis cases | Exact opening text and curated-fact/authorship payload fields | Composer behavior belongs with opening realization/composer; payload shape with `tests/test_upstream_response_repairs.py` | Gate should assert selected output and integration fields only; API should assert source selection/journal path | medium |
| Visibility fallback | `tests/test_final_emission_visibility.py` replacement/metadata tests; large visibility helper/selector block in `tests/test_final_emission_gate.py`; `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence`; `tests/test_failure_classifier.py::test_failure_classifier_preserves_projected_visibility_fallback_evidence` | Visibility failure selects replacement and retains owner-bucket evidence | Visibility helper/pipeline module for decision/payload; gate for ordering/output application | Replay/classifier are downstream diagnostics; gate helper tests should not grow validation semantics | medium |
| Strict-social fallback and sanitizer owner split | `tests/test_social_exchange_emission.py`; `tests/test_strict_social_emergency_fallback_dialogue.py`; `tests/test_output_sanitizer.py::test_strict_social_empty_output_fallback_records_sanitizer_selection_and_social_prose_owner`; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py` | Strict-social fallback prose belongs to social emission while sanitizer can select it; metadata records separate owners | `tests/test_social_exchange_emission.py` for prose/policy; `tests/test_output_sanitizer.py` for sanitizer selection | FEM/replay/classifier should retain only projection/diagnostic contract locks; gate covers order | high |
| Source-family tagging | `tests/test_realization_provenance.py`; source-family assertions in `tests/test_upstream_response_repairs.py` and `tests/test_final_emission_gate.py`; replay/classifier source fields | Known fallback paths carry correct realization/source family rather than legacy/unclassified markers | `tests/test_realization_provenance.py` and realization-authority registry tests | Gate/upstream/replay should verify preservation only when their boundary consumes the tag | medium |
| Fallback lineage and owner-bucket projection | `tests/test_opening_fallback_owner_bucket.py`; `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py`; dashboard controlled probes | Opening/sealed/visibility fallback fields map to owner buckets and runtime evidence | Mapper: `tests/test_opening_fallback_owner_bucket.py`; lineage projection: `tests/test_final_emission_meta.py` | Replay/classifier/dashboard retain explicit downstream projection and triage locks, not mapping semantics | medium |
| Replay promotion | `tests/test_golden_replay.py`; `.github/workflows/convergence-checks.yml`; `docs/testing/protected_replay_manifest.md`; Cycle K K1/K2 reports | Marked protected scenarios form a hard-fail acceptance lane | Protected replay manifest and golden replay suite | CI wiring/doc tests should not restate runtime ownership | low, but little immediate value |
| Replay drift thresholds | `tests/test_golden_replay.py::test_golden_drift_classifier_buckets_exact_structural_and_semantic_drift`; classifier tests; Cycle K K4 memo | Structural/semantic/exact drift categorization and which signals are hard gates | Golden replay helper for bucket mechanics; policy remains K4 documentation until implemented | Classifier owns diagnostic routing only; do not convert diagnostic lineage frequencies into hidden gates | high |
| Failure artifact ergonomics | `tests/test_golden_replay.py::test_protected_golden_assertion_failure_records_canonical_report`; `tests/test_failure_classifier.py` report tests; `tests/test_failure_dashboard_controlled_failures.py`; `tests/conftest.py`; Cycle K K3/K3A/K3B reports | Failing protected replay emits actionable classification/reporting evidence | Golden replay failure bridge/report helper and dashboard renderer according to their distinct outputs | Controlled probes should remain known-bad report checks; protected scenarios should not deeply test renderer policy | medium |
| Longitudinal replay decision behavior | `tests/test_scenario_spine_eval.py`; `tests/test_run_scenario_spine_validation.py`; `tests/test_n1_continuity_analysis.py`; protected golden three-branch smoke; Cycle K K5 memo | Longitudinal continuity/branch evidence appears through multiple lanes | Scenario-spine evaluator for game-facing observation; N1 analyzer for synthetic tooling; golden replay only for protected smoke | Keep lanes distinct; none should be compressed into another absent a promotion decision | high |
| Final emission thinness and boundary layer order | `tests/test_final_emission_gate.py`; `tests/test_final_emission_validators.py`; `tests/test_final_emission_repairs.py`; `tests/test_final_emission_boundary_*`; `tests/test_gate_convergence_closeout.py` | Gate calls owners in order and does not accumulate semantic owner logic | Gate orchestration suite for sequencing; validator/repair suites for semantics | Boundary audit/convergence suites should stay smoke/architecture locks | medium |
| Mutation boundary assertions | `tests/test_response_policy_enforcement_mutation.py`; mutation fencing in `tests/test_final_emission_gate.py`; `tests/test_stage_diff_telemetry.py`; mutation lineage in `tests/test_final_emission_meta.py` | Mutating branches are classified, observable, and do not cross ownership boundaries silently | Mutation generation: response-policy/gate direct owner; observation: stage-diff/FEM projection owners | Replay/classifier should consume projected mutation evidence without redefining allowed mutation rules | medium |
| Contract/registry allowlist drift | `tests/test_contract_registry.py`; `tests/test_contract_registry_static_drift.py`; `tests/test_emergency_fallback_registry_static_drift.py`; `tests/test_ownership_registry.py`; `tests/test_validation_coverage_registry.py`; `tests/test_validation_layer_closeout.py` | Central registries/allowlists remain authoritative and consumers do not duplicate keys/import permissions | Each registry file is a distinct owner; no single "registry" owner exists | Static consumers and audit smoke should assert referencing/validation, not duplicate full allowlist content | medium |

## 4. Failure Attribution Map

| Failure symptom | Current likely failing tests | Ambiguous owners | Proposed probable owner | Downstream/smoke tests that should not deeply reassert it |
| --- | --- | --- | --- | --- |
| Prepared opening payload is not selected or missing payload fails closed incorrectly | Opening adapter tests and multiple opening tests in `tests/test_final_emission_gate.py`; possibly replay/API | Opening adapter versus gate wrapper | `tests/test_final_emission_opening_fallback.py` | Full gate should check application/FEM only; `test_golden_replay.py` and `test_start_campaign_api.py` check boundary survival |
| Exact deterministic opening prose or curated-fact basis changes | Upstream response repairs, gate snapshot, API/start-campaign, scenario-spine tests | Composer versus packager versus gate | Composer/opening-realization tests for prose; `tests/test_upstream_response_repairs.py` for payload package | Gate and replay should not own text composition details |
| Opening owner bucket is wrong | Opening owner bucket, FEM, gate, replay, classifier, dashboard | Mapper versus diagnostic projection | `tests/test_opening_fallback_owner_bucket.py` for mapping; `tests/test_final_emission_meta.py` for lineage emission | Replay/classifier/dashboard assert preservation and routing only |
| Visibility fallback selects wrong branch | Visibility pipeline and large gate selector/helper block; replay/classifier | Visibility helper versus gate ordering | `tests/test_final_emission_visibility.py` / extracted visibility fallback helper tests | Replay/classifier should keep evidence projection only |
| Strict-social fallback text or selection owner is wrong | Social exchange, emergency dialogue, output sanitizer, gate, FEM, replay/classifier | Social prose owner versus sanitizer selector versus gate sequence | `tests/test_social_exchange_emission.py` for prose/policy; `tests/test_output_sanitizer.py` for sanitizer selection | FEM/replay/classifier remain projection diagnostics |
| Fallback family/source tag is absent or mislabeled | Realization provenance, upstream, gate, replay/classifier | Provenance owner versus consuming boundaries | `tests/test_realization_provenance.py` | Gate/replay consume known tag without rebuilding taxonomy |
| Runtime lineage event kind/owner/bucketing is wrong | FEM tests, runtime-lineage telemetry tests, golden replay, classifier/dashboard | Runtime projection versus reporting projection | `tests/test_final_emission_meta.py` and `tests/test_runtime_lineage_telemetry.py` | Golden/classifier/dashboard assert transport and diagnosis only |
| Protected replay fails on a structural invariant | Golden replay scenario plus failure classifier/reporting tests if artifact bridge is invoked | Runtime owner versus replay/report owner | Failed invariant's direct runtime owner; golden replay owns acceptance detection | Dashboard controlled probes should not reassert game behavior |
| Replay drift bucket or threshold decision is surprising | Golden replay helper/classifier tests; K4 policy documentation | Bucket mechanics versus acceptance policy | Golden replay helper for bucket mechanics; no expanded threshold owner yet | Longitudinal evidence lanes should remain advisory |
| Replay failure report lacks useful triage fields | Golden replay report test, classifier/report tests, controlled probes | Assertion bridge versus renderer/schema | Replay reporting bridge/dashboard helper | Protected scenario tests need not restate renderer schema |
| Scenario-spine or N1 longitudinal verdict differs | Scenario-spine evaluator/tool tests or N1 analysis tests | Production-facing observation versus synthetic analyzer | Respective evaluator/analyzer lane; not golden replay | Protected replay three-branch smoke should remain smoke |
| Post-gate mutation is misclassified or invisible | Response-policy mutation tests, gate mutation fences, stage-diff, FEM projection, classifier | Mutator versus instrumentation | Direct mutator suite for legality; stage-diff/FEM for observation | Classifier/replay consume reported evidence |
| Public prompt keys or allowlist drifts | Contract registry/static drift, ownership registry, validation-layer/coverage registry tests | Several independent registries | Specific registry corresponding to the failed key/import/ownership record | Audit smoke and consumer tests should not duplicate authoritative list |

## 5. Candidate Compression Moves

### Block L1 - Opening Adapter Owner and Gate Consumer Boundary

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_final_emission_opening_fallback.py`; `tests/test_final_emission_gate.py`; optionally `tests/test_ownership_registry.py` if the extracted adapter is declared as a named neighbor/sub-owner |
| Exact ownership rule clarified | `game.final_emission_opening_fallback` owns prepared-versus-fail-closed adapter selection fields; `game.final_emission_gate` owns wrapper delegation, route ordering, final output/FEM integration, and side-effect sequencing. |
| Tests likely changed | Add explicit role comments/section headings; narrow gate direct-tuple assertions that restate adapter metadata to wrapper/application obligations or use a named consumer assertion helper. |
| Tests that should remain unchanged | Adapter prepared/fail-closed behavior tests; upstream packager tests; owner-bucket mapper; FEM lineage; golden replay; API integration tests. |
| Expected benefit | A failed adapter policy points to one six-test owner file first, while gate failures indicate integration/order rather than the same policy duplicated at two levels. |
| Risk level | **low** |

### Block L2 - Visibility Decision Owner Versus Gate Ordering Labeling

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_final_emission_visibility.py`; visibility subsection of `tests/test_final_emission_gate.py`; possibly `tests/test_golden_replay.py` comments only |
| Exact ownership rule clarified | Visibility helper/pipeline owns replacement decision and payload shape; gate owns sequence/output application; replay/classifier own projection and triage. |
| Tests likely changed | Label helper-level versus sequencing clusters; replace deep duplicate payload checks in gate tests only where direct visibility tests already lock them. |
| Tests that should remain unchanged | Visibility behavior matrix; owner-bucket classifier tests; replay/classifier evidence tests. |
| Expected benefit | Visibility failures become less likely to fan out across helper and gate internals. |
| Risk level | medium |

### Block L3 - Strict-Social Selection/Prose/Sanitizer Role Ledger

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_social_exchange_emission.py`; `tests/test_strict_social_emergency_fallback_dialogue.py`; `tests/test_output_sanitizer.py`; strict-social sections of `tests/test_final_emission_gate.py`; perhaps role comments in replay/classifier tests |
| Exact ownership rule clarified | Social emission owns prose and strict-social terminal policy; sanitizer owns empty-output selection; gate owns order/integration; FEM/replay/classifier own projection. |
| Tests likely changed | Ownership comments and possibly shared role-oriented helpers; no assertion narrowing before a further focused recon. |
| Tests that should remain unchanged | Existing strict-social behavior assertions and sanitizer owner-split locks. |
| Expected benefit | Establishes a map before attempting compression in the largest multi-owner fallback seam. |
| Risk level | high |

### Block L4 - Runtime Lineage Projection Versus Diagnostic Consumers

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_final_emission_meta.py`; `tests/test_runtime_lineage_telemetry.py`; `tests/test_golden_replay.py`; `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py` |
| Exact ownership rule clarified | FEM/runtime telemetry owns event construction; replay owns observed transport; classifier owns triage mapping; dashboard owns rendering/retention. |
| Tests likely changed | Comments or local helper naming that labels raw construction versus consumer-projection fixtures. |
| Tests that should remain unchanged | Owner bucket and classification taxonomy locks; protected replay assertions; controlled failure cases. |
| Expected benefit | Projection failures and diagnostic-policy failures become distinguishable in the failure list. |
| Risk level | medium |

### Block L5 - Registry Namespace and Allowlist Ownership Labels

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_contract_registry.py`; `tests/test_contract_registry_static_drift.py`; `tests/test_emergency_fallback_registry_static_drift.py`; `tests/test_ownership_registry.py`; `tests/test_validation_coverage_registry.py`; `tests/test_validation_layer_closeout.py` |
| Exact ownership rule clarified | Each registry governs a distinct namespace: public contract keys, fallback vocabulary, test ownership, coverage pointers, or import-layer permissions. |
| Tests likely changed | Module docstrings and failure-message labels; possibly helper names, not allowlists themselves. |
| Tests that should remain unchanged | Registry contents and static drift/allowlist enforcement behavior. |
| Expected benefit | A registry failure names the governance owner rather than merely saying "drift." |
| Risk level | low-medium |

### Block L6 - Mutation Evidence Ownership Map

| Item | Detail |
| --- | --- |
| Files likely touched | `tests/test_response_policy_enforcement_mutation.py`; mutation-fence cases in `tests/test_final_emission_gate.py`; `tests/test_stage_diff_telemetry.py`; mutation lineage cases in `tests/test_final_emission_meta.py`; classifier comments |
| Exact ownership rule clarified | Mutating policy/gate modules own whether a mutation is legal; stage-diff and FEM own observability; classifier owns investigation routing. |
| Tests likely changed | Labeling and fixture/helper naming; later assertion narrowing only after each mutation kind is mapped. |
| Tests that should remain unchanged | Mutation legality classifications and lineage-event evidence. |
| Expected benefit | A mutation regression points to behavior owner versus telemetry consumer. |
| Risk level | medium |

## 6. Recommended First Implementation Block

Choose exactly one first block: **Block L1 - Opening Adapter Owner and Gate Consumer Boundary**.

It is the smallest clear post-extraction ownership improvement:

- Cycle J already created `tests/test_final_emission_opening_fallback.py` as a
  direct adapter test surface.
- `tests/test_final_emission_gate.py` still contains earlier direct-tuple
  prepared/fail-closed assertions alongside valid full-gate orchestration
  assertions.
- The work can be limited to test-role labeling, a small test-only assertion
  helper if useful, and narrowing repeated gate-side adapter internals to
  wrapper/FEM/output obligations.
- No test needs to be deleted. Direct adapter behavior remains locked in its
  owner suite; full-gate/replay/API behavior remains locked downstream.

Suggested implementation boundary for GPT:

1. Add an explicit ownership note to
   `tests/test_final_emission_opening_fallback.py`: adapter result semantics are
   owner-level; the delegation test is its only gate integration pin.
2. In the opening section of `tests/test_final_emission_gate.py`, mark which
   existing tests are wrapper/integration or final-FEM tests and which are
   historical adapter-shaped repetitions.
3. Without deleting tests, narrow only the clearly adapter-shaped gate
   repetitions so they assert delegation/integration outcomes not already-owned
   internal metadata matrices. Preserve the full-gate prepared/fail-closed FEM
   checks.
4. Run the opening/final-emission focused suite and protected golden replay.

Files to pass back to GPT for that implementation:

- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_gate.py`
- `tests/test_upstream_response_repairs.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_start_campaign_api.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_gate.py`
- `docs/cycles/cycle_j_gate_cluster_extraction_closure_2026-05-26.md`

## 7. Commands Run

All command activity was read-only except adding this report. No production or
test file was edited.

| Command | Result |
| --- | --- |
| `Get-Location; git status --short --branch` | Confirmed workspace root and initially clean branch `feature/failure-locality...origin/feature/failure-locality`. |
| `rg --files -g '*test*.py' -g 'tests/**' -g '*cycle*' -g '*.md'` | Located test tree and prior Cycle E/I/J/K reports; output was broad and included cached paths. |
| `Get-ChildItem -Force \| Select-Object Mode,Length,LastWriteTime,Name` | Identified repository directories, pytest configuration, environments, docs, audits, and tests. |
| `$files = rg --files tests -g '*.py' -g '!**/__pycache__/**'; ...` | Counted `336` Python files under `tests`, including `304` `test_*.py` modules and `32` helper/support modules; listed test modules. |
| Broad `rg -n` searches over `tests/*.py` for `fallback`, `opening`, `visibility`, `strict_social`, `source_family`, `lineage`, `final_emission`, `mutation`, `registry`, and `allowlist` | Located candidate assertion families; output was intentionally broad and established high fanout around final emission/fallback concerns. |
| Broad `rg -n` searches over `tests`, `docs/audits`, `docs/testing`, and `docs/reports` for `replay`, `drift`, `promotion`, `failure_artifact`, `longitudinal`, and `protected` | Located Cycle K replay policy, golden replay, failure classifier/dashboard, and longitudinal lanes. |
| `Get-Content -Raw docs\reports\cycle_j_gate_cluster_extraction_recon_2026-05-26.md; ... docs\audits\cycle_k_replay_promotion_recon_2026-05-26.md; ... audits\cycle_e_test_signal_ownership_recon_2026-05-17.md` | Read prior ownership and replay recon context; established intended owner/downstream terminology. |
| Two attempted PowerShell `rg` function-name extraction commands containing a malformed quoted regex | Failed with `The string is missing the terminator: "`; no repository change occurred. |
| `Get-Content -Raw` for Cycle K K2/K3/K4/K5 reports and Cycle I/J contract/closure reports | Established replay promotion status, artifact/threshold policy, longitudinal decision, opening ownership split, and Cycle J adapter extraction. |
| Corrected `$files = @(...) ; foreach ($f in $files) { rg -n '^def test_\|^class Test' $f }` over final-emission/fallback files | Enumerated representative gate, adapter, visibility, strict-social, upstream, owner-bucket, FEM, provenance, and mutation tests. |
| Corrected function-name enumeration over replay/classifier/registry/evaluator files | Enumerated golden replay, dashboard, contract, scenario, N1, and registry test surfaces. |
| `Get-Content ... -TotalCount 35` over selected owner files and `rg -n ... 'owner\|downstream\|smoke\|canonical...'` | Confirmed existing role comments in gate, opening bucket, replay, classifier, fallback-behavior, and ownership-registry suites. |
| `Get-Content tests\test_final_emission_gate.py -TotalCount 24; ... Select-Object -Skip ...` | Inspected gate header and opening cluster alongside replay opening projections and fallback-behavior downstream labeling. |
| Term-frequency file counts via `rg -l` for focus terms | Found test-module mentions: `opening_fallback=18`, `visibility_fallback=8`, `strict_social=55`, `source_family=3`, `lineage=9`, `replay=16`, `drift=45`, `failure_dashboard=5`, `final_emission=111`, `mutation=44`, `registry=44`, `allowlist=10`. |
| `Select-String -Path tests\test_inventory.json -Pattern ... -Context 1,5` | Confirmed inventory references to major current owner/evaluator suites; output was broad. |
| `rg -n '^pytestmark\|pytest\.mark\....'` across targeted files | Confirmed opening/gate/upstream/FEM/visibility/strict-social/mutation suites are unit-marked where defined; golden replay is integration plus `golden_replay`; dashboard probes use their probe marker. |
| Function-name scans over engine/planner/GPT/evaluator/final-emission representative files | Established representative tests and direct-owner language across the requested ownership groups. |
| Per-file `Select-String -Pattern '^def test_'` counts for key files | Top-level function counts included gate `266`, opening adapter `6`, visibility `48`, upstream `16`, owner bucket `10`, FEM `34`, golden replay `31`, classifier `31`, ownership registry `13`; collected counts are higher for parametrized cases. |
| `rg -n` focused occurrence count over high-value ownership files piped to `Measure-Object` | Measured `949` matched focus-term references across the selected high-density files; used only as density evidence. |
| Initial `python -m pytest --collect-only -q --disable-warnings` and targeted collection using `python` | Both failed immediately because `python` is not on `PATH` in this shell. |
| `codex_app.load_workspace_dependencies` | Resolved bundled Python executable at `C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. |
| `$env:PYTHONPATH='.\.venv\Lib\site-packages'; & '<bundled-python>' -m pytest --collect-only -q --disable-warnings` | Succeeded and enumerated current module collection. |
| Bundled-Python targeted `--collect-only` for opening/FEM/replay/classifier/contract/ownership suites | Succeeded; confirmed the selected owner/downstream/contract modules collect cleanly. |
| Bundled-Python collection captured and summed in PowerShell | Succeeded: `collected_modules=304`, `collected_tests=4209`, `collection_exit=0`. |
| `Get-Content` of the responsibility registry, opening adapter tests, and FEM lineage block; representative `rg` scans of opening/social/sanitizer/scenario/validation modules | Confirmed canonical owner declarations and exact opening/lineage duplication boundary. |
| `git status --short --branch; git diff --name-only; git ls-files docs\reports docs\audits audits \| rg 'cycle_[ijk]\|test_signal\|fallback'` | Confirmed the branch remained clean before writing this report and confirmed established report locations. |
| `git diff --check; git status --short --branch; git diff --stat -- docs\reports\cycle_l_test_ownership_compression_recon_2026-05-26.md` | After report creation, `git diff --check` found no whitespace errors and status showed only this new untracked report. (`git diff --stat` does not display an untracked file.) |
| `rg -n '^## [1-7]\.\|^### Block L1\|^\| Failure symptom\|^Choose exactly one first block\|^## Recon Conclusion' docs\reports\cycle_l_test_ownership_compression_recon_2026-05-26.md` | Confirmed all requested numbered sections, the failure table, the single recommended first block, and the conclusion are present. |

## Recon Conclusion

The suite already understands ownership in principle, but Cycle J changed the
opening fallback ownership topology faster than the older gate assertions were
reclassified. Start Cycle L by making that new adapter-owner/gate-consumer
boundary unmistakable. It offers a small, test-only, non-deletion-oriented move
that improves the meaning of a failure without disturbing protected replay,
evaluator policy, or registry governance.
