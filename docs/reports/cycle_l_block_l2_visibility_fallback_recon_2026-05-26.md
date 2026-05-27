# Cycle L Block L2: Visibility Fallback Ownership Recon

Date: 2026-05-26
Scope: Reconnaissance only. No production code or test behavior changed.

## Executive summary

Visibility fallback already has a documented runtime ownership split:

- `game/narration_visibility.py` owns semantic visibility, first-mention, and
  referential-clarity legality validation.
- `game/final_emission_visibility_fallback.py` owns pure route, payload,
  metadata, owner-bucket, annotation, and logging-payload shaping. Its module
  docstring explicitly excludes fallback prose and final-output writes.
- `game/final_emission_gate.py` owns fallback selection/prose calls, output
  writes, gate sequencing, metadata application, tag/debug mutation, and
  logging calls.
- Replay, classifier, dashboard, and FEM lineage tests consume already-emitted
  evidence; they do not own visibility decision behavior.

The test suite expresses that boundary less cleanly than the opening adapter
boundary. `tests/test_final_emission_visibility.py` already declares itself the
semantic visibility owner. However, the direct characterization matrix for the
extracted pure helper module lives inside `tests/test_final_emission_gate.py`
(approximately lines 4961-6337). Therefore, a failure in the gate test file can
currently indicate either a pure visibility-helper contract regression or a
true gate integration/ordering regression.

The inspected gate integration snapshots do not appear to be needlessly
repeating the complete pure-helper metadata matrix. They assert gate-visible
effects such as final route/source, replacement tags, branch distinction, and
ordering. The apparent overbreadth is principally file co-location, not an
obvious set of assertions that can safely be narrowed in place.

Recommendation: **do not compress visibility assertions yet**. A safe L2
implementation block cannot mirror L1 until GPT decides whether pure
`game.final_emission_visibility_fallback` characterization tests should gain a
dedicated owner test module or remain intentionally co-located in the gate
suite. The existing comments already provide the low-risk ownership labeling
that L1 needed.

## Visibility test inventory by role

| Role | File / representative tests | Behavior asserted | Probable canonical owner | Assessment |
| --- | --- | --- | --- | --- |
| Owner: semantic visibility legality | `tests/test_final_emission_visibility.py`: `test_pipeline_replaces_offscene_known_npc_reference`, `test_pipeline_replaces_hidden_fact_assertion`, `test_pipeline_visibility_metadata_captures_entity_and_fact_matches`, `test_pipeline_visibility_enforcement_is_read_only_for_discovery_state` | Visibility validation failure/pass behavior, visible/offscene entity and fact handling, replacement application, checked evidence, state read-only guarantee | `game/narration_visibility.py` plus its finalization-facing pipeline contract | Owner, with integration-shaped entry point |
| Owner: first-mention / referential legality | `tests/test_final_emission_visibility.py`: `test_pipeline_replaces_unearned_familiarity_first_intro`, `test_pipeline_referential_clarity_replaces_same_sentence_ambiguous_pronoun`, `test_validate_player_facing_first_mentions_*`, `test_validate_player_facing_referential_clarity_records_referent_drift` | First-mention and referential-clarity validation semantics and pipeline outcomes | `game/narration_visibility.py` | Owner |
| Owner: pure visibility fallback helper shaping, physically in gate file | `tests/test_final_emission_gate.py`: `test_visibility_fallback_route_helper_decisions`, `test_visibility_fallback_owner_bucket_classifier`, `test_build_visibility_validation_observation_shapes_*`, `test_build_visibility_default_metadata_payload_collects_initial_stamp_kwargs`, `test_stamp_visibility_fallback_metadata_*`, `test_build_visibility_route_metadata_outcome_*`, `test_build_visibility_hard_replacement_plan_collects_side_effect_inputs`, `test_build_visibility_*_logging_payload_*`, `test_build_visibility_route_dispatch_context_*` | Pure route decisions, typed payloads, metadata stamp kwargs, owner-bucket classification, annotations, dispatch/context and logging-payload shape | `game/final_emission_visibility_fallback.py` | Owner assertions located in a consumer-named file; main attribution ambiguity |
| Gate consumer: branch selection and application | `tests/test_final_emission_gate.py`: `test_visibility_safe_fallback_final_emitted_source_snapshot`, `test_selector_snapshot_visibility_vs_generic_terminal_distinct_markers`, `test_sealed_branch_order_accept_path_visibility_before_n4`, `test_sealed_branch_order_replace_path_visibility_before_n4` | Visibility replacement reaches final output/FEM, is distinguished from other sealed branches, and runs in final-gate order | `game/final_emission_gate.py` | Correct gate consumer/integration coverage |
| Gate consumer: first-mention/referential integration | `tests/test_final_emission_gate.py`: Block E strict-social referential substitution tests around lines 1240-1494; visibility-related enforcement calls later in gate runtime | Gate-side local substitution/fallback application and side effects under strict-social routing | `game/final_emission_gate.py` | Gate consumer; adjacent but should not be folded into visibility-helper compression |
| Downstream projection: FEM lineage | `tests/test_final_emission_meta.py::test_assemble_unified_observational_bundle_exposes_fem_runtime_lineage_sibling_surface` | A preexisting `visibility_replacement_applied` signal yields generic lineage events (`visibility_or_scene_replacement`, `visibility_or_scene_replaced`) | `game/final_emission_meta.py` projection surface | Downstream projection lock |
| Downstream projection: replay transport | `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence` | Existing FEM visibility fields are copied into the observed replay turn | `tests/helpers/golden_replay.py` | Downstream projection lock |
| Downstream projection: classifier contract | `tests/test_failure_classifier.py::test_failure_classifier_preserves_projected_visibility_fallback_evidence`, `test_failure_classification_contract_rejects_invalid_visibility_owner_bucket` | Projected visibility evidence survives classification; invalid owner buckets are rejected | `tests/helpers/failure_classifier.py` | Downstream diagnostic/schema lock |
| Downstream projection: dashboard | `tests/test_failure_dashboard_controlled_failures.py`: controlled case `visibility_fallback_owner_bucket`; `test_controlled_failure_probe_dashboard_contains_triage_columns` | Diagnostic artifact displays projected visibility owner/replacement/pool/kind evidence | `tests/helpers/failure_dashboard_report.py` | Downstream diagnostic rendering lock |
| Smoke | No visibility-specific smoke test in the requested set is a candidate owner. Pipeline finalization tests exercise integrated flow, while replay/classifier/dashboard cases use synthetic projection payloads. | End-to-end survival or diagnostic projection only | Direct owner tests above | Do not promote downstream tests into semantic owners |

### Direct answers

1. **Which tests directly own visibility fallback decision/payload behavior?**

   - Semantic legality decisions are owned by
     `tests/test_final_emission_visibility.py` against
     `game/narration_visibility.py`.
   - Pure fallback route/payload/metadata/owner-bucket shaping is directly
     tested in the Block AI visibility helper cluster inside
     `tests/test_final_emission_gate.py`, against
     `game/final_emission_visibility_fallback.py`.

2. **Which gate tests only need to assert ordering, application, or FEM
   propagation?**

   - The visibility final-output snapshot and sealed-branch selector/order
     tests around `tests/test_final_emission_gate.py:4690-4946` are gate
     consumer tests. Their appropriate obligations are output replacement,
     route/source/FEM propagation, branch-specific markers, and sequencing.

3. **Which replay/classifier/dashboard tests are downstream
   projection/diagnostic locks?**

   - `tests/test_final_emission_meta.py::test_assemble_unified_observational_bundle_exposes_fem_runtime_lineage_sibling_surface`
   - `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence`
   - `tests/test_failure_classifier.py::test_failure_classifier_preserves_projected_visibility_fallback_evidence`
   - `tests/test_failure_classifier.py::test_failure_classification_contract_rejects_invalid_visibility_owner_bucket`
   - The `visibility_fallback_owner_bucket` controlled case and dashboard
     column test in `tests/test_failure_dashboard_controlled_failures.py`

4. **Are gate tests deeply reasserting visibility helper-owned metadata?**

   Yes, but chiefly because the pure helper's direct owner matrix is housed in
   `tests/test_final_emission_gate.py`. The tests from
   `test_build_visibility_default_metadata_payload_collects_initial_stamp_kwargs`
   through route/dispatch/logging payload builders deeply assert helper-owned
   metadata and object shapes. They are not merely downstream gate tests and
   must not be narrowed as though they were duplicates. The genuine
   gate-consumer snapshots inspected here are comparatively narrow.

5. **Is there a safe L2 implementation block similar to L1?**

   Not yet. L1 had a dedicated adapter owner suite and clearly adapter-shaped
   assertions in the gate suite. Visibility already has role comments, but its
   pure-helper owner tests are embedded in the gate file. Narrowing those tests
   without first declaring their canonical test home risks weakening direct
   helper coverage.

## Duplicated assertion families

| Family | Files / tests involved | Common assertion repeated | Probable canonical owner | Downstream coverage that should remain narrow | Compression risk |
| --- | --- | --- | --- | --- | --- |
| Visibility legality and hard replacement | `tests/test_final_emission_visibility.py` pipeline replacement tests; `tests/test_final_emission_gate.py::test_visibility_safe_fallback_final_emitted_source_snapshot`; Block AI helper route tests | Failed visibility can result in replacement, with observable replacement evidence | Legality: `tests/test_final_emission_visibility.py`; pure route shaping: helper-owner Block AI tests | Gate should retain applied output/FEM/order only | Medium: the layers intentionally overlap at the integration boundary |
| Visibility owner-bucket tagging | `tests/test_final_emission_gate.py::test_visibility_fallback_owner_bucket_classifier`; pipeline sealed projection assertion in `tests/test_final_emission_visibility.py::test_pipeline_replaces_offscene_known_npc_reference`; golden replay, classifier, dashboard visibility evidence tests | `visibility_fallback_owner_bucket` distinguishes sealed/opening/strict-social/none visibility fallback provenance | `game/final_emission_visibility_fallback.py` direct classifier tests currently in gate file | Pipeline may pin one emitted representative value; replay/classifier/dashboard should only transport/render/validate evidence | Medium |
| Visibility metadata payload/stamping | Gate-file Block AI `test_build_visibility_*metadata*`, `test_stamp_visibility_fallback_metadata_*`, route metadata outcome tests; visibility pipeline metadata tests | Validation result and replacement fields are materialized in FEM-visible metadata | Pure helper Block AI tests | Pipeline should validate semantic evidence on representative pass/fail routes, not reproduce every typed payload combination | Medium |
| First-mention/referential follow-on metadata | `tests/test_final_emission_visibility.py` first-mention/referential pipeline tests; gate-file Block AI selected-fallback payload/logging tests; strict-social gate integration tests | Visibility-related enforcement retains default or replacement evidence for later legality stages | Validation semantics: visibility suite; payload shaping: helper-owner tests; gate side effects: gate integration | Diagnostic projection suites do not need this matrix | High: adjacent enforcement stages have separate behavior owners |
| Visibility replacement lineage projection | Gate/pipeline emits `visibility_replacement_applied`; FEM lineage, golden replay, classifier, dashboard consume it | Replacement evidence remains observable through diagnostics | Emission field production at helper/gate boundary; each projection helper owns only its transformation | Keep lineage/replay/classifier/dashboard projection assertions unchanged | Low for labeling; high if runtime assertions are removed on the assumption projections replace owner coverage |

## Failure attribution map

| Failure symptom | Current likely failing tests | Ambiguous owners | Proposed probable owner | Downstream/smoke tests that should not deeply reassert it |
| --- | --- | --- | --- | --- |
| Offscene NPC or undiscovered fact is accepted/rejected incorrectly | `tests/test_final_emission_visibility.py` pipeline and validator tests | Visibility validator versus gate replacement only if finalization changes simultaneously | `game/narration_visibility.py` / `tests/test_final_emission_visibility.py` | Gate snapshots; replay/classifier/dashboard |
| Failed visibility selects the wrong pure route (`sealed_hard_replace`, exemption, no-hard-replace) | Block AI route helper tests in `tests/test_final_emission_gate.py`; possibly pipeline output tests | File name suggests gate, but assertion is helper-owned | `game/final_emission_visibility_fallback.py` direct helper tests | Gate order/output tests; diagnostics |
| Wrong visibility fallback owner bucket or helper metadata kwargs | Block AI classifier/payload/stamping tests; possibly one pipeline projection test | Pure helper production versus diagnostic copying | `game/final_emission_visibility_fallback.py` direct helper tests | Golden replay, classifier and dashboard should only preserve/project/validate |
| Correct route selected but output, tag, FEM source, or gate order is wrong | Visibility snapshot and sealed branch order tests in `tests/test_final_emission_gate.py` | Helper route result versus gate application if both fail | `game/final_emission_gate.py` gate-consumer tests | Helper payload tests; replay/classifier/dashboard |
| Visibility evidence omitted from observed replay turn | `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence` | Runtime field absence versus replay transport omission | Replay projection helper when supplied FEM contains field; runtime owner otherwise | Classifier/dashboard should consume projected evidence only |
| Diagnostic row drops or rejects visibility evidence | `tests/test_failure_classifier.py` visibility tests | Replay versus classifier contract | Failure classifier helper | Gate and semantic visibility suites |
| Dashboard omits visibility triage evidence | `tests/test_failure_dashboard_controlled_failures.py` | Classifier row versus renderer | Dashboard renderer/helper | Runtime and replay suites |
| Generic lineage identifies visibility replacement incorrectly | `tests/test_final_emission_meta.py::test_assemble_unified_observational_bundle_exposes_fem_runtime_lineage_sibling_surface` | Field producer versus lineage projection | FEM lineage projection once the input signal is present | Replay/classifier/dashboard |

## Recommended L2 implementation block

**Recommendation: do not compress yet.**

Unlike opening fallback, visibility fallback does not currently have a dedicated
test module for its extracted adapter/helper boundary. The test suite already
contains these useful ownership notes:

- `tests/test_final_emission_visibility.py:26-29` identifies semantic
  visibility, first-mention, and referential-clarity legality ownership.
- `tests/test_final_emission_gate.py:4690-4693` identifies visibility gate
  routing/projection/order ownership.
- `tests/test_final_emission_gate.py:4959-4962` states that helper shape belongs
  to `game/final_emission_visibility_fallback.py`.

An L1-like assertion narrowing block would therefore target tests that are
currently the only direct characterization of the extracted helper, not
clearly duplicate consumer assertions. That is not a safe compression.

The next GPT decision should be one of:

1. Accept that pure visibility-helper owner tests remain intentionally
   co-located in `tests/test_final_emission_gate.py`, and make no Cycle L
   visibility compression change.
2. Authorize a later ownership-structure block that gives
   `game/final_emission_visibility_fallback.py` a dedicated test owner module
   while preserving every existing assertion and leaving gate/replay/
   classifier/dashboard behavior unchanged.

Option 2 could improve "a failing test implies probable owner," but it is a
test-location decision rather than an assertion-thinning pass and should not be
started implicitly.

## Files that should be passed back to GPT

| File | Why GPT needs it |
| --- | --- |
| `tests/test_final_emission_visibility.py` | Existing semantic owner note and direct pipeline/validator coverage establish that validation semantics already have a canonical home. |
| `tests/test_final_emission_gate.py` | Contains both true gate consumer snapshots/order tests and the pure helper characterization matrix that creates attribution ambiguity. Focus on lines approximately 4690-6337. |
| `game/final_emission_visibility_fallback.py` | Pure extracted helper boundary; its docstring excludes prose and final-output writes. |
| `game/narration_visibility.py` | Underlying semantic validators for visibility, first mention, and referential clarity. |
| `game/final_emission_gate.py` | Confirms gate-owned selection, output mutation, side effects, and sequencing around `_standard_visibility_safe_fallback` and `_apply_visibility_enforcement`. |
| `audits/cycle_d_visibility_fallback_contraction_closure_2026-05-13.md` | Prior cycle's explicit decision that pure shaping is extracted while selection/prose/output writes remain gate-owned. |
| `tests/test_final_emission_meta.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` | Confirm downstream lineage, replay, classification, and dashboard projection obligations that should remain unchanged. |

## Commands run and results

| Command | Result |
| --- | --- |
| `git status --short --branch; git diff --name-only; git ls-files --others --exclude-standard docs\reports` | Confirmed pre-existing L1/recon worktree state: modified `tests/test_final_emission_gate.py` and `tests/test_final_emission_opening_fallback.py`, plus two untracked earlier Cycle L reports. No L2 changes existed before this report. |
| `rg --files tests game docs` filtered for visibility/final-emission/failure/golden/Cycle L/D files, followed by broad `rg -n "visibility|visible|offscene|first_mention|referential|known_npc|replacement|owner_bucket|fallback" tests game docs` | Located `game/final_emission_visibility_fallback.py`, `game/narration_visibility.py`, gate runtime/tests, and diagnostic projection suites; broad output was large and used for discovery only. |
| `Get-Content -Raw docs\reports\cycle_l_test_ownership_compression_recon_2026-05-26.md; Get-Content -Raw audits\cycle_d_visibility_fallback_contraction_closure_2026-05-13.md; Get-Content -Raw docs\reports\cycle_l_block_l1_opening_adapter_gate_boundary_2026-05-26.md` | Established prior ownership conclusions and the Cycle D runtime split: pure shaping in visibility helper; selection/prose/mutation/order in gate. |
| `Get-Content tests\test_final_emission_visibility.py -TotalCount 100; rg -n "^def test_|visibility|first_mention|referential|offscene|known_npc|replacement" tests\test_final_emission_visibility.py; Get-Content game\final_emission_visibility_fallback.py -TotalCount 120; rg -n "^class |^def " game\final_emission_visibility_fallback.py game\narration_visibility.py` | Found the existing semantic-owner note in the visibility suite, its legality/pipeline tests, and the pure helper API/types. |
| `rg -n "^def test_.*(visibility|first_mention|referential)|visibility_fallback|visibility_safe|first_mention|referential_clarity|owner_bucket" tests\test_final_emission_gate.py; rg -n "_standard_visibility_safe_fallback|_apply_visibility_enforcement|_apply_first_mention_enforcement|_apply_referential_clarity_enforcement|visibility_fallback_owner_bucket|visibility_fallback_pool|visibility_fallback_kind|final_emission_visibility_fallback" game\final_emission_gate.py game\final_emission_meta.py` | Identified gate consumer snapshots/order tests and the gate-file Block AI pure helper matrix; confirmed runtime gate retains orchestration functions. |
| `rg -n "^def test_|visibility|visible|first_mention|referential|owner_bucket|fallback_kind|replacement" tests\test_final_emission_meta.py tests\test_golden_replay.py tests\test_failure_classifier.py tests\test_failure_dashboard_controlled_failures.py tests\helpers\golden_replay.py tests\helpers\failure_classifier.py tests\helpers\failure_dashboard_report.py` | Located downstream FEM lineage, replay projection, classifier/schema, and dashboard evidence tests and helper fields. |
| `Get-Content` focused ranges from `tests\test_final_emission_gate.py`, `game\final_emission_gate.py`, `tests\test_final_emission_meta.py`, `tests\test_golden_replay.py`, `tests\test_failure_classifier.py`, and `tests\test_failure_dashboard_controlled_failures.py` | Verified role comments, gate-visible obligations, runtime write/selection ownership, and downstream tests' synthetic projection nature. |
| `rg -n "Ownership note|owns|visibility fallback|game/final_emission_visibility_fallback|Cycle D|cycle_d_visibility" ...; git diff -- tests\test_final_emission_visibility.py; git diff -- tests\test_final_emission_gate.py` | Confirmed visibility ownership comments pre-exist L2 and that current gate diff is the earlier L1 opening-only change, not visibility work. |
| `rg -n "from game\.final_emission_visibility_fallback|visibility_fallback\." tests game --glob "*.py"; rg -n "validate_player_facing_visibility|validate_player_facing_first_mentions|validate_player_facing_referential_clarity" ...` | Confirmed direct pure-helper test calls are concentrated in `tests/test_final_emission_gate.py`, while semantic validators are exercised by the visibility suite and used by gate runtime. |
| Bundled-Python `pytest <file> --collect-only -q -p no:cacheprovider --disable-warnings` for each requested suite | Collection only succeeded: `tests/test_final_emission_visibility.py: 49`, `tests/test_final_emission_gate.py: 281`, `tests/test_final_emission_meta.py: 34`, `tests/test_golden_replay.py: 33`, `tests/test_failure_classifier.py: 58`, `tests/test_failure_dashboard_controlled_failures.py: 22`. No behavior tests were run. |
