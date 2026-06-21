# BV5 — Follow-On Maintenance Candidates

**Date:** 2026-06-21  
**Trigger:** BV5 classification **REDUCED_COST** (fallback + meta core) with residual redistribution on test/meta-read hubs.  
**Prior list:** [BV_follow_on_candidates.md](BV_follow_on_candidates.md) (BV2–BV4 — **completed or superseded**).

---

## Completed cycles (closeout)

| Cycle | Target | Outcome | Residual |
|---|---|---|---|
| **BV2** | `final_emission_meta` read consolidation | Meta FI **61 → 24** (−64% on core) | meta_read **28** FI; bucket_views **22** FI |
| **BV3** | Fallback observe-route reduction | Incidence **46.39% → 11.58%**; RC **−11** | PSP became dominant until BV4B |
| **BV4B** | PSP upstream concrete-beat satisfier | PSP **10 → 0**; incidence **1.05%** | **1** RC hard-replace observe fallback |

---

## Next highest-value repository-wide targets

Ranked by **measured remaining drag × fan-in × unblocked ROI**.

### 1. BV6 — Residual referential-clarity observe fallback (RC shape expansion)

| Item | Detail |
|---|---|
| **Problem** | **1/95** observe turns still hard-replaces via `referential_clarity_hard_replacement`; last measurable fallback event on BV3D corpus |
| **Scope** | Safe EC-M cluster shapes (title disambiguation, single-candidate grounding) per [BV4_candidate_recommendation.md](BV4_candidate_recommendation.md) BV4B-RC track |
| **Projected ROI** | **High leverage per event** — clearing last observe fallback → **0%** incidence on corpus |
| **Risk** | Medium — speaker contract / alias false positives |
| **Success metric** | Fallback incidence **0%** on BV3D corpus; observe route **0%**; protected replay green |
| **Scorecard impact** | Maintenance Economics **+0.5**; Maintenance Drag **+0.5** |

### 2. BV7 — Test governance facade decomposition (deferred BV4)

| Item | Detail |
|---|---|
| **Problem** | `tests.helpers.emission_smoke_assertions` **73 FI** — largest ecosystem fan-in node; `test_ownership_registry` **57 FO** unchanged |
| **Scope** | Shard smoke facade by concern (gate preflight / fallback / replay adapters); domain-scoped registry scans per original BV4 plan |
| **Projected ROI** | **Medium-high** — reduces test churn on single-module edits; no runtime incidence impact |
| **Risk** | Import churn across **69+** consumers; temporary migration drag |
| **Success metric** | No single test helper FI **>35**; registry FO **<40**; governance commit median **<25** files |
| **Scorecard impact** | Maintenance Drag **+1**; Operational Simplicity **+0.5** |

### 3. BV8 — Speaker projection recurrence retirement

| Item | Detail |
|---|---|
| **Problem** | Speaker drift recurrence key still **8** observations (72.7% share); unchanged through BV2–BV4 |
| **Scope** | Target `tests/helpers/golden_replay.py` speaker projection seam; align with BV2 replay adapter boundaries |
| **Projected ROI** | **Medium** — reduces protected replay maintenance churn unrelated to fallback |
| **Risk** | Low-medium — replay regression surface |
| **Success metric** | Recurrence occurrence **≤2**; validated retirement in `bug_recurrence_history.json` |
| **Scorecard impact** | Maintenance Drag **+0.5**; Ownership Clarity keep |

---

## Secondary targets (defer unless blocked)

| ID | Surface | Why deferred |
|---|---|---|
| BV4C | Measurement / lineage hygiene (`event_owner=gate` on 1 event) | **0 pp** incidence; batch with BV6 |
| Terminal pipeline | **26/14** convergence hub | Legitimate BJ owner; fewer touches than smoke/meta_read |
| Attribution strict completeness | **0%** strict; owner bucket **38.78%** | Requires BS write-path program, not BV fallback follow-on |
| Runtime megamodules | `interaction_context`, `api`, `gm` | Outside BV scope; BO-identified |

---

## Priority ordering

| Rank | Cycle | Rationale |
|---:|---|---|
| **1** | **BV6** | Last measurable fallback event; direct continuation of BV3/BV4 success path |
| **2** | **BV7** | Largest **unchanged** fan-in hub (smoke 73); original BV4 scope still open |
| **3** | **BV8** | Recurrence drag persists despite fallback wins |

---

## If classification had remained REDISTRIBUTED_COST

Would prioritize **meta_read + bucket_views import consolidation** (74 combined meta-ecosystem FI) and **terminal_pipeline** fan-out reduction. BV5 measurement **does not** support that primary path — fallback reduction is decisive.

---

## Evidence

| Source | Role |
|---|---|
| [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md) | Net result + classification |
| [BV5_hub_comparison.md](BV5_hub_comparison.md) | Residual hub ranks |
| [BV5_fallback_burden_comparison.md](BV5_fallback_burden_comparison.md) | 1 residual RC event |
| [BV4_candidate_recommendation.md](BV4_candidate_recommendation.md) | RC shape expansion spec |
| [BV_follow_on_candidates.md](BV_follow_on_candidates.md) | Original BV2–BV4 plan |
