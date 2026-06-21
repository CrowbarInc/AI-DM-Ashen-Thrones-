# BV4A — Passive Scene Pressure Reduction Plan

**Date:** 2026-06-21  
**Goal:** Reduce `sealed_passive_scene_pressure_fallback` **incidence** on observe route — not relocate ownership to another fallback family.  
**Baseline (BV3F):** 10 PSP events; observe route rate **47.83%**; overall fallback incidence **11.58%**.  
**Constraint:** Analysis-only cycle — this document is the implementation plan; no production changes in BV4A discovery.

---

## Executive strategy

Three-phase plan aligned with [BV4A_elimination_candidates.md](BV4A_elimination_candidates.md):

1. **Phase 1 — Highest ROI upstream satisfiers:** Enforce concrete interaction contract + deterministic beat injection repair (EC-4A-01, EC-4A-02).
2. **Phase 2 — Contract enforcement:** Retry policy, post-repair accept path, due-check calibration (EC-4A-03, EC-4A-04, EC-4A-05).
3. **Phase 3 — Fallback retirement candidates:** Retire generic sealed template after incidence collapse (EC-4A-07).

Phase 1 mirrors BV3's proven path: **upstream satisfier first**, terminal hard replace last resort.

---

## Phase 1 — Highest ROI upstream satisfiers

**Duration estimate:** 1–2 cycles  
**Expected movement:** PSP 10 → **0–2**; observe route **−35 to −43 pp**

### Work items

| ID | Work | Module(s) | Acceptance criteria |
|---|---|---|---|
| P1-1 | Passive-scene concrete-beat upstream contract | `gm.py` payload validator, `upstream_response_repairs`, terminal pre-check seam | 0 observe turns with `passive_scene_pressure_missing_concrete_beat` when contract satisfied |
| P1-2 | Contract assertion before non-strict stack reject | `final_emission_non_strict_stack`, `final_emission_terminal_pipeline` | Rejection reason absent when upstream passes concrete-beat check |
| P1-3 | Deterministic beat injection repair (observe) | New module or extend `final_emission_passive_scene_pressure.py` | `passive_scene_upstream_repair_applied=true` on eligible passive observe turns |
| P1-4 | FEM instrumentation stamps | `final_emission_meta` | `passive_scene_pressure_upstream_repair_mode`, attempt/applied/eligible flags |
| P1-5 | Protected replay fixture | `tests/test_bv4a_passive_scene_upstream_repair.py` (future) | Passive observe + atmospheric upstream → repair applied, no sealed replace |
| P1-6 | Measurement ownership packaging | EC-4A-06 parallel | Selection owner visibility on PSP path |

### P1-1 contract specification (draft)

For `route_kind=observe` when `_passive_scene_pressure_due_for_fallback` would be true:

1. Upstream GM output MUST pass `_reply_already_has_concrete_interaction(text)` **or** carry `passive_scene_upstream_repair_applied=true`.
2. Concrete beat MUST reference a visible-scene entity when guard/watch facts present (SAT-03).
3. Failure → upstream repair (P1-3) **before** non-strict stack append of `passive_scene_pressure_missing_concrete_beat`.
4. Terminal sealed passive-scene branch MUST NOT select when (1) or repair applied.

**Mirror reference:** BV3A/BV3E referential-clarity contract in `final_emission_referential_clarity.py`.

### Phase 1 verification gate

```text
pytest tests/test_final_emission_passive_scene_pressure.py
pytest tests/test_bv3e_eligibility_expansion.py  # BV3E regression
pytest tests/test_final_emission_non_strict_stack.py
python tools/bv4a_passive_scene_inventory.py
python tools/bv3f_reduction_metrics.py  # new BV4A-P1 snapshot tag
```

---

## Phase 2 — Contract enforcement

**Duration estimate:** 1–2 cycles  
**Expected movement:** PSP residual → **0–1**; observe route **<10%**

### Work items

| ID | Work | Module(s) | Depends on |
|---|---|---|---|
| P2-1 | GM retry for missing concrete beat | `response_policy_enforcement`, retry strategy registry | P1-1 |
| P2-2 | Post-BV3E-repair accept path | `final_emission_terminal_pipeline`, ordering audit | P1 complete |
| P2-3 | Pressure due-check refinement | `final_emission_passive_scene_pressure._passive_scene_pressure_due_for_fallback` | Corpus evidence from multi-turn spine |
| P2-4 | Replay refresh stub alignment | `tools/bv3f_replay_corpus_refresh.py` | Stub GPT should emit contract-passing OR contract-failing shapes intentionally |
| P2-5 | BV4A metrics tooling | `tools/bv4a_passive_scene_inventory.py`, reduction metrics extension | P1 instrumentation |

### Phase 2 verification gate

```text
python tools/run_scenario_spine_validation.py --branch branch_social_inquiry
pytest tests/test_golden_replay_*.py -q
python tools/bv1b_fallback_incidence_validation.py
```

---

## Phase 3 — Fallback retirement candidates

**Duration estimate:** 1 cycle (only after Phase 1 stable)  
**Prerequisite:** PSP incidence **≤1** on two consecutive replay snapshots

### Work items

| ID | Work | Risk | Acceptance |
|---|---|---|---|
| P3-1 | Gate generic `passive_scene_pressure_generic` template behind contract proof | High | 0 PSP on protected corpus |
| P3-2 | Consolidate passive-scene candidate pool with upstream satisfier | Medium | Code shrink in sealed fallback |
| P3-3 | Remove redundant non-strict reject when upstream contract satisfied | High | No observe sealed replace on contract-pass turns |

**Do not start Phase 3 until:** BV4A-P1 snapshot shows **≥80%** PSP reduction vs BV3F baseline.

---

## Reduction vs relocation guards

| Signal | Relocation (fail) | Reduction (pass) |
|---|---|---|
| PSP event count | Stable at 10 | **Decreases ≥8** |
| RC hard replacement | Increases compensating | **Stable at ≤1** |
| Observe route rate | Unchanged with owner relabel | **Decreases ≥10 pp** |
| Upstream repair stamps | 0 on replay FEM | **`passive_scene_upstream_repair_applied > 0`** |
| Player-facing replay diff | None required | None required |

**Primary discriminator:** `sealed_passive_scene_pressure_fallback` count must decrease alongside **`passive_scene_upstream_repair_applied`** increase — same pattern BV3F used for BV3E.

---

## Dependency on BV3 artifacts

| BV3 deliverable | BV4A reuse |
|---|---|
| BV3E upstream repair pattern | Template for P1-3 beat injection |
| BV3D measurement scope | Corpus filter for BV4A metrics |
| BV3F replay refresh | Baseline corpus; re-run after Phase 1 |
| BV3 Phase 1 ownership fixes | EC-4A-06 packaging |

---

## Evidence

| Source | Role |
|---|---|
| [BV4A_elimination_candidates.md](BV4A_elimination_candidates.md) | Candidate specs |
| [BV4A_verification_projection.md](BV4A_verification_projection.md) | Phase 1 metrics estimate |
| [BV3_fallback_reduction_plan.md](BV3_fallback_reduction_plan.md) | Structural template |
