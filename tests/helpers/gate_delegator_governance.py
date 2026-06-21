"""BU3 — manifest-driven BJ/BU gate delegator governance helpers (tests only).

Consolidates game-module imports used by delegator/ownership governance locks so
test routers can use path/AST source inspection and lazy importlib instead of
per-test direct production imports.
"""
from __future__ import annotations

import ast
import importlib
import inspect
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Manifest: dotted module name -> repo-relative source path (path-based inspection).
GAME_MODULE_PATHS: Final[dict[str, str]] = {
    "game.anti_reset_emission_guard": "game/anti_reset_emission_guard.py",
    "game.dialogue_social_plan": "game/dialogue_social_plan.py",
    "game.diegetic_fallback_narration": "game/diegetic_fallback_narration.py",
    "game.fallback_provenance_debug": "game/fallback_provenance_debug.py",
    "game.final_emission_acceptance_quality": "game/final_emission_acceptance_quality.py",
    "game.final_emission_answer_shape_primacy": "game/final_emission_answer_shape_primacy.py",
    "game.final_emission_anti_railroading": "game/final_emission_anti_railroading.py",
    "game.final_emission_boundary_contract": "game/final_emission_boundary_contract.py",
    "game.final_emission_context_separation": "game/final_emission_context_separation.py",
    "game.final_emission_fast_fallback_composition": "game/final_emission_fast_fallback_composition.py",
    "game.final_emission_fem_assembly": "game/final_emission_fem_assembly.py",
    "game.final_emission_finalize": "game/final_emission_finalize.py",
    "game.final_emission_gate": "game/final_emission_gate.py",
    "game.final_emission_gate_context": "game/final_emission_gate_context.py",
    "game.final_emission_gate_preflight_branch_flags": "game/final_emission_gate_preflight_branch_flags.py",
    "game.final_emission_gate_preflight_defaults": "game/final_emission_gate_preflight_defaults.py",
    "game.final_emission_gate_preflight_interaction": "game/final_emission_gate_preflight_interaction.py",
    "game.final_emission_gate_preflight_pregate_text": "game/final_emission_gate_preflight_pregate_text.py",
    "game.final_emission_gate_preflight_strict_social": "game/final_emission_gate_preflight_strict_social.py",
    "game.final_emission_gate_preflight_telemetry": "game/final_emission_gate_preflight_telemetry.py",
    "game.final_emission_gate_preflight_turn_packet": "game/final_emission_gate_preflight_turn_packet.py",
    "game.final_emission_gate_preflight_upstream": "game/final_emission_gate_preflight_upstream.py",
    "game.final_emission_generic_exit": "game/final_emission_generic_exit.py",
    "game.final_emission_meta": "game/final_emission_meta.py",
    "game.final_emission_narration_constraint_debug": "game/final_emission_narration_constraint_debug.py",
    "game.final_emission_narrative_authority": "game/final_emission_narrative_authority.py",
    "game.final_emission_narrative_mode_output": "game/final_emission_narrative_mode_output.py",
    "game.final_emission_non_strict_stack": "game/final_emission_non_strict_stack.py",
    "game.final_emission_opening_fallback": "game/final_emission_opening_fallback.py",
    "game.final_emission_passive_scene_pressure": "game/final_emission_passive_scene_pressure.py",
    "game.final_emission_player_facing_narration_purity": "game/final_emission_player_facing_narration_purity.py",
    "game.final_emission_repairs": "game/final_emission_repairs.py",
    "game.final_emission_replay_projection": "game/final_emission_replay_projection.py",
    "game.final_emission_response_type": "game/final_emission_response_type.py",
    "game.final_emission_runtime": "game/final_emission_runtime.py",
    "game.final_emission_scene_emit_integrity": "game/final_emission_scene_emit_integrity.py",
    "game.final_emission_scene_state_anchor": "game/final_emission_scene_state_anchor.py",
    "game.final_emission_sealed_fallback": "game/final_emission_sealed_fallback.py",
    "game.final_emission_strict_social_stack": "game/final_emission_strict_social_stack.py",
    "game.final_emission_terminal_pipeline": "game/final_emission_terminal_pipeline.py",
    "game.final_emission_text": "game/final_emission_text.py",
    "game.final_emission_text_formatting": "game/final_emission_text_formatting.py",
    "game.final_emission_text_policy": "game/final_emission_text_policy.py",
    "game.final_emission_text_legacy_semantic_repair": "game/final_emission_text_legacy_semantic_repair.py",
    "game.final_emission_tone_escalation": "game/final_emission_tone_escalation.py",
    "game.final_emission_visibility_fallback": "game/final_emission_visibility_fallback.py",
    "game.interaction_continuity": "game/interaction_continuity.py",
    "game.social_exchange_emission": "game/social_exchange_emission.py",
    "game.social_exchange_fallback_catalog": "game/social_exchange_fallback_catalog.py",
    "game.social_exchange_policy": "game/social_exchange_policy.py",
    "game.social_exchange_projection": "game/social_exchange_projection.py",
    "game.social_exchange_validation": "game/social_exchange_validation.py",
    "game.speaker_contract_enforcement": "game/speaker_contract_enforcement.py",
    "game.stage_diff_telemetry": "game/stage_diff_telemetry.py",
}

# Short aliases for common governance targets.
GATE: Final[str] = "game.final_emission_gate"
GENERIC_EXIT: Final[str] = "game.final_emission_generic_exit"
NON_STRICT_STACK: Final[str] = "game.final_emission_non_strict_stack"
STRICT_SOCIAL_STACK: Final[str] = "game.final_emission_strict_social_stack"
TERMINAL_PIPELINE: Final[str] = "game.final_emission_terminal_pipeline"
FINALIZE: Final[str] = "game.final_emission_finalize"
RESPONSE_TYPE: Final[str] = "game.final_emission_response_type"
VISIBILITY_FALLBACK: Final[str] = "game.final_emission_visibility_fallback"
SEALED_FALLBACK: Final[str] = "game.final_emission_sealed_fallback"
FEM_ASSEMBLY: Final[str] = "game.final_emission_fem_assembly"
GATE_CONTEXT: Final[str] = "game.final_emission_gate_context"
OPENING_FALLBACK: Final[str] = "game.final_emission_opening_fallback"
NARRATION_CONSTRAINT_DEBUG: Final[str] = "game.final_emission_narration_constraint_debug"
REPAIRS: Final[str] = "game.final_emission_repairs"
FAST_FALLBACK: Final[str] = "game.final_emission_fast_fallback_composition"
ACCEPTANCE_QUALITY: Final[str] = "game.final_emission_acceptance_quality"
DIALOGUE_SOCIAL_PLAN: Final[str] = "game.dialogue_social_plan"
META: Final[str] = "game.final_emission_meta"
TEXT: Final[str] = "game.final_emission_text"
TEXT_FORMATTING: Final[str] = "game.final_emission_text_formatting"
TEXT_POLICY: Final[str] = "game.final_emission_text_policy"
TEXT_LEGACY_REPAIR: Final[str] = "game.final_emission_text_legacy_semantic_repair"
BOUNDARY_CONTRACT: Final[str] = "game.final_emission_boundary_contract"
INTERACTION_CONTINUITY: Final[str] = "game.interaction_continuity"
SPEAKER_CONTRACT: Final[str] = "game.speaker_contract_enforcement"
SOCIAL_EXCHANGE: Final[str] = "game.social_exchange_emission"
SOCIAL_EXCHANGE_FALLBACK: Final[str] = "game.social_exchange_fallback_catalog"
SOCIAL_EXCHANGE_POLICY: Final[str] = "game.social_exchange_policy"
SOCIAL_EXCHANGE_PROJECTION: Final[str] = "game.social_exchange_projection"
SOCIAL_EXCHANGE_VALIDATION: Final[str] = "game.social_exchange_validation"
STAGE_DIFF: Final[str] = "game.stage_diff_telemetry"
FALLBACK_PROVENANCE: Final[str] = "game.fallback_provenance_debug"
ANTI_RESET: Final[str] = "game.anti_reset_emission_guard"
DIEGETIC_FALLBACK: Final[str] = "game.diegetic_fallback_narration"
SCENE_EMIT_INTEGRITY: Final[str] = "game.final_emission_scene_emit_integrity"
PASSIVE_SCENE_PRESSURE: Final[str] = "game.final_emission_passive_scene_pressure"
NARRATIVE_MODE_OUTPUT: Final[str] = "game.final_emission_narrative_mode_output"
SCENE_STATE_ANCHOR: Final[str] = "game.final_emission_scene_state_anchor"
TONE_ESCALATION: Final[str] = "game.final_emission_tone_escalation"
NARRATIVE_AUTHORITY: Final[str] = "game.final_emission_narrative_authority"
ANTI_RAILROADING: Final[str] = "game.final_emission_anti_railroading"
CONTEXT_SEPARATION: Final[str] = "game.final_emission_context_separation"
NARRATION_PURITY: Final[str] = "game.final_emission_player_facing_narration_purity"
ANSWER_SHAPE_PRIMACY: Final[str] = "game.final_emission_answer_shape_primacy"
PREFLIGHT_TELEMETRY: Final[str] = "game.final_emission_gate_preflight_telemetry"


def repo_root() -> Path:
    return _REPO_ROOT


def game_module_path(module_name: str) -> Path:
    rel = GAME_MODULE_PATHS.get(module_name)
    if rel is None:
        raise KeyError(f"game module not in governance manifest: {module_name!r}")
    return (_REPO_ROOT / rel).resolve()


def module_source(module_name: str) -> str:
    """Read production module source without importing it."""
    return game_module_path(module_name).read_text(encoding="utf-8")


def function_source(module_name: str, function_name: str) -> str:
    """Extract a top-level function body via AST without importing the module."""
    text = module_source(module_name)
    tree = ast.parse(text, filename=str(game_module_path(module_name)))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            segment = ast.get_source_segment(text, node)
            if segment is not None:
                return segment
            raise LookupError(
                f"could not extract source segment for {module_name}.{function_name}"
            )
    raise LookupError(f"{function_name!r} not found in {module_name}")


@lru_cache(maxsize=None)
def load_game_module(module_name: str) -> Any:
    """Lazy runtime import for hasattr/callable governance checks."""
    if module_name not in GAME_MODULE_PATHS:
        raise KeyError(f"game module not in governance manifest: {module_name!r}")
    return importlib.import_module(module_name)


def gate_module() -> Any:
    return load_game_module(GATE)


def gate_lacks(name: str) -> bool:
    return not hasattr(gate_module(), name)


def assert_gate_lacks(*names: str) -> None:
    feg = gate_module()
    for name in names:
        assert not hasattr(feg, name), f"gate still exposes forbidden delegator/re-export: {name!r}"


def owner_callable(module_name: str, attr: str) -> bool:
    return callable(getattr(load_game_module(module_name), attr, None))


def assert_owner_callable(module_name: str, attr: str) -> None:
    assert owner_callable(module_name, attr), (
        f"owner missing callable entrypoint: {module_name}.{attr}"
    )


def assert_owner_is(module_name: str, attr: str, expected_owner_module: str, expected_attr: str) -> None:
    owner = getattr(load_game_module(module_name), attr, None)
    expected = getattr(load_game_module(expected_owner_module), expected_attr, None)
    assert owner is expected, (
        f"{module_name}.{attr} must alias {expected_owner_module}.{expected_attr}"
    )


def assert_function_source_contains(
    module_name: str,
    function_name: str,
    *markers: str,
    forbidden: tuple[str, ...] = (),
) -> None:
    src = function_source(module_name, function_name)
    for marker in markers:
        assert marker in src, f"{module_name}.{function_name} missing marker: {marker!r}"
    for marker in forbidden:
        assert marker not in src, f"{module_name}.{function_name} forbidden marker: {marker!r}"


def assert_module_source_contains(
    module_name: str,
    *markers: str,
    forbidden: tuple[str, ...] = (),
) -> None:
    src = module_source(module_name)
    for marker in markers:
        assert marker in src, f"{module_name} missing marker: {marker!r}"
    for marker in forbidden:
        assert marker not in src, f"{module_name} forbidden marker: {marker!r}"


def inspect_function_source(module_name: str, function_name: str) -> str:
    """Runtime inspect.getsource fallback when AST segment extraction is insufficient."""
    mod = load_game_module(module_name)
    obj = getattr(mod, function_name)
    return inspect.getsource(obj)


def game_import_fan_out_from_source(source: str) -> frozenset[str]:
    """Count unique game.* imports anywhere in a test module source (BU3 metric helper)."""
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "game" or alias.name.startswith("game."):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "game" or node.module.startswith("game."):
                found.add(node.module)
    return frozenset(found)
