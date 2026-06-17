"""Owner tests for scene-intro / first-mention prose composition helpers.

Direct owner for ``game.final_emission_first_mention_composition``. Gate integration
and fallback-order coverage remain in ``tests/test_final_emission_gate.py`` and
``tests/test_final_emission_visibility.py``.
"""

from __future__ import annotations

import game.final_emission_first_mention_composition as first_mention_composition
from game.defaults import default_scene, default_session, default_world
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.interaction_context import rebuild_active_scene_entities


def test_grounded_scene_intro_fallback_candidates_return_canonical_dataclass() -> None:
    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = ["A brazier throws orange sparks over the checkpoint."]
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    kwargs = {
        "session": session,
        "scene": scene,
        "world": world,
        "active_interlocutor": "guard_captain",
    }
    selected = first_mention_composition._grounded_scene_intro_fallback_candidates(**kwargs)
    assert selected
    assert all(isinstance(candidate, VisibilitySelectedFallback) for candidate in selected)
    dedup_keys = {
        (
            candidate.text,
            candidate.fallback_pool,
            candidate.fallback_kind,
            candidate.final_emitted_source,
            candidate.fallback_strategy,
            candidate.fallback_candidate_source,
        )
        for candidate in selected
    }
    assert len(dedup_keys) == len(selected)
    assert any(candidate.fallback_pool == "visible_scene_composed_intro" for candidate in selected)
    assert any(candidate.final_emitted_source == "visible_fact_scene_intro" for candidate in selected)


def test_build_composed_scene_intro_populates_composition_layers() -> None:
    narration_visibility = {
        "visible_entity_ids": ["guard_captain"],
    }
    composition_facts = [
        "Rain drums on the muddy square while refugees press toward the gate.",
        "Guard Captain scans the crowd at the gate.",
    ]
    scene_context: dict = {
        "entity_rows_by_display_name": {
            "Guard Captain": {
                "entity_id": "guard_captain",
                "display_name": "Guard Captain",
                "aliases": [],
                "role_hints": ["guard"],
            }
        }
    }

    composed = first_mention_composition._build_composed_scene_intro(
        narration_visibility,
        ["Guard Captain"],
        composition_facts,
        scene_context,
    )

    assert composed
    layers = scene_context["composition_layers"]
    assert layers["environment"]
    assert layers["entities"] == ["Guard Captain"]
    assert "guard captain" in composed.lower()


def test_rewrite_visible_fact_as_explicit_intro_rewrites_article_subject() -> None:
    rewritten = first_mention_composition._rewrite_visible_fact_as_explicit_intro(
        "Guard Captain",
        "A guard captain scans the gate.",
        ["guard captain"],
    )
    assert rewritten == "Guard Captain scans the gate."
