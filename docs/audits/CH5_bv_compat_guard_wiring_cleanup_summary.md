# CH5 BV Compat Guard Wiring Cleanup

## Objective

Complete CH2/CH4 BV helper extraction by removing duplicate BV7C/BV12C/BV13C/BV14C implementation still embedded in `tests/test_ownership_registry.py` and wiring all central BV enforcement tests to `tests/ownership_guard_bv_compatibility.py`.

## Files Modified

| File | Change |
| --- | --- |
| `tests/test_ownership_registry.py` | **Updated** — removed duplicate BV7C–BV14C constants and scanners; expanded helper imports; FI-cap doc locks use `bv_governance_documentation_corpus` |
| `tests/ownership_guard_bv_compatibility.py` | **Unchanged** — remains sole BV implementation owner (BV2C/BV10 + BV7C–BV14C) |

`tools/test_audit.py` was **not** modified (no import changes required).

## Duplicate Logic Removed

From `tests/test_ownership_registry.py`:

**Constants / allowlists (~137 lines)**

- BV7C monolith import guard allowlist, extracted-symbol→facade map, static/dynamic importer sets, FI cap
- BV12C replay/gate compat barrel modules, allowlist, importer sets, FI cap, intentional domain hubs, scan roots
- BV13C text compat authorities, allowlist, importer set, FI cap, intentional text domain hubs, scan roots
- BV14C social-exchange compat authorities, allowlist, importer set, FI cap, intentional domain hubs, scan roots
- Duplicate BV7A/BV7B extracted symbol frozensets and BV12A/BD6 facade path strings (now imported for BJ-4/BD-6 callers)

**Pure validation (~366 lines)**

- `collect_bv7c_smoke_monolith_import_guard_violations`
- `iter_bv7c_smoke_monolith_import_guard_scan_paths`
- `collect_bv7c_monolith_static_importers`
- `collect_bv12c_compat_barrel_import_guard_violations`
- `iter_bv12c_compat_barrel_import_guard_scan_paths`
- `collect_bv12c_compat_barrel_static_importers`
- `collect_bv13c_text_compat_import_guard_violations`
- `iter_bv13c_text_compat_import_guard_scan_paths`
- `collect_bv13c_text_compat_static_importers`
- `_bv14c_social_exchange_compat_authority_guidance`
- `collect_bv14c_social_exchange_compat_import_guard_violations`
- `iter_bv14c_social_exchange_compat_import_guard_scan_paths`
- `collect_bv14c_social_exchange_compat_static_importers`

## Helper APIs Reused

Central tests now import from `tests/ownership_guard_bv_compatibility.py`:

**Constants** — `_BV7C_*`, `_BV12C_*`, `_BV13C_*`, `_BV14C_*`, `_BV7A_*`, `_BV7B_*`, `_BV12A_*`, `_BD6_RT/AC/RD_SMOKE_FACADE`

**Scanners** — all `collect_bv7c_*` / `collect_bv12c_*` / `collect_bv13c_*` / `collect_bv14c_*` and matching `iter_*` helpers

**Documentation corpus** — `bv_governance_documentation_corpus` for BV12C/BV13C/BV14C FI-cap domain-hub doc locks (hub strings live in helper module after extraction)

## Remaining BV Logic in test_ownership_registry.py

- **22 BV enforcement tests** — still the visible governance enforcement point:
  - 6 BV2C/BV10 read-cluster tests (CH4)
  - 16 BV7C/BV12C/BV13C/BV14C compat-barrel tests (CH5 wiring)
  - 1 BV16C terminal monkeypatch test (still embedded)
- **BJ-4 facade test** — imports BV7A/BV7B/BV12A/BD6 constants from helper
- **BD-6 gate dependency compression** — imports `_BV12A_*` facades from helper for replacement strings
- Module docstring BV2C–BV14C policy documentation (unchanged semantics)
- BJ-4-only constants (`_BJ4_SMOKE_FACADE_*`) remain local (not BV guard implementation)

## Validation Results

```text
py -3 -c "import tests.ownership_guard_bv_compatibility; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv7c or bv12c or bv13c or bv14c"         # 16 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv2c or bv10"                              # 5 passed, 1 known pre-existing failure
py -3 -m pytest tests/test_test_audit_tool.py -q                                                     # 45 passed
```

Pre-existing repository failure (unrelated to CH5): `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` — 7 violations in `final_emission_passive_scene_pressure.py`, `final_emission_referential_clarity.py`, and `tests/test_cf3_raw_normalized_fem_field_matrix.py`.

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` (CH5 block) | **485** (5622 → 5137) |
| Lines in `tests/ownership_guard_bv_compatibility.py` | **796** (unchanged) |
| Duplicate guard implementations removed | **13** functions (+ 1 private guidance helper) |
| Duplicate constant blocks removed | **4** cycles (BV7C–BV14C) + shared BV7A/BV7B/BV12A facade paths |
| Enforcement tests remaining in central file | **22** BV tests (+ BJ-4 uses helper constants) |
| Tests run (this block) | **67** (16 BV7C–BV14C + 6 BV2C/BV10 + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: BD-6 gate dependency compression guard family.**

Rationale:

- Largest contiguous non-BV `collect_*` / `iter_*` block still embedded in `tests/test_ownership_registry.py` (~BD-6 constants + scanners).
- Shared facade path constants already partially externalized via BV helper imports.
- Does not require registry contract edits.

Other candidates after BD-6: **BV16C terminal monkeypatch guard** (single cycle, partially uses `gate_thin_boundary_locks.py`), **BA-7 gate magnet guard**, and **BU8/BU9 write-path parity** (partially in `tests/helpers/ownership_write_path_governance.py`).
