# BV8A — Retirement Registry

**Date:** 2026-06-21  
**Primary metric:** Recurrence History Accuracy  
**Registry source:** `artifacts/bv8a_recurrence_history.json` → `retirement_registry`  
**Raw history:** Unmodified (`artifacts/golden_replay/bug_recurrence_event_log.json`)

---

## Status definitions

| Status | Meaning |
|---|---|
| **RETIRED** | Stale recurrence tracking; underlying defect resolved; no longer drives governance prioritize tier |
| **HISTORICAL** | One canonical occurrence retained as source evidence in deduplicated view |
| **ACTIVE** | Current emerging or watch-tier recurrence keys with live tracking |

---

## Registry entries

### RETIRED

| recurrence_key | scenario | rationale |
|---|---|---|
| `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` | `vocative_override_after_prior_continuity` | Single historical alias/canonical projection mismatch; vocative test passes; seven duplicate backfill rows removed |

**Retirement evidence:** green vocative structural invariant; `validated_outcome_count: 1` in BV8A view; failure report dated 2026-06-04 only.

---

### HISTORICAL

| recurrence_key | canonical event_index | occurrence_count (deduped) | rationale |
|---|---|---:|---|
| `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` | 28 | 1 | One deduplicated protected-replay failure retained as audit evidence; status `retired` on event |

---

### ACTIVE

| recurrence_key | scenario | occurrence_count (deduped) | trend | rationale |
|---|---|---:|---|---|
| `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` | `wrong_speaker_strict_social_emission` | 1 | emerging | Speaker-contract enforcement observation; monitor before retirement |
| `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` | `directed_npc_question` | 1 | emerging | Fallback drift observation from corpus expansion |
| `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` | `sanitizer_scaffold_leakage` | 1 | emerging | Sanitizer drift observation from corpus expansion |

---

## Registry summary

| Status | Key count | Event rows (deduped view) |
|---|---:|---:|
| RETIRED | 1 | 1 (marked retired) |
| HISTORICAL | 1 | 1 (same key, evidence retention) |
| ACTIVE | 3 | 3 |
| **Total unique keys** | **4** | **4** |

Note: RETIRED and HISTORICAL apply to the same recurrence key at different registry dimensions — retirement stops active tracking; historical retention preserves the canonical event.

---

## Governance impact (deduplicated view)

| Before (raw) | After (BV8A) |
|---|---|
| Projection key on **prioritize** tier (ROI 100) | Projection key **retired** — leaves prioritize tier |
| 8-hit recurring signal | 1 historical occurrence, 0 recurring keys |
| 0 validated outcomes | 1 validated retirement |

---

## Regeneration

Rebuild registry and deduplicated history:

```bash
python tools/bv8a_recurrence_history_regeneration.py
```

Output: `artifacts/bv8a_recurrence_history.json`

---

## Evidence

| Source | Role |
|---|---|
| [BV8A_recurrence_audit.md](BV8A_recurrence_audit.md) | Duplicate row audit |
| [BV8A_retirement_evidence.md](BV8A_retirement_evidence.md) | Green-test and validated outcome evidence |
| [BV8_retirement_plan.md](BV8_retirement_plan.md) | Phase 1 retirement strategy |
| `artifacts/bv8a_recurrence_history.json` | Machine-readable registry + deduplicated view |
