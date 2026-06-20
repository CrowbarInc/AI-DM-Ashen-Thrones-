# BS - Semantic Replacement Attribution Completeness Discovery

Discovery date: 2026-06-20

Scope: semantic replacement paths and their attribution evidence. This is discovery only; no runtime behavior, ownership, or file layout was changed.

## A. Executive Summary

### Apparent pipeline

There is no single runtime `SemanticReplacement` object or universal replacement record. The effective pipeline is distributed:

1. Candidate text is created upstream and enters the final-emission gate.
2. Response-type enforcement may replace it with an opening, answer/action, or strict-social prepared/deterministic fallback.
3. The strict-social stack may compose or replace dialogue and apply additional repairs.
4. Visibility, first-mention, and referential-clarity enforcement may replace the whole text with a selected sealed fallback. Referential clarity also has a local pronoun-substitution mutation that is not marked as a whole-text replacement.
5. Generic terminal and acceptance-quality N4 paths may hard-replace text with sealed fallback prose.
6. The sanitizer may strip/drop text, perform legacy sentence rewrites when explicitly enabled, or supply an empty-output fallback.
7. `_final_emission_meta` (FEM), stage-diff snapshots, and sanitizer traces retain fragments of what happened.
8. `game.final_emission_replay_projection.build_fem_runtime_lineage_events` converts finalized FEM into read-side fallback, gate, speaker-repair, and mutation events.
9. `game.runtime_lineage_telemetry.make_runtime_lineage_event` normalizes each event and synthesizes its `recurrence_key`.
10. Golden replay detects a drift and `tests.helpers.failure_classifier.classify_replay_failure` then infers failure category, primary owner, `source_family`, repair kind, mutation source, confidence, and investigation target.

The requested five attribution dimensions therefore do not currently coexist on one write-time replacement record. Owner buckets are family-specific (`opening_`, `sealed_`, or `visibility_fallback_owner_bucket`), `source_family` is a replay-classifier concept, repair kinds are recorded only by some repair families, recurrence keys are created during read-side lineage projection, and mutation classification is represented indirectly by `mutation_kind`, FEM mutation-lineage tokens, classifier category, or `mutation_source` rather than by a canonical `mutation_classification` field.

### Where attribution originates

- Prose/source identity originates in fallback selectors and composers: `game.upstream_response_repairs`, `game.final_emission_opening_fallback`, `game.final_emission_visibility_fallback`, `game.social_exchange_emission`, `game.diegetic_fallback_narration`, and scene-emission fallback owners.
- Replacement occurrence and route identity originate in FEM write paths: `final_route`, `final_emitted_source`, replacement booleans, fallback pool/kind, response-type repair fields, and `post_gate_mutation_detected`.
- Opening authorship originates in the upstream prepared opening payload. Sealed and visibility owner buckets are computed by `game.final_emission_meta` helpers and stamped by sealed/visibility helpers.
- Event owner, fallback split owners, coarse mutation kind, and recurrence key originate or are synthesized in replay projection plus runtime-lineage normalization.
- Failure owner, `source_family`, classification confidence, investigation target, and classifier `mutation_source` originate only after golden replay has produced drift rows.

### Where attribution is lost, synthesized, or inferred

- **Lost at shape conversion:** `VisibilitySelectedFallback` contains source/kind/pool but no repair kind, recurrence key, or mutation classification. `SealedFallbackSelection.from_visibility_selection` intentionally drops visibility-only strategy and candidate-source fields.
- **Lost at coarse projection:** visibility, first-mention, and referential hard replacements collapse to `visibility_or_scene_replacement`; repair-only flags collapse to `repair_only_mutation`.
- **Missing at write time:** no universal owner bucket or `source_family` is attached to every replacement. Local referential substitution records a token and replacement phrase but no owner bucket or repair kind.
- **Synthesized:** recurrence keys are deterministic composites of event kind, stage, normalized owner, and one preferred detail token. They are not persisted by the replacement producer.
- **Inferred:** opening owner bucket can be reconstructed from FEM; sealed replacement subkind and content owner are inferred from final source/kind; failure `source_family`, failure owner, repair kind fallback, and mutation source are inferred by test-side classifier rules.
- **Potentially ambiguous:** `post_gate_mutation_detected` proves text inequality, not semantic change. Stage-diff fingerprints show ordering and change, but not a universal replacement ID or timestamp.

## B. Replacement Path Inventory

| File | Function/class | Role in replacement path | Creates replacement? | Mutates replacement? | Emits replacement? | Tests covering it | Notes |
|---|---|---|---:|---:|---:|---|---|
| `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload`, `build_upstream_prepared_emission_payload`, `merge_upstream_prepared_emission_into_gm_output` | Composes/packages opening and answer/action prepared fallback candidates | Yes, candidate | Metadata | No | response-type, opening fallback, classifier tests | Opening authorship source is explicit; selection has not happened yet. |
| `game/final_emission_response_type.py` | `enforce_response_type_contract` | Selects opening, answer/action, or dialogue contract repair text | Yes | Yes | Returns replacement to gate | response-type and final-emission tests; classifier tests | Best write-time source of `response_type_repair_kind`; opening failed-closed is represented here. |
| `game/final_emission_opening_fallback.py` | opening safe-fallback selectors and `opening_sealed_fallback_selection` | Adapts prepared opening prose into visibility/sealed selection shapes | Yes, selection | Metadata | No | `test_opening_fallback_owner_bucket.py`, final-emission tests | Carries authorship/composition evidence but no recurrence key. |
| `game/final_emission_strict_social_stack.py` | `run_strict_social_composition_trunk` and strict-social final response path | Replaces/composes strict-social output and applies repairs | Yes | Yes | Yes | strict-social/final-emission tests, FEM lineage tests | Source/fallback details are present; owner bucket is stamped only on sealed replacement metadata. |
| `game/final_emission_generic_exit.py` | non-strict replace branch | Selects terminal sealed fallback and swaps `player_facing_text` | Yes | Yes | Yes | sealed fallback, final-emission, FEM tests | Writes `final_route=replaced`, source, family/frame, and mutation detection; owner bucket is not directly added by `build_gate_replace_fem_base`. |
| `game/final_emission_visibility_fallback.py` | `apply_visibility_enforcement` | Whole-text hard replacement after failed visibility validation | Yes | Yes | Yes | `test_final_emission_visibility_fallback.py`, pipeline visibility tests | Stamps visibility owner bucket and delegates sealed route metadata. |
| `game/final_emission_visibility_fallback.py` | `apply_first_mention_enforcement` | Whole-text replacement after first-mention failure | Yes | Yes | Yes | `test_final_emission_visibility_fallback.py`, final-emission visibility tests | Replacement flag exists, but owner bucket is inherited/inferred from fallback evidence rather than first-mention-specific attribution. |
| `game/final_emission_visibility_fallback.py` | `apply_referential_clarity_enforcement` | Local pronoun substitution first; whole-text fallback if local repair fails | Yes on fallback | Yes | Yes | visibility fallback and `test_final_emission_visibility.py` | Local substitution is a semantic mutation but explicitly leaves `referential_clarity_replacement_applied=False`. |
| `game/final_emission_sealed_fallback.py` | `prepare_sealed_replacement_route_meta`, `finalize_n4_sealed_replace_fem_route_meta` | Shared sealed replacement route/FEM stamping | No prose | Metadata | Supports emit | `test_final_emission_sealed_fallback.py`, `test_final_emission_meta.py` | Adds sealed owner bucket, final route/source, family, preview, and mutation lineage. |
| `game/final_emission_terminal_pipeline.py` | acceptance-quality N4 terminal replace branch | Applies selected N4 fallback and finalizes sealed route | Yes | Yes | Yes | acceptance-quality/final-emission tests | Selection is upstream; shared helper adds route attribution. |
| `game/output_sanitizer.py` | `sanitize_player_facing_output`, `_sanitize_player_facing_output_strip_only`, legacy rewrite helpers | Drops/strips text, optionally rewrites sentences, or emits empty-output fallback | Yes on empty fallback/legacy rewrite | Yes | Yes | `test_output_sanitizer.py`, golden replay projection tests | Has its own trace and split strict-social owners, but no owner bucket or repair kind. |
| `game/final_emission_repairs.py` and adjacent repair modules | layer application helpers | Apply answer, fallback-behavior, purity, authority, tone, context, and related mutations | Usually no whole-text fallback; some rewrite | Yes | Yes through gate | layer-specific tests; FEM mutation tests | Collapsed read-side to `repair_only_mutation` unless more specific evidence exists. |
| `game/final_emission_fem_assembly.py` | `build_gate_replace_fem_base`, `merge_gate_layer_metas_into_fem` | Builds and merges replacement metadata | No | Metadata | No | `test_final_emission_meta.py` and final-emission tests | Central aggregation point, but it does not define the five-field completeness contract. |
| `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection`, `_append_fem_mutation_projections`, `build_fem_runtime_lineage_events` | Classifies finalized replacement/fallback evidence into lineage events | No | Read-side transform | Emits telemetry events | `test_final_emission_meta.py`, golden replay tests | Synthesizes owner/source/subkind and coarse `mutation_kind`; may collapse distinct paths. |
| `game/runtime_lineage_telemetry.py` | `make_runtime_lineage_event`, `build_recurrence_key` | Normalizes attribution and generates recurrence identity | No | Read-side transform | Emits normalized event | `test_runtime_lineage_telemetry.py` | Recurrence identity excludes fallback content owner by design. |
| `game/stage_diff_telemetry.py` | `record_stage_snapshot`, `record_stage_transition` | Observes ordered text/route/fallback/repair changes | No | Metadata only | Emits snapshots/events | `test_stage_diff_telemetry.py`, integration tests | Has list order and optional `timing_ms`, but no automatic wall/monotonic timestamp. |
| `tests/helpers/golden_replay.py` | `classify_golden_drift` | Discovers replay failure and invokes classifier | No | Read-side transform | Emits drift + classifications | failure dashboard/golden replay tests | Exact failure discovery point for current replay workflow. |
| `tests/helpers/failure_classifier.py` | `classify_replay_failure` | Infers category, owner, source family, repair kind, mutation source, confidence | No | Read-side transform | Emits classification rows | `test_failure_classifier.py`, controlled failure tests | Classification is synchronous and post-failure; it does not emit a replacement recurrence key. |

## C. Attribution Field Coverage

Legend: **yes** = directly carried/written by the path; **inferred** = reconstructable only from adjacent metadata or a later read-side rule; **no** = no reliable field/equivalent at that path. `mutation_kind` is accepted as the current equivalent of mutation classification; there is no literal `mutation_classification` runtime field.

| Path/function | owner bucket present? | source family present? | repair kind present? | recurrence key present? | mutation classification present? | Missing fields | Confidence |
|---|---|---|---|---|---|---|---|
| Upstream prepared opening payload | inferred | inferred | no | no | no | repair kind, recurrence key, mutation classification; owner/source require projection vocabulary | High |
| Response-type opening replacement | inferred | inferred | yes | inferred | inferred | direct owner bucket, direct source family, write-time recurrence/mutation class | High |
| Response-type answer/action prepared repair | no | inferred | yes | inferred | inferred | owner bucket; direct source family and write-time recurrence/mutation class | High |
| Strict-social replacement/composition | inferred | inferred | inferred | inferred | inferred | uniform direct fields; repair kind absent on some fallback-only branches | Medium-high |
| Generic non-strict sealed terminal replacement | inferred | inferred | no | inferred | inferred | direct owner bucket, source family, repair kind, write-time recurrence/mutation class | High |
| Visibility hard replacement | yes | inferred | no | inferred | inferred | direct source family, repair kind, write-time recurrence/mutation class | High |
| First-mention hard replacement | inferred | inferred | no | inferred | inferred | direct owner bucket/source family, repair kind, write-time recurrence/mutation class | High |
| Referential-clarity local substitution | no | inferred | no | inferred | inferred | owner bucket, direct source family, repair kind, write-time recurrence/mutation class | High |
| Referential-clarity hard fallback | inferred | inferred | no | inferred | inferred | direct owner bucket/source family, repair kind, write-time recurrence/mutation class | High |
| Acceptance-quality N4 sealed replacement | yes | inferred | inferred | inferred | inferred | direct source family, consistent repair kind, write-time recurrence/mutation class | Medium-high |
| Sanitizer strip/drop/legacy rewrite | no | inferred | no | inferred | inferred | owner bucket, direct source family, repair kind, write-time recurrence/mutation class | High |
| Sanitizer empty/strict-social fallback | no | inferred | no | inferred | inferred | owner bucket, direct source family, repair kind, write-time recurrence/mutation class | High |
| Generic repair-layer mutation | no | inferred | inferred | inferred | inferred | owner bucket; direct source family; consistent repair kind; write-time recurrence/mutation class | Medium |
| FEM lineage projection | inferred | no | inferred | yes | yes | classifier `source_family`; repair kind on non-speaker/non-response repairs | High |
| Replay failure classifier | inferred | yes | inferred | no | inferred | replacement recurrence key; literal mutation classification | High |

Important denominator rule: count only **applied semantic mutations/replacements**, not prepared candidates, validation failures, or replacement flags set to false. Prepared payload creation should be measured separately as "replacement candidates" so availability is not mistaken for emission.

## D. Completeness Scoring Proposal

### Primary metric

Define a canonical evaluated record per applied replacement or semantic mutation:

```text
required_fields = {
  owner_bucket,
  source_family,
  repair_kind,
  recurrence_key,
  mutation_classification
}

complete(record) = all five fields are non-empty and taxonomy-valid
attribution_completeness = complete_replacements / total_applied_replacements
```

Report numerator and denominator, and split the result by replacement path. Do not silently treat `unknown`, `none`, or `ambiguous` as complete unless it is an explicit allowed terminal value with evidence that classification was attempted. Recommended reporting has two rates:

- **Strict completeness:** only directly emitted fields count.
- **Resolved completeness:** direct plus deterministic inferred fields count, with `attribution_origin` per field (`direct`, `projected`, `classifier_inferred`).

### Optional weighted score

Use weights only as a diagnostic supplement, not as the headline metric:

```text
owner_bucket             0.25
source_family            0.20
repair_kind              0.20
recurrence_key           0.15
mutation_classification  0.20

weighted_completeness = sum(weight_i * field_present_and_valid_i) / total_applied_replacements
```

Owner and mutation class receive more weight because they most directly reduce investigation search space. Also report `inference_rate = inferred_field_count / populated_field_count`; a high completeness score driven mostly by inference is weaker than write-time completeness.

## E. Time-To-Classify Failure Measurement

### Current classification flow

- **Failure discovery point:** `tests.helpers.golden_replay.classify_golden_drift`, when `_add_drift`/comparison logic has populated drift buckets and flattened `drift_rows` (the list is complete immediately before the call at the end of `classify_golden_drift`).
- **Classification completion point:** return from synchronous `tests.helpers.failure_classifier.classify_replay_failure`, after each row has category, primary/secondary owner, `source_family`, repair kind, mutation source, confidence, and `investigate_first`.
- Dashboard report code may also call `classify_replay_failure` directly for supplied drift rows, so measurement should cover the classifier itself or a shared wrapper rather than only one dashboard renderer.

### Timestamp or ordering source

- Existing runtime stage-diff data gives ordered snapshot/transition lists and optional `timing_ms` values supplied by callers.
- Existing runtime-lineage events have no timestamp or sequence field.
- Existing drift/classification rows have scenario and turn indexes but no discovery/completion timestamp.
- Therefore elapsed Time-To-Classify cannot be recovered reliably from existing artifacts. Only logical ordering can be reconstructed.

### Proposed measurement

Use `time.perf_counter_ns()` in test/read-side code:

```text
failure_discovered_ns = immediately after drift_rows are finalized
classification_completed_ns = immediately after classify_replay_failure returns
time_to_classify_ms = (classification_completed_ns - failure_discovered_ns) / 1_000_000
```

Also record `drift_row_count`, `classified_row_count`, scenario ID, and whether any classification failed contract validation. Prefer aggregate percentiles (`p50`, `p95`, `max`) over wall-clock assertions in unit tests.

### Existing measurability and smallest safe instrumentation point

- Existing tests/fixtures can validate classification contents and row counts, but cannot measure historical elapsed time because timestamps are absent.
- The smallest safe instrumentation point is the read-only `classify_golden_drift` boundary around its call to `classify_replay_failure`. This changes no runtime game behavior.
- To include direct dashboard calls too, the more complete small design is a timing wrapper adjacent to `classify_replay_failure` in `tests/helpers/failure_classifier.py`, returning classifications plus optional diagnostic timing to callers that request it. Do not add timing fields to canonical classification rows unless the classification contract is intentionally versioned.
- For deterministic unit tests, inject a clock callable. Performance thresholds should live in a benchmark/diagnostic test, not ordinary correctness tests.

## F. Test Inventory

Existing directly relevant coverage:

| Test file | Coverage relevant to BS |
|---|---|
| `tests/test_final_emission_visibility_fallback.py` | Visibility owner buckets; hard replacement plans; first-mention and referential replacement payloads/logging; metadata stamping. |
| `tests/test_final_emission_visibility.py` | End-to-end visibility, first-mention, and referential replacement behavior, including referent drift. |
| `tests/test_final_emission_sealed_fallback.py` | Sealed selection adapters, owner-bucket taxonomy, route stamping helpers. |
| `tests/test_final_emission_meta.py` | FEM mutation lineage; fallback/runtime-lineage projection; sealed subkinds; split owners; sanitizer and speaker mutation events. |
| `tests/test_runtime_lineage_telemetry.py` | Event normalization, recurrence-key determinism/precedence, split owners, recurrence summaries. |
| `tests/test_stage_diff_telemetry.py` | Ordered snapshots/transitions, fingerprint changes, fallback and repair observations. |
| `tests/test_failure_classifier.py` | Owner/source-family/repair/mutation inference, owner buckets, split owners, unknown post-gate cases. |
| `tests/test_failure_classification_contract.py` | Allowed source families, owner buckets, repair kinds, classification row schema. |
| `tests/test_opening_fallback_owner_bucket.py` | Opening, visibility, and sealed bucket mapping, including ambiguous cases. |
| `tests/test_output_sanitizer.py` | Strip-only lineage, legacy rewrites, empty fallback, strict-social selection/prose owner split. |
| `tests/test_golden_replay_projection.py` and fallback projection tests | Projection of FEM/sanitizer/replacement evidence into observed replay rows. |
| `tests/test_failure_dashboard_report.py` and controlled failure tests | Drift discovery, classification attachment, and dashboard evidence. |

Missing BS tests:

1. A parameterized inventory test that executes every applied replacement/mutation family and evaluates the same five-field completeness contract.
2. A test proving prepared-but-unused candidates are excluded from `total_applied_replacements`.
3. Direct-vs-inferred provenance tests for every populated attribution field.
4. A test preventing visibility, first-mention, and referential replacements from collapsing into an indistinguishable attribution row.
5. A local referential-substitution test requiring explicit repair/mutation classification rather than relying only on token evidence.
6. Sanitizer strip, legacy rewrite, empty fallback, and strict-social fallback completeness cases.
7. Unknown/ambiguous taxonomy tests that distinguish "classification attempted" from "field never emitted."
8. Clock-injected Time-To-Classify tests for zero, one, and many drift rows, plus a diagnostic percentile report.
9. A consistency test linking an applied replacement to exactly one canonical recurrence identity, while allowing separate gate-outcome events.

## G. Candidate BS Blocks

| Block | Goal | Likely files touched | Validation command | Risk |
|---|---|---|---|---|
| BS1 - Canonical discovery fixture | Add a test-only inventory of applied replacement paths and current field origins; establish denominator without runtime changes | `tests/helpers/`, new focused test file | `pytest <new_bs_test_file> -q` | Low |
| BS2 - Completeness evaluator | Implement strict/resolved five-field scoring and per-path missing-field report in read-only tooling | new `tools/` module, focused tests | `pytest <new_bs_test_file> -q` and run tool | Low |
| BS3 - Attribution record contract | Define a bounded canonical replacement-attribution record and allowed taxonomies, initially read-side | `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py`, contract tests | `pytest tests/test_runtime_lineage_telemetry.py tests/test_final_emission_meta.py -q` | Medium |
| BS4 - Producer coverage | Stamp missing direct attribution at shared replacement application points, preserving existing ownership and source fields | `game/final_emission_sealed_fallback.py`, `game/final_emission_visibility_fallback.py`, `game/final_emission_response_type.py`, sanitizer trace code | focused final-emission/sanitizer suite | Medium-high |
| BS5 - Projection/classifier convergence | Preserve path-specific mutation classification and consume canonical attribution before heuristic inference | `game/final_emission_replay_projection.py`, `tests/helpers/failure_classifier.py`, golden replay projection helpers | lineage, classifier, and golden replay tests | Medium |
| BS6 - Time-To-Classify diagnostic | Add clock-injected read-side timing and aggregate p50/p95/max reporting without runtime gameplay instrumentation | `tests/helpers/golden_replay.py` or classifier wrapper, dashboard/report tests | `pytest tests/test_failure_classifier.py tests/test_failure_dashboard_report.py -q` | Low |

## Validation Performed

Discovery commands included repository-wide and focused `rg` searches for all requested terms and identifier variants across `game/`, `tests/`, `tools/`, `docs/`, `audits/`, and `artifacts/`.

Focused test command:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest `
  tests\test_final_emission_visibility_fallback.py `
  tests\test_final_emission_sealed_fallback.py `
  tests\test_final_emission_meta.py `
  tests\test_runtime_lineage_telemetry.py `
  tests\test_stage_diff_telemetry.py `
  tests\test_failure_classifier.py `
  tests\test_opening_fallback_owner_bucket.py `
  tests\test_output_sanitizer.py `
  -q --tb=short --basetemp=codex_pytest_tmp_bs
```

Result: **301 passed, 0 failed** in 6.3 seconds.

An initial `python -m pytest ...` attempt did not run because `python` is not on `PATH`; the bundled workspace Python command above succeeded.

## Files Inspected

Primary implementation and attribution files:

- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_generic_exit.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_strict_social_stack.py`
- `game/final_emission_response_type.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_fem_assembly.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_referential_clarity.py`
- `game/final_emission_first_mention_composition.py`
- `game/final_emission_repairs.py`
- `game/output_sanitizer.py`
- `game/upstream_response_repairs.py`
- `game/runtime_lineage_telemetry.py`
- `game/stage_diff_telemetry.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_dashboard_report.py`

Primary tests inspected:

- `tests/test_final_emission_visibility_fallback.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_final_emission_sealed_fallback.py`
- `tests/test_final_emission_meta.py`
- `tests/test_runtime_lineage_telemetry.py`
- `tests/test_stage_diff_telemetry.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_output_sanitizer.py`
- `tests/test_golden_replay_projection.py`
- `tests/test_failure_dashboard_report.py`

Prior design evidence inspected:

- `audits/proposed_failure_classification_schema.md`
- `audits/mutation_boundary_inventory.md`
- `audits/failure_owner_matrix.md`

## Files To Provide Back For Further Analysis

Minimum useful set:

1. `docs/BS_semantic_replacement_attribution_discovery.md`
2. `game/final_emission_visibility_fallback.py`
3. `game/final_emission_sealed_fallback.py`
4. `game/final_emission_replay_projection.py`
5. `game/runtime_lineage_telemetry.py`
6. `game/final_emission_meta.py`
7. `tests/helpers/failure_classifier.py`
8. `tests/helpers/golden_replay.py`
9. `tests/failure_classification_contract.py`
10. `tests/test_final_emission_meta.py`
11. `tests/test_failure_classifier.py`

Add `game/output_sanitizer.py`, `game/final_emission_response_type.py`, and `tests/test_final_emission_visibility_fallback.py` if the next analysis will design producer-level instrumentation rather than only read-side scoring.
