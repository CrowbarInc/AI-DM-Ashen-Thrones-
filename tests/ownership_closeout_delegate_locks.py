"""BJ delegate-collapse closeout lock helpers (import-light; no pytest).

Delegate-collapse closeout locks (cycles BJ-70–BJ-129) verify that ``final_emission_gate``
orchestration delegates to owner modules rather than retaining gate wrappers. Enforced by ``test_bj*`` functions in ``tests/test_gate_delegate_closeout_locks.py``.

Cycles BJ-70–BJ-114 route ownership checks through
``tests.helpers.gate_delegator_governance`` assertion helpers (BJ-93 primitive-routed).
Intentional direct exceptions:

- BJ-108/109: constant-presence / module-attribute meta locks.
- BJ-120–127: harness / stale-FEG source and repo scans.
- BJ-128/129: thin-boundary locks (``gate_thin_boundary_locks``).

BJ-115–119 use source primitives (``assert_function_source_contains``,
``assert_gate_lacks``, ``assert_owner_callable``).
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
        "tests/test_gate_delegate_closeout_locks.py",
        "tests/test_final_emission_gate.py",
        "tests/test_final_emission_gate_delegator_regression.py",
        "tests/test_architecture_audit_tool.py",
        "tests/ownership_closeout_delegate_locks.py",
    }
)
BJ127_FEG_ALIAS_IMPORT_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "tests/helpers/gate_equivalence_monkeypatch.py",
        "tests/test_final_emission_gate.py",
        "tests/test_gate_delegate_closeout_locks.py",
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


_DELEGATE_CLOSEOUT_LOCKS_TEST_PATH = _REPO_ROOT / "tests/test_gate_delegate_closeout_locks.py"


def repo_root() -> Path:
    return _REPO_ROOT


def get_repo_root() -> Path:
    return _REPO_ROOT


def ownership_registry_doc() -> str:
    """Return delegate closeout lock test source (BJ-123–BJ-129 corpus anchor)."""
    return _DELEGATE_CLOSEOUT_LOCKS_TEST_PATH.read_text(encoding="utf-8")


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
    from tests.helpers.gate_delegator_governance import (
        TERMINAL_PIPELINE,
        VISIBILITY_FALLBACK,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=VISIBILITY_FALLBACK,
        owner_attr="apply_visibility_enforcement",
        gate_private_attr="_apply_visibility_enforcement",
        callers=((TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),),
    )

def verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly() -> None:
    """Cycle BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    from tests.helpers.gate_delegator_governance import (
        TONE_ESCALATION,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=TONE_ESCALATION,
        owner_attr="apply_tone_escalation_layer",
        gate_private_attr="_apply_tone_escalation_layer",
    )

def verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly() -> None:
    """Cycle BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    from tests.helpers.gate_delegator_governance import (
        NARRATIVE_AUTHORITY,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=NARRATIVE_AUTHORITY,
        owner_attr="apply_narrative_authority_layer",
        gate_private_attr="_apply_narrative_authority_layer",
    )

def verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly() -> None:
    """Cycle BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    from tests.helpers.gate_delegator_governance import (
        ANTI_RAILROADING,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=ANTI_RAILROADING,
        owner_attr="apply_anti_railroading_layer",
        gate_private_attr="_apply_anti_railroading_layer",
    )

def verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly() -> None:
    """Cycle BJ-82: strict and non-strict stacks call context_separation owner directly."""
    from tests.helpers.gate_delegator_governance import (
        CONTEXT_SEPARATION,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=CONTEXT_SEPARATION,
        owner_attr="apply_context_separation_layer",
        gate_private_attr="_apply_context_separation_layer",
    )

def verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly() -> None:
    """Cycle BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    from tests.helpers.gate_delegator_governance import (
        NARRATION_PURITY,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=NARRATION_PURITY,
        owner_attr="apply_player_facing_narration_purity_layer",
        gate_private_attr="_apply_player_facing_narration_purity_layer",
    )

def verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """Cycle BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    from tests.helpers.gate_delegator_governance import (
        ANSWER_SHAPE_PRIMACY,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=ANSWER_SHAPE_PRIMACY,
        owner_attr="apply_answer_shape_primacy_layer",
        gate_private_attr="_apply_answer_shape_primacy_layer",
    )

def verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly() -> None:
    """Cycle BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    from tests.helpers.gate_delegator_governance import (
        SCENE_STATE_ANCHOR,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=SCENE_STATE_ANCHOR,
        owner_attr="apply_scene_state_anchor_layer",
        gate_private_attr="_apply_scene_state_anchor_layer",
    )

def verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly() -> None:
    """Cycle BJ-71: apply_final_emission_gate calls non_strict_stack owner directly."""
    from tests.helpers.gate_delegator_governance import (
        GATE,
        NON_STRICT_STACK,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=NON_STRICT_STACK,
        owner_attr="run_non_strict_layer_stack",
        gate_private_attr="_run_non_strict_layer_stack",
        callers=((GATE, "apply_final_emission_gate"),),
        forbidden_markers=("_run_non_strict_layer_stack",),
    )

def verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly() -> None:
    """Cycle BJ-70: apply_final_emission_gate calls generic/strict-social exit owners directly."""
    from tests.helpers.gate_delegator_governance import (
        GENERIC_EXIT,
        STRICT_SOCIAL_STACK,
        assert_gate_entrypoint_calls_owners_directly,
    )

    assert_gate_entrypoint_calls_owners_directly(
        owners=(
            (
                STRICT_SOCIAL_STACK,
                "run_strict_social_composition_trunk",
                "run_strict_social_composition_trunk(",
                "_run_strict_social_composition_trunk",
            ),
            (
                GENERIC_EXIT,
                "run_generic_accept_exit",
                "run_generic_accept_exit(",
                "_run_generic_accept_exit",
            ),
            (
                GENERIC_EXIT,
                "run_generic_replace_exit",
                "run_generic_replace_exit(",
                "_run_generic_replace_exit",
            ),
        ),
    )

def verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """Cycle BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    from tests.helpers.gate_delegator_governance import (
        FAST_FALLBACK,
        assert_dual_stacks_call_owner_directly,
    )

    assert_dual_stacks_call_owner_directly(
        owner_module=FAST_FALLBACK,
        owner_attr="apply_fast_fallback_neutral_composition_layer",
        gate_private_attr="_apply_fast_fallback_neutral_composition_layer",
    )

def verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """Cycle BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    from tests.helpers.gate_delegator_governance import assert_repairs_dual_stack_calls_owner_directly

    assert_repairs_dual_stack_calls_owner_directly(
        layer_attr="_apply_answer_completeness_layer",
    )

def verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """Cycle BJ-88: stacks call final_emission_repairs answer exposition plan directly."""
    from tests.helpers.gate_delegator_governance import assert_repairs_dual_stack_count_owner_calls

    assert_repairs_dual_stack_count_owner_calls(
        layer_attr="_apply_answer_exposition_plan_layer",
        strict_social_qualified_call_count=3,
    )

def verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly() -> None:
    """Cycle BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    from tests.helpers.gate_delegator_governance import assert_repairs_dual_stack_calls_owner_directly

    assert_repairs_dual_stack_calls_owner_directly(
        layer_attr="_apply_response_delta_layer",
    )

def verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """Cycle BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    from tests.helpers.gate_delegator_governance import assert_repairs_dual_stack_calls_owner_directly

    assert_repairs_dual_stack_calls_owner_directly(
        layer_attr="_apply_social_response_structure_layer",
    )

def verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """Cycle BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    from tests.helpers.gate_delegator_governance import assert_repairs_dual_stack_calls_owner_directly

    assert_repairs_dual_stack_calls_owner_directly(
        layer_attr="_apply_narrative_authenticity_layer",
    )

def verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """Cycle BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        TERMINAL_PIPELINE,
        assert_repairs_callers_call_owner_directly,
    )

    assert_repairs_callers_call_owner_directly(
        layer_attr="_apply_fallback_behavior_layer",
        callers=(
            (NON_STRICT_STACK, "run_non_strict_layer_stack"),
            (TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),
        ),
    )

def verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-93: stacks call final_emission_repairs fallback debug/meta merge helpers directly."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        REPAIRS,
        TERMINAL_PIPELINE,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
    )

    assert_function_source_contains(
        NON_STRICT_STACK,
        "run_non_strict_layer_stack",
        "merge_fallback_behavior_into_emission_debug(",
        forbidden=("feg._merge_fallback_behavior_into_emission_debug",),
    )
    assert_function_source_contains(
        TERMINAL_PIPELINE,
        "run_gate_terminal_enforcement_pipeline",
        "merge_fallback_behavior_into_emission_debug(",
        "_merge_fallback_behavior_meta(",
        forbidden=(
            "feg._merge_fallback_behavior_into_emission_debug",
            "feg._merge_fallback_behavior_meta",
        ),
    )
    assert_gate_lacks(
        "_merge_fallback_behavior_into_emission_debug",
        "_merge_fallback_behavior_meta",
    )
    assert_owner_callable(REPAIRS, "merge_fallback_behavior_into_emission_debug")
    assert_owner_callable(REPAIRS, "_merge_fallback_behavior_meta")

def verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BU2-A: conversational memory debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        REPAIRS,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=REPAIRS,
        owner_attr="merge_conversational_memory_inspection_into_emission_debug",
        gate_private_attr="_merge_conversational_memory_inspection_into_emission_debug",
        stack_forbidden_merge_call="merge_conversational_memory_inspection_into_emission_debug(",
        fem_assembly_merge_call="merge_conversational_memory_inspection_into_emission_debug(",
    )

def verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BU2-A: scene_state_anchor debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        SCENE_STATE_ANCHOR,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=SCENE_STATE_ANCHOR,
        owner_attr="_merge_scene_state_anchor_into_emission_debug",
        gate_private_attr="_merge_scene_state_anchor_into_emission_debug",
        stack_forbidden_merge_call="_merge_scene_state_anchor_into_emission_debug(",
        fem_assembly_merge_call="_merge_scene_state_anchor_into_emission_debug(",
    )

def verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: tone_escalation debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        TONE_ESCALATION,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=TONE_ESCALATION,
        owner_attr="merge_tone_escalation_into_emission_debug",
        gate_private_attr="_merge_tone_escalation_into_emission_debug",
        stack_forbidden_merge_call="_merge_tone_escalation_into_emission_debug(",
        fem_assembly_merge_call="merge_tone_escalation_into_emission_debug(",
    )

def verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narrative_authority debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        NARRATIVE_AUTHORITY,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=NARRATIVE_AUTHORITY,
        owner_attr="merge_narrative_authority_into_emission_debug",
        gate_private_attr="_merge_narrative_authority_into_emission_debug",
        stack_forbidden_merge_call="_merge_narrative_authority_into_emission_debug(",
        fem_assembly_merge_call="merge_narrative_authority_into_emission_debug(",
    )

def verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BU2-A: anti_railroading debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        ANTI_RAILROADING,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=ANTI_RAILROADING,
        owner_attr="merge_anti_railroading_into_emission_debug",
        gate_private_attr="_merge_anti_railroading_into_emission_debug",
        stack_forbidden_merge_call="_merge_anti_railroading_into_emission_debug(",
        fem_assembly_merge_call="merge_anti_railroading_into_emission_debug(",
    )

def verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: context_separation debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        CONTEXT_SEPARATION,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=CONTEXT_SEPARATION,
        owner_attr="merge_context_separation_into_emission_debug",
        gate_private_attr="_merge_context_separation_into_emission_debug",
        stack_forbidden_merge_call="_merge_context_separation_into_emission_debug(",
        fem_assembly_merge_call="merge_context_separation_into_emission_debug(",
    )

def verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narration_purity debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        NARRATION_PURITY,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=NARRATION_PURITY,
        owner_attr="merge_player_facing_narration_purity_into_emission_debug",
        gate_private_attr="_merge_player_facing_narration_purity_into_emission_debug",
        stack_forbidden_merge_call="_merge_player_facing_narration_purity_into_emission_debug(",
        fem_assembly_merge_call="merge_player_facing_narration_purity_into_emission_debug(",
    )

def verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BU2-A: answer_shape_primacy debug merge consolidated on fem_assembly pre-terminal helper."""
    from tests.helpers.gate_delegator_governance import (
        ANSWER_SHAPE_PRIMACY,
        assert_bu2a_debug_merge_consolidated_on_fem_assembly,
    )

    assert_bu2a_debug_merge_consolidated_on_fem_assembly(
        owner_module=ANSWER_SHAPE_PRIMACY,
        owner_attr="merge_answer_shape_primacy_into_emission_debug",
        gate_private_attr="_merge_answer_shape_primacy_into_emission_debug",
        stack_forbidden_merge_call="_merge_answer_shape_primacy_into_emission_debug(",
        fem_assembly_merge_call="merge_answer_shape_primacy_into_emission_debug(",
    )

def verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """Cycle BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    from tests.helpers.gate_delegator_governance import (
        STRICT_SOCIAL_STACK,
        TONE_ESCALATION,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=TONE_ESCALATION,
        owner_attr="flag_non_hostile_escalation_from_writer_pregate",
        gate_private_attr="_flag_non_hostile_escalation_from_writer_pregate",
        callers=((STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),),
    )

def verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """Cycle BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        SCENE_EMIT_INTEGRITY,
        STRICT_SOCIAL_STACK,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=SCENE_EMIT_INTEGRITY,
        owner_attr="_compute_scene_emit_integrity_assessment",
        callers=(
            (NON_STRICT_STACK, "run_non_strict_layer_stack"),
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),
        ),
    )

def verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """Cycle BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    from tests.helpers.gate_delegator_governance import (
        NON_STRICT_STACK,
        PASSIVE_SCENE_PRESSURE,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=PASSIVE_SCENE_PRESSURE,
        owner_attr="_passive_scene_pressure_due_for_fallback",
        callers=((NON_STRICT_STACK, "run_non_strict_layer_stack"),),
    )

def verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """Cycle BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    from tests.helpers.gate_delegator_governance import (
        NARRATIVE_MODE_OUTPUT,
        NON_STRICT_STACK,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=NARRATIVE_MODE_OUTPUT,
        owner_attr="_narrative_mode_output_legality_assessment",
        callers=((NON_STRICT_STACK, "run_non_strict_layer_stack"),),
    )

def verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly() -> None:
    """Cycle BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    from tests.helpers.gate_delegator_governance import (
        GENERIC_EXIT,
        META,
        STRICT_SOCIAL_STACK,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=META,
        owner_attr="response_type_decision_payload",
        gate_private_attr="_response_type_decision_payload",
        callers=(
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),
            (GENERIC_EXIT, "run_generic_accept_exit"),
            (GENERIC_EXIT, "run_generic_replace_exit"),
        ),
    )

def verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """Cycle BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    from tests.helpers.gate_delegator_governance import (
        GENERIC_EXIT,
        META,
        STRICT_SOCIAL_STACK,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=META,
        owner_attr="infer_accept_path_final_emitted_source",
        callers=(
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),
            (GENERIC_EXIT, "run_generic_accept_exit"),
        ),
    )

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
    from tests.helpers.gate_delegator_governance import (
        BOUNDARY_CONTRACT,
        GENERIC_EXIT,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=BOUNDARY_CONTRACT,
        owner_attr="assert_final_emission_mutation_allowed",
        callers=((GENERIC_EXIT, "run_generic_replace_exit"),),
    )

def verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly() -> None:
    """Cycle BJ-111: stack/exit callers use final_emission_text_formatting._normalize_text directly."""
    from tests.helpers.gate_delegator_governance import (
        GENERIC_EXIT,
        NON_STRICT_STACK,
        STRICT_SOCIAL_STACK,
        TEXT_FORMATTING,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=TEXT_FORMATTING,
        owner_attr="_normalize_text",
        callers=(
            (NON_STRICT_STACK, "run_non_strict_layer_stack"),
            (STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),
            (GENERIC_EXIT, "run_generic_accept_exit"),
            (GENERIC_EXIT, "run_generic_replace_exit"),
        ),
    )

def verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """Cycle BJ-112: strict_social_stack calls final_emission_text_formatting._normalize_text_preserve_paragraphs directly."""
    from tests.helpers.gate_delegator_governance import (
        STRICT_SOCIAL_STACK,
        TEXT_FORMATTING,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=TEXT_FORMATTING,
        owner_attr="_normalize_text_preserve_paragraphs",
        callers=((STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),),
    )

def verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """Cycle BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    from tests.helpers.gate_delegator_governance import (
        DIEGETIC_FALLBACK,
        GENERIC_EXIT,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=DIEGETIC_FALLBACK,
        owner_attr="fallback_template_metadata",
        gate_private_attr="diegetic_classified_fallback_meta",
        owner_call="diegetic_classified_fallback_meta(",
        callers=((GENERIC_EXIT, "run_generic_replace_exit"),),
    )

def verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """Cycle BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    from tests.helpers.gate_delegator_governance import (
        ANTI_RESET,
        GENERIC_EXIT,
        assert_inspect_callers_call_owner_directly,
    )

    assert_inspect_callers_call_owner_directly(
        owner_module=ANTI_RESET,
        owner_attr="anti_reset_suppresses_intro_style_fallbacks",
        callers=((GENERIC_EXIT, "run_generic_replace_exit"),),
    )

def verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """Cycle BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    from tests.helpers.gate_delegator_governance import (
        GENERIC_EXIT,
        SOCIAL_EXCHANGE,
        STRICT_SOCIAL_STACK,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
    )

    logging_required = (
        "log_final_emission_decision(",
        "log_final_emission_trace(",
    )
    logging_forbidden = (
        "feg.log_final_emission_decision",
        "feg.log_final_emission_trace",
    )
    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_accept_exit",
        *logging_required,
        forbidden=logging_forbidden,
    )
    assert_function_source_contains(
        GENERIC_EXIT,
        "run_generic_replace_exit",
        *logging_required,
        forbidden=logging_forbidden,
    )
    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        *logging_required,
        forbidden=logging_forbidden,
    )
    assert_gate_lacks("log_final_emission_decision", "log_final_emission_trace")
    assert_owner_callable(SOCIAL_EXCHANGE, "log_final_emission_decision")
    assert_owner_callable(SOCIAL_EXCHANGE, "log_final_emission_trace")

def verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """Cycle BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    from tests.helpers.gate_delegator_governance import (
        SOCIAL_EXCHANGE,
        STRICT_SOCIAL_STACK,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
    )

    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        "build_final_strict_social_response(",
        "minimal_social_emergency_fallback_line(",
        "strict_social_deterministic_fallback_family_token(",
        forbidden=(
            "feg.build_final_strict_social_response",
            "feg.minimal_social_emergency_fallback_line",
            "feg.strict_social_deterministic_fallback_family_token",
        ),
    )
    assert_gate_lacks(
        "build_final_strict_social_response",
        "minimal_social_emergency_fallback_line",
        "strict_social_deterministic_fallback_family_token",
    )
    assert_owner_callable(SOCIAL_EXCHANGE, "build_final_strict_social_response")
    assert_owner_callable(SOCIAL_EXCHANGE, "minimal_social_emergency_fallback_line")
    assert_owner_callable(SOCIAL_EXCHANGE, "strict_social_deterministic_fallback_family_token")

def verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """Cycle BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    from tests.helpers.gate_delegator_governance import (
        FALLBACK_PROVENANCE,
        STAGE_DIFF,
        STRICT_SOCIAL_STACK,
        assert_function_source_contains,
        assert_gate_lacks,
        assert_owner_callable,
    )

    assert_function_source_contains(
        STRICT_SOCIAL_STACK,
        "run_strict_social_composition_trunk",
        "record_stage_snapshot(",
        "realign_fallback_provenance_selector_to_current_text(",
        forbidden=(
            "feg.record_stage_snapshot",
            "feg.realign_fallback_provenance_selector_to_current_text",
        ),
    )
    assert_gate_lacks(
        "record_stage_snapshot",
        "realign_fallback_provenance_selector_to_current_text",
    )
    assert_owner_callable(STAGE_DIFF, "record_stage_snapshot")
    assert_owner_callable(
        FALLBACK_PROVENANCE,
        "realign_fallback_provenance_selector_to_current_text",
    )

def verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate() -> None:
    """Cycle BJ-118: should_replace_candidate_intro_fallback lives on anti_reset owner, not gate."""
    from tests.helpers.gate_delegator_governance import (
        ANTI_RESET,
        assert_gate_lacks,
        assert_owner_callable,
    )

    assert_gate_lacks("should_replace_candidate_intro_fallback")
    assert_owner_callable(ANTI_RESET, "should_replace_candidate_intro_fallback")

def verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate() -> None:
    """Cycle BJ-119: stage_diff_telemetry helpers live on stage_diff owner, not gate."""
    from tests.helpers.gate_delegator_governance import (
        STAGE_DIFF,
        assert_gate_lacks,
        assert_owner_callable,
    )

    assert_gate_lacks("diff_turn_stage", "record_stage_transition", "snapshot_turn_stage")
    assert_owner_callable(STAGE_DIFF, "diff_turn_stage")
    assert_owner_callable(STAGE_DIFF, "record_stage_transition")
    assert_owner_callable(STAGE_DIFF, "snapshot_turn_stage")

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
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=GATE_CONTEXT,
        owner_attr="initialize_gate_execution_context",
        gate_private_attr="_initialize_gate_execution_context",
        callers=((GATE, "apply_final_emission_gate"),),
        forbidden_markers=("_initialize_gate_execution_context",),
    )

def verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """Cycle BJ-74: terminal pipeline calls acceptance_quality N4 floor seam owner directly."""
    from tests.helpers.gate_delegator_governance import (
        ACCEPTANCE_QUALITY,
        TERMINAL_PIPELINE,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=ACCEPTANCE_QUALITY,
        owner_attr="apply_acceptance_quality_n4_floor_seam",
        gate_private_attr="_apply_acceptance_quality_n4_floor_seam",
        callers=((TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),),
    )

def verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """Cycle BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    from tests.helpers.gate_delegator_governance import (
        INTERACTION_CONTINUITY,
        TERMINAL_PIPELINE,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=INTERACTION_CONTINUITY,
        owner_attr="attach_interaction_continuity_validation",
        gate_private_attr="_attach_interaction_continuity_validation",
        callers=((TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),),
    )

def verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly() -> None:
    """Cycle BJ-76: terminal pipeline and non_strict_stack call IC emission-step owner directly."""
    from tests.helpers.gate_delegator_governance import (
        INTERACTION_CONTINUITY,
        NON_STRICT_STACK,
        TERMINAL_PIPELINE,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=INTERACTION_CONTINUITY,
        owner_attr="apply_interaction_continuity_emission_step",
        gate_private_attr="_apply_interaction_continuity_emission_step",
        callers=(
            (TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline"),
            (NON_STRICT_STACK, "run_non_strict_layer_stack"),
        ),
    )

def verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """Cycle BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    from tests.helpers.gate_delegator_governance import (
        SPEAKER_CONTRACT,
        STRICT_SOCIAL_STACK,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=SPEAKER_CONTRACT,
        owner_attr="enforce_emitted_speaker_with_contract",
        gate_private_attr="enforce_emitted_speaker_with_contract",
        callers=((STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),),
    )

def verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly() -> None:
    """Cycle BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    from tests.helpers.gate_delegator_governance import (
        SPEAKER_CONTRACT,
        STRICT_SOCIAL_STACK,
        assert_callers_call_owner_directly,
    )

    assert_callers_call_owner_directly(
        owner_module=SPEAKER_CONTRACT,
        owner_attr="_sync_eff_social_to_resolution",
        gate_private_attr="_sync_eff_social_to_resolution",
        callers=((STRICT_SOCIAL_STACK, "run_strict_social_composition_trunk"),),
    )

