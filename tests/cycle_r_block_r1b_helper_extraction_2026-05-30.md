# Cycle R / R1-B — Final Emission Gate Fixture Extraction

**Date:** 2026-05-30  
**Status:** Complete — all targeted pytest commands green.

---

## Files changed

| File | Change |
| --- | --- |
| **`tests/helpers/final_emission_gate_fixtures.py`** | **Created** — shared gate harness fixtures + gauntlet callable |
| `tests/test_final_emission_gate.py` | Removed moved definitions; imports from helper; thin wrapper for strict-social NA case |
| `tests/test_upstream_response_repairs.py` | Import repoint |
| `tests/test_diegetic_fallback_narration.py` | Import repoint (still imports `opening_gate_attach_then_enforce_response_type_contract` from gate owner module — out of R1-B scope) |
| `tests/test_api_narration_path_selection.py` | Import repoint |
| `tests/test_run_scenario_spine_validation.py` | Lazy import repoint inside Cycle-I test |
| `tests/test_golden_replay.py` | Import repoint |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | Import repoint |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | Import repoint |
| `tests/test_block_u_finalize_stack_divergence.py` | Import repoint |
| `tests/test_final_emission_boundary_convergence.py` | Import repoint |
| `tests/test_gauntlet_regressions.py` | Test-function import replaced with shared callable |

**Production code:** none modified.

---

## Definitions moved

From `tests/test_final_emission_gate.py` → `tests/helpers/final_emission_gate_fixtures.py`:

| Old name (gate module) | New public name (helper module) |
| --- | --- |
| `_runner_strict_bundle()` | `runner_strict_bundle()` |
| `_opening_gm_output()` | `opening_gm_output()` |
| `_opening_validation_context()` | `opening_validation_context()` |
| `_response_type_contract(required)` | `response_type_contract(required)` |
| `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` (unchanged) |

**Added (gauntlet decouple):**

| Symbol | Purpose |
| --- | --- |
| `run_strict_social_motive_overclaim_gate_case(monkeypatch)` | Shared body for strict-social NA + speaker stability case (assertions unchanged) |
| `_na_contract_for_resolution(resolution)` | Private helper inside fixtures module (supports callable only) |

**Left in gate owner module:** `_DEFAULT_OPENING_HARNESS_RESOLUTION`, `opening_gate_attach_then_enforce_response_type_contract`, all orchestration tests and gate-specific helpers.

---

## Import paths updated

| Consumer | New import |
| --- | --- |
| `test_final_emission_gate.py` | `from tests.helpers.final_emission_gate_fixtures import (...)` |
| `test_upstream_response_repairs.py` | `opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` |
| `test_diegetic_fallback_narration.py` | same + gate `opening_gate_attach_then_enforce_response_type_contract` |
| `test_api_narration_path_selection.py` | same |
| `test_run_scenario_spine_validation.py` | lazy import inside `test_cycle_i_opening_attribution_*` |
| `test_golden_replay.py` | `runner_strict_bundle`, `opening_gm_output` |
| `test_block_s/t/u_*.py`, `test_final_emission_boundary_convergence.py` | `runner_strict_bundle` |
| `test_gauntlet_regressions.py` | `run_strict_social_motive_overclaim_gate_case` |

**Removed:** all `from tests.test_final_emission_gate import (_opening_gm_output|_runner_strict_bundle|EXPECTED_...)` from downstream/replay suites.

**Removed:** `from tests.test_final_emission_gate import test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker` (gauntlet).

---

## Gauntlet test-function import replacement

**Before:**

```python
from tests.test_final_emission_gate import test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker
test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker(monkeypatch)
```

**After:**

- **`tests/helpers/final_emission_gate_fixtures.py`:** `run_strict_social_motive_overclaim_gate_case(monkeypatch)` holds the full assertion body.
- **`tests/test_final_emission_gate.py`:** `test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker` → thin wrapper calling the helper.
- **`tests/test_gauntlet_regressions.py`:** calls `run_strict_social_motive_overclaim_gate_case(monkeypatch)` directly.

No test modules import pytest test functions from other test modules for this case anymore.

---

## Tests run and results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_final_emission_gate.py tests/helpers/ -q` | **PASS** |
| `py -3 -m pytest tests/test_upstream_response_repairs.py tests/test_diegetic_fallback_narration.py tests/test_api_narration_path_selection.py -q` | **PASS** |
| `py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q` | **PASS** (53 items) |
| `py -3 -m pytest tests/test_block_s_speaker_local_rebind_equivalence.py tests/test_block_t_speaker_relocation_shadow_equivalence.py tests/test_block_u_finalize_stack_divergence.py tests/test_final_emission_boundary_convergence.py -q` | **PASS** |
| `py -3 -m pytest tests/test_run_scenario_spine_validation.py::test_cycle_i_opening_attribution_survives_prepared_payload_gate_lineage_and_diagnostics -q` | **PASS** |
| `py -3 -m pytest tests/test_gauntlet_regressions.py::test_gauntlet_slice_strict_social_narrative_authority_repair -q` | **PASS** |

---

## Coverage confirmation

- **Assertions:** unchanged — strict-social case body moved verbatim into `run_strict_social_motive_overclaim_gate_case`; gate test delegates without altering checks.
- **Fixture semantics:** unchanged — fixture builders copied without logic edits; same NPC ids, curated facts, expected fallback prose, and strict-social resolution shape.
- **Golden replay:** full `-m golden_replay` lane passed (53 tests); no replay structural-invariant tests removed or narrowed.
- **Production code:** not touched.

---

## Residual (intentional, out of R1-B scope)

- `tests/test_diegetic_fallback_narration.py` still imports `opening_gate_attach_then_enforce_response_type_contract` from `tests/test_final_emission_gate.py` (gate-owned adapter, not a moved fixture).
- Future R1 follow-up could relocate gate adapter helpers if test-to-test imports should be fully eliminated.
