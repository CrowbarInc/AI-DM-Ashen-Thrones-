# BV1C — Hub Migration Analysis

**Date:** 2026-06-21  
**Question:** Did BI–BM remove maintenance hubs, or relocate them?  
**Sources:** BU fan-in/fan-out validation, BN gate fan-out reduction, BJ extraction, BV1A/BV1B hotspot ranks, `artifacts/bv1_maintenance_matrix_data.json`.

## Executive verdict

Hub migration is predominantly **relocate-and-reduce**, not **remove**. One historical monolith hub (gate orchestration) was **materially reduced**. Four **new** operational hubs were created by BJ. Fallback and metadata read-side hubs **grew** or **persisted** at high fan-in. Test-side hubs **replaced** direct gate imports rather than eliminating coupling.

---

## A. Hubs removed

| Hub | Pre-BI evidence | Current evidence | Verdict |
|---|---|---|---|
| Gate monolith orchestration body | ~9,316 LOC; 125 import statements (BO); primary FE change magnet | **308 LOC**; prod fan-in **1**; orchestration delegated to stacks/pipeline | **Removed as monolith hub** — file no longer acts as utility namespace |
| `tests/test_final_emission_gate.py` integration monolith | 2,917 LOC (BO) | **19 LOC** stub (BM) | **Removed as monolith** — decomposed to focused suites |
| `tests/test_golden_replay.py` integration monolith | 803 LOC (BO) | **26 LOC** stub (BM) | **Removed as monolith** |
| Implicit in-gate fallback selection | Undifferentiated gate internals | Named modules own selection/content (BK) | **Removed as implicit hub** — behavior externalized |

**Count: 4 hub classes removed** (3 file-level monoliths + 1 implicit routing layer).

No production module dropped below measurable fan-in to zero; removal means **role elimination**, not file deletion.

---

## B. Hubs reduced

| Hub | Pre-BI (BU/BO) | Current (BV1) | Delta | Mechanism |
|---|---|---:|---:|---|
| `game.final_emission_gate` | FI **29**, FO **7**, ~9,316 LOC | FI **28**, FO **7**, **308 LOC**, prod FI **1** | LOC **−97%**; prod FI **−96%** | BJ extraction + BN import guards |
| `game.final_emission_finalize` | FI **13**, FO **7** | FI **11**, FO **8** | FI **−2** | BJ explicit finalizer; moderate shared hub |
| `game.final_emission_visibility_fallback` | FI **18**, FO **18** | FI **17**, FO **17** | FI **−1**, FO **−1** | BK ownership split; still bidirectional |
| `game.final_emission_replay_projection` (imports) | FI **10**, FO **3** | FI **15**, FO **4** | FI **+5** ⚠️ | Ownership refs grew; import hub **expanded** |
| Gate test direct imports | 125 gate import statements (BO) | Prod **1** direct gate importer | Prod coupling **−99%** | Delegator pattern + smoke facade |

**Net reduced hubs: 3 production hubs** with meaningful fan-in/LOC drop (gate, finalize, visibility_fallback). Replay projection import hub **increased** despite BL test simplification.

---

## C. Hubs relocated

| Former concentration | New owner(s) | Fan-in / fan-out | Incidence / locality impact |
|---|---|---|---|
| Gate-internal stack routing | `final_emission_strict_social_stack` | **22/22** | BJ routing hub; test-heavy inbound |
| Gate-internal terminal orchestration | `final_emission_terminal_pipeline` | **26/13** | Convergence hub; 4/10 post-BI touches |
| Gate-internal non-strict paths | `final_emission_non_strict_stack` | **11/19** (BU) → in FE rollup | Fan-out hotspot |
| Gate-embedded fallback selection | `final_emission_visibility_fallback` | **17/17** | 38 selection-owner events; 51% referential clarity |
| Gate-embedded sealed content | `final_emission_sealed_fallback` | **10/13** | 39 content-owner events |
| Gate-embedded opening content | `opening_deterministic_fallback` | content owner on 31 events | Explicit BK owner |
| Gate test imports | `tests.helpers.emission_smoke_assertions` | **70/5** | Test dependency hub replacing gate namespace |
| Gate regression locks | `tests.test_final_emission_gate_delegator_regression` | **41** fan-out | Static source-lock router |
| Ownership assertions | `tests.test_ownership_registry` | **57** fan-out, **320** refs | Governance meta-router; 5/10 post-BI commits |
| Fallback lineage packaging default | meta + replay projection read path | meta **61/6**; replay proj **15/4**, 136 refs | Centralized read; distributed write preserved |
| Attribution gaps | BS inventory + contract helpers | provenance **28/1** | Read-side attribution hub |

**Count: 11 relocated hub roles** (7 production routing, 4 test/governance).

---

## D. New hubs created

| Hub | Created by | Fan-in / fan-out | Legitimate owner? | Accidental hub? |
|---|---|---:|---|---|
| `game.final_emission_strict_social_stack` | BJ | **22/22** | Yes — strict-path router | No — intentional; test-amplified |
| `game.final_emission_terminal_pipeline` | BJ | **26/13** | Yes — terminal enforcement owner | Borderline — cross-cutting finalize/fallback/speaker |
| `game.final_emission_non_strict_stack` | BJ | **10/19** (BU baseline) | Yes — non-strict router | No |
| `tests.helpers.emission_smoke_assertions` | BJ/BM downstream | **70/5** | Yes — shared test facade | **Concentration risk** — replacement import hub |
| Governance incidence stack (BP) | BP | 6+ report modules + tests | Yes — observability | Maintenance surface for reports, not runtime |
| Split-owner matrix CI lane | BU20–BU30 | contract + refresh CLI | Yes — governance | Low-frequency manual adjacent steps remain |

**Count: 4 new production routing hubs** (BJ stacks/pipeline) + **2 new test/observability hubs** with material fan-in.

`final_emission_meta` is **not new** but **grew**: FI **57→61** (+4), ownership refs **175→134** (BV1 key_modules) — classified under **relocated read-side growth**, not new creation.

---

## Migration summary matrix

| Category | Count | Representative modules |
|---|---:|---|
| **A. Removed** | 4 | Gate monolith body, gate/golden test monoliths, implicit in-gate fallback |
| **B. Reduced** | 3 | `final_emission_gate`, `finalize`, `visibility_fallback` (partial) |
| **C. Relocated** | 11 | stacks, pipeline, fallback owners, smoke facade, registry, meta/replay read path |
| **D. New** | 6 | strict/non-strict stacks, terminal pipeline, smoke facade, BP/BU governance surfaces |

---

## BU / BN / BJ cross-reference

| Cycle | Hub migration contribution |
|---|---|
| **BJ** | Removed gate monolith; created strict stack, non-strict stack, terminal pipeline, finalize split; relocated 35 production modules |
| **BN** | Reduced gate fan-out via preflight module guards; did not remove terminal pipeline convergence |
| **BK** | Relocated fallback selection/content to named modules; unchanged incidence |
| **BL** | Reduced golden replay test projection; replay runtime hub FI increased |
| **BM** | Removed test monolith hubs; created many focused test files |
| **BU** | Measured redistribution; confirmed gate prod FI=1; documented meta/replay/test hub growth |

---

## Interpretation

1. **Single-hub elimination succeeded** at the gate entry — the primary BI–BM intent for FE orchestration.
2. **Multi-hub redistribution** replaced one monolith with several medium fan-in owners — ecosystem top-5 fan-in share remains ~33% (BU).
3. **Fallback hubs persist** at unchanged incidence — relocation improved naming, not volume.
4. **Test hubs are the largest fan-in nodes** — coupling containment, not elimination.
5. **Read-side metadata hubs grew** — meta + replay projection absorb ownership interpretation load from distributed writers.

This pattern supports **REDISTRIBUTED_COST**: fewer catastrophic monolith touchpoints, **more** explicit maintenance anchors.

---

## Evidence

| Source | Path |
|---|---|
| BU validation | [BU_post_bj_fan_in_fan_out_validation.md](BU_post_bj_fan_in_fan_out_validation.md) |
| Fallback migration | [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md) |
| Hotspots | [BV1A_maintenance_hotspots.md](BV1A_maintenance_hotspots.md), [BV1B_fallback_maintenance_hotspots.md](BV1B_fallback_maintenance_hotspots.md) |
| BO baseline | [BO_maintenance_economics_report.md](../cycles/BO_maintenance_economics_report.md) |
| Machine data | `artifacts/bv1_maintenance_matrix_data.json` |
