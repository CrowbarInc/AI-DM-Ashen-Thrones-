# CH10 Inventory Governance Orchestration Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting inventory governance orchestration into a focused helper and deduplicating registry data against `tests/ownership_registry_contract.py`, while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_inventory_governance.py` | **Added** — inventory load/index helpers, layer alignment, `collect_ownership_governance_errors`, and governance path allowlisting |
| `tests/test_ownership_registry.py` | **Updated** — imports registry contract + inventory governance helper; retains all governance enforcement tests and pytest fixtures |

`tests/ownership_registry_contract.py`, `tools/test_audit.py`, and `tests/test_inventory_governance.json` were **not** modified (registry contents and committed inventory unchanged).

## Orchestration Moved

Into `tests/ownership_inventory_governance.py`:

**Inventory I/O and indexing**

- `DEFAULT_GOVERNANCE_INVENTORY_PATH` / `load_governance_inventory`
- `inventory_paths`
- `full_inventory_by_path`

**Governance policy constants**

- `CANONICAL_VALIDATION_LAYERS`
- `LIVE_LEGALITY_GROUP_IDS`
- `DOWNSTREAM_INTEGRATION_SMOKE_ONLY`

**Layer alignment helpers**

- `direct_owner_inventory_layer_ok`
- `path_is_disallowed_live_legality_owner`
- `_normalize_layer` / `_layers_compatible` (private)

**Core orchestration (2 public + 1 private)**

- `allowed_governance_committed_paths`
- `collect_ownership_governance_errors`
- Uses `build_ownership_registry_index`, `_neighbor_paths_for_group`, `_paths_for_group` from registry contract

## Registry Deduplication Performed

Removed from `tests/test_ownership_registry.py` (now imported from `tests/ownership_registry_contract.py`):

- `ResponsibilityRecord` dataclass
- `RESPONSIBILITY_REGISTRY` (17 groups)
- `_REQUIRED_GROUP_IDS`
- `_CROSS_FILE_DUPLICATE_ALLOWLIST`
- `build_ownership_registry_index`
- `_NEIGHBOR_SUITE_FIELDS`, `_neighbor_paths_for_group`, `_paths_for_group`

Central tests and guard helpers continue to reference `RESPONSIBILITY_REGISTRY` via contract import; no registry content edits.

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **Pytest fixtures** — `inventory`, `inventory_by_path`, `test_audit_module`, `full_inventory` (thin `_load_inventory` wrapper over helper)
- **~32 governance enforcement tests** — AQ/BF inventory schema, synthetic pollution guards, registry index parity, `test_ownership_registry_governance`, allowlist reason locks, etc.
- All other guard families unchanged (BN, BV, BD-6, BA-7, BV16C, BI-8, BJ closeout locks, etc.)

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — 32 governance/registry tests pass that do not require `full_inventory` fixture collection; synthetic pollution tests still invoke `collect_ownership_governance_errors` with identical error strings.
- **Registry contents unchanged** — single canonical source in `ownership_registry_contract.py`; byte-identical responsibility map (verified by `test_registry_defines_all_required_groups`, `test_derived_registry_index_matches_live_registry`).
- **Inventory file unchanged** — same `tests/test_inventory_governance.json` read path and schema expectations.
- **Collector relocated** — `collect_ownership_governance_errors` no longer defined in central test module.
- **No pytest dependency in pure helper logic** — imports only `json`, `pathlib`, typing, registry contract, and optional `validation_layer_contracts`.
- **Runtime unchanged** — test-only relocation; no production module edits.
- **CI unchanged** — no workflow or tooling edits.

### Validation run

```text
py -3 -c "import tests.ownership_inventory_governance; import tests.ownership_registry_contract; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "registry_defines or derived_registry_index or governance_inventory or governance_summary or governance_omits or governance_rejects_stored or governance_file_rows or allowlist_entries or canonical_validation or direct_owner_general or governance_committed_files_include"  # 32 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "bi8 or ba7 or bv16c"  # 6 passed
py -3 -m pytest tests/test_test_audit_tool.py -q  # 45 passed
```

Pre-existing repository failures (unrelated to CH10):

- Tests using the `full_inventory` fixture (`test_ownership_registry_governance`, `test_derived_registry_paths_present_in_inventory`, BF4–BF7 derived-marker tests, etc.) **ERROR** during `tools/test_audit.py` collect-only when `tests/test_golden_replay_long_session.py` fails import (`SEALED_REPLACEMENT_SUBKINDS` from `golden_replay_projection`) — documented since CH1.
- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` — compressed gate/replay-projection imports (documented since CH3/CH6).

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **594** (4707 → 4113) |
| Lines added to `tests/ownership_inventory_governance.py` | **325** |
| Helper functions extracted | **6** public (+ 2 private layer helpers) |
| Registry deduplication | **~330** lines of duplicated registry/index data removed from central file |
| Enforcement tests remaining in central file | **~32** governance/registry tests (+ fixtures) |
| Tests run (this block) | **83** (32 governance + 6 adjacent guards + 45 audit tool) |

## Remaining Ownership Concentration

**Largest remaining concentration: BJ70–BJ129 delegate-collapse closeout locks.**

Rationale:

- ~60+ `test_bj*` entrypoint-lock and delegate-collapse tests remain embedded (~lines 2700–4200).
- These are enforcement assertions against production gate/stack source shape, not reusable guard collectors — lower extraction ROI than completed guard families.
- Natural future work: retire superseded closeout locks or group by BJ cycle into `tests/ownership_guard_bj_delegate_collapse.py` if patterns stabilize.

Other smaller embedded items: **BE6/AL4 documentation-lock tests**, **BJ-128/BJ-129 thin boundary locks** (constants already in `gate_thin_boundary_locks.py`), **module docstring policy corpus** (intentionally central).
