# BV4A — Passive Scene Pressure Elimination Candidates

**Date:** 2026-06-21  
**Baseline:** 10 `sealed_passive_scene_pressure_fallback` events; observe route rate 47.83%; overall fallback incidence 11.58%.  
**Constraint:** Analysis-only — no production changes in BV4A discovery.

---

## Candidate summary

| ID | Candidate | Risk | Projected PSP Δ | Projected observe route Δ | Projected overall incidence Δ | Replay impact | Ownership impact |
|---|---|---|---:|---:|---:|---|---|
| **EC-4A-01** | Upstream concrete-beat contract enforcement | **Medium** | **−8 to −10** | **−35 to −43 pp** | **−8 to −11 pp** | Golden replay + transcript gauntlet | Fewer sealed-gate events; upstream-prepared share rises |
| **EC-4A-02** | Deterministic upstream beat injection repair | **Medium** | **−6 to −10** | **−26 to −43 pp** | **−6 to −11 pp** | Protected replay row required | Visibility/passive-scene repair stamps increase |
| **EC-4A-03** | Post-BV3E-repair accept path at terminal fork | **Low–Medium** | **−2 to −6** | **−9 to −26 pp** | **−2 to −6 pp** | Regression on BV3E tests | Accept path reduces sealed content invocations |
| **EC-4A-04** | Passive-scene pressure due-check refinement | **Low** | **−0 to −2** | **−0 to −9 pp** | **−0 to −2 pp** | Low if guard-in-facts false positive fixed | Measurement shift only if miscalibrated |
| **EC-4A-05** | GM retry targeting `passive_scene_pressure_missing_concrete_beat` | **Medium** | **−5 to −9** | **−22 to −39 pp** | **−5 to −9 pp** | Retry budget / stall tests | Upstream-prepared attribution |
| **EC-4A-06** | Selection owner + lineage packaging (PSP path) | **Low** | **0** | **0 pp** | **0 pp** | Governance registry | Gate hub ↓; visibility hub ↑ |
| **EC-4A-07** | Retire generic sealed template when contract satisfied | **High** | **−10** (after EC-4A-01) | **−43 pp** | **−11 pp** | Phase 3 only | Terminal pipeline shrink |

---

## EC-4A-01 — Upstream concrete-beat contract (primary lever)

**Problem:** 10/10 events reject upstream for `passive_scene_pressure_missing_concrete_beat`; GM instructions exist but are not enforced.

**Proposal:** Add observe-route upstream contract: when `passive_scene_pressure` payload active, output MUST pass `_reply_already_has_concrete_interaction` before terminal pipeline (mirror BV3A RC contract pattern).

| Attribute | Detail |
|---|---|
| **Risk** | **Medium** — text may change; requires golden replay |
| **Projected PSP incidence** | 10 → **0–2** |
| **Projected observe route rate** | 47.83% → **4–13%** |
| **Projected overall fallback incidence** | 11.58% → **1–3%** |
| **Replay impact** | Protected replay manifest; observe prompt variants |
| **Ownership impact** | sealed-gate content owner events ↓; upstream-prepared ↑ |

**Mechanism type:** Explicit contract

---

## EC-4A-02 — Deterministic upstream beat injection repair

**Problem:** Stub/live GM may fail contract; gate currently falls through to sealed generic template.

**Proposal:** Pre-gate repair path injects scene-aware concrete beat (guard speaks first) when pressure due and upstream lacks interaction — analogous to BV3E `exact_alias_introducer`.

| Attribute | Detail |
|---|---|
| **Risk** | **Medium** — must preserve narration purity + anti-railroading |
| **Projected PSP incidence** | 10 → **0–4** |
| **Projected observe route Δ** | **−26 to −43 pp** |
| **Replay impact** | New fixture: passive observe + atmospheric upstream → repair applied |
| **Ownership impact** | `PRODUCER_REPAIR_KIND_PASSIVE_SCENE_PRESSURE` stamp; sealed ↓ |

**Mechanism type:** Deterministic projection / in-place repair

---

## EC-4A-03 — Post-BV3E-repair accept path

**Problem:** BV3E clears RC violations but terminal fork may still replace for pre-repair concrete-beat failure.

**Proposal:** Re-run concrete-beat check on post-repair text; accept upstream when RC clear + concrete beat satisfied.

| Attribute | Detail |
|---|---|
| **Risk** | **Low–Medium** — pipeline ordering sensitivity |
| **Projected PSP incidence** | 10 → **4–8** (partial — repaired text may still lack dialogue) |
| **Projected observe route Δ** | **−9 to −26 pp** |
| **Replay impact** | Extend BV3E tests with passive-scene assertions |
| **Ownership impact** | Fewer sealed replaces on repaired turns |

**Mechanism type:** Terminal fork logic

---

## EC-4A-04 — Pressure due-check refinement

**Problem:** `_passive_scene_pressure_due_for_fallback` fires on single passive observe when `"guard"` appears in visible facts — may be aggressive for first passive action.

**Proposal:** Require `passive_action_streak >= 1` AND concrete scene tension signal; avoid pressure due on first `I look around` unless streak/leads warrant.

| Attribute | Detail |
|---|---|
| **Risk** | **Low** — may reduce legitimate pressure beats |
| **Projected PSP incidence** | **−0 to −2** on current corpus |
| **Replay impact** | Minimal on single-turn refresh corpus |
| **Ownership impact** | None |

**Mechanism type:** Due-check calibration

---

## EC-4A-05 — GM retry for missing concrete beat

**Problem:** Refresh corpus shows retry escape hatches for scene_stall but not for passive-scene concrete beat.

**Proposal:** Add retry strategy class targeting `passive_scene_pressure_missing_concrete_beat` with constrained regeneration prompt.

| Attribute | Detail |
|---|---|
| **Risk** | **Medium** — retry cost + text drift |
| **Projected PSP incidence** | 10 → **1–5** |
| **Replay impact** | Retry budget tests; long-session stability |
| **Ownership impact** | upstream-prepared share ↑ |

**Mechanism type:** Retry policy / explicit contract

---

## EC-4A-06 — Selection owner packaging (behavior-neutral)

**Problem:** 10/10 PSP events label selection owner as gate hub.

**Proposal:** Stamp `game.final_emission_visibility_fallback` on passive-scene terminal selections (EC-10 pattern for PSP).

| Attribute | Detail |
|---|---|
| **Risk** | **Low** |
| **Projected incidence** | **0 pp** |
| **Replay impact** | Governance registry update |
| **Ownership impact** | Truthful visibility hub metrics |

**Mechanism type:** Ownership assertion

---

## EC-4A-07 — Retire generic sealed template (Phase 3)

**Problem:** `passive_scene_pressure_generic` is terminal backstop when upstream fails.

**Proposal:** After EC-4A-01/02 stable, remove or gate generic template behind contract satisfaction proof.

| Attribute | Detail |
|---|---|
| **Risk** | **High** if premature |
| **Projected PSP incidence** | **−10** (only after Phase 1 stable) |
| **Replay impact** | Full protected replay + spine validation |
| **Ownership impact** | Terminal pipeline shrink |

**Mechanism type:** Fallback removal candidate

---

## Risk classification summary

| Risk | Candidates |
|---|---|
| **Low** | EC-4A-04, EC-4A-06 |
| **Medium** | **EC-4A-01**, **EC-4A-02**, EC-4A-03, EC-4A-05 |
| **High** | EC-4A-07 (Phase 3 only) |

---

## Prioritized stack (ROI order)

| Priority | ID | Rationale |
|---:|---|---|
| 1 | **EC-4A-01** | Closes 100% of current trigger class at source; mirrors proven BV3 contract pattern |
| 2 | **EC-4A-02** | Safety net when GM fails contract; deterministic like BV3E |
| 3 | EC-4A-05 | Complements EC-4A-01 for live-upstream paths |
| 4 | EC-4A-03 | Low-cost incremental if pipeline ordering fix suffices |
| 5 | EC-4A-06 | Measurement fidelity before claiming reduction |
| 6 | EC-4A-04 | Tune after primary satisfiers ship |
| 7 | EC-4A-07 | Phase 3 retirement only |

---

## Evidence

| Source | Role |
|---|---|
| [BV4A_upstream_satisfier_map.md](BV4A_upstream_satisfier_map.md) | Satisfier specs |
| [BV4A_concentration_report.md](BV4A_concentration_report.md) | Pareto analysis |
| [BV3_fallback_elimination_candidates.md](BV3_fallback_elimination_candidates.md) | EC-07 predecessor |
