# BV8A — Before / After Measurement Comparison

**Date:** 2026-06-21  
**Primary metric:** Recurrence History Accuracy  
**Before population:** `artifacts/golden_replay/bug_recurrence_history.json` (raw aggregated history)  
**After population:** `artifacts/bv8a_recurrence_history.json` (deduplicated + retirement metadata)

---

## Executive answer

BV8A removes the **false 8-hit recurrence signal** without modifying raw history or runtime behavior. Total protected recurrence rows drop from **11 → 4** in the deduplicated view; recurring keys drop from **1 → 0**; dominant event share drops from **72.7% → 25%**; active recurrence keys drop from **4 → 3** with **1 validated retirement**.

---

## Metric comparison

| Metric | Before | After | Delta |
|---|---:|---:|---|
| Total recurrence rows | 11 | 4 | −7 |
| Projection-key rows | 8 | 1 | −7 |
| Recurring keys (occurrence ≥ 2) | 1 | 0 | −1 |
| Dominant share (max row / total) | **72.7%** (8/11) | **25.0%** (1/4) | −47.7 pp |
| Active recurrence count | 4 | 3 | −1 |
| Unique recurrence keys | 4 | 4 | 0 |
| Regression recurrence rate | 25% (1/4) | 0% (0/4) | −25 pp |
| `validated_outcome_count` | 0 | **1** | +1 |
| False recurring projection signal | **Present** | **Removed** | — |

---

## Recurrence History Accuracy

| Dimension | Before | After |
|---|---|---|
| Rows per actual defect (projection key) | 8 | 1 |
| Duplicate/backfill inflation | 7 extra rows | 0 (deduped view) |
| Stale active tracking | Projection key `active` | Projection key `retired` |
| History reflects live defects | No (green test, active recurring) | Yes (3 active emerging keys only) |

**Primary metric verdict:** Recurrence history accuracy **improved** — the deduplicated view reflects **one historical defect** and **three active emerging keys** instead of an inflated 8-hit recurring signal.

---

## Key-level before / after

### Projection key (dominant before)

| Field | Before | After |
|---|---|---|
| occurrence_count | 8 | 1 |
| trend | recurring | retired / historical |
| status | active | retired |
| governance tier | prioritize | retired (excluded from active watch) |

### Active keys (unchanged observation count)

| Key | Before count | After count | Status |
|---|---:|---:|---|
| speaker / speaker_contract_enforcement | 1 | 1 | ACTIVE |
| fallback / final_emitted_source | 1 | 1 | ACTIVE |
| sanitizer / scaffold_leakage | 1 | 1 | ACTIVE |

---

## What did not change

| Item | Status |
|---|---|
| `artifacts/golden_replay/bug_recurrence_event_log.json` | **Unmodified** (11 raw rows) |
| Runtime speaker projection | **Unchanged** |
| Protected replay behavior | **Unchanged** |
| Golden replay test expectations | **Unchanged** |

---

## Verification

| Check | Result |
|---|---|
| Recurrence report builders (`replay_bug_recurrence.py`) | PASS — `tests/test_replay_bug_class_recurrence.py` |
| Backfill tooling | PASS — `tests/test_backfill_bug_recurrence_history.py` |
| Failure dashboard recurrence writes | PASS — `tests/test_failure_dashboard_report.py` |
| Vocative structural invariant | PASS |
| BV8A regeneration tool | PASS — `python tools/bv8a_recurrence_history_regeneration.py` |

Raw `bug_recurrence_history.json` remains the pre-BV8A aggregated view until a separate commit chooses to adopt the deduplicated population. BV8A delivers the corrected view in `artifacts/bv8a_recurrence_history.json`.

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv8a_recurrence_history.json` | `before_metrics`, `after_metrics`, deduplicated history |
| [BV8A_recurrence_audit.md](BV8A_recurrence_audit.md) | Duplicate audit |
| [BV8A_retirement_registry.md](BV8A_retirement_registry.md) | Status assignments |
| [BV8_concentration_report.md](BV8_concentration_report.md) | Pre-BV8A concentration baseline |
