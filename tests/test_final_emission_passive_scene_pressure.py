"""Owner tests for passive scene pressure visibility fallback helpers.

Direct owner for ``game.final_emission_passive_scene_pressure``. Gate fallback
ordering and integration remain in ``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import game.final_emission_passive_scene_pressure as passive_scene_pressure
from game.defaults import default_session
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.storage import get_scene_runtime


def test_passive_scene_pressure_candidates_return_canonical_dataclass() -> None:
    session = default_session()
    sid = "scene_investigate"
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    rt["passive_action_streak"] = 1
    rt["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    scene = {"scene": {"id": sid, "location": "square", "visible_facts": []}}
    kwargs = {"session": session, "scene": scene, "scene_id": sid}
    selected = passive_scene_pressure._passive_scene_pressure_fallback_candidates(**kwargs)
    assert selected
    assert all(isinstance(candidate, VisibilitySelectedFallback) for candidate in selected)
    assert selected[0].final_emitted_source == "passive_scene_pressure_fallback"
    assert selected[0].fallback_pool == "passive_scene_pressure"
    assert selected[0].fallback_strategy == "passive_scene_pressure_fallback"
    assert selected[0].fallback_candidate_source == "passive_scene_pressure:lead_figure"


def test_passive_scene_pressure_due_for_fallback_requires_passive_signal() -> None:
    session = default_session()
    sid = "scene_investigate"
    scene = {"scene": {"id": sid, "visible_facts": ["A guard watches the gate."]}}

    assert not passive_scene_pressure._passive_scene_pressure_due_for_fallback(
        session=session,
        scene=scene,
        scene_id=sid,
    )

    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    assert passive_scene_pressure._passive_scene_pressure_due_for_fallback(
        session=session,
        scene=scene,
        scene_id=sid,
    )


def test_passive_scene_pressure_guard_rumor_branch_when_visible_facts_match() -> None:
    session = default_session()
    sid = "frontier_gate"
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    rt["passive_action_streak"] = 1
    scene = {
        "scene": {
            "id": sid,
            "visible_facts": [
                "A guard watches the notice board.",
                "A notice board lists a missing patrol.",
            ],
        }
    }

    selected = passive_scene_pressure._passive_scene_pressure_fallback_candidates(
        session=session,
        scene=scene,
        scene_id=sid,
    )

    assert len(selected) == 1
    assert selected[0].fallback_kind == "passive_scene_pressure_guard_rumor"
    assert selected[0].fallback_candidate_source == "passive_scene_pressure:guard_rumor"
    assert "patrol" in selected[0].text.lower()


def test_passive_scene_pressure_visibility_candidate_stamps_canonical_fields() -> None:
    candidate = passive_scene_pressure._passive_scene_pressure_visibility_candidate(
        "A guard steps forward.",
        fallback_kind="passive_scene_pressure_visible_figure",
        fallback_candidate_source="passive_scene_pressure:visible_figure",
    )

    assert candidate.text == "A guard steps forward."
    assert candidate.fallback_pool == "passive_scene_pressure"
    assert candidate.final_emitted_source == "passive_scene_pressure_fallback"
    assert candidate.composition_meta["first_mention_composition_used"] is False
