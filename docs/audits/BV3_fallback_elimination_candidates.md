# BV3 — Observe-Route Fallback Elimination Candidates

**Date:** 2026-06-21  
**Constraint:** Candidates must be implementable **without changing player-visible behavior** on the protected corpus, or with explicit protected-replay validation for upstream contract changes.  
**Baseline:** Observe route rate 95.45%; referential clarity 38/42 observe events.

---

## Candidate summary

| ID | Candidate | Mechanism | Projected observe route Δ | Projected overall incidence Δ | Risk | Ownership impact |
|---|---|---|---:|---:|---|---|
| **EC-01** | Upstream referential-clarity contract on observe turns | Explicit contract | **−25 to −40 pp** | **−8 to −12 pp** | Medium | Shifts burden to GM/upstream-prepared; sealed-gate bucket rate falls with triggers |
| **EC-02** | Expand non-strict local referential repair | Deterministic projection | **−5 to −15 pp** | **−2 to −5 pp** | Medium | Visibility module retains selection; fewer sealed content invocations |
| **EC-03** | Owner bucket registry enforcement on RC path | Ownership assertion | **0 pp** (measurement) | **0 pp** | Low | Closes 8/42 observe ownerless; sealed-gate stamps reach ~100% on RC events |
| **EC-04** | Prepared-emission accept vs replace lineage split | Explicit contract | **−2 to −7 pp** | **−1 to −2 pp** | Low | Stamps response-type owners; 3 ownerless → 0 on observe |
| **EC-05** | Lineage `event_owner` → selection owner default | Deterministic projection | **0 pp** | **0 pp** | Low | Removes false gate hub concentration in reports |
| **EC-06** | Realization family stamp on RC → sealed path | Registry-enforced guarantee | **0 pp** | **0 pp** | Low | `gate_terminal_repair` coverage 1/42 → ~40/42 on observe |
| **EC-07** | Passive-scene upstream pressure satisfier | Explicit contract | **−10 to −20 pp** | **−4 to −8 pp** | Medium-high | Upstream-prepared share may rise if pressure resolved pre-gate |
| **EC-08** | Skip redundant visibility/FM hard-replace branches on observe | Dead path removal | **0 pp** on corpus | **0 pp** | Low | Code shrink; no observe incidence (already zero) |
| **EC-09** | Deterministic observe fallback kind on FEM | Registry-enforced guarantee | **0 pp** | **0 pp** | Low | Sets `visibility_fallback_kind` when RC fires — audit fidelity |
| **EC-10** | Gate selection label removal (OR-PSP-01) | Ownership assertion | **0 pp** | **0 pp** | Low | 1 event reclassified to visibility selection owner |

---

## EC-01 — Upstream referential-clarity contract (primary lever)

**Problem:** 39/42 observe fallback turns fail referential clarity with `ambiguous_entity_reference` before gate enforcement.

**Proposal:** Add an observe-route **upstream contract** (prompt context + `upstream_response_repairs` or GM output validator) requiring explicit entity anchors for observe/resolution text **before** terminal pipeline.

**Mechanism type:** Explicit contract

| Attribute | Detail |
|---|---|
| **Projected observe route rate** | 95.45% → **55–70%** (optimistic **50%** if contract covers majority of ambiguous refs) |
| **Projected overall fallback incidence** | 69.16% → **57–61%** |
| **Risk** | **Medium** — text may change if upstream repair over-corrects; requires golden replay + transcript gauntlet |
| **Ownership impact** | Fewer sealed-gate events; `upstream-prepared` share may increase; visibility selection owner event count drops proportionally |
| **Validation** | Protected replay manifest; compare `referential_clarity_validation_passed=True` rate on observe turns |

---

## EC-02 — Non-strict referential local repair expansion

**Problem:** OR-RC-LOCAL avoids fallback on strict-social dialogue but **never runs** on observe (non-strict) turns.

**Proposal:** Port safe subset of `_try_strict_social_local_pronoun_substitution_repair` to non-strict observe turns where violations are single-entity ambiguous references without multi-entity candidates.

**Mechanism type:** Deterministic projection / in-place repair

| Attribute | Detail |
|---|---|
| **Projected observe route rate** | **−5 to −15 pp** (depends on violation shape overlap with strict-social repair) |
| **Projected overall incidence** | **−2 to −5 pp** |
| **Risk** | **Medium** — must preserve narration purity and anti-reset constraints |
| **Ownership impact** | Visibility module owns repair; `PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION` stamps increase; sealed content owner events decrease |

---

## EC-03 — Owner bucket registry enforcement (RC path)

**Problem:** 8/38 referential-clarity events on observe lack `fallback_owner_bucket` despite sealed-gate content.

**Proposal:** Call `stamp_visibility_fallback_owner_bucket_from_fields` with required fields in `apply_referential_clarity_enforcement` hard-replace path (mirror visibility-hard-replace path at lines 2024–2028).

**Mechanism type:** Ownership assertion / registry-enforced guarantee

| Attribute | Detail |
|---|---|
| **Projected route rate** | **0 pp** — behavior neutral |
| **Projected ownerless (observe)** | 12 → **4** (−8) |
| **Projected ownerless (repo)** | 13 → **5** |
| **Risk** | **Low** |
| **Ownership impact** | sealed-gate bucket count +8 on observe; governance metrics improve |

---

## EC-04 — Prepared-emission accept vs replace lineage split

**Problem:** OR-RTP-01 emits `fallback_selected` for `accept_candidate` turns (2/3).

**Proposal:** Projection rule: `response_type_prepared_emission` + `final_route=accept_candidate` → emit `prepared_emission_accepted` diagnostic event, not fallback selection.

**Mechanism type:** Explicit contract (lineage schema)

| Attribute | Detail |
|---|---|
| **Projected observe route rate** | 95.45% → **90.9%** (−4.55 pp if 2 turns reclassified) to **93.2%** (−2.3 pp if 1 turn) |
| **Projected overall incidence** | 69.16% → **67.3–68.2%** |
| **Risk** | **Low** — measurement semantics; may affect dashboards |
| **Ownership impact** | Stamp `game.final_emission_response_type` selection owner on remaining true fallbacks |

---

## EC-05 — Lineage event_owner packaging fix

**Problem:** All 74 corpus events label `event_owner=game.final_emission_gate` while selection owner split shows visibility 38 / gate 32.

**Proposal:** Default lineage `event_owner` to `fallback_selection_owner` when stamped.

**Mechanism type:** Deterministic projection

| Attribute | Detail |
|---|---|
| **Incidence impact** | **None** |
| **Risk** | **Low** — replay governance registry update required |
| **Ownership impact** | Gate hub metrics decrease; visibility hub metrics increase — **truthful accounting** |

---

## EC-06 — Realization family on referential-clarity sealed replace

**Problem:** 41/42 observe fallback turns missing `realization_fallback_family`; sealed replace path should stamp `gate_terminal_repair`.

**Proposal:** Invoke `stamp_sealed_fallback_realization_family` / `attach_realization_fallback_family` in referential-clarity hard-replace path (parity with visibility-hard-replace).

**Mechanism type:** Registry-enforced guarantee

| Attribute | Detail |
|---|---|
| **Incidence impact** | **None** |
| **Risk** | **Low** |
| **Ownership impact** | Provenance completeness; failure classifier alignment |

---

## EC-07 — Passive-scene pressure upstream satisfier

**Problem:** 40/42 observe hard replaces select `passive_scene_pressure_fallback` — GM observe text fails clarity **and** scene pressure triggers fallback branch.

**Proposal:** Upstream observe realization prepares visible-fact-aligned text satisfying both referential clarity and passive-scene visibility validators (human-adjacent focus + visible fact prioritization).

**Mechanism type:** Explicit contract + deterministic projection

| Attribute | Detail |
|---|---|
| **Projected observe route rate** | **−10 to −20 pp** (overlaps EC-01) |
| **Projected overall incidence** | **−4 to −8 pp** |
| **Risk** | **Medium-high** — touches GM generation path |
| **Ownership impact** | Reduces sealed-gate content owner events; may increase upstream-prepared attribution |

---

## EC-08 — Remove dead hard-replace branches on observe (code hygiene)

**Problem:** Visibility and first-mention hard-replace branches execute checks but never fire on observe corpus.

**Proposal:** Short-circuit or consolidate enforcement order for `res_kind=observe` when contracts guarantee pre-validated text (post EC-01).

**Mechanism type:** Fallback removal candidate (Phase 3 only)

| Attribute | Detail |
|---|---|
| **Incidence impact** | **0 pp** until EC-01 proven |
| **Risk** | **Low** now; **High** if premature |
| **Ownership impact** | Terminal pipeline shrinks; visibility module remains owner |

---

## EC-09 — FEM fallback kind stamp on RC replace

**Problem:** `visibility_fallback_kind` / `fallback_kind` absent on FEM for 42/42 observe fallback turns despite lineage kind.

**Proposal:** Stamp selected candidate's `fallback_kind` on FEM during referential-clarity replace (mirror first-mention replace path).

**Mechanism type:** Registry-enforced guarantee

| Attribute | Detail |
|---|---|
| **Incidence impact** | **None** |
| **Risk** | **Low** |
| **Ownership impact** | FEM ↔ lineage parity; BS contract compliance |

---

## EC-10 — Gate selection label cleanup

**Problem:** 1 observe event labels gate as selection owner for sealed passive sub-kind.

**Proposal:** Route through visibility selection owner consistently; gate retains orchestration role only.

**Mechanism type:** Ownership assertion

| Attribute | Detail |
|---|---|
| **Incidence impact** | **None** |
| **Risk** | **Low** |
| **Ownership impact** | gate selection-owner count −1; visibility +1 repo-wide |

---

## Prioritized elimination stack (ROI order)

| Priority | ID | Rationale |
|---:|---|---|
| 1 | EC-01 | Only candidate with double-digit pp route reduction potential |
| 2 | EC-02 | Complements EC-01; reuses proven local repair pattern |
| 3 | EC-07 | Targets dominant content branch (passive scene pressure) |
| 4 | EC-03, EC-04, EC-05, EC-06, EC-09, EC-10 | Behavior-neutral; enable accurate reduction measurement |
| 5 | EC-08 | Phase 3 only after incidence falls |

---

## Combined projection (if EC-01 + EC-02 + EC-03/04 shipped)

| Metric | Baseline | Conservative | Target |
|---|---:|---:|---:|
| Observe route rate | 95.45% | **75%** | **<85%** (BV follow-on success metric) |
| Overall fallback incidence | 69.16% | **58%** | **<60%** |
| Observe ownerless events | 12 | **4** | **≤5** |
| Repo ownerless | 13 | **5** | **≤5** |

---

## Evidence

| Source | Role |
|---|---|
| [BV3_fallback_necessity_analysis.md](BV3_fallback_necessity_analysis.md) | Necessity classes |
| [BV3_route_concentration_report.md](BV3_route_concentration_report.md) | Concentration metrics |
| [BV_follow_on_candidates.md](BV_follow_on_candidates.md) | BV3 success metric (<85% observe route) |
| Corpus analysis | Violation kinds, `final_emitted_source` distribution |
