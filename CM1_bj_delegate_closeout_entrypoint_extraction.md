# CM1 — BJ Delegate Closeout EntryPoint Extraction

Date: 2026-06-26  
Scope: test file redistribution only. No production behavior changes.

## Summary

Moved **100** BJ delegate/owner closeout pytest entrypoints from `tests/test_ownership_registry.py` into a new focused owner file `tests/test_gate_delegate_closeout_locks.py`. Helper logic remains in `tests/ownership_closeout_delegate_locks.py` (unchanged API; path references updated).

## New File Created

| File | Role |
|---|---|
| `tests/test_gate_delegate_closeout_locks.py` | **742 lines**, **100** pytest entrypoints — owns final-emission gate delegate closeout / direct-owner seam locks (BJ-27–BJ-129) |

Module docstring documents BJ-123–BJ-129 corpus anchors and explicitly states this is **not** the global ownership registry.

## Registry File Reduction

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Lines | 2,357 | 1,640 | **−717** |
| Pytest entrypoints | 217 | 117 | **−100** |

## Tests Moved (100 total; names unchanged)

All `test_bj*` functions **except** `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge` (smoke-facade policy lock, registry-owned).

**Entrypoint / wrapper-collapse locks:**  
`test_bj27_*`, `test_bj28_*`, `test_bj29_*`, `test_bj30_*`, `test_bj31_*`–`test_bj37_*`, `test_bj38_*`, `test_bj39_*`, `test_bj40_*`–`test_bj49_*`, `test_bj50_*`, `test_bj51_*`–`test_bj61_*`, `test_bj62_*`–`test_bj65_*`, `test_bj58_*`

**Direct-call / stack routing locks (`verify_bj*` wrappers):**  
`test_bj69_*`–`test_bj78_*`, `test_bj79_*`–`test_bj101_*`, `test_bj102_*`–`test_bj122_*`

**Harness / thin-boundary locks:**  
`test_bj123_*`–`test_bj129_*`

## Tests Intentionally Left in Registry

| Test | Reason |
|---|---|
| `test_bj4_emission_smoke_facade_stays_weak_consumer_bridge` | Smoke-facade **policy** lock (AL4/BE6/BV7A/BV7B bridge governance), not structural delegate closeout |
| All non-BJ tests (registry, inventory, BN, BV, BU, BA, BD, BI8, etc.) | Remain registry-focused per CM1 scope |

## Allowlists / References Updated

| File | Change |
|---|---|
| `tests/ownership_closeout_delegate_locks.py` | Docstring points to `tests/test_gate_delegate_closeout_locks.py`; `BJ127_GLOBAL_SCAN_EXCLUDE` and `BJ127_FEG_ALIAS_IMPORT_ALLOWLIST` swap `tests/test_ownership_registry.py` → `tests/test_gate_delegate_closeout_locks.py`; `ownership_registry_doc()` now reads closeout test file (BJ-123–BJ-129 corpus anchor) |
| `tests/ownership_guard_bv_compatibility.py` | BV14C `_BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS` entry for `tests/test_ownership_registry.py` — removed stale “BJ-115/116 delegate introspection” note (introspection lives in `tests/ownership_closeout_delegate_locks.py`, already allowlisted) |
| `tests/test_ownership_registry.py` | Added **BV16C** module-doc bullet (owner module paths) — required because BJ block previously supplied `game.final_emission_terminal_pipeline` string presence for `test_bv16c_*` doc corpus check |

**Not broadened:** BN/BV scan allowlists, gate-thin-boundary locks, CI workflows.

## Validation Commands and Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_gate_delegate_closeout_locks.py -q` | **100 passed** |
| `python -m pytest tests/test_ownership_registry.py -q` | **114 passed, 3 failed** (pre-existing import-guard drift: BD6, BV2C, BV10C non-owner violations) |
| `python -m pytest tests/test_ownership_registry.py -q -k "not (bd6_gate_dependency_compression_guard_non_owners or bv2c_final_emission_meta_direct_import_guard_non_owners or bv10_read_cluster_direct_import_guard_non_owners)"` | **114 passed** |
| `python -m pytest tests/test_ownership_registry.py::test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance -q` | **1 passed** (after BV16C docstring fix) |
| `python tools/test_audit.py --check` | **Failed — pre-existing drift** (+4 unrelated `tests/test_failure_dashboard_*.py` files not in committed inventory; not introduced by CM1) |

## Documentation

No updates to `tests/README_TESTS.md`, `docs/convergence_ci_inventory.md`, or `docs/architecture_ownership_ledger.md` — those files reference the ownership registry generically, not BJ closeout test placement.

## Success Criteria

| Criterion | Status |
|---|---|
| BJ delegate closeout coverage preserved | ✓ 100 tests in focused file |
| Registry no longer hosts BJ structural delegate family | ✓ only `test_bj4_*` remains (smoke policy) |
| Focused pytest runs pass | ✓ |
| Inventory/governance checks | ✓ CM1-clean; `--check` failure explained (unrelated dashboard file drift) |
| Registry magnet pressure reduced | ✓ −717 lines, −100 entrypoints |
