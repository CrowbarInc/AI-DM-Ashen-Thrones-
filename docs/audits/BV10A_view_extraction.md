# BV10A — View Extraction Closeout

**Date:** 2026-06-21  
**Phase:** BV10 Phase 1  
**Primary metric:** Read-side consolidation readiness  
**Status:** Facades ready; Phase 2 consumer migration may begin.

---

## Executive summary

BV10 Phase 1 introduced three delegate-only read facades. **No consumers were migrated.** Validation suites confirm parity unchanged.

| Deliverable | Status |
|---|---|
| `attribution_read_views.py` | ✓ Created |
| `ownership_projection_views.py` | ✓ Created |
| `observability_attribution_read.py` | ✓ Created |
| Delegate verification | ✓ 7 automated checks |
| Registry preparation | ✓ Documented in ownership registry |
| Consumer migration | **Deferred to Phase 2** |

---

## Fan-in baseline

### Pre-BV10A (BV10 discovery baseline)

| Module | FI |
|---|---:|
| `final_emission_meta_read` | **29** |
| `final_emission_owner_bucket_views` | **22** |
| `final_emission_ownership_schema` | **19** |
| **Combined cluster** | **70** |

### Post-BV10A (facade scaffolding only)

| Module | FI | Δ | Notes |
|---|---:|---:|---|
| `final_emission_meta_read` | **31** | +2 | `observability_attribution_read` + delegate test |
| `final_emission_owner_bucket_views` | **24** | +2 | `attribution_read_views` + delegate test |
| `final_emission_ownership_schema` | **22** | +3 | Both new facades + delegate test |
| **Combined cluster** | **77** | **+7** | Expected internal facade fan-in; no consumer shift yet |
| `attribution_read_views` | **0*** | — | Not in BU ecosystem until Phase 2 adopters |
| `ownership_projection_views` | **0*** | — | Same |
| `observability_attribution_read` | **0*** | — | Same |

\*BU ecosystem counts direct importers among scanned modules; facades have zero external adopters in Phase 1.

**Readiness interpretation:** Combined cluster FI **temporarily rises +7** while facades import authority internally. Phase 2 migration should net **−40 to −44** on combined cluster (BV10 projection).

---

## New modules

### `game/attribution_read_views.py`

**Purpose:** Single import surface for attribution lookups, owner-bucket reads, and classifier vocabulary.

**Surface:**

- 4 bucket mappers (delegate to `owner_bucket_views`)
- Bucket frozensets + scalar tokens
- `ALLOWED_FALLBACK_*` + selection/content owner tokens for classifier/sync
- `attribution_read_views_surface()` registry

**FO:** 2 (`owner_bucket_views`, `ownership_schema`)

### `game/ownership_projection_views.py`

**Purpose:** Read-only ownership projection vocabulary for lineage and sanitizer trace mapping.

**Surface:**

- Lineage/split-owner constants used by replay projection and runtime telemetry
- `normalize_sanitizer_trace_owner_to_lineage_owner` (delegate)
- `lineage_owner_vocabulary()`, `sanitizer_trace_owner_vocabulary()`
- `ownership_projection_views_surface()` registry

**FO:** 1 (`ownership_schema`)

### `game/observability_attribution_read.py`

**Purpose:** Observability and evaluator read helpers without multi-source attribution imports.

**Surface:**

- 10 observability symbols delegated from `final_emission_meta_read`
- `NARRATIVE_AUTHENTICITY_FEM_KEYS`
- `observability_attribution_read_surface()` registry

**FO:** 1 (`final_emission_meta_read`)

---

## Phase 2 migration inventory (potential)

| Facade | Candidate files | Import edges | BV10 wave |
|---|---|---:|---|
| `attribution_read_views` | failure_classification_contract/sync, failure_classifier, failure_dashboard_fixtures, replacement_attribution_inventory + tests | **~13** | 2A |
| `ownership_projection_views` | output_sanitizer, runtime_lineage_telemetry, replay_projection internals + tests | **~8** | 2B (partial C2) |
| `observability_attribution_read` | dead_turn_report_visibility, playability_eval, narrative_authenticity_eval, stage_diff_telemetry + observability tests | **~7** | 2B (C4) |
| Smoke/gate hardening (C5) | gate tests, emission/replay smoke helpers | **~14** | 2D |
| Replay adapter (C3) | golden replay tests, replay_projection triple-import | **~10** | 2C |

**Total Phase 2 addressable edges:** ~52 (overlap ~16 multi-import files → net **~36** unique migrations)

---

## Projected Phase 2 impact

| Metric | Post-BV10A | Post-Phase 2 (est.) | Post-Phase 3 (est.) |
|---|---:|---:|---:|
| Combined cluster FI | 77 | **~34–38** | **~26–30** |
| `attribution_read_views` FI | 0 | **~11** | ~11 |
| `ownership_projection_views` FI | 0 | **~6** | ~6 |
| `observability_attribution_read` FI | 0 | **~9** | ~9 |
| Cluster authority FI (`meta_read` + `views` + `schema`) | 77 | **~16–20** | **~14–18** |

---

## Validation results

| Suite | Command scope | Result |
|---|---|---|
| BV10A delegate verification | `tests/test_bv10a_read_facade_delegates.py` | **7 passed** |
| Attribution | `test_failure_classifier`, `test_failure_classification_contract`, `test_replacement_attribution_inventory` | **Passed** |
| Replay | `test_golden_replay_projection`, `test_golden_replay_fallback_projection`, `test_golden_replay_direct_seam`, `test_runtime_lineage_telemetry` | **Passed** |
| Ownership (core) | `test_final_emission_meta`, `test_opening_fallback_owner_bucket` | **Passed** |
| Observability | `test_observational_telemetry_confidence`, `test_dead_turn_detection`, `test_dead_turn_evaluation_threading` | **Passed** |

**Parity:** Unchanged — no consumer imports retargeted.  
**Replay:** Unchanged — no replay projection or manifest changes.  
**Ownership:** Unchanged — schema authority and mapper implementations untouched.

*Note: `tests/test_ownership_registry.py` contains pre-existing unrelated failures (inventory/gate BJ governance); not introduced by BV10A.*

---

## Read-side consolidation readiness scorecard

| Criterion | Target | BV10A status |
|---|---|---|
| Domain facades exist | 3 modules | ✓ |
| Delegate-only verified | Automated | ✓ |
| No consumer migration | Required | ✓ |
| No authority relocation | Required | ✓ |
| Registry prep documented | Required | ✓ |
| Phase 2 inventory enumerated | Required | ✓ |
| Validation suites green | Required | ✓ (scoped suites) |

**Verdict:** **READY** for Phase 2 consumer migration.

---

## Next steps (Phase 2)

1. **Wave 2A:** Migrate attribution cluster to `attribution_read_views`
2. **Wave 2B:** Migrate observability evaluators to `observability_attribution_read`; projection reads to `ownership_projection_views`
3. **Wave 2C:** Extend replay adapter; protected manifest parity check
4. **Wave 2D:** Gate/smoke read helper hardening
5. **Phase 3:** `test_bv10_read_cluster_direct_import_guard_*` enforcement

---

## Evidence

| Artifact | Path |
|---|---|
| BV10 discovery | `docs/audits/BV10_consolidation_plan.md` |
| Delegate verification | `docs/audits/BV10A_delegate_verification.md` |
| BU fan-in | `docs/audits/BU_import_fan_in_fan_out.csv` |
| Dependency inventory | `artifacts/bv10_dependency_inventory.json` |
