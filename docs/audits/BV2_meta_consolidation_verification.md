# BV2 — Fan-In Verification & Post-Consolidation Projection

**Date:** 2026-06-21  
**Method:** `scripts/bu_final_emission_coupling_discovery.py` (216-module ecosystem) + BV2 importer analysis

---

## Current measurements (baseline)

| Metric | `final_emission_meta` | Ecosystem context |
|---|---:|---|
| **Fan-in (total)** | **61** | #2 hub (smoke facade 70) |
| Fan-in (production) | 27 | #1 production read hub |
| Fan-in (tests) | 28 | Concentrated in bucket + gate suites |
| Fan-in (helpers) | 6 | `golden_replay_projection` largest |
| **Fan-out** | **6** | schema, replay_projection, validators, realization_provenance, state_channels, telemetry_vocab |
| Ownership refs (lexical) | 134–175 | BU ownership map |
| Direct importers (enumerated) | 61 | `artifacts/bv2_meta_dependency_inventory.json` |
| Indirect read via smoke facade | 34 files | Not counted in FI |

### Fan-in concentration shares (meta)

| Slice | Share of meta FI |
|---|---:|
| Production write/merge owners | 44% (27/61) |
| Test/helper read + bucket | 56% (34/61) |
| Read-only production | 15% (9/61) — migration eligible |

### Top importers by dependency weight

| Rank | Importer | Why it matters |
|---:|---|---|
| 1 | `tests/test_final_emission_meta.py` | Owner suite — permanent |
| 2 | `tests/helpers/golden_replay_projection.py` | 12 symbols — C4 target |
| 3 | `tests/test_opening_fallback_owner_bucket.py` | 16 symbols — C1 target |
| 4 | `game/final_emission_visibility_fallback.py` | Write owner — stays |
| 5 | `game/final_emission_finalize.py` | Write owner — stays |
| 6 | `tests/helpers/emission_smoke_assertions.py` | Central read delegate — C2 |

---

## Projected measurements (after consolidation)

### By phase (conservative)

| Phase | Actions | Projected FI | Δ FI | Projected FO (meta) | Ownership refs |
|---|---|---:|---:|---:|---|
| **Baseline** | — | **61** | — | **6** | ~175 |
| **Phase 1** | C1 views + C5 constants + read skeleton | **47** | −14 | 6–7 | ~175 (unchanged) |
| **Phase 2** | C2 + C3 + C4 consumer migration | **29** | −18 | 6 | ~160 (shift to views/replay) |
| **Phase 3** | Re-export cleanup + registry lock | **20–22** | −7–9 | **5** | ~140 |

### By candidate (cumulative)

| Candidate | FI after | Cumulative Δ |
|---|---:|---:|
| Baseline | 61 | 0 |
| + C1 owner-bucket views | 47 | −14 |
| + C2 read facade | 31 | −30 |
| + C3 observability read | 29 | −32 |
| + C4 replay adapter | 26 | −35 |
| + C5 producer constants | 25 | −36 |
| + C3/C2 overlap adjustment | **20–22** | **−39 to −41** |

*Overlap: stage_diff and gm_retry counted once across C2/C3.*

---

## Projected fan-in concentration (success criteria)

| Criterion | Target | Projected | Met? |
|---|---|---|---|
| Meta FI reduced ≥40% | ≤36 | **20–29** | ✓ |
| Test/helper FI ≤10 | ≤10 | **2–7** | ✓ (phase 2+) |
| Read-only prod FI ≤2 | ≤2 | **0–1** | ✓ (phase 2+) |
| No new meta importers without owner review | 0 drift | Registry lock | ✓ (phase 3) |
| Runtime behavior unchanged | Required | Delegate-only extraction | ✓ (by design) |

---

## New module fan-in (expected redistribution)

| Module | Projected FI | Role |
|---|---:|---|
| `final_emission_owner_bucket_views` | 14–18 | Absorbs bucket read pattern |
| `final_emission_meta_read` | 18–22 | Absorbs sidecar read pattern |
| `final_emission_observability_read` | 8–10 | Absorbs normalize/bundle pattern |
| `final_emission_replay_projection` | +3–4 (delta) | Acceptance adapter growth |
| `final_emission_ownership_schema` | +2–3 (delta) | Constants-only imports |

**Net ecosystem FI:** Unchanged or slightly increased (explicit facades vs one mega-hub) — **meta concentration** is the metric that must drop.

---

## Ownership concentration projection

| Surface | Before | After |
|---|---|---|
| Meta ownership refs | 175 | ~140 (write-focused) |
| Schema + views refs | ~50 | ~90 (read vocabulary centralized) |
| Replay projection refs | 122 | ~130 (acceptance reads absorbed) |
| Accidental read smear | 34 tests on meta | ≤3 (owner + registry only) |

---

## Verification commands (post-implementation)

```bash
python scripts/bu_final_emission_coupling_discovery.py
# Compare game.final_emission_meta row in docs/audits/BU_import_fan_in_fan_out.csv

pytest tests/test_final_emission_meta.py tests/test_opening_fallback_owner_bucket.py -q
pytest -m golden_replay -q
pytest tests/test_ownership_registry.py -q -k meta
```

Store snapshot: `artifacts/bv2_meta_fan_in_baseline.json` (to be captured on implementation start).

---

## Baseline artifact (this analysis pass)

Current inventory committed at:

- `artifacts/bv2_meta_dependency_inventory.json` (61 importers pre-BV2)
- `artifacts/bv2_meta_fan_in_baseline.json` (post-BV2C: FI=22)
- `docs/audits/BU_import_fan_in_fan_out.csv`

---

## Post-BV2C measured results (2026-06-21)

| Phase | `final_emission_meta` FI |
|---|---:|
| Pre-BV2 | 61 |
| BV2A | 47 |
| BV2B | 31 |
| **BV2C** | **22** |

| Facade module | Post-BV2C FI |
|---|---:|
| `final_emission_meta_read` | 28 |
| `final_emission_owner_bucket_views` | 21 |
| `final_emission_replay_projection` | 15 |

All Phase 3 success criteria met. See [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md).

---

## Hub reclassification (post-BV2C)

### Is `final_emission_meta` still a maintenance hub?

**Yes, but narrowed.** Meta remains the canonical **write/packaging owner** for FEM shape, merges, stamps, and sidecar assembly. Fan-in dropped from **61 → 22**; remaining importers are exclusively write-path production modules plus two governance/owner test suites.

Meta is **no longer** the primary hub for:
- Sidecar reads (→ `meta_read`, FI 28)
- Owner-bucket projection (→ `owner_bucket_views`, FI 21)
- Golden replay acceptance reads (→ `replay_projection` adapters, FI 15)

### Has hub concentration been materially reduced?

**Yes.** Pre-BV2, 56% of meta importers were test/helper read consumers. Post-BV2C, **91%** of meta importers (20/22) are production write owners; test read smear eliminated except the FEM owner suite.

### Did BV2 create replacement hubs?

| New hub | FI | Absorbed pattern |
|---|---:|---|
| `final_emission_meta_read` | 28 | Sidecar reads, observability normalize, debug defaults |
| `final_emission_owner_bucket_views` | 21 | Bucket vocabulary + read mappers |
| `final_emission_replay_projection` | 15 | Runtime lineage + replay acceptance adapters |

**Net effect:** Concentration **redistributed** from one mega-module to explicit facades. Total ecosystem import edges increased modestly; **meta maintenance blast radius** decreased 64%.

### BV2 closeout status

**Closed.** Registry lock (`test_bv2c_final_emission_meta_direct_import_guard_*`) prevents read-side regression.

---

## Evidence

| Document | Path |
|---|---|
| Dependency inventory | [BV2_meta_dependency_inventory.md](BV2_meta_dependency_inventory.md) |
| Consolidation plan | [BV2_meta_consolidation_plan.md](BV2_meta_consolidation_plan.md) |
| BV2A closeout | [BV2A_meta_read_extraction.md](BV2A_meta_read_extraction.md) |
| BV2B closeout | [BV2B_replay_attribution_migration.md](BV2B_replay_attribution_migration.md) |
| BV2C remaining imports | [BV2C_remaining_meta_imports.md](BV2C_remaining_meta_imports.md) |
| BV2C fan-in closeout | [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md) |
| Candidates | [BV2_meta_consolidation_candidates.md](BV2_meta_consolidation_candidates.md) |
