# CL - Replay Projection Churn Reduction Discovery

Discovery date: 2026-06-26. Scope: repository inspection, current structure, and available git history. No behavior-changing edits were made.

## 1. Replay Projection File Inventory

The replay projection surface is split between runtime read-side projection, test-side protected observation assembly, classifier/dashboard consumers, and governance/artifact synchronization.

| File | Role | Primary exported symbols / functions / classes | Producer / owner / transformer / consumer | High-touch or central? |
|---|---|---|---|---|
| `tests/helpers/golden_replay_projection.py` | Acceptance projection facade and protected observed-turn assembler | `project_turn_observation`; re-exports projection field/fallback/speaker/manifest helpers | Transformer and owner of protected observed row assembly | Central; 18 commits; many consumers call the facade |
| `tests/helpers/golden_replay_projection_extractors.py` | Extraction registry, raw/normalized presence, unavailable routing, flat observed fields | `_PROTECTED_EXTRACTION_SPECS`, `protected_observation_extraction_registry`, `_project_flat_protected_observed_fields`, `_build_projection_status`, `project_semantic_mutation_summary` | Transformer and partial owner of source routing | High-touch and high-complexity; 978 LOC, 16 commits |
| `tests/helpers/golden_replay_projection_fields.py` | Protected observation schema, defaults, drift bucket assignment | `ProtectedObservationField`, `PROTECTED_OBSERVATION_FIELDS`, `protected_observation_field_paths`, `protected_observation_default_row`, `observed_projection_schema_defaults`, `protected_observation_drift_bucket` | Schema owner | Central authority; new split file has 1 commit, but schema fan-out is high |
| `tests/helpers/golden_replay_projection_fallbacks.py` | Acceptance-side fallback-family precedence and bridge inference | `REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS`, `project_replay_fallback_family_from_fem`, `_resolve_fallback_family`, `dual_fallback_family_replay_precedence_surface` | Transformer/compatibility owner | Central for fallback-family shape; split file is low-history but high-policy |
| `tests/helpers/golden_replay_projection_speaker.py` | Acceptance-side selected-speaker fallback and final-speaker parity | `read_final_speaker_observation_for_replay`, `project_speaker_projection_parity`, `_resolve_selected_speaker_id` | Transformer and consumer of runtime speaker evidence | Central for speaker drift; split file low-history |
| `tests/helpers/golden_replay_projection_manifest.py` | Manifest rendering/parity for protected fields | `protected_observation_manifest_field_rows`, `render_protected_observation_manifest_section`, `protected_observation_manifest_registry_parity_errors` | Serializer/consumer of schema registry | Central to docs churn |
| `tests/helpers/golden_replay_projection_test_support.py` | Projection test fixture support | `load_manifest_refresh_tool`, `speaker_parity_turn_payload`, `ak5_rich_projection_payload` | Test helper/consumer | Low-touch; supports focused tests |
| `game/final_emission_replay_projection.py` | Runtime read-side FEM lineage/source/owner projection | `build_fem_runtime_lineage_events`, `normalize_fem_for_replay_acceptance`, `read_fem_from_turn_for_replay`, `read_emission_debug_lane_for_replay`, `read_opening_fallback_owner_bucket_for_replay`, `project_source_family_from_fallback_kind`, `project_mutation_classification_from_fallback_kind` | Runtime transformer/provider | Central; 892 LOC, 12 commits, broad fan-in |
| `game/final_emission_meta.py` | FEM metadata write/read normalization and opening fallback field registry | `ensure_final_emission_meta_dict`, `patch_final_emission_meta`, `normalize_final_emission_meta_for_observability`, `OPENING_FALLBACK_PROJECTION_FIELDS`, owner-bucket/fallback metadata registries | Producer, owner, normalizer | Very high-touch; 2,291 LOC, 36 commits |
| `game/final_emission_ownership_schema.py` | Canonical owner-token vocabulary and allowed owner buckets | `OPENING_FALLBACK_OWNER_*`, `SEALED_FALLBACK_OWNER_*`, `VISIBILITY_FALLBACK_OWNER_*`, selection/content owner constants, sanitizer owner normalization | Schema owner/provider | Low commit count but central vocabulary |
| `game/final_emission_owner_bucket_views.py` | Narrow owner-bucket read facade | `opening_fallback_owner_bucket_from_fields`, `opening_fallback_owner_bucket_from_meta`, `visibility_fallback_owner_bucket_from_fields`, `sealed_fallback_owner_bucket_from_fields` | Owner/read facade | Central for ownership stabilization; 2 commits |
| `game/ownership_projection_views.py` | Narrow read-side ownership vocabulary facade | `lineage_owner_vocabulary`, `sanitizer_trace_owner_vocabulary`, `ownership_projection_views_surface` | Provider/facade | Low-touch; central import boundary |
| `game/attribution_read_views.py` | Attribution read facade over owner vocabulary | `attribution_read_views_surface` and re-exported ownership constants | Provider/facade | Low-touch; classifier/attribution dependency |
| `game/runtime_lineage_telemetry.py` | Runtime lineage event schema and recurrence-key normalization | `RUNTIME_LINEAGE_*`, `make_runtime_lineage_event`, `normalize_runtime_lineage_events`, `summarize_runtime_lineage_events`, `build_recurrence_key` | Schema/serializer/provider | Central; 8 commits |
| `game/final_emission_speaker_observation.py` | Runtime final-speaker evidence producer/reader | `FINAL_SPEAKER_OBSERVATION_KEY`, `build_final_speaker_observation`, `stamp_final_speaker_observation`, `read_final_speaker_observation` | Producer/provider | Central for speaker parity |
| `tests/helpers/golden_replay.py` | Golden replay runner/assertion/report orchestration | `run_golden_replay`, `assert_golden_turn_observation`, `assert_protected_golden_turn_observation`, drift/render helpers | Consumer/orchestrator | High-touch; 25 commits and broad import fan-in |
| `tests/helpers/golden_replay_api.py` | Narrow facade over replay helper | `observed_turn_from_payload` and replay helper re-exports | Consumer facade | Low-touch, useful interface boundary |
| `tests/helpers/replay_observed_row_fixtures.py` | Synthetic observed-row construction | `synthetic_observed_replay_row` | Test producer/consumer of schema defaults | Medium; can mask absent-source semantics |
| `tests/helpers/failure_classifier.py` | Failure category/owner/source classification | `classify_replay_failure` and classification helpers | Consumer of projected rows | High-touch; 14 commits |
| `tests/helpers/failure_classification_alignment.py` | Contract alignment between classifier/dashboard/projection fields | `protected_replay_classifier_evidence_field_paths`, `assert_classifier_evidence_manifest_locked`, `assert_contract_classifier_alignment` | Governance consumer | Central for field coupling |
| `tests/helpers/failure_classification_builders.py` | Synthetic classifier row builders | many `observed_*_row` builders | Test producer/consumer | High surface; can couple to raw field shape |
| `tests/helpers/failure_classification_split_owner.py` | Split-owner acceptance matrix and projection helpers | `SPLIT_OWNER_ACCEPTANCE_MATRIX`, `project_split_owner_matrix_row`, `assert_split_owner_matrix_fem_projection`, `assert_split_owner_acceptance_matrix_contract` | Governance/test producer and consumer | High-complexity; 1,011 LOC |
| `tests/helpers/failure_dashboard_report.py` | Dashboard and protected failure report rendering | `build_failure_dashboard_rows`, `build_classified_dashboard_row`, `render_failure_dashboard_markdown`, `render_protected_replay_failure_report` | Consumer/serializer | High-touch; 22 commits |
| `tests/helpers/failure_dashboard_*` | Dashboard paths, session buffers, recurrence, drift, stability, fixtures | `write_requested_dashboard_artifacts`, `record_failure_dashboard_rows`, path constants, recurrence/stability renderers | Consumers/serializers | Central as generated-artifact writers |
| `tests/helpers/replay_drift_*` | Drift taxonomy, rows, risk, trends, reports | `classify_owner_drift_bucket`, `build_risk_payload`, `render_owner_drift_*` | Consumers/reporters | Central diagnostic consumers |
| `tests/helpers/replay_bug_recurrence_*` | Recurrence event/history/statistics serialization | `build_recurrence_key`, `aggregate_recurrence_history`, recurrence report/render functions | Consumer/serializer | High-volume generated artifact surface |
| `tests/helpers/replacement_attribution_inventory.py` | Replacement attribution completeness/read path inventory | inventory/report helpers | Governance consumer | Reads projection/lineage attribution |
| `tests/helpers/protected_field_routing_contract.py` | Machine-readable protected field source/default matrix | `build_protected_field_routing_matrix` | Governance owner over projection routing | Central new contract |
| `tests/helpers/trace_nest_contract.py` | Trace dotted-path contract | trace nest helpers | Governance consumer | Central for nested trace compatibility |
| `tests/helpers/fem_normalization_contract.py` | Raw/normalized FEM field contract | normalization matrix helpers | Governance consumer | Central for raw/normalized churn reduction |
| `tests/helpers/synthetic_replay_evidence_bridge.py` | Synthetic replay evidence bridge | bridge helpers | Consumer of projection/classifier shape | Consumer coupling risk |
| `tests/helpers/speaker_contract_risk.py` | Speaker replay risk comparison | `project_final_emission_for_replay`, `observe_final_to_replay_speaker_contract`, `final_replay_parity_record` | Consumer | Reads projected speaker fields |
| `tools/refresh_protected_replay_manifest.py` | Protected replay manifest refresh/check tool | manifest refresh command functions | Serializer/governance consumer | 7 commits; tied to schema churn |
| `tools/run_scenario_spine_validation.py` | Transcript metadata projection for scenario-spine validation | `build_transcript_turn_meta`, runtime-lineage helpers | Consumer/parallel serializer | Reads runtime projection, not protected observed row only |
| `tools/projection_drift_watch.py` | Projection drift watch/audit | drift-watch helpers | Governance consumer | Advisory consumer |
| `tools/fallback_projection_coverage_audit.py` / `tools/fallback_projection_gap_reality_audit.py` | Fallback projection coverage/gap audits | audit command functions | Governance consumers | Reads current projection field coverage |
| `artifacts/golden_replay/README.md` | Artifact governance doc | n/a | Documentation/consumer guide | Low-touch; central for artifact boundary |
| `artifacts/golden_replay/artifact_manifest.md` | Generated/required artifact manifest | n/a | Documentation/serializer output | Low-touch; central for generated-output boundary |
| `docs/testing/protected_replay_manifest.md` | Human protected replay schema/manifest | protected field table | Governance serializer output | High-touch; 17 commits |
| `docs/audits/CF*.md`, `CE*.md`, `CG*.md`, `BU15_split_owner_acceptance_matrix.md` | Discovery/contract evidence | n/a | Governance docs | Useful historical evidence |

Current projection tests include `tests/test_golden_replay_projection.py`, `tests/test_golden_replay_projection_metadata.py`, `tests/test_golden_replay_projection_registry.py`, `tests/test_golden_replay_projection_manifest.py`, `tests/test_golden_replay_projection_presence_integration.py`, `tests/test_golden_replay_projection_fallback_integration.py`, `tests/test_golden_replay_projection_speaker_integration.py`, `tests/test_cf1_*_precedence.py`, `tests/test_cf2_protected_field_routing.py`, `tests/test_cf3_raw_normalized_fem_field_matrix.py`, `tests/test_cf4_trace_nest_dotted_path_contract.py`, `tests/test_cf6_generated_projection_artifact_governance.py`, and `tests/test_cf7_synthetic_row_classifier_evidence_bridge.py`.

## 2. Churn Evidence

Git history is available and not shallow. Commit counts below use `git log --follow -- <file>` on the current path. Low counts on split files are not proof of stability because many were created during the CE/CF split on 2026-06-25.

| File | Commits | Recent dates | Recurring edit themes | Dominant change type |
|---|---:|---|---|---|
| `game/final_emission_meta.py` | 36 | 2026-06-26, 2026-06-25, 2026-06-21 | CK fallback authorship contraction, CG classification sync, BV/BU ownership work | Metadata fields, normalization, owner vocabulary, compatibility |
| `tests/helpers/golden_replay.py` | 25 | 2026-06-22, 2026-06-13, 2026-06-12 | BX speaker parity, BI replay isolation, BG hotspot redistribution | Replay orchestration, assertions, consumer compatibility |
| `tests/helpers/failure_dashboard_report.py` | 22 | 2026-06-25, 2026-06-20, 2026-06-16 | CE concentration split, BQ recurrence, BL projection simplification | Consumer/report serialization |
| `tests/helpers/golden_replay_projection.py` | 18 | 2026-06-26, 2026-06-25, 2026-06-25 | CJ readiness, CG classification sync, CE split | Facade, re-exports, compatibility, assembly |
| `tests/helpers/golden_replay_projection_extractors.py` | 16 | 2026-06-25, 2026-06-22, 2026-06-22 | CE split, BY semantic mutation, BX speaker parity | Extraction logic, new fields, presence routing |
| `docs/testing/protected_replay_manifest.md` | 17 | 2026-06-21, 2026-06-21, 2026-06-11 | BW/BU/BF protected manifest and inventory updates | Governance/schema serialization |
| `tests/helpers/failure_classifier.py` | 14 | 2026-06-25, 2026-06-21, 2026-06-21 | CG classification sync, BV/BU ownership validation | Consumer routing and compatibility |
| `tests/helpers/failure_classification_sync.py` | 13 | 2026-06-25, 2026-06-21, 2026-06-21 | CG/BV/BU split-owner/classifier sync | Governance matrix |
| `game/final_emission_replay_projection.py` | 12 | 2026-06-25, 2026-06-21, 2026-06-21 | CG classification sync, BV/BU maintenance economics and fan-in/out | Runtime lineage, source maps, owner splits |
| `tests/test_golden_replay_projection.py` | 8 | 2026-06-25, 2026-06-22, 2026-06-21 | CF split, BX speaker parity, BV validation | Broad test compatibility, now decomposed |
| `tools/refresh_protected_replay_manifest.py` | 7 | 2026-06-21, 2026-06-17, 2026-06-16 | BV/BK/BL manifest refresh and projection simplification | Schema serialization/governance |
| `game/runtime_lineage_telemetry.py` | 8 | 2026-06-21, 2026-06-21, 2026-06-03 | BV/BU/AP ownership and fallback attribution | Event schema and recurrence identity |
| `tests/helpers/replay_observed_row_fixtures.py` | 4 | 2026-06-25, 2026-06-16, 2026-06-10 | CF routing, BL simplification, AX harness simplification | Synthetic row compatibility |
| `game/final_emission_ownership_schema.py` | 3 | 2026-06-26, 2026-06-25, 2026-06-21 | CK/CG/BU owner vocabulary | Metadata field vocabulary |
| `tests/helpers/replacement_attribution_inventory.py` | 3 | 2026-06-25, 2026-06-21, 2026-06-20 | CG/BV/BS attribution completeness | Governance consumer |
| `game/final_emission_owner_bucket_views.py` | 2 | 2026-06-26, 2026-06-21 | CK/BV read facade updates | Owner-bucket read facade |
| `game/attribution_read_views.py` | 2 | 2026-06-25, 2026-06-21 | CG/BV read facade updates | Consumer-facing read view |
| `tests/helpers/golden_replay_projection_fields.py` | 1 | 2026-06-25 | CE split | Schema extraction, not mature stability evidence |
| `tests/helpers/golden_replay_projection_fallbacks.py` | 1 | 2026-06-25 | CE split | Fallback policy extraction |
| `tests/helpers/golden_replay_projection_speaker.py` | 1 | 2026-06-25 | CE split | Speaker policy extraction |
| `tests/helpers/golden_replay_projection_manifest.py` | 1 | 2026-06-25 | CE split | Manifest extraction |
| CF focused tests (`tests/test_cf*.py`, new projection split tests) | 1 each | 2026-06-25 | CF responsibility audit implementation | Test locality and governance |

Themes visible from commit messages and prior audit reports:

- **Logic/projection changes:** runtime lineage, fallback-family precedence, speaker fallback, raw/normalized FEM projection.
- **Metadata field churn:** owner buckets, fallback authorship/source fields, `fallback_family_used` vs `realization_fallback_family`, response-type and upstream-prepared fields.
- **Ownership moves:** CE/CF split projection helpers/tests; BU/CG owner vocabulary and split-owner acceptance matrix.
- **Consumer compatibility updates:** classifier/dashboard evidence, protected manifest parity, recurrence/drift generated artifacts.

## 3. Projection Helper Churn Analysis

Projection helpers remain high-touch because they sit at a compatibility boundary between many independently owned metadata producers and many consumers that read flat replay rows.

Concrete churn drivers:

- `tests/helpers/golden_replay_projection_extractors.py` knows too much about metadata shape. `_PROTECTED_EXTRACTION_SPECS`, `_extract_fem_flat_observed_fields`, `_raw_presence_for_protected_spec`, `_normalized_presence_for_protected_spec`, `_missing_source_by_field_from_presence`, and `_unavailable_paths_for_projection` combine extraction, raw/normalized diagnostics, unavailable serialization, and consumer-routing evidence.
- `tests/helpers/golden_replay_projection.py::project_turn_observation` is still the one assembly point for snapshots, payload FEM, normalized FEM, sanitizer trace, runtime lineage, fallback family, speaker parity, text hashes, unavailable fields, and missing-source diagnostics.
- `tests/helpers/golden_replay_projection_fallbacks.py::_resolve_fallback_family` intentionally patches field-name drift by collapsing `fallback_family_used`, `realization_fallback_family`, and the lineage-derived `neutral_reply_speaker_grounding_bridge` inference into one observed `fallback_family`.
- `tests/helpers/golden_replay_projection_speaker.py::_resolve_selected_speaker_id` contains consumer compatibility logic: social-contract trace first, transcript target fallback next, then `resolution.social.npc_id`.
- `game/final_emission_replay_projection.py::build_fem_runtime_lineage_events` mixes source-family mapping, owner split projection, sealed subkind inference, mutation classification, repair-flag classification, event assembly, and event normalization handoff.
- `game/final_emission_meta.py` remains a field-owner hotspot because producers and read-side normalizers both touch it. New metadata fields usually require updates in FEM normalization, runtime lineage projection, protected extraction, classifier rows, and manifest/tests.
- Circular or near-circular ownership is present as policy fan-out rather than literal import cycles: runtime metadata defines fields; runtime projection synthesizes lineage; acceptance projection flattens it; classifier/dashboard consume it; governance tests then assert runtime and acceptance remain separate.

The CE/CF split reduced file-size concentration, but it did not fully reduce field-change amplification. A new protected field can still require edits to source registry, default registry, extraction logic, raw/normalized matrix, owner tests, manifest output, classifier evidence, dashboard row shape, and synthetic fixtures.

## 4. Metadata Field Ownership Map

| Field / group | Defining file | Primary owner | Writers | Readers | Validators | Serializers | Consumers | Ownership stability |
|---|---|---|---|---|---|---|---|---|
| `resolution_kind` | payload/resolution shape, projected in extractors | Runtime resolution, accepted by replay | API/gate result producers | `project_turn_observation` | `test_golden_replay_projection.py`, CF2 matrix | observed row | golden replay, classifier | Stable but not FEM-owned |
| `route_kind` | trace/snapshot/resolution precedence in extractors | Replay projection | route trace, snapshots, resolution payload | `_resolve_route_kind` | `test_cf1_route_and_trace_precedence.py`, CF2 | observed row | drift classifier, dashboards | Stable after CF1; multi-source |
| `selected_speaker_id` / `selected_speaker_source` | `golden_replay_projection_speaker.py` | Replay speaker projection | social trace, transcript snapshots, resolution payload | `_resolve_selected_speaker_id`, speaker risk helpers | `test_cf1_speaker_projection_precedence.py`, speaker integration tests | observed row | BX replay, classifier, risk reports | Stable but compatibility-driven |
| `final_speaker_observation` / parity | `game/final_emission_speaker_observation.py`, replay speaker module | Runtime speaker observation owns evidence; replay owns parity | final emission speaker stamping | replay speaker module, risk helpers | `test_final_emission_speaker_observation.py`, `test_golden_replay_projection_speaker_integration.py` | observed row/report | speaker risk, BX corpus | Stable but split ownership |
| `final_emitted_source` | `game/final_emission_meta.py` / extraction specs | FEM metadata owner | final emission gate/assembly/fallback paths | normalized FEM, extractors, runtime lineage | `test_final_emission_meta.py`, CF3 | observed row, lineage | classifier, dashboards | Stable field name; high-touch |
| `final_emission_mutation_lineage` | `game/final_emission_meta.py` | FEM metadata owner | final emission meta helpers | runtime projection, extractors | `test_final_emission_meta.py`, runtime lineage tests | observed row, lineage events | recurrence, attribution | Stable concept, growing consumers |
| `response_type_*` | `game/final_emission_meta.py` / response type modules | Response-type/final emission metadata | response type enforcement and FEM assembly | normalized FEM, extractors | `test_final_emission_meta.py`, CF2/CF3 | observed row | classifier/dashboard | Stable but default/unavailable rules vary |
| `upstream_prepared_emission_*` | `game/final_emission_meta.py` | Upstream-prepared emission metadata | upstream response repairs / gate metadata | normalized FEM, extractors | final emission meta and upstream projection tests | observed row | classifier/dashboard | Stable, but many defaulted nulls |
| `sanitizer_*` / sanitizer lineage fields | sanitizer trace + `game/final_emission_ownership_schema.py` | Sanitizer/output sanitizer owner; replay owns flattening | sanitizer trace producers | extractor module, runtime lineage | sanitizer projection tests, CF2 | observed row, lineage | classifier/dashboard | Ambiguous absent-source semantics for some fields |
| `opening_recovered_via_fallback` | `game/final_emission_meta.py` | Opening fallback metadata | opening fallback/response-type paths | extractors | opening fallback projection tests | observed row | classifier/dashboard | Stable |
| `opening_fallback_authorship_source` | `game/final_emission_meta.py` | Opening fallback metadata | opening fallback/final emission meta | extractors, owner bucket read view | opening fallback tests, CK changes | observed row | classifier/dashboard | Recently touched by CK; high-churn |
| `opening_fallback_owner_bucket` | `game/final_emission_owner_bucket_views.py` + ownership schema | Owner-bucket read facade | Derived from FEM fields, not always raw key | `read_opening_fallback_owner_bucket_for_replay`, classifier | `test_opening_fallback_owner_bucket.py`, fallback projection tests | observed row, lineage | classifier/dashboard/split-owner matrix | Stabilizing through read view |
| `sealed_fallback_owner_bucket` | `game/final_emission_ownership_schema.py`, FEM metadata | Sealed fallback owner | sealed fallback/final emission paths | normalized FEM, extractors | sealed fallback projection tests, CF3 | observed row, lineage | classifier/dashboard | Stable but consumer-sensitive |
| `visibility_fallback_owner_bucket` | ownership schema + visibility fallback metadata | Visibility fallback owner | visibility fallback paths | normalized FEM, extractors | visibility fallback tests, CF3 | observed row, lineage | classifier/dashboard | Stable but broad |
| `visibility_replacement_applied`, `visibility_fallback_pool`, `visibility_fallback_kind` | visibility fallback/FEM metadata | Visibility fallback owner | visibility fallback | normalized FEM, extractors, runtime lineage | visibility projection tests | observed row, lineage | classifier/dashboard/attribution | Stable but source-family mapping can collapse detail |
| `fallback_family` | `golden_replay_projection_fallbacks.py` acceptance field; source fields in FEM/provenance | Replay projection owns collapse; producers own source fields | diegetic fallback, realization provenance, lineage events | `_resolve_fallback_family`, classifiers | `test_cf1_fallback_family_precedence.py`, fallback projection tests | observed row | classifier/dashboard/drift | Ambiguous by design; consumer-driven collapse |
| `fallback_family_used` / `realization_fallback_family` | diegetic fallback / realization provenance | Runtime producers | fallback/provenance writers | acceptance projection and docs | final emission meta/fallback tests | raw/normalized FEM | replay only indirectly | Duplicated concept with explicit precedence |
| `fallback_temporal_frame` | FEM metadata | final emission/fallback metadata | fallback metadata producers | extractor | broad projection tests | observed row | classifier/dashboard | Stable but lightly tested |
| `trace.canonical_entry.*`, `trace.social_contract_trace.route_selected` | trace/debug payloads | Trace producers; replay owns dotted protected representation | debug trace and transcript runners | extractors/trace contract | `test_cf4_trace_nest_dotted_path_contract.py` | observed nested trace | replay/debug consumers | Stable after CF4; nested defaulting remains special |
| `final_text`, `scaffold_leakage` | replay projection fields module | Replay projection/text normalization | snapshot `gm_text` | projection fields/text hash helpers | broad projection tests | observed row | semantic drift, classifier | Stable; `final_text` default `""` can be confused with absent prose |
| `raw_signal_presence`, `normalized_signal_presence`, `missing_source_by_field`, `unavailable` | `golden_replay_projection_extractors.py`, CF2 contract | Replay projection diagnostics | projection assembler | classifier/dashboard/tests | CF2/CF3 tests | observed row | classifier, dashboards, projection diagnostics | Stabilizing, but high coupling |
| `runtime_lineage_events` | `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py` | Runtime lineage projection | FEM projection or payload stamps | replay projection, dashboards, tools | `test_runtime_lineage_telemetry.py`, CF1 runtime lineage tests | lineage event list | recurrence, attribution, dashboards | Stable schema but broad consumers |
| `source_family`, `mutation_classification`, `repair_kind`, owner split fields | runtime projection and failure classifier | Split between runtime projection and classifier | runtime lineage builder, classifier | dashboards, recurrence, attribution | CG/BU/CF tests | dashboard rows, reports | classifier/dashboard/recurrence | Ambiguous boundary: runtime vs post-failure classification |

Flags:

- Same concept under multiple names: `fallback_family_used` vs `realization_fallback_family`; `final_route` vs `final_emitted_source`; owner buckets vs selection/content owner tokens; runtime `mutation_kind` vs classifier `mutation_classification`.
- Defaults happen in more than one place: `protected_observation_default_row`, `observed_projection_schema_defaults`, `synthetic_observed_replay_row`, and individual projection fallbacks.
- Consumers infer meaning from absent fields: synthetic classifier rows and sparse projected turns can both contain `None`, so readers must consult `unavailable`, `raw_signal_presence`, and `missing_source_by_field`.
- Projection helpers mutate/synthesize fields late: `fallback_family`, `opening_fallback_owner_bucket`, selected speaker, scaffold leakage, `missing_source_by_field`, and lineage bridge fallback.
- Tests encode unstable ownership where integration tests assert producer -> runtime projection -> acceptance projection -> classifier in a single path.

## 5. Replay Projection Consumer Map

| Consumer | Projection data read | Raw shape or stable interface? | Churn effect | DTO/view opportunity |
|---|---|---|---|---|
| `tests/helpers/golden_replay.py` | full observed row, protected fields, runtime lineage, drift metadata | Mostly raw observed dict | High; central assertion/report hub | Use narrower assertion DTOs for protected structural, semantic, and diagnostic lanes |
| `tests/helpers/golden_replay_api.py` | `observed_turn_from_payload` / projection facade | Stable facade | Low | Expand adoption to reduce direct helper imports |
| `tests/helpers/failure_classifier.py` | `fallback_family`, owner buckets, source fields, selected speaker, lineage-derived evidence | Raw field names | High; field changes require classifier compatibility | Classifier evidence DTO with versioned field mapping |
| `tests/helpers/failure_classification_alignment.py` | protected field paths and dashboard evidence manifest | Registry API plus raw field paths | Medium-high | Keep as registry consumer but avoid importing broad projection helpers |
| `tests/helpers/failure_classification_builders.py` | synthetic observed rows and replay-shaped classifier rows | Raw shape | High; may overfit internal defaults | Build through DTO or schema-default helper only |
| `tests/helpers/failure_classification_split_owner.py` | split-owner FEM/projection rows, lineage events, classifier rows | Raw plus helper APIs | High; cross-layer matrix drives synchronized edits | Separate runtime-lineage DTO from classifier evidence DTO |
| `tests/helpers/failure_dashboard_report.py` | protected field paths, classifier evidence, observed row fields | Raw row and classifier row | High; report columns often follow field churn | Dashboard row DTO with explicit evidence columns |
| `tests/helpers/failure_dashboard_*` | drift rows, runtime lineage, recurrence events | Raw artifact row shapes | Medium | Stable artifact payload schema/version |
| `tests/helpers/replay_drift_*` | field paths, owner drift buckets, classification rows | Raw field paths | Medium | Risk/trend DTOs keyed by declared schema |
| `tests/helpers/replay_bug_recurrence_*` | recurrence keys, owner buckets, event source metadata | Event dicts | Medium-high due report volume | Versioned recurrence event schema |
| `tests/helpers/replacement_attribution_inventory.py` | owner/source/repair/mutation attribution from projection/lineage | Raw fields and lineage events | Medium | Canonical attribution read view |
| `tests/helpers/protected_semantic_mutation_measurement.py` and semantic mutation tests | projected observed rows and mutation summaries | Raw field shape | Medium | Semantic mutation DTO/view |
| `tests/helpers/speaker_contract_risk.py` | selected speaker, final speaker observation, parity | Raw observed/speaker fields | Medium | Speaker parity DTO |
| `tools/refresh_protected_replay_manifest.py` | protected field registry and manifest rows | Stable registry API | Medium; schema changes require docs updates | Already acceptable; keep registry-only |
| `tools/run_scenario_spine_validation.py` | FEM runtime lineage and transcript metadata | Runtime projection interface plus raw metadata | Medium | Transcript metadata DTO separate from protected observed row |
| `tools/projection_drift_watch.py`, fallback projection audits | protected fields and projection gaps | Raw field paths | Low-medium | Schema registry read API |
| `docs/testing/protected_replay_manifest.md` | rendered protected schema | Serializer output | High doc churn | Generated section remains correct; avoid manual edits inside generated block |
| Protected replay tests (`tests/test_golden_replay_structural_invariants.py`, trend tests, BX tests) | full observed row behavior | Stable test helper, raw assertions | Medium-high end-to-end churn | Keep as broad acceptance, add first-line owner tests |
| Projection tests (`test_cf*`, split projection tests) | source/default/presence/fallback/speaker contracts | Focused helper APIs | Low churn after split | Continue shifting assertions here |

## 6. Stability Opportunities

### Field Ownership Stabilization

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Make protected field source/default/unavailable matrix the canonical machine-readable owner map | `tests/helpers/protected_field_routing_contract.py`, `golden_replay_projection_extractors.py`, `golden_replay_projection_fields.py`, `tests/test_cf2_protected_field_routing.py` | CF2 already documents the rows, but source descriptions and extraction specs can still drift | Medium | Low | Yes |
| Promote owner-bucket read views as the only replay/classifier owner-bucket read path | `game/final_emission_owner_bucket_views.py`, `game/attribution_read_views.py`, classifier/projection helpers | Reduces duplicate derivation of opening/sealed/visibility buckets | Medium | Low-medium | Yes |
| Declare `fallback_family` as a read-side compatibility field with source-field owners listed beside it | `golden_replay_projection_fallbacks.py`, docs, `test_cf1_fallback_family_precedence.py` | Prevents future attempts to collapse runtime fields accidentally | Medium | Low | Yes |

### Helper Decomposition

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Split extractor policy into registry, extraction, presence/unavailable, and semantic-summary modules | `golden_replay_projection_extractors.py`, tests | 978 LOC mixes several policies | High | Medium | Yes, if facade-compatible |
| Split runtime lineage maps from event assembly | `game/final_emission_replay_projection.py`, `test_runtime_lineage_telemetry.py`, CF1 tests | Source-family/mutation maps change for different reasons than event assembly | Medium-high | Medium | Later after contract pinning |
| Keep `project_turn_observation` as facade but move DTO assembly helpers behind stable interfaces | `golden_replay_projection.py`, split helper modules | Reduces facade edits for field-specific changes | Medium | Medium | Yes, small first extraction |

### Consumer-Facing DTO/View Extraction

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Add classifier evidence view over observed rows | `failure_classifier.py`, `failure_classification_alignment.py`, `golden_replay_projection_fields.py` | Classifier currently reads raw projection shape | High | Medium | Yes, read-only compatibility first |
| Add speaker parity view | `golden_replay_projection_speaker.py`, `speaker_contract_risk.py`, BX tests | Speaker consumers should not know full observed row | Medium | Low | Yes |
| Add attribution view for replacement/source/owner fields | `replacement_attribution_inventory.py`, runtime lineage projection, attribution tests | Attribution currently spans runtime and classifier-inferred fields | Medium | Medium | Later |

### Canonical Metadata Defaults

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Route all synthetic replay rows through `observed_projection_schema_defaults` plus explicit overlays | `replay_observed_row_fixtures.py`, `failure_classification_builders.py`, `synthetic_replay_evidence_bridge.py` | Avoids ad hoc defaults hiding absence | Medium | Low | Yes |
| Test `None` vs unavailable vs missing-source per field family | CF2/CF3 tests, projection presence integration | Prevents consumer guesses | Medium | Low | Already partly done; extend |

### Schema/Version Boundary

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Add explicit protected observation schema version in registry/manifest | `golden_replay_projection_fields.py`, manifest tests, docs | Consumers can distinguish schema evolution from data drift | Medium | Medium | Later |
| Add artifact payload version for dashboard/recurrence events | `failure_dashboard_*`, `replay_bug_recurrence_*`, artifacts manifest | Generated artifacts churn as families | Medium | Medium | Later |

### Test Realignment

| Opportunity | Affected files | Reason | Expected churn reduction | Risk | Safe next block? |
|---|---|---|---|---|---|
| Pin first-line owner tests for field families and leave end-to-end tests broad | CF1/CF2/CF3/CF4 tests, fallback projection tests | Failure locality improves without weakening acceptance gates | High | Low | Yes |
| Stop overfitting broad tests to internal helper module shape | `test_golden_replay_projection_modules.py`, `.bak` parity strategy | Backup parity is useful short-term but preserves duplicate implementation coupling | Medium | Low-medium | Later when split settles |

## 7. Recommended Execution Plan

1. **CL1 - Machine-readable Field Ownership Rows**
   - **Goal:** Extend `protected_field_routing_contract` so owner, source/default/unavailable flags, and first-line test owner are generated directly from registry/extraction specs where possible.
   - **Files likely touched:** `tests/helpers/protected_field_routing_contract.py`, `tests/helpers/golden_replay_projection_extractors.py`, `tests/test_cf2_protected_field_routing.py`, `docs/audits/CF2_protected_field_source_default_matrix.md`.
   - **Success criteria:** Every protected field row has machine-readable owner/source/default/unavailable metadata; no manual-only routing policy remains untested.
   - **Validation commands:** `python -m pytest tests/test_cf2_protected_field_routing.py tests/test_golden_replay_projection_presence_integration.py -q`.
   - **Rollback notes:** Revert contract-helper/test changes; runtime projection output should be unchanged.

2. **CL2 - Extract Projection Presence/Unavailable Policy**
   - **Goal:** Move raw/normalized presence, `missing_source_by_field`, and unavailable routing out of the broad extractor module into a focused policy helper behind the same facade.
   - **Files likely touched:** `tests/helpers/golden_replay_projection_extractors.py`, new `tests/helpers/golden_replay_projection_presence.py`, CF2/CF3 tests.
   - **Success criteria:** `project_turn_observation` output is byte-equivalent for existing fixtures; presence-policy tests fail locally.
   - **Validation commands:** `python -m pytest tests/test_cf2_protected_field_routing.py tests/test_cf3_raw_normalized_fem_field_matrix.py tests/test_golden_replay_projection_presence_integration.py -q`.
   - **Rollback notes:** Restore presence functions to extractor module; no public field rename.

3. **CL3 - Classifier Evidence View**
   - **Goal:** Introduce a read-only classifier evidence view so classifier/dashboard code does not consume the full protected observed row directly.
   - **Files likely touched:** `tests/helpers/failure_classifier.py`, `tests/helpers/failure_classification_alignment.py`, `tests/helpers/failure_dashboard_report.py`, `tests/helpers/golden_replay_projection_fields.py`, classifier tests.
   - **Success criteria:** Classifier evidence field list is derived from a single view; existing classifier/dashboard output unchanged.
   - **Validation commands:** `python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_report.py tests/test_cf7_synthetic_row_classifier_evidence_bridge.py -q`.
   - **Rollback notes:** Keep view as unused adapter or revert imports; raw observed-row compatibility stays available.

4. **CL4 - Runtime Lineage Policy Map Split**
   - **Goal:** Separate source-family maps, mutation-classification maps, owner-split policy, and sealed-subkind inference from event assembly in `game/final_emission_replay_projection.py`.
   - **Files likely touched:** `game/final_emission_replay_projection.py`, possibly new runtime projection map module, `tests/test_runtime_lineage_telemetry.py`, `tests/test_cf1_runtime_lineage_precedence.py`.
   - **Success criteria:** `build_fem_runtime_lineage_events` remains public and output-compatible; map-specific failures localize to narrow tests.
   - **Validation commands:** `python -m pytest tests/test_runtime_lineage_telemetry.py tests/test_cf1_runtime_lineage_precedence.py tests/test_final_emission_meta.py -q`.
   - **Rollback notes:** Re-inline maps into runtime projection module; do not change event schema.

5. **CL5 - Synthetic Row Default Discipline**
   - **Goal:** Ensure synthetic rows and classifier builders always start from canonical schema defaults and overlay explicit evidence.
   - **Files likely touched:** `tests/helpers/replay_observed_row_fixtures.py`, `tests/helpers/failure_classification_builders.py`, `tests/helpers/synthetic_replay_evidence_bridge.py`, CF7 tests.
   - **Success criteria:** Tests distinguish synthetic defaults from live sparse projection; no builder invents untracked defaults.
   - **Validation commands:** `python -m pytest tests/test_cf7_synthetic_row_classifier_evidence_bridge.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q`.
   - **Rollback notes:** Revert builder internals; keep public builder outputs compatible.

6. **CL6 - Speaker Projection DTO/View**
   - **Goal:** Provide a narrow speaker projection/parity view for speaker risk and BX tests.
   - **Files likely touched:** `tests/helpers/golden_replay_projection_speaker.py`, `tests/helpers/speaker_contract_risk.py`, `tests/test_golden_replay_projection_speaker_integration.py`, `tests/test_bx_speaker_identity_golden_replay.py`.
   - **Success criteria:** Speaker consumers no longer depend on unrelated observed-row fields; parity behavior unchanged.
   - **Validation commands:** `python -m pytest tests/test_cf1_speaker_projection_precedence.py tests/test_golden_replay_projection_speaker_integration.py tests/test_bx_speaker_identity_golden_replay.py -q`.
   - **Rollback notes:** Keep old raw-field reads as compatibility fallback.

7. **CL7 - Protected Observation Schema Version Boundary**
   - **Goal:** Add explicit schema/version metadata to protected observation registry and manifest without renaming fields.
   - **Files likely touched:** `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/golden_replay_projection_manifest.py`, `tools/refresh_protected_replay_manifest.py`, manifest tests/docs.
   - **Success criteria:** Consumers can report schema version; generated manifest stays current; old field names unchanged.
   - **Validation commands:** `python -m pytest tests/test_golden_replay_projection_registry.py tests/test_golden_replay_projection_manifest.py tests/test_cf6_generated_projection_artifact_governance.py -q`.
   - **Rollback notes:** Remove version field and manifest line; no runtime behavior affected.

## 8. Validation Commands

Use the repository's configured Python environment. Commands listed here assume `python` resolves to the project runtime; in the Codex desktop environment the bundled Python path may be needed.

Targeted replay projection validation:

```powershell
python -m pytest tests/test_golden_replay_projection.py tests/test_golden_replay_projection_metadata.py tests/test_golden_replay_projection_registry.py tests/test_golden_replay_projection_manifest.py tests/test_golden_replay_projection_presence_integration.py tests/test_golden_replay_projection_fallback_integration.py tests/test_golden_replay_projection_speaker_integration.py -q
```

CF contract validation:

```powershell
python -m pytest tests/test_cf1_fallback_family_precedence.py tests/test_cf1_route_and_trace_precedence.py tests/test_cf1_runtime_lineage_precedence.py tests/test_cf1_speaker_projection_precedence.py tests/test_cf2_protected_field_routing.py tests/test_cf3_raw_normalized_fem_field_matrix.py tests/test_cf4_trace_nest_dotted_path_contract.py tests/test_cf6_generated_projection_artifact_governance.py tests/test_cf7_synthetic_row_classifier_evidence_bridge.py -q
```

Runtime metadata and lineage validation:

```powershell
python -m pytest tests/test_final_emission_meta.py tests/test_runtime_lineage_telemetry.py tests/test_opening_fallback_owner_bucket.py -q
```

Consumer validation:

```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_report.py tests/test_failure_dashboard_controlled_failures.py tests/test_replacement_attribution_inventory.py -q
```

Protected replay smoke:

```powershell
python -m pytest -m golden_replay tests/test_golden_replay_structural_invariants.py tests/test_bx_speaker_identity_golden_replay.py -q
```

Manifest/artifact governance:

```powershell
python -m pytest tests/test_golden_replay_projection_manifest.py tests/test_golden_replay_artifact_manifest.py tests/test_cf6_generated_projection_artifact_governance.py -q
python tools/refresh_protected_replay_manifest.py --check
```

Broader regression pass when implementation touches runtime metadata:

```powershell
python -m pytest tests/test_final_emission_meta.py tests/test_runtime_lineage_telemetry.py tests/test_golden_replay_projection*.py tests/test_failure_classifier.py -q
```

## 9. Files To Provide Back

Most useful follow-up files:

1. `CL_replay_projection_churn_reduction_discovery.md`
2. `docs/audits/CF_replay_projection_responsibility_discovery.md`
3. `docs/audits/CF1_projection_precedence_matrix.md`
4. `docs/audits/CF2_protected_field_source_default_matrix.md`
5. `docs/audits/CF3_raw_normalized_fem_field_matrix.md`
6. `docs/audits/CF4_trace_nest_dotted_path_contract.md`
7. `docs/audits/CF5_projection_test_failure_locality.md`
8. `tests/helpers/golden_replay_projection.py`
9. `tests/helpers/golden_replay_projection_extractors.py`
10. `tests/helpers/golden_replay_projection_fields.py`
11. `tests/helpers/golden_replay_projection_fallbacks.py`
12. `tests/helpers/golden_replay_projection_speaker.py`
13. `tests/helpers/protected_field_routing_contract.py`
14. `game/final_emission_replay_projection.py`
15. `game/final_emission_meta.py`
16. `game/final_emission_ownership_schema.py`
17. `game/final_emission_owner_bucket_views.py`
18. `game/runtime_lineage_telemetry.py`
19. `tests/helpers/failure_classifier.py`
20. `tests/helpers/failure_classification_alignment.py`
21. `tests/helpers/failure_classification_split_owner.py`
22. `tests/helpers/failure_dashboard_report.py`
23. `tests/helpers/replay_observed_row_fixtures.py`
24. `tests/test_cf1_fallback_family_precedence.py`
25. `tests/test_cf2_protected_field_routing.py`
26. `tests/test_cf3_raw_normalized_fem_field_matrix.py`
27. `tests/test_golden_replay_projection_presence_integration.py`
28. `tests/test_golden_replay_projection_speaker_integration.py`
29. `docs/testing/protected_replay_manifest.md`
30. `tools/refresh_protected_replay_manifest.py`

If raw churn output is needed separately, regenerate it with:

```powershell
git log --follow --stat -- tests/helpers/golden_replay_projection.py
git log --follow --stat -- tests/helpers/golden_replay_projection_extractors.py
git log --follow --stat -- game/final_emission_replay_projection.py
git log --follow --stat -- game/final_emission_meta.py
```
