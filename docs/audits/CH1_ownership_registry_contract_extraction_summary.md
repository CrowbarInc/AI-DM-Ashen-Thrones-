# CH1 Ownership Registry Contract Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the ownership registry contract into an import-light module while preserving all behavior. Separate registry **data** from registry **enforcement** so tooling no longer imports a pytest test module for canonical responsibility maps.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_registry_contract.py` | **Added** — canonical registry contract (import-light, no pytest) |
| `tests/test_ownership_registry.py` | **Updated** — imports registry contract; retains enforcement tests and guards |
| `tools/test_audit.py` | **Updated** — imports `build_ownership_registry_index` and `_CROSS_FILE_DUPLICATE_ALLOWLIST` from contract module |

## Registry Items Moved

Moved from `tests/test_ownership_registry.py` into `tests/ownership_registry_contract.py`:

- `ResponsibilityRecord` dataclass
- `RESPONSIBILITY_REGISTRY` (17 responsibility groups)
- `_REQUIRED_GROUP_IDS`
- `_CROSS_FILE_DUPLICATE_ALLOWLIST` (13 cross-file duplicate test-name entries)
- `_NEIGHBOR_SUITE_FIELDS`
- `_neighbor_paths_for_group()`
- `_paths_for_group()`
- `build_ownership_registry_index()`
- `gate_magnet_guard_paths()` plus `_GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS` / `_GATE_MAGNET_GUARD_EXCLUDED_PATHS`

## Remaining Responsibilities in test_ownership_registry.py

`tests/test_ownership_registry.py` remains the canonical **enforcement** suite:

- Governance inventory schema and committed-artifact validation (`collect_ownership_governance_errors`, AQ/BF inventory guards)
- Architecture layer alignment heuristics (`_normalize_layer`, `_direct_owner_inventory_layer_ok`, live-legality path checks)
- Import-boundary guards (BD-6, BV2C, BV7C, BV10, BV12C, BV13C, BV14C, BV16C, BN1–BN11)
- Gate magnet import/source-fragment scanning (`collect_gate_magnet_guard_*`)
- Fan-in caps and compat-barrel regrowth lockdown
- Smoke-bridge / delegate-collapse closeout locks (BJ70–BJ129, BV7A/BV12A/BV13A/BV14A)
- BU4/BU8/BU9 write-path parity governance
- BE6/AL4 documentation-lock tests
- Pytest fixtures (`inventory`, `full_inventory`, `test_audit_module`)

## Compatibility Verification

Confirm:

- **Registry contents unchanged** — same 17 groups, 46 governed file paths in derived index, 13 allowlist entries, 6 gate-magnet guard paths; byte-identical registry definitions moved verbatim.
- **Test behavior unchanged** — registry contract tests pass (`test_registry_defines_all_required_groups`, `test_derived_registry_index_matches_live_registry`, governance schema tests, BA-7 guard path coverage); `tests/test_test_audit_tool.py` passes (45 tests).
- **Tooling behavior unchanged** — `tools/test_audit.py` derives the same index and allowlist from the contract module; `_build_ownership_registry_index()` no longer imports a test module.
- **No ownership rules changed** — no edits to responsibility assignments, neighbor lists, allowlist reasons, or guard policy constants beyond relocation.

### Validation run

```text
py -3 -c "import tests.ownership_registry_contract"          # OK — no pytest dependency
py -3 -m pytest tests/test_test_audit_tool.py -q             # 45 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k \
  "registry_defines or derived_registry_index or allowlist_entries or governance_inventory"  # passed
```

**Note:** Full `tests/test_ownership_registry.py` collection currently hits pre-existing repo-wide pytest collect errors (e.g. `test_golden_replay_long_session.py` import failure) when the `full_inventory` fixture runs `tools/test_audit.py` collect-only. Those failures are unrelated to CH1; registry-extraction tests that do not depend on full pytest collection all pass.

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **341** (5959 → 5618) |
| Lines added to `tests/ownership_registry_contract.py` | **362** |
| Registry entries (`RESPONSIBILITY_REGISTRY` groups) | **17** |
| Consumers updated | **2** (`tests/test_ownership_registry.py`, `tools/test_audit.py`) |

## Follow-up Candidates

Remaining responsibilities still concentrated in `tests/test_ownership_registry.py` (CH2+ targets):

1. **CH2 — Ownership guard locality pilot** — move domain guard implementations (BN gate-context, BV compat-barrel caps, BJ delegate-collapse) beside their domains; keep thin aggregator invocations in the central file.
2. **`collect_ownership_governance_errors`** — could move to a governance-check helper module (still test-only) while keeping pytest assertions in the test file.
3. **Import scanner library** — `_collect_import_module_paths`, `collect_*_guard_violations`, and fan-in static importers (~2500+ lines) are enforcement mechanics, not registry data; prime candidates for per-domain modules.
4. **Historical cycle closeout locks** — BJ70–BJ129 terminal-pipeline/delegate tests accumulate in the central file; retire or relocate when superseded by focused owner tests.
5. **BU write-path parity** — already partially extracted to `tests/helpers/ownership_write_path_governance.py`; central file still hosts BU8/BU9 assertion entry points.
