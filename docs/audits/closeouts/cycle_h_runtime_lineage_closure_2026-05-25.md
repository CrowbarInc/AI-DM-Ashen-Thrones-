# Cycle H Closure Report

## Objectives

Cycle H established a read-only runtime lineage projection for finalized runtime
evidence. The instrumentation is intended to count selected fallbacks, speaker
repairs, mutation categories, gate outcomes, and recurring signatures without
changing emitted prose, gameplay behavior, legality decisions, evaluator
scoring, replay comparison behavior, or scenario-spine pass/fail criteria.

This closure audit verifies the implemented H1-H5 surfaces as of 2026-05-25.

## Implemented Components

| Surface | Producer | Consumer | Artifact location | Intended purpose |
|---|---|---|---|---|
| Runtime lineage vocabulary | `game/runtime_lineage_telemetry.py` (`make_runtime_lineage_event`, `build_recurrence_key`, normalizers) | FEM, scenario-spine and dashboard/replay helpers | In-memory JSON-serializable event dictionaries | Stable event schema and recurrence identity |
| FEM lineage projection | `game/final_emission_meta.py::build_fem_runtime_lineage_events` | Unified observability bundle, scenario-spine fallback projection, golden replay fallback projection | In-memory `list[dict]` | Project finalized FEM evidence into `fallback_selected`, `gate_outcome`, `speaker_repair`, and `mutation` events |
| Unified FEM bundle lineage sibling | `game/final_emission_meta.py::assemble_unified_observational_telemetry_bundle` | Supported by scenario-spine/golden replay when carried in payload metadata; directly asserted by tests | `bundle["fem_runtime_lineage_events"]` | Additive observability surface for already-projected FEM events |
| Scenario-spine per-turn persistence | `tools/run_scenario_spine_validation.py::build_transcript_turn_meta` | Aggregate scenario-spine summarizer | `transcript.json` / `run_debug.json`, `turn["meta"]["runtime_lineage_events"]` | Persist bounded lineage events next to copied turn metadata |
| Scenario-spine aggregate summary | `tools/run_scenario_spine_validation.py::build_runtime_lineage_summary` via `build_aggregate_session_health_summary` | JSON artifact writer and aggregate Markdown renderer | `aggregate_session_health_summary.json["runtime_lineage_summary"]` | Frequency and recurrence summary across branch transcripts |
| Standalone scenario-spine lineage artifact | `tools/run_scenario_spine_validation.py::write_aggregate_spine_artifacts` | Operators and downstream audit tooling | `<aggregate_dir>/runtime_lineage_summary.json` | Machine-readable aggregate lineage report |
| Aggregate operator Markdown section | `tools/run_scenario_spine_validation.py::build_aggregate_operator_summary_md` | Operators | `<aggregate_dir>/aggregate_operator_summary.md`, section `Runtime Lineage Summary` | Compact totals and recurring signatures |
| Golden replay observation projection | `tests/helpers/golden_replay.py::_runtime_lineage_events_from_payload` and `_observed_turn` | Opt-in dashboard recorder and golden replay diagnostics | `observed["runtime_lineage_events"]` | Secondary replay-side display of lineage without drift semantics |
| Failure dashboard lineage recorder and summary | `tests/helpers/failure_dashboard_report.py` (`record_runtime_lineage_events`, `build_runtime_lineage_summary`) | Markdown renderer/artifact writer | Optional `Runtime Lineage Summary` section in failure dashboard Markdown | Diagnostic totals, frequency buckets, and recurrence signatures outside classification rows |

All implemented surfaces are additive. The classification contract remains
separate from lineage data: dashboard classification rows do not acquire
runtime lineage keys.

## End-To-End Data Flow

One representative selected opening fallback travels as follows:

1. Finalized FEM already contains evidence such as
   `opening_recovered_via_fallback=True`,
   `fallback_family_used="scene_opening"`, and
   `final_emitted_source="opening_deterministic_fallback"`.
2. `game.final_emission_meta.build_fem_runtime_lineage_events(fem)` converts
   that evidence into normalized events, including:
   `fallback_selected` with `fallback_kind="scene_opening"` and
   `gate_outcome` with `gate_path="opening_fallback"`.
3. Each event receives a deterministic recurrence key from
   `game.runtime_lineage_telemetry.build_recurrence_key`, for example
   `fallback_selected:gate:game.final_emission_gate:scene_opening`.
4. `assemble_unified_observational_telemetry_bundle` can expose those events
   under `fem_runtime_lineage_events`.
5. In scenario-spine runs, `build_transcript_turn_meta` first accepts a
   preprojected `fem_runtime_lineage_events` list when present; otherwise it
   reads copied FEM and performs the same projection. It persists the bounded
   result as `meta["runtime_lineage_events"]`.
6. `build_runtime_lineage_summary` reads persisted turn events and increments
   `by_event_kind`, `by_stage`, `by_recurrence_key`,
   `fallback_frequency`, `speaker_repair_frequency`,
   `mutation_kind_frequency`, and `gate_path_frequency`. Counts greater than
   one become `recurring_events`.
7. `write_aggregate_spine_artifacts` writes the result to
   `runtime_lineage_summary.json` and the aggregate operator Markdown includes
   a compact Runtime Lineage Summary section.
8. Golden replay is a sibling secondary consumer rather than a reader of the
   scenario-spine JSON artifact: `_observed_turn` similarly prefers existing
   `fem_runtime_lineage_events` and otherwise projects from FEM into
   `observed["runtime_lineage_events"]`.
9. When failure-dashboard recording is enabled, golden replay sends only the
   separate lineage event list to `record_runtime_lineage_events`. Dashboard
   rendering aggregates and displays it without changing replay drift or
   failure classification rows.

## Coverage Assessment

| Target | Status | Evidence | Remaining Gaps |
|---|---|---|---|
| fallback frequency | Implemented | FEM projects selected opening, failed-closed, strict-social, sanitizer and replacement fallback kinds; scenario/dashboard summaries expose `fallback_frequency`; focused tests cover these paths. | Conservative by design: prepared-but-unselected fallback payloads are excluded. |
| speaker repair frequency | Implemented with conservative source coverage | FEM projects explicit speaker-contract and interaction-continuity repair evidence; summaries expose `speaker_repair_frequency`; tests cover both sources. | Only repairs recorded in finalized FEM are countable; unstamped upstream repair hints are intentionally not inferred. |
| mutation-kind frequency | Implemented with interpretation caveat | FEM projects response-type, speaker, continuity, sanitizer, fallback, repair-only and final-emission mutation kinds; summaries expose `mutation_kind_frequency`; tests cover dedup and sanitizer/post-gate paths. | Events count categorized mutation evidence, not unique changed turns. One turn may legitimately contain multiple mutation categories. |
| gate path frequency | Implemented with conservative source coverage | FEM projects accept, repair, opening, strict-social, sanitizer, visibility and replacement paths when evidence is available; summaries expose `gate_path_frequency`; tests cover representative routes. | Unknown/ambiguous gate outcomes are not broadly guessed. |
| recurrence tracking | Implemented | Stable keys are generated for every normalized event; scenario and dashboard summaries aggregate `by_recurrence_key` and render `recurring_events` for counts greater than one; tests assert deterministic keys and recurring output. | Recurrence is currently per report/run; no cross-artifact historical store is intended in Cycle H. |

## Validation Results

Broad validation command run:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_runtime_lineage_telemetry.py tests\test_final_emission_meta.py tests\test_final_emission_gate.py tests\test_final_emission_visibility.py tests\test_speaker_contract_enforcement.py tests\test_interaction_continuity_speaker_bridge.py tests\test_output_sanitizer.py tests\test_stage_diff_telemetry.py tests\test_scenario_spine_contracts.py tests\test_scenario_spine_eval.py tests\test_run_scenario_spine_validation.py tests\test_golden_replay.py tests\test_failure_classifier.py tests\test_failure_dashboard_controlled_failures.py tests\test_failure_classification_contract.py --tb=short --basetemp=codex_pytest_tmp_cycle_h_closure
```

Result: **passed**, `645 passed in 5.46s`.

Areas covered:

- Runtime lineage vocabulary, FEM projection, and observational bundle.
- Final-emission gate and visibility regressions.
- Speaker-contract and interaction-continuity repair behavior.
- Output sanitizer and stage-diff telemetry regressions.
- Scenario-spine contracts, evaluator, per-turn persistence, aggregation, and artifact writing.
- Golden replay observation and drift/classification invariants.
- Failure dashboard rendering and failure classification contract.

Patch-format check run:

```powershell
git diff --check -- game/runtime_lineage_telemetry.py game/final_emission_meta.py tools/run_scenario_spine_validation.py tests/helpers/golden_replay.py tests/helpers/failure_dashboard_report.py tests/test_runtime_lineage_telemetry.py tests/test_final_emission_meta.py tests/test_run_scenario_spine_validation.py tests/test_golden_replay.py tests/test_failure_classifier.py
```

Result: no whitespace defects; Git reported only expected Windows line-ending
conversion warnings for modified working-copy files.

## Duplication Risk Review

1. FEM deduplication is present. `build_fem_runtime_lineage_events` appends
   through recurrence-key deduplication, preventing the same projected category
   from being repeated when an explicit field and a mutation-lineage token
   encode the same event kind.
2. Multiple event kinds for one finalized turn are intentional. A selected
   fallback may produce both `fallback_selected` and `fallback_mutation`; an
   explicit speaker repair may produce both `speaker_repair` and
   `speaker_repair_mutation`. Those represent different requested frequency
   axes, not duplicate counts within one axis.
3. Sanitizer fallback can produce more than one mutation category. For example,
   selection of an empty-output sanitizer fallback can yield both
   `fallback_mutation` and `sanitizer_mutation`. This is useful lineage detail,
   but consumers must not interpret total mutation events as the number of
   distinct mutated turns.
4. Scenario-spine and failure-dashboard summaries currently implement
   compatible aggregation locally. The shapes match for Cycle H, but future
   vocabulary expansion could cause drift if only one implementation is
   extended.
5. Scenario-spine and golden replay are separate reporting lanes. Combining
   their output for the same executed turns without an identity-based merge
   would double count events.

## Orphaned Instrumentation Review

| Surface reviewed | Finding | Impact |
|---|---|---|
| `fem_runtime_lineage_events` in the unified observability bundle | Producer exists and is tested. Search did not establish that this preprojected bundle is currently shipped through a live scenario-spine or golden-replay payload by runtime code. Both consumers fall back to FEM projection, so the end-to-end artifact path remains functional. | Minor adoption gap, not a closure blocker. |
| Scenario-spine `runtime_lineage_events` | Persisted, aggregated, written to JSON, and partially rendered in aggregate Markdown; tests cover all handoffs. | No orphan found. |
| Scenario-spine summary detail fields | Frequency dictionaries and raw recurrence counts are written to JSON; Markdown intentionally renders compact totals and recurring keys only. | No orphan; JSON is the detailed artifact. |
| Recurrence keys | Generated in vocabulary helper and consumed by both scenario-spine and dashboard aggregators. | No orphan found. |
| Failure-dashboard lineage section | Reachable by explicit renderer input and by opt-in replay recording (`ASHEN_WRITE_FAILURE_DASHBOARD`); tests prove both projection and rendering. | No orphan found. |
| Dashboard classification rows | Deliberately unchanged and contract-validated separately from lineage events. | Confirms diagnostic-only design. |

## Recommended Follow-Ups

### Required before Cycle H closure

- None. No behavior or contract defect was discovered in the audited scope.

### Optional improvement

- Factor the compatible summary aggregation logic used by scenario-spine and
  failure-dashboard reporting into a shared read-side leaf helper if a later
  cycle adds fields or additional consumers.
- Document in operator-facing guidance that `mutation_kind_frequency` counts
  classified mutation evidence and may exceed distinct affected turns.
- If preprojected bundle transport becomes useful operationally, deliberately
  attach `fem_runtime_lineage_events` in a live observational payload and test
  that path; current FEM fallback projection already satisfies the Cycle H
  reporting goal.

### Future work

- Add cross-run trend storage or comparison only if recurring event history
  across artifacts becomes a product requirement.
- Consider secondary projections into additional validation dashboards only
  after their diagnostic semantics are defined.

## Closure Recommendation

**Ready To Close**

Cycle H provides a functioning additive lineage vocabulary, finalized FEM
projection, scenario-spine persistence and aggregate artifacts, and replay /
failure-dashboard secondary diagnostics. Broad regression validation passed,
and the identified gaps are interpretation or adoption refinements rather
than defects or blockers.
