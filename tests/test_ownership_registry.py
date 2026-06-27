"""Lightweight direct-owner registry identity checks (tests only; no runtime hooks).

This module owns **registry identity only**: responsibility group completeness, derived
registry index, inventory integration, governance error aggregation, allowlist contract
validation, and stable registry neighbor/direct-owner relationships. It does **not** host
domain structural guards, import locks, replay projection policy, or write-path parity.

This module answers: *who may authoritatively define a new legality rule or shipped contract
edge case?* It does **not** claim to catalog all meaningful coverage.

Design notes (read before extending):
- **Direct owner** = exactly one canonical test module that is allowed to introduce detailed
  normative assertions for the responsibility. Other suites may overlap behaviorally.
- **Neighbor** paths (smoke, transcript, gauntlet, evaluator, downstream consumer, compatibility
  residue) are *supporting* surfaces. They must not be named as the direct owner for **live
  legality** responsibilities (gate-era rules, sanitizer post-processing, shipped policy
  materialization, etc.).
- **Downstream consumer** suites (Cycle AD-3 / AL4): integration-visible smoke only — player-facing
  text hygiene, repair/replacement evidence, contract threading through HTTP/API, and
  layer-specific checked/failed/repaired fields owned by that consumer (e.g. answer
  completeness, response delta). They must **not** restate exact gate orchestration tables
  (``final_route``, ``final_emitted_source``, owner-bucket mapping, repair-kind enumeration)
  already owned by ``tests/test_final_emission_gate.py``; prefer
  ``tests/helpers/emission_smoke_assertions.py`` for route/phrase smoke helpers.
- **Smoke facade** (Cycle AL4): ``tests/helpers/emission_smoke_assertions.py`` is the intended
  downstream assertion surface for HTTP/pipeline wiring — intentionally weaker than owner
  legality suites. Replay/golden projection helpers stay separate
  (``tests/helpers/golden_replay_projection.py``, ``tests/helpers/opening_fallback_evidence.py``).
- **Smoke suites**: survival / wiring / one-phrase hygiene checks; not full legality matrices.
- **Gauntlet / replay neighbors** (e.g. ``tests/test_golden_replay.py`` redirect stub and
  ``tests/test_golden_replay_*.py`` focused integration files): intentional
  diagnostic observation and drift projection locks — not runtime gate orchestration owners.
  Classifier/dashboard FEM bucket columns follow the same rule (diagnostic projection, not
  gate ownership).
- New validation rules should land with a clear direct owner first; only then add broad
  regression, transcript, or gauntlet coverage so failures stay attributable.
- **Gate boundary governance** (Cycles AD-3, AL4, BA-7, AG-10, BE6, BJ-4): gate magnet guards,
  downstream smoke-facade locks, and scaffold/phrase layer separation live in
  ``tests/test_gate_boundary_governance.py`` (not this registry module).
- **Replay/projection boundary governance** (Cycles AO5, BI-8, BG-1): golden replay bridge
  boundaries, protected manifest parity, and runtime vs acceptance projection separation live in
  ``tests/test_replay_boundary_governance.py`` (not this registry module).
- **Ownership write-path governance** (Cycles BU8–BU10): BU4 CSV parity and producer-stamp
  pairing locks live in ``tests/test_ownership_write_path_governance.py`` (not this registry
  module).
- **BD/BV compatibility import guards** (Cycles BD-6, BV2C, BV7C, BV10C, BV12C–BV14C, BV16C):
  compat barrel, import-cap, facade-routing, and compressed dependency guardrails live in
  ``tests/test_compat_import_governance.py`` (not this registry module).
- **Gate-context / preflight import guards** (Cycle BN1–BN11): runtime gate entry, lazy gate
  namespace, and gate-context preflight helper routing locks live in
  ``tests/test_gate_context_ownership_guards.py`` (not this registry module).

Governance consumes the live inventory from ``tests/test_inventory_governance.json`` (regenerate via
``py -3 tools/test_audit.py``). Inventory schema, slim JSON shape, and derived-field rejection policy
are enforced in ``tests/test_inventory_governance.py`` (not this registry module). Unclassified test
files elsewhere in the repo do not affect these checks.

Cycle AL4 legality-owner quick reference (downstream suites assert wiring/smoke only):
- Final emission gate orchestration / route tables → ``tests/test_final_emission_gate.py``
  (redirect stub; practical coverage in ``tests/test_final_emission_gate_*.py`` owner files)
- FEM projection / lineage → ``tests/test_final_emission_meta.py`` (``final_emission_meta_projection``)
- Dialogue route classification table → ``tests/test_dialogue_routing_lock.py`` (pure
  ``choose_interaction_route``; HTTP packaging smoke → ``tests/test_turn_pipeline_shared.py``)
- Sanitizer phrase legality → ``tests/test_output_sanitizer.py`` (``output_sanitizer_final_string_cleanup``)
- Strict-social phrase/source legality → ``tests/test_social_exchange_emission.py``
  (``social_emission_legality_surface``)
- Downstream HTTP smoke/wiring → ``tests/test_turn_pipeline_shared.py`` (registered neighbor)
- Downstream smoke facade → ``tests/helpers/emission_smoke_assertions.py`` (helpers module)
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Final

import pytest

from tests.ownership_registry_contract import (
    RESPONSIBILITY_REGISTRY,
    _CROSS_FILE_DUPLICATE_ALLOWLIST,
    _REQUIRED_GROUP_IDS,
    build_ownership_registry_index,
)
from tests.ownership_inventory_governance import (
    DEFAULT_GOVERNANCE_INVENTORY_PATH,
    LIVE_LEGALITY_GROUP_IDS,
    collect_ownership_governance_errors,
    full_inventory_by_path,
    inventory_paths,
    load_governance_inventory,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_INVENTORY_PATH = DEFAULT_GOVERNANCE_INVENTORY_PATH

# CM8 — registry scope guard: identity tests only; extend allowlist deliberately when adding neighbors.
_REGISTRY_IDENTITY_TEST_NAMES: Final[frozenset[str]] = frozenset(
    {
        'test_registry_defines_all_required_groups',
        'test_governance_committed_files_include_all_registry_paths',
        'test_derived_registry_paths_present_in_inventory',
        'test_derived_registry_index_matches_live_registry',
        'test_ownership_registry_governance',
        'test_allowlist_entries_have_non_empty_reasons',
        'test_final_emission_meta_projection_read_side_ownership_boundaries',
        'test_ao5_replay_projection_registry_neighbor_relationships_locked',
        'test_registry_module_scope_guard_identity_only',
    }
)
_FOCUSED_GOVERNANCE_OWNER_MODULES: Final[tuple[str, ...]] = (
    'tests/test_gate_boundary_governance.py',
    'tests/test_replay_boundary_governance.py',
    'tests/test_ownership_write_path_governance.py',
    'tests/test_compat_import_governance.py',
    'tests/test_gate_context_ownership_guards.py',
    'tests/test_inventory_governance.py',
)


@pytest.fixture(scope="module")
def inventory() -> dict:
    return load_governance_inventory(_INVENTORY_PATH)


@pytest.fixture(scope="module")
def inventory_by_path(inventory: dict) -> dict[str, dict]:
    return inventory_paths(inventory)


@pytest.fixture(scope="module")
def full_inventory() -> dict:
    """Fresh full audit payload once per module (BF1: single pytest collect-only per run)."""
    spec = importlib.util.spec_from_file_location("_inv_audit", _REPO_ROOT / "tools" / "test_audit.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_inventory_payload()


def test_registry_defines_all_required_groups() -> None:
    assert set(RESPONSIBILITY_REGISTRY) == _REQUIRED_GROUP_IDS


def test_governance_committed_files_include_all_registry_paths(inventory_by_path: dict[str, dict]) -> None:
    """AQ8: every registry-owned path appears in committed governance files[]."""
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted((fp for fp in files_roles if fp not in inventory_by_path))
    assert not missing, f'registry-owned paths missing from committed governance: {missing[:5]!r}'


def test_derived_registry_paths_present_in_inventory(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """AQ5: derived files_roles paths remain inventory-backed for direct-owner/neighbor checks."""
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted((fp for fp in files_roles if fp not in inventory_by_path))
    assert not missing, f'derived registry paths missing from inventory: {missing[:5]!r}'
    gate = 'tests/test_final_emission_gate.py'
    assert gate in files_roles
    assert files_roles[gate] == [{'group_id': 'final_emission_gate_orchestration', 'role': 'direct_owner'}]
    full_by_path = full_inventory_by_path(full_inventory)
    assert full_by_path[gate].get('likely_architecture_layer') == 'gate'


def test_derived_registry_index_matches_live_registry() -> None:
    """AQ4: neighbor/group maps are derived from Python registry, not committed JSON."""
    idx = build_ownership_registry_index()
    assert idx.get('available') is True
    groups = idx.get('groups')
    roles = idx.get('files_roles')
    assert isinstance(groups, dict) and isinstance(roles, dict)
    assert set(groups) == _REQUIRED_GROUP_IDS
    assert 'final_emission_gate_orchestration' in groups
    gate = groups['final_emission_gate_orchestration']
    assert isinstance(gate, dict)
    assert gate.get('direct_owner') == 'tests/test_final_emission_gate.py'
    assert isinstance(gate.get('transcript_suites'), list)
    for key in ('smoke_suites', 'transcript_suites', 'gauntlet_suites', 'evaluator_suites', 'downstream_consumer_suites', 'compatibility_residue_suites'):
        assert key in gate, f'missing derived registry groups field {key!r}'


def test_ownership_registry_governance(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    derived_dups = full_inventory.get('cross_file_duplicate_test_names')
    errors = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=LIVE_LEGALITY_GROUP_IDS,
        cross_file_duplicate_test_names=derived_dups if isinstance(derived_dups, list) else None,
        full_inventory_by_path=full_inventory_by_path(full_inventory),
    )
    assert not errors, 'ownership governance failures:\n' + '\n'.join(errors)


def test_allowlist_entries_have_non_empty_reasons() -> None:
    for name, reason in _CROSS_FILE_DUPLICATE_ALLOWLIST.items():
        assert name.startswith('test_'), name
        assert reason.strip(), f'empty allowlist reason for {name!r}'


def test_final_emission_meta_projection_read_side_ownership_boundaries() -> None:
    """Cycle AE4: read-side lineage/projection edits stay in meta projection ownership."""
    meta_proj = RESPONSIBILITY_REGISTRY['final_emission_meta_projection']
    gate_orch = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    assert meta_proj.direct_owner == 'tests/test_final_emission_meta.py'
    assert gate_orch.direct_owner == 'tests/test_final_emission_gate.py'
    assert meta_proj.direct_owner != gate_orch.direct_owner
    gate_path = 'tests/test_final_emission_gate.py'
    assert gate_path not in meta_proj.downstream_consumer_suites
    assert gate_path not in meta_proj.smoke_suites
    assert gate_path not in meta_proj.transcript_suites
    assert gate_path not in meta_proj.gauntlet_suites
    assert gate_path not in meta_proj.evaluator_suites
    assert gate_path not in meta_proj.compatibility_residue_suites
    title = meta_proj.human_title.lower()
    assert 'read path' in title or 'replay read path' in title
    assert 'projection' in title
    assert 'gate orchestration' not in title


def test_ao5_replay_projection_registry_neighbor_relationships_locked() -> None:
    """Cycle AO5: replay/projection groups keep gauntlet-neighbor and meta-owner registry relationships."""
    meta_proj = RESPONSIBILITY_REGISTRY['final_emission_meta_projection']
    gauntlet = RESPONSIBILITY_REGISTRY['gauntlet_playability_validation']
    assert 'tests/test_golden_replay.py' in frozenset(
        (p.replace('\\', '/') for p in gauntlet.gauntlet_suites)
    )
    assert meta_proj.direct_owner.replace('\\', '/') == 'tests/test_final_emission_meta.py'
    assert 'game.final_emission_replay_projection' not in frozenset(
        (p.replace('\\', '/') for p in meta_proj.downstream_consumer_suites)
    )


def test_registry_module_scope_guard_identity_only() -> None:
    """CM8: registry file stays identity-focused; domain policy belongs in focused governance modules."""
    source = Path(__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)
    test_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
    }
    unexpected = sorted(test_names - _REGISTRY_IDENTITY_TEST_NAMES)
    assert not unexpected, (
        'tests/test_ownership_registry.py must remain registry identity only; '
        f'unexpected tests {unexpected!r}. Add domain policy to focused governance files instead.'
    )
    missing = sorted(_REGISTRY_IDENTITY_TEST_NAMES - test_names)
    assert not missing, f'registry identity test allowlist out of date; missing {missing!r}'
    module_doc = (ast.get_docstring(tree) or '').lower()
    assert 'registry identity only' in module_doc
    for rel in _FOCUSED_GOVERNANCE_OWNER_MODULES:
        assert rel in module_doc, f'registry module doc must point domain policy to {rel!r}'
