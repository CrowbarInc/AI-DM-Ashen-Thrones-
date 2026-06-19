# BO — Maintenance Compression Closeout Audit

**Cycle:** BO (Maintenance Economics Measurement)  
**Date:** 2026-06-17  
**Status:** Audit complete — measurement only, no refactors  
**Scope:** Post BJ / BK / BL / BN / BM contraction sequence  
**Method:** Static AST import graph + LOC scan across 602 Python files (267,869 total LOC). Artifacts: `artifacts/bo_maintenance_audit.json`.

---

## Executive Summary

The BJ / BN / BM contraction sequence **materially improved gate and test monolith economics**. The canonical gate module collapsed from ~8,968 LOC (Cycle AN baseline) to **324 LOC**; gate context preflight is now **194 LOC + 8 preflight modules (436 LOC)** with BN1–BN11 import guards. Test monoliths decomposed: `test_final_emission_gate.py` (2,917 → 19 LOC stub) and `test_golden_replay.py` (803 → 26 LOC stub).

However, the repository has reached a **new plateau**, not uniform improvement:

- **141 files >500 LOC** and **52 files >1,000 LOC** remain.
- Largest drag has **shifted** from gate orchestration to **runtime megamodules** (`interaction_context`, `api`, `gm`), **fallback projection seams** (BK-identified), and **helper/test megastructures** (`golden_replay.py`, `test_final_emission_visibility_fallback.py`, `test_ownership_registry.py`).
- Replay maintenance is **partially localized** (41-file ownership island, 13,096 LOC) but **two helper hubs** (`golden_replay.py`, `golden_replay_projection.py`) still concentrate 3,580 LOC and 21 external callers.
- Final emission maintenance is **localized at the gate entry** but **not localized across the fallback visibility cluster** (BK touch cascade still live).

**Verdict:** Maintenance economics improved **within the contraction scope** (gate, test monoliths, import guards). Broader repo economics remain **moderate** — dependency hubs and >1K LOC files dominate remaining change cost.

---

## A. Hotspot Analysis

### Top 25 Largest Files by Line Count

| Rank | File | LOC |
|------|------|----:|
| 1 | `game/interaction_context.py` | 6,004 |
| 2 | `game/api.py` | 5,534 |
| 3 | `game/gm.py` | 4,579 |
| 4 | `tests/test_ownership_registry.py` | 4,518 |
| 5 | `game/social_exchange_emission.py` | 3,881 |
| 6 | `tests/test_prompt_context.py` | 3,597 |
| 7 | `game/narrative_planning.py` | 3,197 |
| 8 | `game/leads.py` | 3,196 |
| 9 | `game/prompt_context.py` | 3,067 |
| 10 | `game/gm_retry.py` | 2,854 |
| 11 | `game/social.py` | 2,828 |
| 12 | `tests/test_social_exchange_emission.py` | 2,295 |
| 13 | `game/planner_ctir_projection.py` | 2,276 |
| 14 | `game/final_emission_validators.py` | 2,229 |
| 15 | `game/final_emission_meta.py` | 2,210 |
| 16 | `game/clues.py` | 2,075 |
| 17 | `tools/architecture_audit.py` | 2,023 |
| 18 | `tests/helpers/golden_replay.py` | 1,995 |
| 19 | `tests/test_turn_pipeline_shared.py` | 1,981 |
| 20 | `game/final_emission_visibility_fallback.py` | 1,976 |
| 21 | `tests/test_final_emission_visibility_fallback.py` | 1,927 |
| 22 | `game/narrative_authenticity.py` | 1,861 |
| 23 | `tests/test_prompt_and_guard.py` | 1,856 |
| 24 | `game/intent_parser.py` | 1,796 |
| 25 | `tests/test_synthetic_smoke.py` | 1,705 |

### Top 25 Most-Imported Modules (import statement count)

| Rank | Module | Import Count |
|------|--------|-------------:|
| 1 | `game.gm` | 153 |
| 2 | `game.storage` | 150 |
| 3 | `game.final_emission_gate` | 125 |
| 4 | `game.defaults` | 98 |
| 5 | `game` (package) | 91 |
| 6 | `game.interaction_context` | 85 |
| 7 | `tests.helpers.emission_smoke_assertions` | 77 |
| 8 | `game.api` | 76 |
| 9 | `game.final_emission_meta` | 73 |
| 10 | `game.social_exchange_emission` | 70 |
| 11 | `game.final_emission_strict_social_stack` | 59 |
| 12 | `game.final_emission_text` | 52 |
| 13 | `game.final_emission_repairs` | 47 |
| 14 | `game.social` | 45 |
| 15 | `game.leads` | 45 |
| 16 | `game.final_emission_non_strict_stack` | 42 |
| 17 | `game.prompt_context` | 38 |
| 18 | `game.final_emission_validators` | 36 |
| 19 | `game.final_emission_terminal_pipeline` | 36 |
| 20 | `game.ctir_runtime` | 35 |
| 21 | `game.exploration` | 31 |
| 22 | `game.world` | 29 |
| 23 | `game.utils` | 26 |
| 24 | `game.realization_provenance` | 26 |
| 25 | `game.final_emission_visibility_fallback` | 25 |

### Top 25 Highest Fan-Out Modules (unique internal dependencies)

| Rank | Module | Fan-Out |
|------|--------|--------:|
| 1 | `tests.test_ownership_registry` | 56 |
| 2 | `game.api` | 48 |
| 3 | `tests.test_final_emission_gate_delegator_regression` | 42 |
| 4 | `game.prompt_context` | 34 |
| 5 | `game.final_emission_strict_social_stack` | 21 |
| 6 | `tests.test_final_emission_gate_orchestration_order` | 21 |
| 7 | `tests.test_final_emission_opening_fallback` | 20 |
| 8 | `game.final_emission_non_strict_stack` | 19 |
| 9 | `game.final_emission_visibility_fallback` | 18 |
| 10 | `game.api_turn_support` | 17 |
| 11 | `tests.test_prompt_context` | 17 |
| 12 | `game.gm` | 16 |
| 13 | `game.gm_retry` | 15 |
| 14 | `tests.test_social_exchange_emission` | 15 |
| 15 | `tests.test_final_emission_gate_selector_snapshots` | 14 |
| 16 | `tests.test_mixed_state_recovery_regressions` | 14 |
| 17 | `tests.test_narration_transcript_regressions` | 14 |
| 18 | `game.exploration` | 13 |
| 19 | `game.final_emission_terminal_pipeline` | 13 |
| 20 | `tests.helpers.golden_replay` | 13 |
| 21 | `tests.test_c4_narrative_mode_live_pipeline` | 13 |
| 22 | `tests.test_final_emission_boundary_convergence` | 13 |
| 23 | `tests.test_final_emission_meta` | 13 |
| 24 | `game.final_emission_generic_exit` | 12 |
| 25 | `game.social_exchange_emission` | 12 |

### Top 25 Highest Fan-In Modules (unique internal importers)

| Rank | Module | Fan-In |
|------|--------|-------:|
| 1 | `game.storage` | 112 |
| 2 | `game.defaults` | 94 |
| 3 | `game` (package) | 78 |
| 4 | `game.interaction_context` | 74 |
| 5 | `tests.helpers.emission_smoke_assertions` | 69 |
| 6 | `game.api` | 61 |
| 7 | `game.gm` | 60 |
| 8 | `game.final_emission_meta` | 57 |
| 9 | `game.social_exchange_emission` | 53 |
| 10 | `game.final_emission_text` | 49 |
| 11 | `game.leads` | 43 |
| 12 | `game.prompt_context` | 37 |
| 13 | `game.social` | 37 |
| 14 | `game.ctir_runtime` | 33 |
| 15 | `game.final_emission_gate` | 28 |
| 16 | `game.exploration` | 27 |
| 17 | `game.world` | 27 |
| 18 | `game.realization_provenance` | 26 |
| 19 | `game.utils` | 26 |
| 20 | `game.final_emission_terminal_pipeline` | 24 |
| 21 | `game.narration_plan_bundle` | 23 |
| 22 | `game.scene_actions` | 22 |
| 23 | `game.final_emission_repairs` | 21 |
| 24 | `game.final_emission_strict_social_stack` | 21 |
| 25 | `game.final_emission_validators` | 21 |

### Threshold Summary

| Threshold | Count |
|-----------|------:|
| Files >500 LOC | **141** |
| Files >1,000 LOC | **52** |

All 52 files >1,000 LOC are listed in `BO_hotspot_inventory.md` Category A/B; the full >500 list is in `artifacts/bo_maintenance_audit.json`.

---

## B. Test Maintenance Analysis

### Golden Replay Monolith Decomposition (BM)

| File | LOC | Tests | Helper Deps | Fixtures | Ownership |
|------|----:|------:|-------------|----------|-----------|
| `tests/test_golden_replay.py` | 26 | 1 | 1 (self stub) | 0 | Redirect stub / BI-8 governance anchor |
| `tests/test_golden_replay_protected_bridge.py` | 42 | 1 | 3 | 0 | Protected assertion bridge |
| `tests/test_golden_replay_structural_invariants.py` | 235 | 6 | 2 | 0 | Short full-replay structural integration |
| `tests/test_golden_replay_long_session.py` | 353 | 3 | 4 | 0 | 25-turn stability / resume |
| `tests/test_golden_replay_direct_seam.py` | 105 | 2 | 8 | 0 | Direct-seam gate observation |
| `tests/test_golden_replay_scenario_spine.py` | 126 | 1 | 2 | 0 | Scenario-spine smoke |
| **BM subtotal** | **887** | **14** | — | — | — |

### Golden Replay Neighbors (pre-existing, not BM-split)

| File | LOC | Tests | Helper Deps | Fixtures | Ownership |
|------|----:|------:|-------------|----------|-----------|
| `tests/test_golden_replay_projection.py` | 747 | 25 | 5 | 0 | Protected observation projection contracts |
| `tests/test_golden_replay_fallback_projection.py` | 457 | 14 | 4 | 0 | Fallback owner-bucket projection locks |
| `tests/test_golden_replay_helper_contracts.py` | 179 | 8 | 1 | 0 | Helper/fixture contract smoke |
| **Neighbor subtotal** | **1,383** | **47** | — | — | — |

### Replay Governance / Drift Suite

| File | LOC | Tests | Helper Deps | Key Helpers |
|------|----:|------:|-------------|-------------|
| `tests/test_replay_drift_taxonomy.py` | 434 | 20 | 5 | `replay_drift_taxonomy`, `failure_classifier` |
| `tests/test_replay_drift_risk.py` | 436 | 21 | 3 | `replay_drift_risk`, `failure_dashboard_report` |
| `tests/test_replay_drift_hotspots.py` | 154 | 8 | 5 | `replay_drift_hotspots`, `replay_drift_trends` |
| `tests/test_replay_drift_longitudinal.py` | 165 | 8 | 4 | `replay_drift_longitudinal` |
| `tests/test_replay_drift_trends.py` | 109 | 7 | 5 | `replay_drift_trends` |
| `tests/test_replay_bug_class_recurrence.py` | 205 | 16 | 1 | `replay_bug_recurrence` |
| `tests/test_replay_governance_*.py` (4 files) | 474 | 35 | 2–4 each | `replay_governance_*` contracts |
| **Drift/governance subtotal** | **1,977** | **115** | — | — |

**Golden + replay test total:** ~3,247 LOC, ~176 test cases across 20 modules.

### Final Emission Gate Decomposition (BM)

| File | LOC | Tests | Helper Deps | Fixtures | Ownership |
|------|----:|------:|-------------|----------|-----------|
| `tests/test_final_emission_gate.py` | 19 | 1 | 1 | 0 | Redirect stub |
| `tests/test_final_emission_gate_delegator_regression.py` | 1,370 | 123 | 6 | 0 | BJ delegator / re-export regression locks |
| `tests/test_final_emission_gate_selector_snapshots.py` | 437 | 11 | 3 | 0 | Selector snapshots + sealed-branch order |
| `tests/test_final_emission_gate_orchestration_order.py` | 805 | 18 | 5 | 0 | Behavioral layer order |
| `tests/test_final_emission_gate_n4.py` | 145 | 3 | 1 | 0 | N4 acceptance-quality placement |
| `tests/test_final_emission_gate_diagnostics.py` | 172 | 4 | 3 | 0 | FEM/debug diagnostics |
| **BM gate subtotal** | **2,948** | **160** | — | — | — |

### Final Emission Domain Test Neighbors (selected high-cost)

| File | LOC | Tests | Helper Deps | Ownership Domain |
|------|----:|------:|-------------|------------------|
| `tests/test_final_emission_visibility_fallback.py` | 1,927 | 59 | 1 | Visibility fallback direct owner |
| `tests/test_final_emission_meta.py` | 1,687 | 69 | 4 | FEM projection / lineage owner |
| `tests/test_final_emission_opening_fallback.py` | 1,450 | 56 | 3 | Opening fallback direct owner |
| `tests/test_final_emission_visibility.py` | 1,091 | 57 | 2 | Visibility integration |
| `tests/test_final_emission_sealed_fallback.py` | 516 | 15 | 1 | Sealed fallback direct owner |
| `tests/test_final_emission_boundary_convergence.py` | 507 | 21 | 3 | 1 fixture | Boundary convergence |
| **High-cost FE subtotal** | **7,178** | **277** | — | BK visibility cluster |

### Remaining Test Maintenance Hotspots

| Hotspot | LOC | Tests | Change-Cost Driver |
|---------|----:|------:|-------------------|
| `test_final_emission_gate_delegator_regression.py` | 1,370 | 123 | BJ `inspect.getsource` locks; 42 fan-out deps; runs on every gate submodule edit |
| `test_final_emission_visibility_fallback.py` | 1,927 | 59 | Largest single FE test file; co-moves with 1,976 LOC runtime module |
| `test_final_emission_meta.py` | 1,687 | 69 | FEM hub fan-in 57; replay projection cross-assertions |
| `test_golden_replay_projection.py` | 747 | 25 | Protected observation contract density |
| `test_ownership_registry.py` | 4,518 | — | Governance megamodule; fan-out 56; hosts BN/BD/BM guards |
| `test_prompt_context.py` | 3,597 | — | Unrelated to contraction scope; top-6 LOC file |

---

## C. Replay Maintenance Burden

### Ownership File Inventory

| Category | Files | LOC |
|----------|------:|----:|
| Core helpers (`golden_replay*`, `replay_*`) | 17 | 8,220 |
| Golden replay test owners | 8 | 2,263 |
| Replay drift / governance tests | 14 | 2,465 |
| Runtime projection | 1 | 664 |
| Tooling (`refresh_protected_replay_manifest`) | 1 | 148 |
| **Total replay ownership island** | **41** | **13,096** |

### Dependency Graph Summary

- **Internal edges:** 93 (within replay island)
- **Key external callers into replay helpers:**
  - `tests.helpers.golden_replay` ← 15 external modules (`game.api`, `game.final_emission_meta`, integration tests)
  - `tests.helpers.golden_replay_projection` ← 6 external modules
  - `game.final_emission_replay_projection` ← 3 external modules (meta, telemetry — allowlisted per BD-4)

### Internal Hub Structure

```
golden_replay.py (1995 LOC, fan-out 13)
  ├── golden_replay_fixtures.py (460)
  ├── golden_replay_projection.py (1585, fan-out via meta/telemetry)
  ├── golden_replay_api.py (80)
  └── golden_replay_profiles.py (224)

replay_drift_taxonomy.py (1253 LOC)
  └── replay_drift_risk.py (729) → failure_dashboard_report.py
```

### Is Replay Maintenance Localized?

**Partially yes.**

- BM decomposition successfully split integration tests into **6 focused owner files** (+ stub).
- BD-4/BD-5 routed non-owner replay reads through `golden_replay_projection` / `opening_fallback_evidence` facades (3 allowlisted direct projection import sites).
- Drift/governance tests form a **coherent secondary island** (14 files, 2,465 LOC).

**Remaining drag:**

| File | LOC | Drag Mechanism |
|------|----:|----------------|
| `tests/helpers/golden_replay.py` | 1,995 | Scenario runner + assertion orchestration; 15 external callers; 13 fan-out |
| `tests/helpers/golden_replay_projection.py` | 1,585 | Protected observation projection; couples to FEM meta + lineage |
| `tests/helpers/replay_drift_taxonomy.py` | 1,253 | Classification taxonomy hub for drift suite |
| `tests/test_golden_replay_projection.py` | 747 | Dense projection contract tests |
| `game/final_emission_replay_projection.py` | 664 | Runtime replay projection (Cycle O extract; still cross-domain) |

---

## D. Final Emission Maintenance Burden

### Ownership File Inventory

| Category | Files | LOC |
|----------|------:|----:|
| Runtime `game/final_emission_*.py` modules | 37 | ~24,800 |
| Gate preflight modules (`final_emission_gate_preflight_*`) | 8 | 436 |
| Gate entry + context + runtime delegate | 3 | 555 |
| Final emission test modules | 31 | ~7,400 |
| **Total FE-named surface** | **77** | **32,726** |

### Gate Entry Contraction (BJ / BN outcome)

| Module | LOC | Role |
|--------|----:|------|
| `game/final_emission_gate.py` | 324 | Canonical orchestration owner (was ~8,968 LOC pre-BJ) |
| `game/final_emission_gate_context.py` | 194 | Preflight context assembly (BN-extracted) |
| `game/final_emission_runtime.py` | 37 | BN1 runtime entry delegate |
| 8× `final_emission_gate_preflight_*.py` | 436 | BN3–BN11 preflight slices |

### Dependency Graph Summary

- **Internal FE edges:** 332
- **Top external callers into FE modules:**
  - `tests.test_final_emission_gate` stub → 15 game modules (collection/import graph artifact)
  - `tests.test_final_emission_gate_delegator_regression` → 14 game modules
  - `game.final_emission_gate` → 11 game modules (orchestration imports)
  - `tests.test_final_emission_opening_fallback` → 11 game modules

### Is Final Emission Maintenance Localized?

**At gate entry: yes. Across fallback families: no.**

- BN successfully **localized preflight** into 8 modules with import guards (BN1–BN11 in `test_ownership_registry.py`).
- BM successfully **localized gate test ownership** into 5 focused files.
- BD-6 guard reports **0 compressed-import violations** (2026-06-10 baseline; guards still in place).

**Remaining drag (BK-confirmed, still measured live):**

| Cluster | LOC (runtime + test) | Fan-In / Fan-Out | Drag |
|---------|---------------------:|------------------|------|
| Visibility fallback | 1,976 + 1,927 = 3,903 | 18 / 18 | Bidirectional hub; BK touch cascade 6–9 files |
| FEM meta projection | 2,210 + 1,687 = 3,897 | 57 / 4 | Highest FE hub; owner-bucket seam |
| Opening fallback | ~800 + 1,450 = ~2,250 | — | Co-moves with visibility/sealed |
| Validators | 2,229 + 313 = 2,542 | 21 / 4 | Layer validation density |
| Gate delegator tests | 1,370 | 42 fan-out | Static regression locks |

---

## E. Fan-Out Trend Review (vs Prior BN / BD Findings)

### Gate Contraction — Measured Improvement

| Metric | Pre-Contraction (AN / BD baseline) | Current (BO) | Trend |
|--------|-----------------------------------|-------------|-------|
| `final_emission_gate.py` LOC | ~8,968 (AN) | **324** | ▼ 96% |
| `apply_final_emission_gate` body | ~1,566 lines in-file (AN) | Extracted to layer modules | ▼ orchestration density |
| Gate context | Monolithic pre-BN | **194 LOC + 8 preflight modules** | ▼ localized |
| Runtime gate entry paths | Direct `apply_final_emission_gate` in non-owners | **BN1 delegate** via `final_emission_runtime` | ▼ leakage |
| `final_emission_gate` fan-in | 32 files any-symbol (BD) | **28** unique importers | ▼ slight |
| BD-6 guard violations | 0 (2026-06-10) | Guards present; no new bypass observed | → held |

### Remaining Fan-Out Hubs (post-plateau)

| Hub | Fan-Out | Fan-In | Routing Role |
|-----|--------:|-------:|--------------|
| `tests.test_ownership_registry` | **56** | — | Governance router / guard host |
| `game.api` | **48** | 61 | Primary runtime API router |
| `tests.test_final_emission_gate_delegator_regression` | **42** | — | BJ regression import scanner |
| `game.prompt_context` | **34** | 37 | Prompt assembly router |
| `game.final_emission_visibility_fallback` | **18** | 18 | Fallback selection router (BK H1 target) |
| `tests.helpers.golden_replay` | **13** | 8 | Replay scenario router |

### Remaining Dependency Clusters

1. **Fallback visibility family** — opening + visibility + sealed runtime modules + 3 direct-owner test suites (BK: 6–9 FTPF)
2. **FEM meta / bucket projection** — `final_emission_meta` fan-in 57 (BK: 49); owner-bucket seam across meta/visibility/sealed
3. **Prompt/GM/API spine** — `gm` (153 imports), `storage` (150), `api` (61 fan-in) — unchanged by contraction cycles
4. **Governance/test guard cluster** — `test_ownership_registry` + `emission_smoke_assertions` (69 fan-in)

### Ownership Leakage Still Present

| Leakage | Evidence |
|---------|----------|
| Gate symbol still #3 most-imported module | 125 import statements for `game.final_emission_gate` (compat re-exports + owner suites) |
| FEM meta hub growth | Fan-in 57 vs BK estimate 49 (+8 importers since BK recon) |
| Replay helper external coupling | `golden_replay.py` called from 15 non-replay modules |
| Visibility fallback bidirectional hub | 18 fan-in + 18 fan-out — acts as routing layer per BK |

---

## F. Maintenance Economics Assessment

**Rating scale:** 1 = poor economics (high cost, diffuse ownership) → 10 = strong economics (low cost, clear locality).

| Dimension | Rating | Justification |
|-----------|:------:|---------------|
| **Change Locality** | **6/10** | Gate and test monolith splits (BJ/BN/BM) materially improved locality for those surfaces. 52 files >1K LOC and runtime megamodules (`interaction_context`, `api`) still force wide blast radius on unrelated changes. |
| **Ownership Clarity** | **7/10** | Registry + BN/BD guards provide explicit ownership boundaries. Fallback bucket seam (BK) and triple-layer scaffold split (BE6) remain documented but operationally costly. |
| **Replay Maintenance Cost** | **6/10** | BM test decomposition + BD facades reduced non-owner coupling. Two helper hubs (3,580 LOC combined) and 115 drift/governance tests still create significant maintenance surface. |
| **Final Emission Maintenance Cost** | **5/10** | Gate entry dramatically cheaper (324 LOC vs 8,968). Visibility/opening/sealed cluster (7,178 LOC tests + 4K runtime) dominates remaining FE change cost. Delegator regression file (1,370 LOC, 123 tests) adds static lock overhead. |
| **Test Maintenance Cost** | **5/10** | Monolith splits helped gate/replay integration tests. Top test files remain >1,500 LOC each; `test_ownership_registry` (4,518 LOC) is itself a maintenance hotspot. |
| **Dependency Complexity** | **4/10** | 141 files >500 LOC; top hubs (`storage`, `gm`, `api`, `interaction_context`) unchanged. Fan-out governance module (56) adds meta-complexity. Lower score = higher complexity. |
| **Hotspot Concentration** | **4/10** | Top 10 files = 38,681 LOC (14.4% of repo). Concentration shifted from gate to runtime + fallback + helpers but remains high. Lower score = higher concentration risk. |
| **Overall Maintenance Economics** | **5/10** | Contraction cycles delivered **real, measurable gains** in scoped areas. Repo-wide economics plateaued: megamodules, fallback seams, and helper hubs now dominate. Next gains require targeting measured clusters (BK H1/H2, helper decomposition), not further gate entry contraction. |

---

## Measurement Provenance

- Scan date: 2026-06-17
- Files analyzed: 602 Python modules, 267,869 LOC
- Import graph: AST walk of `game.*` and `tests.*` imports only (stdlib/third-party excluded from fan metrics)
- Prior cycle references: Cycle AN (gate baseline), Cycle BD (import compression closeout 2026-06-10), Cycle BM (test decomposition completion), Cycle BK (fallback recon 2026-06-16)
- Raw data: `artifacts/bo_maintenance_audit.json`
