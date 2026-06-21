# BV2 — `final_emission_meta` Consumer Classification

**Date:** 2026-06-21  
**Scope:** Read-side and write-side consumers grouped by maintenance subsystem.  
**Source:** 61 direct importers from BU scan (`artifacts/bv2_meta_dependency_inventory.json`).

## Classification overview

| Subsystem | Direct importers | Prod | Test/helper | Read-only | Write/merge | Migration eligible |
|---|---:|---:|---:|---:|---:|---|
| **Fallback** | 14 | 8 | 6 | 3 | 11 | Partial (read/bucket tests) |
| **Tests** | 14 | 0 | 14 | 8 | 6 | High (non-owner suites) |
| **Final emission** | 10 | 10 | 0 | 0 | 10 | Low (legitimate write owners) |
| **Diagnostics** | 9 | 4 | 5 | 9 | 0 | **High** |
| **Terminal pipeline** | 9 | 4 | 5 | 2 | 7 | Low–medium |
| **Replay** | 2 | 1 | 1 | 2 | 0 | **High** |
| **Attribution** | 2 | 0 | 2 | 2 | 0 | **High** |
| **Speaker finalize** | 1 | 1 | 0 | 1 | 0 | Medium |

*Totals exceed 61 where files serve multiple roles; counts assign each file one primary subsystem.*

---

## Replay

**Role:** Project FEM into protected replay observations and runtime lineage owner buckets.

| Consumer | Kind | Symbols / pattern |
|---|---|---|
| `game/final_emission_replay_projection.py` | production | `opening_fallback_owner_bucket_from_meta` for lineage packaging |
| `tests/helpers/golden_replay_projection.py` | helper | Bucket constants (×8), `normalize_final_emission_meta_for_observability`, `read_*_from_turn_payload`, `opening_fallback_owner_bucket_from_meta` |
| `tests/test_golden_replay_direct_seam.py` | test | `read_final_emission_meta_dict` seam check |

**Assessment:** Golden replay helper is the **densest read-side consumer** (12 symbols). Runtime replay owner should absorb acceptance-side normalize/bucket reads (AO5 boundary).

---

## Attribution

**Role:** Classifier and inventory derive owner buckets and repair attribution from FEM.

| Consumer | Kind | Symbols / pattern |
|---|---|---|
| `tests/helpers/failure_classifier.py` | helper | `opening_fallback_owner_bucket_from_meta` |
| `tests/helpers/replacement_attribution_inventory.py` | helper | All three `*_owner_bucket_from_*` mappers |
| `tests/test_opening_fallback_owner_bucket.py` | test | 16 bucket constants + mapper parity (attribution-adjacent owner suite) |

**Assessment:** Bucket **mappers** belong with ownership schema / replay projection read views, not raw meta.

---

## Fallback

**Role:** Stamp and classify fallback selection/content ownership on FEM at write time; read bucket values in tests.

| Consumer | Kind | Write vs read |
|---|---|---|
| `game/final_emission_visibility_fallback.py` | production | Write: producer kinds, visibility bucket stamp |
| `game/final_emission_sealed_fallback.py` | production | Write: mutation lineage refresh, sealed bucket |
| `game/final_emission_opening_fallback.py` | production | Write: opening projection, bucket stamp |
| `game/opening_deterministic_fallback.py` | production | Write: context mirror defaults |
| `game/fallback_provenance_debug.py` | production | Write: provenance trace patch |
| `game/gm_retry.py` | production | Read + write: retry stamp |
| `game/upstream_response_repairs.py` | production | Write: upstream-prepared stamp (lazy) |
| `tests/helpers/opening_fallback_evidence.py` | helper | Read: bucket mappers + constants |
| `tests/test_*_fallback*.py` (6 files) | test | Constants + bucket field tests |
| `tests/test_gm_retry.py` | test | `OPENING_FALLBACK_OWNER_RETRY` constant |

**Assessment:** Production fallback modules **must keep write-path imports** on meta (or a future write-stamps submodule owned by meta). Test bucket suites can migrate to **ownership views**.

---

## Speaker finalize

| Consumer | Pattern |
|---|---|
| `game/post_emission_speaker_adoption.py` | Single read: `read_final_emission_meta_dict` for post-finalize speaker state |

**Assessment:** Candidate for **FEM read-access facade** (narrow read model).

---

## Terminal pipeline

**Role:** Finalize stack packages FEM, stamps producer repair kinds, projects accept-path sources.

| Consumer | Pattern |
|---|---|
| `game/final_emission_finalize.py` | Full packaging: sidecar, dead-turn, sanitizer attribution, lineage refresh |
| `game/final_emission_generic_exit.py` | Accept-path inference, opening projection apply |
| `game/final_emission_strict_social_stack.py` | Strict accept FEM writes + producer stamp |
| `game/final_emission_terminal_pipeline.py` | Terminal enforcement writes |
| Gate orchestration tests (5 files) | `read_final_emission_meta_dict` for order/diagnostics/snapshots |

**Assessment:** Production terminal modules stay on meta **write API**. Gate tests migrate to read facade.

---

## Diagnostics

**Role:** Observability bundles, dead-turn classification, evaluator projections — **read-only**.

| Consumer | Pattern |
|---|---|
| `game/narrative_authenticity_eval.py` | Normalize + read_from_turn_payload + FEM key registry |
| `game/playability_eval.py` | Telemetry bundle + gameplay validation summary |
| `game/dead_turn_report_visibility.py` | Same bundle pattern |
| `game/stage_diff_telemetry.py` | Read dict + NA projection for stage-diff |
| `tests/test_observational_telemetry_confidence.py` | Normalize + observability events + stage-diff projection |
| `tests/test_dead_turn_*.py` | Dead-turn classify/read |
| `tests/helpers/behavioral_gauntlet_eval.py` | Read dict + dead-turn + validation summary |
| `tools/run_scenario_spine_validation.py` | Tooling read dict |

**Assessment:** **Highest-yield migration cluster** — no write ownership; can share `final_emission_observability_read` module.

---

## Tests (owner + governance)

| Consumer | Role |
|---|---|
| `tests/test_final_emission_meta.py` | **Canonical owner suite** — must retain direct meta import |
| `tests/test_ownership_registry.py` | Static governance scan of meta import paths |
| Remaining gate/FEM tests (12 files) | Focused contract tests using read helpers or constants |

**Assessment:** Only `test_final_emission_meta.py` and registry parity tests require permanent direct meta coupling.

---

## Final emission (write/merge owners)

Modules that **package or merge** FEM subtrees at runtime (legitimate meta write owners):

- `final_emission_acceptance_quality`, `fem_assembly`, `gate_preflight_defaults`, `narration_constraint_debug`, `narrative_mode_output`, `repairs`, `response_type`, `narrative_authenticity`, `interaction_continuity`, `output_sanitizer` (constants only — migratable)

**Assessment:** **Not migration targets** except `output_sanitizer` producer-kind constants → `ownership_schema`.

---

## Cross-cutting: indirect smoke consumers

**34 files** use `emission_smoke_assertions.final_emission_meta_from_output` without importing meta. Classification: **tests / integration smoke**. Consolidation should **strengthen the facade** rather than expand meta fan-in.

---

## Evidence

| Source | Path |
|---|---|
| Inventory | [BV2_meta_dependency_inventory.md](BV2_meta_dependency_inventory.md) |
| Machine data | `artifacts/bv2_meta_dependency_inventory.json` |
