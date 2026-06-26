# CH9 BI-8 Golden Replay Ownership Boundary Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BI-8 golden replay ownership boundary guard family into a focused helper while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bi8_golden_replay_boundary.py` | **Added** — BI-8 constants, target path registry, `__all__` parser, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports BI-8 helpers; retains 1 enforcement test as aggregator |

`tools/test_audit.py`, `tests/helpers/golden_replay.py`, `tests/helpers/golden_replay_projection.py`, and `tests/helpers/protected_replay_registry.py` were **not** modified (no runtime/helper behavior changes).

## Implementation Moved

Into `tests/ownership_guard_bi8_golden_replay_boundary.py`:

**Constants / ownership boundary policy surface**

- `BI8_GOLDEN_REPLAY_TARGETS` (3 governed paths: stub, harness, API facade)
- `BI8_GOLDEN_REPLAY_OWNED_EXPORTS` (10 allowed API exports)
- `BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS` (9 subsystem legality preset exports)
- `BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS` (21 source-fragment rules with owner reasons)
- `BI8_GOLDEN_REPLAY_DOCUMENTATION_PHRASES` (11 required ownership-note phrases)

**Pure validation (6 public + 1 private helper)**

- `load_bi8_golden_replay_target_sources`
- `parse_bi8_golden_replay_api_exports`
- `collect_bi8_golden_replay_documentation_phrase_violations`
- `collect_bi8_golden_replay_owned_export_violations`
- `collect_bi8_golden_replay_forbidden_export_violations`
- `collect_bi8_golden_replay_forbidden_source_fragment_violations`
- `_module_all_exports` (private literal `__all__` AST parser)

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **1 enforcement test** — `test_bi8_golden_replay_ownership_boundary_is_locked` (load → collect → assert)
- Module docstring BI-8 / golden replay policy documentation (unchanged semantics)

Adjacent golden replay governance tests (`test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner`, `test_bg1_protected_replay_manifest_registry_parity`) remain in the central file unchanged.

All other guard families remain in central file or prior helpers (BN, BV compat, BD-6, BA-7, BV16C, inventory governance, BJ closeout locks, etc.).

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — BI-8 test passes; same 3 target paths, owned/forbidden export sets, and source-fragment rules.
- **Golden replay ownership policy unchanged** — no edits to `golden_replay.py`, `golden_replay_api.py`, or `test_golden_replay.py` content.
- **Protected replay policy unchanged** — BG-1 manifest parity test unaffected.
- **Boundary detection unchanged** — identical documentation phrase checks, `__all__` export subset rules, and helper/API fragment scans.
- **Diagnostics unchanged** — violation message strings preserved verbatim (aggregated under single assert prefix).
- **Central ownership test still invokes the guard** — enforcement test imports and calls moved helpers.
- **No pytest dependency in pure helper logic** — imports only `ast`, `pathlib`, and typing.
- **Runtime unchanged** — test-only relocation; no production module edits.
- **CI unchanged** — no workflow or tooling edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bi8_golden_replay_boundary; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bi8 or bg1 or ad3_golden_replay"              # 3 passed
py -3 -m pytest tests/test_test_audit_tool.py -q                                                          # 45 passed
```

Pre-existing repository failures (unrelated to CH9):

- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` — compressed gate/replay-projection imports in helpers and golden-replay suites (documented since CH3/CH6).

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **90** (4797 → 4707) |
| Lines added to `tests/ownership_guard_bi8_golden_replay_boundary.py` | **179** |
| Helper functions extracted | **6** public (+ 1 private `__all__` parser) |
| Enforcement tests remaining in central file | **1** BI-8 test |
| Tests run (this block) | **48** (3 BI-8/adjacent + 45 audit tool) |

## Remaining Ownership Concentration

**Next extraction candidate: inventory governance orchestration.**

Rationale:

- Largest cohesive implementation family still embedded: `collect_ownership_governance_errors`, `_allowed_governance_committed_paths`, inventory schema validation, and the duplicated `RESPONSIBILITY_REGISTRY` block (~lines 490–780, 1400+).
- Broadest concentration; should be decomposed carefully (registry deduplication via `ownership_registry_contract` import first, then governance error collector helper).
- Natural helper name: `tests/ownership_guard_inventory_governance.py` (or split registry wiring from inventory schema checks).

Other candidates: **BJ70–BJ129 delegate-collapse closeout locks** (large test concentration, ~60+ entrypoint-lock tests, not reusable guard logic), **registry contract deduplication** (wire central file to import `ownership_registry_contract` instead of duplicating registry data — high leverage, lower risk than full governance extraction).
