# BV8 — Speaker Recurrence Concentration Report

**Date:** 2026-06-21  
**Primary metric:** Recurrence concentration  
**Population:** `protected_replay_history` (`bug_recurrence_event_log.json`)

---

## Executive answer

Speaker projection recurrence is **highly concentrated** but **misleadingly inflated**. One recurrence key accounts for **72.7% of all events** and **100% of recurring keys** — yet it represents **a single historical failure duplicated seven times**, on a test that **passes today**. This is **one root cause** (projection ID vocabulary mismatch) plus **one instrumentation cause** (duplicate backfill), not eight independent repair cycles.

---

## Recurrence frequency

| Metric | Value |
|---|---:|
| Total event rows | 11 |
| Speaker-family event rows | 9 (**81.8%**) |
| Projection-key event rows | 8 (**72.7%**) |
| Unique recurrence keys (all families) | 4 |
| Keys with occurrence_count ≥ 2 | **1** (projection key only) |
| Regression recurrence rate | **25%** (1/4 keys) |
| Recurring keys (trends) | **1** |
| Emerging keys | **3** |
| Retired keys | **0** |
| `validated_outcome_count` | **0** |

### Frequency by scenario

| Scenario | Event rows | Keys | Share |
|---|---:|---:|---:|
| `vocative_override_after_prior_continuity` | 8 | 1 | **72.7%** |
| `wrong_speaker_strict_social_emission` | 1 | 1 | 9.1% |
| `directed_npc_question` | 1 | 1 | 9.1% |
| `sanitizer_scaffold_leakage` | 1 | 1 | 9.1% |

### Frequency by field path

| field_path | Event rows | Share |
|---|---:|---:|
| `selected_speaker_id` | 9 | **81.8%** |
| `final_emitted_source` | 1 | 9.1% |
| `scaffold_leakage` | 1 | 9.1% |

---

## Ownership concentration

| Owner / bucket | Keys | Event rows | Share | Governance load |
|---|---:|---:|---:|---|
| `projection` / `speaker_drift` | 1 | 8 | **72.7%** | **prioritize** (ROI 100) |
| `speaker` / `speaker_drift` | 1 | 1 | 9.1% | watch |
| `fallback` / `fallback_drift` | 1 | 1 | 9.1% | watch |
| `sanitizer` / `semantic_drift` | 1 | 1 | 9.1% | watch |

**Highest governance load owner:** `speaker_drift` (2 keys, 9 events)

**Investigate-first concentration:**

| investigate_first | Events |
|---|---:|
| `tests/helpers/golden_replay.py` | 8 |
| `game/speaker_contract_enforcement.py` | 1 |
| `game/final_emission_gate.py` | 1 |
| `game/output_sanitizer.py` | 1 |

Note: 8 events point to `golden_replay.py` but divergence localizes to `golden_replay_projection.py` — ownership concentration is **misaligned with code ownership**.

---

## Subsystem concentration

| Subsystem | Recurrence rows | Code modules | Maintenance touches (BV1–BV7) |
|---|---:|---|---|
| **Replay projection** | 8 | `golden_replay_projection.py`, `replay_smoke_assertions.py` | Unchanged through BV7 |
| **Speaker enforcement** | 1 | `speaker_contract_enforcement.py`, strict_social_stack | Block T/U probes added (BT) |
| Speaker adoption | 0 | `post_emission_speaker_adoption.py` | No recurrence signal |
| Speaker relocation | 0 | `speaker_relocation_shadow_harness.py` | No recurrence signal |
| Replay orchestration | 0 | `golden_replay.py` | Misclassified as investigate_first |

---

## Portfolio concentration metrics

| Metric | Value | Source |
|---|---:|---|
| `concentration_current` | **0.686** | `bug_recurrence_history.json` |
| `concentration_baseline` | 0.686 | unchanged since backfill |
| Dominant key share (events) | **72.7%** | 8/11 |
| Dominant key share (recurring class) | **100%** | 1/1 recurring key |
| Forecast classification | **concentrated** | projection key |
| Estimated portfolio reduction if dominant key retired | **74.2** | history JSON remediation targets |

---

## Root-cause cardinality verdict

| Hypothesis | Verdict | Evidence |
|---|---|---|
| **One root cause** | **Yes (primary)** | All 8 projection events: same scenario, same run_id, same expected/actual mismatch |
| **Several related causes** | **Partial** | Projection alias mismatch (dominant) + separate wrong_speaker enforcement row (emerging) share `selected_speaker_id` field but different categories/owners |
| **Unrelated incidents** | **No** | 7/8 projection rows are duplicate instrumentation, not separate bugs |

### Concentration shape

```text
                    ┌─────────────────────────────────────┐
  Event share 72.7% │ projection / selected_speaker_id    │ ← 1 incident × 8 log rows
                    └─────────────────────────────────────┘
         9.1% each  │ speaker enforcement │ fallback │ sanitizer │ ← emerging singles
```

**Interpretation:** Maintenance drag is **concentrated in replay observation vocabulary**, not distributed across speaker finalize/adoption/relocation subsystems. Recurrence instrumentation **amplifies** a resolved mismatch into a false "8-hit" signal.

---

## Comparison to pre-BV8 baseline claims

| Claim (BV5 scorecard) | BV8 finding |
|---|---|
| "8 recurrence rows unchanged" | **Confirmed** in artifact — but **7 are duplicates** |
| "72.7% share" | **Confirmed** — event-level concentration |
| "Speaker projection drift persists" | **Partially false** — test green; **artifact stale** |
| "0 validated retirements" | **Confirmed** — retirement workflow never executed |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bug_recurrence_history.json` | Concentration + remediation ROI |
| `artifacts/golden_replay/bug_recurrence_event_log.json` | Event-level dedupe analysis |
| [BV8_recurrence_inventory.md](BV8_recurrence_inventory.md) | Row inventory |
| [BV8_failure_family_map.md](BV8_failure_family_map.md) | Cause families |
