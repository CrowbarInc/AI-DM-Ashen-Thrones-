# BX Emission — Retirement Registry

**Date:** 2026-06-28  
**Primary metric:** Recurrence History Accuracy  
**Registry source:** `tools/propagate_outcome_retirements.py` → documented retirement registry  
**Cycle:** CO105

---

## Status definitions

| Status | Meaning |
|---|---|
| **RETIRED** | Stale recurrence tracking; underlying defect resolved during BX program closeout; no longer drives governance prioritize tier |
| **ACTIVE** | Current emerging or watch-tier recurrence keys with live tracking |

---

## Registry entries

### RETIRED

| recurrence_key | scenarios | rationale |
|---|---|---|
| `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` | `bx5_guard_role_alias_guard_captain`, `bx5_guard_canonical_guard_captain`, `bx5_guard_gate_guard_distinct` (+ one additional bx5 observation) | Historical BX development `response_type_candidate_ok` projection mismatches; BX program **closed**; all `bx_speaker_parity` protected tests **pass**; no reproduction since 2026-06-22 |

**Retirement evidence:** green BX speaker parity suite; CO103 accepted-fix disposition; failure report observations dated 2026-06-22 only.

---

## Regeneration

Propagate into protected event log:

```bash
python tools/propagate_outcome_retirements.py --generated-at <ISO8601>
```

---

## Evidence

| Source | Role |
|---|---|
| [BX_speaker_identity_end_to_end_parity_closeout.md](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md) | BX program closed; validation bundle |
| [CO103_outcome_lifecycle_inventory.md](CO103_outcome_lifecycle_inventory.md) | Accepted-fix disposition |
| [CO103_observation_outcome_correlation.md](CO103_observation_outcome_correlation.md) | Observation→fix correlation |
| [BV8A_retirement_registry.md](BV8A_retirement_registry.md) | Registry pattern reference (CO104) |
