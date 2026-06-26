# CH6 BD-6 Gate Dependency Compression Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BD-6 gate dependency compression guard family into a focused helper while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bd_dependency_compression.py` | **Added** — BD-6 constants, compression rules, AST scanners, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports BD-6 helpers; retains 3 BD-6 enforcement tests as aggregator |

`tools/test_audit.py` was **not** modified (no import changes required).

## Implementation Moved

Into `tests/ownership_guard_bd_dependency_compression.py`:

**Constants / compression policy surface**

- Facade path constants (`_BD6_SMOKE_FACADE`, `_BD6_GATE_BRIDGE_FACADE`, `_BD6_REPLAY_BRIDGE_FACADE`, `_BD6_GOLDEN_REPLAY_FACADE`, `_BD6_OPENING_FACADE`)
- Forbidden FEM read symbols and owner-bucket prefix rules
- Compressed owner module set (`game.final_emission_gate`, `game.final_emission_meta`, `game.final_emission_replay_projection`)
- Full `_BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST` (52 documented paths)

**Pure validation (4 helpers)**

- `_bd6_is_forbidden_owner_bucket_symbol`
- `_bd6_facade_replacement` (routes through `_BV12A_*` facades imported from BV helper)
- `collect_gate_dependency_compression_guard_violations`
- `iter_gate_dependency_compression_guard_scan_paths`

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **3 BD-6 enforcement tests** (`test_bd6_gate_dependency_compression_*`) — still the visible governance enforcement point
- Module docstring BD-6 policy documentation (unchanged semantics)
- **BE6** scaffold-layer map imports `_BD6_GOLDEN_REPLAY_FACADE` from BD helper
- **BJ-4** facade test imports `_BD6_GATE_BRIDGE_FACADE` / `_BD6_REPLAY_BRIDGE_FACADE` from BD helper; RT/AC/RD paths remain from BV helper

All other guard families remain in central file or prior helpers (BN, BV, BV16C, BA-7, BI-8, inventory governance, etc.).

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — BD-6 synthetic and allowlist tests pass; full-repo scan produces identical violations and facade guidance messages.
- **Ownership policy unchanged** — allowlist contents, forbidden import rules, and facade replacement strings unchanged.
- **Dependency graph unchanged** — same compressed owner modules, forbidden symbols, and owner-bucket prefix detection.
- **Central ownership test still invokes the guard** — enforcement tests import and call moved helpers.
- **No pytest dependency in pure helper logic** — imports only `ast`, `pathlib`, typing, and BV facade path constants.
- **Runtime unchanged** — test-only relocation; no production module edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bd_dependency_compression; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bd6"                                         # 2 passed, 1 known pre-existing failure
py -3 -m pytest tests/test_ownership_registry.py -q -k "bj4_emission_smoke or bv7c or bv2c or bv10"    # adjacent passed except known BV2C failure
py -3 -m pytest tests/test_test_audit_tool.py -q                                                       # 45 passed
```

Pre-existing repository failures (unrelated to CH6):

- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` — compressed gate/replay-projection imports in helpers and golden-replay suites (documented since CH3).
- `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` — direct `final_emission_meta` imports in production/test modules.

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **177** (5137 → 4960) |
| Lines added to `tests/ownership_guard_bd_dependency_compression.py` | **210** |
| Helper functions extracted | **4** (+ 2 private compression helpers) |
| Enforcement tests remaining in central file | **3** BD-6 tests |
| Tests run (this block) | **57** (3 BD-6 + 9 adjacent BV/BJ-4 + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: BA-7 / AG-10 gate magnet guard family.**

Rationale:

- Cohesive constants block (`_GATE_MAGNET_GUARD_*`, `_FORBIDDEN_REPLAY_READ_SIDE_*`, `_FORBIDDEN_GATE_READ_SIDE_*`) plus `collect_gate_magnet_guard_import_violations` and `collect_gate_magnet_guard_source_fragment_violations` still embedded (~lines 348–390, 905–940).
- Three enforcement tests (`test_ba7_*`) with same scan→collect→assert pattern as extracted BN/BV/BD families.
- Does not require registry contract edits.
- Natural helper name: `tests/ownership_guard_ba_gate_magnet.py` (or similar).

Other candidates after BA-7: **BV16C terminal monkeypatch guard** (single cycle, partially delegates to `gate_thin_boundary_locks.py`), **BI-8 golden replay ownership boundary** (constants + one test), and **inventory governance orchestration** (`collect_ownership_governance_errors` and registry contract integration).
