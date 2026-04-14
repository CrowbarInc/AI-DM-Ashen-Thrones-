"""Downstream speaker-grounding coverage for social reply attribution and authority consumption."""

from __future__ import annotations

import copy

import pytest

from game.defaults import default_character, default_session
from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    set_social_target,
)
from game.leads import ensure_lead_registry, normalize_lead
from game.social import (
    apply_social_reply_speaker_grounding,
    can_actor_speak_in_current_exchange,
    is_actor_explicitly_addressed_for_social,
    is_scene_actor_present_for_social,
    record_npc_lead_discussion,
    resolve_grounded_social_speaker,
    resolve_social_action,
)
from game.social_exchange_emission import (
    build_final_strict_social_response,
    reconcile_strict_social_resolution_speaker,
)
from game.storage import get_scene_runtime, load_scene



pytestmark = pytest.mark.integration

def _assert_runner_strict_social_grounding(social: dict) -> None:
    """Player-visible reply speaker must remain Tavern Runner with grounding metadata populated."""
    assert social.get("npc_id") == "tavern_runner"
    assert social.get("npc_name") == "Tavern Runner"
    assert social.get("grounded_speaker_id") == "tavern_runner"
    assert social.get("reply_speaker_grounding_neutral_bridge") is not True
    assert social.get("authority_source_used")
    assert social.get("grounding_reason_code")
    assert social.get("proposed_reply_speaker_id") == "tavern_runner"
    assert social.get("grounding_fallback_applied") is False


# ``apply_structured_social_answer_candidate_to_resolution`` only adjusts hints / answer-candidate flags;
# it does not assign ``npc_id`` and is not called from ``game.api`` (audited: no user-reachable bypass of
# ``resolve_social_action`` / emission grounding).


@pytest.fixture
def frontier_gate_scene_bundle():
    world: dict = {
        "npcs": [
            {
                "id": "lord_aldric",
                "name": "Lord Aldric",
                "location": "castle_keep",
                "disposition": "neutral",
            },
        ]
    }
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = load_scene("frontier_gate")
    st = session["scene_state"]
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = [
        "guard_captain",
        "tavern_runner",
        "refugee",
        "threadbare_watcher",
    ]
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, world, scene


def test_mentioning_offscene_npc_does_not_make_them_reply_speaker(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    set_social_target(session, "tavern_runner")
    line = "Tavern runner, what do you think Lord Aldric would say about the patrol schedule?"
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=line,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "tavern_runner"
    assert auth.get("source") in ("continuity", "spoken_vocative", "vocative"), auth

    aldric = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "lord_aldric",
        auth,
    )
    assert aldric["allowed"] is False
    assert aldric["reason_code"] == "not_scene_present"

    runner = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "tavern_runner",
        auth,
    )
    assert runner["allowed"] is True
    assert runner["grounded_actor_id"] == "tavern_runner"


def test_topic_pressure_cannot_elevate_non_authoritative_speaker(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    # Aldric in-scene so ineligibility is authority/topic policy, not ``not_scene_present``.
    w2 = copy.deepcopy(world)
    for row in w2.get("npcs") or []:
        if isinstance(row, dict) and row.get("id") == "lord_aldric":
            row["location"] = "frontier_gate"
            break
    rebuild_active_scene_entities(session, w2, "frontier_gate", scene_envelope=scene)

    set_social_target(session, "tavern_runner")
    auth = resolve_authoritative_social_target(
        session,
        w2,
        "frontier_gate",
        player_text="And the east road?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "tavern_runner"
    assert is_scene_actor_present_for_social(session, scene, "lord_aldric", world=w2)["present"] is True

    rt = get_scene_runtime(session, "frontier_gate")
    rt["topic_pressure_current"] = {
        "topic_key": "patrol",
        "speaker_key": "lord_aldric",
        "player_text": "",
    }
    rt["topic_pressure"] = {
        "patrol": {
            "last_answer": "Lord Aldric keeps his own counsel.",
            "repeat_count": 1,
            "speaker_targets": {"lord_aldric": {"repeat_count": 1}},
        }
    }

    out = can_actor_speak_in_current_exchange(
        session,
        w2,
        "frontier_gate",
        scene,
        "lord_aldric",
        auth,
        topic_pressure_speaker_id="lord_aldric",
    )
    assert out["allowed"] is False
    assert out["reason_code"] == "topic_pressure_cannot_elevate_non_authoritative_speaker"
    assert out["fallback_actor_id"] == "tavern_runner"

    resolved = resolve_grounded_social_speaker(
        session,
        w2,
        "frontier_gate",
        scene,
        auth,
        proposed_reply_speaker_id="lord_aldric",
        topic_pressure_speaker_id="lord_aldric",
    )
    assert resolved["allowed"] is False
    assert resolved["fallback_actor_id"] == "tavern_runner"


def test_stable_explicit_address_only_counts_for_present_actor(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    auth_present = {
        "npc_id": "tavern_runner",
        "npc_name": "Tavern Runner",
        "target_resolved": True,
        "offscene_target": False,
        "source": "explicit_target",
        "reason": "test",
    }
    assert is_scene_actor_present_for_social(session, scene, "tavern_runner", world=world)["present"] is True
    addr = is_actor_explicitly_addressed_for_social(auth_present, "tavern_runner")
    assert addr["addressed"] is True
    assert addr["reason_code"] == "explicit_stable_address_source"

    absent_auth = copy.deepcopy(auth_present)
    absent_auth["npc_id"] = "not_in_scene_npc"
    absent_auth["npc_name"] = "Nobody"
    assert (
        is_scene_actor_present_for_social(session, scene, "not_in_scene_npc", world=world)["present"] is False
    )
    speak = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "not_in_scene_npc",
        absent_auth,
    )
    assert speak["allowed"] is False
    assert speak["reason_code"] == "not_scene_present"


def test_grounded_interlocutor_remains_eligible_on_followups(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    set_social_target(session, "tavern_runner")
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Why is that?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("source") == "continuity"
    out = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "tavern_runner",
        auth,
    )
    assert out["allowed"] is True
    assert out["reason_code"] == "authoritative_speaker_eligible"


def test_explicit_approach_present_actor_is_eligible_speaker(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    line = "You, runner — what did you hear?"
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=line,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "tavern_runner"
    assert auth.get("source") in (
        "explicit_target",
        "declared_action",
        "spoken_vocative",
        "vocative",
        "generic_role",
        "substring",
    )
    explicit = is_actor_explicitly_addressed_for_social(auth, "tavern_runner")
    assert explicit["addressed"] is True
    speak = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "tavern_runner",
        auth,
    )
    assert speak["allowed"] is True


def test_first_roster_authority_does_not_license_reply_speaker(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    auth = {
        "npc_id": "guard_captain",
        "npc_name": "Guard Captain",
        "target_resolved": True,
        "offscene_target": False,
        "source": "first_roster",
        "reason": "test_fixture",
    }
    out = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "guard_captain",
        auth,
    )
    assert out["allowed"] is False
    assert out["reason_code"] == "authority_source_disallowed_for_reply"


def test_reconcile_emission_keeps_tavern_runner_when_stale_resolution_named_aldric(
    frontier_gate_scene_bundle,
):
    """Live strict-social reconciliation must not leave a mentioned off-scene NPC as reply speaker."""
    session, world, scene = frontier_gate_scene_bundle
    set_social_target(session, "tavern_runner")
    res = {
        "kind": "question",
        "prompt": "Tavern runner, what do you think Lord Aldric would say about the patrol schedule?",
        "label": "social",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "lord_aldric",
            "npc_name": "Lord Aldric",
            "target_resolved": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    out = reconcile_strict_social_resolution_speaker(res, session, world, "frontier_gate")
    soc = out.get("social") or {}
    assert soc.get("npc_id") == "tavern_runner"
    assert soc.get("grounded_speaker_id") == "tavern_runner"
    assert soc.get("grounding_reason_code")
    assert soc.get("authority_source_used")
    assert soc.get("grounding_fallback_applied") is False
    assert soc.get("reply_speaker_grounding_neutral_bridge") is not True


def test_apply_reply_grounding_sets_metadata_when_eligible(frontier_gate_scene_bundle):
    session, world, scene = frontier_gate_scene_bundle
    set_social_target(session, "tavern_runner")
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Why is that?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    soc = {
        "npc_id": "tavern_runner",
        "npc_name": "Tavern Runner",
        "target_resolved": True,
        "npc_reply_expected": True,
        "reply_kind": "answer",
    }
    apply_social_reply_speaker_grounding(
        soc, session, world, "frontier_gate", scene, auth, proposed_reply_speaker_id="tavern_runner"
    )
    assert soc.get("npc_id") == "tavern_runner"
    assert soc.get("grounding_fallback_applied") is False
    assert soc.get("grounded_speaker_id") == "tavern_runner"
    assert soc.get("authority_source_used") == "continuity"


def test_retry_fallback_gm_regrounds_resolution_social(frontier_gate_scene_bundle):
    from game.social_exchange_emission import apply_social_exchange_retry_fallback_gm

    session, world, scene = frontier_gate_scene_bundle
    set_social_target(session, "tavern_runner")
    resolution = {
        "kind": "question",
        "prompt": "Runner, and the east road?",
        "label": "Runner, and the east road?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "target_resolved": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    gm = {"player_facing_text": "x", "tags": []}
    out = apply_social_exchange_retry_fallback_gm(
        gm,
        player_text="Runner, and the east road?",
        session=session,
        world=world,
        resolution=resolution,
        scene_id="frontier_gate",
    )
    assert isinstance(out, dict)
    assert resolution["social"]["npc_id"] == "tavern_runner"
    assert resolution["social"].get("grounding_reason_code")
    assert resolution["social"].get("grounded_speaker_id") == "tavern_runner"
    assert resolution["social"].get("authority_source_used")
    assert resolution["social"].get("grounding_fallback_applied") is True


def test_build_final_strict_social_emits_neutral_bridge_when_grounding_denied(frontier_gate_scene_bundle):
    _session, _world, _scene = frontier_gate_scene_bundle
    res = {
        "kind": "question",
        "prompt": "test",
        "social": {
            "social_intent_class": "social_exchange",
            "reply_speaker_grounding_neutral_bridge": True,
            "npc_reply_expected": False,
        },
    }
    text, meta = build_final_strict_social_response(
        "Some illegal scene holds stillness.",
        resolution=res,
        tags=[],
        session=None,
        scene_id="frontier_gate",
        world=None,
    )
    assert "scene holds" not in text.lower()
    assert meta.get("final_emitted_source") == "neutral_reply_speaker_grounding_bridge"
    assert meta.get("fallback_kind") == "neutral_speaker_grounding_bridge"
    assert meta.get("used_internal_fallback") is True
    assert meta.get("rejection_reasons") == []
    assert res["social"].get("reply_speaker_grounding_neutral_bridge") is True
    assert res["social"].get("npc_id") is None
    assert res["social"].get("npc_name") is None


def test_substring_authority_cannot_promote_offscene_npc_to_speaker(frontier_gate_scene_bundle):
    """If resolver ever pointed at an absent id, grounding denies and clears false attribution."""
    session, world, scene = frontier_gate_scene_bundle
    auth_bad = {
        "npc_id": "lord_aldric",
        "npc_name": "Lord Aldric",
        "target_resolved": True,
        "offscene_target": False,
        "source": "substring",
        "reason": "synthetic_fixture",
    }
    soc = {
        "npc_id": "lord_aldric",
        "npc_name": "Lord Aldric",
        "target_resolved": True,
        "npc_reply_expected": True,
        "reply_kind": "answer",
    }
    apply_social_reply_speaker_grounding(
        soc, session, world, "frontier_gate", scene, auth_bad, proposed_reply_speaker_id="lord_aldric"
    )
    assert soc.get("reply_speaker_grounding_neutral_bridge") is True
    assert soc.get("npc_id") is None
    assert soc.get("npc_name") is None
    assert soc.get("npc_reply_expected") is False
    assert soc.get("target_resolved") is False
    assert soc.get("authority_source_used") == "substring"
    assert soc.get("proposed_reply_speaker_id") == "lord_aldric"
    assert soc.get("grounding_fallback_applied") is False
    assert soc.get("grounding_reason_code")
    assert not (soc.get("grounded_speaker_id") or "")


def test_transcript_runner_asks_about_aldric_followup_stays_runner(frontier_gate_scene_bundle):
    """Smoke bug shape: Aldric is only mentioned; follow-up exchange still attributes reply to Tavern Runner."""
    session, world, env = frontier_gate_scene_bundle
    char = default_character()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")

    line1 = "Runner, what do you think Lord Aldric would say about the patrol schedule?"
    a1 = {
        "id": "question_tavern_runner",
        "type": "question",
        "label": line1,
        "prompt": line1,
        "target_id": "tavern_runner",
    }
    get_scene_runtime(session, sid)["last_player_action_text"] = line1
    r1 = resolve_social_action(env, session, world, a1, raw_player_text=line1, character=char, turn_counter=1)
    assert r1.get("success") is True
    _assert_runner_strict_social_grounding(r1.get("social") or {})

    rt = get_scene_runtime(session, sid)
    rt["topic_pressure_current"] = {
        "topic_key": "aldric_patrol",
        "speaker_key": "lord_aldric",
        "player_text": line1,
    }
    rt["topic_pressure"] = {
        "aldric_patrol": {
            "last_answer": "Lord Aldric keeps his own counsel on patrols.",
            "repeat_count": 1,
            "speaker_targets": {"lord_aldric": {"repeat_count": 1}},
        }
    }

    line2 = "Why would he care about the east road?"
    a2 = {"id": "question_followup", "type": "question", "label": line2, "prompt": line2}
    get_scene_runtime(session, sid)["last_player_action_text"] = line2
    r2 = resolve_social_action(env, session, world, a2, raw_player_text=line2, character=char, turn_counter=2)
    soc2 = r2.get("social") or {}
    _assert_runner_strict_social_grounding(soc2)
    assert soc2.get("authority_source_used") == "continuity"
    assert soc2.get("grounding_reason_code") == "authoritative_speaker_eligible_topic_salience_ignored"

    stale = {
        "kind": "question",
        "prompt": line2,
        "metadata": {"normalized_action": a2},
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "lord_aldric",
            "npc_name": "Lord Aldric",
            "target_resolved": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    out = reconcile_strict_social_resolution_speaker(stale, session, world, sid)
    socf = out.get("social") or {}
    assert socf.get("npc_id") == "tavern_runner"
    assert socf.get("grounded_speaker_id") == "tavern_runner"
    assert socf.get("authority_source_used") == "continuity"
    assert socf.get("grounding_fallback_applied") is False


def test_transcript_where_is_aldric_repeated_followups_stay_runner(frontier_gate_scene_bundle):
    """Location question about absent Aldric: interlocutor answers; pressure loops cannot drift speaker to Aldric."""
    session, world, env = frontier_gate_scene_bundle
    char = default_character()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")

    line1 = "Runner, where can I find Lord Aldric?"
    a1 = {
        "id": "q_where",
        "type": "question",
        "label": line1,
        "prompt": line1,
        "target_id": "tavern_runner",
    }
    get_scene_runtime(session, sid)["last_player_action_text"] = line1
    r1 = resolve_social_action(env, session, world, a1, raw_player_text=line1, character=char, turn_counter=1)
    assert r1.get("success") is True
    _assert_runner_strict_social_grounding(r1.get("social") or {})

    rt = get_scene_runtime(session, sid)
    rt["topic_pressure_current"] = {
        "topic_key": "aldric_whereabouts",
        "speaker_key": "lord_aldric",
        "player_text": line1,
    }
    rt["topic_pressure"] = {
        "aldric_whereabouts": {
            "last_answer": "Lord Aldric quarters at the keep when he is in town.",
            "repeat_count": 1,
            "speaker_targets": {"lord_aldric": {"repeat_count": 1}},
        }
    }

    line2 = "Is he usually at the keep at this hour?"
    a2 = {"id": "q_keep", "type": "question", "label": line2, "prompt": line2}
    get_scene_runtime(session, sid)["last_player_action_text"] = line2
    r2 = resolve_social_action(env, session, world, a2, raw_player_text=line2, character=char, turn_counter=2)
    _assert_runner_strict_social_grounding(r2.get("social") or {})

    line3 = "And the postern—would a stranger be turned away if Aldric is there?"
    a3 = {"id": "q_postern", "type": "question", "label": line3, "prompt": line3}
    get_scene_runtime(session, sid)["last_player_action_text"] = line3
    r3 = resolve_social_action(env, session, world, a3, raw_player_text=line3, character=char, turn_counter=3)
    soc3 = r3.get("social") or {}
    _assert_runner_strict_social_grounding(soc3)
    assert soc3.get("npc_id") != "lord_aldric"
    assert soc3.get("grounded_speaker_id") != "lord_aldric"


def test_transcript_continuity_and_runner_topic_pressure_do_not_bootstrap_aldric(
    frontier_gate_scene_bundle,
):
    """Continuity keeps the grounded interlocutor; engine topic salience may reinforce runner, never off-scene Aldric."""
    session, world, env = frontier_gate_scene_bundle
    char = default_character()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")

    line0 = "Runner, heard anything about the patrols?"
    a0 = {
        "id": "q_patrol",
        "type": "question",
        "label": line0,
        "prompt": line0,
        "target_id": "tavern_runner",
    }
    get_scene_runtime(session, sid)["last_player_action_text"] = line0
    r0 = resolve_social_action(env, session, world, a0, raw_player_text=line0, character=char, turn_counter=1)
    _assert_runner_strict_social_grounding(r0.get("social") or {})

    rt = get_scene_runtime(session, sid)
    rt["topic_pressure_current"] = {
        "topic_key": "patrols",
        "speaker_key": "tavern_runner",
        "player_text": line0,
    }
    rt["topic_pressure"] = {
        "patrols": {
            "last_answer": "Thin on the east road—Aldric's people watch it.",
            "repeat_count": 2,
            "speaker_targets": {"tavern_runner": {"repeat_count": 2}},
        }
    }

    line1 = "When you said Aldric's people watch the east road—does he ever come to the square himself?"
    a1 = {"id": "q_aldric_square", "type": "question", "label": line1, "prompt": line1}
    get_scene_runtime(session, sid)["last_player_action_text"] = line1
    r1 = resolve_social_action(env, session, world, a1, raw_player_text=line1, character=char, turn_counter=2)
    soc1 = r1.get("social") or {}
    _assert_runner_strict_social_grounding(soc1)
    assert soc1.get("authority_source_used") == "continuity"
    assert soc1.get("npc_id") != "lord_aldric"


def test_transcript_lead_registry_and_recent_leads_do_not_emit_aldric_as_speaker(
    frontier_gate_scene_bundle,
):
    """Aldric may be salient in lead memory; absent Aldric still cannot become the emitted reply speaker."""
    session, world, env = frontier_gate_scene_bundle
    char = default_character()
    sid = "frontier_gate"
    reg = ensure_lead_registry(session)
    reg["lead_lord_aldric"] = normalize_lead(
        {
            "id": "lead_lord_aldric",
            "title": "Lord Aldric",
            "summary": "Noble tied to patrol decisions; quarters at the keep.",
            "related_npc_ids": ["lord_aldric"],
        }
    )
    rt = get_scene_runtime(session, sid)
    rt["recent_contextual_leads"] = [
        {
            "key": "lord_aldric",
            "subject": "Lord Aldric",
            "kind": "npc",
            "position": "castle_keep",
            "named": True,
            "mentions": 4,
            "last_turn": 6,
        }
    ]
    set_social_target(session, "tavern_runner")

    line = "Runner, is Lord Aldric the one who ordered the extra patrols?"
    action = {
        "id": "q_aldric_order",
        "type": "question",
        "label": line,
        "prompt": line,
        "target_id": "tavern_runner",
    }
    get_scene_runtime(session, sid)["last_player_action_text"] = line
    r = resolve_social_action(env, session, world, action, raw_player_text=line, character=char, turn_counter=1)
    soc = r.get("social") or {}
    _assert_runner_strict_social_grounding(soc)
    assert soc.get("npc_id") != "lord_aldric"


def test_absent_lead_salience_does_not_override_grounded_speaker(frontier_gate_scene_bundle):
    """Even if an absent NPC has denser lead history, active grounded speaker remains authoritative."""
    session, world, env = frontier_gate_scene_bundle
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    session["turn_counter"] = 6

    reg = ensure_lead_registry(session)
    reg["lead_runner_thread"] = normalize_lead(
        {
            "id": "lead_runner_thread",
            "title": "Runner Thread",
            "summary": "Local watch movement near the gate.",
            "related_npc_ids": ["tavern_runner"],
        }
    )
    reg["lead_aldric_thread"] = normalize_lead(
        {
            "id": "lead_aldric_thread",
            "title": "Aldric Thread",
            "summary": "Lord Aldric influence over patrol choices.",
            "related_npc_ids": ["lord_aldric"],
        }
    )
    record_npc_lead_discussion(
        session,
        sid,
        "lord_aldric",
        "lead_aldric_thread",
        disclosure_level="explicit",
        turn_counter=3,
    )
    record_npc_lead_discussion(
        session,
        sid,
        "lord_aldric",
        "lead_aldric_thread",
        disclosure_level="explicit",
        turn_counter=4,
    )
    record_npc_lead_discussion(
        session,
        sid,
        "lord_aldric",
        "lead_aldric_thread",
        disclosure_level="explicit",
        turn_counter=5,
    )
    record_npc_lead_discussion(
        session,
        sid,
        "tavern_runner",
        "lead_runner_thread",
        disclosure_level="hinted",
        turn_counter=6,
    )

    line = "Runner, does Aldric still inspect the east road?"
    action = {
        "id": "q_runner_aldric",
        "type": "question",
        "label": line,
        "prompt": line,
        "target_id": "tavern_runner",
    }
    get_scene_runtime(session, sid)["last_player_action_text"] = line
    r = resolve_social_action(
        env,
        session,
        world,
        action,
        raw_player_text=line,
        character=default_character(),
        turn_counter=7,
    )
    soc = r.get("social") or {}
    _assert_runner_strict_social_grounding(soc)
