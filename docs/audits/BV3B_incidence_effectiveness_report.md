# BV3B — Incidence Effectiveness Report

**Date:** 2026-06-21  
**Question:** Did BV3A upstream referential-clarity repair reduce fallback incidence on a fresh corpus?  
**Answer:** **No.** Primary family incidence **increased**; upstream repair **did not activate** on measured observe turns.

---

## Metric dashboard

| Metric | BV1B baseline | BV3 baseline (verification doc) | BV3B current | Delta vs BV1B |
|---|---:|---:|---:|---:|
| **Observe route rate** | 95.45% | 95.45% (raw Phase 1 adj. 90.91%) | **80.00%** | **−15.45 pp** |
| **Fallback incidence (overall)** | 69.16% | 69.16% (adj. 67.29%) | **57.50%** | **−11.66 pp** |
| **Ownerless count (repo)** | 13 | 13 (Phase 1 proj. 5) | **13** | **0** |
| **Referential clarity replacements** | 38 | 38 (Phase 2 proj. ≤26) | **48** | **+10** |
| **`passive_scene_pressure_fallback`** | 1 | 1 | **1** | **0** |

---

## BV3A repair metrics (`artifacts/bv3b_referential_clarity_metrics.json`)

| Signal | Value |
|---|---:|
| Repaired violations (upstream applied on observe) | **0** |
| Local substitutions applied on observe | **0** |
| Hard replacements (`referential_clarity_replacement_applied` on observe) | **49** |
| Unrepaired violation turns | **10** |
| Repair success rate on observe | **0.0** |

---

## Reduction vs relocation verdict

| Test | Expected for effective reduction | BV3B observation | Pass? |
|---|---|---|---|
| A. `referential_clarity_hard_replacement` count falls | Decrease ≥10 from 38 | **+10 (48)** | **✗** |
| B. `passive_scene_pressure_fallback` falls | Stable or down | **Unchanged (1)** | ○ |
| C. No compensating family surge | No offsetting spike | **`scene_opening` +31** (corpus expansion) | **✗** |
| D. Upstream repair stamps on observe | >0 on eligible turns | **0 applied** | **✗** |
| E. Player-facing behavior preserved | No replay regression | Protected replay 89/91 green | ○ |

**Classification driver:** Primary discriminator from [BV3_fallback_reduction_verification.md](BV3_fallback_reduction_verification.md) requires referential-clarity hard-replace events to **decrease alongside** observe route rate. Route rate fell, but hard-replace events **rose** with **zero** upstream repair telemetry—matching the BV1B **relocation / measurement** failure mode, not BV3A effectiveness.

---

## Scenario classification

| Outcome | Selected |
|---|---|
| A. Incidence reduced (primary metric) | |
| B. Incidence unchanged | |
| C. Incidence relocated | |
| **D. No measurable BV3A effectiveness** | **✓ `NO_MEASURABLE_CHANGE`** |

**Rationale:** Fresh corpus does **not** demonstrate measurable reduction in `referential_clarity_hard_replacement`. Overall incidence improved only via corpus composition (more scene_opening-eligible turns, larger denominator). BV3A contract remains **unvalidated at incidence layer** until upstream repair stamps appear on observe FEM and hard-replace lineage events fall on a **like-for-like** prompt set.

---

## Recommended follow-on

1. Re-run refresh on a **fixed 107-turn prompt manifest** (pre-refresh turn fingerprints) to separate corpus expansion from behavioral change.
2. Trace why `referential_clarity_upstream_repair_applied` is absent on API observe turns despite unit-test coverage in `tests/test_bv3a_observe_referential_clarity_repair.py`.
3. Restrict incidence scan to **top-level finalized FEM** (exclude nested `emission_debug_lane` snapshots) for sensitivity analysis—the pre-refresh corpus counted debug-lane FEM heavily.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv3b_referential_clarity_metrics.json` | BV3A instrumentation |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.baseline.json` | Frozen BV1B |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | BV3B measurement |
| [BV3B_fallback_incidence_delta.md](BV3B_fallback_incidence_delta.md) | Detailed deltas |
| [BV3B_replay_refresh.md](BV3B_replay_refresh.md) | Refresh protocol |
