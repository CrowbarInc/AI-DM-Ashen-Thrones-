# BV10 — Read-Side Attribution Cluster Projection

**Date:** 2026-06-21
**Method:** BU ecosystem fan-in + BV10 candidate estimates + BV2/BV9 scorecard lineage

## Current measurements

| Metric | Value | Source |
|---|---:|---|
| `final_emission_meta_read` FI | **29** | BU CSV |
| `owner_bucket_views` FI | **22** | BU CSV |
| `ownership_schema` FI | **19** | BU CSV |
| **Combined cluster FI** | **70** | sum |
| Unique importers (deduped) | **54** | BV10 AST scan |
| Multi-import files | **16** | BV10 hub analysis |
| meta write owner FI (context) | **24** | BV9 — already reduced |

### Concentration shares (cluster)

| Slice | Share of combined FI |
|---|---:|
| Tests + helpers | **~62%** (44/71 AST edges) |
| Production read-only | **~17%** |
| Production write-adjacent (fallback read) | **~13%** |
| Authority re-imports (meta write owner) | **~8%** |

---

## Projected measurements (after consolidation)

### By phase

| Phase | Actions | Combined FI | Δ | Per-module (approx.) |
|---|---|---:|---:|---|
| **Baseline** | — | **70** | — | 29 / 22 / 19 |
| **Phase 1** | C1+C2+C4 module skeletons | **~58** | −12 | 29 / 22 / 19 (unchanged) |
| **Phase 2** | Consumer migration (all waves) | **~34** | −36 | 16 / 12 / 10 |
| **Phase 2 (BV10B complete)** | Consumer migration | **~39** authority + **37** facade FI | **+38** authority | 13 / 13 / 13 |
| **Phase 3** | Governance lock + re-export trim | **~26–30** | −40 to −44 | 14 / 10 / 8 |

### By candidate (cumulative combined FI)

| Candidate | Combined FI after | Cumulative Δ |
|---|---:|---:|
| Baseline | 70 | 0 |
| + C1 attribution_read_views | 58 | −12 |
| + C4 observability_attribution_read | 51 | −19 |
| + C3 replay_attribution_adapter | 43 | −27 |
| + C5 smoke hardening | 37 | −33 |
| + C2 ownership_projection_views | **26–30** | **−40 to −44** |

*Overlap adjustment: replay adapter and attribution views share 3–4 importers.*

---

## Scorecard impact (BV9 maintenance matrix)

| Area | BV9 FI | Projected post-BV10 | Notes |
|---|---:|---:|---|
| attribution | 106 | **~88–92** | Classifier/sync chain thinned |
| replay | 126 | **~118–122** | Adapter absorbs cluster reads; golden path unchanged |
| final_emission | 410 | **~392–398** | Read facade FI redistributes, write owner stable |
| tests_smoke | 54 | **~48–50** | Gate read helper consolidation |

**BV9 drag center addressed:** `final_emission_meta_read_attribution_cluster` → redistributed across domain facades; combined hub FI −43 to −57%.

---

## Comparison to BV2 meta consolidation

| Metric | BV2 (meta write) | BV10 (read cluster) |
|---|---|---|
| Baseline FI | 61 | 70 (combined) |
| Achieved / target FI | 22 (achieved) | **26–30** (target) |
| Reduction | **−64%** | **−43 to −57%** |
| Replay risk | Medium (BV2B) | Medium (Wave 2C only) |
| Owner authority change | None | None |

---

## Success criteria

| Criterion | Target | Projected | Met? |
|---|---|---|---|
| Combined cluster FI ≤30 | ≤30 | **26–30** | ✓ (phase 3) |
| No ownership authority move | Required | Delegate-only | ✓ |
| Replay behavior unchanged | Required | Adapter delegates | ✓ (by design) |
| Concrete migration plan exists | Required | Phase 1–3 doc | ✓ |

## Evidence

| Artifact | Path |
|---|---|
| Dependency inventory | `docs/audits/BV10_dependency_inventory.md` |
| Consolidation plan | `docs/audits/BV10_consolidation_plan.md` |
| BV9 matrix | `docs/audits/BV9_maintenance_matrix.md` |
| BV2 verification template | `docs/audits/BV2_meta_consolidation_verification.md` |


---

## BV10B closeout update (2026-06-21)

| Metric | BV10A exit | BV10B exit | Δ |
|---|---:|---:|---:|
| Authority cluster FI (`meta_read` + `bucket_views` + `schema`) | 77 | **39** | **-38** |
| `attribution_read_views` FI | 0 | **20** | +20 |
| `ownership_projection_views` FI | 0 | **7** | +7 |
| `observability_attribution_read` FI | 0 | **10** | +10 |

**Phase 2 target (≤45 authority cluster FI):** **MET**.

### Phase 3 projection (revised)

| Metric | Estimate |
|---|---:|
| Authority cluster FI after governance lock | **~31–35** |
| Remaining consumer migrations (C5 smoke/gate) | **~14** |
| Governance-lock FI trim (re-export dedupe) | **−2 to −4** |

**Scorecard:** Attribution area churn routes through 3 facades; accidental multi-import hubs collapsed for classifier/sync and replay projection adapters.
