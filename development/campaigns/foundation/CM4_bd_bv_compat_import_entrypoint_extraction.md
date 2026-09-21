# CM4 — BD/BV Compatibility Guard EntryPoint Extraction

Date: 2026-06-27  
Scope: test file redistribution only. No production behavior changes. No guard allowlist broadening.

## Summary

Moved **26** BD/BV structural import-guard pytest entrypoints from `tests/test_ownership_registry.py` into `tests/test_compat_import_governance.py`. Helper logic remains in `tests/ownership_guard_bd_dependency_compression.py`, `tests/ownership_guard_bv_compatibility.py`, and `tests/ownership_guard_bv16c_terminal_monkeypatch.py` (docstring and allowlist references updated).

Builds on CM3 (BD/BV import-guard drift stabilization).

## New File Created

| File | Role |
|---|---|
| `tests/test_compat_import_governance.py` | **433 lines**, **26** pytest entrypoints — owns BD-6 gate dependency compression, BV2C/BV10C read-cluster routing, BV7C smoke monolith caps, BV12C–BV14C compat barrel regrowth locks, and BV16C terminal monkeypatch governance |

Module docstring carries BD/BV policy corpus (cycle anchors for `registry_doc = Path(__file__).read_text()` doc-lock checks).

## Registry File Reduction

| Metric | After CM3 | After CM4 | CM4 Delta |
|---|---:|---:|---:|
| Lines | 1,239 | 819 | **−420** |
| Pytest entrypoints | 84 | 58 | **−26** |

| Metric | Original (pre-CM1) | After CM4 | Total Delta |
|---|---:|---:|---:|
| Lines | 2,357 | 819 | **−1,538** |
| Pytest entrypoints | 217 | 58 | **−159** |

## Tests Moved (26 total; names unchanged)

**BD-6 — gate dependency compression (3):**  
`test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons`, `test_bd6_gate_dependency_compression_guard_detects_synthetic_violation`, `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`

**BV2C — final_emission_meta direct import (3):**  
`test_bv2c_final_emission_meta_direct_import_allowlist_entries_have_non_empty_reasons`, `test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation`, `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`

**BV10C — read-cluster facade routing (3):**  
`test_bv10_read_cluster_direct_import_allowlist_entries_have_non_empty_reasons`, `test_bv10_read_cluster_direct_import_guard_detects_synthetic_violation`, `test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades`

**BV7C — smoke monolith import lockdown (4):**  
`test_bv7c_smoke_monolith_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv7c_smoke_monolith_import_guard_detects_synthetic_violation`, `test_bv7c_smoke_monolith_import_guard_non_owners_route_through_family_facades`, `test_bv7c_emission_smoke_assertions_concentration_locked`

**BV12C — compat barrel regrowth (4):**  
`test_bv12c_compat_barrel_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv12c_compat_barrel_import_guard_detects_synthetic_violation`, `test_bv12c_compat_barrel_import_guard_non_owners_route_through_domain_facades`, `test_bv12c_compat_barrel_fi_cap_locked`

**BV13C — text compat barrel regrowth (4):**  
`test_bv13c_text_compat_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv13c_text_compat_import_guard_detects_synthetic_violation`, `test_bv13c_text_compat_import_guard_non_owners_route_through_authorities`, `test_bv13c_text_compat_fi_cap_locked`

**BV14C — social-exchange compat barrel regrowth (4):**  
`test_bv14c_social_exchange_compat_import_guard_allowlist_entries_have_non_empty_reasons`, `test_bv14c_social_exchange_compat_import_guard_detects_synthetic_violation`, `test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities`, `test_bv14c_social_exchange_compat_fi_cap_locked`

**BV16C — terminal monkeypatch governance (1):**  
`test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance`

## Allowlists / References Updated

| File | Change |
|---|---|
| `tests/ownership_guard_bd_dependency_compression.py` | Module docstring — enforcement entrypoints now `tests/test_compat_import_governance.py`; **BD-6 allowlist unchanged** (`tests/test_ownership_registry.py` retained for AO5 replay-projection import in registry) |
| `tests/ownership_guard_bv_compatibility.py` | Module docstring; BV2C/BV10C/BV12C/BV13C/BV14C allowlists and BV7C dynamic-importer set — `tests/test_ownership_registry.py` **replaced by** `tests/test_compat_import_governance.py` (swap, not expansion) |
| `tests/ownership_guard_bv16c_terminal_monkeypatch.py` | Module docstring; scan allowlist — registry path swapped for compat governance path |
| `tests/helpers/gate_thin_boundary_locks.py` | Comment references updated to compat governance file |
| `tools/bv10c_generate_audit_docs.py` | Prose reference updated |
| `tools/bv12c_generate_audit_docs.py` | ALLOWLIST path swapped |
| `tools/bv13c_generate_audit_docs.py` | ALLOWLIST path swapped |
| `tools/bv14c_generate_audit_docs.py` | ALLOWLIST + GOVERNANCE path swapped |
| `tests/test_ownership_registry.py` | Removed BD/BV import block and all moved test functions; replaced BD–BV16C policy bullets with pointer to `tests/test_compat_import_governance.py` |

**Not broadened:** BD-6 compression allowlist paths, BJ delegate scans, BN guard scans, CI workflows, inventory JSON.

## Validation Commands and Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_compat_import_governance.py -q` | **26 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **58 passed** |
| `python -m pytest tests/test_gate_context_ownership_guards.py tests/test_gate_delegate_closeout_locks.py -q` | **133 passed** (33 + 100) |
| `python tools/test_audit.py --check` | **Failed — pre-existing unrelated drift** (+4 `tests/test_failure_dashboard_*.py` files missing from committed inventory; not introduced by CM4) |

## Failures Left Untouched

| Item | Why |
|---|---|
| `tools/test_audit.py --check` inventory drift | Pre-existing failure-dashboard module additions (`test_failure_dashboard_drift.py`, `test_failure_dashboard_orchestration.py`, `test_failure_dashboard_recurrence.py`, `test_failure_dashboard_stability.py`) not in committed `tests/test_inventory_governance.json`; documented per CM3 handoff, out of CM4 scope |

## Success Criteria Met

- BD/BV structural import-guard coverage intact (26/26 in focused file).
- `tests/test_ownership_registry.py` no longer hosts BD/BV compatibility/import guard entrypoints.
- New focused compatibility governance file passes.
- Registry file remains green (58/58).
- No guard weakening or allowlist expansion (registry ↔ compat path swaps only where enforcement moved).
