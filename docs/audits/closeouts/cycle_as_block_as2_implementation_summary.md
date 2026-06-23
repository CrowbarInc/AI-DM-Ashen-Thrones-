# Cycle AS2 — Downstream Gate Import Thinning Implementation Summary

**Date:** 2026-06-04  
**Block:** AS2 — Route registered downstream suites through `emission_smoke_assertions` facade  
**Behavior change:** None (import/facade relocation only)

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/emission_smoke_assertions.py` | Added AS2 consumer integration + layer seam facades |
| `tests/test_turn_pipeline_shared.py` | `read_debug_notes_from_turn_payload` → `read_turn_debug_notes` |
| `tests/test_answer_completeness_rules.py` | Gate/meta imports → smoke facade |
| `tests/test_response_delta_requirement.py` | Gate/meta imports → smoke facade |
| `tests/test_interaction_continuity_repair.py` | Gate/meta imports → smoke facade |
| `tests/test_diegetic_fallback_narration.py` | `feg.apply_final_emission_gate` + meta read → facade |

---

## Direct gate imports removed (target suites)

| Suite | Before | After |
| --- | --- | --- |
| `test_turn_pipeline_shared.py` | — (no gate import) | — |
| `test_answer_completeness_rules.py` | `apply_final_emission_gate`, `_apply_answer_completeness_layer`, `validate_answer_completeness` from `game.final_emission_gate` | `apply_final_emission_gate_consumer`, `apply_answer_completeness_layer`, `validate_answer_completeness` from smoke facade |
| `test_response_delta_requirement.py` | 7 symbols from `game.final_emission_gate` | Same behavior via smoke facade wrappers |
| `test_interaction_continuity_repair.py` | `apply_final_emission_gate` | `apply_final_emission_gate_consumer` |
| `test_diegetic_fallback_narration.py` | `import game.final_emission_gate as feg` | `apply_final_emission_gate_consumer` |

**Target suites now have zero direct `from game.final_emission_gate` / `import game.final_emission_gate` imports.**

---

## Direct meta-reader imports removed or retained

| Import | Suite | AS2 action |
| --- | --- | --- |
| `read_debug_notes_from_turn_payload` | `test_turn_pipeline_shared.py` | **Removed** → `read_turn_debug_notes` (smoke facade) |
| `read_final_emission_meta_dict` | `test_interaction_continuity_repair.py` | **Removed** → FEM from `apply_final_emission_gate_consumer` |
| `read_final_emission_meta_dict` | `test_diegetic_fallback_narration.py` | **Removed** → FEM from `apply_final_emission_gate_consumer` |
| `final_emission_meta_from_output` | AC/RD integration tests | **Removed** (bundled into `apply_final_emission_gate_consumer` return tuple) |

Meta reads in target suites now go through `emission_smoke_assertions` only. The facade module retains a single internal import of `read_final_emission_meta_dict` / `read_debug_notes_from_turn_payload`.

---

## Helpers added / expanded (`emission_smoke_assertions.py`)

**Integration:**
- `read_turn_debug_notes(payload)` — turn-packet debug notes for HTTP smoke
- `apply_final_emission_gate_consumer(...)` → `(output, fem)`
- `STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH` — monkeypatch path constant

**Consumer-owned layer seams (delegate to gate, lazy import):**
- `validate_answer_completeness`
- `apply_answer_completeness_layer`
- `apply_response_delta_layer`
- `skip_answer_completeness_layer` / `skip_response_delta_layer`
- `strict_social_answer_pressure_rd_contract_active`
- `validate_response_delta` / `inspect_response_delta_failure`

---

## Remaining downstream direct consumers (outside AS2 scope)

Target suites are clean. Repo-wide, other non-owner tests still import `game.final_emission_gate` directly (examples):

- Equivalence harnesses: `test_block_s_*`, `test_block_t_*`, `test_block_u_*` (use `strict_social_harness` + direct `feg` for layer monkeypatch)
- Transcript/regression neighbors: `test_narration_transcript_regressions.py`, `test_c4_narrative_mode_live_pipeline.py`, …
- Owner suites: `test_final_emission_gate.py`, `test_final_emission_opening_fallback.py`, …

Gate import concentration for registered downstream consumers is now in **`tests/helpers/emission_smoke_assertions.py`** (single module boundary).

---

## Validation commands and results

| Command | Result |
| --- | --- |
| `pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `pytest tests/test_turn_pipeline_shared.py -q` | **PASS** (69) |
| `pytest tests/test_answer_completeness_rules.py tests/test_response_delta_requirement.py tests/test_interaction_continuity_repair.py tests/test_diegetic_fallback_narration.py -q` | **PASS** (89) |
| `pytest tests/test_golden_replay.py -q` | **PASS** (68) |

---

## Recommended AS3 target

**AS3 — Repairs-layer downstream decoupling**

Stop non-owner suites from importing `_apply_*` repair layers directly from `game.final_emission_repairs`; route through gate owner tests or boundary validators. Primary candidates from AS recon:

- `tests/test_narrative_authenticity.py`, `tests/test_narrative_authenticity_aer4.py`
- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_answer_exposition_plan_convergence.py`
- `tests/test_n5_boundary_regressions.py`, `tests/test_referent_clarity_clause_consumption.py`

Optional AS2 follow-up (not AS3): delete zero-importer `tests/helpers/final_emission_gate_fixtures.py` transitional shim.
