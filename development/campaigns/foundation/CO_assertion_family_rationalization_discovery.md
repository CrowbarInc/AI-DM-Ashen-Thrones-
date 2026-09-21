# CO - Assertion Family Rationalization Discovery

## Scope

Discovery-only inventory of assertion-heavy governance/test suites for measuring Semantic Duplicate Assertion Burden by owner family rather than keyword frequency. Counts are approximate AST assertion nodes plus `pytest.raises` occurrences in live `tests/`, `tools/`, and `scripts/` Python files. Generated artifacts and historical audit dumps were excluded from the burden ranking.

## Inventory Table

| File | Owner Family | Assertion Count / Density | Duplication Pattern | Intentional vs Suspect | Notes |
|---|---:|---:|---|---|---|
| `tests/test_replay_bug_class_recurrence.py` | replay, validator, ownership | ~535 asserts; ~17.0 / 100 LOC | Repeated row-shape, status, lifecycle, governance, ROI, maturity, roadmap, graduation, confidence, and event-log assertions | Suspect semantic duplication, partly intentional | Largest live assertion burden. Many tests verify the same recurrence guarantee: classification rows preserve owner/category/status identity through different summaries, reports, event logs, and lifecycle views. |
| `tests/test_failure_classifier.py` | validator, ownership, replay, fallback, speaker | ~323 asserts; ~15.8 / 100 LOC | Parametrized canonical failure cases repeatedly assert `category`, `primary_owner`, `severity`, `investigate_first`; split-owner rows assert classifier/dashboard/FEM/lineage parity | Mixed; intentionally redundant at owner boundaries, suspect inside row matrices | Good semantic owner file, but repeated guarantees about category-owner-severity routing are spread across many fixture shapes. |
| `tests/test_failure_dashboard_report.py` | diagnostic, validator, replay, ownership, speaker | ~315 asserts; ~23.2 / 100 LOC | Repeated markdown/report string assertions for protected replay failure reports, rerun scorecards, lineage summaries, recurrence artifacts | Suspect diagnostic string duplication | Dense diagnostic string suite. Many assertions check the same semantic guarantee: report includes locator, owner drift, severity, lineage, and command sections. |
| `tests/test_final_emission_opening_fallback.py` | fallback, ownership, validator | ~269 asserts; ~16.7 / 100 LOC | Repeated opening fallback metadata/source/owner bucket/authorship checks across prepared, missing payload, fail-closed, response-type, and gate paths | Mostly intentional, with suspect intra-family repetition | Strong direct owner suite. Repeated patterns include `opening_fallback_authorship_source`, `opening_fallback_failed_closed`, `fallback_family_used`, `fallback_temporal_frame`, and owner bucket assertions. |
| `tests/test_final_emission_visibility.py` | fallback, ownership, validator | ~251 asserts; ~23.0 / 100 LOC | Repeated visibility replacement metadata, tags, route/source/family, checked entity lists, first-mention/referential meta shape | Mixed; projection smoke intentional, shape repetition suspect | Comments already distinguish legality owner from projection smoke. Repeated `read_final_emission_meta_dict(out)[...]` assertions could be helper-absorbed without changing semantics. |
| `tests/ownership_closeout_delegate_locks.py` | ownership, gate, validator | ~351 asserts; ~27.1 / 100 LOC | Structural import/source-fragment locks repeatedly assert owner module callable exists, dead `feg.*` wrapper absent, and live delegate call present | Mostly intentionally redundant | High structural duplication by design. It protects delegate-collapse boundaries, not runtime behavior. Rationalization should preserve table-driven specificity. |
| `tests/test_final_emission_meta.py` | ownership, replay, fallback, speaker, validator | ~418 asserts; ~17.9 / 100 LOC | Repeated FEM metadata shape/projection assertions across route, fallback, speaker, and ownership fields | Mixed; likely large semantic burden | Not sampled deeply in this pass, but count makes it a top hotspot. Likely repeats many projection guarantees also checked by replay projection/failure classifier suites. Manual review recommended. |
| `tests/test_run_scenario_spine_validation.py` | replay, validator, diagnostic | ~225 asserts; ~16.4 / 100 LOC | Repeated CLI/artifact/summary assertions around scenario-spine run metadata, long-session summaries, and report payloads | Mixed | Useful acceptance/ops lane, but overlaps with golden replay helper summary checks and recurrence/dashboard artifact assertions. |
| `tests/test_golden_replay_projection_presence_integration.py` | replay, validator | ~26 asserts; ~17.4 / 100 LOC | Repeated protected-path represented/unavailable/raw-vs-normalized presence checks | Intentional | Focused projection owner. Low count after decomposition; useful as canonical owner for presence semantics. |
| `tests/test_golden_replay_projection_speaker_integration.py` | replay, speaker, validator | ~22 asserts; ~18.2 / 100 LOC | Repeated selected speaker / trace target projection checks | Intentional | Better rationalization target is upstream speaker tests or golden helper expectation construction, not this focused integration file. |
| `tests/test_golden_replay_projection.py` | replay, validator | ~12 asserts; ~14.8 / 100 LOC | Thin projection contract checks | Intentional | Current `tests/test_golden_replay.py` is now a 1-assert wrapper; historic burden moved into helpers and focused suites. |
| `tests/test_ownership_registry.py` | ownership | ~39 asserts; ~15.1 / 100 LOC | Registry/inventory locality checks | Intentional | Smaller than older audit reports suggested. Main ownership magnet now also lives in closeout guard modules and inventory governance tests. |
| `tests/test_inventory_governance.py` | ownership, diagnostic | ~70 asserts; ~21.5 / 100 LOC | Repeated "must not store derived diagnostic fields" string/error assertions | Suspect diagnostic duplication | Assertions verify the same governance rule through many forbidden keys. Good candidate for table-driven helper. |
| `tests/test_opening_fallback_owner_bucket.py` | fallback, ownership | ~20 asserts; ~7.0 / 100 LOC | Owner bucket classification matrix | Intentional | Low burden and semantically clear. Keep as canonical owner-bucket vocabulary check. |
| `tests/test_fallback_behavior_validator.py` | fallback, validator | ~37 asserts; ~22.8 / 100 LOC | Repeated validator pass/fail and repair-mode checks | Mostly intentional | Dense but focused. Later rationalization could use a case-table helper if many tests repeat `passed`, `failure_reasons`, and repair flags. |
| `tests/test_fallback_behavior_gate.py` | fallback, gate, validator | ~25 asserts; ~7.2 / 100 LOC | Gate-layer fallback behavior metadata and merge checks | Intentional | Cross-owner companion suite; do not collapse into validator owner without preserving gate integration semantics. |
| `tests/test_speaker_contract_enforcement.py` | speaker, validator, fallback | ~113 asserts; ~13.2 / 100 LOC | Repeated `ok`, `reason_code`, `repair_mode`, speaker label/confidence, generic fallback label checks | Mixed | Direct owner suite. Some semantic duplication can be absorbed into validation-case helpers, but redundancy across speaker contract states is valuable. |
| `tests/test_social_speaker_grounding.py` | speaker, validator | ~55 asserts; ~7.6 / 100 LOC | Repeated social grounding and active speaker assertions | Mostly intentional | Acceptance-ish companion to direct speaker contract enforcement. Review before moving assertions. |
| `tests/test_interaction_continuity_repair.py` | speaker, validator, gate | ~45 asserts; ~9.4 / 100 LOC | Repeated continuity validation/repair shape, bridge application, malformed attribution repair checks | Intentional with some helper opportunity | Speaker-adjacent, but owner is continuity repair. Do not fold into speaker family blindly. |
| `tests/test_validation_layer_contracts.py` | validator, ownership | ~30 asserts; ~21.4 / 100 LOC | Layer/kind owner maps and forbidden-kind checks | Intentional | Small, dense, canonical validation-layer ownership suite. |
| `tests/test_failure_classification_contract.py` | validator, diagnostic, ownership | ~97 asserts; ~18.8 / 100 LOC | Contract schema, dashboard evidence manifest, field count, allowed value assertions | Mixed | Overlaps with `test_failure_classifier.py` and dashboard tests but owns schema/manifest contract. |
| `tests/test_turn_pipeline_shared.py` | fallback, speaker, validator, gate | ~254 asserts; ~12.8 / 100 LOC | Repeated smoke assertions via helper calls: no validator voice, no fallback stock, response-type meta, route smoke, repair evidence | Mostly intentional acceptance smoke; helper already absorbs some duplication | Large cross-family acceptance surface. Semantic duplication is in helper invocation frequency more than raw local assert nodes. |
| `tests/test_prompt_context.py` | fallback, replay, ownership, speaker, validator | ~457 asserts; ~12.7 / 100 LOC | Broad prompt/gate/context metadata assertions | Needs manual review | Top count, but likely outside the primary target families except as downstream duplicate consumer. |
| `tests/test_social_exchange_emission.py` | fallback, speaker, validator | ~280 asserts; ~12.2 / 100 LOC | Strict-social emission route/source/fallback/speaker assertions | Needs manual review | Likely overlaps speaker fallback and gate behavior. Not sampled enough to classify safely. |

## Bucketed Findings

### Fallback Ownership/Authorship Assertions

Primary files: `tests/test_final_emission_opening_fallback.py`, `tests/test_final_emission_visibility.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_fallback_behavior_gate.py`, `tests/test_fallback_behavior_validator.py`, `tests/test_final_emission_visibility_fallback.py`, `tests/test_final_emission_sealed_fallback.py`, `tests/test_upstream_response_repairs.py`.

Repeated patterns:

- `opening_fallback_authorship_source == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED`
- `opening_fallback_failed_closed is True`
- `opening_fallback_owner_bucket == ...`
- `fallback_family_used == OPENING_FALLBACK_FAMILY`
- `fallback_temporal_frame == "first_impression"`
- `final_emitted_source == "global_scene_fallback"` or opening fallback source constants
- `sealed_fallback_owner_bucket == "sealed-gate"` and `visibility_fallback_owner_bucket == "sealed-gate"`

Assessment: direct owner redundancy is largely intentional, but the same semantic guarantee appears through prepared payload, adapter selection, response-type selection, gate output, replay projection, and classifier rows. Future rationalization should separate "owner stamps correct metadata" from "downstream projection can read metadata".

### Replay Presence/Projection Assertions

Primary files: `tests/test_golden_replay_projection_presence_integration.py`, `tests/test_golden_replay_projection_speaker_integration.py`, `tests/test_golden_replay_projection.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_replay_bug_class_recurrence.py`, `tests/helpers/golden_replay.py`.

Repeated patterns:

- protected path is either present or explicitly unavailable
- raw signal presence vs normalized signal presence
- `missing_source_by_field` routes raw-present/normalized-missing cases
- replay failure rows preserve `scenario_id`, `turn_index`, `field_path`, `expected`, `actual`
- recurrence keys ignore scenario/turn identity while preserving owner/category/field identity

Assessment: current projection integration files are compact and well-owned. The burden sits more in recurrence/reporting layers, where the same replay row identity is reasserted across summaries, reports, and event logs.

### Ownership Registry Assertions

Primary files: `tests/ownership_closeout_delegate_locks.py`, `tests/test_ownership_registry.py`, `tests/test_inventory_governance.py`, `tests/test_gate_delegate_closeout_locks.py`, `tests/test_gate_context_ownership_guards.py`, `tests/test_compat_import_governance.py`.

Repeated patterns:

- source contains owner delegate call
- source does not contain stale `game.final_emission_gate` wrapper/import/re-export
- owner callable exists on destination module
- governance JSON must not store derived diagnostic fields
- registry/inventory rows remain sorted, unique, or aligned

Assessment: structural duplication is often intentional. Semantic duplication is less about runtime behavior and more about repeated boundary-lock shape. This family should be rationalized with table-driven guard helpers, not by deleting checks.

### Speaker Attribution Assertions

Primary files: `tests/test_speaker_contract_enforcement.py`, `tests/test_social_speaker_grounding.py`, `tests/test_interaction_continuity_repair.py`, `tests/test_golden_replay_projection_speaker_integration.py`, `tests/test_bx_speaker_identity_end_to_end_parity.py`.

Repeated patterns:

- `v["ok"] is False/True`
- `v["reason_code"] == ...`
- `v["repair_mode"] == ...`
- `sig["speaker_label"] == ...`
- `selected_speaker_id`, trace target, and active interlocutor agree
- generic fallback labels are forbidden as invented speakers

Assessment: direct speaker-contract redundancy is mostly intentional because it distinguishes failure modes. Suspect duplication appears where golden replay, social grounding, and classifier all restate "wrong selected speaker routes to speaker owner/critical severity".

### Validator/Gate Assertions

Primary files: `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py`, `tests/test_final_emission_gate_diagnostics.py`, `tests/test_validation_layer_contracts.py`, `tests/test_fallback_behavior_validator.py`, `tests/test_turn_pipeline_shared.py`.

Repeated patterns:

- `category`, `primary_owner`, `severity`, `investigate_first`
- `passed/ok/checked/failed/repaired` boolean suites
- gate metadata mirrors validator result into `emission_debug`
- forbidden validator voice / retry coaching / scaffold terms absent from player text

Assessment: many checks verify the same semantic guarantee through multiple call paths: direct validator, gate-layer metadata, smoke helper, replay observation, classifier row, and dashboard report. This is exactly the family where Semantic Duplicate Assertion Burden should beat keyword counting.

### Diagnostic String Assertions

Primary files: `tests/test_failure_dashboard_report.py`, `tests/test_inventory_governance.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_ck_hotspot_compression_report.py`, `tests/test_replay_drift_longitudinal.py`.

Repeated patterns:

- markdown headings and table headers
- command snippets
- owner drift bucket labels
- field-path mismatch strings
- "must not store ..." governance errors

Assessment: this is the clearest suspect duplication family. Many assertions prove that diagnostic artifacts contain the same semantic sections through exact strings. A section-level report assertion helper could preserve intent while shrinking repeated literal checks.

## Existing Helpers and Utilities That Could Absorb Intent

| Helper / Utility | Current Role | Rationalization Opportunity |
|---|---|---|
| `tests/helpers/opening_fallback_evidence.py` | Opening fallback evidence constants and assertions: `assert_final_emission_meta_contains`, `assert_fallback_owner_bucket`, `assert_opening_fallback_source`, `assert_sealed_fallback_owner_bucket` | Best first home for repeated opening authorship/source/owner-bucket assertions. |
| `tests/helpers/emission_smoke_assertions.py` | Shared acceptance smoke: player text present, no validator voice, no retry coaching, no fallback stock, route/meta smoke, repair evidence | Already absorbs cross-suite smoke. Could add family-specific semantic wrappers to reduce repeated raw metadata asserts in acceptance files. |
| `tests/helpers/golden_replay.py` | Golden observation and profile assertions: `assert_golden_turn_observation`, `assert_protected_golden_turn_observation`, lineage/profile assertions | Good home for replay presence/profile assertion intent, but avoid making it a second owner for classifier/dashboard semantics. |
| `tests/helpers/golden_replay_projection_presence.py` | Pure projection presence/unavailable policy | Canonical owner for protected-path representation checks; keep tests focused here. |
| `tests/helpers/golden_replay_projection_speaker.py` | Speaker projection helpers | Candidate for compact speaker projection expectation helpers. |
| `tests/helpers/failure_classification_sync.py` | Canonical split-owner acceptance matrix, classifier/dashboard/projection fixture rows | Strong candidate for table-driven owner/category/severity assertions currently repeated in classifier/dashboard tests. |
| `tests/helpers/failure_dashboard_report.py` | Diagnostic row rendering and artifact writing | Could expose section/header assertion helpers or structured report parse helpers for markdown tests. |
| `tests/helpers/ownership_write_path_governance.py` | Ownership write-path drift/producer-stamp pairing checks | Useful for ownership registry rationalization, though not the main closeout-lock owner. |
| `tests/helpers/attribution_contract.py` | Shared attribution contract and validation helpers | Could absorb repeated attribution completeness/ownership assertions. |
| `tests/helpers/replay_smoke_assertions.py` | Compatibility replay smoke facade | Thin facade today; likely not the best place for new behavior unless maintaining compatibility imports. |

## Top 5 Duplication Hotspots

1. `tests/test_replay_bug_class_recurrence.py` - largest assertion count; same recurrence identity/status/governance semantics repeated across many report and lifecycle views.
2. `tests/test_failure_dashboard_report.py` - dense diagnostic string assertions; repeated section/header/owner-drift guarantees.
3. `tests/test_failure_classifier.py` - repeated category/owner/severity/investigate-first mapping across many fixture variants and split-owner paths.
4. `tests/test_final_emission_opening_fallback.py` - repeated opening fallback authorship/source/owner-bucket metadata across adapter, response-type, and gate paths.
5. `tests/ownership_closeout_delegate_locks.py` - very high structural duplication; mostly intentional but ripe for table-driven expression if future churn demands it.

## Recommended First Rationalization Target

Start with `tests/test_failure_dashboard_report.py`.

Reason: it has high density, mostly diagnostic string duplication, and lower risk of weakening core runtime semantics. A helper that asserts report sections, locator identity, owner-drift breakdown, command guidance, and lineage summary would reduce repeated literal assertions while preserving the diagnostic contract.

Second target: `tests/test_failure_classifier.py` plus `tests/helpers/failure_classification_sync.py`, but only after dashboard string consolidation, because classifier assertions are closer to semantic ownership and need more careful boundary preservation.

## Files To Pass Back For Next Implementation Block

- `tests/test_failure_dashboard_report.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_final_emission_visibility.py`
- `tests/helpers/emission_smoke_assertions.py`

## Uncertainty / Manual Review Needed

- `tests/test_final_emission_meta.py` has ~418 assertions and likely overlaps replay/ownership/fallback projection semantics, but was not deeply sampled in this pass. It needs manual review before choosing any rationalization there.
- `tests/test_prompt_context.py` and `tests/test_social_exchange_emission.py` have very high assertion counts, but their family ownership is broader than the requested target families. They may be downstream duplicate consumers rather than first-order rationalization targets.
- `tests/ownership_closeout_delegate_locks.py` has encoding artifacts in its docstring/comments and many source-fragment locks. Treat duplication there as structural governance until a specific maintenance pain is confirmed.
- Historic audit files still refer to older large `tests/test_golden_replay.py` burden. Current live state is different: `tests/test_golden_replay.py` is thin, with replay assertion intent decomposed into helpers and focused projection suites.
