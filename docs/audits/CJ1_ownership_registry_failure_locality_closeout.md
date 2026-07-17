# CJ1 — Ownership Registry Failure Locality Closeout

## Initial Failure Inventory

| failing test | category | root cause | owner |
| --- | --- | --- | --- |
| `test_governance_committed_files_exclude_non_registry_paths` | D — Inventory collection failure | `full_inventory` fixture raised when pytest collect failed on `test_golden_replay_long_session.py` (`SEALED_REPLACEMENT_SUBKINDS` missing from acceptance facade) | `tests/helpers/golden_replay_projection.py` |
| `test_derived_registry_paths_present_in_inventory` | A + D | Same collection block; plus gate redirect stub scored `general` instead of declared `gate` layer | `tests/test_final_emission_gate.py`, `tests/helpers/golden_replay_projection.py` |
| `test_inventory_block_b_schema_v2_coherence` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_evaluator_neighbor_may_have_general_inventory_layer` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_governance_rejects_sharp_direct_owner_layer_mismatch` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_inventory_per_test_rows_include_marker_set` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_governance_registry_paths_have_derived_marker_sets` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_governance_registry_paths_have_derived_architecture_layers` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_governance_registry_paths_have_derived_duplicate_base_names` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_governance_registry_paths_have_live_collected_counts` | D | Collection failure via `full_inventory` | `tests/helpers/golden_replay_projection.py` |
| `test_cross_file_duplicate_allowlist_from_derived_full_audit` | E — Stale governance artifact | New dashboard compatibility-wrapper duplicate test name not allowlisted | `tests/ownership_registry_contract.py` |
| `test_ownership_registry_governance` | D + E | Collection failure + duplicate allowlist + gate stub layer mismatch | Multiple (see rows above) |
| `test_governance_rejects_duplicate_direct_owner` | F — Architecture change requiring registry update | Missing `dataclasses.replace` import after CH13 wiring removed embedded imports | `tests/test_ownership_registry.py` |
| `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` | B — Import-boundary violation | 26 CE/CF/CG replay/classification owner paths not yet registered in BD-6 allowlist | `tests/ownership_guard_bd_dependency_compression.py` |
| `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` | B — Import-boundary violation | Production FEM write owners (`passive_scene_pressure`, `referential_clarity`) and CF3 owner missing from BV2C game/test allowlists | `tests/ownership_guard_bv_compatibility.py` |
| `test_bv12c_compat_barrel_fi_cap_locked` | A — Missing registry metadata | Intentional domain hub module paths not present in central registry docstring | `tests/test_ownership_registry.py` |
| `test_bv13c_text_compat_fi_cap_locked` | A — Missing registry metadata | Same — text domain hub paths undocumented in registry docstring | `tests/test_ownership_registry.py` |
| `test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities` | B — Import-boundary violation | `ownership_closeout_delegate_locks.py` imports compat barrel for BJ-115/116 introspection without BV14C allowlist entry | `tests/ownership_guard_bv_compatibility.py` |
| `test_bv14c_social_exchange_compat_fi_cap_locked` | A + F | Domain hubs undocumented; allowed-importer set stale after CH11 extraction moved import to closeout helper | `tests/ownership_guard_bv_compatibility.py`, `tests/test_ownership_registry.py` |
| `test_bj127_ownership_registry_global_stale_gate_harness_scan` | E — Stale governance artifact | Legitimate negative-test fixture strings in delegator regression owner not excluded from global scan | `tests/ownership_closeout_delegate_locks.py` |
| `test_bu8_bu4_production_ownership_write_paths_parity_locked` | E — Stale governance artifact | BU4 CSV stale after owner-bucket view extraction and new generic-exit producer stamp | `docs/audits/BU4_ownership_write_paths.csv` |
| `test_bu9_visibility_fallback_producer_stamp_pairing_locked` | F — Architecture change requiring registry update | Referential-clarity upstream repair stamps producer kind without visibility bucket pairing | `game/final_emission_referential_clarity.py` |

## Changes Performed

| file changed | reason | locality preserved? |
| --- | --- | --- |
| `tests/helpers/golden_replay_projection.py` | Re-export runtime replay-projection symbols (`SEALED_REPLACEMENT_SUBKINDS`, lineage builders, hard-replacement constants) so acceptance facade restores BD-4 contract and unblocks inventory collection | Yes — facade remains authoritative; no logic moved into registry test |
| `tests/test_ownership_registry.py` | Add `dataclasses.replace` import; document BV12C/BV13C/BV14C intentional domain hubs in policy docstring | Yes — orchestration-only edits |
| `tests/ownership_guard_bd_dependency_compression.py` | Register 26 CE/CF/CG/BX replay and classification owner/helper paths in BD-6 allowlist with documented reasons | Yes — guard policy stays in BD-6 helper |
| `tests/ownership_guard_bv_compatibility.py` | Add BV2C write-owner modules; BV14C allowlist + FI-cap importer set for closeout delegate locks; remove stale `test_ownership_registry.py` FI entry | Yes — compat guard helper remains owner |
| `tests/ownership_closeout_delegate_locks.py` | Exclude delegator regression negative-test fixtures from BJ-127 global stale-`feg` scan | Yes — closeout lock helper owns scan registries |
| `tests/ownership_registry_contract.py` | Allowlist `test_compatibility_wrappers_reference_same_functions` cross-file duplicate from CE dashboard split | Yes — contract module owns allowlist data |
| `tests/test_final_emission_gate.py` | Add gate-layer inventory signal constant on redirect stub so declared `gate` owner layer matches derived inventory | Yes — one-line signal on documented redirect stub |
| `docs/audits/BU4_ownership_write_paths.csv` | Move `opening_fallback_owner_bucket_from_meta` writes to `final_emission_owner_bucket_views`; add `run_generic_accept_exit` producer stamp | Yes — registry CSV parity only |
| `game/final_emission_referential_clarity.py` | Pair visibility producer repair kind with `stamp_visibility_fallback_owner_bucket_from_fields` on upstream observe repair | Yes — production owner-local stamp pairing |

## Responsibility Review

Did any ownership move back into the registry?

**No.**

- `tests/test_ownership_registry.py` retains thin orchestration: fixtures, guard test entrypoints, and policy docstring corpus only.
- Guard enforcement logic remains in `ownership_guard_*` modules.
- Registry data remains in `ownership_registry_contract.py`.
- Inventory governance orchestration remains in `ownership_inventory_governance.py`.
- BJ closeout verification remains in `ownership_closeout_delegate_locks.py`.
- BU write-path parity remains in `tests/helpers/ownership_write_path_governance.py`.
- Collection diagnostics were fixed at the root cause (missing facade re-export) rather than by suppressing `full_inventory` errors in the registry test.

## Remaining Failures

None in `tests/test_ownership_registry.py`.

Follow-on (outside CJ-1 scope):

- CJ-2 may still improve collection error messaging when unrelated pytest collect failures occur.
- BD-6 allowlist now documents intentional compressed-import owners; future consumers should route through facades or extend the allowlist with reasons rather than weakening the guard.

## Test Results

Commands:

```text
python -m pytest tests/test_ownership_registry.py -q --tb=line
python -m pytest tests/test_ownership_registry.py -v --tb=no
```

Results:

| run | outcome |
| --- | --- |
| Initial (pre-fix) | 10 failed, 12 errors, 194 passed |
| Final | **216 passed**, 0 failed, 0 errors (~67s) |

## Governance Locality Assessment

**Improved**

Failures now route to focused owners:

- Inventory collection errors traced to a missing acceptance-facade re-export instead of dumping full pytest collect output into registry setup.
- Import-boundary violations resolved via guard-module allowlist updates (BD-6, BV2C, BV14C) rather than central test changes.
- Closeout scan false positives isolated in `ownership_closeout_delegate_locks.py`.
- Write-path parity and producer-stamp pairing fixed in BU4 CSV and production referential-clarity owner.
- CH-extracted helper architecture preserved; registry test passes as orchestration-only enforcement hub.
