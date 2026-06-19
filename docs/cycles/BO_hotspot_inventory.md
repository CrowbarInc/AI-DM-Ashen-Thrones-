# BO — Hotspot Inventory

**Date:** 2026-06-17  
**Source:** Static LOC + fan-in/fan-out scan (`artifacts/bo_maintenance_audit.json`)  
**Thresholds:** >500 LOC (141 files), >1,000 LOC (52 files)

**Maintenance risk scale:** Critical / High / Medium / Low  
**Recommendation types:** Immediate target / Medium-term target / Acceptable long-term hotspot

---

## Category A — Immediate Targets

Files with Critical or High maintenance risk: large LOC, high fan-in/out, or confirmed cross-cycle touch cascades.

| File | LOC | Ownership Domain | Fan-In | Fan-Out | Risk | Recommendation |
|------|----:|------------------|-------:|--------:|------|----------------|
| `game/interaction_context.py` | 6,004 | Runtime / interaction | 74 | 8 | **Critical** | Immediate target — largest file in repo; 74 importers; any edit risks wide regression |
| `game/api.py` | 5,534 | Runtime API router | 61 | 48 | **Critical** | Immediate target — dual hub (high fan-in + highest runtime fan-out); routing layer |
| `game/gm.py` | 4,579 | GM orchestration | 60 | 16 | **Critical** | Immediate target — #1 most-imported module (153 import statements) |
| `tests/test_ownership_registry.py` | 4,518 | Governance / guards | 0* | 56 | **Critical** | Immediate target — hosts BN/BD/BM guards; highest test fan-out; split guard domains |
| `game/social_exchange_emission.py` | 3,881 | Strict-social emission | 53 | 12 | **High** | Immediate target — top fan-in runtime module; FE stack dependency |
| `tests/test_prompt_context.py` | 3,597 | Prompt test owner | 0* | 17 | **High** | Immediate target — #6 largest file; prompt router test mirror |
| `game/prompt_context.py` | 3,067 | Prompt assembly | 37 | 34 | **High** | Immediate target — bidirectional hub (fan-in 37, fan-out 34); routing layer |
| `game/final_emission_meta.py` | 2,210 | FEM projection | 57 | 4 | **High** | Immediate target — highest FE fan-in; BK owner-bucket seam anchor |
| `tests/helpers/golden_replay.py` | 1,995 | Replay orchestration | 8 | 13 | **High** | Immediate target — replay maintenance hub; 15 external callers |
| `game/final_emission_visibility_fallback.py` | 1,976 | Visibility fallback | 18 | 18 | **High** | Immediate target — BK touch cascade anchor; bidirectional hub |
| `tests/test_final_emission_visibility_fallback.py` | 1,927 | Visibility fallback tests | 0* | 1 | **High** | Immediate target — largest FE test file; co-moves with runtime (3,903 combined) |
| `tests/test_final_emission_meta.py` | 1,687 | FEM projection tests | 0* | 13 | **High** | Immediate target — 69 tests; couples to replay projection helpers |
| `tests/helpers/golden_replay_projection.py` | 1,585 | Replay projection facade | 6** | — | **High** | Immediate target — BD-4 facade; 1,585 LOC still dense |
| `tests/test_final_emission_gate_delegator_regression.py` | 1,370 | BJ delegator locks | 0* | 42 | **High** | Immediate target — 123 static tests; 42 fan-out; edit tax on every gate submodule |
| `tests/helpers/replay_drift_taxonomy.py` | 1,253 | Drift classification | 1** | — | **High** | Immediate target — taxonomy hub for 115 drift/governance tests |
| `game/final_emission_validators.py` | 2,229 | Gate validators | 21 | 4 | **High** | Immediate target — 2,229 LOC validator density; 21 importers |
| `tests/test_final_emission_opening_fallback.py` | 1,450 | Opening fallback tests | 0* | 20 | **High** | Immediate target — BK visibility cluster; 56 tests |
| `tests/test_social_exchange_emission.py` | 2,295 | Strict-social tests | 0* | 15 | **High** | Immediate target — mirrors 3,881 LOC runtime owner |
| `game/narrative_planning.py` | 3,197 | Narrative planning | — | — | **High** | Immediate target — top-8 LOC; planning spine |
| `game/leads.py` | 3,196 | Lead engine | 43 | — | **High** | Immediate target — fan-in 43; cross-cutting domain |

\* Test modules show fan-in 0 because importers are typically pytest collection, not Python imports.  
\*\* External fan-in to helper modules from outside replay island.

---

## Category B — Medium-Term Targets

Large or moderately coupled files that are owned and stable but still elevate change cost.

| File | LOC | Ownership Domain | Fan-In | Fan-Out | Risk | Recommendation |
|------|----:|------------------|-------:|--------:|------|----------------|
| `game/gm_retry.py` | 2,854 | Retry / fast fallback | 15 | 15 | Medium | Medium-term — BK fast-fallback provenance cluster |
| `game/social.py` | 2,828 | Social runtime | 37 | 9 | Medium | Medium-term — moderate fan-in hub |
| `game/planner_ctir_projection.py` | 2,276 | CTIR projection | 3 | 5 | Medium | Medium-term — large but lower coupling |
| `game/clues.py` | 2,075 | Clue engine | 17 | 5 | Medium | Medium-term — domain owner; contained |
| `tests/test_turn_pipeline_shared.py` | 1,981 | Pipeline smoke | 0* | 6 | Medium | Medium-term — downstream smoke hub (69 fan-in to smoke facade) |
| `game/narrative_authenticity.py` | 1,861 | Narrative quality | — | — | Medium | Medium-term — FE layer dependency |
| `tests/test_prompt_and_guard.py` | 1,856 | Prompt guard tests | 0* | — | Medium | Medium-term — cross-cutting smoke |
| `game/intent_parser.py` | 1,796 | Intent parsing | — | — | Medium | Medium-term — upstream routing |
| `tests/test_synthetic_smoke.py` | 1,705 | Synthetic smoke | 0* | — | Medium | Medium-term — broad smoke surface |
| `game/interaction_continuity.py` | 1,654 | Continuity | — | — | Medium | Medium-term — FE layer owner |
| `game/response_policy_enforcement.py` | 1,636 | Policy enforcement | — | — | Medium | Medium-term — policy spine |
| `tests/test_narration_transcript_regressions.py` | 1,627 | Transcript regressions | 0* | 14 | Medium | Medium-term — transcript harness; 14 fan-out |
| `tests/helpers/failure_dashboard_report.py` | 1,597 | Failure reporting | — | — | Medium | Medium-term — replay drift report bridge |
| `game/output_sanitizer.py` | 1,571 | Sanitizer owner | — | — | Medium | Medium-term — BE6 legality owner; stable |
| `tests/test_run_scenario_spine_validation.py` | 1,373 | Scenario spine | 0* | — | Medium | Medium-term — replay-adjacent validation |
| `game/narration_visibility.py` | 1,388 | Narration visibility | — | — | Medium | Medium-term — FE visibility dependency |
| `game/final_emission_repairs.py` | 1,277 | FE repairs | 21 | — | Medium | Medium-term — 21 importers; bounded scope |
| `tests/helpers/replay_drift_risk.py` | 729 | Drift risk scoring | 1** | — | Medium | Medium-term — couples taxonomy + dashboard |
| `tests/test_golden_replay_projection.py` | 747 | Projection contracts | 0* | 5 | Medium | Medium-term — 25 dense projection tests |
| `tests/test_final_emission_gate_orchestration_order.py` | 805 | Gate order tests | 0* | 21 | Medium | Medium-term — 18 behavioral order tests |
| `tests/test_final_emission_visibility.py` | 1,091 | Visibility integration | 0* | 10 | Medium | Medium-term — BK cluster member |
| `game/final_emission_gate.py` | 324 | Gate orchestration | 28 | — | Medium | Medium-term — **already contracted**; monitor regrowth |
| `game/final_emission_replay_projection.py` | 664 | Runtime replay projection | 3 | 2 | Medium | Medium-term — Cycle O extract; cross-domain |

---

## Category C — Acceptable Long-Term Hotspots

Files that are large by necessity, tooling, or stable ownership with acceptable economics given guards and decomposition already applied.

| File | LOC | Ownership Domain | Fan-In | Fan-Out | Risk | Recommendation |
|------|----:|------------------|-------:|--------:|------|----------------|
| `game/final_emission_gate_context.py` | 194 | Gate preflight context | 2 | 8 | Low | Acceptable — BN-contracted; BN11 allowlist guarded |
| `game/final_emission_runtime.py` | 37 | Runtime gate delegate | 1 | 1 | Low | Acceptable — BN1 narrow entry seam |
| 8× `game/final_emission_gate_preflight_*.py` | 436 | Preflight slices | 1 each | 1–3 | Low | Acceptable — BN3–BN11 localized preflight |
| `tests/test_golden_replay.py` | 26 | Replay stub | — | 1 | Low | Acceptable — BM redirect stub |
| `tests/test_final_emission_gate.py` | 19 | Gate stub | — | 15*** | Low | Acceptable — BM redirect stub |
| `tests/test_golden_replay_structural_invariants.py` | 235 | Replay invariants | 0* | 2 | Low | Acceptable — focused BM owner |
| `tests/test_golden_replay_long_session.py` | 353 | Long session | 0* | 4 | Low | Acceptable — shardable slow path (BM recommendation) |
| `tests/test_golden_replay_direct_seam.py` | 105 | Direct seam | 0* | 8 | Low | Acceptable — focused seam owner |
| `tests/test_golden_replay_scenario_spine.py` | 126 | Scenario spine | 0* | 2 | Low | Acceptable — focused smoke |
| `tests/test_golden_replay_protected_bridge.py` | 42 | Protected bridge | 0* | 3 | Low | Acceptable — diagnostic only |
| `tests/test_final_emission_gate_n4.py` | 145 | N4 placement | 0* | 1 | Low | Acceptable — focused owner |
| `tests/test_final_emission_gate_diagnostics.py` | 172 | Diagnostics | 0* | 6 | Low | Acceptable — focused owner |
| `tests/test_final_emission_gate_selector_snapshots.py` | 437 | Selector snapshots | 0* | 14 | Low | Acceptable — bounded snapshot owner |
| `tests/helpers/emission_smoke_assertions.py` | ~400 | Smoke facade | 69 | — | Low | Acceptable — intentional BD-2/BD-3 facade hub |
| `tools/architecture_audit.py` | 2,023 | Audit tooling | 0 | 0 | Low | Acceptable — offline governance tool |
| `tools/test_audit.py` | 1,664 | Test audit tooling | 0 | — | Low | Acceptable — inventory generator |
| `game/storage.py` | 1,222 | Persistence | 112 | — | Low | Acceptable — infrastructure hub; high fan-in expected |
| `game/defaults.py` | — | Defaults | 94 | — | Low | Acceptable — config hub |
| `tests/replay_governance_*.py` (4 contracts) | 453 | Governance contracts | — | — | Low | Acceptable — stable contract surfaces |
| `tests/test_replay_governance_*.py` (4 files) | 474 | Governance tests | — | — | Low | Acceptable — small, focused |

\* Test fan-in not captured by import graph.  
\*\* Helper external fan-in.  
\*\*\* Stub imports game modules for collection-side re-export checks.

---

## Summary Counts

| Category | Files Listed | Combined LOC (listed) | Primary Risk Pattern |
|----------|-------------:|----------------------:|----------------------|
| A — Immediate | 20 | ~52,000 | Megamodules + FE fallback cluster + replay/governance hubs |
| B — Medium-term | 23 | ~38,000 | Large domain owners + dense test mirrors |
| C — Acceptable | 20+ | ~6,500 (gate/replay contracted core) | Guarded, decomposed, or infrastructure |

## Post-Contraction Observations

1. **Gate surfaces moved from Category A to Category C** — `final_emission_gate.py` (324 LOC) and BM test stubs are no longer monolith hotspots.
2. **Hotspot center of gravity shifted** to `interaction_context`, `api`, `gm`, fallback visibility cluster, and `golden_replay` helpers.
3. **Test hotspots now dominate** — 8 of top 20 immediate targets are test modules (>1,370 LOC each).
4. **141 files >500 LOC** remain — contraction cycles addressed scoped surfaces, not repo-wide size distribution.
