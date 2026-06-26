# CH2 Ownership Guard Locality Pilot

## Objective

Reduce continued concentration in `tests/test_ownership_registry.py` by moving one contained ownership-governance guard family beside its domain while preserving the central test file as the enforcement aggregator.

## Guard Family Selected

**BV compatibility / fan-in cap guard family** (Cycles BV7C, BV12C, BV13C, BV14C).

Chosen because it is:

- **Coherent** — four related compat-barrel regrowth lockdowns plus smoke-monolith FI caps share AST import-scan patterns and fan-in registry constants.
- **Domain-bounded** — guards smoke-bridge barrels (`emission_smoke_assertions`, `replay_smoke_assertions`, `gate_integration_smoke`) and production compat barrels (`final_emission_text`, `social_exchange_emission`) without touching the responsibility registry contract.
- **Import-light** — pure AST scanning over repo paths; no pytest, inventory fixtures, or registry mutation.
- **Narrow assertions** — central tests remain thin orchestrators (scan → collect violations → assert empty / cap parity / synthetic fixtures).
- **Already partially localized** — BV12A domain facade paths and BV7A/BV7B extracted symbol sets naturally belong with BV guard policy.

Alternative families considered (BN gate-context, BD-6 compression) were larger and shared more cross-cutting constants with non-BV guards still embedded in the central file.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bv_compatibility.py` | **Added** — BV7C/BV12C/BV13C/BV14C constants, import guards, FI static importers, documentation corpus helper |
| `tests/test_ownership_registry.py` | **Updated** — imports guard helpers; retains 16 BV enforcement tests as aggregator |

`tools/test_audit.py` was **not** modified (no import changes required).

## Logic Moved

Into `tests/ownership_guard_bv_compatibility.py`:

**Constants / caps**

- BV7C monolith import guard allowlist, extracted-symbol→facade map, static/dynamic importer sets, FI cap (18)
- BV12C replay/gate compat barrel modules, allowlist, importer sets, FI cap (2), intentional domain hubs
- BV13C text compat barrel authorities, allowlist, importer set, FI cap (8), intentional text domain hubs
- BV14C social-exchange compat authorities, allowlist, importer set, FI cap (12), intentional domain hubs
- Supporting facade path constants and BV7A/BV7B extracted symbol frozensets (re-exported for BJ-4 / BD-6 callers)

**Pure validation**

- `collect_bv7c_smoke_monolith_import_guard_violations`
- `iter_bv7c_smoke_monolith_import_guard_scan_paths`
- `collect_bv7c_monolith_static_importers`
- `collect_bv12c_compat_barrel_import_guard_violations`
- `iter_bv12c_compat_barrel_import_guard_scan_paths`
- `collect_bv12c_compat_barrel_static_importers`
- `collect_bv13c_text_compat_import_guard_violations`
- `iter_bv13c_text_compat_import_guard_scan_paths`
- `collect_bv13c_text_compat_static_importers`
- `collect_bv14c_social_exchange_compat_import_guard_violations`
- `iter_bv14c_social_exchange_compat_import_guard_scan_paths`
- `collect_bv14c_social_exchange_compat_static_importers`
- `bv_governance_documentation_corpus` (documentation-lock helper for FI cap tests)

## Logic Remaining in test_ownership_registry.py

- **16 BV enforcement tests** (`test_bv7c_*`, `test_bv12c_*`, `test_bv13c_*`, `test_bv14c_*`) — still the visible governance enforcement point
- **BJ-4 smoke facade test** — imports BV7A/BV7B symbols and facade paths from the guard module
- **BD-6 facade replacement strings** — imports BV12A/BV7B facade paths from the guard module
- All non-BV guard families (BD-6, BV2C, BV10, BN1–BN11, BA-7, BJ70–BJ129, BU8/BU9, inventory governance, etc.)

## Compatibility Verification

Confirm:

- **Ownership enforcement unchanged** — all 17 BV/BJ-4 related tests pass with identical scan/violation/cap behavior.
- **Registry contents unchanged** — `tests/ownership_registry_contract.py` untouched.
- **Central ownership test still invokes the guard** — enforcement tests import and call moved helpers; failure messages unchanged.
- **No pytest dependency in pure helper logic** — `tests/ownership_guard_bv_compatibility.py` imports only `ast`, `pathlib`, and typing.
- **No runtime behavior changed** — test-only relocation; no production module edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bv_compatibility; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv7c or bv12c or bv13c or bv14c or bj4_emission_smoke"  # 17 passed
py -3 -m pytest tests/test_test_audit_tool.py -q                                                               # 45 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "registry_defines or derived_registry_index or allowlist_entries or governance_inventory"  # passed
```

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **479** (5618 → 5139) |
| Lines added to `tests/ownership_guard_bv_compatibility.py` | **565** |
| Guard implementations moved | **12** functions (+ 1 documentation corpus helper) |
| Enforcement tests remaining in central file | **16** BV tests (+ BJ-4 facade test uses re-exported constants) |
| Tests run (this block) | **62** (17 ownership BV/BJ-4 + 45 audit tool) |

## Remaining Concentration

**Next safest extraction candidate: BN gate-context import guard family (BN1–BN11).**

Rationale:

- Self-contained cycle markers with repeated AST import-scan structure similar to BV guards.
- Already grouped in module docstring and function naming (`collect_bn*_`, `iter_bn*_`, `test_bn*_`).
- Does not require registry contract edits.
- Slightly larger than BV per-function count but still coherent; extract to e.g. `tests/ownership_guard_bn_gate_context.py` with central aggregator tests retained.

Other candidates after BN: **BD-6 gate dependency compression** (shared facade constants already partially externalized via BV module imports) and **BU8/BU9 write-path parity** (partially in `tests/helpers/ownership_write_path_governance.py`).
