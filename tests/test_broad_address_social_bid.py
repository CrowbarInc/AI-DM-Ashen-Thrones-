"""Broad-address (crowd) social bids: open solicitation recovery when NPCs are addressable."""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.interaction_context import (
    canonical_scene_addressable_roster,
    detect_broad_address_social_bid,
    rank_open_social_solicitation_candidates,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    set_social_target,
)
from game.social import resolve_social_action
from game.social_exchange_emission import (
    build_open_social_solicitation_recovery,
    _open_social_recovery_passes_anti_stall,
)
from game.storage import load_scene

import pytest

pytestmark = pytest.mark.unit


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def test_detect_broad_address_positive_examples():
    session, scene, world = _gate_session_scene()
    roster = canonical_scene_addressable_roster(world, "frontier_gate", scene_envelope=scene, session=session)
    for line in (
        "Anyone up for a chat?",
        "Who here knows about the patrol?",
        "Can somebody tell me what happened?",
        "I call out for anyone willing to talk.",
        '"Anyone up for a chat?" Galinor shouts.',
    ):
        d = detect_broad_address_social_bid(
            line,
            roster=list(roster),
            session=session,
            scene_envelope=scene,
            world=world,
        )
        assert d.get("is_broad_address") is True, (line, d)
        assert d.get("phrase_matched"), d


def test_detect_broad_address_negative_named_vocative():
    session, scene, world = _gate_session_scene()
    roster = canonical_scene_addressable_roster(world, "frontier_gate", scene_envelope=scene, session=session)
    line = "Guard, what happened here?"
    d = detect_broad_address_social_bid(
        line,
        roster=list(roster),
        session=session,
        scene_envelope=scene,
        world=world,
    )
    assert d.get("is_broad_address") is False, d


def test_detect_broad_address_negative_observational():
    session, scene, world = _gate_session_scene()
    roster = canonical_scene_addressable_roster(world, "frontier_gate", scene_envelope=scene, session=session)
    line = "What do I see?"
    d = detect_broad_address_social_bid(
        line,
        roster=list(roster),
        session=session,
        scene_envelope=scene,
        world=world,
    )
    assert d.get("is_broad_address") is False, d


def test_resolve_directed_social_open_solicitation_with_npcs():
    session, scene, world = _gate_session_scene()
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text='Anyone up for a chat?" Galinor shouts.',
    )
    assert ent.get("should_route_social") is True
    assert ent.get("reason") == "open_social_solicitation"
    assert ent.get("target_actor_id") in (None, "")
    assert ent.get("target_source") == "scene_open_bid"
    assert ent.get("open_social_solicitation") is True
    assert ent.get("broad_address_bid") is True
    ids = ent.get("candidate_addressable_ids")
    assert isinstance(ids, list) and len(ids) >= 2
    assert ent.get("candidate_addressable_count") == len(ids)


def test_broad_bid_skips_active_interlocutor_steal():
    session, scene, world = _gate_session_scene()
    set_social_target(session, "guard_captain")
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="Does anyone know where the patrol went?",
    )
    assert ent.get("reason") == "open_social_solicitation"
    assert ent.get("target_actor_id") is None


def test_open_solicitation_without_addressables_still_fails():
    session = create_fresh_session_document()
    session["active_scene_id"] = "empty_road"
    session["scene_state"]["active_scene_id"] = "empty_road"
    session["scene_state"]["active_entities"] = []
    world = {"npcs": []}
    scene = {"scene": {"id": "empty_road"}, "scene_state": dict(session["scene_state"])}
    ent = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="Can anyone hear me?",
    )
    assert ent.get("should_route_social") is False
    assert ent.get("reason") == "no_addressable_target"


def test_rank_candidates_orders_interlocutor_first():
    session, scene, world = _gate_session_scene()
    set_social_target(session, "tavern_runner")
    ranked = rank_open_social_solicitation_candidates(
        session, world, "frontier_gate", scene_envelope=scene
    )
    assert ranked[0] == "tavern_runner"
    assert len(ranked) >= 2


def test_resolve_social_action_open_solicitation_payload():
    session, scene, world = _gate_session_scene()
    action = {
        "id": "open-bid",
        "type": "question",
        "label": "Anyone?",
        "prompt": "Anyone up for a chat?",
        "metadata": {
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["guard_captain", "tavern_runner"],
            "candidate_addressable_count": 2,
            "broad_address_reason": "broad_lexical_and_framing_ok",
            "broad_address_phrase_matched": "anyone",
        },
    }
    res = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text=action["prompt"],
        character=None,
        turn_counter=1,
    )
    soc = res.get("social") or {}
    assert soc.get("open_social_solicitation") is True
    assert soc.get("social_intent_class") == "open_call"
    assert soc.get("broad_address_bid") is True
    assert soc.get("target_resolved") is False
    assert soc.get("target_source") == "scene_open_bid"
    assert soc.get("target_reason") == "broad_address_to_available_scene_npcs"
    assert soc.get("npc_reply_expected") is False
    assert soc.get("reply_kind") == "reaction"
    assert isinstance(soc.get("candidate_addressable_ids"), list)
    assert soc.get("candidate_addressable_count") == 2


def test_build_open_social_solicitation_recovery_concrete_responder_top_ranked(monkeypatch):
    import game.social_exchange_emission as see

    monkeypatch.setattr(see, "resolve_grounded_social_speaker", lambda *a, **k: {"allowed": True})

    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "Anyone know about the patrol?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    rec = build_open_social_solicitation_recovery(
        resolution=resolution,
        session=session,
        world=world,
        scene_id="frontier_gate",
        scene_envelope=scene,
        player_text="Anyone know about the patrol?",
    )
    assert rec.get("used") is True
    assert rec.get("mode") == "concrete_responder"
    assert rec.get("candidate_id") == "tavern_runner"
    assert rec.get("reason") == "concrete_responder"
    text_raw = str(rec.get("text") or "")
    low = text_raw.lower()
    assert "tavern runner" in low
    assert '"' in text_raw
    assert "the moment passes" not in low
    assert "no one answers" not in low or len(low) > 40
    banned = ("secretly", "unknown to you", "hidden agenda", "plotting in secret")
    assert not any(b in low for b in banned)


def test_build_open_social_solicitation_recovery_concrete_lead_when_grounding_blocks_speakers(monkeypatch):
    session, scene, world = _gate_session_scene()
    import game.social_exchange_emission as see

    monkeypatch.setattr(see, "resolve_grounded_social_speaker", lambda *a, **k: {"allowed": False})

    resolution = {
        "kind": "question",
        "prompt": "Anyone up for a chat?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    rec = build_open_social_solicitation_recovery(
        resolution=resolution,
        session=session,
        world=world,
        scene_id="frontier_gate",
        scene_envelope=scene,
        player_text='Anyone up for a chat?" Galinor shouts.',
    )
    assert rec.get("used") is True
    assert rec.get("mode") == "concrete_lead"
    assert rec.get("candidate_id") is None
    assert rec.get("reason") == "concrete_lead_after_speaker_blocked"
    text = str(rec.get("text") or "")
    low = text.lower()
    assert "tavern runner" in low
    pure_stall = low.strip() in {
        "no one answers.",
        "nobody answers.",
        "the moment passes.",
        "nobody steps forward.",
        "no one steps forward.",
    }
    assert not pure_stall


def test_open_social_recovery_anti_stall_guard_directly():
    assert _open_social_recovery_passes_anti_stall("No one answers.", "the tavern runner") is False
    assert _open_social_recovery_passes_anti_stall("The moment passes.", "") is False
    assert _open_social_recovery_passes_anti_stall(
        "The tavern runner lifts a hand. Nobody steps forward.",
        "the tavern runner",
    ) is False
    ok_line = (
        'The tavern runner lifts a hand through the rain. "Depends what you\'re buying—stew, rumor, or both?"'
    )
    assert _open_social_recovery_passes_anti_stall(ok_line, "the tavern runner") is True


def test_build_open_social_solicitation_recovery_rejects_anti_stall_templates(monkeypatch):
    session, scene, world = _gate_session_scene()
    import game.social_exchange_emission as see

    monkeypatch.setattr(see, "resolve_grounded_social_speaker", lambda *a, **k: {"allowed": True})
    monkeypatch.setattr(see, "_open_social_responder_templates", lambda _nid: ("No one answers.",))

    resolution = {
        "kind": "question",
        "prompt": "Anyone?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner"],
            "candidate_addressable_count": 1,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    rec = build_open_social_solicitation_recovery(
        resolution=resolution,
        session=session,
        world=world,
        scene_id="frontier_gate",
        scene_envelope=scene,
        player_text="Anyone?",
    )
    assert rec.get("used") is False
    assert rec.get("reason") == "anti_stall_or_missing_anchor"


def test_apply_deterministic_retry_open_social_suppresses_uncertainty_pool(monkeypatch):
    from game.gm import apply_deterministic_retry_fallback

    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: None,
    )

    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "Anyone here know about the patrol?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    gm = {"player_facing_text": "vague", "tags": []}
    out = apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="Anyone here know about the patrol?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "open_social_recovery" in tags
    low = out.get("player_facing_text", "").lower()
    assert "nothing in the scene points" not in low
    assert "answer has not formed yet" not in low
    assert "suppressed:uncertainty_pool" in str(out.get("debug_notes") or "").lower()
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is True
    assert em.get("open_social_recovery_mode") in ("concrete_responder", "concrete_lead")
    assert isinstance(em.get("open_social_recovery_reason"), str) and em.get("open_social_recovery_reason")
    assert em.get("open_social_recovery_suppressed_retry_fallback") is True


def test_apply_deterministic_retry_known_fact_wins_before_open_social_recovery(monkeypatch):
    from game.gm import apply_deterministic_retry_fallback

    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: {"text": "Posted notice: patrol east.", "source": "notice_board"},
    )

    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "What does the notice say?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="What does the notice say?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "known_fact_guard" in tags
    assert "open_social_recovery" not in tags
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is not True


def test_apply_deterministic_retry_without_open_social_leaves_recovery_metadata_unset(monkeypatch):
    from game.gm import apply_deterministic_retry_fallback

    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: None,
    )

    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "Where did they go?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
            "npc_reply_expected": True,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="Where did they go?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is not True


def test_anyone_chat_open_solicitation_retry_fallback_not_dead_air(monkeypatch):
    """Regression: broad-address shout should not settle on generic dead-air via uncertainty pool."""
    from game.gm import apply_deterministic_retry_fallback

    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: None,
    )

    session, scene, world = _gate_session_scene()
    player_line = '"Anyone up for a chat?" Galinor shouts.'
    resolution = {
        "kind": "question",
        "prompt": "Anyone up for a chat?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["guard_captain", "tavern_runner"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
            "broad_address_bid": True,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "No one answers.", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text=player_line,
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    low = str(out.get("player_facing_text") or "").lower()
    assert "open_social_recovery" in [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert low.strip() not in {"no one answers.", "nobody answers.", "the moment passes.", "nobody steps forward."}
    assert "guard captain" in low or "tavern runner" in low
    assert "pin down who they meet" not in low
