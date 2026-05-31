# Cycle R / R1-C — Gate Import Leakage Closure

**Date:** 2026-05-30  
**Status:** Complete — all targeted pytest commands green.

---

## Remaining imports found (before fix)

| Consumer | Import |
| --- | --- |
| `tests/test_diegetic_fallback_narration.py` | `from tests.test_final_emission_gate import opening_gate_attach_then_enforce_response_type_contract` |

**After fix:** no `from tests.test_final_emission_gate import` or `import tests.test_final_emission_gate` in any `tests/**/*.py` file.

**Broader scan (`from tests.test_.* import test_`):** no matches in `tests/**/*.py` (R1-B gauntlet test-function import already removed).

Other test-to-test imports remain elsewhere (e.g. `test_turn_pipeline_shared`, `test_block_s_*`) — out of R1-C scope; none reference `test_final_emission_gate`.

---

## Adapter classification

| Symbol | Classification | Rationale |
| --- | --- | --- |
| `opening_gate_attach_then_enforce_response_type_contract` | **Reusable harness helper** | Block-O seam: runs `maybe_attach_upstream_prepared_opening_fallback_payload` then `feg._enforce_response_type_contract` with default opening resolution — mirrors gate entry prep, not a gate-owner semantic assertion |
| `opening_gate_attach_then_opening_scene_safe_fallback_tuple` | **Reusable harness helper** (moved with pair) | Same Block-O pattern for `_opening_scene_safe_fallback_tuple`; gate owner and downstream should share one attach-then-helper entry |

Neither symbol encodes gate-specific assertion logic; both delegate to production helpers after upstream attach.

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/final_emission_gate_fixtures.py` | Added `_DEFAULT_OPENING_HARNESS_RESOLUTION`, `opening_gate_attach_then_opening_scene_safe_fallback_tuple`, `opening_gate_attach_then_enforce_response_type_contract` (verbatim move from gate owner) |
| `tests/test_final_emission_gate.py` | Removed adapter definitions; imports adapters from helper |
| `tests/test_diegetic_fallback_narration.py` | Import repoint: `opening_gate_attach_then_enforce_response_type_contract` from helper (no gate-module import) |

**Production code:** none modified.

---

## Import paths updated

| Consumer | New import |
| --- | --- |
| `tests/test_diegetic_fallback_narration.py` | `opening_gate_attach_then_enforce_response_type_contract` from `tests.helpers.final_emission_gate_fixtures` |
| `tests/test_final_emission_gate.py` | same module (plus `opening_gate_attach_then_opening_scene_safe_fallback_tuple`) |

---

## Tests run and results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_final_emission_gate.py tests/test_diegetic_fallback_narration.py -q` | **PASS** |
| `py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q` | **PASS** (53 items) |
| `py -3 -m pytest tests/test_gauntlet_regressions.py::test_gauntlet_slice_strict_social_narrative_authority_repair -q` | **PASS** |

---

## Coverage confirmation

- **No downstream/replay imports from gate owner:** confirmed — `rg "from tests.test_final_emission_gate import"` and `rg "import tests.test_final_emission_gate"` over `tests/**/*.py` return zero matches.
- **Assertions unchanged:** `test_final_emission_opening_repair_debug_labels_legacy_diegetic_fallback_boundary` still calls the same adapter with the same arguments and asserts the same `text`, `debug`, and provenance fields; adapter body moved verbatim.
- **Gate owner coverage unchanged:** all gate tests that used `opening_gate_attach_then_*` still call the same functions via helper import; `opening_gate_attach_then_opening_scene_safe_fallback_tuple` co-located for consistency.
- **Golden replay / gauntlet:** full golden lane and gauntlet slice passed with no test removals or narrowing.

---

## R1 closure note

R1-B residual (diegetic → gate-module adapter import) is closed. Shared opening attach-then-helper adapters now live in `tests/helpers/final_emission_gate_fixtures.py` alongside opening GM scaffold and strict-social harness fixtures.
