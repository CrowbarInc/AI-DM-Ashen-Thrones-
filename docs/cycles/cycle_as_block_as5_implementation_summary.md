# Cycle AS5 — Test-to-Test Import and Convergence Assert Retirement Implementation Summary

**Date:** 2026-06-04  
**Block:** AS5 — Extract shared contracts to helpers; thin FEM reads in high-read non-owner suites  
**Behavior change:** None (import/facade/fixture relocation only)

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/boundary_semantic_repair_fixtures.py` | **New** — FEM flag asserts + dialogue policy scaffold |
| `tests/helpers/repairs_consumer_facade.py` | Added `apply_response_delta_layer`, `apply_social_response_structure_layer` |
| `tests/helpers/narrative_mode_validator_fixtures.py` | Added `build_validator_narrative_mode_contract` |
| `tests/helpers/fallback_behavior_fixtures.py` | AS5 docstring (import-from-here, not test modules) |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | Repairs facade + boundary fixtures + smoke FEM reads |
| `tests/test_fallback_behavior_gate.py` | FEM reads → `final_emission_meta_from_output` |
| `tests/test_social_exchange_emission.py` | FEM reads → smoke facade (12 call sites) |
| `tests/test_lead_lifecycle_block3_transcript_regression.py` | FEM reads → smoke facade (4 call sites) |
| `tests/test_narrative_mode_output_validator.py` | `_contract` delegates to validator fixtures helper |
| `tests/test_fallback_behavior_repairs.py` | FEM read → smoke facade (adjacent downstream) |
| `tests/test_narration_transcript_regressions.py` | **No code change** — already on `fallback_behavior_fixtures` + smoke FEM (AS4) |

---

## Test-to-test imports removed

**Primary AS5 targets had zero `from tests.test_*` imports at block start** (resolved in AS1/AS4 or never present in these files).

| Prior anti-pattern (recon) | AS5 status |
| --- | --- |
| `test_narration_transcript_regressions` → `test_fallback_behavior_gate._fallback_contract` | **Already retired** — uses `tests/helpers/fallback_behavior_fixtures` |
| `test_*` → `test_narrative_mode_output_validator._minimal_ctir_continuation` | **Already retired** — uses `narrative_mode_validator_fixtures` |
| `test_answer_completeness_rules` → `test_social_escalation._session_with_pressure` | **Already retired** — uses `social_escalation_fixtures.session_with_pressure` |

**Convergence coupling retired (module-local → helpers):**

| Extracted from | Moved to |
| --- | --- |
| `test_final_emission_boundary_no_semantic_repair` (`_FEM_SEMANTIC_REPAIR_FLAG_KEYS`, `_assert_fem_*`, `_dialogue_policy_with_social_structure`) | `boundary_semantic_repair_fixtures.py` |
| `test_narrative_mode_output_validator` (`_contract` → `build_narrative_mode_contract`) | `narrative_mode_validator_fixtures.build_validator_narrative_mode_contract` |

No new test-to-test imports introduced.

---

## Helpers extracted or created

### New: `tests/helpers/boundary_semantic_repair_fixtures.py`

| Symbol | Purpose |
| --- | --- |
| `FEM_SEMANTIC_REPAIR_FLAG_KEYS` | Shared flag tuple for boundary integration tests |
| `assert_fem_has_no_semantic_repair_success_flags` | Convergence assert used after gate output |
| `dialogue_policy_with_social_structure` | Stable `response_policy` scaffold for SRS boundary cases |

### Expanded: `tests/helpers/repairs_consumer_facade.py`

| Function | Delegates to |
| --- | --- |
| `apply_response_delta_layer` | `_apply_response_delta_layer` |
| `apply_social_response_structure_layer` | `_apply_social_response_structure_layer` |

(Existing: `apply_narrative_authenticity_layer`, `repair_fallback_behavior`, …)

### Expanded: `tests/helpers/narrative_mode_validator_fixtures.py`

| Function | Purpose |
| --- | --- |
| `build_validator_narrative_mode_contract` | Non-owner wrapper around `build_narrative_mode_contract` |

### Reused (unchanged implementations, clarified ownership)

- `tests/helpers/fallback_behavior_fixtures.py` — `fallback_contract`, `answer_contract`
- `tests/helpers/emission_smoke_assertions.py` — `final_emission_meta_from_output`, `response_type_contract`
- `tests/helpers/social_escalation_fixtures.py` — `session_with_pressure`

---

## FEM reads removed or retained (with reason)

| Suite | AS5 action |
| --- | --- |
| `test_fallback_behavior_gate.py` | **Removed** `read_final_emission_meta_dict` (6 sites) → `final_emission_meta_from_output` |
| `test_social_exchange_emission.py` | **Removed** (12 sites) → smoke facade |
| `test_lead_lifecycle_block3_transcript_regression.py` | **Removed** (4 sites) → smoke facade |
| `test_final_emission_boundary_no_semantic_repair.py` | **Removed** (6 sites) → smoke facade |
| `test_fallback_behavior_repairs.py` | **Removed** (1 site) → smoke facade |
| `test_narration_transcript_regressions.py` | **Retained** smoke path from AS4 — no further change |
| `test_narrative_mode_output_validator.py` | **Retained** owner FEM projection imports (`NARRATIVE_MODE_OUTPUT_FEM_KEYS`, merge helpers) — no `read_final_emission_meta_dict` usage |

Meta read concentration for targeted non-owner suites is now **`emission_smoke_assertions.final_emission_meta_from_output`** (single delegate to `read_final_emission_meta_dict`).

---

## Repair imports migrated or retained (with reason)

| Suite | Before | After |
| --- | --- | --- |
| `test_final_emission_boundary_no_semantic_repair.py` | `game.final_emission_repairs._apply_*` (3 layer seams) | `repairs_consumer_facade.apply_*` |

| Retained in owner / intentional |
| --- | --- |
| `tests/test_final_emission_repairs.py` | Direct repairs imports — **KEEP** (owner) |
| `test_final_emission_boundary_no_semantic_repair.py` | `feg._apply_referent_clarity_pre_finalize` | **KEEP** — gate private seam for referent pre-finalize pin (AS6 candidate) |

---

## Validation commands and results

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `python -m pytest tests/test_narration_transcript_regressions.py -q` | **PASS** (41) |
| `python -m pytest tests/test_fallback_behavior_gate.py tests/test_narrative_mode_output_validator.py -q` | **PASS** (29) |
| `python -m pytest tests/test_social_exchange_emission.py tests/test_lead_lifecycle_block3_transcript_regression.py -q` | **PASS** when run sequentially* |
| `python -m pytest tests/test_final_emission_boundary_no_semantic_repair.py -q` | **PASS** (9) |
| `python -m pytest tests/test_golden_replay.py -q` | **PASS** (68) |

\*Combined parallel run hit Windows `codex_pytest_tmp` `FileExistsError` (fixture teardown race); individual suite runs passed.

Additional spot-check: `test_social_exchange_emission.py` alone — **PASS** (88).

---

## Recommended AS6 target

**AS6 — Equivalence harness gate decoupling (block S/T/U)** (from AS recon)

- Refactor `test_block_s_*`, `test_block_t_*`, `test_block_u_*` and `speaker_relocation_shadow_harness` / `post_speaker_finalize_probe` to depend on public gate entry + observation probes, not private `feg._*` layer monkeypatch lists
- Retire remaining test-to-test imports: `test_block_u` / `test_block_t` / `test_golden_replay` → `test_block_s_speaker_local_rebind_equivalence` (extract shared equivalence seeds to `tests/helpers/`)
- Continue FEM read thinning in remaining non-owner suites (e.g. `test_fallback_overwrite_containment.py`, `test_dialogue_plan_final_emission_gate.py`)

**Do not proceed to AS6 in this block.**
