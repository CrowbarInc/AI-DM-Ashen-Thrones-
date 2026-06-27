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
  ``test_bn11_gate_context_*``.
"""

from __future__ import annotations

from pathlib import Path

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
)


_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons() -> None:
    """BN1: every runtime gate-entry allowlist path documents why it may import gate entry."""
    for path, reason in BN1_RUNTIME_GATE_ENTRY_ALLOWLIST.items():
        assert path.startswith('game/'), path
        assert reason.strip(), f'empty BN1 allowlist reason for {path!r}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN1' in registry_doc

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
    violations: list[str] = []
    for rel in iter_bn1_runtime_gate_entry_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BN1 scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bn1_runtime_gate_entry_guard_violations(rel, source))
    assert not violations, 'BN1 runtime gate-entry import violations:\n' + '\n'.join(violations)

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
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN2' in registry_doc

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
    violations: list[str] = []
    for rel in sorted(BN2_LAZY_GATE_NAMESPACE_FILES):
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BN2 scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bn2_lazy_gate_namespace_violations(rel, source))
    assert not violations, 'BN2 lazy gate namespace violations:\n' + '\n'.join(violations)

def test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked() -> None:
    """BN3: preflight layer-meta defaults live on dedicated helper owner."""
    import game.final_emission_gate_preflight_defaults as gpfd
    assert callable(getattr(gpfd, 'initialize_gate_preflight_layer_meta_defaults', None))
    assert callable(getattr(gpfd, 'GatePreflightLayerMetaDefaults', None))

def test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation() -> None:
    """BN3: guard flags regrown direct layer-meta owner imports on gate_context."""
    synthetic = 'from game.final_emission_tone_escalation import default_tone_escalation_meta\ndef initialize_gate_execution_context():\n    return default_tone_escalation_meta()\n'
    violations = collect_bn3_gate_context_layer_meta_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_tone_escalation' in joined
    assert 'preflight_defaults' in joined

def test_bn3_gate_context_avoids_direct_layer_meta_owner_imports() -> None:
    """BN3: gate_context routes layer-meta defaults through preflight_defaults helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN3 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn3_gate_context_layer_meta_import_violations(source)
    assert not violations, 'BN3 gate_context import violations:\n' + '\n'.join(violations)
    defaults_path = _REPO_ROOT / BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE
    assert defaults_path.is_file(), f'missing BN3 helper: {BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN3' in registry_doc

def test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked() -> None:
    """BN4: preflight telemetry/containment lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_telemetry as gpft
    assert callable(getattr(gpft, 'apply_gate_preflight_telemetry_and_containment', None))
    assert callable(getattr(gpft, 'GatePreflightTelemetryResult', None))

def test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation() -> None:
    """BN4: guard flags regrown direct telemetry/provenance imports on gate_context."""
    synthetic = "from game.stage_diff_telemetry import record_stage_snapshot\ndef initialize_gate_execution_context():\n    record_stage_snapshot(out, 'final_emission_gate_entry')\n"
    violations = collect_bn4_gate_context_telemetry_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'stage_diff_telemetry' in joined
    assert 'preflight_telemetry' in joined

def test_bn4_gate_context_avoids_direct_telemetry_provenance_imports() -> None:
    """BN4: gate_context routes telemetry/containment through preflight_telemetry helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN4 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn4_gate_context_telemetry_import_violations(source)
    assert not violations, 'BN4 gate_context import violations:\n' + '\n'.join(violations)
    telemetry_path = _REPO_ROOT / BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE
    assert telemetry_path.is_file(), f'missing BN4 helper: {BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}'
    telemetry_source = telemetry_path.read_text(encoding='utf-8')
    helper_violations = collect_bn4_preflight_telemetry_helper_gate_import_violations(telemetry_source)
    assert not helper_violations, 'BN4 telemetry helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN4' in registry_doc

def test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked() -> None:
    """BN5: preflight upstream attach lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_upstream as gpfu
    assert callable(getattr(gpfu, 'apply_gate_preflight_upstream_attach', None))
    assert callable(getattr(gpfu, 'upstream_prepared_emission_payload', None))

def test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation() -> None:
    """BN5: guard flags regrown direct upstream attach imports on gate_context."""
    synthetic = 'from game.upstream_response_repairs import merge_upstream_prepared_emission_into_gm_output\ndef initialize_gate_execution_context():\n    merge_upstream_prepared_emission_into_gm_output(out)\n'
    violations = collect_bn5_gate_context_upstream_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'upstream_response_repairs' in joined
    assert 'preflight_upstream' in joined

def test_bn5_gate_context_avoids_direct_upstream_attach_imports() -> None:
    """BN5: gate_context routes upstream attach through preflight_upstream helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN5 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn5_gate_context_upstream_import_violations(source)
    assert not violations, 'BN5 gate_context import violations:\n' + '\n'.join(violations)
    upstream_path = _REPO_ROOT / BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE
    assert upstream_path.is_file(), f'missing BN5 helper: {BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}'
    upstream_source = upstream_path.read_text(encoding='utf-8')
    helper_violations = collect_bn5_preflight_upstream_helper_gate_import_violations(upstream_source)
    assert not helper_violations, 'BN5 upstream helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN5' in registry_doc

def test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked() -> None:
    """BN6: preflight turn-packet/policy setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_turn_packet as gpfttp
    assert callable(getattr(gpfttp, 'initialize_gate_preflight_turn_packet', None))

def test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation() -> None:
    """BN6: guard flags regrown direct turn-packet/policy imports on gate_context."""
    synthetic = "from game.turn_packet import get_turn_packet\ndef initialize_gate_execution_context():\n    out['_gate_turn_packet_cache'] = get_turn_packet(out)\n"
    violations = collect_bn6_gate_context_turn_packet_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'turn_packet' in joined
    assert 'preflight_turn_packet' in joined

def test_bn6_gate_context_avoids_direct_turn_packet_policy_imports() -> None:
    """BN6: gate_context routes turn-packet/policy setup through preflight_turn_packet helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN6 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn6_gate_context_turn_packet_import_violations(source)
    assert not violations, 'BN6 gate_context import violations:\n' + '\n'.join(violations)
    turn_packet_path = _REPO_ROOT / BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE
    assert turn_packet_path.is_file(), f'missing BN6 helper: {BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}'
    turn_packet_source = turn_packet_path.read_text(encoding='utf-8')
    helper_violations = collect_bn6_preflight_turn_packet_helper_gate_import_violations(turn_packet_source)
    assert not helper_violations, 'BN6 turn-packet helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN6' in registry_doc

def test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked() -> None:
    """BN7: preflight interaction metadata lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_interaction as gpfi
    assert callable(getattr(gpfi, 'resolve_gate_preflight_interaction_metadata', None))
    assert callable(getattr(gpfi, 'GatePreflightInteractionMetadata', None))

def test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation() -> None:
    """BN7: guard flags regrown direct interaction inspection imports on gate_context."""
    synthetic = 'from game.interaction_context import inspect as inspect_interaction_context\ndef initialize_gate_execution_context():\n    return inspect_interaction_context(session)\n'
    violations = collect_bn7_gate_context_interaction_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'interaction_context' in joined
    assert 'preflight_interaction' in joined

def test_bn7_gate_context_avoids_direct_interaction_inspection_imports() -> None:
    """BN7: gate_context routes interaction metadata through preflight_interaction helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN7 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn7_gate_context_interaction_import_violations(source)
    assert not violations, 'BN7 gate_context import violations:\n' + '\n'.join(violations)
    interaction_path = _REPO_ROOT / BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE
    assert interaction_path.is_file(), f'missing BN7 helper: {BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}'
    interaction_source = interaction_path.read_text(encoding='utf-8')
    helper_violations = collect_bn7_preflight_interaction_helper_gate_import_violations(interaction_source)
    assert not helper_violations, 'BN7 interaction helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN7' in registry_doc

def test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked() -> None:
    """BN8: preflight strict-social routing lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_strict_social as gpfs
    assert callable(getattr(gpfs, 'resolve_gate_preflight_strict_social_routing', None))
    assert callable(getattr(gpfs, 'GatePreflightStrictSocialRouting', None))

def test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation() -> None:
    """BN8: guard flags regrown direct strict-social routing imports on gate_context."""
    synthetic = "from game.social_exchange_emission import strict_social_emission_will_apply\ndef initialize_gate_execution_context():\n    return strict_social_emission_will_apply(None, None, None, '')\n"
    violations = collect_bn8_gate_context_strict_social_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'social_exchange_emission' in joined
    assert 'preflight_strict_social' in joined

def test_bn8_gate_context_avoids_direct_strict_social_routing_imports() -> None:
    """BN8: gate_context routes strict-social setup through preflight_strict_social helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN8 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn8_gate_context_strict_social_import_violations(source)
    assert not violations, 'BN8 gate_context import violations:\n' + '\n'.join(violations)
    strict_social_path = _REPO_ROOT / BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE
    assert strict_social_path.is_file(), f'missing BN8 helper: {BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE}'
    strict_social_source = strict_social_path.read_text(encoding='utf-8')
    helper_violations = collect_bn8_preflight_strict_social_helper_import_violations(strict_social_source)
    assert not helper_violations, 'BN8 strict-social helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN8' in registry_doc

def test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked() -> None:
    """BN9: preflight pregate text/tag setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_pregate_text as gpfpt
    assert callable(getattr(gpfpt, 'resolve_gate_preflight_pregate_text', None))
    assert callable(getattr(gpfpt, 'GatePreflightPregateText', None))

def test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation() -> None:
    """BN9: guard flags regrown direct pregate text imports on gate_context."""
    synthetic = "from game.final_emission_text_formatting import _normalize_text\ndef initialize_gate_execution_context():\n    return _normalize_text(out.get('player_facing_text'))\n"
    violations = collect_bn9_gate_context_pregate_text_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_text_formatting' in joined
    assert 'preflight_pregate_text' in joined

def test_bn9_gate_context_avoids_direct_pregate_text_imports() -> None:
    """BN9: gate_context routes pregate text/tag setup through preflight_pregate_text helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN9 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn9_gate_context_pregate_text_import_violations(source)
    assert not violations, 'BN9 gate_context import violations:\n' + '\n'.join(violations)
    pregate_text_path = _REPO_ROOT / BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE
    assert pregate_text_path.is_file(), f'missing BN9 helper: {BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE}'
    pregate_text_source = pregate_text_path.read_text(encoding='utf-8')
    helper_violations = collect_bn9_preflight_pregate_text_helper_import_violations(pregate_text_source)
    assert not helper_violations, 'BN9 pregate text helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN9' in registry_doc

def test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked() -> None:
    """BN10: preflight branch-flag derivation lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_branch_flags as gpfb
    assert callable(getattr(gpfb, 'resolve_gate_preflight_branch_flags', None))
    assert callable(getattr(gpfb, 'GatePreflightBranchFlags', None))

def test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation() -> None:
    """BN10: guard flags inline branch-flag derivation regrown on gate_context."""
    synthetic = "def initialize_gate_execution_context():\n    retry_output = any('question_retry_fallback' in t for t in tag_list)\n"
    violations = collect_bn10_gate_context_branch_flags_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'question_retry_fallback' in joined
    assert 'preflight_branch_flags' in joined

def test_bn10_gate_context_routes_branch_flags_through_helper() -> None:
    """BN10: gate_context routes branch flags through preflight_branch_flags helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN10 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn10_gate_context_branch_flags_violations(source)
    assert not violations, 'BN10 gate_context branch-flag violations:\n' + '\n'.join(violations)
    branch_flags_path = _REPO_ROOT / BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE
    assert branch_flags_path.is_file(), f'missing BN10 helper: {BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE}'
    branch_flags_source = branch_flags_path.read_text(encoding='utf-8')
    helper_violations = collect_bn10_preflight_branch_flags_helper_import_violations(branch_flags_source)
    assert not helper_violations, 'BN10 branch-flags helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN10' in registry_doc

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
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN11' in registry_doc
