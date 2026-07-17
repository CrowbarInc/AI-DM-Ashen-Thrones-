# CM7 — Cross-Domain Ownership Boundary Extraction

Date: 2026-06-27  
Scope: test file redistribution only. No production behavior changes. No allowlist broadening.

## Summary

Moved **16** cross-domain governance pytest entrypoints from `tests/test_ownership_registry.py` into three focused owner test modules. Helper logic remains in existing guard modules (`ownership_guard_gate_magnet.py`, `ownership_guard_bi8_golden_replay_boundary.py`, `ownership_write_path_governance.py`, etc.).

Builds on CM6 (inventory governance entrypoint extraction).

## New Files Created

| File | Role |
|---|---|
| `tests/test_gate_boundary_governance.py` | **399 lines**, **10** pytest entrypoints — owns BA-7/AG-10 gate magnet guards, AD-3 downstream smoke neighbor locks, AL4 legality-owner alignment, BJ-4 smoke-facade weakness, BE6 triple-layer scaffold split |
| `tests/test_replay_boundary_governance.py` | **113 lines**, **3** pytest entrypoints — owns BI-8 golden replay bridge boundary, BG-1 protected manifest parity, AO5 runtime vs acceptance projection separation |
| `tests/test_ownership_write_path_governance.py` | **74 lines**, **3** pytest entrypoints — owns BU8 BU4 CSV parity, attach_realization producer-stamp pairing, BU9/BU10 visibility fallback producer-stamp pairing |

## Registry File Reduction

| Metric | After CM6 | After CM7 | CM7 Delta |
|---|---:|---:|---:|
| Lines | 551 | 205 | **−346** |
| Pytest entrypoints | 23 | 8 | **−15** |

| Metric | Original (pre-CM1) | After CM7 | Total Delta |
|---|---:|---:|---:|
| Lines | 2,357 | 205 | **−2,152** |
| Pytest entrypoints | 217 | 8 | **−209** |

## Tests Moved (16 total; names unchanged unless noted)

**Replay/projection boundary governance (3):**  
`test_bi8_golden_replay_ownership_boundary_is_locked`, `test_bg1_protected_replay_manifest_registry_parity`, `test_ao5_runtime_and_acceptance_projection_modules_remain_separate`

**Gate / smoke-facade boundary governance (10):**  
`test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners`, `test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers`, `test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions`, `test_final_emission_gate_does_not_accumulate_read_side_projection_assertions`, `test_ad3_gate_orchestration_direct_owner_is_final_emission_gate`, `test_ad3_downstream_integration_smoke_suites_registered_as_neighbors`, `test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner`, `test_al4_legality_owners_and_smoke_facade_locked`, `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge`, `test_be6_scaffold_phrase_triple_layer_split_locked`

**Ownership write-path governance (3):**  
`test_bu8_bu4_production_ownership_write_paths_parity_locked`, `test_bu8_attach_realization_fallback_family_producer_stamp_pairing_locked`, `test_bu9_visibility_fallback_producer_stamp_pairing_locked`

**AO5 split:** registry neighbor assertions extracted into new `test_ao5_replay_projection_registry_neighbor_relationships_locked` (registry file); projection module separation stays in replay governance file.

## Remaining Tests in Registry (8)

| Test | Why retained |
|---|---|
| `test_registry_defines_all_required_groups` | Registry source-of-truth identity |
| `test_governance_committed_files_include_all_registry_paths` | Registry ↔ committed inventory integration |
| `test_derived_registry_paths_present_in_inventory` | Derived paths inventory-backed; gate direct-owner spot-check |
| `test_derived_registry_index_matches_live_registry` | Live registry index derivation |
| `test_ownership_registry_governance` | End-to-end `collect_ownership_governance_errors` integration |
| `test_allowlist_entries_have_non_empty_reasons` | Cross-file duplicate allowlist contract |
| `test_final_emission_meta_projection_read_side_ownership_boundaries` | AE4 registry neighbor/direct-owner relationship |
| `test_ao5_replay_projection_registry_neighbor_relationships_locked` | AO5 gauntlet-neighbor / meta-owner registry relationships only |

## References Updated

| File | Change |
|---|---|
| `tests/ownership_guard_gate_magnet.py` | Enforcement entrypoints → `tests/test_gate_boundary_governance.py` |
| `tests/ownership_guard_bi8_golden_replay_boundary.py` | Enforcement entrypoint → `tests/test_replay_boundary_governance.py` |
| `tests/ownership_guard_bd_dependency_compression.py` | BD-6 allowlist: AO5 import path swapped to replay governance file (swap, not expansion) |
| `tests/helpers/ownership_write_path_governance.py` | Docstring points to write-path governance test module |
| `tests/helpers/emission_smoke_assertions.py` | BE6 lock + AL4 references updated |
| `tests/helpers/*_smoke.py` (8 files) | Registry references → gate boundary governance for smoke-facade locks |
| `tests/test_gate_context_ownership_guards.py` | Docstring cross-domain pointer trimmed |
| `tests/test_compat_import_governance.py` | Docstring cross-domain pointer trimmed |
| `tests/test_gate_delegate_closeout_locks.py` | Docstring cross-domain pointer trimmed |
| `.github/workflows/convergence-checks.yml` | Pytest step runs all five governance suites |
| `tests/test_test_audit_tool.py` | CI workflow guard asserts new governance files |
| `docs/convergence_ci_inventory.md` | CI table and command references updated |

**Not broadened:** BD-6 compression allowlist paths (swap only), BJ/BN/BD/BV guard scans, inventory JSON, registry contract allowlists.

## Validation Commands and Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_ownership_registry.py -q` | **8 passed** |
| `python -m pytest tests/test_gate_boundary_governance.py -q` | **10 passed** |
| `python -m pytest tests/test_replay_boundary_governance.py -q` | **3 passed** |
| `python -m pytest tests/test_ownership_write_path_governance.py -q` | **3 passed** |
| `python tools/test_audit.py --check` | **Pass** |
| `python -m pytest tests/test_compat_import_governance.py tests/test_gate_context_ownership_guards.py tests/test_gate_delegate_closeout_locks.py tests/test_inventory_governance.py tests/test_gate_boundary_governance.py tests/test_replay_boundary_governance.py tests/test_ownership_write_path_governance.py -q` | **207 passed** |
| `python -m pytest tests/test_test_audit_tool.py -k convergence_checks_workflow -q` | **1 passed** |

## Remaining Failures

None.

## Success Criteria Met

- Cross-domain ownership policy (gate magnet, replay bridge, write-path parity, smoke facade) resides beside its actual owner modules.
- Registry file is almost exclusively registry identity, inventory integration, and registry neighbor relationship assertions (8 entrypoints, 205 lines).
- All governance suites remain green.
- `tools/test_audit.py --check` remains green.
- Ownership registry is no longer an architectural edit magnet for replay, gate, smoke, or write-path policy.

## CM Completion Recommendation

**CM series is complete for ownership-registry magnet reduction.**

The registry file has reached the intended end state: a thin identity + integration module (8 entrypoints) with all cross-domain structural guards distributed across focused governance suites:

| Suite | Entrypoints |
|---|---:|
| `test_ownership_registry.py` | 8 |
| `test_inventory_governance.py` | 35 |
| `test_gate_boundary_governance.py` | 10 |
| `test_replay_boundary_governance.py` | 3 |
| `test_ownership_write_path_governance.py` | 3 |
| `test_compat_import_governance.py` | 26 |
| `test_gate_context_ownership_guards.py` | 33 |
| `test_gate_delegate_closeout_locks.py` | 100 |

Further maintenance should add new policy to the domain-appropriate governance file first, not back into the registry. Optional follow-up (outside CM scope): refresh historical audit closeout docs and hotspot reassessment tools that still cite the pre-CM registry line counts.
