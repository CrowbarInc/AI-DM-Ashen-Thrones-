# BV1 — Maintenance-Cost Attribution Matrix

**Date:** 2026-06-21  
**Scope:** Measurement only. Combines fresh BU AST scan (216 modules), BV baseline, BV1 locality, and BV1 fallback incidence.

## Executive summary

Maintenance economics after BI–BM are **not uniformly cheaper**. The gate monolith and largest test files **contracted**, while **final-emission metadata, replay projection, fallback routers, and governance tests** absorbed fan-in and ownership references. Attribution completeness **improved materially** but remains **incomplete** (38.78% owner bucket). Fallback incidence is now **measurable** at **69.16%** on the 107-FEM artifact corpus — high, with ownership splits visible but not eliminated.

**Matrix verdict:** **Shifted** dominates; **Improved** applies selectively (gate concentration, attribution, projection legibility); **Unknown** remains for bug-fix locality (zero post-BI corrective commits) and fallback trend (one snapshot).

## Area comparison table

| Area | Before (BU / BV baseline) | After (BV1 fresh scan) | Improved | Shifted | Unknown |
|---|---|---|---|---|---|
| **Replay** | 208 modules ecosystem; `golden_replay_projection` 17/7; `final_emission_replay_projection` 10/3; golden helper hub moderate | 216 modules; `golden_replay_projection` **18/7**; `final_emission_replay_projection` **15/4**; replay area **20 modules**, fan-in **86** (prod FI **1**, test FI **57**) | Projection simplified in BL (test-side); recurrence instrumentation live (BQ) | Fan-in moved into replay projection + drift taxonomy helpers; speaker-projection recurrence **8** protected rows | Live-traffic replay incidence not measured separately from artifact corpus |
| **Final emission** | Gate **29/7** (~9300 lines pre-BJ); finalize **13/7**; meta **57/4**; terminal pipeline **25/14** | Gate **28/7** (308 lines); finalize **11/8**; meta **61/6**; terminal pipeline **26/13**; FE area **43 prod modules**, fan-in **443** | Gate production fan-in **1**; gate file size collapse; explicit BJ module owners | **Meta** +4 fan-in; **strict_social_stack** 22/22; **terminal_pipeline** persists as convergence hub; test fan-in **239** across FE policy modules | Future defect locality on extracted modules unobserved (no bug-fix cohort) |
| **Fallback** | `visibility_fallback` **18/18**; BK estimated 6–11 files per dominant change; incidence **unavailable** | `visibility_fallback` **17/17**; fallback area **43 modules**, fan-in **103**, fan-out **193**; incidence **69.16%** (74/107 FEM) | BP2/BP3 coverage; BK owner map in meta/projection; selection/content owners on **70/74** events | Selection split visibility (**38**) vs gate label (**32**); content split sealed (**39**) vs opening deterministic (**31**); 13 events still lack owner bucket | Longitudinal decrease not provable (first snapshot); rate is corpus-specific |
| **Attribution** | BS1 owner bucket **17.31%**; repair_kind **15.38%**; resolved completeness **5.77%** | Owner bucket **38.78%**; repair_kind **59.18%**; resolved **32.65%**; contract compliance **100%**; strict completeness **0%** | +21.47 pp owner bucket; +43.8 pp repair_kind; recurrence_key **100%** | Gaps concentrated: response type **0/6** resolved, sealed **0/5**, repair mutation **0/4**; attribution reads span **17 modules**, fan-in **75** | Strict completeness still zero; source_family slipped **0.95 pp** |
| **Speaker finalize** | `speaker_contract_enforcement` **15/4** stable; BT parity probes added | `speaker_contract_enforcement` **15/4**; finalize **11/8**; terminal_pipeline **26/13** in finalize path; area fan-in **80**, fan-out **125** | Covered P3/P4 parity probes pass; measurable divergence taxonomy (`dialogue_plan_subtractive_strip`) | Finalize stack shares terminal pipeline hub with non-speaker work; post-speaker text mutation layer explicit | Runtime frequency of speaker mismatch branches not measured on representative replay turns |

## Per-area metrics (after)

### Replay

| Metric | Value |
|---|---:|
| Modules in area | 20 |
| Total fan-in / fan-out | 86 / 80 |
| Production fan-in | 1 |
| Test fan-in | 57 |
| Ownership refs (lexical) | 650 |
| Top hub | `tests.helpers.golden_replay_projection` **18/7** |

### Final emission (production policy + gate + finalize)

| Metric | Value |
|---|---:|
| Production modules | 43 |
| Total fan-in / fan-out | 443 / 218 |
| Production fan-in | 174 |
| Top hub | `game.final_emission_meta` **61/6** (134 ownership refs) |
| Gate | **28/7**, production fan-in **1** |

### Fallback

| Metric | Value |
|---|---:|
| Modules | 43 |
| Fan-in / fan-out | 103 / 193 |
| Top two-way hub | `game.final_emission_visibility_fallback` **17/17** |
| Incidence trigger rate | **69.16%** |
| Dominant kinds | referential clarity (51%), scene opening (42%) |

### Attribution

| Metric | Value |
|---|---:|
| Modules | 17 |
| Fan-in / fan-out | 75 / 53 |
| Top module | `game.realization_provenance` **28/1** |
| Owner bucket coverage | **38.78%** (19/49 records) |

### Speaker finalize

| Metric | Value |
|---|---:|
| Modules | 19 |
| Fan-in / fan-out | 80 / 125 |
| Core enforcement | `game.speaker_contract_enforcement` **15/4** |
| Shared finalize hub | `game.final_emission_terminal_pipeline` **26/13** |

## Test ownership concentration (cross-cutting)

| Module | Fan-in | Fan-out | Role |
|---|---:|---:|---|
| `tests.helpers.emission_smoke_assertions` | **70** | 5 | Test facade; high consumer concentration |
| `tests.test_ownership_registry` | 0 | **57** | Governance meta-router |
| `tests.helpers.golden_replay_projection` | 18 | 7 | Replay acceptance adapter |

Test fan-in growth **does not** equal runtime coupling, but it **does** increase maintenance surface for governance changes.

## Hotspot frequency signals

| Signal | Source | Frequency | Interpretation |
|---|---|---:|---|
| Speaker projection drift | `bug_recurrence_history.json` | **8** protected rows | Recurring replay/speaker boundary work |
| Other protected families | same | 1 each × 3 | Watch state |
| Fallback route `observe` | BV1 incidence | **95.45%** trigger rate | Dominant corpus hotspot |
| Gate file touches (historical) | BR git hotspots | 64 commits all-time | Legacy cost; current file thin |
| `final_emission_meta` fan-in | BU scan | **61** | Growing read-side hub |

## Interpretation for BV classification

| Criterion | Satisfied? |
|---|---|
| Bug-fix locality improved | **No** (N=0 post-BI bug fixes) |
| Hotspot concentration reduced | **Partial** (gate yes; meta/replay/governance up) |
| Fallback incidence reduced or stable | **Unknown** (baseline only; rate high) |
| No equivalent new maintenance hub | **No** (terminal pipeline, strict stack, meta, smoke facade) |
| Ownership improved | **Yes** |
| Burden moved to new hubs | **Yes** |

This matrix supports **`REDISTRIBUTED_COST`**, not **`REDUCED_COST`**.

## Evidence

| Source | Path |
|---|---|
| BU import fan-in/fan-out (fresh scan, restored from side-effect write) | `artifacts/bv1_maintenance_matrix_data.json` |
| BU baseline | `docs/audits/BU_post_bj_fan_in_fan_out_validation.md`, BV §6 |
| Bug-fix locality | `docs/audits/BV1_bug_fix_locality_validation.md` |
| Fallback incidence | `docs/audits/BV1_fallback_incidence_validation.md` |
| Attribution | `artifacts/bv1_attribution_completeness_report.md` |
| Recurrence | `artifacts/golden_replay/bug_recurrence_history.json` |

## Command log

| Command | Result |
|---|---|
| `python scripts/bu_final_emission_coupling_discovery.py` | 623 files → 216 modules (CSV side effects restored after capture) |
| Area aggregation script → `artifacts/bv1_maintenance_matrix_data.json` | Five area rollups + key modules |
| `python tools/attribution_completeness_report.py` | 49-record corpus reproduced |
| `git checkout -- docs/audits/BU_*.csv` | Restored tracked BU CSVs after scan |
