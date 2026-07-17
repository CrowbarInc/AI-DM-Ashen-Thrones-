# CF5 — Projection Test Failure Locality Split

## Executive Summary

The monolithic `tests/test_golden_replay_projection.py` (31 tests covering six projection layers) was decomposed into **seven focused ownership suites** plus a **thin assembler smoke module** (2 tests). All original assertions were preserved; one additional envelope smoke test documents required assembler output keys.

**Projection Failure Locality (primary metric):** Failures in registry, manifest, governance, fallback, speaker, presence, and metadata layers now localize to named test modules instead of a shared 900-line file. CF1–CF4 contract matrices (178 tests) provide first-line unit coverage for precedence, routing, FEM normalization, and trace nest behavior.

**Runtime behavior unchanged.** No production code was modified.

---

## Projection Test Inventory

| Test Module | Projection Layer | Classification | Failure Locality |
|-------------|------------------|----------------|------------------|
| `test_golden_replay_projection.py` | Assembler | assembler smoke | High — adapter wiring + envelope keys |
| `test_golden_replay_projection_registry.py` | Extraction registry, representation | registry | High — registry/extraction parity |
| `test_golden_replay_projection_manifest.py` | Manifest generation | manifest | High — manifest drift |
| `test_golden_replay_projection_governance.py` | Facade API, deprecated aliases | governance | High — packaging/boundary |
| `test_golden_replay_projection_fallback_integration.py` | Fallback family via assembler | fallback integration | Medium-high — dual-family + trace/scaffold |
| `test_golden_replay_projection_speaker_integration.py` | Speaker parity via assembler | speaker integration | Medium-high — BX3 parity statuses |
| `test_golden_replay_projection_presence_integration.py` | Presence/unavailable via assembler | integration | Medium — BL3 exact locks (CF2 unit overlap) |
| `test_golden_replay_projection_metadata.py` | FEM/sanitizer/response-delta | metadata | Medium-high — field-family projection |
| `test_golden_replay_projection_modules.py` | Module split, import graph | governance | High — CE5 packaging |
| `test_cf1_speaker_projection_precedence.py` | Speaker precedence | unit | High |
| `test_cf1_fallback_family_precedence.py` | Fallback precedence | unit | High |
| `test_cf1_route_and_trace_precedence.py` | Route/trace source | unit | High |
| `test_cf1_runtime_lineage_precedence.py` | Payload vs FEM lineage | unit | High |
| `test_cf2_protected_field_routing.py` | Defaults/unavailable/presence | unit | High |
| `test_cf3_raw_normalized_fem_field_matrix.py` | Raw/normalized FEM | unit | High |
| `test_cf4_trace_nest_dotted_path_contract.py` | Trace nest dotted paths | unit | High |
| `test_golden_replay_fallback_opening_projection.py` | Opening fallback family | fallback | Medium |
| `test_golden_replay_fallback_sealed_projection.py` | Sealed fallback | fallback | Medium |
| `test_golden_replay_fallback_visibility_projection.py` | Visibility fallback | fallback | Medium |
| `test_golden_replay_fallback_upstream_projection.py` | Upstream prepared | fallback | Medium |
| `test_golden_replay_fallback_sanitizer_projection.py` | Sanitizer fallback | fallback | Medium |
| `test_golden_replay_fallback_upstream_fast_projection.py` | Upstream fast | fallback | Medium |
| `test_golden_replay_fallback_acceptance_matrix.py` | Split-owner matrix | governance/integration | Medium |
| `test_golden_replay_structural_invariants.py` | End-to-end protected | integration | Low — broad gate |
| `test_bx_speaker_identity_golden_replay.py` | BX protected speaker | integration | Low |
| `test_final_emission_meta.py` | FEM metadata/normalization | metadata | High |
| `test_final_emission_speaker_observation.py` | Runtime speaker stamp | speaker | High |

Shared support: `tests/helpers/golden_replay_projection_test_support.py` (manifest loader, speaker payloads, rich fixture builder).

---

## Ownership Matrix

| Projection Behavior | Canonical Owner | First-Line Test | Integration Test | Governance Test |
|---------------------|-----------------|-----------------|----------------|-----------------|
| Assembler wiring | `project_turn_observation` | `test_golden_replay_projection.py` | `test_bl2_*` in metadata | `test_golden_replay_projection_modules.py` |
| Extraction registry parity | `_PROTECTED_EXTRACTION_SPECS` | `test_golden_replay_projection_registry.py` | AK5 representation | AO1 in registry |
| Manifest parity | `render_protected_observation_manifest_section` | `test_golden_replay_projection_manifest.py` | — | manifest + bl5 governance |
| Facade / deprecated aliases | `golden_replay_projection.py` facade | — | — | `test_golden_replay_projection_governance.py` |
| Dual fallback family | `project_replay_fallback_family_from_fem` | `test_cf1_fallback_family_precedence.py` | `test_golden_replay_projection_fallback_integration.py` | — |
| Speaker selection | `_resolve_selected_speaker_id` | `test_cf1_speaker_projection_precedence.py` | speaker_integration BX3 | — |
| Speaker parity | `project_speaker_projection_parity` | CF1 + unit in speaker_integration | BX3 integration | — |
| Route kind | `_resolve_route_kind` | `test_cf1_route_and_trace_precedence.py` | metadata bl2 | — |
| Trace dotted paths | trace nest assembly | `test_cf4_trace_nest_dotted_path_contract.py` | fallback complex / metadata bl2 | — |
| Defaults/unavailable | `_build_projection_status` | `test_cf2_protected_field_routing.py` | `test_golden_replay_projection_presence_integration.py` | — |
| Raw/normalized FEM presence | `normalize_fem_for_replay_acceptance` | `test_cf3_raw_normalized_fem_field_matrix.py` | presence_integration bl3 | — |
| FEM flat metadata | `_extract_fem_flat_observed_fields` | `test_cf3_*` | `test_golden_replay_projection_metadata.py` | — |
| Sanitizer lineage | sanitizer extractors | — | metadata sanitizer tests | `test_golden_replay_fallback_sanitizer_projection.py` |
| Response delta (non-protected) | `project_turn_observation` FEM reads | — | metadata response_delta test | — |
| Opening/sealed/visibility fallback | runtime + acceptance | family `test_golden_replay_fallback_*` | same | acceptance_matrix |

---

## Failure Locality Findings

| Behavior | Current Failure (post-CF5) | Desired Failure | Notes |
|----------|----------------------------|-----------------|-------|
| Registry/extraction drift | `test_golden_replay_projection_registry.py` | Same | Was mixed with manifest/speaker |
| Manifest out of date | `test_golden_replay_projection_manifest.py` | Same | Isolated from behavioral tests |
| Dual-family precedence | `test_cf1_fallback_family_precedence.py` | Unit first, integration second | Integration in fallback_integration |
| Speaker parity status | `test_cf1_*` or speaker_integration | Unit before BX E2E | BX protected remains last gate |
| Presence/unavailable | `test_cf2_*` | Unit first | BL3 integration locks exact lists |
| Trace leaf extraction | `test_cf4_*` | Unit first | Complex test in fallback_integration |
| FEM normalization | `test_cf3_*` | Unit first | Meta tests in final_emission_meta |
| Deprecated facade alias | `test_golden_replay_projection_governance.py` | Governance only | No behavioral coupling |
| Broad multi-layer drift | `test_golden_replay_structural_invariants.py` | Last resort | Unchanged end-to-end gate |

**Removed coupling:** A fallback-family unit change no longer fails manifest or speaker tests in the same file. A manifest refresh failure no longer appears alongside sanitizer lineage assertions.

---

## Test Changes

### Files created

| File | Tests | Source |
|------|-------|--------|
| `tests/helpers/golden_replay_projection_test_support.py` | (helper) | Extracted shared payloads |
| `tests/test_golden_replay_projection_registry.py` | 4 | AK5, AO1, BL2 registry |
| `tests/test_golden_replay_projection_manifest.py` | 2 | Manifest parity |
| `tests/test_golden_replay_projection_governance.py` | 1 | BL5 closeout |
| `tests/test_golden_replay_projection_fallback_integration.py` | 7 | Dual-family + direct seam + complex |
| `tests/test_golden_replay_projection_speaker_integration.py` | 6 | BX3 parity |
| `tests/test_golden_replay_projection_presence_integration.py` | 3 | BL3 presence locks |
| `tests/test_golden_replay_projection_metadata.py` | 7 | BL2 representative, FEM, sanitizer, response-delta |

### Files reduced

| File | Before | After |
|------|--------|-------|
| `tests/test_golden_replay_projection.py` | 31 tests | 2 smoke tests |

### Assertions

- **Moved:** 30 test functions with identical assertions (reorganized only)
- **Added:** 1 assembler envelope smoke test
- **Retained:** All BL/AK/AO/BX/BL5 assertions verbatim in new modules

---

## Coverage Verification

Post-split run (all projection + CF suites):

```
pytest tests/test_golden_replay_projection*.py tests/test_cf*.py tests/test_golden_replay_projection_modules.py
→ 234 tests passed
```

| Coverage type | Status |
|---------------|--------|
| Behavioral assertions | Preserved (30 moved + 1 new smoke) |
| Governance (`test_golden_replay_projection_modules.py`) | Unchanged |
| CF1–CF4 contract matrices | Unchanged (178 tests) |
| Fallback family files | Unchanged (39 tests in 7 modules) |
| Protected structural invariants | Unchanged (integration gate) |

---

## Behavior Changes

**None.** Test file organization only.

---

## Remaining Risks

1. **`test_golden_replay_projection_fallback_integration.py::test_ak5_complex_projection_contracts_remain_locked`** still crosses fallback + trace + scaffold — intentional integration lock; unit layers covered by CF1/CF4.

2. **`test_golden_replay_projection_metadata.py::test_bl2_representative_projected_observed_turns_unchanged`** remains a multi-field integration lock — acceptable as metadata smoke; CF2/CF4 cover sub-behaviors.

3. **Fallback family files** (`test_golden_replay_fallback_*`) still cross runtime FEM → acceptance → classifier in some cases — out of CF5 scope but noted for future decomposition.

4. **`.bak` oracle** in `test_golden_replay_projection_modules.py` — temporary governance coupling (pre-existing).

5. **CI/doc references** to `test_golden_replay_projection.py` as sole contract file — still valid for smoke; full suite now spans multiple modules.

---

## Recommended Next Block

**Proceed with CF6 unchanged** (if planned: classifier evidence bridge or synthetic row governance), with priorities:

1. Decompose `test_ak5_complex_projection_contracts_remain_locked` into CF1/CF4 unit tests only if redundancy becomes maintenance drag (optional; not required now).
2. Add `pytest` markers (`projection_registry`, `projection_manifest`, etc.) for selective CI locality — optional ergonomics.
3. Retire `.bak` facade oracle when explicit contract fixtures replace backup parity (pre-existing CF discovery recommendation).

CF5 acceptance criteria met:

- [x] Every projection owner has a focused first-line test (CF1–CF4 + split suites)
- [x] Broad monolith reduced to thin assembler smoke (2 tests)
- [x] Governance tests remain independent
- [x] Failure locality improved via module-per-owner split
- [x] Runtime behavior unchanged
- [x] Overall test coverage preserved (234 passing projection/CF tests)
