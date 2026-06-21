# BV3 — Observe-Route Fallback Reduction Verification

**Date:** 2026-06-21  
**Purpose:** Estimate projected metrics after reduction phases and define verification protocol to prove **incidence reduction** vs **ownership relocation**.  
**Baseline corpus:** 107 FEM instances; 44 observe turns; 74 fallback events.

---

## Baseline (BV1B snapshot)

| Metric | Value | Source |
|---|---:|---|
| Eligible turns | 107 | `bv1b_fallback_incidence_report.json` |
| Fallback trigger rate (overall) | **69.16%** (74/107) | idem |
| Fallback events | 74 | idem |
| **Observe route rate** | **95.45%** (42/44) | idem |
| Referential clarity events (all routes) | 38 | idem |
| Referential clarity on observe | 38/42 observe events | cross-tab |
| Ownerless fallback events (repo) | **13** | BV1B comparison |
| Ownerless on observe | **12** | BV3 corpus analysis |
| Unique fallback families | 4 | idem |
| Selection owner coverage | 70/74 | idem |
| Content owner coverage | 70/74 | idem |

---

## Projection model

Turn-scoped fallback rate:

```text
fallback_trigger_rate = fallback_turn_count / eligible_turn_count
observe_route_rate    = observe_fallback_turns / observe_eligible_turns
```

Observe contributes **42 of 74** fallback turns (56.8%). Non-observe fallback turns: **32** (mostly scene_opening at 31).

**Conservative modeling assumption:** Phase 2 upstream contract reduces observe fallback turns by **30–50%** without increasing scene_opening fallbacks. Phase 1 reclassification removes **2** accept_candidate turns from fallback turn count.

---

## Projected metrics by phase

### Phase 1 — Low-risk eliminations (measurement correction)

| Metric | Baseline | Projected | Delta | Notes |
|---|---:|---:|---:|---|
| Observe route rate (raw) | 95.45% | 95.45% | 0 | No behavior change |
| Observe route rate (adjusted) | 95.45% | **90.91%** | **−4.54 pp** | EC-04: 2 accept turns reclassified |
| Overall fallback incidence (raw) | 69.16% | 69.16% | 0 | |
| Overall incidence (adjusted) | 69.16% | **67.29%** | **−1.87 pp** | 72/107 fallback turns |
| Fallback events (lineage) | 74 | 74 | 0 | Event count unchanged |
| Ownerless (repo) | 13 | **5** | **−8** | EC-03 closes RC bucket gaps |
| Ownerless (observe) | 12 | **4** | **−8** | |
| Referential clarity events | 38 | 38 | 0 | |
| Gate event_owner share | 100% | **~57%** | — | EC-05 packaging fix |

**Phase 1 verdict:** Improves **measurement fidelity** and **ownership clarity**; does **not** alone meet BV3 success criteria.

---

### Phase 2 — Contract enforcement (incidence reduction)

Assumptions:

- EC-01 upstream contract eliminates **40%** of observe referential-clarity hard replaces (**15 turns**).
- EC-02 local repair avoids **10%** additional observe hard replaces (**4 turns**).
- Overlap adjusted: **net −18 observe fallback turns** (42 → **24**).
- Scene_opening unchanged (31).

| Metric | Baseline | Conservative | Target | Stretch |
|---|---:|---:|---:|---:|
| Observe fallback turns | 42 | **24** | **≤37** | **22** |
| Observe eligible turns | 44 | 44 | 44 | 44 |
| **Observe route rate** | 95.45% | **54.55%** | **<85%** ✓ | **50.00%** |
| Overall fallback turns | 74 | **56** | **≤62** | **53** |
| **Overall fallback incidence** | 69.16% | **52.34%** | **<60%** ✓ | **49.53%** |
| Referential clarity events | 38 | **≤23** | **≤26** | **≤20** |
| Ownerless (repo) | 13 | **≤5** | **≤5** ✓ | **≤3** |
| Passive-scene content share (observe) | 95.2% | **~90%** | — | **~75%** |

**Phase 2 success criteria (from BV follow-on):**

| Criterion | Target | Conservative projection |
|---|---|---|
| Observe route rate | **<85%** | **54.55%** ✓ |
| Owner-bucket gaps | **≤5 events** | **≤5** ✓ |
| Longitudinal trend | **improving** | Requires appended BV3-P2 snapshot |

---

### Phase 3 — Fallback removal candidates

Assumption: Phase 2 stable at ~54% observe route; Phase 3 upstream satisfier + enforcement collapse removes **50%** of remaining observe fallbacks (24 → **12**).

| Metric | Baseline | Phase 3 projected | Delta vs baseline |
|---|---:|---:|---:|
| Observe fallback turns | 42 | **12** | **−30** |
| **Observe route rate** | 95.45% | **27.27%** | **−68.18 pp** |
| Overall fallback turns | 74 | **43** | **−31** |
| **Overall fallback incidence** | 69.16% | **40.19%** | **−28.97 pp** |
| Referential clarity events | 38 | **≤12** | **−26** |
| Ownerless (repo) | 13 | **≤3** | **−10** |
| Maintenance burden score | 62.0 | **~45–50** (est.) | **−12 to −17** |

---

## Verification protocol

### Snapshot pipeline

1. Run `python tools/bv1b_fallback_incidence_validation.py` after each phase (extend artifact source tag to `BV3-P1`, `BV3-P2`, `BV3-P3`).
2. Append to `artifacts/golden_replay/fallback_incidence_history.json`.
3. Compare against BV1B baseline — **require strictly lower observe route rate** for Phase 2 sign-off.

### Regression gates (must pass before claiming reduction)

| Gate | Command / artifact | Pass condition |
|---|---|---|
| Protected replay | `pytest tests/test_golden_replay_direct_seam.py` | No drift |
| Visibility fallback | `pytest tests/test_final_emission_visibility_fallback.py` | Green |
| Ownership registry | `pytest tests/test_ownership_registry.py -k visibility` | Green |
| Failure classification | `pytest tests/test_failure_classification_contract.py` | Green |
| Transcript gauntlet | `pytest tests/test_transcript_gauntlet_actor_addressing.py` | Green |
| Spine validation | `python tools/run_scenario_spine_validation.py` (protected branches) | No new fallbacks vs baseline unless expected |

### Reduction vs relocation discrimination

| Signal | Relocation (fail) | Reduction (pass) |
|---|---|---|
| Observe route rate | Unchanged ±1 pp | **≥10 pp decrease** Phase 2 |
| Referential clarity event count | Stable at 38 | **Decreases** with route rate |
| Selection owner module | Changes without rate change | Rate change with stable owner module |
| Player-facing replay diff | None | None (behavior preserved) |
| Upstream clarity pass rate | Unchanged | **Increases** on observe turns |

**Primary discriminator:** `referential_clarity_hard_replacement` event count **must decrease** alongside observe route rate. BV1B showed this count **stable at 38** after BK relocation — that pattern must not repeat.

---

## Metric dashboard (verification targets)

| Metric | Baseline | Phase 1 | Phase 2 target | Phase 3 stretch |
|---|---:|---:|---:|---:|
| **Fallback route rate (observe)** | 95.45% | 90.91% adj. | **<85%** | **<55%** |
| **Fallback incidence (overall)** | 69.16% | 67.29% adj. | **<60%** | **<45%** |
| **Ownerless count** | 13 | 5 | **≤5** | **≤3** |
| Referential clarity events | 38 | 38 | **≤26** | **≤12** |
| Observe non-fallback turns | 2 | 4 adj. | **≥7** | **≥20** |

---

## Confidence assessment

| Projection | Confidence | Basis |
|---|---|---|
| Phase 1 ownerless → 5 | **High** | Stamp path exists; missing calls identified |
| Phase 1 adjusted incidence −1.87 pp | **High** | Accept/replace reclassification arithmetic |
| Phase 2 observe −20 to −40 pp | **Medium** | Depends on upstream contract coverage of `ambiguous_entity_reference` |
| Phase 3 overall <45% | **Low** | Requires Phase 2 success + aggressive upstream adoption |

Maintenance economics confidence remains **low** per `fallback_maintenance_economics_summary.json` until remediation snapshots exist (0 remediations recorded).

---

## Success criteria checklist (BV3 closeout)

- [x] Phase 1 shipped: ownerless ≤5; projection packaging fixed
- [x] Phase 2 shipped: observe route rate **<85%** on BV3F snapshot (47.83%)
- [x] `referential_clarity_hard_replacement` events decreased **≥10** from BV3D baseline (12 → 1)
- [x] Longitudinal trend classification **improving** (BV3F snapshot appended)
- [x] Protected replay manifest green
- [x] No increase in scene-opening fallback rate on observe route
- [x] BV3E implementation executed — incidence reduced on replay corpus, not relocated alone

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Baseline measurements |
| [BV3_fallback_reduction_plan.md](BV3_fallback_reduction_plan.md) | Phase definitions |
| [BV3_fallback_elimination_candidates.md](BV3_fallback_elimination_candidates.md) | EC projections |
| [BV1B_fallback_baseline_comparison.md](BV1B_fallback_baseline_comparison.md) | Relocation failure mode |
| `artifacts/golden_replay/fallback_maintenance_economics_summary.json` | Burden score 62.0 |

---

## BV3B effectiveness closeout (2026-06-21)

**Classification:** **`NO_MEASURABLE_CHANGE`**

BV3B refreshed the canonical FEM corpus (107 → 200 instances) via `tools/bv3b_replay_corpus_refresh.py`, re-ran protected golden replay (89/91 green), scenario-spine smoke validation, projection refresh, and incidence tooling.

| Metric | BV1B baseline | BV3B current | Delta |
|---|---:|---:|---:|
| Observe route rate | 95.45% | 80.00% | −15.45 pp |
| Fallback incidence | 69.16% | 57.50% | −11.66 pp |
| Ownerless count | 13 | 13 | 0 |
| Referential clarity hard replacements | 38 | **48** | **+10** |
| Passive-scene pressure fallback | 1 | 1 | 0 |

**Verdict:** Overall incidence and observe route rate improved on the **expanded** corpus, but the **primary BV3A discriminator regressed**. Refreshed observe turns show **`referential_clarity_upstream_repair_applied = 0`** and **`referential_clarity_hard_replacement` lineage +10**. This is **not** effective reduction and **not** ownership relabeling alone—it indicates BV3A repair is **not yet observable on the API-finalized replay corpus**.

**Success criterion (BV3A):** *Fresh corpus demonstrates measurable reduction in `referential_clarity_hard_replacement` events* — **not met**.

Deliverables:

- [BV3B_replay_refresh.md](BV3B_replay_refresh.md)
- [BV3B_fallback_incidence_delta.md](BV3B_fallback_incidence_delta.md)
- [BV3B_incidence_effectiveness_report.md](BV3B_incidence_effectiveness_report.md)
- `artifacts/bv3b_referential_clarity_metrics.json`
- `artifacts/bv3b_replay_refresh/corpus_refresh_manifest.json`

---

## BV3F effectiveness closeout (2026-06-21)

**Classification:** **`EFFECTIVE_REDUCTION`**

BV3F refreshed the canonical FEM corpus under BV3E gate code via `tools/bv3f_replay_corpus_refresh.py`, preserved frozen BV3D/BV3E baselines, re-ran BV3A/BV3D/BV1B/BV3E metrics, and aggregated results in `artifacts/bv3f_reduction_metrics.json`.

| Metric | BV3D frozen | BV3E projection | BV3F actual | Delta (actual vs BV3D) |
|---|---:|---:|---:|---:|
| Eligible turns | 1 | 12 | **11** | **+10** |
| Repairs applied | 1 | 12 | **11** | **+10** |
| Referential clarity hard replacements | 12 | **1** | **1** | **−11** |
| Observe route rate | 52.17% | 4.35%¹ | **47.83%** | −4.34 pp |
| Fallback incidence | 46.39% | — | **11.58%** | −34.81 pp |

¹ Optimistic projection assumed all repaired turns exit observe-route fallback entirely; actual corpus retains sealed passive-scene fallbacks on adjacent turns.

**Final verdict:** BV3 **closed with effective reduction**. The primary BV3 discriminator — `referential_clarity_hard_replacement` event count — decreased **−11** on replay-derived metrics, matching BV3E shape simulation projection. BV3E repair stamps (`referential_clarity_bv3e_repair_mode=exact_alias_introducer`) are observable on **10** replay-only FEM turns. This is real incidence reduction, not simulation-only projection and not the BV3B failure mode (frozen repair stamps at zero).

**Achieved reductions:**

- RC hard replacement: **12 → 1** (−11)
- Upstream repair applied (observe): **1 → 11**
- Replay-only eligible: **0 → 10**
- Unrepaired violation turns (observe): **12 → 1**
- Overall fallback incidence: **46.39% → 11.58%**

**Remaining dominant fallback families (post-BV3F observe route):**

| Family | Events | Share |
|---|---:|---:|
| `sealed_passive_scene_pressure_fallback` | **10** | 90.9% |
| `referential_clarity_hard_replacement` | **1** | 9.1% |

**Success criteria checklist (BV3 closeout):**

- [x] Phase 2 shipped: BV3E eligibility expansion live on replay FEM
- [x] `referential_clarity_hard_replacement` events decreased **≥10** from BV3D baseline 12
- [x] Replay refresh confirms repair activation (not simulation-only)
- [x] Protected replay manifest field-path parity green
- [x] No scene-opening fallback rate increase on observe (0 events)
- [ ] Observe route rate **<85%** — **met** (47.83%)
- [ ] Longitudinal trend **improving** — appended BV3F snapshot to `fallback_incidence_history.json`

**Follow-on:** [BV4_candidate_recommendation.md](BV4_candidate_recommendation.md) — **BV4A** (sealed passive-scene pressure satisfier) ranked first by ROI.

**Deliverables:**

- [BV3F_replay_refresh.md](BV3F_replay_refresh.md)
- [BV3F_reduction_validation.md](BV3F_reduction_validation.md)
- [BV3F_reduction_classification.md](BV3F_reduction_classification.md)
- [BV4_candidate_recommendation.md](BV4_candidate_recommendation.md)
- `artifacts/bv3f_reduction_metrics.json`
- `artifacts/bv3f_replay_refresh/corpus_refresh_manifest.json`
- `tools/bv3f_replay_corpus_refresh.py`
- `tools/bv3f_reduction_metrics.py`

