# BX Emission — Retirement Evidence

**Date:** 2026-06-28  
**Target key:** `recurrence:v1:emission_drift|projection|response_type_candidate_ok|tests/helpers/golden_replay.py`  
**Scenarios:** `bx5_guard_*` guard-matrix cases  
**Cycle:** CO105

---

## Executive answer

The emission-drift recurrence key represents **resolved historical BX development observations**, not an active repeating defect. Protected replay for all BX speaker parity scenarios **passes today**, failures have **not reproduced** since the 2026-06-22 development run, and CO105 propagates **one additional validated retirement outcome** independent of the BV8A vocative projection key.

---

## Evidence 1 — Underlying tests currently pass

**Verification command (CO105 propagation gate):**

```bash
python -m pytest -m bx_speaker_parity -q --tb=short
```

**Alternate bundle (BX closeout):**

```bash
python -m pytest tests/test_bx_speaker_identity_golden_replay.py -q --tb=short
```

**Result:** PASS (exit code 0, verified during CO105 propagation run)

---

## Evidence 2 — Recurrence no longer reproduces

| Signal | Value | Interpretation |
|---|---|---|
| Latest protected failures for key | `2026-06-22T21:38:39Z` | Historical BX development run only |
| Post-closeout protected replay runs | No new emission-drift key events | Defect not re-triggered |
| BX program status | **Closed** (2026-06-22) | Engineering disposition finalized |
| Live BX parity suite | PASS | Projection path satisfies locked parity expectations |

Four protected-lane events share the same recurrence key and `response_type_candidate_ok` field path from bx5 guard-matrix scenarios during BX development. No post-closeout failure signature exists in protected history.

---

## Evidence 3 — Engineering disposition documented

| Source | Disposition |
|---|---|
| [CO103_outcome_lifecycle_inventory.md](CO103_outcome_lifecycle_inventory.md) | **Accepted fix** — BX parity expectations locked |
| [CO103_observation_outcome_correlation.md](CO103_observation_outcome_correlation.md) | **High** confidence observation→fix correlation |
| [BX_speaker_identity_end_to_end_parity_closeout.md](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md) | BX **closed** with locked replay fields |

---

## Historical failure record (retained)

| Artifact | Content |
|---|---|
| `artifacts/golden_replay/replay_failure_report.md` | BX development failure table rows |
| `artifacts/golden_replay/bug_recurrence_event_log.json` | Four emission-drift protected-lane events (preserved) |

**Failure shape:**

- Category: `projection`
- Field: `response_type_candidate_ok`
- Owner drift bucket: `emission_drift`
- Investigate first: `tests/helpers/golden_replay.py`

---

## Retirement decision

| Criterion | Met? |
|---|---|
| Underlying BX tests green | Yes |
| BX program formally closed | Yes |
| No reproduction since historical run | Yes |
| Accepted-fix disposition in CO103 | Yes |
| Source evidence retained | Yes |
| Runtime / replay / projection unchanged | Yes |

**Verdict:** Mark emission-drift recurrence key **RETIRED** in protected event log; retain all four historical observations for audit trail.

---

## Evidence

| Source | Role |
|---|---|
| [BX_emission_retirement_registry.md](BX_emission_retirement_registry.md) | Machine-readable registry entry |
| `tools/propagate_outcome_retirements.py` | Propagation gate including live test run |
| [CO104_outcome_retirement_propagation_report.md](CO104_outcome_retirement_propagation_report.md) | Prior single-key validation baseline |
