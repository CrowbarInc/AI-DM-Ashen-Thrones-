"""Pure owner tests for ``game.final_emission_sealed_fallback``.

This suite owns sealed fallback helper shape, tuple/dataclass conversion,
metadata stamping, injected-provider assembly, and importability. It does not
own final-emission gate orchestration.
"""
from __future__ import annotations

import copy
import inspect
import sys
from typing import Any

import pytest

import game.final_emission_gate as feg
from game.final_emission_terminal_pipeline import apply_strict_social_emergency_fallback_patch
from game.final_emission_meta import (
    SEALED_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
)
import game.final_emission_passive_scene_pressure as passive_scene_pressure
import game.final_emission_scene_emit_integrity as scene_emit_integrity
import game.final_emission_sealed_fallback as sealed_fallback
import game.final_emission_visibility_fallback as visibility_fallback
import game.social_exchange_emission as social_exchange_emission
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.realization_provenance import (
    REALIZATION_FALLBACK_FAMILY_FIELD,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
)
from tests.helpers.opening_fallback_evidence import (
    assert_final_emission_meta_contains,
    assert_sealed_fallback_owner_bucket,
    opening_gm_output,
    opening_upstream_composition_meta_slice,
)

pytestmark = pytest.mark.unit


def test_sealed_fallback_owner_bucket_constants_match_canonical_registry() -> None:
    assert sealed_fallback.SEALED_FALLBACK_OWNER_SEALED_GATE is SEALED_FALLBACK_OWNER_SEALED_GATE
    assert sealed_fallback.SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED is SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
    assert sealed_fallback.SEALED_FALLBACK_OWNER_UNKNOWN_NONE is SEALED_FALLBACK_OWNER_UNKNOWN_NONE
    assert sealed_fallback.SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS is SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
    assert sealed_fallback.SEALED_FALLBACK_OWNER_BUCKETS == SEALED_FALLBACK_OWNER_BUCKETS
    assert SEALED_FALLBACK_OWNER_BUCKETS == frozenset(
        {
            "sealed-gate",
            "strict-social-sealed",
            "unknown-none",
            "unknown-ambiguous",
        }
    )


def test_block_ai_sealed_fallback_metadata_module_exports_helpers_only() -> None:
    for name in (
        "SealedFallbackSelection",
        "build_non_strict_sealed_fallback_providers",
        "stamp_sealed_fallback_realization_family",
        "stamp_non_strict_sealed_replacement_realization_family",
        "prepare_sealed_replacement_route_meta",
        "finalize_n4_sealed_replace_fem_route_meta",
        "select_acceptance_quality_n4_sealed_fallback_line",
        "select_non_strict_replace_path_terminal_sealed_fallback_branch",
        "select_non_strict_replace_path_terminal_sealed_fallback_selection",
        "assemble_non_strict_sealed_fallback_selection",
    ):
        assert callable(getattr(sealed_fallback, name, None)), name

    for selector_name in (
        "_select_non_strict_replace_path_terminal_sealed_fallback_selection",
        "_standard_visibility_safe_fallback",
        "_opening_scene_safe_fallback_selection",
        "minimal_social_emergency_fallback_line",
        "global_scene_fallback",
    ):
        assert not hasattr(sealed_fallback, selector_name)


def test_block_ai_sealed_fallback_selection_round_trips_legacy_tuple() -> None:
    composition_meta = opening_upstream_composition_meta_slice()
    legacy = (
        "Selected fallback text.",
        "opening_scene_safe_fallback",
        "opening_deterministic_fallback",
        "opening_deterministic_fallback",
        composition_meta,
    )

    selection = sealed_fallback.SealedFallbackSelection.from_legacy_tuple(legacy)

    assert selection.text == "Selected fallback text."
    assert selection.fallback_pool == "opening_scene_safe_fallback"
    assert selection.fallback_kind == "opening_deterministic_fallback"
    assert selection.final_emitted_source == "opening_deterministic_fallback"
    assert selection.composition_meta == composition_meta
    assert selection.as_legacy_tuple() == legacy


def test_sealed_fallback_from_visibility_selection_matches_manual_field_copy() -> None:
    selected = VisibilitySelectedFallback(
        text="Visibility fallback text.",
        fallback_pool="visibility_pool",
        fallback_kind="visibility_kind",
        final_emitted_source="visibility_source",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="visibility_candidate_source",
        composition_meta={"first_mention_composition_used": False},
    )
    sealed = sealed_fallback.SealedFallbackSelection.from_visibility_selection(selected)
    assert sealed.text == selected.text
    assert sealed.fallback_pool == selected.fallback_pool
    assert sealed.fallback_kind == selected.fallback_kind
    assert sealed.final_emitted_source == selected.final_emitted_source
    assert sealed.composition_meta == selected.composition_meta


def test_block_ai_sealed_fallback_selection_round_trips_visibility_tuple() -> None:
    legacy = (
        "Visibility fallback text.",
        "visibility_pool",
        "visibility_kind",
        "visibility_source",
        "standard_safe_fallback",
        "visibility_candidate_source",
        {"first_mention_composition_used": False},
    )
    selection = sealed_fallback.SealedFallbackSelection.from_visibility_tuple(legacy)
    assert selection.text == "Visibility fallback text."
    assert selection.fallback_pool == "visibility_pool"
    assert selection.fallback_kind == "visibility_kind"
    assert selection.final_emitted_source == "visibility_source"
    assert selection.composition_meta == {"first_mention_composition_used": False}


def test_build_non_strict_sealed_fallback_providers_social_branch_uses_owner_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gm = {"player_facing_text": "x", "tags": []}
    monkeypatch.setattr(
        social_exchange_emission,
        "minimal_social_emergency_fallback_line",
        lambda _res: "owner social line",
    )
    monkeypatch.setattr(
        social_exchange_emission,
        "_npc_display_name_for_emission",
        lambda _w, _sid, _npc: "Aldric",
    )
    providers = sealed_fallback.build_non_strict_sealed_fallback_providers(
        gm,
        session={},
        scene=None,
        world={"scenes": {"yard": {"npcs": [{"id": "npc_a", "name": "Aldric"}]}}},
        sid="yard",
        resolution=None,
        eff_resolution=None,
        active_interlocutor="npc_a",
        res_kind="question",
        response_type_required="dialogue",
        opening_sealed_fallback_provider=lambda _gm: sealed_fallback.SealedFallbackSelection(
            "opening",
            "opening_pool",
            "opening_kind",
            "opening_source",
            None,
        ),
    )
    selection = providers.social_interlocutor_provider()
    assert selection.text == "owner social line"
    assert selection.fallback_pool == "social_active_interlocutor_minimal"
    assert selection.final_emitted_source == "social_interlocutor_minimal_fallback"
    assert callable(providers.passive_candidates_provider)
    assert callable(providers.use_neutral_nonprogress_provider)
    assert callable(providers.global_provider)
    assert gm["player_facing_text"] == "x"
    assert gm["tags"] == []


def test_block_ai_non_strict_terminal_selector_does_not_mutate_gm_output_when_opening_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal selector owner entrypoint must not mutate gm_output on opening branch."""
    monkeypatch.setattr(passive_scene_pressure, "_passive_scene_pressure_fallback_candidates", lambda **_: [])
    monkeypatch.setattr(
        visibility_fallback,
        "_should_use_neutral_nonprogress_fallback_instead_of_global_stock",
        lambda *_: False,
    )
    gm = copy.deepcopy(opening_gm_output())
    snap = copy.deepcopy(gm)
    resolution = {"kind": "scene_opening", "prompt": "Start the campaign."}
    sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_selection(
        gm,
        session={},
        scene=None,
        world={},
        sid="frontier_gate",
        resolution=resolution,
        eff_resolution=None,
        active_interlocutor="",
        strict_social_suppressed_non_social_turn=False,
        res_kind="scene_opening",
        response_type_required="scene_opening",
        suppress_intro_replace=False,
        interaction_mode="",
        opening_sealed_fallback_provider=lambda _gm: sealed_fallback.SealedFallbackSelection(
            "opening text",
            "opening_scene_safe_fallback",
            "opening_deterministic_fallback",
            "opening_deterministic_fallback",
            None,
        ),
    )
    assert gm == snap


def test_bj60_generic_replace_exit_calls_sealed_fallback_selector_directly() -> None:
    """BJ-60: generic replace exit calls sealed_fallback owner; gate retains no selector wrapper."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge

    assert not hasattr(feg, "_select_non_strict_replace_path_terminal_sealed_fallback_selection")
    src = inspect.getsource(ge.run_generic_replace_exit)
    assert "select_non_strict_replace_path_terminal_sealed_fallback_selection" in src
    assert "_select_non_strict_replace_path_terminal_sealed_fallback_selection" not in src


def test_block_ai_n4_sealed_line_selector_preserves_copied_input_dicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eff: dict[str, Any] = {
        "kind": "question",
        "social": {"npc_id": "n1", "grounded_speaker_id": "n1", "social_intent_class": "social_exchange"},
    }
    session: dict[str, Any] = {"active_scene_id": "yard"}
    eff0 = copy.deepcopy(eff)
    session0 = copy.deepcopy(session)
    monkeypatch.setattr(
        social_exchange_emission,
        "minimal_social_emergency_fallback_line",
        lambda _resolution: "strict-social line",
    )
    sealed_fallback.select_acceptance_quality_n4_sealed_fallback_line(
        strict_social_path=True,
        eff_resolution=eff,
        scene=None,
        scene_id="yard",
        resolution=None,
        session=session,
        world=None,
        res_kind="question",
        response_type_required="dialogue",
    )
    assert eff == eff0
    assert session == session0


def test_block_ai_extracted_n4_selector_uses_owner_modules_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        social_exchange_emission,
        "minimal_social_emergency_fallback_line",
        lambda _resolution: calls.append("minimal") or "strict-social owner line",
    )
    monkeypatch.setattr(
        scene_emit_integrity,
        "_scene_emit_integrity_global_fallback_selection",
        lambda *_args, **_kwargs: calls.append("global")
        or VisibilitySelectedFallback(
            text="global owner line",
            fallback_pool="global_scene_narrative",
            fallback_kind="narrative_safe_fallback",
            final_emitted_source="global_scene_fallback",
            fallback_strategy="standard_safe_fallback",
            fallback_candidate_source="global_scene_fallback",
            composition_meta=None,
        ),
    )

    assert (
        sealed_fallback.select_acceptance_quality_n4_sealed_fallback_line(
            strict_social_path=True,
            eff_resolution={"kind": "question"},
            scene=None,
            scene_id="yard",
            resolution=None,
            session=None,
            world=None,
            res_kind="question",
            response_type_required="dialogue",
        )
        == "strict-social owner line"
    )
    assert calls == ["minimal"]

    calls.clear()
    assert (
        sealed_fallback.select_acceptance_quality_n4_sealed_fallback_line(
            strict_social_path=False,
            eff_resolution=None,
            scene={},
            scene_id="yard",
            resolution={},
            session={},
            world={},
            res_kind="observe",
            response_type_required="narration",
        )
        == "global owner line"
    )
    assert calls == ["global"]


def test_block_ai_assemble_non_strict_opening_branch_does_not_mutate_gm_output() -> None:
    gm = copy.deepcopy(opening_gm_output())
    snap = copy.deepcopy(gm)
    sealed_fallback.assemble_non_strict_sealed_fallback_selection(
        opening_mode_active=True,
        has_active_social_interlocutor=False,
        passive_candidates_provider=lambda: [],
        use_neutral_nonprogress_provider=lambda: False,
        suppress_intro_replace=False,
        opening_provider=lambda: sealed_fallback.SealedFallbackSelection(
            "opening text",
            "opening_pool",
            "opening_kind",
            "opening_source",
            None,
        ),
        social_interlocutor_provider=lambda: sealed_fallback.SealedFallbackSelection(
            "social",
            "social_pool",
            "social_kind",
            "social_source",
            None,
        ),
        neutral_nonprogress_provider=lambda: sealed_fallback.SealedFallbackSelection(
            "neutral",
            "neutral_pool",
            "neutral_kind",
            "neutral_source",
            None,
        ),
        anti_reset_provider=lambda: sealed_fallback.SealedFallbackSelection(
            "anti_reset",
            "anti_reset_pool",
            "anti_reset_kind",
            "anti_reset_source",
            None,
        ),
        global_provider=lambda: sealed_fallback.SealedFallbackSelection(
            "global",
            "global_pool",
            "global_kind",
            "global_source",
            None,
        ),
    )
    assert gm == snap


def test_strict_social_emergency_fallback_patch_applies_caller_provided_text_without_selecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden_minimal(*_a: Any, **_k: Any) -> str:
        raise AssertionError("patch helper must not invoke minimal_social_emergency_fallback_line")

    import game.social_exchange_emission as social_exchange_emission

    monkeypatch.setattr(social_exchange_emission, "minimal_social_emergency_fallback_line", _forbidden_minimal)
    out = {
        "player_facing_text": "Bad candidate.",
        "tags": ["existing"],
        "_final_emission_meta": {"final_route": "accept_candidate", "candidate_validation_passed": True},
    }

    apply_strict_social_emergency_fallback_patch(
        out,
        fallback_text='"Runner says, "No."',
        pre_gate_text="Bad candidate.",
        gate_tag="narrative_mode_output",
        final_route="replaced",
        candidate_validation_passed=False,
    )

    fem = out["_final_emission_meta"]
    assert out["player_facing_text"] == '"Runner says, "No."'
    assert out["tags"] == [
        "existing",
        "final_emission_gate_replaced",
        "final_emission_gate:narrative_mode_output",
    ]
    assert fem["final_route"] == "replaced"
    assert fem["candidate_validation_passed"] is False
    assert fem["final_emitted_source"] == "minimal_social_emergency_fallback"
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == STRICT_SOCIAL_DETERMINISTIC_FALLBACK
    assert fem["post_gate_mutation_detected"] is True


def test_block_ai_extracted_non_strict_branch_selector_preserves_order() -> None:
    assert (
        sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_branch(
            opening_mode_active=True,
            has_active_social_interlocutor=True,
            passive_candidate_available=True,
            use_neutral_nonprogress=True,
            suppress_intro_replace=True,
        )
        == "opening_scene_safe_fallback"
    )
    assert (
        sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_branch(
            opening_mode_active=False,
            has_active_social_interlocutor=True,
            passive_candidate_available=True,
            use_neutral_nonprogress=True,
            suppress_intro_replace=True,
        )
        == "social_active_interlocutor_minimal"
    )
    assert (
        sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_branch(
            opening_mode_active=False,
            has_active_social_interlocutor=False,
            passive_candidate_available=True,
            use_neutral_nonprogress=True,
            suppress_intro_replace=True,
        )
        == "passive_scene_pressure"
    )


def test_block_ai_non_strict_assembler_selects_each_injected_candidate_branch() -> None:
    calls: list[str] = []

    def _selection(name: str) -> sealed_fallback.SealedFallbackSelection:
        calls.append(name)
        return sealed_fallback.SealedFallbackSelection(
            text=f"{name} text",
            fallback_pool=f"{name}_pool",
            fallback_kind=f"{name}_kind",
            final_emitted_source=f"{name}_source",
            composition_meta=None,
        )

    def _assemble(**overrides: Any) -> sealed_fallback.SealedFallbackSelection:
        base: dict[str, Any] = {
            "opening_mode_active": False,
            "has_active_social_interlocutor": False,
            "passive_candidates_provider": lambda: [],
            "use_neutral_nonprogress_provider": lambda: False,
            "suppress_intro_replace": False,
            "opening_provider": lambda: _selection("opening"),
            "social_interlocutor_provider": lambda: _selection("social"),
            "neutral_nonprogress_provider": lambda: _selection("neutral"),
            "anti_reset_provider": lambda: _selection("anti_reset"),
            "global_provider": lambda: _selection("global"),
        }
        base.update(overrides)
        return sealed_fallback.assemble_non_strict_sealed_fallback_selection(**base)

    assert _assemble(opening_mode_active=True).fallback_pool == "opening_pool"
    assert calls == ["opening"]
    calls.clear()

    assert _assemble(has_active_social_interlocutor=True).fallback_pool == "social_pool"
    assert calls == ["social"]
    calls.clear()

    passive = sealed_fallback.SealedFallbackSelection("passive text", "passive_pool", "passive_kind", "passive_source")
    assert _assemble(passive_candidates_provider=lambda: [passive]).fallback_pool == "passive_pool"
    assert calls == []
    calls.clear()

    assert _assemble(use_neutral_nonprogress_provider=lambda: True).fallback_pool == "neutral_pool"
    assert calls == ["neutral"]
    calls.clear()

    assert _assemble(suppress_intro_replace=True).fallback_pool == "anti_reset_pool"
    assert calls == ["anti_reset"]
    calls.clear()

    assert _assemble().fallback_pool == "global_pool"
    assert calls == ["global"]


def test_block_ai_assembly_helpers_stamp_meta_without_selecting_fallback_lines() -> None:
    """Assembly paths set FEM route/source/stamp from caller-provided ids; they must not pick sealed line text."""
    meta: dict[str, Any] = {}
    sealed_fallback.prepare_sealed_replacement_route_meta(
        meta,
        gm_output={"player_facing_text": "Stock sealed visibility-safe line.", "tags": []},
        pre_gate_candidate_text="illegal candidate",
        final_emitted_source="global_scene_fallback",
        strict_social_route=False,
        composition_meta=None,
    )
    assert_final_emission_meta_contains(
        meta,
        final_route="replaced",
        final_emitted_source="global_scene_fallback",
    )
    assert_sealed_fallback_owner_bucket(meta, SEALED_FALLBACK_OWNER_SEALED_GATE)

    fem: dict[str, Any] = {}
    sealed_fallback.finalize_n4_sealed_replace_fem_route_meta(fem, strict_social_path=False)
    assert_final_emission_meta_contains(fem, final_emitted_source="acceptance_quality_global_scene_fallback")
    assert_sealed_fallback_owner_bucket(fem, SEALED_FALLBACK_OWNER_SEALED_GATE)

    strict_fem: dict[str, Any] = {}
    sealed_fallback.finalize_n4_sealed_replace_fem_route_meta(strict_fem, strict_social_path=True)
    assert_final_emission_meta_contains(strict_fem, final_emitted_source="minimal_social_emergency_fallback")
    assert_sealed_fallback_owner_bucket(strict_fem, SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED)

    stamp_meta: dict[str, Any] = {}
    sealed_fallback.stamp_sealed_fallback_realization_family(
        stamp_meta,
        final_emitted_source="acceptance_quality_global_scene_fallback",
        strict_social_route=False,
    )
    assert REALIZATION_FALLBACK_FAMILY_FIELD in stamp_meta

    helper_source = "\n".join(
        inspect.getsource(fn)
        for fn in (
            sealed_fallback.stamp_sealed_fallback_realization_family,
            sealed_fallback.prepare_sealed_replacement_route_meta,
            sealed_fallback.finalize_n4_sealed_replace_fem_route_meta,
            sealed_fallback.select_acceptance_quality_n4_sealed_fallback_line,
            sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_branch,
            sealed_fallback.assemble_non_strict_sealed_fallback_selection,
        )
    )
    for forbidden in (
        "_select_non_strict_replace_path_terminal_sealed_fallback_selection",
        "_standard_visibility_safe_fallback",
        "_opening_scene_safe_fallback_selection",
        "global_scene_fallback(",
        "Nothing confirms progress toward that lead",
    ):
        assert forbidden not in helper_source


def test_block_ai_sealed_fallback_helper_entrypoints_remain_importable() -> None:
    """Regression anchor: relocated Block AI sealed helper tests must stay importable."""
    mod = sys.modules[__name__]
    for name in (
        "test_block_ai_sealed_fallback_metadata_module_exports_helpers_only",
        "test_block_ai_sealed_fallback_selection_round_trips_legacy_tuple",
        "test_block_ai_sealed_fallback_selection_round_trips_visibility_tuple",
        "test_build_non_strict_sealed_fallback_providers_social_branch_uses_owner_modules",
        "test_block_ai_non_strict_terminal_selector_does_not_mutate_gm_output_when_opening_branch",
        "test_bj60_generic_replace_exit_calls_sealed_fallback_selector_directly",
        "test_block_ai_n4_sealed_line_selector_preserves_copied_input_dicts",
        "test_block_ai_assemble_non_strict_opening_branch_does_not_mutate_gm_output",
        "test_block_ai_extracted_n4_selector_uses_owner_modules_only",
        "test_block_ai_extracted_non_strict_branch_selector_preserves_order",
        "test_block_ai_non_strict_assembler_selects_each_injected_candidate_branch",
        "test_block_ai_assembly_helpers_stamp_meta_without_selecting_fallback_lines",
    ):
        assert callable(getattr(mod, name, None)), name
