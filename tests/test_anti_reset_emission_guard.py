"""Anti-reset guard: opener-style stock fallbacks must not replay during established local exchange."""
from __future__ import annotations

from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output

import pytest

import game.final_emission_gate_context as gate_context
import game.social_exchange_emission as social_exchange_emission
from game.anti_reset_emission_guard import (
    anti_reset_suppresses_intro_style_fallbacks,
    resolution_allows_scene_intro_framing,
    text_overlaps_known_scene_intro_sources,
)
from game.defaults import default_scene, default_session, default_world
from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer

pytestmark = [pytest.mark.regression]

# Opening-establishment phrases from ``default_scene('frontier_gate')`` summary / visible facts.
_FORBIDDEN_OPENING_MARKERS = (
    "rain spatters soot-dark stone",
    "you take in the scene",
    "what surrounds you resolves into focus",
)


def _social_exchange_resolution(npc_id: str = "tavern_runner") -> dict:
    return {
        "kind": "question",
        "prompt": "Test",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def test_mid_scene_strict_social_first_mention_no_scene_summary_replay():
    """A) Established exchange + gate repair must not replay opening scene paragraph / global anchor."""
    session = default_session()
    session["turn_counter"] = 4
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    world = default_world()
    scene = default_scene("frontier_gate")
    res = _social_exchange_resolution()
    assert anti_reset_suppresses_intro_style_fallbacks(session, scene, world, "frontier_gate", res) is True

    gm = {"player_facing_text": "He waits, watching the gate.", "tags": []}
    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution=res,
        session=session,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
    )
    text_norm = " ".join(str(out.get("player_facing_text") or "").lower().split())
    for frag in _FORBIDDEN_OPENING_MARKERS:
        assert frag not in text_norm


def test_non_social_replace_uses_anti_reset_not_global_anchor(monkeypatch: pytest.MonkeyPatch):
    """A/D) Forced final replacement stays exchange-local when intro suppression is active."""
    _force_non_strict = lambda *a, **k: False
    monkeypatch.setattr(social_exchange_emission, "strict_social_emission_will_apply", _force_non_strict)
    monkeypatch.setattr(gate_context, "strict_social_emission_will_apply", _force_non_strict)

    session = default_session()
    session["turn_counter"] = 4
    session["interaction_context"] = {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
    }
    world = default_world()
    scene = default_scene("frontier_gate")
    res = {
        "kind": "observe",
        "prompt": "look around",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }
    assert anti_reset_suppresses_intro_style_fallbacks(session, scene, world, "frontier_gate", res) is True

    gm = {"player_facing_text": "From here, no certain answer presents itself.", "tags": []}
    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution=res,
        session=session,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
    )
    meta = final_emission_meta_from_output(out)
    assert meta.get("final_emitted_source") == "anti_reset_local_continuation_fallback"
    assert meta.get("anti_reset_intro_suppressed") is True
    text_norm = " ".join(str(out.get("player_facing_text") or "").lower().split())
    for frag in _FORBIDDEN_OPENING_MARKERS:
        assert frag not in text_norm


def test_opening_turn_still_allows_grounded_intro_path():
    """B) Early campaign / explicit opening turn keeps intro-shaped fallbacks eligible (suppress off)."""
    session = default_session()
    session["turn_counter"] = 0
    session["visited_scene_ids"] = ["frontier_gate"]
    session["interaction_context"] = {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
    }
    world = default_world()
    scene = default_scene("frontier_gate")
    res = {
        "kind": "question",
        "prompt": "Look around",
        "state_changes": {"opening_scene_turn": True},
    }
    assert anti_reset_suppresses_intro_style_fallbacks(session, scene, world, "frontier_gate", res) is False


def test_explicit_transition_allows_scene_intro_framing():
    """C) Arrival / transition resolutions must not arm anti-reset suppression."""
    session = default_session()
    session["turn_counter"] = 5
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    res = {
        "kind": "travel",
        "resolved_transition": True,
        "state_changes": {"arrived_at_scene": True},
    }
    assert resolution_allows_scene_intro_framing(res, session) is True
    assert anti_reset_suppresses_intro_style_fallbacks(
        session, default_scene("frontier_gate"), default_world(), "frontier_gate", res
    ) is False


def test_local_fallback_line_not_scene_summary_overlap():
    """D) Continuation-safe line does not match scene opener template overlap heuristic."""
    scene = default_scene("frontier_gate")
    from game.anti_reset_emission_guard import local_exchange_continuation_fallback_line

    session = default_session()
    session["turn_counter"] = 3
    session["interaction_context"] = {
        "active_interaction_target_id": "guard_captain",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "focused",
    }
    line = local_exchange_continuation_fallback_line(
        session=session,
        world=default_world(),
        scene_id="frontier_gate",
        resolution=_social_exchange_resolution(npc_id="guard_captain"),
    )
    assert not text_overlaps_known_scene_intro_sources(line, scene)
