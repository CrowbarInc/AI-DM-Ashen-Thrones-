# BV5 — Scorecard Revalidation

**Date:** 2026-06-21  
**Scope:** Post-BV2/BV3/BV4 measurement re-run on current tree (`HEAD`).  
**Prior classification:** **REDISTRIBUTED_COST** ([BV_maintenance_economics_validation_closeout.md](BV_maintenance_economics_validation_closeout.md), BV1C).  
**Method:** Fresh BU AST scan (628 files, 220-module ecosystem), `tools/bv1a_bug_fix_locality_validation.py`, `tools/bv1b_fallback_incidence_validation.py`, `tools/bv4b_concrete_beat_metrics.py`, protected replay recurrence artifacts.

---

## Executive answer

BV2–BV4 **changed the maintenance-economics verdict**. The BV1C blocker — **unchanged high fallback incidence** — is **removed** on the active BV3D measurement corpus. Measured fallback trigger rate fell **69.16% → 1.05%** (107-FEM legacy baseline vs 95-FEM current scope). Meta read-side fan-in **contracted 64%** on `final_emission_meta` (61 → 22 → **24**). Bug-fix locality remains **unobserved** (N = 0 post-BI corrective commits).

**BV5 scorecard verdict:** maintenance burden **was reduced on measured runtime fallback and meta coupling**; **partial redistribution persists** in read facades and test governance hubs.

---

## Scorecard metrics (recalculated)

| Metric | BV1C baseline | BV5 current | Delta | Direction |
|---|---:|---:|---:|---|
| **Bug-fix locality** | Post-BI N = 0; BR median **9** files (11 commits) | Post-BI N = **0**; BR median **9** unchanged | — | **Unchanged / unobserved** |
| **Refactor/architecture locality** | Post-BI refactor median **18** files (5 commits) | Post-BI refactor median **18** (includes BV2–BV4 program commits) | 0 | **Unchanged** (extraction breadth persists) |
| **Recurrence history** | 4 families / 11 rows; speaker projection **8** hits; 25% regression rate | **Unchanged** — same 4 keys, speaker projection still **8** occurrences (72.7% share) | 0 | **Inconclusive** for improvement |
| **Runtime fallback incidence** | **69.16%** (74/107 FEM); BV1B second snapshot stable | **1.05%** (1/95 FEM, BV3D scope) | **−68.11 pp** (cross-scope) | **Reduced** on active corpus |
| **Observe-route rate** | **95.45%** (42/44 observe turns, 107 FEM) | **4.35%** (1/23 observe turns, 95 FEM) | **−91.10 pp** (cross-scope) | **Reduced** |
| **Fallback owner-bucket gaps** | **13** ownerless events (107 FEM) | **0** ownerless (1/1 stamped) | **−13** | **Improved** |
| **Attribution owner bucket** | **38.78%** (19/49) | **38.78%** (no BV5 re-run; BS artifact unchanged) | 0 | **Unchanged** |
| **Attribution contract compliance** | **100%** | **100%** | 0 | **Unchanged** |
| **Speaker-finalize parity** | `speaker_contract_enforcement` **15/4**; P3/P4 probes pass | **15/4** unchanged; terminal pipeline **26/14** (+1 FO) | 0 FI | **Unchanged drag, unchanged measurability** |
| **Fan-in / fan-out (key hubs)** | See hub table below | See hub table below | Mixed | **Meta core down; read facades up; smoke up** |

### Key hub fan-in / fan-out

| Hub | BV1C (FI/FO) | BV5 (FI/FO) | Δ FI | Notes |
|---|---:|---:|---:|---|
| `game.final_emission_meta` | **61 / 6** | **24 / 8** | **−37** | BV2 consolidation |
| `game.final_emission_meta_read` | — (pre-BV2) | **28 / 1** | +28 | Read-side delegate (BV2A) |
| `game.final_emission_owner_bucket_views` | — | **22 / 1** | +22 | Bucket vocabulary (BV2A) |
| **Meta ecosystem (sum)** | **61** | **74** | **+13** | Coupling **relocated**, core meta **down** |
| `game.final_emission_replay_projection` | **15 / 4** | **15 / 5** | 0 | Stable replay owner |
| `tests.helpers.golden_replay_projection` | **18 / 7** | **14 / 6** | **−4** | Replay adapter de-concentrated |
| `game.final_emission_visibility_fallback` | **17 / 17** | **17 / 18** | 0 | Router unchanged; +1 FO from BV4 hooks |
| `game.final_emission_terminal_pipeline` | **26 / 13** | **26 / 14** | 0 | Convergence hub persists |
| `game.final_emission_gate` | **28 / 7** | **30 / 9** | **+2** | BV3/BV4 satisfier hooks |
| `tests.helpers.emission_smoke_assertions` | **70 / 5** | **73 / 5** | **+3** | Test facade still dominant FI node |
| `tests.test_ownership_registry` | **0 / 57** | **0 / 57** | 0 | Governance router unchanged |
| `game.speaker_contract_enforcement` | **15 / 4** | **15 / 4** | 0 | Stable |
| Ecosystem module count | **216** | **220** | **+4** | BV4 passive-scene + meta facades |

---

## Per-metric interpretation

### Bug-fix locality

Post-BI corrective cohort remains **N = 0**. BV2–BV4 were program/refactor work, not defect repairs. **Cannot claim cheaper bug fixes** from git evidence.

### Recurrence history

Protected replay recurrence unchanged: speaker projection drift key still **8** observations (concentrated). BV3/BV4 fallback reduction **not yet reflected** in recurrence retirement metrics (`validated_outcome_count: 0` in `bug_recurrence_history.json`).

### Fallback incidence

Two measurement scopes must be read together:

| Scope | Corpus | Rate | Role |
|---|---:|---:|---|
| BV1B legacy | 107 FEM | **69.16%** | Pre-BV3 frozen baseline |
| BV3F post-refresh | 95 FEM (BV3D) | **11.58%** | Post-BV3E effective reduction |
| BV5 current | 95 FEM (BV3D) | **1.05%** | Post-BV4B effective reduction |

Longitudinal history on the **107-FEM pair** remains **stable** (0.00 pp). Reduction claims are valid on the **BV3D corpus lineage**, not as a direct continuation of the 107-FEM snapshot.

### Fan-in / fan-out

BV2 achieved **−64%** on `final_emission_meta` direct imports (61 → 22; current 24 after BV4 production hooks). Total meta-related imports **rose slightly** when facades are included (+13), matching **structured redistribution** rather than elimination. Largest ecosystem fan-in node remains **`emission_smoke_assertions` (73)** — BV4 test-facade cycle **not executed**.

---

## Classification input (for BV5 closeout)

| Track | BV5 finding | Weight |
|---|---|---|
| BV2 meta consolidation | Core meta FI **−37**; read facades +50 FI across new modules | Supports partial redistribution |
| BV3F fallback reduction | Incidence **46.39% → 11.58%** on BV3D corpus; RC hard replace **−11** | Supports **REDUCED_COST** |
| BV4B concrete beat | PSP **10 → 0**; incidence **11.58% → 1.05%**; observe **47.83% → 4.35%** | Supports **REDUCED_COST** |
| BV1A bug-fix locality | N = 0 | Contradicts full **REDUCED_COST** |
| Test smoke facade | FI **70 → 73** | Contradicts full **REDUCED_COST** |
| Attribution completeness | Unchanged at 38.78% owner bucket | Neutral / slight drag |

**Recommended BV5 classification:** **REDUCED_COST** (dominant measured drag reduced) with **residual redistribution** on meta read facades and test governance. Confidence: **medium-high**.

---

## Evidence

| Deliverable | Path |
|---|---|
| BU fan-in scan | `docs/audits/BU_import_fan_in_fan_out.csv` (628 files, 2026-06-21) |
| Bug-fix locality | [BV1A_bug_fix_locality_comparison.md](BV1A_bug_fix_locality_comparison.md) |
| Fallback incidence | [BV1B_fallback_incidence_validation.md](BV1B_fallback_incidence_validation.md) |
| BV4B metrics | `artifacts/bv4b_concrete_beat_metrics.json` |
| BV3F metrics | `artifacts/bv3f_reduction_metrics.json` |
| Recurrence | `artifacts/golden_replay/bug_recurrence_history.json` |
| BV2 closeout | [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md) |
