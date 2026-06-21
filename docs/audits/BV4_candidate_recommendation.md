# BV4 — Candidate Recommendation

**Date:** 2026-06-21  
**Trigger:** BV3F confirmed **EFFECTIVE_REDUCTION** on `referential_clarity_hard_replacement` (−11).  
**Corpus:** Post-BV3F replay scan — 95 FEM instances, 11 observe fallback events.

---

## Post-BV3F fallback landscape

| Family | Observe events | % of observe fallbacks | Notes |
|---|---:|---:|---|
| **Sealed passive scene pressure** | **10** | **90.9%** | Dominant remaining cost center |
| Referential clarity hard replacement | 1 | 9.1% | Residual multi-entity / non-introducer shape |
| Scene opening | 0 | 0% | Non-observe route |
| Diagnostics / response-type | 0 | 0% | Cleared on refreshed corpus |

BV3E eliminated the MV-01 exact-alias introducer cluster. Remaining observe burden concentrates in **sealed passive-scene content selection** and **one residual RC shape**.

---

## BV4 candidate ranking (by expected ROI)

| Rank | ID | Focus | Mechanism | Projected observe Δ | Projected overall Δ | Risk | ROI rationale |
|---:|---|---|---|---:|---:|---|---|
| **1** | **BV4A** | Sealed passive-scene pressure upstream satisfier | EC-07 explicit contract | **−15 to −25 pp** | **−6 to −10 pp** | Medium-high | Targets **90.9%** of remaining observe fallbacks; largest single-family leverage |
| **2** | **BV4B** | Medium-risk RC shape expansion (EC-M01 … EC-M04) | Deterministic in-place repair | **−2 to −5 pp** | **−1 to −2 pp** | Medium | Clears residual RC hard replace + shapes without singular introducer; smaller but direct |
| **3** | **BV4C** | Measurement / ownership hygiene stack (EC-03 … EC-06, EC-09, EC-10) | Registry + lineage fixes | **0 pp** | **0 pp** | Low | Enables accurate BV4A/B measurement; no incidence alone but unblocks trustworthy ROI tracking |

---

## BV4A — Sealed passive-scene pressure satisfier (recommended first)

**Problem:** 10/11 post-BV3F observe fallbacks stamp `sealed_passive_scene_pressure_fallback` as content owner despite BV3E clearing RC violations in place on adjacent turns.

**Proposal:** Upstream observe realization contract requiring visible-fact-aligned text that satisfies both referential clarity and passive-scene visibility validators before terminal gate (extends EC-07).

| Attribute | Detail |
|---|---|
| **Expected ROI** | **Highest** — addresses dominant post-BV3 family |
| **Projected observe route rate** | 47.83% → **22–33%** |
| **Dependencies** | BV3F refresh corpus as baseline; protected replay + transcript gauntlet |
| **Validation** | Require RC + sealed sub-kind both absent on observe turns |

---

## BV4B — Residual referential-clarity shape expansion

**Problem:** 1 observe turn retains `referential_clarity_hard_replacement`; ~30 archive ambiguous-speaker shapes lack introducer (deferred EC-M cluster).

**Proposal:** Port safe subsets of multi-violation dialogue repair beyond exact-alias introducer (title disambiguation, single-candidate grounding).

| Attribute | Detail |
|---|---|
| **Expected ROI** | **Medium** — small event count but closes BV3 residual |
| **Projected observe route rate** | **−2 to −5 pp** incremental |
| **Risk** | Medium — false-positive alias / speaker contract edge cases |
| **Validation** | `tests/test_bv3e_eligibility_expansion.py` pattern + golden replay |

---

## BV4C — Measurement fidelity / ownership stack

**Problem:** Post-BV3F lineage still labels `event_owner=game.final_emission_gate` on all 11 events; sealed vs visibility selection-owner split obscures BV4A targeting.

**Proposal:** Ship behavior-neutral EC-03 … EC-06, EC-09, EC-10 before BV4A incidence claims.

| Attribute | Detail |
|---|---|
| **Expected ROI** | **Enabling** — zero direct incidence; prevents relocation false positives |
| **Effort** | Low per item; batchable |
| **When** | Parallel or immediately before BV4A snapshot comparison |

---

## Recommended sequence

1. **BV4C** (1–2 cycles) — ownership + FEM parity so BV4A deltas are trustworthy.
2. **BV4A** (primary) — attack sealed passive-scene pressure on observe route.
3. **BV4B** (follow-on) — mop residual RC shapes after BV4A stabilizes.

---

## Success criteria (BV4 entry)

| Criterion | BV3F achieved | BV4 target |
|---|---|---|
| RC hard replacement (observe) | 1 | **0** |
| Observe route rate | 47.83% | **<35%** |
| Dominant family | sealed passive (91%) | **<50%** sealed share |
| Repair activation observable on replay FEM | Yes | Maintain |

---

## Evidence

| Source | Role |
|---|---|
| [BV3F_reduction_validation.md](BV3F_reduction_validation.md) | BV3 closeout metrics |
| [BV3_fallback_elimination_candidates.md](BV3_fallback_elimination_candidates.md) | EC-07 / EC-M definitions |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Post-BV3F family counts |
| [BV4A_reduction_plan.md](BV4A_reduction_plan.md) | BV4A discovery closeout — Phase 1 plan |
| `artifacts/bv4a_passive_scene_inventory.json` | PSP event inventory |
