# CM8 — Ownership Registry Magnet Reduction Closeout

Date: 2026-06-27  
Scope: documentation, anti-regression guard, and closeout verification. No production behavior changes.

## Summary

Verified that `tests/test_ownership_registry.py` is a stable **registry identity** module after CM1–CM7 extractions. Added placement documentation, a narrow scope guard, and confirmed all governance validation remains green.

**CM magnet-reduction series: COMPLETE.**

## Final Registry Shape

| Metric | After CM7 | After CM8 |
|---|---:|---:|
| Lines | 205 | **257** |
| Pytest entrypoints | 8 | **9** |

CM8 added one anti-regression test (`test_registry_module_scope_guard_identity_only`) and expanded the module docstring with explicit registry-identity ownership language. No domain policy tests were added.

### Remaining tests (all registry identity)

| Test | Category |
|---|---|
| `test_registry_defines_all_required_groups` | Required registry groups |
| `test_governance_committed_files_include_all_registry_paths` | Inventory integration |
| `test_derived_registry_paths_present_in_inventory` | Derived registry index + inventory integration |
| `test_derived_registry_index_matches_live_registry` | Derived registry index |
| `test_ownership_registry_governance` | Governance errors (end-to-end) |
| `test_allowlist_entries_have_non_empty_reasons` | Allowlist reason validation |
| `test_final_emission_meta_projection_read_side_ownership_boundaries` | Stable registry neighbor/direct-owner relationship (AE4) |
| `test_ao5_replay_projection_registry_neighbor_relationships_locked` | Stable registry neighbor relationship (AO5) |
| `test_registry_module_scope_guard_identity_only` | Anti-regression scope guard (CM8) |

**Flagged as acceptable (not domain policy):** AE4 and AO5 tests assert `RESPONSIBILITY_REGISTRY` neighbor/direct-owner relationships only — no structural import guards, source-fragment scans, or projection module enforcement.

**No remaining domain-policy tests** (gate magnet, smoke facade AST scans, replay export guards, write-path parity, compat import caps, BN guards, BJ delegate locks) remain in the registry file.

## Extracted Governance Owner Files

| File | Entrypoints | Domain |
|---|---:|---|
| `tests/test_ownership_registry.py` | 9 | Registry identity + inventory integration |
| `tests/test_inventory_governance.py` | 35 | Committed inventory JSON shape |
| `tests/test_gate_boundary_governance.py` | 10 | Gate magnet, smoke facade, downstream neighbors |
| `tests/test_replay_boundary_governance.py` | 3 | Replay bridge, manifest parity, projection split |
| `tests/test_ownership_write_path_governance.py` | 3 | BU4 CSV / producer-stamp pairing |
| `tests/test_compat_import_governance.py` | 26 | BD/BV compat barrel / import-cap guards |
| `tests/test_gate_context_ownership_guards.py` | 33 | BN gate-context / preflight guards |
| `tests/test_gate_delegate_closeout_locks.py` | 100 | BJ delegate closeout / thin-boundary locks |

Helper modules remain import-light beside their domains (`tests/ownership_guard_*.py`, `tests/helpers/ownership_write_path_governance.py`, etc.).

## Anti-Regression Guard (CM8)

Added `test_registry_module_scope_guard_identity_only` in `tests/test_ownership_registry.py`:

- **Explicit test-name allowlist** — unexpected `test_*` functions fail with guidance to use focused governance files.
- **Module docstring checks** — requires `registry identity only` statement and pointers to all focused governance owner modules.
- **No line-count lock** — avoids brittle size enforcement; test-name allowlist is the primary guard.

## Documentation Updated

| File | Change |
|---|---|
| `tests/README_TESTS.md` | Governance suite placement table (CM8); BA-7 pointer; maintenance loop command |
| `docs/convergence_ci_inventory.md` | New *Governance suite placement (CM8)* subsection |
| `docs/architecture_ownership_ledger.md` | BA-7 enforcement pointer; new *Test Governance Suite Placement* section |

## Future Placement Rule

When adding new governance tests:

1. **Default:** land in the focused owner module for the policy domain (see placement tables in README, convergence CI inventory, and architecture ledger).
2. **Registry file:** only for registry identity — new group ids, derived index parity, inventory integration, allowlist contract, or stable neighbor/direct-owner relationship locks that read `RESPONSIBILITY_REGISTRY` without structural enforcement.
3. **Explicit allowlist update:** if a new registry-identity test is genuinely required, add its name to `_REGISTRY_IDENTITY_TEST_NAMES` in `tests/test_ownership_registry.py` and document why in the test docstring.

## Validation Results

| Command | Result |
|---|---|
| `python -m pytest tests/test_ownership_registry.py -q` | **9 passed** |
| `python -m pytest tests/test_gate_boundary_governance.py tests/test_replay_boundary_governance.py tests/test_ownership_write_path_governance.py -q` | **16 passed** |
| `python -m pytest tests/test_inventory_governance.py tests/test_compat_import_governance.py tests/test_gate_context_ownership_guards.py tests/test_gate_delegate_closeout_locks.py -q` | **194 passed** |
| `python tools/test_audit.py --check` | **Pass** |

## CM Series Totals (pre-CM1 → post-CM8)

| Metric | Pre-CM1 | Post-CM8 | Delta |
|---|---:|---:|---:|
| Registry lines | 2,357 | 257 | **−2,100** |
| Registry entrypoints | 217 | 9 | **−208** |

## Governance Magnet Pressure — Resolved

| Signal | Pre-CM | Post-CM8 |
|---|---|---|
| Registry as cross-domain policy magnet | Yes — hosted BN/BD/BV/BJ/BA/AD/BI/AO/AL/BE/BG/BU guards | **No** — identity + integration only |
| Domain policy beside domain owners | Partial | **Yes** — 7 focused governance test modules |
| Accidental re-bloat prevention | None | **Yes** — test-name allowlist scope guard |
| Contributor placement guidance | Scattered / outdated pointers | **Yes** — README, CI inventory, architecture ledger |

**Judgment:** Governance Magnet Pressure on `tests/test_ownership_registry.py` is **resolved**. The file is no longer an architectural edit magnet; future structural/import/replay/write-path guards should not return there by default.

## CM Completion Status

**COMPLETE.** No further CM extraction blocks are required for ownership-registry magnet reduction. Optional follow-up (outside CM): refresh historical audit closeout docs and hotspot reassessment tools that still cite pre-CM registry line counts.
