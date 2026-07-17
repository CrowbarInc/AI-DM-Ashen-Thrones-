# CH4 BV Read-Cluster Guard Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BV2C/BV10C read-cluster guard family into the existing BV compatibility helper while preserving centralized enforcement. Move implementation—not authority.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bv_compatibility.py` | **Extended** — BV2C/BV10C constants, import scanners, allowlists, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports BV2C/BV10 helpers; retains 6 enforcement tests as aggregator |

`tools/test_audit.py` was **not** modified (no import changes required).

## BV2C/BV10 Logic Moved

Into `tests/ownership_guard_bv_compatibility.py`:

**Constants / allowlists**

- BV2C production write-owner game module set (21 modules)
- BV2C test direct-import allowlist (2 paths)
- BV2C read facades (`final_emission_meta_read`, `final_emission_owner_bucket_views`)
- BV10C read-cluster authority modules (meta_read, owner_bucket_views, ownership_schema)
- BV10C facade routing targets (attribution_read_views, ownership_projection_views, observability_attribution_read, replay_fem_read_smoke)
- BV10C game allowlist (10 modules) and test allowlist (10 paths)

**Pure validation (6 helpers)**

- `_bv2c_meta_import_replacement`
- `collect_bv2c_final_emission_meta_import_violations`
- `iter_bv2c_final_emission_meta_import_guard_scan_paths`
- `_bv10_read_cluster_import_replacement`
- `collect_bv10_read_cluster_direct_import_guard_violations`
- `iter_bv10_read_cluster_direct_import_guard_scan_paths`

## Logic Remaining in test_ownership_registry.py

- **6 BV2C/BV10 enforcement tests** — still the visible governance enforcement point:
  - `test_bv2c_final_emission_meta_direct_import_allowlist_entries_have_non_empty_reasons`
  - `test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation`
  - `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`
  - `test_bv10_read_cluster_direct_import_allowlist_entries_have_non_empty_reasons`
  - `test_bv10_read_cluster_direct_import_guard_detects_synthetic_violation`
  - `test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades`
- Module docstring BV2C/BV10C policy documentation (unchanged semantics)
- **BV7C/BV12C/BV13C/BV14C** compat-barrel guards still embedded (CH2 helper exists but central file not yet wired)
- All other non-BV guard families (BD-6, BN1–BN11, BA-7, BJ70–BJ129, BU8/BU9, inventory governance, BV16C, etc.)

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — BV10 tests pass; BV2C synthetic/allowlist tests pass; BV2C full-repo scan behavior identical (same violations, same messages).
- **Registry contents unchanged** — `tests/ownership_registry_contract.py` untouched.
- **Central ownership test still invokes the guard** — enforcement tests import and call moved helpers; failure messages unchanged.
- **Same scanned paths** — `game/**/*.py` and `tests/**/*.py` via shared `iter_bv2c_*` / `iter_bv10_*` scan roots.
- **Same importer detection** — AST `ImportFrom` / `Import` walk with identical allowlist gates.
- **No pytest dependency in pure helper logic** — `tests/ownership_guard_bv_compatibility.py` imports only `ast`, `pathlib`, and typing.
- **No runtime behavior changed** — test-only relocation; no production module edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bv_compatibility; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv2c or bv10"                          # 5 passed, 1 known pre-existing failure
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv7c or bv12c or bv13c or bv14c"         # 16 passed
py -3 -m pytest tests/test_test_audit_tool.py -q                                                 # 45 passed
```

Pre-existing repository failure (unrelated to CH4): `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` — 7 violations in `final_emission_passive_scene_pressure.py`, `final_emission_referential_clarity.py`, and `tests/test_cf3_raw_normalized_fem_field_matrix.py`.

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` (BV2C/BV10 block) | **~226** |
| Lines added to `tests/ownership_guard_bv_compatibility.py` (BV2C/BV10 block) | **~231** |
| Guard implementations moved | **6** functions (+ 2 private replacement helpers) |
| Enforcement tests remaining in central file | **6** BV2C/BV10 tests |
| Tests run (this block) | **67** (6 BV2C/BV10 + 16 BV7C–BV14C + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: complete CH2 wiring — wire central file to existing BV7C/BV12C/BV13C/BV14C helpers already in `tests/ownership_guard_bv_compatibility.py`.**

Rationale:

- Largest contiguous duplicate `collect_bv*` / `iter_bv*` block still embedded in `tests/test_ownership_registry.py` (~lines 1245–1610).
- Helper module already contains identical implementations from CH2 pilot; central file retains duplicate copies.
- Same AST import-scan structure as extracted BN and BV2C/BV10 families.
- Does not require registry contract edits.

Other candidates after that: **BD-6 gate dependency compression** (shared facade constants overlap with BV guards), **BV16C terminal monkeypatch guard**, and **BU8/BU9 write-path parity** (partially in `tests/helpers/ownership_write_path_governance.py`).
