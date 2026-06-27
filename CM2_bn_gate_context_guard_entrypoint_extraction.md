# CM2 — BN Gate-Context Guard EntryPoint Extraction

Date: 2026-06-26  
Scope: test file redistribution only. No production behavior changes.

## Summary

Moved **33** BN1–BN11 gate-context / preflight structural guard pytest entrypoints from `tests/test_ownership_registry.py` into `tests/test_gate_context_ownership_guards.py`. Helper logic remains in `tests/ownership_guard_bn_gate_context.py` (docstring reference updated).

Builds on CM1 (BJ delegate closeout extraction).

## New File Created

| File | Role |
|---|---|
| `tests/test_gate_context_ownership_guards.py` | **425 lines**, **33** pytest entrypoints — owns BN1–BN11 runtime gate entry, lazy gate namespace, and gate-context preflight import regrowth locks |

Module docstring carries BN1–BN11 policy corpus (BN cycle anchors for `registry_doc = Path(__file__).read_text()` checks).

## Registry File Reduction

| Metric | After CM1 | After CM2 | CM2 Delta |
|---|---:|---:|---:|
| Lines | 1,640 | 1,239 | **−401** |
| Pytest entrypoints | 117 | 84 | **−33** |

| Metric | Original (pre-CM1) | After CM2 | Total Delta |
|---|---:|---:|---:|
| Lines | 2,357 | 1,239 | **−1,118** |
| Pytest entrypoints | 217 | 84 | **−133** |

## Tests Moved (33 total; names unchanged)

**BN1 — runtime gate entry (4):**  
`test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons`, `test_bn1_runtime_gate_entry_guard_detects_synthetic_violation`, `test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import`, `test_bn1_runtime_delegate_seam_remains_narrow`

**BN2 — lazy gate namespace (3):**  
`test_bn2_lazy_gate_namespace_allowlist_covers_scan_files`, `test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation`, `test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg`

**BN3 — preflight defaults (3):**  
`test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked`, `test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation`, `test_bn3_gate_context_avoids_direct_layer_meta_owner_imports`

**BN4 — preflight telemetry (3):**  
`test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked`, `test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation`, `test_bn4_gate_context_avoids_direct_telemetry_provenance_imports`

**BN5 — preflight upstream (3):**  
`test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked`, `test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation`, `test_bn5_gate_context_avoids_direct_upstream_attach_imports`

**BN6 — preflight turn packet (3):**  
`test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked`, `test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation`, `test_bn6_gate_context_avoids_direct_turn_packet_policy_imports`

**BN7 — preflight interaction (3):**  
`test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked`, `test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation`, `test_bn7_gate_context_avoids_direct_interaction_inspection_imports`

**BN8 — preflight strict social (3):**  
`test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked`, `test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation`, `test_bn8_gate_context_avoids_direct_strict_social_routing_imports`

**BN9 — preflight pregate text (3):**  
`test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked`, `test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation`, `test_bn9_gate_context_avoids_direct_pregate_text_imports`

**BN10 — preflight branch flags (3):**  
`test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked`, `test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation`, `test_bn10_gate_context_routes_branch_flags_through_helper`

**BN11 — preflight-only import allowlist (2):**  
`test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation`, `test_bn11_gate_context_preflight_only_import_allowlist_locked`

## Allowlists / References Updated

| File | Change |
|---|---|
| `tests/ownership_guard_bn_gate_context.py` | Module docstring — enforcement entrypoints now `tests/test_gate_context_ownership_guards.py` |
| `tests/test_ownership_registry.py` | Removed BN import block and all `test_bn*` functions; replaced 11 BN policy bullets with single pointer to `tests/test_gate_context_ownership_guards.py` |

**Not broadened:** BN scan allowlists, BJ127 harness scans, CI workflows, inventory JSON.

## Validation Commands and Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_gate_context_ownership_guards.py -q` | **33 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **81 passed, 3 failed** (pre-existing BD6/BV2C/BV10C import-guard drift — unchanged from CM1) |
| `python -m pytest tests/test_ownership_registry.py -q -k "not (bd6_gate_dependency_compression_guard_non_owners or bv2c_final_emission_meta_direct_import_guard_non_owners or bv10_read_cluster_direct_import_guard_non_owners)"` | **81 passed** |
| `python tools/test_audit.py --check` | **Failed — pre-existing drift** (+4 unrelated `tests/test_failure_dashboard_*.py` files; not introduced by CM2) |

## Failures Left Untouched

| Failure | Why untouched |
|---|---|
| `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` | Pre-existing compressed gate import violations in production/tests |
| `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` | Pre-existing direct `final_emission_meta` import violations |
| `test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades` | Pre-existing read-cluster authority import violations |
| `tools/test_audit.py --check` inventory drift | Unrelated failure-dashboard test files missing from committed governance JSON |

## Success Criteria

| Criterion | Status |
|---|---|
| BN1–BN11 coverage preserved | ✓ 33 tests in focused file |
| Registry no longer hosts BN structural guards | ✓ zero `test_bn*` entrypoints remain |
| Focused BN file passes | ✓ |
| Registry smaller / lower churn risk | ✓ −401 lines, −33 entrypoints vs post-CM1 |
