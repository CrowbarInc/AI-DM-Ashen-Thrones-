# CH7 Gate Magnet Guard Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BA-7 / AG-10 gate magnet guard family into a focused helper while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_gate_magnet.py` | **Added** — BA-7 / AG-10 constants, path resolution, AST import scanner, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports gate-magnet helpers; retains 4 enforcement tests as aggregator |
| `tests/ownership_registry_contract.py` | **Updated** — removed duplicated `gate_magnet_guard_paths` (now owned by gate-magnet helper; uses contract registry) |

`tools/test_audit.py` was **not** modified (no import changes required).

## Implementation Moved

Into `tests/ownership_guard_gate_magnet.py`:

**Constants / magnet policy surface**

- `_GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS` / `_GATE_MAGNET_GUARD_EXCLUDED_PATHS`
- `_FORBIDDEN_REPLAY_READ_SIDE_IMPORT_PREFIXES`
- `_FORBIDDEN_GATE_READ_SIDE_SOURCE_FRAGMENTS`

**Pure validation (3 public + 2 private helpers)**

- `gate_magnet_guard_paths` (resolves gate-layer direct owners from `ownership_registry_contract.RESPONSIBILITY_REGISTRY`)
- `collect_gate_magnet_guard_import_violations`
- `collect_gate_magnet_guard_source_fragment_violations`
- `_collect_import_module_paths` (private AST import scanner)
- `_import_matches_forbidden_prefix` (private prefix matcher)

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **4 enforcement tests** — `test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners`, `test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers`, `test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions`, `test_final_emission_gate_does_not_accumulate_read_side_projection_assertions` (AG-10)
- Module docstring BA-7 / AG-10 policy documentation (unchanged semantics)

All other guard families remain in central file or prior helpers (BN, BV, BD-6, BV16C, BI-8, inventory governance, BJ closeout locks, etc.).

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — all 4 BA-7 / AG-10 tests pass; identical 6 guarded gate-layer direct-owner paths.
- **Ownership rules unchanged** — exclusion group ids, excluded paths, forbidden import prefixes, and source fragments unchanged.
- **Scan coverage unchanged** — same gate-layer direct owners scanned; same FEM meta / gauntlet / classifier neighbors excluded.
- **Diagnostics unchanged** — violation message strings preserved verbatim.
- **Central ownership test still invokes the guard** — enforcement tests import and call moved helpers.
- **No pytest dependency in pure helper logic** — imports only `ast`, typing, and registry contract data.
- **Runtime unchanged** — test-only relocation; no production module edits.
- **CI unchanged** — no workflow or tooling edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_gate_magnet; import tests.ownership_registry_contract; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "ba7 or final_emission_gate_does_not_accumulate"  # 4 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "ba7 or final_emission_gate_does_not_accumulate or bd6 or bv16c or registry_defines"  # 8 passed, 1 known pre-existing failure
py -3 -m pytest tests/test_test_audit_tool.py -q                                                       # 45 passed
```

Pre-existing repository failures (unrelated to CH7):

- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` — compressed gate/replay-projection imports in helpers and golden-replay suites (documented since CH3/CH6).

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **107** (4960 → 4853) |
| Lines added to `tests/ownership_guard_gate_magnet.py` | **125** |
| Helper functions extracted | **3** public (+ 2 private scanners) |
| Enforcement tests remaining in central file | **4** BA-7 / AG-10 tests |
| Tests run (this block) | **57** (4 BA-7/AG-10 + 8 adjacent + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: BV16C terminal monkeypatch guard.**

Rationale:

- Cohesive scan/collect pair (`collect_bv16c_terminal_delegate_monkeypatch_violations`, `iter_bv16c_terminal_monkeypatch_scan_paths`) still embedded (~lines 836–890).
- Constants already live in `tests/helpers/gate_thin_boundary_locks.py`; central file only hosts thin orchestration.
- Single enforcement test (`test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance`).
- Natural helper name: `tests/ownership_guard_bv16c_terminal_monkeypatch.py` (or extend `gate_thin_boundary_locks.py`).

**Largest remaining implementation family still embedded: inventory governance orchestration** (`collect_ownership_governance_errors`, `_allowed_governance_committed_paths`, registry index integration, and the duplicated `RESPONSIBILITY_REGISTRY` block still in the central file ~lines 533–830). This is broader than a single cycle guard and should follow smaller guard extractions (BV16C, BI-8).

Other candidates: **BI-8 golden replay ownership boundary** (constants + one documentation-lock test), **BJ70–BJ129 delegate-collapse closeout locks** (large test concentration, not reusable guard logic).
