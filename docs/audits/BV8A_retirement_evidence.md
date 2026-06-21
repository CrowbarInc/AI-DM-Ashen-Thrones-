# BV8A — Retirement Evidence

**Date:** 2026-06-21  
**Target key:** `recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py`  
**Scenario:** `vocative_override_after_prior_continuity`  
**Artifact:** `artifacts/bv8a_recurrence_history.json`

---

## Executive answer

The dominant speaker projection recurrence key represents a **resolved historical defect**, not an active repeating bug. Protected replay for the vocative scenario **passes today**, the failure has **not reproduced** since the single 2026-06-04 run, and BV8A records **one validated retirement outcome** in the deduplicated history view.

---

## Evidence 1 — Underlying test currently passes

**Test node:**

`tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants`

**Verification command (BV8A regeneration gate):**

```bash
python -m pytest tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q --tb=short
```

**Result:** PASS (exit code 0, verified during `tools/bv8a_recurrence_history_regeneration.py` run on 2026-06-21)

**Recorded in artifact:**

```json
"bv8a_retirement_evidence": {
  "vocative_test_passed": true,
  "failure_no_longer_reproduces": true
}
```

---

## Evidence 2 — Recurrence no longer reproduces

| Signal | Value | Interpretation |
|---|---|---|
| Latest protected failure for scenario | `2026-06-04T22:31:59Z` | Single historical observation |
| Post-fix protected replay runs | No new projection-key events | Defect not re-triggered |
| Raw event log duplicate rows | Same `run_id`, same mismatch | Instrumentation inflation, not new failures |
| Live structural invariant | PASS | Projection path satisfies test today |

The eight raw rows share one run id and one mismatch shape (`guard` vs `guard_captain`). No second run id or divergent failure signature exists in protected history.

---

## Evidence 3 — Validated outcome exists

After deduplication and retirement marking in the BV8A view:

| Metric | Before (raw) | After (BV8A view) |
|---|---:|---:|
| `validated_outcome_count` | 0 | **1** |
| `has_validated_outcomes` | false | **true** |

**Validated outcome (from `artifacts/bv8a_recurrence_history.json`):**

- **Signal:** `retired_recurrence_key`
- **Recurrence key:** projection / `selected_speaker_id` / `golden_replay.py`
- **Evidence backing:** explicit `recurrence_status: retired` on canonical event + green vocative test at regeneration time
- **Source artifact:** `artifacts/golden_replay/replay_failure_report.md`

---

## Historical failure record (retained)

Raw source evidence is preserved in:

| Artifact | Content |
|---|---|
| `artifacts/golden_replay/replay_failure_report.md` | Original failure table: projection mismatch, turn 1 |
| `artifacts/golden_replay/bug_recurrence_event_log.json` | All 11 raw events including 8 projection rows |
| `artifacts/bv8a_recurrence_history.json` | Canonical event_index 28 with retirement metadata |

**Failure shape:**

- Category: `projection`
- Field: `selected_speaker_id`
- Expected: `guard`
- Actual: `guard_captain`
- Investigate first: `tests/helpers/golden_replay.py` (divergence localizes to `golden_replay_projection.py`)

---

## Retirement decision

| Criterion | Met? |
|---|---|
| Underlying test green | Yes |
| No reproduction since historical run | Yes |
| Validated outcome recorded | Yes |
| Source evidence retained | Yes |
| Runtime / replay / projection unchanged | Yes |

**Verdict:** Mark projection recurrence key **RETIRED** in BV8A deduplicated view; retain one **HISTORICAL** occurrence for audit trail.

---

## Evidence

| Source | Role |
|---|---|
| [BV8_verification_projection.md](BV8_verification_projection.md) | Pre-BV8A green-test confirmation |
| [BV8_recurrence_trace.md](BV8_recurrence_trace.md) | End-to-end mismatch trace |
| `artifacts/bv8a_recurrence_history.json` | Retirement evidence blob + validated outcomes |
| `tools/bv8a_recurrence_history_regeneration.py` | Regeneration gate including live test run |
