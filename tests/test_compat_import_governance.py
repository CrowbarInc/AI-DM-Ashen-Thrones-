"""BD/BV compatibility barrel, import-cap, facade-routing, and compressed dependency guards (tests only).

This module owns **structural import-governance pytest entrypoints** for compatibility barrel
regrowth lockdown, read-cluster facade routing, smoke-monolith import caps, gate dependency
compression, and terminal monkeypatch governance (Cycles BD-6, BV2C, BV7C, BV10C, BV12C–BV14C,
BV16C).

This is **not** the global test-responsibility ownership registry. Registry identity, inventory
parity, direct-owner relationship checks, and registry neighbor assertions remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_guard_bd_dependency_compression.py``,
``tests/ownership_guard_bv_compatibility.py``, and ``tests/ownership_guard_bv16c_terminal_monkeypatch.py``.

- **Gate dependency compression guard** (Cycle BD-6): non-owner tests must not reintroduce
  direct imports of gate entry, FEM read, replay projection, or owner-bucket constants already
  routed through helper facades during BD-2–BD-5. Enforced by ``test_bd6_gate_dependency_compression_*``.
- **BV7C smoke monolith import lockdown** (Cycle BV7C): non-barrel modules must not import
  BV7A/BV7B extracted bridge or consumer-layer symbols from
  ``tests/helpers/emission_smoke_assertions.py``; route through
  ``response_type_smoke``, ``actor_consistency_smoke``, ``route_determinism_smoke``,
  ``replay_fem_read_smoke``, ``gate_orchestration_smoke``, or ``fallback_bridge_smoke``.
  Compatibility barrels ``replay_smoke_assertions`` and ``gate_integration_smoke`` remain
  re-export-only shims (BV12B consumer migration complete). Monolith FI capped at 18 static
  importers (phrase/route/speaker smoke only). Enforced by ``test_bv7c_smoke_monolith_*``.
- **BV12A/BV12B smoke-bridge domain facades** (Cycle BV12A/BV12B): replay FEM read, gate
  orchestration, and fallback dual-bridge surfaces live in ``replay_fem_read_smoke``,
  ``gate_orchestration_smoke``, and ``fallback_bridge_smoke``. BV12B migrated consumers off
  compatibility barrels onto domain facades; barrels remain re-export shims for BV12C governance.
- **BV12C compat barrel regrowth lockdown** (Cycle BV12C): non-barrel modules must not import
  ``replay_smoke_assertions`` or ``gate_integration_smoke`` directly; route through
  ``replay_fem_read_smoke``, ``gate_orchestration_smoke``, or ``fallback_bridge_smoke``.
  Compat barrel FI capped at 2 each (delegate verification residual only). Enforced by
  ``test_bv12c_compat_barrel_*``. Intentional domain hubs:
  ``tests.helpers.replay_fem_read_smoke`` (FEM read + debug notes),
  ``tests.helpers.gate_orchestration_smoke`` (gate consumer + HTTP stub),
  ``tests.helpers.fallback_bridge_smoke`` (dual-bridge fallback suites).
- **BV13C text compat barrel regrowth lockdown** (Cycle BV13C): non-barrel modules must not import
  ``game.final_emission_text`` for formatting or policy symbols; route through
  ``final_emission_text_formatting`` or ``final_emission_text_policy``. Compat barrel FI capped at
  8 (fallback wrapper + delegate verification residual only). Enforced by
  ``test_bv13c_text_compat_*``. Intentional text domain hubs:
  ``game.final_emission_text_formatting`` (text normalization/sanitization primitives),
  ``game.final_emission_text_policy`` (validator policy vocabulary tuples),
  ``game.final_emission_text_legacy_semantic_repair`` (test-only legacy semantic repair).
- **BV14C social-exchange compat barrel regrowth lockdown** (Cycle BV14C): non-barrel modules must
  not import ``game.social_exchange_emission`` for fallback, policy, validation, or projection
  symbols; route through ``social_exchange_fallback_catalog``, ``social_exchange_policy``,
  ``social_exchange_validation``, or ``social_exchange_projection``. Compat barrel FI capped at 12
  (composition authority + BD-2 legality + delegate verification residual only). Enforced by
  ``test_bv14c_social_exchange_compat_*``. Intentional social-exchange domain hubs:
  ``game.social_exchange_fallback_catalog`` (strict-social fallback phrase catalog),
  ``game.social_exchange_policy`` (strict-social routing/policy predicates),
  ``game.social_exchange_validation`` (route legality + interruption shape validators),
  ``game.social_exchange_projection`` (final-emission logging/trace projection).
- **BV2C meta import lockdown** (Cycle BV2C): non-owner ``game/`` and ``tests/`` modules must not
  import ``game.final_emission_meta`` directly except production write owners and the FEM owner /
  governance suites. Read traffic routes through ``final_emission_meta_read``,
  ``final_emission_owner_bucket_views``, or ``final_emission_replay_projection``. Enforced by
  ``test_bv2c_final_emission_meta_direct_import_guard_*``.
- **BV10 read-cluster facade routing** (Cycle BV10C): non-owner modules must not import
  ``final_emission_meta_read``, ``final_emission_owner_bucket_views``, or
  ``final_emission_ownership_schema`` directly except production write owners, vocabulary
  authority modules, facade delegates, and allowlisted owner suites. Route attribution reads
  through ``game.attribution_read_views``; lineage/sanitizer projection through
  ``game.ownership_projection_views``; observability/FEM dict reads through
  ``game.observability_attribution_read`` or ``tests/helpers/replay_fem_read_smoke``.
  Enforced by ``test_bv10_read_cluster_direct_import_guard_*``.
- **BV16C terminal monkeypatch guard** (Cycle BV16C): tests must monkeypatch finalize-tail owner
  modules (``game.final_emission_visibility_fallback``, ``game.final_emission_acceptance_quality``,
  ``game.interaction_continuity``, ``game.final_emission_opening_fallback``,
  ``game.final_emission_repairs``), not ``game.final_emission_terminal_pipeline`` delegate
  symbols. Enforced by
  ``test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance``.
"""

from __future__ import annotations

from pathlib import Path

from tests.ownership_guard_bd_dependency_compression import (
    _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
    collect_gate_dependency_compression_guard_violations,
    iter_gate_dependency_compression_guard_scan_paths,
)
from tests.ownership_guard_bv16c_terminal_monkeypatch import (
    BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS,
    BV16C_IC_OWNER,
    BV16C_N4_OWNER,
    BV16C_OPENING_OWNER,
    BV16C_REPAIRS_OWNER,
    BV16C_TERMINAL_ORCHESTRATION_SYMBOLS,
    BV16C_TERMINAL_PIPELINE_MODULE,
    BV16C_VISIBILITY_OWNER,
    collect_bv16c_terminal_delegate_monkeypatch_violations,
    iter_bv16c_terminal_monkeypatch_scan_paths,
)
from tests.ownership_guard_bv_compatibility import (
    _BD6_AC_SMOKE_FACADE,
    _BD6_RD_SMOKE_FACADE,
    _BD6_RT_SMOKE_FACADE,
    _BV10C_ATTRIBUTION_READ_FACADE,
    _BV10C_OBSERVABILITY_READ_FACADE,
    _BV10C_READ_CLUSTER_TEST_ALLOWLIST,
    _BV12A_GATE_ORCHESTRATION_FACADE,
    _BV12A_REPLAY_FEM_READ_FACADE,
    _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS,
    _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS,
    _BV12C_COMPAT_BARREL_FI_CAP,
    _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST,
    _BV12C_GATE_COMPAT_MODULE,
    _BV12C_INTENTIONAL_DOMAIN_HUBS,
    _BV12C_REPLAY_COMPAT_MODULE,
    _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS,
    _BV13C_INTENTIONAL_TEXT_DOMAIN_HUBS,
    _BV13C_TEXT_COMPAT_FI_CAP,
    _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST,
    _BV13C_TEXT_COMPAT_MODULE,
    _BV13C_TEXT_FORMATTING_AUTHORITY,
    _BV13C_TEXT_POLICY_AUTHORITY,
    _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS,
    _BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE,
    _BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY,
    _BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST,
    _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS,
    _BV7C_MONOLITH_FI_CAP,
    _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST,
    collect_bv10_read_cluster_direct_import_guard_violations,
    collect_bv12c_compat_barrel_import_guard_violations,
    collect_bv12c_compat_barrel_static_importers,
    collect_bv13c_text_compat_import_guard_violations,
    collect_bv13c_text_compat_static_importers,
    collect_bv14c_social_exchange_compat_import_guard_violations,
    collect_bv14c_social_exchange_compat_static_importers,
    collect_bv2c_final_emission_meta_import_violations,
    collect_bv7c_monolith_static_importers,
    collect_bv7c_smoke_monolith_import_guard_violations,
    iter_bv10_read_cluster_direct_import_guard_scan_paths,
    iter_bv12c_compat_barrel_import_guard_scan_paths,
    iter_bv13c_text_compat_import_guard_scan_paths,
    iter_bv14c_social_exchange_compat_import_guard_scan_paths,
    iter_bv2c_final_emission_meta_import_guard_scan_paths,
    iter_bv7c_smoke_monolith_import_guard_scan_paths,
    assert_compat_allowlist_entries_have_reasons,
    assert_compat_live_scan_paths_clean,
    assert_compat_synthetic_violation,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons() -> None:
    """BD-6: every compression-guard allowlist path documents why it may import compressed gate symbols."""
    assert_compat_allowlist_entries_have_reasons(
        _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
        path_prefix='tests/',
        empty_reason_label='BD-6',
    )

def test_bd6_gate_dependency_compression_guard_detects_synthetic_violation() -> None:
    """BD-6: guard flags representative compressed imports with facade guidance."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\nfrom game.final_emission_meta import read_final_emission_meta_from_turn_payload, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED\nimport game.final_emission_replay_projection as replay\n'
    rel = 'tests/test_synthetic_bd6_violation.py'
    assert_compat_synthetic_violation(
        collect_gate_dependency_compression_guard_violations,
        rel,
        synthetic,
        expected_in_violation_lines=(
            'apply_final_emission_gate',
            'read_final_emission_meta_from_turn_payload',
            'OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED',
            'final_emission_replay_projection',
        ),
        expected_in_joined=(
            'apply_final_emission_gate_consumer',
            'final_emission_meta_from_output',
            'opening_fallback_evidence',
            'build_fem_runtime_lineage_events',
        ),
    )

def test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports() -> None:
    """BD-6: non-owner tests must not reintroduce direct imports compressed during BD-2–BD-5."""
    assert_compat_live_scan_paths_clean(
        iter_gate_dependency_compression_guard_scan_paths(),
        collect_gate_dependency_compression_guard_violations,
        cycle_tag='BD-6',
        violation_label='gate dependency compression-guard import violations',
        repo_root=_REPO_ROOT,
    )

def test_bv2c_final_emission_meta_direct_import_allowlist_entries_have_non_empty_reasons() -> None:
    """BV2C: every meta direct-import allowlist path documents why it may import the write owner."""
    assert_compat_allowlist_entries_have_reasons(
        _BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST,
        path_prefix='tests/',
        empty_reason_label='BV2C',
    )

def test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation() -> None:
    """BV2C: guard flags representative read-side imports with facade guidance."""
    synthetic = 'from game.final_emission_meta import read_final_emission_meta_dict, default_response_type_debug\nimport game.final_emission_meta as emission_meta\n'
    rel = 'tests/test_synthetic_bv2c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv2c_final_emission_meta_import_violations,
        rel,
        synthetic,
        expected_in_violation_lines=(
            'read_final_emission_meta_dict',
            'default_response_type_debug',
        ),
        expected_in_joined=('game.final_emission_meta_read',),
    )

def test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades() -> None:
    """BV2C: non-owner modules must not import game.final_emission_meta directly."""
    assert_compat_live_scan_paths_clean(
        iter_bv2c_final_emission_meta_import_guard_scan_paths(),
        collect_bv2c_final_emission_meta_import_violations,
        cycle_tag='BV2C',
        violation_label='BV2C final_emission_meta direct-import violations',
        repo_root=_REPO_ROOT,
    )

def test_bv10_read_cluster_direct_import_allowlist_entries_have_non_empty_reasons() -> None:
    """BV10C: every read-cluster allowlist path documents why it may import authority modules."""
    assert_compat_allowlist_entries_have_reasons(
        _BV10C_READ_CLUSTER_TEST_ALLOWLIST,
        path_prefix='tests/',
        empty_reason_label='BV10C',
    )

def test_bv10_read_cluster_direct_import_guard_detects_synthetic_violation() -> None:
    """BV10C: guard flags representative read-cluster authority imports with facade guidance."""
    synthetic = 'from game.final_emission_meta_read import read_final_emission_meta_dict\nfrom game.final_emission_owner_bucket_views import opening_fallback_owner_bucket_from_meta\nfrom game.final_emission_ownership_schema import ALLOWED_FALLBACK_SELECTION_OWNERS\n'
    rel = 'tests/test_synthetic_bv10c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv10_read_cluster_direct_import_guard_violations,
        rel,
        synthetic,
        expected_in_violation_lines=(
            'read_final_emission_meta_dict',
            'opening_fallback_owner_bucket_from_meta',
            'ALLOWED_FALLBACK_SELECTION_OWNERS',
        ),
        expected_in_joined=(
            _BV10C_ATTRIBUTION_READ_FACADE,
            _BV10C_OBSERVABILITY_READ_FACADE,
        ),
    )

def test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades() -> None:
    """BV10C: non-owner modules must not import read-cluster authority modules directly."""
    assert_compat_live_scan_paths_clean(
        iter_bv10_read_cluster_direct_import_guard_scan_paths(),
        collect_bv10_read_cluster_direct_import_guard_violations,
        cycle_tag='BV10C',
        violation_label='BV10C read-cluster direct-import violations',
        repo_root=_REPO_ROOT,
    )

def test_bv7c_smoke_monolith_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV7C: every monolith import-guard allowlist path documents why it may import extracted symbols."""
    assert_compat_allowlist_entries_have_reasons(
        _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST,
        path_prefix='tests/',
        empty_reason_label='BV7C',
    )

def test_bv7c_smoke_monolith_import_guard_detects_synthetic_violation() -> None:
    """BV7C: guard flags representative extracted-symbol imports with facade guidance."""
    synthetic = 'from tests.helpers.emission_smoke_assertions import response_type_contract\nfrom tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer\nfrom tests.helpers.emission_smoke_assertions import final_emission_meta_from_output\nfrom tests.helpers.emission_smoke_assertions import validate_answer_completeness\nfrom tests.helpers.emission_smoke_assertions import apply_response_delta_layer\n'
    rel = 'tests/test_synthetic_bv7c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv7c_smoke_monolith_import_guard_violations,
        rel,
        synthetic,
        expected_in_violation_lines=(
            'response_type_contract',
            'apply_final_emission_gate_consumer',
            'final_emission_meta_from_output',
            'validate_answer_completeness',
            'apply_response_delta_layer',
        ),
        expected_in_joined=(
            _BD6_RT_SMOKE_FACADE,
            _BV12A_GATE_ORCHESTRATION_FACADE,
            _BV12A_REPLAY_FEM_READ_FACADE,
            _BD6_AC_SMOKE_FACADE,
            _BD6_RD_SMOKE_FACADE,
        ),
    )

def test_bv7c_smoke_monolith_import_guard_non_owners_route_through_family_facades() -> None:
    """BV7C: non-barrel modules must not reimport BV7A/BV7B extracted symbols from monolith."""
    assert_compat_live_scan_paths_clean(
        iter_bv7c_smoke_monolith_import_guard_scan_paths(),
        collect_bv7c_smoke_monolith_import_guard_violations,
        cycle_tag='BV7C',
        violation_label='BV7C smoke monolith import-guard violations',
        repo_root=_REPO_ROOT,
    )

def test_bv7c_emission_smoke_assertions_concentration_locked() -> None:
    """BV7C: monolith FI stays within smoke-core band; no new static importers without registry update."""
    source_by_rel: dict[str, str] = {}
    for rel in iter_bv7c_smoke_monolith_import_guard_scan_paths():
        source_by_rel[rel] = (_REPO_ROOT / rel).read_text(encoding='utf-8')
    static_importers = collect_bv7c_monolith_static_importers(source_by_rel)
    assert len(static_importers) <= _BV7C_MONOLITH_FI_CAP, f'emission_smoke_assertions static importer count {len(static_importers)} exceeds BV7C cap {_BV7C_MONOLITH_FI_CAP}: {sorted(static_importers - _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS)!r}'
    unexpected = static_importers - _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS
    assert not unexpected, f'new static emission_smoke_assertions importers require BV7C registry update: {sorted(unexpected)!r}'
    missing = _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS - static_importers
    assert not missing, f'BV7C allowed importer registry drift — remove stale entries or restore imports: {sorted(missing)!r}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV7C' in registry_doc

def test_bv12c_compat_barrel_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV12C: every compat-barrel import-guard allowlist path documents why it may import compat barrels."""
    assert_compat_allowlist_entries_have_reasons(
        _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST,
        path_prefix=('tests/', 'tools/', 'scripts/'),
        empty_reason_label='BV12C',
    )

def test_bv12c_compat_barrel_import_guard_detects_synthetic_violation() -> None:
    """BV12C: guard flags compat-barrel imports with domain-facade guidance."""
    synthetic = 'import tests.helpers.replay_smoke_assertions as replay_smoke_assertions\nimport tests.helpers.gate_integration_smoke as gate_integration_smoke\nfrom tests.helpers.replay_smoke_assertions import final_emission_meta_from_output\nfrom tests.helpers.gate_integration_smoke import apply_final_emission_gate_consumer\n'
    rel = 'tests/test_synthetic_bv12c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv12c_compat_barrel_import_guard_violations,
        rel,
        synthetic,
        expected_in_violation_lines=(
            _BV12C_REPLAY_COMPAT_MODULE,
            _BV12C_GATE_COMPAT_MODULE,
        ),
        expected_in_joined=(
            _BV12A_REPLAY_FEM_READ_FACADE,
            _BV12A_GATE_ORCHESTRATION_FACADE,
        ),
    )

def test_bv12c_compat_barrel_import_guard_non_owners_route_through_domain_facades() -> None:
    """BV12C: non-barrel modules must not import compat smoke bridge barrels directly."""
    assert_compat_live_scan_paths_clean(
        iter_bv12c_compat_barrel_import_guard_scan_paths(),
        collect_bv12c_compat_barrel_import_guard_violations,
        cycle_tag='BV12C',
        violation_label='BV12C compat-barrel import-guard violations',
        repo_root=_REPO_ROOT,
    )

def test_bv12c_compat_barrel_fi_cap_locked() -> None:
    """BV12C: compat barrel FI stays at delegate-verification residual; domain hubs documented separately."""
    replay_importers = collect_bv12c_compat_barrel_static_importers(compat_module=_BV12C_REPLAY_COMPAT_MODULE)
    gate_importers = collect_bv12c_compat_barrel_static_importers(compat_module=_BV12C_GATE_COMPAT_MODULE)
    assert len(replay_importers) <= _BV12C_COMPAT_BARREL_FI_CAP, f'replay_smoke_assertions static importer count {len(replay_importers)} exceeds BV12C cap {_BV12C_COMPAT_BARREL_FI_CAP}: {sorted(replay_importers - _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS)!r}'
    assert len(gate_importers) <= _BV12C_COMPAT_BARREL_FI_CAP, f'gate_integration_smoke static importer count {len(gate_importers)} exceeds BV12C cap {_BV12C_COMPAT_BARREL_FI_CAP}: {sorted(gate_importers - _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS)!r}'
    unexpected_replay = replay_importers - _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS
    unexpected_gate = gate_importers - _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS
    assert not unexpected_replay, f'new replay_smoke_assertions importers require BV12C registry update: {sorted(unexpected_replay)!r}'
    assert not unexpected_gate, f'new gate_integration_smoke importers require BV12C registry update: {sorted(unexpected_gate)!r}'
    assert replay_importers == _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS
    assert gate_importers == _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV12C' in registry_doc
    for hub, role in _BV12C_INTENTIONAL_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty domain hub role for {hub!r}'

def test_bv13c_text_compat_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV13C: every text compat-barrel import-guard allowlist path documents why it may import compat."""
    assert_compat_allowlist_entries_have_reasons(
        _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST,
        path_prefix=('game/', 'tests/', 'tools/', 'scripts/'),
        empty_reason_label='BV13C',
    )

def test_bv13c_text_compat_import_guard_detects_synthetic_violation() -> None:
    """BV13C: guard flags compat-barrel imports with formatting/policy authority guidance."""
    synthetic = 'from game.final_emission_text import _normalize_text\nimport game.final_emission_text as emission_text\n'
    rel = 'tests/test_synthetic_bv13c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv13c_text_compat_import_guard_violations,
        rel,
        synthetic,
        expected_in_joined=(
            _BV13C_TEXT_COMPAT_MODULE,
            _BV13C_TEXT_FORMATTING_AUTHORITY,
            _BV13C_TEXT_POLICY_AUTHORITY,
        ),
    )

def test_bv13c_text_compat_import_guard_non_owners_route_through_authorities() -> None:
    """BV13C: non-barrel modules must not import final_emission_text compat barrel directly."""
    assert_compat_live_scan_paths_clean(
        iter_bv13c_text_compat_import_guard_scan_paths(),
        collect_bv13c_text_compat_import_guard_violations,
        cycle_tag='BV13C',
        violation_label='BV13C text compat-barrel import-guard violations',
        repo_root=_REPO_ROOT,
    )

def test_bv13c_text_compat_fi_cap_locked() -> None:
    """BV13C: text compat barrel FI stays at fallback-wrapper residual; domain hubs documented separately."""
    importers = collect_bv13c_text_compat_static_importers()
    assert len(importers) <= _BV13C_TEXT_COMPAT_FI_CAP, f'final_emission_text static importer count {len(importers)} exceeds BV13C cap {_BV13C_TEXT_COMPAT_FI_CAP}: {sorted(importers - _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS)!r}'
    unexpected = importers - _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS
    assert not unexpected, f'new final_emission_text importers require BV13C registry update: {sorted(unexpected)!r}'
    assert importers == _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV13C' in registry_doc
    for hub, role in _BV13C_INTENTIONAL_TEXT_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional text domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty text domain hub role for {hub!r}'

def test_bv14c_social_exchange_compat_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV14C: every social-exchange compat-barrel import-guard allowlist path documents why it may import compat."""
    assert_compat_allowlist_entries_have_reasons(
        _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST,
        path_prefix=('game/', 'tests/', 'tools/', 'scripts/'),
        empty_reason_label='BV14C',
    )

def test_bv14c_social_exchange_compat_import_guard_detects_synthetic_violation() -> None:
    """BV14C: guard flags compat-barrel imports with fallback/policy/validation/projection authority guidance."""
    synthetic = 'from game.social_exchange_emission import strict_social_emission_will_apply\nimport game.social_exchange_emission as social_exchange_emission\n'
    rel = 'tests/test_synthetic_bv14c_violation.py'
    assert_compat_synthetic_violation(
        collect_bv14c_social_exchange_compat_import_guard_violations,
        rel,
        synthetic,
        expected_in_joined=(
            _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE,
            _BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY,
            _BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY,
            _BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY,
            _BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY,
        ),
    )

def test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities() -> None:
    """BV14C: non-barrel modules must not import social_exchange_emission compat barrel directly."""
    assert_compat_live_scan_paths_clean(
        iter_bv14c_social_exchange_compat_import_guard_scan_paths(),
        collect_bv14c_social_exchange_compat_import_guard_violations,
        cycle_tag='BV14C',
        violation_label='BV14C social-exchange compat-barrel import-guard violations',
        repo_root=_REPO_ROOT,
    )

def test_bv14c_social_exchange_compat_fi_cap_locked() -> None:
    """BV14C: social-exchange compat barrel FI stays at composition-authority residual; domain hubs documented separately."""
    importers = collect_bv14c_social_exchange_compat_static_importers()
    assert len(importers) <= _BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP, f'social_exchange_emission static importer count {len(importers)} exceeds BV14C cap {_BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP}: {sorted(importers - _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS)!r}'
    unexpected = importers - _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS
    assert not unexpected, f'new social_exchange_emission importers require BV14C registry update: {sorted(unexpected)!r}'
    assert importers == _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV14C' in registry_doc
    for hub, role in _BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional social-exchange domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty social-exchange domain hub role for {hub!r}'

def test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance() -> None:
    """Cycle BV16C: tests must monkeypatch finalize-tail owner modules, not terminal_pipeline delegates."""
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    violations: list[str] = []
    for rel in iter_bv16c_terminal_monkeypatch_scan_paths(repo_root):
        source = (repo_root / rel).read_text(encoding='utf-8')
        violations.extend(collect_bv16c_terminal_delegate_monkeypatch_violations(rel, source))
    assert not violations, 'BV16C terminal delegate monkeypatch violations:\n' + '\n'.join(violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV16C' in registry_doc
    assert BV16C_TERMINAL_PIPELINE_MODULE in registry_doc
    assert BV16C_VISIBILITY_OWNER in registry_doc
    assert BV16C_N4_OWNER in registry_doc
    assert BV16C_IC_OWNER in registry_doc
    assert BV16C_OPENING_OWNER in registry_doc
    assert BV16C_REPAIRS_OWNER in registry_doc
    assert 'run_gate_terminal_enforcement_pipeline' in BV16C_TERMINAL_ORCHESTRATION_SYMBOLS
    assert BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS
