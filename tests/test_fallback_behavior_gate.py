"""Downstream gate application coverage for shipped fallback-behavior contracts.

Direct ``game.final_emission_repairs`` helper semantics live in
``tests/test_final_emission_repairs.py``. This file keeps gate ordering, application,
and emitted-metadata behavior focused on downstream orchestration.

This file owns downstream orchestration coverage for ``fallback_behavior`` through
``apply_final_emission_gate()``:

- gate ordering
- layer invocation
- final-emission metadata/debug propagation
- historically important end-to-end fallback_behavior paths

It does not own validator predicate semantics, detailed repair semantics, or the
full adversarial fallback_behavior predicate matrix. Those are owned by
``tests/test_fallback_behavior_validator.py`` and
``tests/test_final_emission_repairs.py``.
"""
from __future__ import annotations

import game.interaction_continuity as interaction_continuity
import game.final_emission_repairs as emission_repairs
import pytest

import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_strict_social_stack as strict_social_stack
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime
from tests.helpers.fallback_behavior_fixtures import (
    assert_fallback_gate_propagation,
    assert_fallback_gate_repair_evidence,
    fallback_contract,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.response_type_smoke import response_type_contract


pytestmark = pytest.mark.unit
_FORBIDDEN_META_BITS = (
    "unclear",
    "not settled",
    "move plays out",
    "move resolves",
    "unresolved",
    "insufficient",
    "information",
    "system",
)


def _strict_social_bundle() -> tuple[dict, dict, str, dict]:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": sid,
            "topics": [{"id": "lanes", "text": "East lanes.", "clue_id": "east_lanes"}],
        }
    ]
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    set_social_target(session, "runner")
    rebuild_active_scene_entities(session, world, sid)
    interaction_context = dict(session.get("interaction_context") or {})
    interaction_context["engagement_level"] = "engaged"
    session["interaction_context"] = interaction_context
    runtime = get_scene_runtime(session, sid)
    runtime["last_player_action_text"] = "No. Exactly who?"
    resolution = {
        "kind": "question",
        "prompt": "No. Exactly who?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
        },
    }
    return session, world, sid, resolution


def _assert_no_meta_bits(text: str) -> None:
    low = text.lower()
    for bit in _FORBIDDEN_META_BITS:
        assert bit not in low


def test_gate_repairs_meta_fallback_voice_into_bounded_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            "tags": [],
            "response_policy": {"fallback_behavior": fallback_contract()},
        },
        resolution={"kind": "adjudication_query", "prompt": "Who did it?"},
        session=None,
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    # Gate ownership: the layer ran, produced player-facing text, and propagated FEM/debug.
    # Detailed repair-mode semantics live in tests/test_final_emission_repairs.py.
    assert_fallback_gate_repair_evidence(
        out,
        forbidden_phrases=("don't have enough information",),
        required_phrases=("ward clerk",),
    )
    assert_fallback_gate_propagation(
        out,
        repaired=True,
        validation_checked=True,
        repair_mode_matches_fem=True,
    )


def test_gate_skips_fallback_behavior_when_uncertainty_inactive() -> None:
    raw = "Rain tracks down the gatehouse stone."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "response_policy": {"fallback_behavior": fallback_contract(uncertainty_active=False)},
        },
        resolution={"kind": "observe", "prompt": "I look at the gatehouse."},
        session=None,
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    # Gate ownership: inactive contracts bypass the layer without changing output and
    # still expose skip state. Exact predicate semantics live in the validator suite.
    assert out.get("player_facing_text") == raw
    assert_fallback_gate_propagation(
        out,
        checked=False,
        repaired=False,
        uncertainty_active=False,
        validation_checked=False,
    )


def test_gate_runs_fallback_behavior_after_interaction_continuity_non_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    orig_ic = non_strict_stack.apply_interaction_continuity_emission_step
    orig_fb = non_strict_stack._apply_fallback_behavior_layer

    def wrap_ic(*args, **kwargs):
        order.append("interaction_continuity")
        return orig_ic(*args, **kwargs)

    def wrap_fb(*args, **kwargs):
        order.append("fallback_behavior")
        return orig_fb(*args, **kwargs)

    monkeypatch.setattr(non_strict_stack, "apply_interaction_continuity_emission_step", wrap_ic)
    monkeypatch.setattr(non_strict_stack, "_apply_fallback_behavior_layer", wrap_fb)

    apply_final_emission_gate(
        {
            "player_facing_text": "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            "tags": [],
            "response_policy": {"fallback_behavior": fallback_contract()},
        },
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    # Gate-order owner lock: continuity must run before fallback_behavior in non-strict stack.
    assert order.index("interaction_continuity") < order.index("fallback_behavior")


def test_gate_runs_fallback_behavior_after_strict_social_continuity(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, sid, resolution = _strict_social_bundle()
    order: list[str] = []
    orig_ic = interaction_continuity.apply_interaction_continuity_emission_step
    orig_fb = emission_repairs._apply_fallback_behavior_layer

    def wrap_ic(*args, **kwargs):
        order.append("interaction_continuity")
        return orig_ic(*args, **kwargs)

    def wrap_fb(*args, **kwargs):
        order.append("fallback_behavior")
        return orig_fb(*args, **kwargs)

    monkeypatch.setattr(interaction_continuity, "apply_interaction_continuity_emission_step", wrap_ic)
    monkeypatch.setattr(emission_repairs, "_apply_fallback_behavior_layer", wrap_fb)

    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(candidate_text: str, *, resolution: dict, tags: list[str], session: dict, scene_id: str, world: dict):
        _ = candidate_text, resolution, tags, session, scene_id, world
        return (
            "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            dict(stub_details),
        )

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": "No names yet.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": fallback_contract(),
                "response_type_contract": response_type_contract("dialogue"),
            },
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert order.index("interaction_continuity") < order.index("fallback_behavior")
    assert_fallback_gate_repair_evidence(out, forbidden_phrases=("enough information",))
    assert_fallback_gate_propagation(out, checked=True)


def test_gate_repairs_adversarial_uncertainty_followups_without_fabricating_certainty() -> None:
    source = "unknown_quantity"
    prompt = "How many were there?"
    raw = "There were exactly 5 guards at the gate. Ask the watch captain for the tally sheet."
    forbidden = "exactly 5"
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "response_policy": {
                "response_type_contract": response_type_contract("answer"),
                "fallback_behavior": fallback_contract(uncertainty_sources=[source]),
            },
        },
        resolution={"kind": "adjudication_query", "prompt": prompt},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    # Gate ownership keeps one representative end-to-end sanity check. The full
    # adversarial predicate matrix belongs to validator/repair owner tests.
    assert_fallback_gate_repair_evidence(
        out,
        forbidden_phrases=(forbidden,),
        require_non_empty=True,
    )
    assert_fallback_gate_propagation(out, repaired=True)


def test_gate_rewrites_runner_copper_meta_leak_into_diegetic_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The reason is still unclear.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": fallback_contract(
                    uncertainty_sources=["unknown_motive"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=False,
                )
            },
        },
        resolution={
            "kind": "question",
            "prompt": "I offer the tavern runner a copper for the story.",
            "social": {
                "npc_id": "runner",
                "npc_name": "The Tavern Runner",
                "social_intent_class": "social_exchange",
            },
        },
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    assert "tavern runner" in low
    assert "grimaces" in low or "not something i can say" in low
    _assert_no_meta_bits(text)


def test_gate_rewrites_open_call_move_plays_out_meta_leak_into_diegetic_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "That is not settled until the move plays out.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": fallback_contract(
                    uncertainty_sources=["unknown_feasibility"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=False,
                )
            },
        },
        resolution={
            "kind": "question",
            "prompt": "Anyone willing to talk if I toss a copper into the crowd?",
            "social": {
                "social_intent_class": "open_call",
            },
        },
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()

    assert "move plays out" not in low
    assert "moment passes" in low or "stepping forward" in low
    _assert_no_meta_bits(text)


def test_finalize_emission_output_preserves_duplicate_subject_without_micro_smooth() -> None:
    """Packaging finalize must not merge consecutive short sentences for cadence (removed helper)."""
    from game.final_emission_finalize import finalize_emission_output

    pre = "Tavern Runner nods once. Tavern Runner does not answer at once."
    out: dict = {"player_facing_text": pre, "tags": []}
    finalize_emission_output(out, pre_gate_text=pre)
    text = str(out.get("player_facing_text") or "")
    meta = final_emission_meta_from_output(out) or {}
    assert text.count("Tavern Runner") == 2
    assert meta.get("sentence_micro_smoothing_applied") is False
    assert meta.get("final_emission_boundary_semantic_repair_disabled") is True
