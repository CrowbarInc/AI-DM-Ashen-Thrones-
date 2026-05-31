# Cycle I.A - Opening Owner Semantics Contract

## Scope

This contract applies to successful deterministic `scene_opening` fallback and
its fail-closed alternative. It does not change fallback prose, fallback
routing, or fixtures. Cycle I.B implements the distinction with additive
runtime-lineage attribution fields.

## Canonical Ownership

| Case | Prose/content owner | Payload packager | Selector/gate owner | Fail-closed owner |
| --- | --- | --- | --- | --- |
| Successful deterministic opening fallback | `game.opening_deterministic_fallback` | `game.upstream_response_repairs` | `game.final_emission_gate` | Not applicable |
| Fail-closed opening fallback | Not successful prepared prose | Not applicable | `game.final_emission_gate` | `game.final_emission_gate` |

For a successful deterministic opening fallback:

- The emitted text is the prepared opening fallback text composed by
  `game.opening_deterministic_fallback` and packaged by
  `game.upstream_response_repairs`.
- FEM preserves
  `opening_fallback_authorship_source=upstream_prepared_opening_fallback`.
- The opening owner bucket is `upstream-prepared`.
- Gate selection remains visible through `fallback_kind=scene_opening` and
  `gate_path=opening_fallback`.

For a fail-closed opening fallback:

- The owner bucket is `sealed-gate`.
- Runtime lineage distinguishes it as `fallback_kind=opening_failed_closed`
  and `gate_path=opening_failed_closed`.

## Existing Executable Locks

| Contract fact | Test surface |
| --- | --- |
| Composer/prepared payload produces the canonical opening text and authorship source | `tests/test_upstream_response_repairs.py::test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family` |
| Full gate emits prepared opening text and retains upstream-prepared ownership | `tests/test_final_emission_gate.py::test_canonical_final_gate_opening_fallback_fem_is_upstream_prepared_not_compatibility_local` |
| Successful replay projection retains upstream-prepared owner bucket | `tests/test_golden_replay.py::test_golden_observed_turn_projects_canonical_upstream_prepared_opening_owner_bucket` |
| Fail-closed maps to sealed-gate ownership | `tests/test_opening_fallback_owner_bucket.py::test_fail_closed_repair_kind_maps_to_sealed_gate` |
| Successful selection path and fail-closed path stay distinct while authorship bucket remains intact | `tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks` |

## Runtime Lineage Fields

`game.final_emission_meta` projects successful opening fallback selection into
runtime lineage with:

- `fallback_kind=scene_opening`
- `gate_path=opening_fallback`
- `owner=game.final_emission_gate`
- `fallback_authorship_source=upstream_prepared_opening_fallback`
- `fallback_owner_bucket=upstream-prepared`

The `owner` field records selector/event ownership. It does not identify the
author of successful opening prose. That authorship is explicitly represented
by `fallback_authorship_source` and `fallback_owner_bucket`.

Fail-closed opening fallback selection projects:

- `fallback_kind=opening_failed_closed`
- `gate_path=opening_failed_closed`
- `owner=game.final_emission_gate`
- `fallback_owner_bucket=sealed-gate`
- no `fallback_authorship_source` for successful upstream-prepared prose

## Exported Diagnostics

The authorship distinction is exposed through:

- FEM runtime-lineage events.
- Golden replay projected events and debug output.
- Failure-dashboard evidence and runtime-lineage summary output.
- Scenario-spine `runtime_lineage_summary.json`.
- Scenario-spine aggregate operator Markdown.

Scenario-spine summaries count:

- `fallback_authorship_frequency`
- `fallback_owner_bucket_frequency`
- `fallback_frequency`
- `gate_path_frequency`

## Consolidated Regression

`tests/test_run_scenario_spine_validation.py::test_cycle_i_opening_attribution_survives_prepared_payload_gate_lineage_and_diagnostics`
traces successful opening fallback from the prepared upstream payload through
full final emission, FEM lineage projection, and operator-facing scenario
summary output. The same regression pairs a fail-closed opening and verifies
that it remains `sealed-gate` rather than being attributed to the prepared
opening prose owner.

## Cycle I Status

Cycle I opening fallback authorship contraction is complete for the canonical
successful deterministic opening fallback: prose authorship, payload
packaging, gate selection, and fail-closed gate ownership are separately
observable without changing emitted text or fallback routing.
