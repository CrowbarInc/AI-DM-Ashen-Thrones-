# Cycle O Final Emission Gate Contraction Closure - 2026-05-28

## Summary

Cycle O is complete.

Selected cluster: **replay projection helpers**.

This cluster was chosen because it reduced final-emission orchestration density with the lowest behavior risk. The extracted logic is read-side projection from finalized FEM evidence only: it does not select fallbacks, mutate output, stamp write-time FEM, or alter gate ordering. It already had strong projection/replay coverage, and Block O1 added the missing visibility/sealed projection locks before extraction.

## Blocks Completed

- **O1 Projection Lock**: Added targeted projection-lock assertions before extraction.
- **O2 Helper Extraction**: Created `game/final_emission_replay_projection.py` and moved FEM runtime-lineage projection helpers there.
- **O3 Replay Projection Confirmation**: Confirmed golden replay, scenario-spine, and runtime-lineage telemetry consumers still see the expected projected surfaces.
- **O4 Full Protection Sweep**: Ran the full suite, classified failures, and fixed the Cycle O static module-inventory expectation.
- **O4a Stale Bundle-Key Expectation Cleanup**: Updated stale unified-bundle key expectations to include `fem_runtime_lineage_events`; full suite then passed.

## Files Changed

- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_final_emission_debt_retirement.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/test_observational_telemetry_confidence.py`

## Tests Added / Strengthened

- Added `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_preserves_visibility_sealed_projection_split`.
- Strengthened `tests/test_golden_replay.py::test_golden_observed_turn_projects_visibility_fallback_evidence` to assert projected runtime-lineage events.
- Strengthened `tests/test_run_scenario_spine_validation.py::test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback` to assert visibility replacement contributes to `fallback_frequency` and `gate_path_frequency`.
- Updated stale unified observational bundle assertions in `tests/test_dead_turn_evaluation_threading.py` and `tests/test_observational_telemetry_confidence.py`.
- Updated the final-emission module debt snapshot for the new read-side projection module.

## Public API

Preserved:

- `game.final_emission_meta.build_fem_runtime_lineage_events`

The public import path now re-exports the extracted helper from `game.final_emission_replay_projection`.

## Behavior

- Behavior changed: **No**
- Gate behavior changed: **No**
- FEM write-time behavior changed: **No**
- Fixture churn: **No**
- Full suite result: **green**

## Remaining Risks / Follow-Ups

- Runtime-lineage projection remains replay/dashboard-sensitive: event ordering, recurrence keys, and owner/fallback fields should stay protected by the O1/O3 tests.
- Future changes to unified observational bundle shape should update all bundle key-set tests together.
- Further contraction should avoid mixing replay projection with opening, visibility, strict-social, or provenance tagging behavior.
