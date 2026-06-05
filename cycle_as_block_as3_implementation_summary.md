# Cycle AS3 — Repairs-Layer Downstream Decoupling Implementation Summary

**Date:** 2026-06-04  
**Block:** AS3 — Route non-owner suites off `game.final_emission_repairs` private seams  
**Behavior change:** None (import/facade relocation only)

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/repairs_consumer_facade.py` | **New** — lazy-delegate facade for repair layer seams |
| `tests/test_narrative_authenticity.py` | `_apply_narrative_authenticity_layer` → facade |
| `tests/test_narrative_authenticity_aer4.py` | `_apply_narrative_authenticity_layer` → facade |
| `tests/test_n5_boundary_regressions.py` | `_apply_referent_clarity_emission_layer` → facade |
| `tests/test_referent_clarity_clause_consumption.py` | `_apply_referent_clarity_emission_layer` → facade |
| `tests/test_final_emission_answer_exposition_plan_convergence.py` | AEP layer + gate/meta → facades |
| `tests/test_final_emission_boundary_convergence.py` | Repairs + gate/meta → facades |

`tests/helpers/emission_smoke_assertions.py` was **not** expanded (per AS3 scope).

---

## Direct `final_emission_repairs` imports removed

| Suite | Removed symbol(s) | Replacement |
| --- | --- | --- |
| `test_narrative_authenticity.py` | `_apply_narrative_authenticity_layer` | `repairs_consumer_facade.apply_narrative_authenticity_layer` |
| `test_narrative_authenticity_aer4.py` | `_apply_narrative_authenticity_layer` (8 call sites) | same |
| `test_n5_boundary_regressions.py` | `_apply_referent_clarity_emission_layer` | `repairs_consumer_facade.apply_referent_clarity_emission_layer` |
| `test_referent_clarity_clause_consumption.py` | `_apply_referent_clarity_emission_layer` | same |
| `test_final_emission_answer_exposition_plan_convergence.py` | `_apply_answer_exposition_plan_layer` | `repairs_consumer_facade.apply_answer_exposition_plan_layer` |
| `test_final_emission_boundary_convergence.py` | `_apply_answer_completeness_layer`, `_apply_response_delta_layer`, `repair_fallback_behavior` | `emission_smoke_assertions` (AC/RD layers) + `repairs_consumer_facade.repair_fallback_behavior` |

**Candidate suites: zero direct `game.final_emission_repairs` imports.**

---

## Private helper imports removed or retained (with reason)

| Import | Suite | AS3 action |
| --- | --- | --- |
| `_apply_narrative_authenticity_layer` | NA tests | **Removed** → repairs facade |
| `_apply_referent_clarity_emission_layer` | N5 + clause consumption | **Removed** → repairs facade |
| `_apply_answer_exposition_plan_layer` | AEP convergence | **Removed** → repairs facade |
| `_apply_answer_completeness_layer` / `_apply_response_delta_layer` | boundary convergence | **Removed** → emission_smoke (AS2 seams) |
| `repair_fallback_behavior` | boundary convergence | **Removed** → repairs facade |
| `validate_referent_clarity` | N5, clause consumption | **Retained** — boundary validator in `final_emission_validators`, not repairs owner |
| `validate_narrative_authenticity`, `repair_narrative_authenticity_minimal`, etc. | NA tests | **Retained** — domain owner APIs in `game.narrative_authenticity` |
| `evaluate_narrative_authenticity` | NA aer4 | **Retained** — evaluator owner in `game.narrative_authenticity_eval` |
| `feg._enforce_response_type_contract`, `feg._strip_*` | boundary convergence | **Retained** — gate private seams (AS2/AS6 scope, not repairs) |
| `apply_final_emission_gate` / `read_final_emission_meta_dict` | AEP + boundary convergence | **Removed** → `apply_final_emission_gate_consumer` (AS2) |

---

## Helpers added / expanded

### New: `tests/helpers/repairs_consumer_facade.py`

| Function | Delegates to |
| --- | --- |
| `apply_narrative_authenticity_layer` | `_apply_narrative_authenticity_layer` |
| `apply_referent_clarity_emission_layer` | `_apply_referent_clarity_emission_layer` |
| `apply_answer_exposition_plan_layer` | `_apply_answer_exposition_plan_layer` |
| `repair_fallback_behavior` | `repair_fallback_behavior` |

All use lazy imports so repair module load stays in one place.

### Reused from AS2 (not modified)

- `emission_smoke_assertions.apply_final_emission_gate_consumer`
- `emission_smoke_assertions.apply_answer_completeness_layer`
- `emission_smoke_assertions.apply_response_delta_layer`

---

## Remaining downstream repair-layer consumers (outside AS3 candidates)

Direct `game.final_emission_repairs` imports still present in:

| File | Symbols | Notes |
| --- | --- | --- |
| `tests/test_final_emission_repairs.py` | owner suite | **KEEP** |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | layer imports | AS4/AS5 candidate |
| `tests/test_final_emission_validators.py` | `_apply_referent_clarity_emission_layer` | validator/repair cross-test |
| `tests/test_bounded_partial_quality.py` | `repair_fallback_behavior` | downstream |
| `tests/test_social_fallback_leak_containment.py` | `repair_fallback_behavior` | downstream |
| `tests/test_final_emission_boundary_contract.py` | lazy `repair_fallback_behavior` | integration pin |
| `tests/test_validation_layer_separation_runtime.py` | `_default_response_delta_meta` | audit/runtime |

Repairs import concentration is now: **owner suite** + **`repairs_consumer_facade.py`** + a small set of legacy downstream files above.

---

## Validation commands and results

| Command | Result |
| --- | --- |
| `pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `pytest tests/test_narrative_authenticity.py tests/test_narrative_authenticity_aer4.py -q` | **PASS** |
| `pytest tests/test_final_emission_boundary_convergence.py tests/test_final_emission_answer_exposition_plan_convergence.py -q` | **PASS** |
| `pytest tests/test_n5_boundary_regressions.py tests/test_referent_clarity_clause_consumption.py -q` | **PASS** |
| `pytest tests/test_golden_replay.py -q` | **PASS** (68) |

Combined candidate sweep: **100 tests PASS**.

---

## Recommended AS4 target

**AS4 — FEM read-path redirect and compat re-export cleanup** (from AS recon)

- Consolidate remaining downstream `read_final_emission_meta_dict` / `build_fem_runtime_lineage_events` consumers on turn-packet or smoke helpers
- Primary files: `tests/helpers/golden_replay_projection.py`, `tools/run_scenario_spine_validation.py`, high-read transcript/C4 suites
- Optional follow-up in same block: migrate `test_bounded_partial_quality.py` and `test_social_fallback_leak_containment.py` to `repairs_consumer_facade.repair_fallback_behavior`

**Do not proceed to AS4 in this block.**
