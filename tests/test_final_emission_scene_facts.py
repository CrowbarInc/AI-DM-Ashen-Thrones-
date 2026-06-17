"""Owner tests for runtime scene visible-fact helpers.

Direct owner for ``game.final_emission_scene_facts``. Gate validation ordering
and integration remain in ``tests/test_final_emission_visibility.py`` and
``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import game.final_emission_scene_facts as scene_facts
from game.defaults import default_session
from game.storage import get_scene_runtime


def test_scene_visible_facts_normalizes_and_dedupes() -> None:
    scene = {
        "scene": {
            "visible_facts": [
                "A guard watches the gate",
                "A guard watches the gate.",
                "  ",
                42,
            ],
        }
    }

    facts = scene_facts._scene_visible_facts(scene)

    assert facts == ["A guard watches the gate."]


def test_augment_scene_with_runtime_visible_leads_appends_lead_facts() -> None:
    session = default_session()
    sid = "scene_investigate"
    session["turn_counter"] = 3
    rt = get_scene_runtime(session, sid)
    rt["recent_contextual_leads"] = [
        {
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
        }
    ]
    scene = {"scene": {"id": sid, "visible_facts": ["Rain drums on the stones."]}}

    augmented = scene_facts._augment_scene_with_runtime_visible_leads(
        scene,
        session=session,
        scene_id=sid,
    )

    assert augmented is not None
    assert augmented is not scene
    facts = scene_facts._scene_visible_facts(augmented)
    assert facts[0] == "Rain drums on the stones."
    assert facts[-1] == "the tattered man lingers by the shuttered well."


def test_augment_scene_with_runtime_visible_leads_skips_opening_preference() -> None:
    session = default_session()
    sid = "frontier_gate"
    session["turn_counter"] = 0
    session["visited_scene_ids"] = [sid]
    rt = get_scene_runtime(session, sid)
    rt["recent_contextual_leads"] = [
        {
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
        }
    ]
    scene = {"scene": {"id": sid, "visible_facts": ["A brazier throws sparks."]}}

    augmented = scene_facts._augment_scene_with_runtime_visible_leads(
        scene,
        session=session,
        scene_id=sid,
    )

    assert augmented is scene


def test_augment_scene_with_runtime_visible_leads_returns_original_without_leads() -> None:
    session = default_session()
    session["turn_counter"] = 4
    scene = {"scene": {"id": "yard", "visible_facts": ["Fog rolls in."]}}

    augmented = scene_facts._augment_scene_with_runtime_visible_leads(
        scene,
        session=session,
        scene_id="yard",
    )

    assert augmented is scene
