# BQ3.6 Recurrence Write Path Audit

**Date:** 2026-06-19  
**Scope:** History hygiene only. No replay behavior, recurrence key, metric definition, gating, or committed artifact rewrite in this cycle.

**Related:** [BQ3.5 recurrence event source audit](./BQ35_recurrence_event_source_audit.md)

## Executive Summary

All recurrence event persistence flows through **`write_bug_recurrence_history_artifacts()`** in `tests/helpers/failure_dashboard_report.py`. BQ3.6 introduces **explicit persistence lanes** and **`is_commit_worthy_recurrence_event()`** routing so session/test noise no longer inflates committed protected replay history.

**Committed log audit (classify only, no rewrite):** 43 total events → **1 commit-worthy protected event**, **42 excluded** (32 session noise, 10 ephemeral protected/test paths).

---

## Write Path Inventory

Target artifact: `artifacts/golden_replay/bug_recurrence_event_log.json` (protected lane)  
Session diagnostic lane: `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json`

| Caller | File | `event_source` | `artifact_source` | Context | In tests? | Protected replay run? |
|---|---|---|---|---|---|---|
| `write_owner_drift_risk_artifacts()` | `failure_dashboard_report.py` | `session` (default) or `protected_replay_failure` when metadata passed | `(none)` for session; report path for protected | Called from rerun scorecard writer and protected failure report writer | **Yes** — primary session noise path | Partial — protected failure path only on replay fail |
| `write_protected_replay_failure_report_if_present()` | `failure_dashboard_report.py` | `protected_replay_failure` via `protected_replay_recurrence_event_metadata()` | `artifacts/golden_replay/replay_failure_report.md` when committed; tmp path in unit tests | Pytest session hook on protected replay failure | **Yes** — tmp paths create ephemeral protected events | **Yes** when golden replay lane fails |
| `write_rerun_drift_scorecard_artifacts()` → `write_owner_drift_risk_artifacts()` | `failure_dashboard_report.py` | `session` | `(none)` | Successful rerun drift scorecard opt-in (`ASHEN_WRITE_RERUN_DRIFT_SCORECARD`) | **Yes** | No — success path only |
| `backfill_bug_recurrence_history()` | `tools/backfill_bug_recurrence_history.py` | `protected_replay_failure` | Relative path to parsed failure report | Parses committed failure report markdown; sets `persistence_intent=backfill_protected_replay` | **Yes** in unit tests | **Yes** — intended production backfill |
| `write_bug_recurrence_history_artifacts()` direct | tests / tooling | varies | varies | Unit tests, manual invocation | **Yes** | Depends on metadata |
| `append_recurrence_events()` | `replay_bug_recurrence.py` | caller-provided | caller-provided | Low-level append helper; no file I/O | **Yes** | N/A — library primitive |

**Low-level I/O:** only `write_recurrence_event_log()` writes JSON event logs.

---

## Contamination Path Table

| Writer | Event Source | Events Produced (typical) | Protected Replay? | Commit-Worthy? |
|---|---|---:|---|---|
| Rerun drift → owner drift risk | `session` | 5 synthetic drift rows per scorecard write | No | **No** — session + null scenario + synthetic keys |
| Protected failure report (committed path) | `protected_replay_failure` | 1+ rows per failure | **Yes** | **Yes** when `artifact_source` under `artifacts/golden_replay/` |
| Protected failure report (pytest tmp path) | `protected_replay_failure` | 1 row per test failure | Test-only | **No** — ephemeral `codex_pytest_tmp` / tmp artifact |
| Backfill tool | `protected_replay_failure` + `persistence_intent=backfill_protected_replay` | 1 row per parsed failure table row | **Yes** | **Yes** — explicit backfill intent |
| Direct session test writes | `session` | varies | No | **No** |

### Synthetic drift keys identified (session-only placeholders)

| Recurrence key | Events in committed log |
|---|---:|
| `recurrence:v1:fallback_drift\|unknown\|fallback_family\|unknown` | 5 |
| `recurrence:v1:lineage_drift\|unknown\|runtime_lineage\|unknown` | 5 |
| `recurrence:v1:replay_drift_unclassified\|unknown\|final_text\|unknown` | 5 |
| `recurrence:v1:route_drift\|unknown\|route_kind\|unknown` | 5 |
| `recurrence:v1:speaker_drift\|unknown\|selected_speaker_id\|unknown` | 5 |

All have `(null)` scenario IDs and originate from session writes during rerun/risk artifact generation in pytest.

---

## BQ3.6 Implementation

### Commit-worthiness policy (`is_commit_worthy_recurrence_event`)

**Allow (protected lane):**

- `event_source=protected_replay_failure` with `artifact_source` prefix `artifacts/golden_replay/`
- Backfill rows with `persistence_intent=backfill_protected_replay` (explicit, not silent)

**Disallow (session diagnostic lane):**

- `event_source=session`
- Ephemeral artifact paths containing `codex_pytest_tmp`, `pytest_tmp`, `/tmp/`
- Synthetic drift recurrence keys (`|unknown|…|unknown`)
- Protected events with null `scenario_id`

Each rejection returns an explicit **reason string**; events are routed to the session diagnostic log, not dropped.

### Persistence lanes

| Lane | Path | Used for |
|---|---|---|
| **A. Protected replay history** | `bug_recurrence_event_log.json` | Committed recurrence history, regression metrics, future BQ5 trends |
| **B. Session diagnostic history** | `bug_recurrence_session_diagnostic_event_log.json` | Dev/test diagnostics, session drift inspection |

`write_bug_recurrence_history_artifacts()` aggregates **protected lane only** into `bug_recurrence_history.json` / `.md`.

Optional `persistence_report` out-parameter records routing counts and per-event reasons.

### Protected metric helper

`calculate_protected_replay_regression_recurrence_rate()` wraps BQ3.5 filtering over commit-worthy protected events only.

---

## Committed History Classification (No Rewrite)

Analysis of `artifacts/golden_replay/bug_recurrence_event_log.json` via `classify_committed_recurrence_event_log()`:

| Category | Count |
|---|---:|
| Total events | 43 |
| **Retained for protected history** | **1** |
| Excluded from protected history | 42 |
| Session noise (`session_event_source`) | 32 |
| Ephemeral protected/test paths | 10 |
| Synthetic drift keys (distinct) | 5 |

### Protected population after cleanup (proposed)

| Metric | Legacy unified | Protected commit-worthy |
|---|---:|---:|
| Numerator | 6 | 0 |
| Denominator | 7 | 1 |
| Rate | 85.7% | 0.0% |

The single commit-worthy event is the backfilled `vocative_override_after_prior_continuity` projection failure from `artifacts/golden_replay/replay_failure_report.md`.

---

## Migration Strategy (Recommended)

This cycle **classifies only** — it does not rewrite the committed 43-event log.

**Recommended BQ3.7 / migration block:**

1. Export current log to `bug_recurrence_event_log.legacy.json` (archive).
2. Run classification migration:
   - Move 1 commit-worthy event → protected lane (already correct if isolated)
   - Move 42 excluded events → `bug_recurrence_session_diagnostic_event_log.json`
3. Regenerate `bug_recurrence_history.json` / `.md` from protected lane only.
4. Add CI check: fail if new session events appear in protected log path.

**Immediate effect of BQ3.6 code:** new writes route correctly; existing committed contamination remains until explicit migration.

---

## Code Additions

| Symbol | Location |
|---|---|
| `RecurrenceCommitWorthinessPolicy` | `replay_bug_recurrence.py` |
| `is_commit_worthy_recurrence_event()` | `replay_bug_recurrence.py` |
| `append_recurrence_events_to_persistence_lanes()` | `replay_bug_recurrence.py` |
| `classify_committed_recurrence_event_log()` | `replay_bug_recurrence.py` |
| `calculate_protected_replay_regression_recurrence_rate()` | `replay_bug_recurrence.py` |
| `aggregate_protected_recurrence_history_from_event_log()` | `replay_bug_recurrence.py` |
| Lane routing in `write_bug_recurrence_history_artifacts()` | `failure_dashboard_report.py` |
| `persistence_intent=backfill_protected_replay` | `backfill_bug_recurrence_history.py` |

---

## Next Cycle

**BQ3.6** adds commit-worthiness filtering and persistence lanes so session/test noise no longer inflates protected history on new writes. See [BQ3.6 recurrence write path audit](./BQ36_recurrence_write_path_audit.md).

**BQ5 — Protected Replay Recurrence Trends** can proceed once migration repopulates a clean protected lane. Trend buckets should use `calculate_protected_replay_regression_recurrence_rate()` and protected event log only.
