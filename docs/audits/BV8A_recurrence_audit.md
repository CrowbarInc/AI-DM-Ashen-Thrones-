# BV8A — Recurrence Event Audit

**Date:** 2026-06-21  
**Primary metric:** Recurrence History Accuracy  
**Scope:** Speaker projection recurrence family (`selected_speaker_id`, `vocative_override_after_prior_continuity`)  
**Sources:** `artifacts/golden_replay/bug_recurrence_event_log.json`, `artifacts/bv8a_recurrence_history.json`

---

## Executive answer

Speaker projection recurrence history contains **8 event rows for one historical defect**. Seven rows are duplicate backfill bookkeeping sharing the same run id, recurrence key, scenario, turn, and root cause. BV8A retains the canonical row (`event_index` 28) in the deduplicated view and marks the projection key **RETIRED** with green-test evidence.

Raw history is **unchanged**. Deduplication is applied only in `artifacts/bv8a_recurrence_history.json`.

---

## Scope filter

| Term | Match rule |
|---|---|
| vocative_override_after_prior_continuity | `scenario_id=vocative_override_after_prior_continuity` |
| selected_speaker_id projection mismatch | `category=projection`, `field_path=selected_speaker_id`, `speaker_drift` bucket |
| Related speaker projection keys | `recurrence_key` in speaker_drift family with `selected_speaker_id` field path |

---

## Recurrence event audit table

### Projection key — `recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py`

| event_index | run_id | duplicate_count | validation_status | Notes |
|---:|---|---:|---|---|
| 28 | `2026-06-04T22:31:59Z` | 8 | **canonical_retained** | Original row from `replay_failure_report.md`; includes `test_node_id` |
| 204 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Same root cause; `command` differs (`pytest golden replay`) |
| 219 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |
| 220 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |
| 228 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |
| 236 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |
| 244 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |
| 252 | `2026-06-04T22:31:59Z` | 8 | duplicate_removed | Backfill/migration inflation |

**Root cause (all 8 rows):** `selected_speaker_id: exact value mismatch` — expected `guard`, actual `guard_captain` on turn 1 of `vocative_override_after_prior_continuity`.

**Dedupe key:** `(recurrence_key, scenario_id, run_id, turn_index, category, field_path, investigate_first, owner_drift_bucket)`

**Why duplicates entered history:** Backfill dedupe includes `command` as a field ([BQ36_recurrence_write_path_audit.md](BQ36_recurrence_write_path_audit.md)). The original failure used the full pytest path; seven later backfills used the shorthand `pytest golden replay`, producing distinct dedupe keys for the same defect.

---

### Speaker enforcement key — `recurrence:v1:speaker_drift|speaker|selected_speaker_id|game/speaker_contract_enforcement.py`

| event_index | run_id | duplicate_count | validation_status | Notes |
|---:|---|---:|---|---|
| 253 | `2026-06-20T12:00:00Z` | 1 | **unique** | Corpus observation backfill; unrelated scenario (`wrong_speaker_strict_social_emission`) |

---

## Summary counts

| Metric | Value |
|---|---:|
| Raw projection-key rows | 8 |
| Actual historical defects | 1 |
| Duplicate/backfilled rows removed | 7 |
| Speaker-family rows audited | 9 |
| Canonical retained event_index | 28 |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bug_recurrence_event_log.json` | Unmodified raw event log (11 rows) |
| `artifacts/golden_replay/replay_failure_report.md` | Original 2026-06-04 failure classification |
| `artifacts/bv8a_recurrence_history.json` | Deduplicated view + audit metadata |
| [BV8_recurrence_inventory.md](BV8_recurrence_inventory.md) | Pre-BV8A inventory |
| [BQ36_recurrence_write_path_audit.md](BQ36_recurrence_write_path_audit.md) | Duplicate write-path analysis |
