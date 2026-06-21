"""BJ-128/BJ-129 / BN1–BN11 — thin ``final_emission_gate`` boundary locks (tests only).

Single source of truth for allowed orchestration imports, live compatibility seams,
forbidden regrowth categories on :mod:`game.final_emission_gate`, the runtime/API
entry seam policy (BN1), internal lazy gate namespace policy (BN2), gate-context
preflight import regrowth policies (BN3–BN10), and gate-context preflight-only
positive import allowlist (BN11).
"""
from __future__ import annotations

import re
from typing import Any, Final, Mapping

# Cycle BJ-128 — live compatibility seams re-exported through the gate module.
BJ128_LIVE_GATE_SEAM_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "apply_final_emission_gate",
        "get_speaker_selection_contract",
        "validate_emitted_speaker_against_contract",
        "detect_emitted_speaker_signature",
        "SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES",
        "apply_interaction_continuity_emission_step",
        "attach_interaction_continuity_validation",
    }
)

BJ128_DEAD_GATE_REEXPORT_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "validate_answer_completeness",
        "inspect_answer_completeness_failure",
        "validate_response_delta",
        "inspect_response_delta_failure",
        "candidate_satisfies_answer_contract",
        "candidate_satisfies_dialogue_contract",
        "candidate_satisfies_action_outcome_contract",
        "candidate_satisfies_scene_opening_contract",
        "_global_narrative_fallback_stock_line",
        "sanitize_player_facing_output",
        "get_turn_packet",
        "get_scene_runtime",
        "merge_upstream_prepared_emission_into_gm_output",
        "maybe_attach_upstream_prepared_opening_fallback_payload",
        "effective_strict_social_resolution_for_emission",
        "merged_player_prompt_for_gate",
        "_merge_response_type_meta",
        "_default_tone_escalation_meta",
        "_merge_tone_escalation_meta",
        "_default_fallback_behavior_meta",
        "_skip_answer_completeness_layer",
        "_strict_social_answer_pressure_ac_contract_active",
    }
)

BJ128_DEAD_GATE_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.interaction_context import inspect",
    "from game.narrative_authority import",
    "from game.narration_visibility import",
    "from game.output_sanitizer import sanitize_player_facing_output",
    "from game.social_exchange_emission import",
    "from game.storage import get_scene_runtime",
    "from game.leads import get_lead",
    "from game.prompt_context import canonical_interaction_target_npc_id",
    "from game.turn_packet import get_turn_packet",
    "from game.final_emission_meta import",
    "from game.final_emission_text import",
    "from game.final_emission_narrative_mode_output import",
    "from game.final_emission_scene_state_anchor import",
    "from game.opening_deterministic_fallback import",
    "from game.response_policy_contracts import",
    "from game.final_emission_tone_escalation import",
    "from game.final_emission_narrative_authority import",
    "from game.final_emission_anti_railroading import",
    "from game.final_emission_context_separation import",
    "from game.final_emission_player_facing_narration_purity import",
    "from game.final_emission_answer_shape_primacy import",
    "from game.final_emission_repairs import",
    "from game.upstream_response_repairs import",
    "from game.final_emission_validators import",
    "def _question_prompt_for_resolution(",
    "def _speaker_label(",
    "def _dedupe_preserve_order(",
)

# Cycle BJ-129 — allowed import roots; gate must not regrow beyond orchestration + live seams.
BJ129_ALLOWED_GATE_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "__future__",
        "typing",
        "game.emitted_speaker_signature",
        "game.speaker_contract_enforcement",
        "game.final_emission_non_strict_stack",
        "game.final_emission_generic_exit",
        "game.final_emission_strict_social_stack",
        "game.final_emission_gate_context",
        "game.interaction_continuity",
        "game.final_emission_passive_scene_pressure",
        "game.final_emission_gate_preflight_pregate_text",
    }
)

BJ129_ALLOWED_MODULE_LEVEL_DEFS: Final[frozenset[str]] = frozenset({"apply_final_emission_gate"})

BJ129_ORCHESTRATION_CALL_MARKERS: Final[tuple[str, ...]] = (
    "initialize_gate_execution_context(",
    "run_strict_social_composition_trunk(",
    "run_non_strict_layer_stack(",
    "run_generic_accept_exit(",
    "run_generic_replace_exit(",
)

# Cycle BN1 — runtime/API entry seam (import-path compression; no behavior change).
# Direct ``from game.final_emission_gate import apply_final_emission_gate`` in ``game/`` is
# allowed only for the orchestration owner and the runtime delegate below. Production/runtime/API
# callers must use the runtime seam; downstream tests should use ``emission_smoke_assertions``
# consumer facade.
BN1_RUNTIME_API_ENTRY_SEAM: Final[str] = "game.final_emission_runtime.finalize_player_facing_emission"
BN1_ORCHESTRATION_OWNER_ENTRY: Final[str] = "game.final_emission_gate.apply_final_emission_gate"
BN1_DOWNSTREAM_TEST_ENTRY_SEAM: Final[str] = (
    "tests.helpers.gate_orchestration_smoke.apply_final_emission_gate_consumer"
)

# Cycle BN2 — internal lazy ``feg`` namespace in extracted stack modules (import-path only).
# Post-BN2 these files must not lazy-import ``game.final_emission_gate``; layer owners are
# imported directly. Monkeypatch tests patch owner modules (e.g. terminal_pipeline,
# emission_finalize), not ``feg``. Add retained symbols only with explicit test reason.
BN2_LAZY_GATE_NAMESPACE_FILES: Final[frozenset[str]] = frozenset(
    {
        "game/final_emission_non_strict_stack.py",
        "game/final_emission_terminal_pipeline.py",
    }
)
BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE: Final[Mapping[str, frozenset[str]]] = {
    "game/final_emission_non_strict_stack.py": frozenset(),
    "game/final_emission_terminal_pipeline.py": frozenset(),
}
BN2_FORBIDDEN_LAZY_GATE_MARKERS: Final[tuple[str, ...]] = (
    "def _gate_module(",
    "import game.final_emission_gate",
    "_gate_module()",
)

# Cycle BN3 — gate_context must not regrow direct layer-meta owner imports after preflight split.
BN3_GATE_CONTEXT_OWNER_MODULE: Final[str] = "game/final_emission_gate_context.py"
BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_defaults.py"
)
BN3_GATE_CONTEXT_FORBIDDEN_LAYER_META_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_anti_railroading import",
    "from game.final_emission_answer_shape_primacy import",
    "from game.final_emission_context_separation import",
    "from game.final_emission_fast_fallback_composition import",
    "from game.final_emission_meta import",
    "from game.final_emission_narrative_authority import",
    "from game.final_emission_player_facing_narration_purity import",
    "from game.final_emission_repairs import",
    "from game.final_emission_response_type import",
    "from game.final_emission_tone_escalation import",
    "default_anti_railroading_meta(",
    "default_answer_shape_primacy_meta(",
    "default_context_separation_meta(",
    "default_fast_fallback_neutral_composition_meta(",
    "default_narrative_authenticity_layer_meta(",
    "default_response_type_debug(",
    "default_narrative_authority_meta(",
    "default_player_facing_narration_purity_meta(",
    "_default_fallback_behavior_meta(",
    "_default_response_delta_meta(",
    "_default_social_response_structure_meta(",
    "default_tone_escalation_meta(",
    "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug(",
)
BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults"
)

# Cycle BN4 — gate_context must not regrow direct telemetry/provenance imports after preflight split.
BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_telemetry.py"
)
BN4_GATE_CONTEXT_FORBIDDEN_TELEMETRY_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.fallback_provenance_debug import",
    "from game.stage_diff_telemetry import",
    "record_final_emission_gate_entry(",
    "apply_upstream_fallback_pregate_containment(",
    "snapshot_turn_stage(",
    "record_stage_snapshot(",
    "diff_turn_stage(",
    "record_stage_transition(",
)
BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_telemetry import apply_gate_preflight_telemetry_and_containment"
)
BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER: Final[str] = "from game.final_emission_gate import"
BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN5 — gate_context must not regrow direct upstream attach imports after preflight split.
BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_upstream.py"
)
BN5_GATE_CONTEXT_FORBIDDEN_UPSTREAM_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.upstream_response_repairs import",
    "merge_upstream_prepared_emission_into_gm_output(",
    "maybe_attach_upstream_prepared_opening_fallback_payload(",
    "UPSTREAM_PREPARED_EMISSION_KEY",
)
BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_upstream import apply_gate_preflight_upstream_attach"
)
BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER: Final[str] = "from game.final_emission_gate import"
BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN6 — gate_context must not regrow direct turn-packet/policy setup imports after preflight split.
BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_turn_packet.py"
)
BN6_GATE_CONTEXT_FORBIDDEN_TURN_PACKET_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.response_policy_contracts import",
    "from game.turn_packet import",
    "materialize_response_policy_bundle(",
    "get_turn_packet(",
    "_gate_turn_packet_cache",
)
BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_turn_packet import initialize_gate_preflight_turn_packet"
)
BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER: Final[str] = "from game.final_emission_gate import"
BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN7 — gate_context must not regrow direct interaction inspection imports after preflight split.
BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_interaction.py"
)
BN7_GATE_CONTEXT_FORBIDDEN_INTERACTION_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.interaction_context import",
    "inspect_interaction_context(",
)
BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_interaction import resolve_gate_preflight_interaction_metadata"
)
BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER: Final[str] = "from game.final_emission_gate import"
BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN8 — gate_context must not regrow direct strict-social routing/sanitizer imports after split.
BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_strict_social.py"
)
BN8_GATE_CONTEXT_FORBIDDEN_STRICT_SOCIAL_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.social_exchange_emission import",
    "from game.output_sanitizer import",
    "effective_strict_social_resolution_for_emission(",
    "strict_social_emission_will_apply(",
    "merged_player_prompt_for_gate(",
    "strict_social_suppress_non_native_coercion_for_narration_beat(",
    "sanitize_player_facing_output(",
)
BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_strict_social import resolve_gate_preflight_strict_social_routing"
)
BN8_FORBIDDEN_GATE_IMPORT_IN_STRICT_SOCIAL_HELPER: Final[str] = "from game.final_emission_gate import"
BN8_FORBIDDEN_GATE_IMPORT_IN_STRICT_SOCIAL_HELPER_ALT: Final[str] = "import game.final_emission_gate"
BN8_FORBIDDEN_STRICT_SOCIAL_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BV13C — production must not regrow compat-barrel text imports (registry guard owner:
# ``tests/test_ownership_registry.py`` ``collect_bv13c_text_compat_import_guard_violations``).
BV13C_FORBIDDEN_TEXT_COMPAT_BARREL_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_text import _normalize_text",
    "from game.final_emission_text import _normalize_text_preserve_paragraphs",
    "from game.final_emission_text import _sanitize_output_text",
    "from game.final_emission_text import _RESPONSE_TYPE_VALUES",
    "import game.final_emission_text",
)

# Cycle BV14C — production must not regrow compat-barrel social-exchange imports (registry guard owner:
# ``tests/test_ownership_registry.py`` ``collect_bv14c_social_exchange_compat_import_guard_violations``).
BV14C_FORBIDDEN_SOCIAL_EXCHANGE_COMPAT_BARREL_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.social_exchange_emission import strict_social_emission_will_apply",
    "from game.social_exchange_emission import minimal_social_emergency_fallback_line",
    "from game.social_exchange_emission import effective_strict_social_resolution_for_emission",
    "from game.social_exchange_emission import merged_player_prompt_for_gate",
    "from game.social_exchange_emission import is_route_illegal_global_or_sanitizer_fallback_text",
    "from game.social_exchange_emission import log_final_emission_decision",
    "from game.social_exchange_emission import log_final_emission_trace",
    "import game.social_exchange_emission",
)

# Cycle BV16C — tests must monkeypatch finalize-tail owner modules, not terminal_pipeline namespace.
BV16C_TERMINAL_PIPELINE_MODULE: Final[str] = "game.final_emission_terminal_pipeline"
BV16C_VISIBILITY_OWNER: Final[str] = "game.final_emission_visibility_fallback"
BV16C_N4_OWNER: Final[str] = "game.final_emission_acceptance_quality"
BV16C_IC_OWNER: Final[str] = "game.interaction_continuity"
BV16C_OPENING_OWNER: Final[str] = "game.final_emission_opening_fallback"
BV16C_REPAIRS_OWNER: Final[str] = "game.final_emission_repairs"
BV16C_TERMINAL_ORCHESTRATION_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "run_gate_terminal_enforcement_pipeline",
        "apply_strict_social_emergency_fallback_patch",
        "GateTerminalEnforcementProfile",
        "_apply_referent_clarity_pre_finalize",
        "_patch_fem_text_fingerprint",
    }
)
BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS: Final[tuple[str, ...]] = (
    'monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement"',
    'monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam"',
    'monkeypatch.setattr(terminal_pipeline, "attach_interaction_continuity_validation"',
    'monkeypatch.setattr(terminal_pipeline, "apply_interaction_continuity_emission_step"',
    'monkeypatch.setattr(terminal_pipeline, "_apply_fallback_behavior_layer"',
    "terminal_pipeline.apply_visibility_enforcement",
    "terminal_pipeline.apply_acceptance_quality_n4_floor_seam",
    "terminal_pipeline.attach_interaction_continuity_validation",
    "terminal_pipeline.apply_interaction_continuity_emission_step",
    "terminal_pipeline._apply_fallback_behavior_layer",
)
BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "tests/test_ownership_registry.py",
        "tests/helpers/gate_thin_boundary_locks.py",
        "tools/bv16c_migrate_monkeypatches.py",
        "tools/bv16_generate_audit_docs.py",
    }
)
BV16C_TERMINAL_MONKEYPATCH_SCAN_ROOTS: Final[tuple[str, ...]] = ("tests",)

# Cycle BN9 — gate_context must not regrow direct pregate text imports after preflight split.
BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_pregate_text.py"
)
BN9_GATE_CONTEXT_FORBIDDEN_PREGATE_TEXT_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_text import",
    "from game.final_emission_text_formatting import",
    "_normalize_text(",
)
BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_pregate_text import resolve_gate_preflight_pregate_text"
)
BN9_FORBIDDEN_PREGATE_TEXT_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BN10 — branch-flag helper must not import gate/FEM/replay/terminal modules.
BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_branch_flags.py"
)
BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_branch_flags import resolve_gate_preflight_branch_flags"
)
BN10_GATE_CONTEXT_FORBIDDEN_INLINE_BRANCH_FLAG_MARKERS: Final[tuple[str, ...]] = (
    "question_retry_fallback",
    "social_exchange_retry_fallback",
    "npc_directed_guard",
)
BN10_FORBIDDEN_BRANCH_FLAGS_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BN11 — gate_context positive preflight-only import allowlist (stdlib/typing + preflight helpers).
BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate_preflight_branch_flags",
        "game.final_emission_gate_preflight_defaults",
        "game.final_emission_gate_preflight_interaction",
        "game.final_emission_gate_preflight_pregate_text",
        "game.final_emission_gate_preflight_strict_social",
        "game.final_emission_gate_preflight_telemetry",
        "game.final_emission_gate_preflight_turn_packet",
        "game.final_emission_gate_preflight_upstream",
    }
)
BN11_GATE_CONTEXT_ALLOWED_STDLIB_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {"__future__", "typing"}
)
BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS: Final[tuple[str, ...]] = (
    BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT,
    BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT,
    BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT,
    BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT,
    BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT,
    BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT,
    BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT,
    BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT,
)
BN11_FORBIDDEN_NON_PREFLIGHT_GAME_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate",
        "game.final_emission_meta",
        "game.final_emission_replay_projection",
        "game.final_emission_text",
        "game.output_sanitizer",
        "game.social_exchange_emission",
        "game.upstream_response_repairs",
        "game.turn_packet",
        "game.response_policy_contracts",
    }
)

BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "repair helper imports",
        (
            "from game.final_emission_repairs import",
            "from game.upstream_response_repairs import",
            "from game.final_emission_finalize import",
        ),
    ),
    (
        "validator helper imports",
        (
            "from game.final_emission_validators import",
            "validate_answer_completeness(",
            "validate_response_delta(",
            "candidate_satisfies_answer_contract",
        ),
    ),
    (
        "text helper imports",
        (
            "from game.final_emission_text import",
            "from game.final_emission_text_formatting import",
            "_global_narrative_fallback_stock_line",
            "_normalize_text(",
        ),
    ),
    (
        "meta/debug merge imports",
        (
            "from game.final_emission_meta import",
            "merge_narrative_authenticity_into_final_emission_meta",
            "_merge_response_type_meta",
            "_default_tone_escalation_meta",
            "_merge_tone_escalation_meta",
            "_default_fallback_behavior_meta",
            "merge_tone_escalation_meta",
        ),
    ),
    (
        "social_exchange helper imports",
        (
            "from game.social_exchange_emission import",
            "strict_social_emission_will_apply",
            "merged_player_prompt_for_gate",
        ),
    ),
    (
        "layer-owner imports unrelated to orchestration boundary",
        (
            "from game.final_emission_tone_escalation import",
            "from game.final_emission_narrative_authority import",
            "from game.final_emission_anti_railroading import",
            "from game.final_emission_context_separation import",
            "from game.final_emission_player_facing_narration_purity import",
            "from game.final_emission_answer_shape_primacy import",
            "from game.final_emission_scene_state_anchor import",
            "from game.final_emission_narrative_mode_output import",
            "from game.final_emission_visibility_fallback import",
            "from game.final_emission_opening_fallback import",
            "from game.final_emission_terminal_pipeline import",
        ),
    ),
    (
        "local helper defs unrelated to orchestration",
        (
            "def _question_prompt_for_resolution(",
            "def _speaker_label(",
            "def _dedupe_preserve_order(",
            "def _apply_",
            "def _merge_",
            "def _enforce_",
            "def _repair_",
            "def _validate_",
        ),
    ),
)


def gate_import_modules(gate_src: str) -> frozenset[str]:
    """Return top-level modules imported by ``final_emission_gate`` source."""
    mods: set[str] = set()
    for match in re.finditer(r"^from ([\w.]+) import", gate_src, re.MULTILINE):
        mods.add(match.group(1))
    for match in re.finditer(r"^import ([\w.]+)(?: as \w+)?$", gate_src, re.MULTILINE):
        mods.add(match.group(1))
    return frozenset(mods)


def module_level_defs(gate_src: str) -> tuple[str, ...]:
    """Return module-level ``def`` names declared in gate source."""
    return tuple(re.findall(r"^def (\w+)\(", gate_src, re.MULTILINE))


def assert_gate_bj128_no_dead_import_reexports(feg: Any, *, gate_src: str | None = None) -> None:
    """BJ-128: gate keeps orchestration + documented live seams only."""
    import game.interaction_continuity as ic
    import game.speaker_contract_enforcement as sce

    if gate_src is None:
        gate_src = _read_gate_source(feg)

    for marker in BJ128_DEAD_GATE_IMPORT_MARKERS:
        assert marker not in gate_src, f"gate source still imports dead residue marker: {marker!r}"

    for name in BJ128_DEAD_GATE_REEXPORT_SYMBOLS:
        assert not hasattr(feg, name), f"gate still re-exports dead import-only symbol: {name!r}"

    for name in BJ128_LIVE_GATE_SEAM_SYMBOLS:
        assert hasattr(feg, name), f"gate missing live seam: {name!r}"

    assert callable(feg.apply_final_emission_gate)
    assert callable(feg.get_speaker_selection_contract)
    assert feg.get_speaker_selection_contract is sce.get_speaker_selection_contract
    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation


def assert_gate_bj129_thin_boundary_shape(feg: Any, *, gate_src: str | None = None) -> None:
    """BJ-129: gate source shape rejects regrowth beyond thin orchestration boundary."""
    if gate_src is None:
        gate_src = _read_gate_source(feg)

    assert_gate_bj128_no_dead_import_reexports(feg, gate_src=gate_src)

    imported = gate_import_modules(gate_src)
    disallowed = sorted(imported - BJ129_ALLOWED_GATE_IMPORT_MODULES)
    assert not disallowed, f"gate imports modules outside BJ-129 allowlist: {disallowed!r}"

    defs = module_level_defs(gate_src)
    extra_defs = sorted(set(defs) - BJ129_ALLOWED_MODULE_LEVEL_DEFS)
    assert not extra_defs, f"gate declares module-level helpers outside allowlist: {extra_defs!r}"
    assert "apply_final_emission_gate" in defs

    apply_src = _apply_final_emission_gate_source(feg)
    for marker in BJ129_ORCHESTRATION_CALL_MARKERS:
        assert marker in apply_src, f"apply_final_emission_gate missing orchestration call: {marker!r}"

    for category, markers in BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES:
        for marker in markers:
            if marker.startswith("def _"):
                if marker in gate_src:
                    raise AssertionError(
                        f"gate source regrowth ({category}): forbidden local helper {marker!r}"
                    )
                continue
            if marker.startswith("from game."):
                if marker in gate_src:
                    raise AssertionError(
                        f"gate source regrowth ({category}): forbidden import {marker!r}"
                    )
                continue
            if marker in apply_src:
                raise AssertionError(
                    f"apply_final_emission_gate regrowth ({category}): forbidden call/reference {marker!r}"
                )


def _read_gate_source(feg: Any) -> str:
    from pathlib import Path

    return Path(feg.__file__).read_text(encoding="utf-8")


def _apply_final_emission_gate_source(feg: Any) -> str:
    import inspect

    return inspect.getsource(feg.apply_final_emission_gate)


def collect_bn2_lazy_gate_namespace_violations(rel_path: str, source: str) -> list[str]:
    """BN2: flag lazy ``feg`` namespace usage in extracted stack modules."""
    norm = rel_path.replace("\\", "/")
    if norm not in BN2_LAZY_GATE_NAMESPACE_FILES:
        return []

    violations: list[str] = []
    for marker in BN2_FORBIDDEN_LAZY_GATE_MARKERS:
        if marker in source:
            violations.append(
                f"{norm}: forbidden BN2 lazy gate namespace marker {marker!r} "
                f"(import layer owners directly; monkeypatch owner modules, not feg)",
            )

    for match in re.finditer(r"\bfeg\.(\w+)", source):
        symbol = match.group(1)
        allowed = BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE.get(norm, frozenset())
        if symbol not in allowed:
            violations.append(
                f"{norm}: forbidden BN2 lazy gate namespace access feg.{symbol!r} "
                f"(not in retained allowlist; import owner module directly)",
            )
    return violations


def collect_bn3_gate_context_layer_meta_import_violations(source: str) -> list[str]:
    """BN3: flag direct layer-meta owner imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN3_GATE_CONTEXT_FORBIDDEN_LAYER_META_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN3 layer-meta owner marker {marker!r} "
                f"(use {BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE!r})",
            )
    if BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN3 preflight defaults import "
            f"{BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT!r}",
        )
    return violations


def collect_bn4_gate_context_telemetry_import_violations(source: str) -> list[str]:
    """BN4: flag direct telemetry/provenance imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN4_GATE_CONTEXT_FORBIDDEN_TELEMETRY_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN4 telemetry/provenance marker {marker!r} "
                f"(use {BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE!r})",
            )
    if BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN4 preflight telemetry import "
            f"{BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT!r}",
        )
    return violations


def collect_bn4_preflight_telemetry_helper_gate_import_violations(source: str) -> list[str]:
    """BN4: preflight telemetry helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER in source:
        violations.append(
            f"{BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}: forbidden gate owner import "
            f"{BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER!r}",
        )
    if BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT in source:
        violations.append(
            f"{BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}: forbidden gate owner import "
            f"{BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT!r}",
        )
    return violations


def collect_bn5_gate_context_upstream_import_violations(source: str) -> list[str]:
    """BN5: flag direct upstream attach imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN5_GATE_CONTEXT_FORBIDDEN_UPSTREAM_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN5 upstream attach marker {marker!r} "
                f"(use {BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE!r})",
            )
    if BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN5 preflight upstream import "
            f"{BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT!r}",
        )
    return violations


def collect_bn5_preflight_upstream_helper_gate_import_violations(source: str) -> list[str]:
    """BN5: preflight upstream helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER in source:
        violations.append(
            f"{BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}: forbidden gate owner import "
            f"{BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER!r}",
        )
    if BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT in source:
        violations.append(
            f"{BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}: forbidden gate owner import "
            f"{BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT!r}",
        )
    return violations


def collect_bn6_gate_context_turn_packet_import_violations(source: str) -> list[str]:
    """BN6: flag direct turn-packet/policy setup imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN6_GATE_CONTEXT_FORBIDDEN_TURN_PACKET_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN6 turn-packet/policy marker {marker!r} "
                f"(use {BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE!r})",
            )
    if BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN6 preflight turn-packet import "
            f"{BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT!r}",
        )
    return violations


def collect_bn6_preflight_turn_packet_helper_gate_import_violations(source: str) -> list[str]:
    """BN6: preflight turn-packet helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER in source:
        violations.append(
            f"{BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}: forbidden gate owner import "
            f"{BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER!r}",
        )
    if BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT in source:
        violations.append(
            f"{BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}: forbidden gate owner import "
            f"{BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT!r}",
        )
    return violations


def collect_bn7_gate_context_interaction_import_violations(source: str) -> list[str]:
    """BN7: flag direct interaction inspection imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN7_GATE_CONTEXT_FORBIDDEN_INTERACTION_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN7 interaction inspection marker {marker!r} "
                f"(use {BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE!r})",
            )
    if BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN7 preflight interaction import "
            f"{BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT!r}",
        )
    return violations


def collect_bn7_preflight_interaction_helper_gate_import_violations(source: str) -> list[str]:
    """BN7: preflight interaction helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER in source:
        violations.append(
            f"{BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}: forbidden gate owner import "
            f"{BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER!r}",
        )
    if BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT in source:
        violations.append(
            f"{BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}: forbidden gate owner import "
            f"{BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT!r}",
        )
    return violations


def collect_bn8_gate_context_strict_social_import_violations(source: str) -> list[str]:
    """BN8: flag direct strict-social routing/sanitizer imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN8_GATE_CONTEXT_FORBIDDEN_STRICT_SOCIAL_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN8 strict-social routing marker {marker!r} "
                f"(use {BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE!r})",
            )
    if BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN8 preflight strict-social import "
            f"{BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT!r}",
        )
    return violations


def collect_bn8_preflight_strict_social_helper_import_violations(source: str) -> list[str]:
    """BN8: preflight strict-social helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN8_FORBIDDEN_STRICT_SOCIAL_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE}: forbidden BN8 helper import {marker!r}",
            )
    return violations


def collect_bn9_gate_context_pregate_text_import_violations(source: str) -> list[str]:
    """BN9: flag direct pregate text imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN9_GATE_CONTEXT_FORBIDDEN_PREGATE_TEXT_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN9 pregate text marker {marker!r} "
                f"(use {BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE!r})",
            )
    if BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN9 preflight pregate text import "
            f"{BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT!r}",
        )
    return violations


def collect_bn9_preflight_pregate_text_helper_import_violations(source: str) -> list[str]:
    """BN9: preflight pregate text helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN9_FORBIDDEN_PREGATE_TEXT_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE}: forbidden BN9 helper import {marker!r}",
            )
    return violations


def collect_bn10_gate_context_branch_flags_violations(source: str) -> list[str]:
    """BN10: gate_context must route branch flags through preflight helper."""
    violations: list[str] = []
    if BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN10 preflight branch-flags import "
            f"{BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT!r}",
        )
    initialize_src = ""
    if "def initialize_gate_execution_context(" in source:
        initialize_src = source.split("def initialize_gate_execution_context(", 1)[1]
        if "def " in initialize_src:
            initialize_src = initialize_src.split("\ndef ", 1)[0]
    for marker in BN10_GATE_CONTEXT_FORBIDDEN_INLINE_BRANCH_FLAG_MARKERS:
        if marker in initialize_src:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN10 inline branch-flag marker {marker!r} "
                f"(use {BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE!r})",
            )
    return violations


def collect_bn10_preflight_branch_flags_helper_import_violations(source: str) -> list[str]:
    """BN10: preflight branch-flags helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN10_FORBIDDEN_BRANCH_FLAGS_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE}: forbidden BN10 helper import {marker!r}",
            )
    return violations


def gate_context_import_modules(source: str) -> frozenset[str]:
    """Return top-level modules imported by ``final_emission_gate_context`` source."""
    return gate_import_modules(source)


def collect_bn11_gate_context_preflight_only_import_violations(source: str) -> list[str]:
    """BN11: gate_context may import only stdlib/typing plus preflight helper owners."""
    violations: list[str] = []
    imported = gate_context_import_modules(source)
    allowed = BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES | BN11_GATE_CONTEXT_ALLOWED_STDLIB_IMPORT_MODULES

    game_imports = {mod for mod in imported if mod.startswith("game.")}
    disallowed_game = sorted(game_imports - BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)
    for mod in disallowed_game:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN11 non-preflight game import {mod!r} "
            f"(allowed game modules: {sorted(BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)!r})",
        )

    other_disallowed = sorted(imported - allowed)
    for mod in other_disallowed:
        if mod.startswith("game."):
            continue
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN11 import outside stdlib/typing allowlist: {mod!r}",
        )

    for required in BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS:
        if required not in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN11 required preflight import {required!r}",
            )

    return violations


def _iter_collect_bn11_function_blocks(source: str) -> list[tuple[str, str]]:
    """Return ``(name, body)`` for each ``collect_bn11_*`` function after the BN11 anchor."""
    bn11_anchor = "# Cycle BN11"
    if bn11_anchor not in source:
        return []

    tail = source.split(bn11_anchor, 1)[1]
    blocks: list[tuple[str, str]] = []
    current_name = ""
    current_lines: list[str] = []
    capturing = False

    for line in tail.splitlines(keepends=True):
        if line.startswith("def collect_bn11_"):
            if capturing and current_name:
                blocks.append((current_name, "".join(current_lines)))
            current_name = line.split("(", 1)[0].removeprefix("def ").strip()
            current_lines = [line]
            capturing = True
            continue
        if capturing:
            if line.startswith("def ") and not line.startswith("def collect_bn11_"):
                blocks.append((current_name, "".join(current_lines)))
                current_name = ""
                current_lines = []
                capturing = False
                continue
            current_lines.append(line)

    if capturing and current_name:
        blocks.append((current_name, "".join(current_lines)))
    return blocks


def collect_bn11_scan_logic_runtime_gate_import_violations(source: str) -> list[str]:
    """BN11: collect_bn11 scan helpers must be string-scan only (no runtime gate imports)."""
    blocks = _iter_collect_bn11_function_blocks(source)
    if not blocks:
        return ["tests/helpers/gate_thin_boundary_locks.py: missing collect_bn11_* scan helpers"]

    violations: list[str] = []
    for func_name, func_source in blocks:
        for line in func_source.splitlines():
            stripped = line.lstrip()
            if not (stripped.startswith("from ") or stripped.startswith("import ")):
                continue
            violations.append(
                "tests/helpers/gate_thin_boundary_locks.py: forbidden BN11 scan-logic import in "
                f"{func_name}: {stripped!r}",
            )
    return violations
