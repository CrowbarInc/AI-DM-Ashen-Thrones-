# CB7 Ownership Drift Watch

**Block:** CB7 — Ownership Drift Watch Refresh  
**Type:** Read-only audit (no runtime behavior changes)  
**Baselines:** BV1 (`artifacts/bv1_maintenance_matrix_data.json`, `docs/audits/BV1_maintenance_cost_matrix.md`), CB discovery (`docs/audits/CB_feature_boundary_readiness_discovery.md`), CB1–CB6 program blocks  
**Analysis tool:** [`tools/cb7_ownership_drift_analysis.py`](../../tools/cb7_ownership_drift_analysis.py)  
**Machine output:** [`artifacts/cb7_analysis.json`](../../artifacts/cb7_analysis.json)  
**Generated:** 2026-06-23

---

## Executive summary

| Signal | Verdict |
|---|---|
| **Ownership drift** | **Detected** — hub leadership shifted (meta ↓, text_formatting ↑, visibility_fallback ↑); 125 heuristic dual-domain `game/` files; registry stable at 17 responsibility groups |
| **Coupling drift** | **Detected** — replay governance (+22 FI vs CB), prompt/CTIR (+52 FI vs CB), visibility_fallback (+15 FI vs BV1 ecosystem); final-emission full-repo AST **stable vs CB** |
| **Governance drift** | **+19 test files** — missing from committed `tests/test_inventory_governance.json`; **process gap**, not ownership-registry corruption |
| **Feature readiness** | **Stable with selective improvement** — safe-domain pilots (CB2/CB5) validated; prohibited domains unchanged per CB6 frequency evidence |

**Recommendation:** **Continue maintenance** on governance inventory regen and longitudinal fallback snapshots; **resume normal feature development in safe domains only** (CB1 registry). Prohibited and caution workflows remain mandatory elsewhere.

---

# Ownership Inventory

Inventory rebuilt for eight CB7 watch domains. File counts use live repository paths; ownership assignments use `tests/test_ownership_registry.py` `RESPONSIBILITY_REGISTRY` (17 canonical groups) plus `docs/architecture_ownership_ledger.md` runtime owners.

## Summary table

| Domain | Files (prod / test / tool) | Registry direct owners | Lexical ownership refs | Unresolved / gap notes |
|---|---:|---|---:|---|
| Final emission | 52 / 0 / 0 | 5 groups (`gate_orchestration`, `meta_projection`, `visibility_semantics`, `validators`, `repairs`) | 622 | `final_emission_text_formatting` is de-facto hub (FI 52) without a dedicated registry group — covered under text/BV13 facade governance |
| Fallback | 9 / 0 / 0 | 2 groups (`visibility_semantics`, `output_sanitizer_final_string_cleanup`) + opening/sealed owners in gate suites | 115 | BV1 counted 43 modules (tests/helpers in area); narrow prod slice is 9 modules |
| Speaker | 3 / 0 / 0 | 0 dedicated groups; speaker legality adjacent to `social_emission_legality_surface` | 6 | Runtime owners: `speaker_contract_enforcement`, `emitted_speaker_signature`, `post_emission_speaker_adoption` per ledger |
| Response policy | 3 / 0 / 0 | 1 group (`response_policy_contract_materialization`); enforcement via `test_response_policy_enforcement_mutation.py` | 3 | Ledger splits contracts vs enforcement (both drift-watch) |
| Replay governance | 1 / 42 / 2 | 1 group (`transcript_regression`); golden/protected suites are neighbors | 781 | Largest lexical concentration; `replay_fem_read_smoke` FI 60 (BV12 domain facade) |
| API orchestration | 6 / 0 / 1 | 0 dedicated groups; `turn_pipeline_shared` is downstream neighbor | 10 | `game.api` FI 65, `game.gm` FI 62 — unchanged concentration |
| Prompt / CTIR | 20 / 0 / 0 | 2 groups (`planner_prompt_bundle_shipped_contract`, `prompt_context_contract_assembly`) | 3 | CTIR boundary tests listed in ledger; `prompt_context` FI 38 |
| State / storage | 8 / 0 / 0 | 2 groups (`engine_truth_persistence_mechanics`, `social_engine_state_rules`) | 1 | `storage` FI 125, `defaults` FI 105 — stable hubs |

## Dual-owned files (heuristic)

AST/header heuristic tags **125** `game/*.py` files with multiple domain keywords (expected at orchestration seams). High-risk examples:

| File | Domains tagged | Interpretation |
|---|---|---|
| `game/final_emission_terminal_pipeline` | final_emission, fallback, speaker, prompt_ctir | Convergence hub — governed, not unresolved |
| `game/gm.py` | fallback, speaker, api_orchestration, prompt_ctir, state_storage | Orchestration re-export surface |
| `game/response_policy_contracts.py` | final_emission, fallback, response_policy, prompt_ctir, state_storage | Contract read hub |
| `game/final_emission_visibility_fallback` | final_emission, fallback, state_storage | Two-way fallback hub (FI 32 ecosystem / 32 narrow) |

**14** `game/` files have **no** domain keyword match (e.g. `game/combat.py`, `game/content_lint.py`) — correctly outside prohibited watch surfaces.

## Unresolved ownership

| Gap | Severity | Notes |
|---|---|---|
| Governance JSON stale (+19 tests) | Medium | Registry paths for existing groups still valid; new suites not enrolled in `files[]` |
| `final_emission_text_formatting` hub FI 52 | Low | BV13 intentional authority; compat barrel governance caps FI |
| Speaker runtime owners without registry group | Low | By design — speaker prohibited domain uses ledger + BX/BT suites |
| Heuristic dual-tags on seam modules | Informational | Not duplicate ownership claims in `RESPONSIBILITY_REGISTRY` |

---

# Coupling Comparison

Two measurement lenses:

1. **Full-repo AST** (CB discovery methodology) — all `game/`, `tests/`, `tools/`, `scripts/` imports  
2. **BU final-emission ecosystem** (`scripts/bu_final_emission_coupling_discovery.py`) — 236 governed modules, comparable to BV1 matrix key modules

## Domain fan-in / fan-out (full-repo AST)

| Domain | Current FI | Current FO | Δ FI vs BV1 | Δ FO vs BV1 | Δ FI vs CB | Δ FO vs CB |
|---|---:|---:|---:|---:|---:|---:|
| Final emission | **527** | **285** | +84 | +67 | **0** | **0** |
| Fallback (narrow) | **116** | **66** | +13 | −127 | +13 | −127 |
| Speaker | **29** | **16** | −51 | −109 | **0** | **0** |
| Response policy | **26** | **13** | −3 | −5 | −9 | −9 |
| Replay governance | **222** | **155** | +136 | +75 | **+22** | +5 |
| API orchestration | **156** | **102** | 0 | +1 | **0** | +1 |
| Prompt / CTIR | **236** | **94** | +52 | +21 | **+52** | +21 |
| State / storage | **284** | **16** | **0** | **0** | **0** | **0** |

*BV1 area totals mixed test modules differently (e.g. fallback area 43 modules incl. tests → FI 103). Narrow fallback row above is prod-only slice; BV1 comparable area FI was 103.*

### Interpretation

- **Stable vs CB discovery:** final emission, speaker, state/storage, API orchestration — **no material full-repo drift since CB baseline (2026-06-23)**.
- **Drift vs BV1:** replay governance and prompt/CTIR grew with **new test suites and narration modules**; final-emission **internal** hub ranks changed (see ecosystem table below).
- **Fallback:** visibility_fallback FI **doubled** in ecosystem scan (+15 vs BV1); narrow-pattern FO dropped (import routing consolidated).

## Key module deltas (BU ecosystem — BV1 → CB7)

| Module | BV1 FI | Current FI | Δ FI | BV1 FO | Current FO | Δ FO |
|---|---:|---:|---:|---:|---:|---:|
| `game.final_emission_meta` | 61 | **24** | **−37** | 6 | 8 | +2 |
| `game.final_emission_visibility_fallback` | 17 | **32** | **+15** | 17 | 20 | +3 |
| `game.final_emission_gate` | 28 | **34** | +6 | 7 | 9 | +2 |
| `game.final_emission_terminal_pipeline` | 26 | **12** | **−14** | 13 | 15 | +2 |
| `tests.helpers.emission_smoke_assertions` | 70 | **15** | **−55** | 5 | 5 | 0 |
| `game.final_emission_text_formatting` | — | **52** | new top hub | — | 0 | BV13 authority |
| `tests.helpers.replay_fem_read_smoke` | — | **60** | BV12 facade | — | 1 | domain routing |
| `game.speaker_contract_enforcement` | 15 | **17** | +2 | 4 | 7 | +3 |
| `game.final_emission_replay_projection` | 15 | **15** | 0 | 4 | 5 | +1 |

**Coupling verdict:** Concentration **redistributed**, not eliminated — BV2/BV7/BV10/BV12/BV13 governance succeeded on meta and smoke monolith, but **visibility fallback**, **text formatting**, and **replay FEM read facade** absorbed inbound pressure.

---

# Governance Drift Analysis

## CB5 finding confirmed

```text
py tools/test_audit.py --check
→ Inventory drift: +19 test files added, 0 removed
```

## Newly added files (not in committed governance JSON)

| Cluster | Files |
|---|---|
| Protected replay closeout (BW/BZ) | `test_bw_protected_replay_trend_window_closeout.py`, `test_bz_protected_replay_trend_window_2_closeout.py` |
| Golden replay structural suite | `test_golden_replay_direct_seam.py`, `test_golden_replay_long_session.py`, `test_golden_replay_protected_bridge.py`, `test_golden_replay_scenario_spine.py`, `test_golden_replay_structural_invariants.py` |
| Fallback portfolio / economics | `test_fallback_incidence_anomalies.py`, `test_fallback_maintenance_economics.py`, `test_fallback_portfolio_benefit.py`, `test_fallback_recurrence.py`, `test_fallback_remediation_effectiveness.py`, `test_fallback_remediation_queue.py`, `test_fallback_risk_scoring.py`, `test_fallback_roi.py` |
| Corrective attribution (CA) | `test_corrective_fix_absence_report.py`, `test_corrective_fix_availability_report.py`, `test_corrective_prevention_effectiveness.py`, `test_embedded_corrective_attribution.py` |

## Root causes

| Cause | Evidence |
|---|---|
| **Process: inventory regen decoupled from feature landings** | CB5 pilot explicitly did not regen governance JSON; same +19 set still present at CB7 |
| **Not missing registry logic** | `tests/test_ownership_registry.py` passes; 17 `_REQUIRED_GROUP_IDS` unchanged |
| **Not stale inventory entries removed** | 0 files removed — drift is **additive only** |
| **Not ownership assignment conflicts** | No duplicate `direct_owner` claims in registry |
| **Replay/governance test expansion** | BW/BZ/CB6 era suites added without `py tools/test_audit.py` commit |

## Remediation (out of CB7 scope — maintenance task)

1. Run `py tools/test_audit.py` and commit updated `tests/test_inventory_governance.json` in a **dedicated inventory-only PR** (per CB5/CB6 recommendation).
2. Enroll new golden-replay files as **neighbors** under existing replay/transcript groups — no new prohibited-domain owners required.

---

# Ownership Gaps

| ID | Gap | Owner today | Risk if unaddressed |
|---|---|---|---|
| G1 | +19 governance `files[]` rows missing | `tools/test_audit.py` workflow | CI `--check` noise; author triage friction |
| G2 | `final_emission_text_formatting` high FI without registry group | BV13C compat caps + facade tests | Regrowth into `final_emission_text` barrel |
| G3 | Longitudinal fallback snapshots (CB6) | 2 history rows | Cannot prove incidence trend from CB7 alone |
| G4 | Speaker mismatch runtime proxy | Protected scenarios only | Low runtime rate does not close acceptance risk (CB6) |
| G5 | Prompt/CTIR FI growth (+52 vs BV1) | Ledger drift-watch | Silent semantic shifts at prompt boundary |

---

# Risk Assessment

| Domain | Classification | Drift posture | Feature work |
|---|---|---|---|
| Content lint / evaluators / UI / combat / model config | **Safe** | Stable | **Resume normal development** |
| World, state, prompt, social, API, telemetry | **Caution** | Prompt FI ↑; state stable | Caution workflow (CB3) |
| Final emission, fallback, speaker, policy, replay | **Prohibited** | Hub redistribution; visibility ↑ | **Block** — audit approval only |

### Overall risk level: **Medium**

- Runtime emit paths show **no CB7 code changes** and **no new monolith**.
- **Governance inventory lag** is the highest actionable risk (process, not architecture).
- **Coupling drift** is **localized** to governed facades (replay FEM read, text formatting, visibility fallback) — consistent with BV10–BV16 program intent.

---

## Validation

| Check | Result |
|---|---|
| No modifications to `final_emission*`, `fallback*`, `speaker*`, `response_policy*`, `replay*`, `protected_replay*` | **PASS** |
| Read-only measurements only | **PASS** |
| BU coupling CSV regenerated | **PASS** — `docs/audits/BU_import_fan_in_fan_out.csv` |
| Governance drift reproduced | **PASS** — +19 files |

### Commands run

```text
py scripts/bu_final_emission_coupling_discovery.py
py tools/test_audit.py --check
py tools/cb7_ownership_drift_analysis.py
```

---

## Cursor Feedback

| Item | Finding |
|---|---|
| Ownership drift | **Detected** — meta/smoke ↓; text_formatting/visibility_fallback/replay facade ↑ |
| Coupling drift | **Detected** — replay +22 FI, prompt +52 FI vs CB; ecosystem hubs redistributed vs BV1 |
| Governance inventory root cause | **Process gap** — 19 new test files never regenned into governance JSON post BW/BZ/CA/fallback portfolio |
| Readiness trend | **Stable** — safe pilots pass; prohibited unchanged |
| Recommendation | **Continue maintenance** (inventory regen, fallback longitudinal snapshots); **resume normal feature development in safe domains only** |
