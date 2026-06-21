# BV3C — Remediation Plan

**Date:** 2026-06-21  
**Scope:** Analysis-derived plan only — **no behavior changes in BV3C**.  
**Root cause:** Mixed — corpus mismatch + eligibility drift + replay divergence ([BV3C_root_cause.md](BV3C_root_cause.md)).

---

## Goals

1. Make repair activation rate **measurable** on corpus that actually contains eligible shapes.  
2. Reduce `referential_clarity_hard_replacement` on observe turns **where BV3A contract applies**.  
3. Avoid changing BV3A eligibility rules or gate ordering in the first fix tranche.

---

## Minimal fix (recommended sequence)

### Fix 1 — Corpus hygiene for measurement (zero code risk)

| Action | Detail |
|---|---|
| Exclude archived pre-refresh paths | Remove `artifacts/bv3b_replay_refresh/scene_canon_hygiene_runtime.*` from `DEFAULT_ROOTS` or metrics filter |
| Prefer top-level finalized FEM | Skip nested `emission_debug_lane` snapshots when counting activation |
| Re-run | `python tools/bv3a_referential_clarity_metrics.py` |

**Expected outcome:** Denominator reflects **current code only** (~21 observe turns post-filter). Activation rate may remain 0% but incidence becomes **interpretable**.

### Fix 2 — Replay refresh alignment (low code, refresh tooling)

| Action | Detail |
|---|---|
| Update BV3B stub candidate | Use **validator-failing** shape: `"…," he says` **without** preceding named guard anchor |
| Optional grounding variant | Second playthrough prompt with `set_social_target` / social question preamble to populate interlocutor on subsequent observe |
| Add one protected replay row | Mirror `test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` fixture |

**Expected outcome:** ≥1 observe turn with `upstream_repair_applied=true` in refresh corpus → activation rate **>0%** on eligible subset.

### Fix 3 — Eligibility extension (product decision; **not** minimal)

Only if product intent includes multi-violation and `referent_drift` shapes:

| Action | Detail |
|---|---|
| Relax `_violations_eligible_for_non_strict_local_pronoun_repair` | e.g. repair isolated dialogue-tag `he` when other violations are possessive/narrative |
| Add `referent_drift` branch | Separate from ambiguous_entity_reference |

**Defer** until Fix 1–2 confirm activation on contract slice. This is **not** the minimal fix.

---

## Projected impact (after Fix 1 + Fix 2)

Assumptions: 21 refreshed observe turns; 1–3 turns seeded with unit-test-equivalent shape; archive excluded.

| Metric | Current | Projected (conservative) |
|---|---:|---:|
| **Repair activation rate** (eligible subset) | 0% | **33–100%** (1–3 / 1–3 eligible seeded turns) |
| **Repair activation rate** (all observe) | 0% | **5–15%** (1–3 / ~21) |
| `referential_clarity_hard_replacement` count | 48 (repo-wide lineage) | **−1 to −3** per refresh cycle on seeded turns only |
| Observe route fallback rate | 0.80 | **−0.02 to −0.05 pp** (limited to seeded shapes) |
| Overall fallback incidence | 0.575 | **−0.005 to −0.015 pp** |

**Not projected to reach BV3A `-8 to −15` hard-replacement delta** until corpus includes ~30+ grounded ambiguous-speaker turns — those shapes remain **ineligible by design** without interlocutor/social NPC.

---

## Impact on fallback incidence

| Fallback family | Expected change |
|---|---|
| `referential_clarity_hard_replacement` | Small decrease only on newly eligible seeded turns; **no change** on multi-person ungrounded `he` (still hard replace) |
| `sealed_passive_scene_pressure_fallback` | Unchanged |
| `scene_opening` | Unchanged |
| Observe accept path (`accept_candidate`) | Unchanged for named-anchor prepared text |

---

## Verification plan (post-remediation)

1. `pytest tests/test_bv3a_observe_referential_clarity_repair.py` — regression guard.  
2. Refresh corpus with aligned stub → confirm ≥1 `upstream_repair_applied=true`.  
3. Re-run BV3A metrics + BV1B incidence delta on **filtered** roots.  
4. Compare `referential_clarity_hard_replacement` lineage before/after on **fixed prompt manifest** (107-turn fingerprint lock per BV3B recommendation).

---

## Success criteria (remediation complete)

| Criterion | Target |
|---|---|
| Explain 0% activation | **Met in BV3C** |
| Activation on eligible shapes | >0% after Fix 2 |
| No regression on ineligible multi-person | hard replace preserved |
| Incidence interpretability | archive/debug FEM excluded |

---

## Explicit non-goals (BV3C)

- No gate logic changes in this audit pass  
- No eligibility rule expansion without product sign-off  
- No commit of temporary analysis scripts (`tools/_bv3c_*`)
