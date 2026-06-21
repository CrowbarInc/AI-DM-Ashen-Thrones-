# BV8 — Speaker Recurrence Inventory

**Date:** 2026-06-21  
**Primary metric:** Recurrence concentration  
**Current:** 8 rows on dominant key; **72.7%** of recurrence event history (8/11 events)  
**Sources:** `artifacts/golden_replay/bug_recurrence_event_log.json`, `artifacts/golden_replay/bug_recurrence_history.json`, `artifacts/golden_replay/replay_failure_report.md`

---

## Executive answer

Speaker-projection recurrence is **not eight independent regressions**. It is **one historical protected-replay failure** (`vocative_override_after_prior_continuity`, 2026-06-04) **recorded eight times** in the event log through backfill/migration duplication. The underlying test **passes today**. A second speaker-family key (speaker-contract enforcement) has **one emerging observation** on a different scenario.

Recurrence persists because **instrumentation was never retired** after the underlying mismatch was resolved — not because the team repeatedly repaired the same live bug eight times.

---

## Scope filter

Included recurrence families:

| Family term | Match rule |
|---|---|
| speaker projection | `category=projection` + `field_path=selected_speaker_id` + `speaker_drift` bucket |
| speaker adoption | `post_emission_speaker_adoption` owner paths (no direct recurrence rows today) |
| speaker relocation | Block T shadow-equivalence drift (no direct recurrence rows today) |
| speaker finalize | `speaker_contract_enforcement` category rows |
| speaker identity preservation | `selected_speaker_id` field path across speaker_drift bucket |

---

## Inventory — speaker-family recurrence keys

### Key 1 (dominant — 8 event rows)

| Field | Value |
|---|---|
| **Recurrence ID** | `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` |
| **Originating subsystem** | Golden replay projection seam (`tests/helpers/golden_replay_projection.py` → `_resolve_selected_speaker_id`; classified owner `projection`; investigate_first points to `golden_replay.py`) |
| **Recurrence count** | **8** (aggregated `occurrence_count` in history JSON) |
| **First appearance** | `2026-06-04T22:31:59Z` (event_index 28; run_id `2026-06-04T22:31:59Z`) |
| **Latest appearance** | `2026-06-04T22:31:59Z` (event_index 252 — same run, duplicate backfill) |
| **Scenario** | `vocative_override_after_prior_continuity` |
| **Test** | `tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` |
| **Failure shape** | `selected_speaker_id: exact value mismatch` — expected `guard`, actual `guard_captain` |
| **Trend class** | `recurring` (only key with occurrence_count ≥ 2) |
| **Live status** | Test **passes** as of BV8 discovery re-run |

### Key 2 (emerging — 1 event row)

| Field | Value |
|---|---|
| **Recurrence ID** | `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` |
| **Originating subsystem** | Strict-social speaker contract enforcement (`game/speaker_contract_enforcement.py`) |
| **Recurrence count** | **1** |
| **First appearance** | `2026-06-20T12:00:00Z` (event_index 253; backfill via `expand_protected_replay_observations`) |
| **Latest appearance** | `2026-06-20T12:00:00Z` |
| **Scenario** | `wrong_speaker_strict_social_emission` |
| **Test** | `tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` |
| **Trend class** | `emerging` |

---

## Event-level row table (all 9 speaker-family events)

| Row | Recurrence ID (short) | Scenario | recorded_at | event_index | Notes |
|---:|---|---|---|---:|---|
| 1 | projection / golden_replay | vocative_override | 2026-06-04 | 28 | Original backfill from `replay_failure_report.md` |
| 2–8 | projection / golden_replay | vocative_override | 2026-06-04 | 204, 219, 220, 228, 236, 244, 252 | **Duplicates** — same run_id, same failure, migration/backfill inflation |
| 9 | speaker / speaker_contract_enforcement | wrong_speaker | 2026-06-20 | 253 | Corpus observation backfill |

---

## Non-recurrence speaker surfaces (context only)

These subsystems appear in speaker maintenance paths but have **no recurrence event rows** today:

| Subsystem | Module | Role |
|---|---|---|
| Speaker adoption | `game/post_emission_speaker_adoption.py` | Post-emission canonical speaker adoption into interaction state |
| Speaker relocation | `tests/helpers/speaker_relocation_shadow_harness.py` | Block T gate vs isolated enforcement parity |
| Speaker finalize probe | `tests/helpers/post_speaker_finalize_probe.py` | Block U first post-speaker text diverger |
| Replay FEM speaker repair | `game/final_emission_replay_projection.py` | `_fem_speaker_repair_projections` lineage events |
| Drift taxonomy | `tests/helpers/replay_drift_taxonomy.py` | Routes `selected_speaker_id` drift to `speaker_drift` bucket |

---

## Portfolio context

| Metric | Value |
|---|---:|
| Total recurrence events (all families) | 11 |
| Speaker-family events | 9 (**81.8%**) |
| Speaker projection events (Key 1) | 8 (**72.7%**) |
| Unique recurrence keys (all) | 4 |
| Speaker-family keys | 2 (**50%** of keys, **81.8%** of events) |
| `validated_outcome_count` | **0** — no key has been formally retired despite green test |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bug_recurrence_event_log.json` | Authoritative event rows |
| `artifacts/golden_replay/bug_recurrence_history.json` | Aggregated `recurrences[]` + concentration metrics |
| `artifacts/golden_replay/replay_failure_report.md` | Original 2026-06-04 failure classification |
| [BQ36_recurrence_write_path_audit.md](BQ36_recurrence_write_path_audit.md) | Duplicate backfill contamination path |
| [BT_speaker_finalization_divergence_discovery.md](BT_speaker_finalization_divergence_discovery.md) | Projection vs finalize identity gap |
