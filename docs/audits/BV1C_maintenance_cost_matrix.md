# BV1C — Maintenance Cost Matrix (Integrated)

**Date:** 2026-06-21  
**Scope:** Analysis only. Integrates BV baseline, BV1 matrix, BV1A locality/hotspots, and BV1B fallback incidence.  
**Commit boundary:** BI `f7e73fb` through HEAD `22cd49a` (10 post-BI commits).

## Executive verdict

BI–BM **did not reduce net maintenance cost**. It **redistributed** coupling from the gate monolith and test megastructures into explicit stack/pipeline owners, metadata readers, fallback routers, attribution surfaces, and governance test facades. Structural simplification is **real and measured** in scoped surfaces; **measured maintenance reduction** is **not demonstrated** (zero post-BI bug-fix cohort; fallback incidence unchanged at 69.16%).

**Classification input:** **REDISTRIBUTED_COST**

---

## Integrated area matrix

| Area | Pre-BI state | Current state | Ownership | Fan-in | Fan-out | Maintenance hotspot count | Bug-fix locality impact | Fallback impact | Net result |
|---|---|---|---|---:|---:|---:|---|---|---|
| **Replay** | 208-module ecosystem; `golden_replay_projection` 17/7; `final_emission_replay_projection` 10/3; BL simplified test projection surface | 20 modules; FI **86** / FO **80**; prod FI **1**, test FI **57**; `golden_replay_projection` **18/7**; `final_emission_replay_projection` **15/4** (+5 FI); speaker-projection recurrence **8** protected rows | Legitimate replay projection owner (`final_emission_replay_projection`); test adapter (`golden_replay_projection`); drift taxonomy helpers | **86** (area) | **80** (area) | **3** (replay projection, golden helper, drift taxonomy in top-15 post-BI touches) | **Unchanged / unobserved** — 0 bug-fix touches in BR cohort; recurrence signal on speaker projection | **Unchanged on incidence** — replay routes not dominant in 74-event corpus; BL reduced test projection surface only | **Shifted** — import-bounded but ownership-dense (136 refs on replay projection); recurrence instrumentation live |
| **Fallback** | `visibility_fallback` **18/18**; incidence **unmeasured**; BK estimated 6–11 files per dominant change | 43 modules; FI **103** / FO **193**; `visibility_fallback` **17/17**; incidence **69.16%** (74/107 FEM); selection split visibility (**38**) vs gate label (**32**); content split sealed (**39**) vs opening (**31**); 13 events unbucketed | BK-explicit selection/content owners on **70/74** events; distributed write / centralized read via meta + replay projection | **103** (area) | **193** (area) | **12** (BV1B ranked fallback ownership/test surfaces) | **Unchanged / unobserved** — 1 pre-BI bug-fix touch total in BR cohort | **Burden relocated, not removed** — trigger rate stable 69.16%; observe route **95.45%**; paths extracted to named modules | **Shifted** — legibility up; measured incidence and routing volume unchanged |
| **Attribution** | BS1 owner bucket **17.31%**; repair_kind **15.38%**; resolved **5.77%**; 17 modules | Owner bucket **38.78%**; repair_kind **59.18%**; resolved **32.65%**; contract compliance **100%**; strict completeness **0%**; 17 modules; FI **75** / FO **53**; `realization_provenance` **28/1** | BS3 contract + distributed writers; read-side concentration in provenance/lineage telemetry | **75** (area) | **53** (area) | **4** (provenance, lineage telemetry, attribution inventory, contract helpers in top ownership ranks) | **Unchanged / unobserved** — 0 bug-fix touches pre/post in attribution subsystem | **Indirect improvement** — owner bucket coverage on fallback events improved; 30/49 records still missing owner bucket | **Improved legibility, partial burden** — metadata completeness up; gaps on sealed/response-type/repair-mutation paths persist |
| **Final emission** | Gate **29/7**, ~9,316 LOC; meta **57/4**; terminal pipeline **25/14**; finalize **13/7**; 43 prod modules | Gate **28/7**, **308 LOC**, prod FI **1**; meta **61/6** (+4 FI); terminal pipeline **26/13**; strict stack **22/22**; finalize **11/8**; area FI **443** / FO **218** | BJ explicit module owners; BN import guards; gate thin facade | **443** (area) | **218** (area) | **8** (gate, meta, terminal pipeline, strict stack, sealed/opening fallback, output_sanitizer in BV1A top-15) | **Unchanged / unobserved** — gate had 3 historical bug-fix touches; 0 post-BI; extraction unprobed for cheaper fixes | **Gate code reduced; lineage label unchanged** — gate still labels 32 selection events; implementation outward | **Mixed structural** — gate hotspot **reduced**; meta + stack/pipeline **redistribution hubs** |
| **Speaker finalize** | `speaker_contract_enforcement` **15/4** stable; BT divergence undocumented | **15/4** enforcement; finalize **11/8**; terminal pipeline **26/13** shared hub; area FI **80** / FO **125**; P3/P4 parity probes pass | Split owners: enforcement vs post-adoption; shared terminal pipeline with non-speaker work | **80** (area) | **125** (area) | **2** (enforcement + terminal pipeline convergence; BT added 2 probe modules) | **Unchanged / unobserved** — 0 bug-fix touches in BR cohort | **Unchanged** — minimal speaker footprint in fallback incidence corpus | **Improved measurability, unchanged drag** — divergence taxonomy explicit; shared finalize hub persists |
| **Ownership governance** | Pre-BU20 ad hoc matrix drift; registry fan-out **54**; 311 ownership refs | BU20–BU30 closed: matrix contract CI-enforced; registry **57** fan-out, **320** refs; touched **5/10** post-BI commits; split-owner acceptance self-maintaining on critical path | Legitimate governance meta-router (`test_ownership_registry`); BU15 generated report; CI refresh workflow | **0** (registry FI) | **57** (registry FO) | **1** dominant + **3** secondary (matrix contract tests, convergence inventory guard, failure classifier alignment) | **Unchanged / unobserved** — governance commits broad (median 31 files) but not corrective | **Improved fallback owner stamping** — BK/BU alignment; 13 events still unbucketed at runtime | **Improved clarity, relocated test burden** — governance surface mature; registry remains high fan-out router |
| **Tests** | Gate test monolith 2,917 LOC; golden replay monolith 803 LOC; smoke facade emerging | Gate stub **19 LOC** (BM); golden stub **26 LOC**; `emission_smoke_assertions` **70** FI; `test_ownership_registry` **57** FO; test FI **239** across FE policy modules; governance median **31** files/commit | Intentional test facades and regression locks; monolith decomposition to focused files | **70** (smoke facade) + area aggregates above | **57** (registry) + delegator regression **41** | **6** (smoke facade, ownership registry, gate delegator regression, visibility fallback test, meta test, golden replay fallback projection) | **Unchanged / unobserved** — tests absorbed 24/24 path touches in pre-BI bug-fix cohort; post-BI touches are program work | **Test ownership of fallback improved** — BK/BP incidence and owner-bucket tests added | **Shifted** — monolith stubs gone; **new** test-hub concentration (smoke + registry + fallback suites) |

---

## Maintenance burden accounting (claimed improvements)

| Claimed improvement | Burden removed | Burden relocated | Burden unchanged | Structural simplification? | Measured maintenance reduction? |
|---|---|---|---|---|---|
| Gate monolith extraction (BJ) | ~9,000 LOC gate orchestration; prod gate FI **29→1** | Stack/pipeline/strict/non-strict modules; 70-importer smoke facade | Gate test historical cost (64 commits all-time); gate labels 32 fallback selection events | **Yes** — thin facade, explicit owners | **No** — refactor median 18 files; N=0 bug fixes |
| Gate fan-out reduction (BN) | Monolithic import guards split to preflight modules | 8 preflight modules + import guard maintenance | Terminal pipeline convergence | **Yes** | **No** |
| Fallback ownership compression (BK) | Implicit gate-internal fallback routing | visibility, sealed, opening, deterministic modules + tests | 69.16% incidence; observe 95.45% route rate | **Yes** — named owners | **No** — incidence identical BV1→BV1B |
| Replay projection simplification (BL) | Golden replay test projection complexity | `final_emission_replay_projection` ownership refs (+136); drift helpers | Speaker projection recurrence (8 rows) | **Partial** (test-side) | **No** |
| Test monolith decomposition (BM) | Single gate/golden integration files | Many focused test files + delegator regression router | Top test files still >1,500 LOC each | **Yes** | **No** |
| Attribution completeness (BS) | — | Attribution read modules; inventory helpers | 30/49 missing owner bucket; strict completeness 0% | **Partial** (contract) | **Partial** (field coverage +21–44 pp) |
| Governance stack (BU20–BU30) | Ad hoc matrix drift risk on critical path | Registry fan-out; manual secondary doc sync | Deep classifier/FEM behavior tests outside CI slice | **Yes** (CI self-maintaining core) | **No** (governance commits among broadest touches) |
| Fallback incidence instrumentation (BP) | Incidence previously unmeasurable | BP5–BP12 report stack maintenance | 69.16% rate now baseline, not reduced | **Yes** (observability) | **No** (rate unchanged) |

---

## Hotspot count methodology

**Maintenance hotspot count** = files appearing in BV1A top-15 post-BI change list **or** BV1B top-12 fallback ownership list **for that area**. Cross-area files (e.g. terminal pipeline) attributed to primary responsibility.

| Area | Count | Primary magnets |
|---|---:|---|
| Replay | 3 | `final_emission_replay_projection`, `golden_replay_projection`, drift taxonomy helpers |
| Fallback | 12 | visibility/sealed/opening modules + owner-bucket/incidence test facades |
| Attribution | 4 | `realization_provenance`, `runtime_lineage_telemetry`, attribution inventory/contract helpers |
| Final emission | 8 | gate, meta, terminal pipeline, strict stack, sealed/opening fallback, sanitizer |
| Speaker finalize | 2 | `speaker_contract_enforcement`, shared `terminal_pipeline` |
| Ownership governance | 4 | `test_ownership_registry`, matrix contract, convergence inventory, classifier alignment |
| Tests | 6 | smoke facade, registry, delegator regression, visibility/meta/golden fallback tests |

---

## Net result summary

| Net label | Areas |
|---|---|
| **Reduced** (structural, scoped) | Final emission gate entry; test monolith stubs; governance CI critical path |
| **Improved legibility** | Attribution, fallback ownership metadata, speaker parity probes, incidence observability |
| **Shifted / relocated** | Replay projection, fallback routing, stack/pipeline orchestration, test facades |
| **Unchanged (measured)** | Bug-fix locality; fallback trigger rate; strict attribution completeness; ecosystem breadth (216 modules, +8 vs BU baseline) |

---

## Evidence

| Source | Role |
|---|---|
| [BV1_maintenance_cost_matrix.md](BV1_maintenance_cost_matrix.md) | BV1 five-area comparison |
| [BV1A_maintenance_hotspots.md](BV1A_maintenance_hotspots.md) | Post-BI change-frequency ranks |
| [BV1A_bug_fix_locality_comparison.md](BV1A_bug_fix_locality_comparison.md) | N=0 corrective cohort |
| [BV1B_fallback_baseline_comparison.md](BV1B_fallback_baseline_comparison.md) | Incidence stable at 69.16% |
| [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md) | Relocated-not-removed paths |
| [BU_post_bj_fan_in_fan_out_validation.md](BU_post_bj_fan_in_fan_out_validation.md) | Pre-BV1 fan-in baseline |
| `artifacts/bv1_maintenance_matrix_data.json` | Machine rollups |
| `artifacts/bv1a_analysis.json` | Hotspot ranks |
