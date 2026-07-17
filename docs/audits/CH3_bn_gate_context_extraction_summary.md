# CH3 BN Gate-Context Guard Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BN1–BN11 gate-context guard family into a focused helper module while preserving centralized enforcement. Move implementation—not authority.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bn_gate_context.py` | **Added** — BN1–BN11 constants, import scanners, allowlists, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports BN helpers; retains 33 BN enforcement tests as aggregator |
| `tests/helpers/gate_thin_boundary_locks.py` | **Updated** — BN2–BN11 implementation removed; BJ-128/BJ-129/BV13C/BV14C/BV16C locks retained |

`tools/test_audit.py` was **not** modified (no import changes required).

## Guard Family Extracted

**BN1–BN11 gate-context and runtime entry guards** (Cycles BN1–BN11):

| Cycle | Policy surface |
| --- | --- |
| BN1 | Runtime/API modules must not import `apply_final_emission_gate` directly |
| BN2 | Stack modules must not lazy-import `game.final_emission_gate as feg` |
| BN3–BN10 | `final_emission_gate_context` and preflight helpers must not regrow forbidden direct imports |
| BN11 | Positive preflight-only import allowlist on `final_emission_gate_context` |

**Constants / caps moved**

- BN1 runtime gate-entry allowlist and replacement seams
- BN2 lazy namespace file set, retained-symbol map, forbidden markers
- BN3–BN10 gate-context owner paths, forbidden import markers, required preflight import strings, helper gate-import guards
- BN11 allowed game/stdlib import modules, required preflight imports, forbidden non-preflight modules

**Pure validation moved (21 helpers)**

- `collect_bn1_runtime_gate_entry_guard_violations`
- `iter_bn1_runtime_gate_entry_guard_scan_paths`
- `collect_bn2_lazy_gate_namespace_violations`
- `collect_bn3_gate_context_layer_meta_import_violations`
- `collect_bn4_gate_context_telemetry_import_violations`
- `collect_bn4_preflight_telemetry_helper_gate_import_violations`
- `collect_bn5_gate_context_upstream_import_violations`
- `collect_bn5_preflight_upstream_helper_gate_import_violations`
- `collect_bn6_gate_context_turn_packet_import_violations`
- `collect_bn6_preflight_turn_packet_helper_gate_import_violations`
- `collect_bn7_gate_context_interaction_import_violations`
- `collect_bn7_preflight_interaction_helper_gate_import_violations`
- `collect_bn8_gate_context_strict_social_import_violations`
- `collect_bn8_preflight_strict_social_helper_import_violations`
- `collect_bn9_gate_context_pregate_text_import_violations`
- `collect_bn9_preflight_pregate_text_helper_import_violations`
- `collect_bn10_gate_context_branch_flags_violations`
- `collect_bn10_preflight_branch_flags_helper_import_violations`
- `gate_context_import_modules`
- `collect_bn11_gate_context_preflight_only_import_violations`
- `collect_bn11_scan_logic_runtime_gate_import_violations`

## Remaining BN Logic

In `tests/test_ownership_registry.py` only:

- **33 BN enforcement tests** (`test_bn1_*` … `test_bn11_*`) — still the visible governance enforcement point
- Module docstring BN1–BN11 policy documentation (unchanged semantics)
- BN11 scan-logic self-check now reads `tests/ownership_guard_bn_gate_context.py` instead of `gate_thin_boundary_locks.py`

In `tests/helpers/gate_thin_boundary_locks.py`:

- BJ-128/BJ-129 thin gate boundary shape locks (orchestration owner only)
- BV13C/BV14C production compat-barrel forbidden marker tuples (string markers for other guards)
- BV16C terminal monkeypatch scan constants

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — all 33 BN tests pass with identical scan/violation behavior.
- **Registry contents unchanged** — `tests/ownership_registry_contract.py` untouched.
- **Central ownership test still invokes the guard** — enforcement tests import and call moved helpers; failure messages unchanged (BN11 meta-governance path strings updated to the new helper module path only).
- **No pytest dependency in pure helper logic** — `tests/ownership_guard_bn_gate_context.py` imports only `ast`, `re`, `pathlib`, and typing.
- **No imports from test modules** — helper is import-light; no circular imports with `test_ownership_registry.py`.
- **No runtime behavior changed** — test-only relocation; no production module edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bn_gate_context; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bn1 or bn2 or bn3 or bn4 or bn5 or bn6 or bn7 or bn8 or bn9 or bn10 or bn11"  # 33 passed
py -3 -m pytest tests/test_test_audit_tool.py -q                                                               # 45 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "ba7 or bv10 or bv16c" --tb=no                          # passed (BN-adjacent guards unaffected)
```

Pre-existing repository failures (unrelated to CH3): `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`, `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades`.

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **119** (5959 → 5840) |
| Lines removed from `tests/helpers/gate_thin_boundary_locks.py` | **590** (929 → 339) |
| Lines added to `tests/ownership_guard_bn_gate_context.py` | **670** |
| Guard implementations moved | **21** functions |
| Enforcement tests remaining in central file | **33** BN tests |
| Tests run (this block) | **78** (33 BN ownership + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: BV compatibility / fan-in cap guard family (BV7C, BV12C, BV13C, BV14C) plus adjacent BV2C/BV10 read-cluster guards.**

Rationale:

- Largest contiguous `collect_*` / `iter_*` implementation block still embedded in `tests/test_ownership_registry.py` (~lines 1232–1875).
- Same AST import-scan structure as the extracted BN and CH2 BV pilot families.
- Does not require registry contract edits.
- A focused `tests/ownership_guard_bv_compatibility.py` pilot already exists in-repo as the CH2 template; wiring the central file to import it is the natural follow-on.

Other candidates after that: **BD-6 gate dependency compression** (shared facade constants overlap with BV guards) and **BU8/BU9 write-path parity** (partially in `tests/helpers/ownership_write_path_governance.py`).
