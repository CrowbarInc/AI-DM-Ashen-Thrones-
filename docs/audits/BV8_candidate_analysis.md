# BV8 — Next-Candidate Analysis

**Date:** 2026-06-21  
**Context:** Post-BV7C closeout; monolith FI=15; largest test hubs are extracted bridges.  
**Goal:** Select the next maintenance-reduction target using current repository evidence.

---

## Candidates

| ID | Target | Current signal |
|---|---|---|
| **A** | `replay_smoke_assertions` decomposition | FI **46** (#3 repo hub) |
| **B** | `gate_integration_smoke` decomposition | FI **39** (#4 repo hub) |
| **C** | Speaker projection recurrence retirement (BV8) | **8** protected recurrence rows (72.7% of recurrence history) |

---

## Scoring matrix

Scale: **5 = best / lowest risk**, **1 = worst / highest risk** for maintenance reduction and replay risk; implementation cost inverted (**5 = cheapest**).

| Criterion | A: `replay_smoke_assertions` | B: `gate_integration_smoke` | C: Speaker projection (BV8) |
|---|---:|---:|---:|
| **Expected maintenance reduction** | 3 | 3 | **5** |
| **Implementation cost** | 2 | 2 | **4** |
| **Replay risk** | 2 | 3 | **4** |
| **Weighted score** | 7 | 8 | **13** |

---

## Candidate A — `replay_smoke_assertions` (FI 46)

### Evidence

- Largest post-BV7 test-helper hub by design (BV7A FEM read bridge).
- Owns `final_emission_meta_from_output` (43 consumer suites) and `read_turn_debug_notes`.
- Thin production fan-out (`game.final_emission_meta_read` only).

### Maintenance reduction potential

| Pro | Con |
|---|---|
| High FI visibility | Bridge is **already extracted** — further split yields diminishing returns |
| Single production dependency | Most consumers co-import gate bridge; overlap-heavy |
| Clear ownership charter | FEM read path is intentionally centralized |

### Implementation cost: **High (2/5)**

- Would require second-order split (e.g. debug-notes vs FEM meta read) with ~40 consumer touchpoints.
- Overlap with `opening_fallback_evidence` (23 FI) and `golden_replay_projection` (14 FI) increases coordination cost.

### Replay risk: **Medium-high (2/5)**

- FEM read bridge is on the critical path for golden replay, transcript regressions, and gate diagnostics.
- Any import reshuffle risks replay fixture drift without semantic benefit.

**Verdict:** **Defer.** BV7A already achieved the intended extraction; FI=46 reflects legitimate replay integration surface, not accidental monolith regrowth.

---

## Candidate B — `gate_integration_smoke` (FI 39)

### Evidence

- Second-largest test-helper hub (BV7A gate orchestration bridge).
- Owns `apply_final_emission_gate_consumer` (37 suites) and `gm_response_stub`.
- Co-located with `strict_social_harness` (15 FI) by design.

### Maintenance reduction potential

| Pro | Con |
|---|---|
| High FI | Gate consumer seam is **intentionally named** post-BV7A |
| Clear BN1 runtime delegate boundary | Further split would duplicate `strict_social_harness` / runtime docs |
| Medium migration cost vs replay | Gate orchestration touches ordering-sensitive suites |

### Implementation cost: **High (2/5)**

- Gate consumer wrapper is a single function with broad co-import overlap.
- Splitting stub vs consumer adds module count without reducing total ecosystem FI.

### Replay risk: **Medium (3/5)**

- Lower than replay bridge (no FEM lineage reads) but gate ordering regressions are expensive to diagnose.

**Verdict:** **Defer.** Gate integration FI is expected post-extraction concentration; not accidental hub drag.

---

## Candidate C — Speaker projection recurrence retirement (BV8)

### Evidence

| Signal | Value | Source |
|---|---:|---|
| Protected recurrence rows | **8** | `bug_recurrence_history.json` / BV5 scorecard |
| Share of recurrence history | **72.7%** | [BV5_scorecard_revalidation.md](BV5_scorecard_revalidation.md) |
| BV3/BV4 fallback wins reflected in recurrence | **No** (`validated_outcome_count: 0`) | BV5 follow-on |
| BV7 impact on speaker drift | **None** | BV7 targeted smoke facade, not golden replay speaker seam |
| Prior recommendation | **Rank #3 in BV5 follow-on** | [BV5_follow_on_candidates.md](BV5_follow_on_candidates.md) |

### Maintenance reduction potential: **High (5/5)**

- Addresses the **only recurrence signal with repeat-fix history** unchanged through BV2–BV7.
- Fallback incidence collapsed (69% → 1%) but speaker projection drift **persisted** — maintenance drag shifted, not eliminated.
- Targets `tests/helpers/golden_replay.py` speaker projection seam per BV5 recon scope.

### Implementation cost: **Low-medium (4/5)**

- Bounded scope: golden replay speaker observation path, not 40+ suite import migration.
- Aligns with existing BV2 replay adapter boundaries (`final_emission_replay_projection` owner stable at 15 FI).
- No production runtime changes required for initial retirement pass.

### Replay risk: **Low-medium (4/5)**

- Works **within** legitimate replay ownership (`golden_replay_projection`, `final_emission_replay_projection`).
- Protected observation path changes need golden corpus review — but recurrence data proves current path **already fails repeatedly**.
- Lower blast radius than reshuffling 46 FI replay bridge consumers.

**Verdict:** **Recommended next target.**

---

## Ranked recommendation

| Rank | Target | Rationale |
|---:|---|---|
| **1** | **C — BV8 speaker projection recurrence retirement** | Highest maintenance reduction per unit cost; addresses persistent recurrence drag untouched by BV7 |
| 2 | B — `gate_integration_smoke` further split | Legitimate hub; defer until gate ordering docs need refresh |
| 3 | A — `replay_smoke_assertions` further split | Legitimate hub; defer — BV7A already extracted FEM bridge |

---

## Why not continue BV7-style smoke splits?

Post-BV7C monolith FI (**15**) is within the 12–18 target band. Remaining monolith importers are **100% intentional** smoke-core ([BV7C_import_classification.md](BV7C_import_classification.md)). Further phrase/route/speaker module splits would:

- Reduce monolith FI by ~10 at most
- Add module proliferation without addressing the **recurrence signal**
- Risk BE6 triple-layer boundary erosion

The next maintenance win is **recurrence retirement**, not additional smoke facade fragmentation.

---

## Suggested BV8 scope sketch

1. Inventory speaker projection calls in `golden_replay.py` / `golden_replay_projection.py`.
2. Align protected observation expectations with `final_emission_replay_projection` owner boundaries (BV2 adapter model).
3. Retire or narrow recurrence-prone projection rows; validate against golden corpus.
4. Measure recurrence history delta (`bug_recurrence_history.json`) post-retirement.

---

## Evidence

| Source | Role |
|---|---|
| [BV7_closeout.md](BV7_closeout.md) | BV7 completion metrics |
| [BV7C_hub_rankings.md](BV7C_hub_rankings.md) | Current FI landscape |
| [BV5_follow_on_candidates.md](BV5_follow_on_candidates.md) | Prior BV8 recommendation |
| [BV5_scorecard_revalidation.md](BV5_scorecard_revalidation.md) | Recurrence concentration |
| `docs/audits/BU_import_fan_in_fan_out.csv` | Bridge hub FI |
