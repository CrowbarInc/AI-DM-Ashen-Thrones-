# BQ3.5 Recurrence Event Source Audit

**Date:** 2026-06-19  
**Scope:** Audit only. No replay behavior, recurrence key, gating, artifact deletion, or history pruning changes.

**Artifacts inspected:** `artifacts/golden_replay/bug_recurrence_event_log.json`, `artifacts/golden_replay/bug_recurrence_history.json`

## Executive Summary

The committed recurrence event log contains **36 events** across **7 unique recurrence keys**. **Session-sourced writes dominate volume (75%)** and **define the unified Regression Recurrence Rate (85.7%)** through five synthetic drift keys that repeat identically five times each with `(null)` scenario IDs. Protected replay failure events account for **25% of volume** but only **2 unique keys**; **8 of 9 protected events** reference ephemeral `codex_pytest_tmp/...` report paths rather than the committed `artifacts/golden_replay/replay_failure_report.md`.

**Recommendation: B — Separate protected replay and session metrics.** Use **protected-replay-only** as the primary regression recurrence signal for BQ trend work; retain session as a secondary diagnostic population until write paths are scoped.

---

## Event Source Distribution

| Source | Events | Percent |
|---|---:|---:|
| `session` | 27 | 75.0% |
| `protected_replay_failure` | 9 | 25.0% |
| `unknown` | 0 | 0.0% |
| **Total** | **36** | **100%** |

**Totals:** 36 events, 7 unique recurrence keys.

### Source bucket detail

| Source | Events | Unique keys | First recorded | Last recorded |
|---|---:|---:|---|---|
| `session` | 27 | 6 | `2026-05-26T00:00:00Z` | `2026-05-30T00:00:00Z` |
| `protected_replay_failure` | 9 | 2 | `2026-05-26T00:00:00Z` | `2026-06-04T22:31:59Z` |
| `unknown` | 0 | 0 | — | — |

### Scenario ID distribution (cross-source)

| Scenario ID | Events |
|---|---:|
| `(null)` | 25 |
| `synthetic_protected_bridge` | 5 |
| `synthetic_inline_bridge` | 5 |
| `vocative_override_after_prior_continuity` | 1 |

Twenty-five events (69%) have no `scenario_id`. All five `(null)`-scenario drift keys (`fallback_drift`, `lineage_drift`, `replay_drift_unclassified`, `route_drift`, `speaker_drift|unknown`) are **session-only** with exactly five events each.

### Artifact source distribution (protected events)

| Artifact source | Events |
|---|---:|
| `(none)` — session writes | 27 |
| `codex_pytest_tmp/test_protected_replay_failure_0/replay_failure_report.md` | 4 |
| `codex_pytest_tmp/test_protected_replay_failure_1/replay_failure_report_no_identity.md` | 4 |
| `artifacts/golden_replay/replay_failure_report.md` | 1 |

Only **one** protected event is tied to the committed golden replay failure report. The remainder are test-run artifacts that were appended into the shared event log.

---

## Recurrence Key Distribution

| Source | Unique keys |
|---|---:|
| `session` | 6 |
| `protected_replay_failure` | 2 |
| `unknown` | 0 |
| **Overall (union)** | **7** |

### Per-key event counts (all sources)

| Recurrence key (abbreviated) | Total events | Session | Protected |
|---|---:|---:|---:|
| `…\|fallback_drift\|unknown\|fallback_family\|unknown` | 5 | 5 | 0 |
| `…\|lineage_drift\|unknown\|runtime_lineage\|unknown` | 5 | 5 | 0 |
| `…\|replay_drift_unclassified\|unknown\|final_text\|unknown` | 5 | 5 | 0 |
| `…\|route_drift\|unknown\|route_kind\|unknown` | 5 | 5 | 0 |
| `…\|speaker_drift\|unknown\|selected_speaker_id\|unknown` | 5 | 5 | 0 |
| `…\|speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` | 10 | 2 | 8 |
| `…\|speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` | 1 | 0 | 1 |

---

## Regression Recurrence Rate Comparison

Definition (unchanged from BQ4): numerator = keys with `occurrence_count >= 2`; denominator = unique keys in the measured population.

| Population | Numerator | Denominator | Rate |
|---|---:|---:|---:|
| **Overall (unified)** | 6 | 7 | **85.7%** |
| **Protected replay only** | 1 | 2 | **50.0%** |
| **Session only** | 6 | 6 | **100.0%** |

Filtered rates computed via `calculate_regression_recurrence_rate(event_log, event_source_filter=...)` in `tests/helpers/replay_bug_recurrence.py`.

### Source contribution to unified metric

| Contribution | Session | Protected | Notes |
|---|---:|---:|---|
| Events | 27 (75%) | 9 (25%) | Session dominates raw volume |
| Denominator keys | 6 of 7 (86%) | 2 of 7 (29%) | Speaker key shared across sources |
| Numerator keys | 6 of 6 session-only keys repeat ≥2 | 1 of 2 protected keys repeat ≥2 | Unified numerator is entirely explainable by session repetition |
| Keys exclusive to source | 5 drift keys (5 events each) | 1 projection key (1 event) | Session keys are synthetic rerun/scorecard noise |

The unified **85.7%** rate is **not** a protected-replay regression signal today. It largely reflects session artifact writers re-emitting the same five placeholder classification rows across test runs. The protected-only rate (**50%**, 1/2) is thin but aligns with the one governed failure key (`speaker|selected_speaker_id|game/speaker_contract_enforcement.py`) repeating across failure reports.

---

## Metric Distortion Assessment

### Do session events materially affect the metric?

**Yes.** Session events supply:

- **75%** of all events
- **6 of 7** unified denominator keys
- **All six** unified numerator keys when counted within their session-only populations (session-only rate = **100%**)
- Five keys that exist **only** because `write_owner_drift_risk_artifacts` / rerun scorecard paths call `write_bug_recurrence_history_artifacts` with default `event_source=session` during pytest

Without session events, the unified population would collapse to two protected keys with rate **50%**, not **85.7%**.

### Is protected replay history sufficiently populated?

**Not yet for trend reporting.** Protected replay contributes:

- **9 events** (25%), but **8** are from ephemeral pytest tmp report paths
- **1 event** from the committed `artifacts/golden_replay/replay_failure_report.md` backfill
- **2 unique keys**, only one of which has `occurrence_count >= 2` within the protected-only window

Protected replay recurrence is **measurable in principle** but **under-sampled and contaminated** by test tmp artifact paths in the shared log.

### Is trend reporting currently meaningful?

**Not on the unified metric.** A BQ5 trend over the headline 85.7% rate would primarily track session write frequency and synthetic drift fixture repetition, not protected replay regression recurrence. Trend work should wait until:

1. Metrics are reported **by source** (at minimum protected vs session)
2. Protected events are scoped to committed governance artifacts (see BQ3.6)
3. Session writes are either excluded from the primary KPI or gated behind an explicit opt-in env flag

---

## Recommendation

**B — Separate protected replay and session metrics**

### Rationale

| Option | Assessment |
|---|---|
| **A. Keep unified metric** | Rejected. Unified rate is dominated by session noise (100% session-only vs 50% protected-only). Misleading for operators evaluating protected replay regression. |
| **B. Separate protected replay and session metrics** | **Selected.** Preserves visibility into both populations, makes distortion explicit, and allows BQ5 trends on `protected_replay_failure` without losing session diagnostics during development. |
| **C. Exclude session events from recurrence reporting** | Partially aligned — session should not feed the **primary** KPI — but full exclusion now would hide useful dev-time drift signals until write paths are redesigned. Prefer B first; promote protected-only to primary headline in BQ5 rendering. |

### Implementation notes (future blocks, not in BQ3.5 scope)

- BQ5: render trend buckets **by `event_source`** using `event_source_filter` on `calculate_regression_recurrence_rate`
- BQ3.6: stop appending pytest tmp `artifact_source` paths into committed `bug_recurrence_event_log.json`; consider env-gating session recurrence writes
- Optionally mark primary dashboard metric as `protected_replay_failure` filtered rate; keep unified rate as `diagnostic_unified`

---

## Code additions (BQ3.5)

| Symbol | Location | Purpose |
|---|---|---|
| `normalized_recurrence_event_source()` | `tests/helpers/replay_bug_recurrence.py` | Bucket A/B/C classification |
| `calculate_regression_recurrence_rate(..., event_source_filter=None)` | same | Filtered rate support (additive; default unchanged) |
| `audit_recurrence_event_log_provenance()` | same | Structured provenance + rate comparison for audits |
