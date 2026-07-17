"""Gate / smoke-facade ownership boundary governance (tests only).

This module owns **gate-layer magnet guards, downstream smoke-facade locks, and scaffold/phrase
layer separation** that keep gate orchestration direct owners free of replay read-side projection
creep and preserve intentional weakness in downstream HTTP smoke bridges (Cycles AD-3, AL4, BA-7,
AG-10, BE6, BJ-4).

This is **not** the global test-responsibility ownership registry. Registry identity, inventory
parity, and registry neighbor relationship assertions remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_guard_gate_magnet.py``,
``tests/ownership_guard_bd_dependency_compression.py``, and
``tests/ownership_guard_bv_compatibility.py``.

- **BA-7 / AG-10 gate magnet guard** (Cycle BA-7): gate-layer direct-owner suites must not
  import replay/dashboard/classifier projection helpers or accumulate read-side projection
  assertions. Enforced by ``test_ba7_*`` and
  ``test_final_emission_gate_does_not_accumulate_read_side_projection_assertions``.
- **AD-3 downstream integration smoke** (Cycle AD-3): AD-thinned suites are downstream
  neighbors, never direct owners; golden replay is gauntlet neighbor. Enforced by ``test_ad3_*``.
- **AL4 legality owner / smoke facade lock** (Cycle AL4): AL1–AL3 convergence boundaries stay
  aligned with registry direct owners and downstream smoke facade path. Enforced by
  ``test_al4_legality_owners_and_smoke_facade_locked``.
- **BJ-4 smoke facade weakness** (Cycle BJ-4 / BV7A / BV7B): emission smoke facade stays weak;
  extracted bridge symbols live in dedicated modules. Enforced by
  ``test_bj4_emission_smoke_facade_stays_weak_consumer_bridge``.
- **BE6 triple-layer scaffold split** (Cycle BE6): sanitizer legality, HTTP smoke phrases, and
  replay scaffold projection stay separate. Enforced by
  ``test_be6_scaffold_phrase_triple_layer_split_locked``.

Cycle BE6 — triple-layer scaffold / phrase split (documentation lock; **do not merge**):

1. ``tests/test_output_sanitizer.py`` — full sanitizer/procedural phrase **legality matrices**
2. ``tests/helpers/emission_smoke_assertions.py`` — weak HTTP/pipeline **smoke** phrases only
3. ``tests/helpers/golden_replay_projection.py`` — replay **scaffold-leakage projection**
   (``final_text_has_scaffold_leakage``, protected observation path)

Assertion-economy blocks must not unify these into one shared phrase matrix.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Mapping

from tests.ownership_guard_bd_dependency_compression import (
    _BD6_GATE_BRIDGE_FACADE,
    _BD6_GOLDEN_REPLAY_FACADE,
    _BD6_REPLAY_BRIDGE_FACADE,
)
from tests.ownership_guard_bv_compatibility import (
    _BD6_AC_SMOKE_FACADE,
    _BD6_RD_SMOKE_FACADE,
    _BD6_RT_SMOKE_FACADE,
    _BV12A_FALLBACK_BRIDGE_FACADE,
    _BV12A_GATE_ORCHESTRATION_FACADE,
    _BV12A_REPLAY_FEM_READ_FACADE,
    _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS,
    _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS,
    _BV7B_EXTRACTED_AC_SYMBOLS,
    _BV7B_EXTRACTED_RD_SYMBOLS,
    _BV7B_EXTRACTED_RT_SYMBOLS,
)
from tests.ownership_guard_gate_magnet import (
    collect_gate_magnet_guard_import_violations,
    collect_gate_magnet_guard_source_fragment_violations,
    gate_magnet_guard_paths,
)
from tests.ownership_inventory_governance import DOWNSTREAM_INTEGRATION_SMOKE_ONLY
from tests.ownership_registry_contract import RESPONSIBILITY_REGISTRY

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Cycle AL4: documented downstream smoke facade (helpers module — not a pytest suite path).
_DOWNSTREAM_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"

# Cycle AL4: legality owners locked by AL1–AL3 convergence.
_AL4_LEGALITY_OWNER_PATHS: Final[Mapping[str, str]] = {
    "final_emission_gate": "tests/test_final_emission_gate.py",
    "final_emission_meta": "tests/test_final_emission_meta.py",
    "dialogue_route_classification": "tests/test_dialogue_routing_lock.py",
    "output_sanitizer": "tests/test_output_sanitizer.py",
    "social_exchange_emission": "tests/test_social_exchange_emission.py",
    "turn_pipeline_http_smoke": "tests/test_turn_pipeline_shared.py",
}

# Cycle BE6: scaffold/phrase ownership layers — intentional separation; do not merge matrices.
_BE6_SCAFFOLD_PHRASE_LAYER_OWNERS: Final[Mapping[str, str]] = {
    "sanitizer_legality": "tests/test_output_sanitizer.py",
    "http_smoke_facade": _DOWNSTREAM_SMOKE_FACADE,
    "replay_scaffold_projection": _BD6_GOLDEN_REPLAY_FACADE,
}

_BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_final_emission_gate_consumer",
        "enforce_response_type_contract_layer",
        "final_emission_meta_from_output",
        "read_turn_debug_notes",
    }
)
_BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_answer_completeness_layer",
        "apply_response_delta_layer",
        "assert_no_boundary_reorder_repair",
        "assert_response_delta_boundary_validate_only",
        "inspect_response_delta_failure",
        "skip_answer_completeness_layer",
        "skip_response_delta_layer",
        "strict_social_answer_pressure_rd_contract_active",
        "validate_answer_completeness",
        "validate_response_delta",
    }
)
_BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS: Final[Mapping[str, str]] = {
    "gate_legality": "full gate legality matrices belong to tests/test_final_emission_gate.py",
    "legality_matrix": "legality matrices belong to owner suites",
    "route_enum": "route enum tables belong to route/gate owner suites",
    "route_table": "route tables belong to route/gate owner suites",
    "sanitizer_legality": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "sanitizer_phrase": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "repair_matrix": "AC/RD repair semantics belong to owner suites",
    "repair_semantic": "AC/RD repair semantics belong to owner suites",
}


def test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners() -> None:
    """BA-7: magnet guard spans gate-layer direct owners except meta projection and gauntlet."""
    guarded = gate_magnet_guard_paths()
    assert 'tests/test_final_emission_gate.py' in guarded
    assert 'tests/test_final_emission_validators.py' in guarded
    assert 'tests/test_output_sanitizer.py' in guarded
    assert 'tests/test_final_emission_meta.py' not in guarded
    assert 'tests/test_gauntlet_regressions.py' not in guarded


def test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not import replay/dashboard/classifier projection helpers."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing gate magnet-guard path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_gate_magnet_guard_import_violations(rel, source))
    assert not violations, 'gate magnet-guard import violations:\n' + '\n'.join(violations)


def test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not re-own replay/dashboard/classifier projection contracts."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_gate_magnet_guard_source_fragment_violations(rel, source))
    assert not violations, 'gate magnet-guard source-fragment violations:\n' + '\n'.join(violations)


def test_final_emission_gate_does_not_accumulate_read_side_projection_assertions() -> None:
    """AG-10: primary gate owner stays free of replay read-side projection assertion creep."""
    rel = 'tests/test_final_emission_gate.py'
    source = (_REPO_ROOT / rel).read_text(encoding='utf-8')
    violations = collect_gate_magnet_guard_source_fragment_violations(rel, source)
    assert not violations, (
        'tests/test_final_emission_gate.py owns gate orchestration/wrappers, not read-side replay projection assertions. '
        'Move these contracts to tests/test_final_emission_meta.py:\n' + '\n'.join(violations)
    )


def test_ad3_gate_orchestration_direct_owner_is_final_emission_gate() -> None:
    """Cycle AD-3: gate orchestration normative owner stays on the gate module."""
    rec = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    assert rec.direct_owner.replace('\\', '/') == 'tests/test_final_emission_gate.py'


def test_ad3_downstream_integration_smoke_suites_registered_as_neighbors() -> None:
    """Cycle AD-3: AD-thinned suites are downstream neighbors, never direct owners."""
    gate = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    sanitizer = RESPONSIBILITY_REGISTRY['output_sanitizer_final_string_cleanup']
    visibility = RESPONSIBILITY_REGISTRY['final_emission_visibility_semantics']
    social = RESPONSIBILITY_REGISTRY['social_emission_legality_surface']
    gate_downstream = frozenset((p.replace('\\', '/') for p in gate.downstream_consumer_suites))
    assert DOWNSTREAM_INTEGRATION_SMOKE_ONLY.issubset(gate_downstream)
    turn_pipeline = 'tests/test_turn_pipeline_shared.py'
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in frozenset(
        (p.replace('\\', '/') for p in sanitizer.downstream_consumer_suites)
    )
    assert turn_pipeline in frozenset(
        (p.replace('\\', '/') for p in visibility.downstream_consumer_suites)
    )
    ac_rd = frozenset(
        {'tests/test_answer_completeness_rules.py', 'tests/test_response_delta_requirement.py'}
    )
    assert ac_rd.issubset(gate_downstream)
    assert ac_rd.issubset(
        frozenset((p.replace('\\', '/') for p in social.downstream_consumer_suites))
    )
    for gid, rec in RESPONSIBILITY_REGISTRY.items():
        owner = rec.direct_owner.replace('\\', '/')
        assert owner not in DOWNSTREAM_INTEGRATION_SMOKE_ONLY, (
            f'{gid} must not list {owner!r} as direct_owner (downstream integration smoke only).'
        )


def test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner() -> None:
    """Cycle AD-3: replay observation locks live under gauntlet neighbor, not gate orchestration."""
    gate = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    gauntlet = RESPONSIBILITY_REGISTRY['gauntlet_playability_validation']
    golden = 'tests/test_golden_replay.py'
    assert golden in frozenset((p.replace('\\', '/') for p in gauntlet.gauntlet_suites))
    assert gauntlet.direct_owner.replace('\\', '/') != gate.direct_owner.replace('\\', '/')
    assert golden not in frozenset((p.replace('\\', '/') for p in gate.downstream_consumer_suites))


def test_al4_legality_owners_and_smoke_facade_locked() -> None:
    """Cycle AL4: AL1–AL3 convergence boundaries stay aligned with registry direct owners."""
    assert (
        RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration'].direct_owner.replace('\\', '/')
        == _AL4_LEGALITY_OWNER_PATHS['final_emission_gate']
    )
    assert (
        RESPONSIBILITY_REGISTRY['final_emission_meta_projection'].direct_owner.replace('\\', '/')
        == _AL4_LEGALITY_OWNER_PATHS['final_emission_meta']
    )
    assert (
        RESPONSIBILITY_REGISTRY['output_sanitizer_final_string_cleanup'].direct_owner.replace('\\', '/')
        == _AL4_LEGALITY_OWNER_PATHS['output_sanitizer']
    )
    assert (
        RESPONSIBILITY_REGISTRY['social_emission_legality_surface'].direct_owner.replace('\\', '/')
        == _AL4_LEGALITY_OWNER_PATHS['social_exchange_emission']
    )
    turn_pipeline = _AL4_LEGALITY_OWNER_PATHS['turn_pipeline_http_smoke']
    gate_downstream = frozenset(
        (p.replace('\\', '/') for p in RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration'].downstream_consumer_suites)
    )
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in DOWNSTREAM_INTEGRATION_SMOKE_ONLY
    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    assert facade_path.is_file(), f'missing downstream smoke facade: {_DOWNSTREAM_SMOKE_FACADE}'
    route_owner = (_REPO_ROOT / _AL4_LEGALITY_OWNER_PATHS['dialogue_route_classification']).resolve()
    assert route_owner.is_file(), 'dialogue route legality owner must remain tests/test_dialogue_routing_lock.py'


def test_bj4_emission_smoke_facade_stays_weak_consumer_bridge() -> None:
    """Cycle BJ-4 / BV7A / BV7B: smoke facade stays weak; bridges live in dedicated modules."""
    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    source = facade_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and (not node.name.startswith('_'))
    }
    bv7b_extracted_repair = _BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES & (
        _BV7B_EXTRACTED_AC_SYMBOLS | _BV7B_EXTRACTED_RD_SYMBOLS
    )
    for expected_bridge in _BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES - bv7b_extracted_repair:
        assert expected_bridge in public_functions
    for expected_bridge in (
        _BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES
        - _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS
        - _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS
        - _BV7B_EXTRACTED_RT_SYMBOLS
    ):
        assert expected_bridge in public_functions
    gate_bridge_path = (_REPO_ROOT / _BD6_GATE_BRIDGE_FACADE).resolve()
    replay_bridge_path = (_REPO_ROOT / _BD6_REPLAY_BRIDGE_FACADE).resolve()
    replay_fem_path = (_REPO_ROOT / _BV12A_REPLAY_FEM_READ_FACADE).resolve()
    gate_orch_path = (_REPO_ROOT / _BV12A_GATE_ORCHESTRATION_FACADE).resolve()
    fallback_bridge_path = (_REPO_ROOT / _BV12A_FALLBACK_BRIDGE_FACADE).resolve()
    rt_bridge_path = (_REPO_ROOT / _BD6_RT_SMOKE_FACADE).resolve()
    ac_bridge_path = (_REPO_ROOT / _BD6_AC_SMOKE_FACADE).resolve()
    rd_bridge_path = (_REPO_ROOT / _BD6_RD_SMOKE_FACADE).resolve()
    assert gate_bridge_path.is_file(), f'missing BV7A gate bridge: {_BD6_GATE_BRIDGE_FACADE}'
    assert replay_bridge_path.is_file(), f'missing BV7A replay bridge: {_BD6_REPLAY_BRIDGE_FACADE}'
    assert replay_fem_path.is_file(), f'missing BV12A replay FEM facade: {_BV12A_REPLAY_FEM_READ_FACADE}'
    assert gate_orch_path.is_file(), f'missing BV12A gate orchestration facade: {_BV12A_GATE_ORCHESTRATION_FACADE}'
    assert fallback_bridge_path.is_file(), f'missing BV12A fallback bridge: {_BV12A_FALLBACK_BRIDGE_FACADE}'
    assert rt_bridge_path.is_file(), f'missing BV7B RT bridge: {_BD6_RT_SMOKE_FACADE}'
    assert ac_bridge_path.is_file(), f'missing BV7B AC bridge: {_BD6_AC_SMOKE_FACADE}'
    assert rd_bridge_path.is_file(), f'missing BV7B RD bridge: {_BD6_RD_SMOKE_FACADE}'

    def _public_functions(module_path: Path) -> set[str]:
        module_tree = ast.parse(module_path.read_text(encoding='utf-8'))
        return {
            node.name
            for node in module_tree.body
            if isinstance(node, ast.FunctionDef) and (not node.name.startswith('_'))
        }

    def _module_all_exports(module_path: Path) -> set[str]:
        module_tree = ast.parse(module_path.read_text(encoding='utf-8'))
        for node in module_tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == '__all__' and isinstance(node.value, (ast.List, ast.Tuple)):
                    return {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
        return set()

    gate_functions = _public_functions(gate_orch_path)
    replay_functions = _public_functions(replay_fem_path)
    gate_compat_exports = _module_all_exports(gate_bridge_path)
    replay_compat_exports = _module_all_exports(replay_bridge_path)
    rt_functions = _public_functions(rt_bridge_path)
    ac_functions = _public_functions(ac_bridge_path)
    rd_functions = _public_functions(rd_bridge_path)
    for expected_gate in _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS:
        assert expected_gate in gate_functions, (
            f'expected gate bridge {expected_gate!r} in {_BV12A_GATE_ORCHESTRATION_FACADE}'
        )
        assert expected_gate in gate_compat_exports, (
            f'expected gate compat re-export {expected_gate!r} in {_BD6_GATE_BRIDGE_FACADE}'
        )
    for expected_replay in _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS:
        assert expected_replay in replay_functions, (
            f'expected replay bridge {expected_replay!r} in {_BV12A_REPLAY_FEM_READ_FACADE}'
        )
        assert expected_replay in replay_compat_exports, (
            f'expected replay compat re-export {expected_replay!r} in {_BD6_REPLAY_BRIDGE_FACADE}'
        )
    for expected_rt in _BV7B_EXTRACTED_RT_SYMBOLS:
        assert expected_rt in rt_functions, f'expected RT bridge {expected_rt!r} in {_BD6_RT_SMOKE_FACADE}'
    for expected_ac in _BV7B_EXTRACTED_AC_SYMBOLS:
        assert expected_ac in ac_functions, f'expected AC bridge {expected_ac!r} in {_BD6_AC_SMOKE_FACADE}'
    for expected_rd in _BV7B_EXTRACTED_RD_SYMBOLS:
        assert expected_rd in rd_functions, f'expected RD bridge {expected_rd!r} in {_BD6_RD_SMOKE_FACADE}'
    facade_all = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == '__all__' and isinstance(node.value, (ast.List, ast.Tuple)):
                facade_all = {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
    bv7_extracted = (
        _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS
        | _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS
        | _BV7B_EXTRACTED_RT_SYMBOLS
        | _BV7B_EXTRACTED_AC_SYMBOLS
        | _BV7B_EXTRACTED_RD_SYMBOLS
    )
    for expected_bridge in bv7_extracted:
        assert expected_bridge in facade_all, (
            f'compatibility facade must re-export {expected_bridge!r} via __all__'
        )
    public_names = set(public_functions)
    public_table_lengths: dict[str, int] = {}
    for node in tree.body:
        target_name: str | None = None
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        if not target_name or target_name.startswith('_'):
            continue
        public_names.add(target_name)
        if target_name.isupper() and isinstance(value, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            public_table_lengths[target_name] = len(value.keys if isinstance(value, ast.Dict) else value.elts)
    forbidden_public_names = {
        name: reason
        for name in public_names
        for fragment, reason in _BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS.items()
        if fragment in name.lower()
    }
    assert not forbidden_public_names, (
        f'emission_smoke_assertions.py must not grow public legality-owner helpers/constants: {forbidden_public_names!r}'
    )
    oversized_public_tables = {name: size for name, size in public_table_lengths.items() if size > 8}
    assert not oversized_public_tables, (
        'emission_smoke_assertions.py must not grow large public phrase/route/repair tables; '
        f'move legality matrices to owner suites: {oversized_public_tables!r}'
    )
    low = source.lower()
    assert 'ownership note' in low
    assert 'weak downstream smoke/consumer bridges' in low
    assert 'must not become the owner' in low
    assert 'full gate legality matrices' in low
    assert 'route enum tables' in low
    assert 'sanitizer phrase legality' in low
    assert 'ac/rd repair semantics' in low


def test_be6_scaffold_phrase_triple_layer_split_locked() -> None:
    """Cycle BE6: sanitizer legality, HTTP smoke phrases, and replay scaffold projection stay separate."""
    for label, rel_path in _BE6_SCAFFOLD_PHRASE_LAYER_OWNERS.items():
        path = (_REPO_ROOT / rel_path).resolve()
        assert path.is_file(), f'BE6 layer {label!r} missing owner path: {rel_path}'
    smoke_doc = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).read_text(encoding='utf-8')
    assert 'BE6' in smoke_doc, 'emission_smoke_assertions must document Cycle BE6 triple-layer split'
    assert 'do not merge' in smoke_doc.lower(), 'emission_smoke_assertions must warn against merging phrase matrices'
    assert 'tests/test_output_sanitizer.py' in smoke_doc
    assert 'golden_replay_projection' in smoke_doc
    assert 'final_text_has_scaffold_leakage' in smoke_doc
    governance_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BE6' in governance_doc, 'gate boundary governance must document Cycle BE6 triple-layer split'
    assert 'do not merge' in governance_doc.lower()
