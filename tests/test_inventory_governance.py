"""Committed governance inventory policy and audit-schema enforcement (tests only).

This module owns **inventory JSON shape**, slim committed-artifact policy, derived-field
omission/rejection checks, and synthetic mutation tests for ``tests/test_inventory_governance.json``.

This is **not** the global test-responsibility ownership registry. Registry identity,
direct-owner source-of-truth, and registry/inventory integration checks remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_inventory_governance.py``.
``tools/test_audit.py`` unit behavior is covered by ``tests/test_test_audit_tool.py``.
"""

from __future__ import annotations

import importlib.util
import json
import types
from dataclasses import replace
from pathlib import Path

import pytest

from tests.ownership_inventory_governance import (
    CANONICAL_VALIDATION_LAYERS,
    DEFAULT_GOVERNANCE_INVENTORY_PATH,
    LIVE_LEGALITY_GROUP_IDS,
    collect_ownership_governance_errors,
    direct_owner_inventory_layer_ok,
    full_inventory_by_path,
    inventory_paths,
    load_governance_inventory,
)
from tests.ownership_registry_contract import (
    RESPONSIBILITY_REGISTRY,
    ResponsibilityRecord,
    _CROSS_FILE_DUPLICATE_ALLOWLIST,
    build_ownership_registry_index,
)

try:
    from game import validation_layer_contracts as vlc
except ImportError:  # pragma: no cover - repo layout guard
    vlc = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEST_AUDIT_PATH = _REPO_ROOT / "tools" / "test_audit.py"
_INVENTORY_PATH = DEFAULT_GOVERNANCE_INVENTORY_PATH


@pytest.fixture(scope="module")
def inventory() -> dict:
    return load_governance_inventory(_INVENTORY_PATH)


@pytest.fixture(scope="module")
def inventory_by_path(inventory: dict) -> dict[str, dict]:
    return inventory_paths(inventory)


@pytest.fixture(scope="module")
def test_audit_module() -> types.ModuleType:
    """Load ``tools/test_audit.py`` once per module (BF1: avoid repeated importlib loads)."""
    spec = importlib.util.spec_from_file_location("_inv_audit", _TEST_AUDIT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def full_inventory(test_audit_module: types.ModuleType) -> dict:
    """Fresh full audit payload once per module (BF1: single pytest collect-only per run)."""
    return test_audit_module.build_inventory_payload()


def test_inventory_schema_version_matches_audit_tool(test_audit_module: types.ModuleType, inventory: dict) -> None:
    """Block A: inventory generator and governance tests agree on schema generation."""
    assert inventory.get('summary', {}).get('inventory_schema_version') == test_audit_module.INVENTORY_SCHEMA_VERSION

def test_governance_inventory_contains_required_fields(inventory: dict) -> None:
    """AQ9: committed artifact retains stable governance sections only."""
    for key in ('summary', 'files'):
        assert key in inventory, f'missing governance inventory key {key!r}'
    assert 'cross_file_duplicate_test_names' not in inventory, 'governance JSON must not store cross_file_duplicate_test_names; derive via tools/test_audit.py --check'
    assert 'tests' not in inventory, 'governance JSON must not store tests[]; derive per-test marker coverage via tools/test_audit.py --check'
    assert 'block_b_overlap_clusters' not in inventory, 'governance JSON must not store block_b_overlap_clusters; use --full diagnostic output'
    assert 'import_hub_modules' not in inventory, 'governance JSON must not store import_hub_modules; use --full diagnostic output'
    assert 'ownership_registry_index' not in inventory, 'governance JSON must not embed ownership_registry_index; derive via build_ownership_registry_index()'
    assert inventory.get('summary', {}).get('inventory_kind') == 'governance'
    sample = inventory['files'][0]
    for key in ('path',):
        assert key in sample, f'missing governance file row key {key!r}'
    assert 'marker_set' not in sample, 'governance file rows must not store marker_set; derive via tools/test_audit.py --check'
    assert 'likely_architecture_layer' not in sample, 'governance file rows must not store likely_architecture_layer; derive via tools/test_audit.py --check'
    assert 'pytest_collected' not in sample, 'governance file rows must not store pytest_collected; derive via tools/test_audit.py --check'
    assert 'collected_duplicate_base_names' not in sample, 'governance file rows must not store collected_duplicate_base_names; derive via tools/test_audit.py --check'
    assert 'ownership_registry_positions' not in sample, 'governance file rows must not store ownership_registry_positions; derive via build_ownership_registry_index()'

def test_governance_summary_contains_stable_metadata_only(inventory: dict) -> None:
    """AQ9: committed summary retains stable metadata; counts are derived at --check."""
    summary = inventory.get('summary')
    assert isinstance(summary, dict)
    assert set(summary) == {'inventory_schema_version', 'inventory_kind', 'declared_pytest_markers'}
    assert summary.get('inventory_kind') == 'governance'

def test_governance_omits_cross_file_duplicate_test_names(inventory: dict) -> None:
    """AQ9: cross-file duplicate rows are derived from full audit, not committed."""
    assert 'cross_file_duplicate_test_names' not in inventory

def test_governance_rejects_stored_cross_file_duplicate_test_names(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ9: committed governance must not embed derived duplicate-name rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['cross_file_duplicate_test_names'] = [{'base_name': 'test_x', 'files': ['tests/test_a.py']}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store cross_file_duplicate_test_names' in e for e in errs))

def test_governance_file_rows_omit_committed_per_test_rows(inventory: dict) -> None:
    """AQ6: per-test marker rows are derived at check time, not committed."""
    assert 'tests' not in inventory

def test_governance_rejects_stored_per_test_rows(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ6: committed governance must not embed derived per-test marker rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['tests'] = [{'nodeid': 'tests/test_x.py::test_y', 'marker_set': ['unit']}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store tests[]' in e for e in errs))

def test_governance_file_rows_omit_marker_set(inventory: dict) -> None:
    """BF7: per-file marker sets are derived at check time, not committed."""
    with_markers = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'marker_set' in row]
    assert not with_markers, f'governance files must not store marker_set: {with_markers[:3]!r}'

def test_governance_rejects_stored_marker_set(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF7: committed governance must not embed derived per-file marker sets."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['marker_set'] = ['unit']
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store marker_set' in e for e in errs))

def test_governance_file_rows_omit_likely_architecture_layer(inventory: dict) -> None:
    """BF6: architecture-layer heuristics are derived at check time, not committed."""
    with_layers = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'likely_architecture_layer' in row]
    assert not with_layers, f'governance files must not store likely_architecture_layer: {with_layers[:3]!r}'

def test_governance_rejects_stored_likely_architecture_layer(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF6: committed governance must not embed derived architecture-layer heuristics."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['likely_architecture_layer'] = 'gate'
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store likely_architecture_layer' in e for e in errs))

def test_governance_file_rows_omit_collected_duplicate_base_names(inventory: dict) -> None:
    """BF5: in-file duplicate base names are derived at check time, not committed."""
    with_dups = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'collected_duplicate_base_names' in row]
    assert not with_dups, f'governance files must not store collected_duplicate_base_names: {with_dups[:3]!r}'

def test_governance_rejects_stored_collected_duplicate_base_names(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF5: committed governance must not embed derived in-file duplicate-base-name lists."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['collected_duplicate_base_names'] = ['test_dup']
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store collected_duplicate_base_names' in e for e in errs))

def test_governance_file_rows_omit_pytest_collected(inventory: dict) -> None:
    """BF4: per-file collect counts are derived at check time, not committed."""
    with_counts = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'pytest_collected' in row]
    assert not with_counts, f'governance files must not store pytest_collected: {with_counts[:3]!r}'

def test_governance_rejects_stored_pytest_collected(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF4: committed governance must not embed derived per-file collect counts."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['pytest_collected'] = 99
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store pytest_collected' in e for e in errs))

def test_governance_file_rows_omit_registry_positions(inventory: dict) -> None:
    """AQ5: per-file registry positions are derived, not committed."""
    with_positions = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'ownership_registry_positions' in row]
    assert not with_positions, f'governance files must not store ownership_registry_positions: {with_positions[:3]!r}'

def test_governance_committed_files_exclude_non_registry_paths(inventory: dict, full_inventory: dict, test_audit_module: types.ModuleType) -> None:
    """AQ8: committed governance files[] retains registry-owned paths only (+ cross-file dup files)."""
    allowed = test_audit_module.governance_committed_file_paths(full_inventory)
    committed = {str(row['path']).replace('\\', '/') for row in inventory.get('files', []) if isinstance(row, dict)}
    extra = sorted(committed - allowed)
    assert not extra, f'governance files[] includes non-governance paths: {extra[:5]!r}'

def test_governance_rejects_non_registry_committed_file_row(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ8: committed governance must not embed non-registry file rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'] = list(polluted.get('files', [])) + [{'path': 'tests/test_non_registry_module.py'}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store non-governance path' in e for e in errs))

def test_governance_omits_triage_aggregates(inventory: dict) -> None:
    """AQ7: diagnostic triage aggregates are full-only, not committed."""
    assert 'block_b_overlap_clusters' not in inventory
    assert 'import_hub_modules' not in inventory

def test_governance_rejects_stored_triage_aggregates(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ7: committed governance must not embed full-only triage aggregates."""
    polluted = json.loads(json.dumps(inventory))
    polluted['block_b_overlap_clusters'] = [{'kind': 'dense_ownership_theme_by_architecture_layer', 'cells': []}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store block_b_overlap_clusters' in e for e in errs))

def test_inventory_block_b_schema_v2_coherence(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """AQ7: triage aggregates and registry paths are validated; clusters/hubs derived from full audit."""
    clusters = full_inventory.get('block_b_overlap_clusters')
    assert isinstance(clusters, list) and clusters, 'block_b_overlap_clusters must be a non-empty list in full output'
    kinds = {c.get('kind') for c in clusters if isinstance(c, dict)}
    assert 'dense_ownership_theme_by_architecture_layer' in kinds
    hubs = full_inventory.get('import_hub_modules')
    assert isinstance(hubs, list)
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict)
    for fp, roles in files_roles.items():
        assert fp in inventory_by_path, f'derived registry path not in inventory: {fp}'
        assert isinstance(roles, list) and roles

def test_evaluator_neighbor_may_have_general_inventory_layer(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """Heuristic ``general`` is allowed for non-owner paths; governance only sharpens direct owners."""
    p = 'tests/test_player_agency_evaluator.py'
    assert p in inventory_by_path
    full_row = full_inventory_by_path(full_inventory).get(p)
    assert full_row is not None and full_row.get('likely_architecture_layer') == 'general'
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=LIVE_LEGALITY_GROUP_IDS, full_inventory_by_path=full_inventory_by_path(full_inventory))
    assert not any((p in e for e in errs))

def test_governance_rejects_stored_registry_positions(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ5: committed governance rows must not embed derived registry positions."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['ownership_registry_positions'] = [{'group_id': 'x', 'role': 'direct_owner'}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store ownership_registry_positions' in e for e in errs))

def test_governance_rejects_duplicate_direct_owner(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    owner = 'tests/test_save_load.py'
    reg = {'a': replace(RESPONSIBILITY_REGISTRY['engine_truth_persistence_mechanics'], direct_owner=owner), 'b': replace(RESPONSIBILITY_REGISTRY['planner_prompt_bundle_shipped_contract'], direct_owner=owner)}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('duplicate direct_owner' in e for e in errs))

def test_governance_rejects_missing_inventory_path(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    reg = {'__missing__': ResponsibilityRecord(human_title='Synthetic', declared_architecture_layer='engine', direct_owner='tests/__this_file_should_not_exist__.py')}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('not in inventory' in e for e in errs))

def test_direct_owner_general_disallowed_when_declared_layer_set() -> None:
    assert not direct_owner_inventory_layer_ok('engine', 'general')
    assert not direct_owner_inventory_layer_ok('gate', 'General')
    assert direct_owner_inventory_layer_ok(None, 'general')
    assert direct_owner_inventory_layer_ok('engine', 'smoke')
    assert direct_owner_inventory_layer_ok('engine', 'engine')

def test_governance_rejects_sharp_direct_owner_layer_mismatch(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    reg = {'__layer__': ResponsibilityRecord(human_title='Synthetic layer mismatch', declared_architecture_layer='gate', direct_owner='tests/test_save_load.py')}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset(), full_inventory_by_path=full_inventory_by_path(full_inventory))
    assert any(('inventory layer incompatible' in e for e in errs))

def test_inventory_per_test_rows_include_marker_set(test_audit_module: types.ModuleType, full_inventory: dict) -> None:
    """AQ6: per-test marker_set is derived from fresh audit output, not committed JSON."""
    rows = test_audit_module.derive_per_test_marker_rows(full_inventory)
    assert rows, 'expected derived per-test marker rows from fresh inventory'
    missing = [r.get('nodeid') for r in rows if not isinstance(r, dict) or 'marker_set' not in r]
    assert not missing, f'missing marker_set on {len(missing)} derived rows (first: {missing[:3]!r})'

def test_governance_registry_paths_have_derived_marker_sets(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF7: registry-owned paths retain marker_set data in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        marker_set = frow.get('marker_set')
        assert isinstance(marker_set, list)

def test_governance_registry_paths_have_derived_architecture_layers(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF6: registry-owned paths retain architecture-layer heuristics in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        layer = frow.get('likely_architecture_layer')
        assert isinstance(layer, str) and layer.strip()

def test_governance_registry_paths_have_derived_duplicate_base_names(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF5: registry-owned paths retain in-file duplicate-base-name data in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        dup_bases = frow.get('collected_duplicate_base_names')
        assert isinstance(dup_bases, list)

def test_governance_registry_paths_have_live_collected_counts(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF4: registry-owned paths retain live per-file collect counts in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        collected = frow.get('pytest_collected')
        nodeids = frow.get('collected_nodeids')
        assert isinstance(collected, int) and collected >= 0
        assert isinstance(nodeids, list)
        assert collected == len(nodeids), f'{fp}: pytest_collected mismatch vs collected_nodeids'

def test_cross_file_duplicate_allowlist_from_derived_full_audit(test_audit_module: types.ModuleType, full_inventory: dict) -> None:
    """AQ9: duplicate allowlist enforcement uses derived full audit output."""
    dups = full_inventory.get('cross_file_duplicate_test_names')
    assert isinstance(dups, list)
    errs = test_audit_module.collect_cross_file_duplicate_governance_errors(dups, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST)
    assert not errs, 'derived cross-file duplicate allowlist failures:\n' + '\n'.join(errs)

def test_canonical_validation_layers_importable() -> None:
    assert vlc is not None, 'game.validation_layer_contracts must import for layer alignment'
    assert set(vlc.CANONICAL_VALIDATION_LAYERS) == CANONICAL_VALIDATION_LAYERS
