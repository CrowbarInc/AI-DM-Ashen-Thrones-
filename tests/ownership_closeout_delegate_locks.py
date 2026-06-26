"""BJ delegate-collapse closeout lock helpers (import-light; no pytest).

Delegate-collapse closeout locks (cycles BJ-70–BJ-129) verify that ``final_emission_gate``
orchestration delegates to owner modules rather than retaining gate wrappers. Enforced by
``test_bj*`` functions in ``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

from tests.helpers.gate_thin_boundary_locks import (
    BJ128_DEAD_GATE_IMPORT_MARKERS,
    BJ128_DEAD_GATE_REEXPORT_SYMBOLS,
    BJ128_LIVE_GATE_SEAM_SYMBOLS,
    BJ129_ALLOWED_GATE_IMPORT_MODULES,
    BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES,
    assert_gate_bj128_no_dead_import_reexports,
    assert_gate_bj129_thin_boundary_shape,
    gate_import_modules,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Cycle BJ-123 — allowed ``feg.*`` test/harness patch seams (live gate re-exports only).
BJ123_ALLOWED_FEG_PATCH_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "get_speaker_selection_contract",  # compatibility re-export; also patch sce owner
        "apply_final_emission_gate",  # orchestration entry — direct calls, not monkeypatch targets
    }
)
BJ123_STALE_FEG_PATCH_FRAGMENTS: Final[tuple[str, ...]] = (
    'monkeypatch.setattr(feg, "_apply_visibility_enforcement"',
    'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"',
    '"game.final_emission_gate._apply_visibility_enforcement"',
    'monkeypatch.setattr(feg, "minimal_social_emergency_fallback_line"',
    'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
    'monkeypatch.setattr(_feg, "strict_social_emission_will_apply"',
    "feg._finalize_emission_output(",
    "feg._final_emission_fast_path_eligible(",
    "feg._default_response_type_debug(",
    '"game.final_emission_gate.strict_social_emission_will_apply"',
    "final_emission_gate.validate_player_facing_referential_clarity",
    "final_emission_gate._try_strict_social_local_pronoun_substitution_repair",
    'monkeypatch.setattr(feg, "build_final_strict_social_response"',
    'monkeypatch.setattr(feg, "record_stage_snapshot"',
    'monkeypatch.setattr(feg, "_repair_location_opening"',
    'monkeypatch.setattr(feg, "validate_scene_state_anchoring"',
    "import game.final_emission_gate as _feg",
    "from game.final_emission_gate import _global_narrative_fallback_stock_line",
    "from game.final_emission_gate import validate_answer_completeness",
    "from game.final_emission_gate import inspect_answer_completeness_failure",
)
BJ123_HARNESS_PATCH_SCAN_PATHS: Final[tuple[str, ...]] = (
    "tests/helpers/gate_equivalence_monkeypatch.py",
    "tests/helpers/post_speaker_finalize_probe.py",
    "tests/helpers/speaker_relocation_shadow_harness.py",
    "tests/helpers/strict_social_harness.py",
    "tests/helpers/emission_smoke_assertions.py",
    "tests/test_final_emission_boundary_convergence.py",
    "tests/test_final_emission_boundary_no_semantic_repair.py",
    "tests/test_anti_railroading_transcript_regressions.py",
    "tests/test_prompt_context.py",
    "tests/test_social_exchange_emission.py",
    "tests/test_final_emission_sealed_fallback.py",
    "tests/test_final_emission_visibility.py",
    "tests/test_manual_play_latency.py",
    "tests/test_tone_escalation_rules.py",
    "tests/test_referential_clarity_strict_social_local_repair.py",
    "tests/test_lead_npc_payoff_and_fallback.py",
    "tests/test_strict_social_answer_pressure_cashout.py",
    "tests/test_anti_reset_emission_guard.py",
    "tests/test_narration_transcript_regressions.py",
    "tests/test_answer_completeness_rules.py",
    "tests/test_interaction_continuity_repair.py",
    "tests/test_narrative_authority_rules.py",
    "tests/test_player_facing_narration_purity.py",
    "tests/test_context_separation.py",
    "tests/test_anti_railroading.py",
    "tests/test_fallback_behavior_gate.py",
    "tests/test_final_emission_opening_fallback.py",
    "tests/test_diegetic_fallback_block4.py",
)

# Cycle BJ-124 — BJ-123-dead seams must not remain as gate-module imports/re-exports.
BJ124_DEAD_GATE_REEXPORT_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "_apply_visibility_enforcement",
        "strict_social_emission_will_apply",
        "minimal_social_emergency_fallback_line",
        "_finalize_emission_output",
        "_final_emission_fast_path_eligible",
        "_default_response_type_debug",
        "_default_response_delta_meta",
        "validate_player_facing_referential_clarity",
        "_try_strict_social_local_pronoun_substitution_repair",
    }
)
BJ124_DEAD_GATE_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "strict_social_emission_will_apply",
    "_default_response_type_debug",
    "_default_response_delta_meta",
    "_apply_visibility_enforcement",
    "minimal_social_emergency_fallback_line",
    "_finalize_emission_output",
    "_final_emission_fast_path_eligible",
    "validate_player_facing_referential_clarity",
    "_try_strict_social_local_pronoun_substitution_repair",
)

# Cycle BJ-127 — global stale gate harness scan (extends BJ-123 fragment/allowlist locks).
BJ127_GLOBAL_SCAN_EXCLUDE: Final[frozenset[str]] = frozenset(
    {
        "tests/test_ownership_registry.py",
        "tests/test_final_emission_gate.py",
        "tests/test_architecture_audit_tool.py",
        "tests/ownership_closeout_delegate_locks.py",
    }
)
BJ127_FEG_ALIAS_IMPORT_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "tests/helpers/gate_equivalence_monkeypatch.py",
        "tests/test_final_emission_gate.py",
        "tests/test_ownership_registry.py",
        "tests/test_speaker_contract_enforcement_extraction.py",
        "tests/test_diegetic_fallback_narration.py",
        "tests/test_final_emission_acceptance_quality.py",
        "tests/test_final_emission_response_type.py",
        "tests/test_final_emission_scene_state_anchor.py",
        "tests/test_final_emission_visibility.py",
        "tests/test_final_emission_sealed_fallback.py",
        "tests/test_c4_narrative_mode_live_pipeline.py",
        "tests/test_answer_shape_primacy.py",
        "tests/test_final_emission_fast_fallback_composition.py",
        "tests/test_final_emission_visibility_fallback.py",
        "tests/test_dialogue_social_plan.py",
    }
)
BJ127_FEG_ALIAS_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "import game.final_emission_gate as feg",
    "import game.final_emission_gate as _feg",
    "import game.final_emission_gate as feg_module",
)


_OWNERSHIP_REGISTRY_PATH = _REPO_ROOT / "tests/test_ownership_registry.py"


def repo_root() -> Path:
    return _REPO_ROOT


def get_repo_root() -> Path:
    return _REPO_ROOT


def ownership_registry_doc() -> str:
    """Return central ownership registry source (enforcement hub docstring corpus)."""
    return _OWNERSHIP_REGISTRY_PATH.read_text(encoding="utf-8")


def collect_stale_feg_patch_fragment_violations(
    rel_path: str,
    text: str,
    *,
    fragments: tuple[str, ...] = BJ123_STALE_FEG_PATCH_FRAGMENTS,
) -> list[str]:
    """Return violations when a test/harness file retains stale feg patch fragments."""
    return [
        f"{rel_path} still has stale feg seam fragment: {frag!r}"
        for frag in fragments
        if frag in text
    ]


def iter_bj127_global_harness_scan_paths(repo_root: Path | None = None) -> tuple[str, ...]:
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "tests").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel in BJ127_GLOBAL_SCAN_EXCLUDE:
            continue
        paths.append(rel)
    return tuple(paths)


def collect_bj127_feg_alias_import_violations(rel_path: str, text: str) -> list[str]:
    """Return BJ-127 stale fragment and feg-alias import violations for one file."""
    violations = collect_stale_feg_patch_fragment_violations(rel_path, text)
    if any(marker in text for marker in BJ127_FEG_ALIAS_IMPORT_MARKERS):
        if rel_path not in BJ127_FEG_ALIAS_IMPORT_ALLOWLIST:
            uses_alias = "feg." in text or "_feg." in text or "feg_module." in text
            if not uses_alias:
                violations.append(
                    f"{rel_path} imports final_emission_gate alias but never uses it "
                    f"(remove dead import or add to _BJ127_FEG_ALIAS_IMPORT_ALLOWLIST)"
                )
    return violations

def verify_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """Cycle BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    import game.final_emission_visibility_fallback as visibility_fallback

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert not hasattr(feg, "_apply_visibility_enforcement")
    assert callable(getattr(visibility_fallback, "apply_visibility_enforcement", None))

def verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly() -> None:
    """Cycle BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as te

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_tone_escalation_layer(" in nss_src
    assert "apply_tone_escalation_layer(" in ss_src
    assert "feg._apply_tone_escalation_layer" not in nss_src
    assert "feg._apply_tone_escalation_layer" not in ss_src
    assert not hasattr(feg, "_apply_tone_escalation_layer")
    assert callable(getattr(te, "apply_tone_escalation_layer", None))

def verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly() -> None:
    """Cycle BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_narrative_authority_layer(" in nss_src
    assert "apply_narrative_authority_layer(" in ss_src
    assert "feg._apply_narrative_authority_layer" not in nss_src
    assert "feg._apply_narrative_authority_layer" not in ss_src
    assert not hasattr(feg, "_apply_narrative_authority_layer")
    assert callable(getattr(na, "apply_narrative_authority_layer", None))

def verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly() -> None:
    """Cycle BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    import inspect

    import game.final_emission_anti_railroading as ar
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_anti_railroading_layer(" in nss_src
    assert "apply_anti_railroading_layer(" in ss_src
    assert "feg._apply_anti_railroading_layer" not in nss_src
    assert "feg._apply_anti_railroading_layer" not in ss_src
    assert not hasattr(feg, "_apply_anti_railroading_layer")
    assert callable(getattr(ar, "apply_anti_railroading_layer", None))

def verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly() -> None:
    """Cycle BJ-82: strict and non-strict stacks call context_separation owner directly."""
    import inspect

    import game.final_emission_context_separation as cs
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_context_separation_layer(" in nss_src
    assert "apply_context_separation_layer(" in ss_src
    assert "feg._apply_context_separation_layer" not in nss_src
    assert "feg._apply_context_separation_layer" not in ss_src
    assert not hasattr(feg, "_apply_context_separation_layer")
    assert callable(getattr(cs, "apply_context_separation_layer", None))

def verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly() -> None:
    """Cycle BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_player_facing_narration_purity as pfp
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_player_facing_narration_purity_layer(" in nss_src
    assert "apply_player_facing_narration_purity_layer(" in ss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in nss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in ss_src
    assert not hasattr(feg, "_apply_player_facing_narration_purity_layer")
    assert callable(getattr(pfp, "apply_player_facing_narration_purity_layer", None))

def verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """Cycle BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    import inspect

    import game.final_emission_answer_shape_primacy as asp
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")
    assert callable(getattr(asp, "apply_answer_shape_primacy_layer", None))

def verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly() -> None:
    """Cycle BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_state_anchor as ssa
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src
    assert not hasattr(feg, "_apply_scene_state_anchor_layer")
    assert callable(getattr(ssa, "apply_scene_state_anchor_layer", None))

def verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly() -> None:
    """Cycle BJ-71: apply_final_emission_gate calls non_strict_stack owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss

    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src
    assert not hasattr(feg, "_run_non_strict_layer_stack")
    assert callable(getattr(nss, "run_non_strict_layer_stack", None))

def verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly() -> None:
    """Cycle BJ-70: apply_final_emission_gate calls generic/strict-social exit owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge
    import game.final_emission_strict_social_stack as ss

    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_strict_social_composition_trunk(" in gate_src
    assert "run_generic_accept_exit(" in gate_src
    assert "run_generic_replace_exit(" in gate_src
    assert "_run_strict_social_composition_trunk" not in gate_src
    assert "_run_generic_accept_exit" not in gate_src
    assert "_run_generic_replace_exit" not in gate_src
    for name in (
        "_run_strict_social_composition_trunk",
        "_run_generic_accept_exit",
        "_run_generic_replace_exit",
    ):
        assert not hasattr(feg, name), name
    assert callable(getattr(ss, "run_strict_social_composition_trunk", None))
    assert callable(getattr(ge, "run_generic_accept_exit", None))
    assert callable(getattr(ge, "run_generic_replace_exit", None))

def verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """Cycle BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    import inspect

    import game.final_emission_fast_fallback_composition as ffnc
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src
    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")
    assert callable(getattr(ffnc, "apply_fast_fallback_neutral_composition_layer", None))

def verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """Cycle BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_answer_completeness_layer(" in nss_src
    assert "feg._apply_answer_completeness_layer" not in nss_src
    assert "emission_repairs._apply_answer_completeness_layer(" in ss_src
    assert "feg._apply_answer_completeness_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_completeness_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_completeness_layer", None))

def verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """Cycle BJ-88: stacks call final_emission_repairs answer exposition plan directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss)
    assert "_apply_answer_exposition_plan_layer(" in nss_src
    assert "feg._apply_answer_exposition_plan_layer" not in nss_src
    assert ss_src.count("emission_repairs._apply_answer_exposition_plan_layer(") == 3
    assert "feg._apply_answer_exposition_plan_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_exposition_plan_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_exposition_plan_layer", None))

def verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly() -> None:
    """Cycle BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_response_delta_layer(" in nss_src
    assert "feg._apply_response_delta_layer" not in nss_src
    assert "emission_repairs._apply_response_delta_layer(" in ss_src
    assert "feg._apply_response_delta_layer" not in ss_src
    assert not hasattr(feg, "_apply_response_delta_layer")
    assert callable(getattr(emission_repairs, "_apply_response_delta_layer", None))

def verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """Cycle BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_social_response_structure_layer(" in nss_src
    assert "feg._apply_social_response_structure_layer" not in nss_src
    assert "emission_repairs._apply_social_response_structure_layer(" in ss_src
    assert "feg._apply_social_response_structure_layer" not in ss_src
    assert not hasattr(feg, "_apply_social_response_structure_layer")
    assert callable(getattr(emission_repairs, "_apply_social_response_structure_layer", None))

def verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """Cycle BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_narrative_authenticity_layer(" in nss_src
    assert "feg._apply_narrative_authenticity_layer" not in nss_src
    assert "emission_repairs._apply_narrative_authenticity_layer(" in ss_src
    assert "feg._apply_narrative_authenticity_layer" not in ss_src
    assert not hasattr(feg, "_apply_narrative_authenticity_layer")
    assert callable(getattr(emission_repairs, "_apply_narrative_authenticity_layer", None))

def verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """Cycle BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "_apply_fallback_behavior_layer(" in nss_src
    assert "feg._apply_fallback_behavior_layer" not in nss_src
    assert "_apply_fallback_behavior_layer(" in tp_src
    assert "feg._apply_fallback_behavior_layer" not in tp_src
    assert not hasattr(feg, "_apply_fallback_behavior_layer")
    assert callable(getattr(emission_repairs, "_apply_fallback_behavior_layer", None))

def verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-93: stacks call final_emission_repairs fallback debug/meta merge helpers directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in nss_src
    assert "merge_fallback_behavior_into_emission_debug(" in tp_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in tp_src
    assert "_merge_fallback_behavior_meta(" in tp_src
    assert "feg._merge_fallback_behavior_meta" not in tp_src
    assert not hasattr(feg, "_merge_fallback_behavior_into_emission_debug")
    assert not hasattr(feg, "_merge_fallback_behavior_meta")
    assert callable(getattr(emission_repairs, "merge_fallback_behavior_into_emission_debug", None))
    assert callable(getattr(emission_repairs, "_merge_fallback_behavior_meta", None))

def verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BU2-A: conversational memory debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "merge_conversational_memory_inspection_into_emission_debug(" not in src
    assert "merge_conversational_memory_inspection_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_conversational_memory_inspection_into_emission_debug")
    assert callable(
        getattr(emission_repairs, "merge_conversational_memory_inspection_into_emission_debug", None)
    )

def verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BU2-A: scene_state_anchor debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_state_anchor as scene_state_anchor
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_scene_state_anchor_into_emission_debug(" not in src
    assert "_merge_scene_state_anchor_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_scene_state_anchor_into_emission_debug")
    assert callable(getattr(scene_state_anchor, "_merge_scene_state_anchor_into_emission_debug", None))

def verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: tone_escalation debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as tone_escalation

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_tone_escalation_into_emission_debug(" not in src
    assert "merge_tone_escalation_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_tone_escalation_into_emission_debug")
    assert callable(getattr(tone_escalation, "merge_tone_escalation_into_emission_debug", None))

def verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narrative_authority debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as narrative_authority
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_narrative_authority_into_emission_debug(" not in src
    assert "merge_narrative_authority_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_narrative_authority_into_emission_debug")
    assert callable(getattr(narrative_authority, "merge_narrative_authority_into_emission_debug", None))

def verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BU2-A: anti_railroading debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_anti_railroading as anti_railroading
    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_anti_railroading_into_emission_debug(" not in src
    assert "merge_anti_railroading_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_anti_railroading_into_emission_debug")
    assert callable(getattr(anti_railroading, "merge_anti_railroading_into_emission_debug", None))

def verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: context_separation debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_context_separation as context_separation
    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_context_separation_into_emission_debug(" not in src
    assert "merge_context_separation_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_context_separation_into_emission_debug")
    assert callable(getattr(context_separation, "merge_context_separation_into_emission_debug", None))

def verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narration_purity debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_player_facing_narration_purity as narration_purity
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_player_facing_narration_purity_into_emission_debug(" not in src
    assert "merge_player_facing_narration_purity_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_player_facing_narration_purity_into_emission_debug")
    assert callable(
        getattr(narration_purity, "merge_player_facing_narration_purity_into_emission_debug", None)
    )

def verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BU2-A: answer_shape_primacy debug merge consolidated on fem_assembly pre-terminal helper."""
    import inspect

    import game.final_emission_answer_shape_primacy as answer_shape_primacy
    import game.final_emission_fem_assembly as fem_assembly
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    fa_src = inspect.getsource(fem_assembly.merge_pre_terminal_layer_debug)
    for src in (nss_src, ss_src):
        assert "fem_assembly.merge_pre_terminal_layer_debug(" in src
        assert "_merge_answer_shape_primacy_into_emission_debug(" not in src
    assert "merge_answer_shape_primacy_into_emission_debug(" in fa_src
    assert not hasattr(feg, "_merge_answer_shape_primacy_into_emission_debug")
    assert callable(getattr(answer_shape_primacy, "merge_answer_shape_primacy_into_emission_debug", None))

def verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """Cycle BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as tone_escalation

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "flag_non_hostile_escalation_from_writer_pregate(" in ss_src
    assert "feg._flag_non_hostile_escalation_from_writer_pregate" not in ss_src
    assert not hasattr(feg, "_flag_non_hostile_escalation_from_writer_pregate")
    assert callable(getattr(tone_escalation, "flag_non_hostile_escalation_from_writer_pregate", None))

def verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """Cycle BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_emit_integrity as scene_emit_integrity
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_compute_scene_emit_integrity_assessment(" in nss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in nss_src
    assert "_compute_scene_emit_integrity_assessment(" in ss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in ss_src
    assert not hasattr(feg, "_compute_scene_emit_integrity_assessment")
    assert callable(getattr(scene_emit_integrity, "_compute_scene_emit_integrity_assessment", None))

def verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """Cycle BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_passive_scene_pressure as passive_scene_pressure

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "_passive_scene_pressure_due_for_fallback(" in nss_src
    assert "feg._passive_scene_pressure_due_for_fallback" not in nss_src
    assert not hasattr(feg, "_passive_scene_pressure_due_for_fallback")
    assert callable(getattr(passive_scene_pressure, "_passive_scene_pressure_due_for_fallback", None))

def verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """Cycle BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_narrative_mode_output as narrative_mode_output
    import game.final_emission_non_strict_stack as nss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "_narrative_mode_output_legality_assessment(" in nss_src
    assert "feg._narrative_mode_output_legality_assessment" not in nss_src
    assert not hasattr(feg, "_narrative_mode_output_legality_assessment")
    assert callable(getattr(narrative_mode_output, "_narrative_mode_output_legality_assessment", None))

def verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly() -> None:
    """Cycle BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "response_type_decision_payload(" in ss_src
    assert "feg._response_type_decision_payload" not in ss_src
    assert "response_type_decision_payload(" in ge_accept_src
    assert "feg._response_type_decision_payload" not in ge_accept_src
    assert "response_type_decision_payload(" in ge_replace_src
    assert "feg._response_type_decision_payload" not in ge_replace_src
    assert not hasattr(feg, "_response_type_decision_payload")
    assert callable(getattr(emission_meta, "response_type_decision_payload", None))

def verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """Cycle BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    assert "infer_accept_path_final_emitted_source(" in ss_src
    assert "feg.infer_accept_path_final_emitted_source" not in ss_src
    assert "infer_accept_path_final_emitted_source(" in ge_accept_src
    assert "feg.infer_accept_path_final_emitted_source" not in ge_accept_src
    assert not hasattr(feg, "infer_accept_path_final_emitted_source")
    assert callable(getattr(emission_meta, "infer_accept_path_final_emitted_source", None))

def verify_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """Cycle BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "apply_opening_fallback_projection_fields(" in ge_replace_src
    assert "feg.apply_opening_fallback_projection_fields" not in ge_replace_src
    assert "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" in ge_replace_src
    assert "feg.OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" not in ge_replace_src
    assert not hasattr(feg, "apply_opening_fallback_projection_fields")
    assert not hasattr(feg, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")
    assert callable(getattr(emission_meta, "apply_opening_fallback_projection_fields", None))
    assert hasattr(emission_meta, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")

def verify_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly() -> None:
    """Cycle BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "FINAL_EMISSION_META_KEY" in ss_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ss_src
    assert "FINAL_EMISSION_META_KEY" in ge_accept_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_accept_src
    assert "FINAL_EMISSION_META_KEY" in ge_replace_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_replace_src
    assert not hasattr(feg, "FINAL_EMISSION_META_KEY")
    assert hasattr(emission_meta, "FINAL_EMISSION_META_KEY")

def verify_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """Cycle BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    import inspect

    import game.final_emission_boundary_contract as boundary_contract
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "assert_final_emission_mutation_allowed(" in ge_replace_src
    assert "feg.assert_final_emission_mutation_allowed" not in ge_replace_src
    assert not hasattr(feg, "assert_final_emission_mutation_allowed")
    assert callable(getattr(boundary_contract, "assert_final_emission_mutation_allowed", None))

def verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly() -> None:
    """Cycle BJ-111: stack/exit callers use final_emission_text_formatting._normalize_text directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_text_formatting as emission_text_formatting

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "_normalize_text(" in nss_src
    assert "feg._normalize_text(" not in nss_src
    assert "_normalize_text(" in ss_src
    assert "feg._normalize_text(" not in ss_src
    assert "_normalize_text(" in ge_accept_src
    assert "feg._normalize_text(" not in ge_accept_src
    assert "_normalize_text(" in ge_replace_src
    assert "feg._normalize_text(" not in ge_replace_src
    assert not hasattr(feg, "_normalize_text")
    assert callable(getattr(emission_text_formatting, "_normalize_text", None))

def verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """Cycle BJ-112: strict_social_stack calls final_emission_text_formatting._normalize_text_preserve_paragraphs directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_text_formatting as emission_text_formatting

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_normalize_text_preserve_paragraphs(" in ss_src
    assert "feg._normalize_text_preserve_paragraphs" not in ss_src
    assert not hasattr(feg, "_normalize_text_preserve_paragraphs")
    assert callable(getattr(emission_text_formatting, "_normalize_text_preserve_paragraphs", None))

def verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """Cycle BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    import inspect

    import game.diegetic_fallback_narration as diegetic_fallback_narration
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "diegetic_classified_fallback_meta(" in ge_replace_src
    assert "feg.diegetic_classified_fallback_meta" not in ge_replace_src
    assert not hasattr(feg, "diegetic_classified_fallback_meta")
    assert callable(getattr(diegetic_fallback_narration, "fallback_template_metadata", None))

def verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """Cycle BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    import inspect

    import game.anti_reset_emission_guard as anti_reset_emission_guard
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "anti_reset_suppresses_intro_style_fallbacks(" in ge_replace_src
    assert "feg.anti_reset_suppresses_intro_style_fallbacks" not in ge_replace_src
    assert not hasattr(feg, "anti_reset_suppresses_intro_style_fallbacks")
    assert callable(getattr(anti_reset_emission_guard, "anti_reset_suppresses_intro_style_fallbacks", None))

def verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """Cycle BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_strict_social_stack as ss
    import game.social_exchange_emission as social_exchange_emission

    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "log_final_emission_decision(" in ge_accept_src
    assert "log_final_emission_trace(" in ge_accept_src
    assert "feg.log_final_emission_decision" not in ge_accept_src
    assert "feg.log_final_emission_trace" not in ge_accept_src
    assert "log_final_emission_decision(" in ge_replace_src
    assert "log_final_emission_trace(" in ge_replace_src
    assert "feg.log_final_emission_decision" not in ge_replace_src
    assert "feg.log_final_emission_trace" not in ge_replace_src
    assert "log_final_emission_decision(" in ss_src
    assert "log_final_emission_trace(" in ss_src
    assert "feg.log_final_emission_decision" not in ss_src
    assert "feg.log_final_emission_trace" not in ss_src
    assert not hasattr(feg, "log_final_emission_decision")
    assert not hasattr(feg, "log_final_emission_trace")
    assert callable(getattr(social_exchange_emission, "log_final_emission_decision", None))
    assert callable(getattr(social_exchange_emission, "log_final_emission_trace", None))

def verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """Cycle BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.social_exchange_emission as social_exchange_emission

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "build_final_strict_social_response(" in ss_src
    assert "minimal_social_emergency_fallback_line(" in ss_src
    assert "strict_social_deterministic_fallback_family_token(" in ss_src
    assert "feg.build_final_strict_social_response" not in ss_src
    assert "feg.minimal_social_emergency_fallback_line" not in ss_src
    assert "feg.strict_social_deterministic_fallback_family_token" not in ss_src
    assert not hasattr(feg, "build_final_strict_social_response")
    assert not hasattr(feg, "minimal_social_emergency_fallback_line")
    assert not hasattr(feg, "strict_social_deterministic_fallback_family_token")
    assert callable(getattr(social_exchange_emission, "build_final_strict_social_response", None))
    assert callable(getattr(social_exchange_emission, "minimal_social_emergency_fallback_line", None))
    assert callable(getattr(social_exchange_emission, "strict_social_deterministic_fallback_family_token", None))

def verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """Cycle BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    import inspect

    import game.fallback_provenance_debug as fallback_provenance_debug
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.stage_diff_telemetry as stage_diff_telemetry

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "record_stage_snapshot(" in ss_src
    assert "realign_fallback_provenance_selector_to_current_text(" in ss_src
    assert "feg.record_stage_snapshot" not in ss_src
    assert "feg.realign_fallback_provenance_selector_to_current_text" not in ss_src
    assert not hasattr(feg, "record_stage_snapshot")
    assert not hasattr(feg, "realign_fallback_provenance_selector_to_current_text")
    assert callable(getattr(stage_diff_telemetry, "record_stage_snapshot", None))
    assert callable(getattr(fallback_provenance_debug, "realign_fallback_provenance_selector_to_current_text", None))

def verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate() -> None:
    """Cycle BJ-118: should_replace_candidate_intro_fallback lives on anti_reset owner, not gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard
    import game.final_emission_gate as feg

    assert not hasattr(feg, "should_replace_candidate_intro_fallback")
    assert callable(getattr(anti_reset_emission_guard, "should_replace_candidate_intro_fallback", None))

def verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate() -> None:
    """Cycle BJ-119: stage_diff_telemetry helpers live on stage_diff owner, not gate."""
    import game.final_emission_gate as feg
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "diff_turn_stage")
    assert not hasattr(feg, "record_stage_transition")
    assert not hasattr(feg, "snapshot_turn_stage")
    assert callable(getattr(stage_diff_telemetry, "diff_turn_stage", None))
    assert callable(getattr(stage_diff_telemetry, "record_stage_transition", None))
    assert callable(getattr(stage_diff_telemetry, "snapshot_turn_stage", None))

def verify_bj120_ownership_registry_harness_patches_canonical_owner_seams() -> None:
    """Cycle BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    import inspect

    import tests.helpers.gate_equivalence_monkeypatch as gate_mp
    import tests.test_turn_packet_stage_diff_integration as tp_stage_diff

    mp_src = inspect.getsource(gate_mp.patch_build_final_strict_social_response)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in mp_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in mp_src
    tp_src = inspect.getsource(tp_stage_diff.test_gate_exit_records_observability_before_cache_pop)
    assert 'monkeypatch.setattr(emission_finalize, "record_stage_snapshot"' in tp_src
    assert 'monkeypatch.setattr(feg, "record_stage_snapshot"' not in tp_src
    assert "import game.final_emission_gate as feg" not in inspect.getsource(tp_stage_diff)

def verify_bj121_ownership_registry_strict_social_build_patches_use_stack_seam() -> None:
    """Cycle BJ-121: strict-social build monkeypatches target strict_social_stack, not gate."""
    import inspect
    import pathlib

    import tests.helpers.strict_social_harness as strict_social_harness

    harness_src = inspect.getsource(strict_social_harness.run_strict_social_motive_overclaim_gate_case)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in harness_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in harness_src

    repo_root = get_repo_root()
    for rel in (
        "tests/test_fallback_behavior_gate.py",
        "tests/test_scene_state_anchoring.py",
        "tests/helpers/gate_equivalence_monkeypatch.py",
        "tests/helpers/strict_social_harness.py",
    ):
        text = (repo_root / rel).read_text(encoding="utf-8")
        assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in text
        assert 'monkeypatch.setattr(feg_module, "build_final_strict_social_response"' not in text

def verify_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings() -> None:
    """Cycle BJ-122: scene_state_anchoring tests use final_emission_scene_state_anchor owner bindings."""
    import inspect

    import tests.test_scene_state_anchoring as scene_state_anchoring_tests

    module_src = inspect.getsource(scene_state_anchoring_tests)
    assert "import game.final_emission_gate as feg" not in module_src
    assert 'monkeypatch.setattr(feg, "_repair_location_opening"' not in module_src
    assert 'monkeypatch.setattr(feg, "validate_scene_state_anchoring"' not in module_src
    assert "feg._resolve_scene_state_anchor_contract" not in module_src
    assert "feg._merge_scene_state_anchor_meta" not in module_src

def verify_bj123_ownership_registry_harness_patches_no_stale_feg_seams() -> None:
    """Cycle BJ-123: tests/helpers patch canonical owner modules, not removed feg re-exports."""
    import inspect
    import pathlib

    import tests.helpers.gate_equivalence_monkeypatch as gate_mp

    repo_root = get_repo_root()
    for rel in BJ123_HARNESS_PATCH_SCAN_PATHS:
        text = (repo_root / rel).read_text(encoding="utf-8")
        for frag in BJ123_STALE_FEG_PATCH_FRAGMENTS:
            assert frag not in text, f"{rel} still has stale feg seam fragment: {frag!r}"

    mp_src = inspect.getsource(gate_mp.patch_get_speaker_selection_contract)
    assert 'monkeypatch.setattr(feg, "get_speaker_selection_contract"' in mp_src
    assert 'monkeypatch.setattr(sce, "get_speaker_selection_contract"' in mp_src

    smoke_src = (repo_root / "tests/helpers/emission_smoke_assertions.py").read_text(encoding="utf-8")
    assert "game.social_exchange_emission.strict_social_emission_will_apply" in smoke_src
    assert "game.final_emission_gate.strict_social_emission_will_apply" not in smoke_src

    registry_doc = ownership_registry_doc()
    assert "BJ-123" in registry_doc
    assert "get_speaker_selection_contract" in registry_doc

def verify_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports() -> None:
    """Cycle BJ-124: gate module must not re-export BJ-123-dead harness seams."""
    import game.final_emission_gate as feg

    gate_path = Path(feg.__file__)
    gate_src = gate_path.read_text(encoding="utf-8")

    for name in BJ124_DEAD_GATE_REEXPORT_SYMBOLS:
        assert not hasattr(feg, name), f"gate still re-exports dead seam: {name!r}"

    for marker in BJ124_DEAD_GATE_IMPORT_MARKERS:
        assert marker not in gate_src, f"gate source still imports dead seam marker: {marker!r}"

    assert callable(getattr(feg, "apply_final_emission_gate", None))
    assert callable(getattr(feg, "get_speaker_selection_contract", None))

    registry_doc = ownership_registry_doc()
    assert "BJ-124" in registry_doc

def verify_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-125/BN8: anti-reset tests patch social_exchange_emission + preflight strict-social seam."""
    import inspect
    import pathlib

    import tests.test_anti_reset_emission_guard as anti_reset_tests

    module_src = inspect.getsource(anti_reset_tests)
    assert "import game.final_emission_gate as" not in module_src
    assert "from game.final_emission_gate import" not in module_src
    assert "feg." not in module_src
    assert "_feg" not in module_src
    assert 'monkeypatch.setattr(social_exchange_policy, "strict_social_emission_will_apply"' in module_src
    assert 'monkeypatch.setattr(gate_preflight_strict_social, "strict_social_emission_will_apply"' in module_src
    assert 'monkeypatch.setattr(feg, "strict_social_emission_will_apply"' not in module_src
    assert '"game.final_emission_gate.strict_social_emission_will_apply"' not in module_src

    rel = "tests/test_anti_reset_emission_guard.py"
    text = (pathlib.Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")
    for frag in (
        'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
        '"game.final_emission_gate.strict_social_emission_will_apply"',
        "import game.final_emission_gate as",
        "from game.final_emission_gate import",
    ):
        assert frag not in text, f"anti_reset test still uses stale gate seam: {frag!r}"
    assert "import game.final_emission_gate_preflight_strict_social as gate_preflight_strict_social" in text

    registry_doc = ownership_registry_doc()
    assert "BJ-125" in registry_doc

def verify_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-126/BN8: narration transcript tests patch owner + preflight strict-social seam."""
    import inspect
    import pathlib

    import tests.test_narration_transcript_regressions as narration_transcript_tests

    module_src = inspect.getsource(narration_transcript_tests)
    assert "import game.final_emission_gate as" not in module_src
    assert "from game.final_emission_gate import" not in module_src
    assert "_feg" not in module_src
    assert 'monkeypatch.setattr(feg, "strict_social_emission_will_apply"' not in module_src
    assert '"game.final_emission_gate.strict_social_emission_will_apply"' not in module_src
    assert "def patch_strict_social_emission_will_apply(" in module_src
    helper_src = inspect.getsource(narration_transcript_tests.patch_strict_social_emission_will_apply)
    assert 'monkeypatch.setattr(social_exchange_policy, "strict_social_emission_will_apply"' in helper_src
    assert 'monkeypatch.setattr(gate_preflight_strict_social, "strict_social_emission_will_apply"' in helper_src
    vis_src = inspect.getsource(narration_transcript_tests.patch_final_emission_helpers)
    assert 'monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement"' in vis_src
    assert 'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"' not in vis_src

    rel = "tests/test_narration_transcript_regressions.py"
    text = (pathlib.Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")
    for frag in (
        'monkeypatch.setattr(_feg, "strict_social_emission_will_apply"',
        'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
        '"game.final_emission_gate.strict_social_emission_will_apply"',
        'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"',
        "import game.final_emission_gate as",
    ):
        assert frag not in text, f"narration transcript test still uses stale gate seam: {frag!r}"

    registry_doc = ownership_registry_doc()
    assert "BJ-126" in registry_doc

def verify_bj127_ownership_registry_global_stale_gate_harness_scan() -> None:
    """Cycle BJ-127: global scan — no stale feg monkeypatches or dead feg alias imports."""
    import pathlib

    repo_root = get_repo_root()
    for path in sorted((repo_root / "tests").rglob("*.py")):
        rel = path.relative_to(repo_root).as_posix()
        if rel in BJ127_GLOBAL_SCAN_EXCLUDE:
            continue
        text = path.read_text(encoding="utf-8")
        for frag in BJ123_STALE_FEG_PATCH_FRAGMENTS:
            assert frag not in text, f"{rel} still has stale feg seam fragment: {frag!r}"

        if any(marker in text for marker in BJ127_FEG_ALIAS_IMPORT_MARKERS):
            if rel not in BJ127_FEG_ALIAS_IMPORT_ALLOWLIST:
                uses_alias = "feg." in text or "_feg." in text or "feg_module." in text
                assert uses_alias, (
                    f"{rel} imports final_emission_gate alias but never uses it "
                    f"(remove dead import or add to _BJ127_FEG_ALIAS_IMPORT_ALLOWLIST)"
                )

    registry_doc = ownership_registry_doc()
    assert "BJ-127" in registry_doc

def verify_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports() -> None:
    """Cycle BJ-128: gate module keeps orchestration + live seams only; no import-only residue."""
    import game.final_emission_gate as feg

    assert_gate_bj128_no_dead_import_reexports(feg)

    registry_doc = ownership_registry_doc()
    assert "BJ-128" in registry_doc

def verify_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked() -> None:
    """Cycle BJ-129: gate module must not regrow beyond orchestration + documented live seams."""
    import game.final_emission_gate as feg

    assert_gate_bj129_thin_boundary_shape(feg)

    gate_src = Path(feg.__file__).read_text(encoding="utf-8")
    assert gate_import_modules(gate_src) == BJ129_ALLOWED_GATE_IMPORT_MODULES

    registry_doc = ownership_registry_doc()
    assert "BJ-129" in registry_doc
    assert "_BJ129_ALLOWED_GATE_IMPORT_MODULES" in registry_doc
    assert "_BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES" in registry_doc

def verify_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly() -> None:
    """Cycle BJ-72: apply_final_emission_gate calls gate_context owner directly."""
    from tests.helpers.gate_delegator_governance import (
        GATE,
        GATE_CONTEXT,
        assert_gate_lacks,
        assert_owner_callable,
        function_source,
    )

    gate_src = function_source(GATE, "apply_final_emission_gate")
    assert "initialize_gate_execution_context(" in gate_src
    assert "_initialize_gate_execution_context" not in gate_src
    assert_gate_lacks("_initialize_gate_execution_context")
    assert_owner_callable(GATE_CONTEXT, "initialize_gate_execution_context")

def verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """Cycle BJ-74: terminal pipeline calls acceptance_quality N4 floor seam owner directly."""
    import inspect

    import game.final_emission_acceptance_quality as aq
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")
    assert callable(getattr(aq, "apply_acceptance_quality_n4_floor_seam", None))

def verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """Cycle BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    import game.interaction_continuity as ic

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "attach_interaction_continuity_validation(" in tp_src
    assert "feg._attach_interaction_continuity_validation" not in tp_src
    assert not hasattr(feg, "_attach_interaction_continuity_validation")
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))

def verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly() -> None:
    """Cycle BJ-76: terminal pipeline and non_strict_stack call IC emission-step owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_terminal_pipeline as tp
    import game.interaction_continuity as ic

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_interaction_continuity_emission_step(" in tp_src
    assert "feg._apply_interaction_continuity_emission_step" not in tp_src
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "apply_interaction_continuity_emission_step(" in nss_src
    assert "feg._apply_interaction_continuity_emission_step" not in nss_src
    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))

def verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """Cycle BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.speaker_contract_enforcement as sce

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "enforce_emitted_speaker_with_contract(" in ss_src
    assert "feg.enforce_emitted_speaker_with_contract" not in ss_src
    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert callable(getattr(sce, "enforce_emitted_speaker_with_contract", None))

def verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly() -> None:
    """Cycle BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.speaker_contract_enforcement as sce

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_sync_eff_social_to_resolution(" in ss_src
    assert "feg._sync_eff_social_to_resolution" not in ss_src
    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert callable(getattr(sce, "_sync_eff_social_to_resolution", None))

