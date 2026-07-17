# CR Protected Replay Recurrence Separation Discovery

## Executive summary

Current recurrence reporting is partially separated already, but the separation is not consistently reflected in names, report sections, or tests.

The canonical persisted protected replay history is `artifacts/golden_replay/bug_recurrence_event_log.json` -> `artifacts/golden_replay/bug_recurrence_history.json`. The current committed protected event log contains only `protected_replay_failure` events, and the history payload is marked `persistence_population: protected_replay_history`.

Session diagnostic and synthetic/test artifact recurrence are routed to `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json`, but that diagnostic log currently mixes two kinds of excluded rows:

- session diagnostic rows (`event_source: session`)
- protected-looking rows rejected from protected history by commit-worthiness policy, including ephemeral pytest artifacts, null scenarios, and synthetic drift keys

The main remaining contamination risk is not the canonical protected history writer; it is the shared "regression recurrence rate" vocabulary and legacy comparison surfaces that still expose `overall` or `legacy_unified` rates. Those rates intentionally combine populations for compatibility/audit comparison, but their names are easy to consume as a health metric.

Recommended separation strategy: keep existing public/generated fields for now, add explicitly named sibling fields and report sections for `protected_replay`, `session_diagnostic`, and `synthetic_test_artifact`, then migrate tests to protect those separated fields before deprecating legacy/unified comparison labels.

## Current recurrence surfaces

| Surface | Path | Type | Inputs | Outputs | Protected replay | Session diagnostic | Synthetic/test artifacts | Use |
|---|---|---|---|---|---|---|---|---|
| Path registry | `tests/helpers/failure_dashboard_paths.py` | test helper / report infrastructure | requested history JSON path | canonical artifact paths and derived event-log paths | yes | yes | yes, by routing destination | infrastructure |
| Recurrence writer/report renderer | `tests/helpers/failure_dashboard_recurrence.py` | test helper / generated report writer | classification rows, protected/session logs, recurrence metadata | `bug_recurrence_history.json`, `bug_recurrence_history.md`, recurrence governance docs | yes, canonical analytics use protected log | loads/writes diagnostic log | routes rejected rows to diagnostic log | health/regression/report context |
| Report hub facade | `tests/helpers/failure_dashboard_report.py` | test helper / compatibility facade | protected replay failures and assertion helpers | protected failure report, compatibility recurrence APIs | yes | yes via writer | yes via writer | diagnostics and tests |
| Event identity, routing, analytics | `tests/helpers/replay_bug_recurrence_events.py` | test helper / canonical recurrence core | classification rows and event logs | recurrence keys, event logs, source audits, rates, lane classification | yes | yes | yes, rejected by policy | regression metric core, diagnostic context |
| History/forecast/governance analytics | `tests/helpers/replay_bug_recurrence_history.py`, `tests/helpers/replay_bug_recurrence_statistics.py`, `tests/helpers/replay_bug_recurrence_serialization.py` | test helper / analytics | protected recurrence history/log payloads | trend, forecast, portfolio, governance, lifecycle, maturity, completion, graduation, confidence, outcome sections | yes | generally no | generally no, unless caller passes contaminated history | health/readiness context |
| Owner drift risk writer cascade | `tests/helpers/failure_dashboard_drift.py` | test helper / generated report writer | owner drift classifications, scorecards, stability scorecards | owner drift risk artifacts plus recurrence history side effect | yes when protected metadata is supplied | yes when rows are session/default | yes when rows fail commit-worthiness | diagnostics, side-effect writer |
| Drift report facade | `tests/helpers/replay_drift_reports.py` | test helper facade | recurrence/drift helper imports | compatibility re-exports | unknown | unknown | unknown | infrastructure |
| Protected replay failure recorder | `tests/helpers/failure_dashboard_report.py` | test helper / producer | golden replay assertion failures | `replay_failure_report.md`, owner drift artifacts, recurrence metadata | yes | no | no, except tmp-path test artifacts become diagnostic | diagnostic/regression context |
| Backfill tool | `tools/backfill_bug_recurrence_history.py` | script | committed `replay_failure_report.md` markdown | appends protected-intent rows and regenerates recurrence history | yes | no direct separate diagnostic output | protected backfill can bypass ephemeral artifact rejection by persistence intent | migration/maintenance |
| Migration tool | `tools/migrate_bug_recurrence_event_log.py` | script | legacy unified recurrence event log | protected log, session diagnostic log, history JSON/MD, migration report | yes | yes | yes, as diagnostic rejects | migration/governance |
| BV8A regeneration tool | `tools/bv8a_recurrence_history_regeneration.py` | script | protected event log and history | `artifacts/bv8a_recurrence_history.json` | yes | no | no | audit/generated artifact |
| Outcome retirement propagation | `tools/propagate_outcome_retirements.py` | script | protected event log, retirement registries, tests | updated protected log/history and closeout data | yes | no | no | governance/health context |
| Protected trend runner | `tools/run_protected_replay_trend.py` | script | protected replay runs, recurrence history/log | trend artifacts and BZ recurrence movement | yes | no direct | no direct | diagnostic/trend context |
| Runtime lineage summaries | `tests/helpers/runtime_lineage_reporting.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/test_run_scenario_spine_validation.py` | production-adjacent test helpers/tests | runtime lineage event lists | frequency and persisted recurrence bucket summaries | unknown | session diagnostic likely | unknown | diagnostic context |
| Fallback recurrence tool/report | `tools/fallback_recurrence.py`, `tests/test_fallback_recurrence.py`, `artifacts/golden_replay/fallback_recurrence_report.*` | script/test/generated report | fallback incidence inputs | fallback recurrence report | unknown | unknown | unknown | separate diagnostic context, not bug-class protected recurrence |
| Generated protected recurrence artifacts | `artifacts/golden_replay/bug_recurrence_event_log.json`, `bug_recurrence_history.json`, `bug_recurrence_history.md`, `recurrence_trajectory_history.json` | generated artifacts | protected event log and history writer | protected recurrence history and derived reports | yes | no in current committed protected log | no in current committed protected log | health/regression/report context |
| Generated diagnostic recurrence artifact | `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json` | generated artifact | rejected/session rows | diagnostic event log | contains rejected protected-looking rows | yes | yes | diagnostic context |
| Legacy archived unified log | `artifacts/golden_replay/bug_recurrence_event_log.legacy.json` | generated artifact / archive | pre-migration unified log | archived unified evidence | yes | yes | yes | migration evidence only |
| Governance docs | `docs/audits/CG_recurrence_taxonomy_registry.md`, `docs/audits/BQ35_recurrence_event_source_audit.md`, `docs/audits/BQ36_recurrence_write_path_audit.md`, `docs/audits/BQ37_recurrence_history_migration.md`, `docs/audits/CO108_recurrence_program_closeout.md`, `docs/audits/CO109_*` | governance/documentation | generated artifacts and audit conclusions | policy, ownership, closeout docs | yes | yes in migration/write-path docs | yes in migration/write-path docs | governance |

## Current contamination points

1. `calculate_regression_recurrence_rate()` in `tests/helpers/replay_bug_recurrence_events.py` is intentionally generic. Without `event_source_filter`, it calculates a unified rate over any event log or aggregate history passed to it. This is safe for protected-only logs, but contaminated for legacy unified logs or diagnostic logs.

2. `audit_recurrence_event_log_provenance()` emits `regression_recurrence_rate_comparison.overall` beside source-filtered protected/session values. This is useful as a distortion audit, but the `overall` name can be mistaken for a health metric.

3. `classify_committed_recurrence_event_log()` emits `regression_recurrence_rate_comparison.legacy_unified` beside `protected_replay_history` and `session_diagnostic_history`. This explicitly documents legacy mixing, but needs clearer downstream treatment as compatibility-only.

4. `bug_recurrence_session_diagnostic_event_log.json` is one diagnostic lane for both session rows and protected-looking rejected rows. Current committed counts observed during discovery:
   - protected log: 19 `protected_replay_failure` events
   - diagnostic log: 549 `session` events and 202 `protected_replay_failure` events rejected from protected history

5. The report title and primary field names remain generic: `Bug-Class Recurrence History` and `regression_recurrence_rate`. In the committed protected history these are protected-only by construction, but the wording does not force consumers to preserve that distinction.

6. `failure_dashboard_drift.write_owner_drift_risk_artifacts()` writes recurrence history as a side effect from owner drift rows. Depending on supplied metadata, those rows can route to protected or diagnostic lanes. This side-effect path is a risk for accidental mixed writes.

7. Historical/generated artifacts and audit snapshots (`bug_recurrence_event_log.legacy.json`, `artifacts/bv8a_recurrence_history.json`, hotspot analyses referencing `artifacts/bv8a_recurrence_history.json`) preserve prior mixed or derived views. They should remain evidence, not canonical health metrics.

## Proposed metric taxonomy

Keep existing fields and add explicitly scoped siblings first.

| Proposed key/section | Population | Meaning | Initial source |
|---|---|---|---|
| `protected_replay.recurrence_rate` or `protected_replay_regression_recurrence_rate` | commit-worthy protected replay events only | health/regression metric for protected recurrence | `calculate_protected_replay_regression_recurrence_rate()` |
| `session_diagnostic.recurrence_rate` | `event_source: session` diagnostic events only | diagnostic context; not health | `calculate_regression_recurrence_rate(..., event_source_filter="session")` |
| `synthetic_test_artifact.recurrence_rate` | events rejected due to ephemeral artifact source, synthetic drift key, null protected scenario, or unknown source | test/artifact hygiene context; not health | commit-worthiness `classifications.reason` buckets |
| `legacy_unified.recurrence_rate` | historical combined population | migration comparison only | existing `legacy_unified` / `overall` calculations |

Recommended report wording:

- "Protected Replay Recurrence" for health/regression sections
- "Session Diagnostic Recurrence" for session rows
- "Synthetic/Test Artifact Recurrence" for rejected protected-looking or synthetic rows
- "Legacy Unified Recurrence (compatibility only)" for old mixed comparisons

## Canonical owner recommendation

Canonical recurrence reporting ownership is split but coherent:

- `tests/helpers/replay_bug_recurrence_events.py` should own recurrence identity, event source taxonomy, commit-worthiness, lane routing, and scoped recurrence-rate calculations.
- `tests/helpers/failure_dashboard_recurrence.py` should own artifact writing and markdown/JSON report layout.
- `tests/helpers/failure_dashboard_paths.py` should own artifact paths only.
- `tools/migrate_bug_recurrence_event_log.py` should remain the historical migration/audit owner for unified-to-lane separation.

No single file owns all recurrence reporting. The safest canonical owner label is "recurrence core + dashboard recurrence writer": core semantics in `replay_bug_recurrence_events.py`, generated report shape in `failure_dashboard_recurrence.py`.

## Tests that will need to change

| Test file | Current protection | Classification |
|---|---|---|
| `tests/test_replay_bug_class_recurrence.py` | recurrence keys, aggregation, source filters, commit-worthiness, lane routing, protected-only trend/governance analytics | mixed: protected replay behavior, session diagnostic behavior, synthetic/test artifact behavior, legacy unified behavior |
| `tests/test_failure_dashboard_recurrence.py` | recurrence writer filenames, protected metadata writer path, report hub delegation | protected replay recurrence behavior and writer structure |
| `tests/test_failure_dashboard_report.py` | recurrence writer routing, report sections, payload structure, protected tmp routing behavior | mixed: protected replay recurrence behavior, session diagnostic routing, legacy structure |
| `tests/test_migrate_bug_recurrence_event_log.py` | unified log split, history regeneration from protected lane, diagnostic exclusion | migration from legacy mixed/unified behavior into protected/session lanes |
| `tests/test_backfill_bug_recurrence_history.py` | protected failure-report parsing and protected backfill idempotency | protected replay recurrence behavior |
| `tests/test_recurrence_trajectory_history.py` | protected trajectory snapshot serialization and markdown section | protected replay recurrence behavior |
| `tests/test_replay_bug_recurrence_decomposition.py` | facade compatibility and unchanged recurrence calculations | legacy compatibility plus core calculation behavior |
| `tests/test_replay_drift_risk.py` | owner drift risk payload; recurrence side-effect is indirect | diagnostic context, possible writer side-effect risk |
| `tests/test_replay_maintenance_metrics.py` | maintenance metrics include recurrence helper/test files | governance/maintenance, not recurrence values |
| `tests/test_recurrence_contract.py` | governance doc path and authority references | governance/documentation |

Specific legacy/mixed assertions found:

- `tests/test_replay_bug_class_recurrence.py::test_regression_recurrence_rate_from_event_log_matches_history`
- `tests/test_replay_bug_class_recurrence.py::test_calculate_regression_recurrence_rate_backward_compatible_without_filter`
- `tests/test_replay_bug_class_recurrence.py::test_audit_recurrence_event_log_provenance_reports_source_buckets`
- `tests/test_replay_bug_recurrence_decomposition.py::test_recurrence_key_and_history_calculations_unchanged`
- migration tests asserting old unified fixture splitting in `tests/test_migrate_bug_recurrence_event_log.py`

## Files likely to be touched in implementation

First implementation block should be additive and narrow:

- `tests/helpers/replay_bug_recurrence_events.py`
- `tests/helpers/failure_dashboard_recurrence.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_replay_bug_class_recurrence.py`
- `tests/test_failure_dashboard_recurrence.py`
- `tests/test_failure_dashboard_report.py`
- `tests/test_migrate_bug_recurrence_event_log.py`

Possible later blocks:

- `tools/migrate_bug_recurrence_event_log.py`
- `tools/backfill_bug_recurrence_history.py`
- `tests/helpers/failure_dashboard_drift.py`
- `tools/run_protected_replay_trend.py`
- governance docs under `docs/audits/`
- generated artifacts under `artifacts/golden_replay/` after tests are protecting the new additive fields

## Risks / unknowns

- Some dashboards or docs may consume `regression_recurrence_rate` as if it is globally meaningful. Do not rename it until consumers are inventoried or compatibility aliases exist.
- Golden/generated artifacts will need regeneration only after additive fields are stable. Do not regenerate in the discovery block.
- `bug_recurrence_session_diagnostic_event_log.json` is large and currently combines session diagnostics with rejected protected-looking rows. Splitting this into two generated artifacts may produce significant churn.
- The legacy archive `bug_recurrence_event_log.legacy.json` intentionally remains mixed. Tests should keep it as migration evidence, not a current health source.
- Some recurrence references in runtime lineage, fallback recurrence, and scenario spine validation may be adjacent recurrence concepts rather than protected replay recurrence. Marked unknown unless tied to `bug_recurrence_*` artifacts.
- `failure_dashboard_drift.write_owner_drift_risk_artifacts()` has a recurrence side effect. It needs a guard test ensuring default/session metadata cannot contaminate protected history.
- Several docs describe recurrence operational graduation and health scores. They may need wording updates once separated metric names exist.

## Recommended next implementation block

1. Add a small taxonomy helper in `replay_bug_recurrence_events.py` that classifies recurrence event populations into `protected_replay`, `session_diagnostic`, `synthetic_test_artifact`, and `legacy_unified` without changing existing calculations.
2. Add additive JSON fields under a new scoped object, for example `recurrence_rate_by_population`, while preserving `regression_recurrence_rate` and `protected_replay_regression_recurrence_rate`.
3. Add markdown sections that clearly label protected, session diagnostic, synthetic/test artifact, and legacy unified metrics. Keep current headings for compatibility in the same report.
4. Add tests that assert:
   - protected health metrics read only protected log events
   - session diagnostics are present but not health metrics
   - synthetic/test artifact rejects are counted separately from session diagnostics
   - legacy unified rates are labeled compatibility-only
5. Only after those tests pass, schedule a separate artifact regeneration block.

## Validation notes

Discovery commands used:

- `rg -n -i "recurrence|regression recurrence|replay recurrence|health metrics|golden replay|diagnostic recurrence|synthetic recurrence|contaminated|unified recurrence|recurrence rate" .`
- targeted `rg` across `tests`, `tools`, `docs`, `audits`, and top-level `artifacts`
- PowerShell JSON summaries of committed protected and diagnostic recurrence event logs

No generated artifacts were updated.
