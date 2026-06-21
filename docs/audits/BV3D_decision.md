# BV3D — Decision

**Date:** 2026-06-21  
**Primary metric:** Eligible Observe-Turn Coverage  
**Result:** **1.0** (1 applied / 1 eligible) under BV3D measurement scope

---

## Decision

## **B — BV3A receives eligible turns and repairs occur**

With BV3D measurement scope and positive-control fixtures, BV3A activation is **observable and correct** on eligible shapes.

---

## Rationale

| Evidence | Finding |
|---|---|
| OBS-M001 (measurement fixture) | `upstream_eligible=true`, `upstream_applied=true`, `referential_clarity_local_substitution_applied=true` |
| Eligible coverage | 1/1 = **100%** |
| Unit test regression | `test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` still passes |
| Replay-only eligible count | **0** — live refreshed replay alone still lacks contract-shaped observe turns |

---

## Sub-decisions (replay vs measurement)

| Slice | Decision | Detail |
|---|---|---|
| **Full BV3D corpus** (replay + fixtures) | **B** | Repair occurs when eligible |
| **Replay-only** (excl. fixtures) | **A** | No eligible refreshed observe turns |
| **Archive-contaminated scan** (pre-BV3D) | N/A | Removed from measurement — was invalid denominator |

Options **C** (eligible but repair fails) is **not** observed: the single eligible turn repairs successfully.

---

## Success criteria

| Criterion | Met? |
|---|---|
| Exclude stale archive contamination | **Yes** — `artifacts/bv3b_replay_refresh/` filtered |
| Exclude nested debug FEM / run_debug | **Yes** |
| Include valid BV3A-eligible cases | **Yes** — positive-control fixture |
| Measure activation on valid corpus | **Yes** — 100% on eligible set |
| No production behavior changes | **Yes** — measurement tooling only |

---

## Follow-on (out of BV3D scope)

1. Align BV3B refresh stub with validator-failing observe shapes if replay-only eligibility > 0 is required without fixtures.
2. Extend hygiene playthrough to persist observe-turn `session_log` lines in every batch (many batches currently stop at 2 lines: scene_opening + social_probe).
3. Keep BV3D scope as default for all BV3 incidence tooling; retain `legacy_unfiltered=True` only for historical baseline diffs.

---

## Related

- [BV3D_measurement_scope.md](BV3D_measurement_scope.md)
- [BV3C_root_cause.md](BV3C_root_cause.md)
- [BV3D_fixture_alignment.md](BV3D_fixture_alignment.md)
