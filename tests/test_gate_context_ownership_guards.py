"""Gate-context / preflight structural import guards (tests only).

This module owns **BN1–BN11** gate-context and runtime-entry import/preflight regrowth locks:
runtime gate-entry seam (BN1), lazy gate namespace (BN2), and gate-context preflight helper
routing (BN3–BN11).

This is **not** the global test-responsibility ownership registry. Registry identity,
inventory parity, and registry neighbor relationship assertions remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_guard_bn_gate_context.py``.

- **Runtime gate entry guard** (Cycle BN1): non-owner ``game/`` modules must not import
  ``apply_final_emission_gate`` from ``game.final_emission_gate``; runtime/API callers use
  ``game.final_emission_runtime.finalize_player_facing_emission``. Enforced by
  ``test_bn1_runtime_gate_entry_*``.
- **Lazy gate namespace guard** (Cycle BN2): ``final_emission_non_strict_stack`` and
  ``final_emission_terminal_pipeline`` must not lazy-import ``game.final_emission_gate as feg``
  or access ``feg.<symbol>``; layer owners are imported directly. Enforced by
  ``test_bn2_lazy_gate_namespace_*``.
- **Gate context preflight import guard** (Cycle BN3): ``final_emission_gate_context`` must not
  regrow direct layer-meta owner imports after preflight-defaults extraction; use
  ``final_emission_gate_preflight_defaults``. Enforced by ``test_bn3_gate_context_*``.
- **Gate context telemetry import guard** (Cycle BN4): ``final_emission_gate_context`` must not
  regrow direct telemetry/provenance imports after preflight-telemetry extraction; use
  ``final_emission_gate_preflight_telemetry``. Enforced by ``test_bn4_gate_context_*``.
- **Gate context upstream attach import guard** (Cycle BN5): ``final_emission_gate_context`` must
  not regrow direct upstream attach imports after preflight-upstream extraction; use
  ``final_emission_gate_preflight_upstream``. Enforced by ``test_bn5_gate_context_*``.
- **Gate context turn-packet import guard** (Cycle BN6): ``final_emission_gate_context`` must not
  regrow direct response-policy / turn-packet setup imports after preflight turn-packet extraction;
  use ``final_emission_gate_preflight_turn_packet``. Enforced by ``test_bn6_gate_context_*``.
- **Gate context interaction metadata import guard** (Cycle BN7): ``final_emission_gate_context``
  must not regrow direct interaction inspection imports after preflight interaction extraction; use
  ``final_emission_gate_preflight_interaction``. Enforced by ``test_bn7_gate_context_*``.
- **Gate context strict-social routing import guard** (Cycle BN8): ``final_emission_gate_context``
  must not regrow direct strict-social routing/sanitizer imports after preflight strict-social
  extraction; use ``final_emission_gate_preflight_strict_social``. Enforced by
  ``test_bn8_gate_context_*``.
- **Gate context pregate text import guard** (Cycle BN9): ``final_emission_gate_context`` must not
  regrow direct ``final_emission_text`` imports after preflight pregate-text extraction; use
  ``final_emission_gate_preflight_pregate_text``. Enforced by ``test_bn9_gate_context_*``.
- **Gate context branch-flag derivation guard** (Cycle BN10): branch flags must route through
  ``final_emission_gate_preflight_branch_flags``. Enforced by ``test_bn10_gate_context_*``.
- **Gate context preflight-only import allowlist** (Cycle BN11): ``final_emission_gate_context``
  may import only stdlib/typing plus ``final_emission_gate_preflight_*`` helpers. Enforced by
  ``test_bn11_gate_context_*`` (intentionally direct positive-allowlist lock).

Lane structure (CO70 closeout):
- **BN1/BN2**: allowlist + live-scan loop guards; runtime delegate seam (BN1) stays direct.
- **BN3–BN10**: CO67 orchestration helpers; CO69 consolidated helper collectors.
- **BN11**: intentionally direct positive-allowlist and scan-logic lock (not BN3–BN10 template).
- **Not in scope**: BJ delegate-closeout (``tests/test_gate_delegate_closeout_locks.py``).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

from tests.ownership_guard_bn_gate_context import (
    BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT,
    BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
    BN1_RUNTIME_GATE_ENTRY_REPLACEMENT,
    BN2_LAZY_GATE_NAMESPACE_FILES,
    BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE,
    BN3_GATE_CONTEXT_OWNER_MODULE,
    BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE,
    BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE,
    BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE,
    BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE,
    BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE,
    BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE,
    BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE,
    BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE,
    BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES,
    BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS,
    collect_bn1_runtime_gate_entry_guard_violations,
    collect_bn2_lazy_gate_namespace_violations,
    collect_bn3_gate_context_layer_meta_import_violations,
    collect_bn4_gate_context_telemetry_import_violations,
    collect_bn4_preflight_telemetry_helper_gate_import_violations,
    collect_bn5_gate_context_upstream_import_violations,
    collect_bn5_preflight_upstream_helper_gate_import_violations,
    collect_bn6_gate_context_turn_packet_import_violations,
    collect_bn6_preflight_turn_packet_helper_gate_import_violations,
    collect_bn7_gate_context_interaction_import_violations,
    collect_bn7_preflight_interaction_helper_gate_import_violations,
    collect_bn8_gate_context_strict_social_import_violations,
    collect_bn8_preflight_strict_social_helper_import_violations,
    collect_bn9_gate_context_pregate_text_import_violations,
    collect_bn9_preflight_pregate_text_helper_import_violations,
    collect_bn10_gate_context_branch_flags_violations,
    collect_bn10_preflight_branch_flags_helper_import_violations,
    collect_bn11_gate_context_preflight_only_import_violations,
    collect_bn11_scan_logic_runtime_gate_import_violations,
    gate_context_import_modules,
    iter_bn1_runtime_gate_entry_guard_scan_paths,
    assert_bn_cycle_documented,
    assert_bn_live_gate_context_clean,
    assert_bn_live_scan_paths_clean,
    assert_bn_owner_entrypoint_callable,
    assert_bn_synthetic_violation,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]

# CO70 — scope guard: explicit BN1–BN11 test inventory; extend allowlist deliberately.
_GATE_CONTEXT_BN_TEST_NAMES: Final[frozenset[str]] = frozenset(
    {
        'test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons',
        'test_bn1_runtime_gate_entry_guard_detects_synthetic_violation',
        'test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import',
        'test_bn1_runtime_delegate_seam_remains_narrow',
        'test_bn2_lazy_gate_namespace_allowlist_covers_scan_files',
        'test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation',
        'test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg',
        'test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked',
        'test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation',
        'test_bn3_gate_context_avoids_direct_layer_meta_owner_imports',
        'test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked',
        'test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation',
        'test_bn4_gate_context_avoids_direct_telemetry_provenance_imports',
        'test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked',
        'test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation',
        'test_bn5_gate_context_avoids_direct_upstream_attach_imports',
        'test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked',
        'test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation',
        'test_bn6_gate_context_avoids_direct_turn_packet_policy_imports',
        'test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked',
        'test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation',
        'test_bn7_gate_context_avoids_direct_interaction_inspection_imports',
        'test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked',
        'test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation',
        'test_bn8_gate_context_avoids_direct_strict_social_routing_imports',
        'test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked',
        'test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation',
        'test_bn9_gate_context_avoids_direct_pregate_text_imports',
        'test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked',
        'test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation',
        'test_bn10_gate_context_routes_branch_flags_through_helper',
        'test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation',
        'test_bn11_gate_context_preflight_only_import_allowlist_locked',
        'test_gate_context_module_scope_guard_bn_inventory_locked',
    }
)


def test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons() -> None:
    """BN1: every runtime gate-entry allowlist path documents why it may import gate entry."""
    for path, reason in BN1_RUNTIME_GATE_ENTRY_ALLOWLIST.items():
        assert path.startswith('game/'), path
        assert reason.strip(), f'empty BN1 allowlist reason for {path!r}'
    assert_bn_cycle_documented(Path(__file__).read_text(encoding='utf-8'), 'BN1')

def test_bn1_runtime_gate_entry_guard_detects_synthetic_violation() -> None:
    """BN1: guard flags direct gate entry imports in non-owner game modules."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\n'
    rel = 'game/synthetic_bn1_violation.py'
    violations = collect_bn1_runtime_gate_entry_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'apply_final_emission_gate' in joined
    assert BN1_RUNTIME_GATE_ENTRY_REPLACEMENT in joined
    assert BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT in joined

def test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import() -> None:
    """BN1: non-owner game modules must not import apply_final_emission_gate from the gate owner."""
    assert_bn_live_scan_paths_clean(
        iter_bn1_runtime_gate_entry_guard_scan_paths(),
        collect_bn1_runtime_gate_entry_guard_violations,
        cycle_tag='BN1',
        violation_label='BN1 runtime gate-entry import violations',
        repo_root=_REPO_ROOT,
    )

def test_bn1_runtime_delegate_seam_remains_narrow() -> None:
    """BN1: final_emission_runtime stays a thin delegate with no policy imports."""
    import game.final_emission_runtime as runtime
    runtime_src = Path(runtime.__file__).read_text(encoding='utf-8')
    assert 'def finalize_player_facing_emission' in runtime_src
    assert 'from game.final_emission_gate import apply_final_emission_gate' in runtime_src
    assert 'return apply_final_emission_gate(' in runtime_src
    forbidden_markers = ('from game.final_emission_meta import', 'from game.final_emission_replay_projection import', 'from game.output_sanitizer import', 'from game.final_emission_validators import')
    for marker in forbidden_markers:
        assert marker not in runtime_src, f'runtime seam must not import policy surface: {marker!r}'

def test_bn2_lazy_gate_namespace_allowlist_covers_scan_files() -> None:
    """BN2: retained-symbol map spans every lazy-namespace scan file."""
    assert BN2_LAZY_GATE_NAMESPACE_FILES == frozenset(BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE)
    assert_bn_cycle_documented(Path(__file__).read_text(encoding='utf-8'), 'BN2')

def test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation() -> None:
    """BN2: guard flags stale lazy feg namespace markers."""
    synthetic = 'def _gate_module():\n    import game.final_emission_gate as feg\n    return feg\ndef run():\n    feg = _gate_module()\n    feg._apply_visibility_enforcement(out)\n'
    rel = 'game/final_emission_terminal_pipeline.py'
    violations = collect_bn2_lazy_gate_namespace_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'def _gate_module(' in joined
    assert 'import game.final_emission_gate' in joined
    assert '_apply_visibility_enforcement' in joined

def test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg() -> None:
    """BN2: non_strict_stack and terminal_pipeline must not lazy-import gate namespace."""
    assert_bn_live_scan_paths_clean(
        sorted(BN2_LAZY_GATE_NAMESPACE_FILES),
        collect_bn2_lazy_gate_namespace_violations,
        cycle_tag='BN2',
        violation_label='BN2 lazy gate namespace violations',
        repo_root=_REPO_ROOT,
    )

def test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked() -> None:
    """BN3: preflight layer-meta defaults live on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_defaults',
        'initialize_gate_preflight_layer_meta_defaults',
        'GatePreflightLayerMetaDefaults',
    )

def test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation() -> None:
    """BN3: guard flags regrown direct layer-meta owner imports on gate_context."""
    synthetic = 'from game.final_emission_tone_escalation import default_tone_escalation_meta\ndef initialize_gate_execution_context():\n    return default_tone_escalation_meta()\n'
    assert_bn_synthetic_violation(
        collect_bn3_gate_context_layer_meta_import_violations,
        synthetic,
        'final_emission_tone_escalation',
        'preflight_defaults',
    )

def test_bn3_gate_context_avoids_direct_layer_meta_owner_imports() -> None:
    """BN3: gate_context routes layer-meta defaults through preflight_defaults helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN3',
        gate_context_collector=collect_bn3_gate_context_layer_meta_import_violations,
        gate_context_violation_label='BN3 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE,
    )

def test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked() -> None:
    """BN4: preflight telemetry/containment lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_telemetry',
        'apply_gate_preflight_telemetry_and_containment',
        'GatePreflightTelemetryResult',
    )

def test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation() -> None:
    """BN4: guard flags regrown direct telemetry/provenance imports on gate_context."""
    synthetic = "from game.stage_diff_telemetry import record_stage_snapshot\ndef initialize_gate_execution_context():\n    record_stage_snapshot(out, 'final_emission_gate_entry')\n"
    assert_bn_synthetic_violation(
        collect_bn4_gate_context_telemetry_import_violations,
        synthetic,
        'stage_diff_telemetry',
        'preflight_telemetry',
    )

def test_bn4_gate_context_avoids_direct_telemetry_provenance_imports() -> None:
    """BN4: gate_context routes telemetry/containment through preflight_telemetry helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN4',
        gate_context_collector=collect_bn4_gate_context_telemetry_import_violations,
        gate_context_violation_label='BN4 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE,
        helper_collector=collect_bn4_preflight_telemetry_helper_gate_import_violations,
        helper_violation_label='BN4 telemetry helper gate import violations',
    )

def test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked() -> None:
    """BN5: preflight upstream attach lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_upstream',
        'apply_gate_preflight_upstream_attach',
        'upstream_prepared_emission_payload',
    )

def test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation() -> None:
    """BN5: guard flags regrown direct upstream attach imports on gate_context."""
    synthetic = 'from game.upstream_response_repairs import merge_upstream_prepared_emission_into_gm_output\ndef initialize_gate_execution_context():\n    merge_upstream_prepared_emission_into_gm_output(out)\n'
    assert_bn_synthetic_violation(
        collect_bn5_gate_context_upstream_import_violations,
        synthetic,
        'upstream_response_repairs',
        'preflight_upstream',
    )

def test_bn5_gate_context_avoids_direct_upstream_attach_imports() -> None:
    """BN5: gate_context routes upstream attach through preflight_upstream helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN5',
        gate_context_collector=collect_bn5_gate_context_upstream_import_violations,
        gate_context_violation_label='BN5 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE,
        helper_collector=collect_bn5_preflight_upstream_helper_gate_import_violations,
        helper_violation_label='BN5 upstream helper gate import violations',
    )

def test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked() -> None:
    """BN6: preflight turn-packet/policy setup lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_turn_packet',
        'initialize_gate_preflight_turn_packet',
    )

def test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation() -> None:
    """BN6: guard flags regrown direct turn-packet/policy imports on gate_context."""
    synthetic = "from game.turn_packet import get_turn_packet\ndef initialize_gate_execution_context():\n    out['_gate_turn_packet_cache'] = get_turn_packet(out)\n"
    assert_bn_synthetic_violation(
        collect_bn6_gate_context_turn_packet_import_violations,
        synthetic,
        'turn_packet',
        'preflight_turn_packet',
    )

def test_bn6_gate_context_avoids_direct_turn_packet_policy_imports() -> None:
    """BN6: gate_context routes turn-packet/policy setup through preflight_turn_packet helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN6',
        gate_context_collector=collect_bn6_gate_context_turn_packet_import_violations,
        gate_context_violation_label='BN6 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE,
        helper_collector=collect_bn6_preflight_turn_packet_helper_gate_import_violations,
        helper_violation_label='BN6 turn-packet helper gate import violations',
    )

def test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked() -> None:
    """BN7: preflight interaction metadata lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_interaction',
        'resolve_gate_preflight_interaction_metadata',
        'GatePreflightInteractionMetadata',
    )

def test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation() -> None:
    """BN7: guard flags regrown direct interaction inspection imports on gate_context."""
    synthetic = 'from game.interaction_context import inspect as inspect_interaction_context\ndef initialize_gate_execution_context():\n    return inspect_interaction_context(session)\n'
    assert_bn_synthetic_violation(
        collect_bn7_gate_context_interaction_import_violations,
        synthetic,
        'interaction_context',
        'preflight_interaction',
    )

def test_bn7_gate_context_avoids_direct_interaction_inspection_imports() -> None:
    """BN7: gate_context routes interaction metadata through preflight_interaction helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN7',
        gate_context_collector=collect_bn7_gate_context_interaction_import_violations,
        gate_context_violation_label='BN7 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE,
        helper_collector=collect_bn7_preflight_interaction_helper_gate_import_violations,
        helper_violation_label='BN7 interaction helper gate import violations',
    )

def test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked() -> None:
    """BN8: preflight strict-social routing lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_strict_social',
        'resolve_gate_preflight_strict_social_routing',
        'GatePreflightStrictSocialRouting',
    )

def test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation() -> None:
    """BN8: guard flags regrown direct strict-social routing imports on gate_context."""
    synthetic = "from game.social_exchange_emission import strict_social_emission_will_apply\ndef initialize_gate_execution_context():\n    return strict_social_emission_will_apply(None, None, None, '')\n"
    assert_bn_synthetic_violation(
        collect_bn8_gate_context_strict_social_import_violations,
        synthetic,
        'social_exchange_emission',
        'preflight_strict_social',
    )

def test_bn8_gate_context_avoids_direct_strict_social_routing_imports() -> None:
    """BN8: gate_context routes strict-social setup through preflight_strict_social helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN8',
        gate_context_collector=collect_bn8_gate_context_strict_social_import_violations,
        gate_context_violation_label='BN8 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE,
        helper_collector=collect_bn8_preflight_strict_social_helper_import_violations,
        helper_violation_label='BN8 strict-social helper import violations',
    )

def test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked() -> None:
    """BN9: preflight pregate text/tag setup lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_pregate_text',
        'resolve_gate_preflight_pregate_text',
        'GatePreflightPregateText',
    )

def test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation() -> None:
    """BN9: guard flags regrown direct pregate text imports on gate_context."""
    synthetic = "from game.final_emission_text_formatting import _normalize_text\ndef initialize_gate_execution_context():\n    return _normalize_text(out.get('player_facing_text'))\n"
    assert_bn_synthetic_violation(
        collect_bn9_gate_context_pregate_text_import_violations,
        synthetic,
        'final_emission_text_formatting',
        'preflight_pregate_text',
    )

def test_bn9_gate_context_avoids_direct_pregate_text_imports() -> None:
    """BN9: gate_context routes pregate text/tag setup through preflight_pregate_text helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN9',
        gate_context_collector=collect_bn9_gate_context_pregate_text_import_violations,
        gate_context_violation_label='BN9 gate_context import violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE,
        helper_collector=collect_bn9_preflight_pregate_text_helper_import_violations,
        helper_violation_label='BN9 pregate text helper import violations',
    )

def test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked() -> None:
    """BN10: preflight branch-flag derivation lives on dedicated helper owner."""
    assert_bn_owner_entrypoint_callable(
        'game.final_emission_gate_preflight_branch_flags',
        'resolve_gate_preflight_branch_flags',
        'GatePreflightBranchFlags',
    )

def test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation() -> None:
    """BN10: guard flags inline branch-flag derivation regrown on gate_context."""
    synthetic = "def initialize_gate_execution_context():\n    retry_output = any('question_retry_fallback' in t for t in tag_list)\n"
    assert_bn_synthetic_violation(
        collect_bn10_gate_context_branch_flags_violations,
        synthetic,
        'question_retry_fallback',
        'preflight_branch_flags',
    )

def test_bn10_gate_context_routes_branch_flags_through_helper() -> None:
    """BN10: gate_context routes branch flags through preflight_branch_flags helper."""
    assert_bn_live_gate_context_clean(
        cycle_tag='BN10',
        gate_context_collector=collect_bn10_gate_context_branch_flags_violations,
        gate_context_violation_label='BN10 gate_context branch-flag violations',
        registry_doc=Path(__file__).read_text(encoding='utf-8'),
        repo_root=_REPO_ROOT,
        preflight_module=BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE,
        helper_collector=collect_bn10_preflight_branch_flags_helper_import_violations,
        helper_violation_label='BN10 branch-flags helper import violations',
    )

def test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation() -> None:
    """BN11: guard flags non-preflight game imports on gate_context."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\nfrom game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults\ndef initialize_gate_execution_context():\n    return apply_final_emission_gate({})\n'
    violations = collect_bn11_gate_context_preflight_only_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_gate' in joined
    assert 'preflight' in joined

def test_bn11_gate_context_preflight_only_import_allowlist_locked() -> None:
    """BN11: live gate_context imports only stdlib/typing and preflight helper owners."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN11 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn11_gate_context_preflight_only_import_violations(source)
    assert not violations, 'BN11 gate_context preflight-only import violations:\n' + '\n'.join(violations)
    imported_game = {mod for mod in gate_context_import_modules(source) if mod.startswith('game.')}
    assert imported_game == BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES, f'BN11 gate_context game import set mismatch:\n  imported: {sorted(imported_game)!r}\n  allowed:  {sorted(BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)!r}'
    for required in BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS:
        assert required in source, f'missing BN11 required preflight import: {required!r}'
    lock_path = _REPO_ROOT / 'tests/ownership_guard_bn_gate_context.py'
    lock_source = lock_path.read_text(encoding='utf-8')
    scan_violations = collect_bn11_scan_logic_runtime_gate_import_violations(lock_source)
    assert not scan_violations, 'BN11 scan-logic runtime gate import violations:\n' + '\n'.join(scan_violations)
    assert_bn_cycle_documented(Path(__file__).read_text(encoding='utf-8'), 'BN11')

def test_gate_context_module_scope_guard_bn_inventory_locked() -> None:
    """CO70: gate-context file stays BN1–BN11 inventory; extend allowlist deliberately."""
    source = Path(__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)
    test_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
    }
    unexpected = sorted(test_names - _GATE_CONTEXT_BN_TEST_NAMES)
    assert not unexpected, (
        'tests/test_gate_context_ownership_guards.py must remain BN1–BN11 gate-context only; '
        f'unexpected tests {unexpected!r}. Extend _GATE_CONTEXT_BN_TEST_NAMES deliberately.'
    )
    missing = sorted(_GATE_CONTEXT_BN_TEST_NAMES - test_names)
    assert not missing, f'gate-context BN test allowlist out of date; missing {missing!r}'
    module_doc = (ast.get_docstring(tree) or '').lower()
    assert 'bn1–bn11' in module_doc or 'bn1-bn11' in module_doc.replace('–', '-')
    assert 'delegate-closeout' in module_doc.replace('_', '-')
