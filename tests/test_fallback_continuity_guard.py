"""Tests for player-facing fallback continuity validation (Block #3)."""
from __future__ import annotations

from game.defaults import default_scene, default_session, default_world
from game.gm import _is_valid_player_facing_fallback_answer, classify_uncertainty
from game.gm_retry import apply_deterministic_retry_fallback

import pytest

pytestmark = pytest.mark.unit


def test_malformed_recognition_continuity_rejected():
    bad = (
        "You recognize them as stay with the guards reacting to the missing patrol rumor "
        "until it gives you one concrete turn."
    )
    assert not _is_valid_player_facing_fallback_answer(
        bad,
        player_text="Who is that?",
        known_fact={
            "source": "recent_dialogue_continuity",
            "subject": "stay with the guards reacting",
            "position": "",
        },
        failure_class="unresolved_question",
    )


def test_planner_residue_rejected():
    assert not _is_valid_player_facing_fallback_answer(
        "Stay with the rumor until you get one concrete turn from the crowd.",
        player_text="What did they say?",
        known_fact=None,
        failure_class="unresolved_question",
    )


def test_stale_continuity_rejected_when_no_overlap_with_question():
    assert not _is_valid_player_facing_fallback_answer(
        "The eastern patrol route is still unconfirmed.",
        player_text="What wares is the silk merchant selling today?",
        known_fact={
            "source": "recent_dialogue_continuity",
            "subject": "eastern patrol",
            "position": "",
        },
        failure_class="unresolved_question",
    )


def test_valid_short_continuity_accepted_for_follow_up_find():
    text = "Lady Misia is near the tavern entrance."
    assert _is_valid_player_facing_fallback_answer(
        text,
        player_text="Where do I find that person?",
        known_fact={
            "source": "recent_dialogue_continuity",
            "subject": "Lady Misia",
            "position": "near the tavern entrance",
        },
        failure_class="unresolved_question",
    )


def test_apply_deterministic_retry_fallback_skips_invalid_known_fact_context():
    scene = default_scene("scene_investigate")
    session = default_session()
    world = default_world()
    bad = (
        "You recognize them as stay with the guards until the rumor gives you one concrete turn."
    )
    gm = apply_deterministic_retry_fallback(
        {"player_facing_text": "stub", "tags": [], "debug_notes": ""},
        failure={
            "failure_class": "answer",
            "known_fact_context": {
                "answer": bad,
                "source": "structured_fact",
                "subject": "",
                "position": "",
            },
        },
        player_text="Who is that?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution={"kind": "question", "social": {}},
    )
    out = (gm.get("player_facing_text") or "").lower()
    assert bad.lower() not in out
    assert "question_retry_fallback" in (gm.get("tags") or [])


def test_classify_uncertainty_drops_invalid_known_fact_from_context():
    scene = default_scene("frontier_gate")
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    world = default_world()
    session.setdefault("scene_runtime", {}).setdefault("frontier_gate", {})
    rt = session["scene_runtime"]["frontier_gate"]
    rt["recent_contextual_leads"] = [
        {
            "key": "poison",
            "kind": "recent_named_figure",
            "subject": "stay with the guards until one concrete turn",
            "position": "by the gate",
            "named": True,
            "positioned": True,
        }
    ]
    u = classify_uncertainty(
        "Who is that?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=None,
    )
    kf = u.get("known_fact")
    assert not isinstance(kf, dict) or not str(kf.get("text") or "").strip()
    assert str(u.get("category") or "").strip() == "unknown_identity"
