"""BJ-128/BJ-129 — thin ``final_emission_gate`` boundary locks (tests only).

Single source of truth for allowed orchestration imports, live compatibility seams,
and forbidden regrowth categories on :mod:`game.final_emission_gate`. BN1–BN11
runtime/gate-context guards live in ``tests/ownership_guard_bn_gate_context.py``.
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

# Cycle BV13C — production must not regrow compat-barrel text imports (registry guard owner:
# ``tests/test_compat_import_governance.py`` ``collect_bv13c_text_compat_import_guard_violations``).
BV13C_FORBIDDEN_TEXT_COMPAT_BARREL_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_text import _normalize_text",
    "from game.final_emission_text import _normalize_text_preserve_paragraphs",
    "from game.final_emission_text import _sanitize_output_text",
    "from game.final_emission_text import _RESPONSE_TYPE_VALUES",
    "import game.final_emission_text",
)

# Cycle BV14C — production must not regrow compat-barrel social-exchange imports (registry guard owner:
# ``tests/test_compat_import_governance.py`` ``collect_bv14c_social_exchange_compat_import_guard_violations``).
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

from tests.ownership_guard_bv16c_terminal_monkeypatch import (
    BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS,
    BV16C_IC_OWNER,
    BV16C_N4_OWNER,
    BV16C_OPENING_OWNER,
    BV16C_REPAIRS_OWNER,
    BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST,
    BV16C_TERMINAL_MONKEYPATCH_SCAN_ROOTS,
    BV16C_TERMINAL_ORCHESTRATION_SYMBOLS,
    BV16C_TERMINAL_PIPELINE_MODULE,
    BV16C_VISIBILITY_OWNER,
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

