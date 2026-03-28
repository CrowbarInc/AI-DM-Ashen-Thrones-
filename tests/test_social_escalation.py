"""Tests for refusal/evasion escalation ladder (topic pressure + social engine)."""
from game.gm import register_topic_probe
from game.social import (
    apply_social_topic_escalation_to_resolution,
    classify_social_followup_dimension,
    determine_social_escalation_outcome,
    is_valid_followup_question,
    npc_social_knowledge_exhausted,
    sync_strategy_forced_to_answer_for_valid_followup_alignment,
)


def _session_with_pressure(scene_id: str, topic_key: str, speaker_key: str, repeat_count: int) -> dict:
    session: dict = {"turn_counter": 1}
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, scene_id)
    rt["topic_pressure_current"] = {
        "topic_key": topic_key,
        "speaker_key": speaker_key,
        "turn": 1,
        "player_text": "Who ordered it?",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Runner",
    }
    rt["topic_pressure"] = {
        topic_key: {
            "repeat_count": repeat_count,
            "low_progress_streak": 0,
            "progress_score_total": 0.0,
            "last_answer": "",
            "last_turn": 1,
            "speaker_targets": {
                speaker_key: {
                    "repeat_count": repeat_count,
                    "low_progress_streak": 0,
                    "patience": 3,
                    "last_turn": 1,
                }
            },
        }
    }
    return session


def test_escalation_second_press_partial_not_exhausted():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 2)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": False},
    )
    assert out["escalation_level"] == 2
    assert out["force_partial_answer"] is True
    assert out["force_actionable_lead"] is False
    assert out["add_suspicion"] is False
    assert out["effective_reply_kind"] == "answer"


def test_escalation_second_press_exhausted_redirect_not_partial():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 2)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
    )
    assert out["force_partial_answer"] is False
    assert out["force_actionable_lead"] is True
    assert out["topic_exhausted"] is True
    assert "redirect" in out["escalation_effect"]


def test_escalation_third_press_actionable_and_conditioned_refusal():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 3)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": False},
    )
    assert out["escalation_level"] == 3
    assert out["force_actionable_lead"] is True
    assert out["convert_refusal_to_conditioned_offer"] is True
    assert out["force_partial_answer"] is True


def test_escalation_fourth_press_suspicion_and_momentum():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 4)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": False},
    )
    assert out["add_suspicion"] is True
    assert out["trigger_scene_momentum"] is True
    assert out["force_actionable_lead"] is True


def test_npc_social_knowledge_exhausted_empty_topics():
    world = {
        "npcs": [
            {"id": "runner", "name": "Runner", "location": "s1", "topics": []},
        ]
    }
    session: dict = {}
    assert npc_social_knowledge_exhausted(world, session, "runner") is True


def test_npc_social_knowledge_exhausted_unrevealed_topic():
    world = {
        "npcs": [
            {
                "id": "runner",
                "name": "Runner",
                "location": "s1",
                "topics": [{"id": "t1", "text": "A lead."}],
            },
        ]
    }
    session: dict = {}
    assert npc_social_knowledge_exhausted(world, session, "runner") is False


def test_escalation_uses_aggregate_repeat_when_speaker_target_missing():
    """If per-speaker repeat_count desyncs, fall back to aggregate topic repeat_count."""
    session: dict = {"turn_counter": 1}
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    rt["topic_pressure_current"] = {
        "topic_key": "crossroads_incident",
        "speaker_key": "runner",
        "turn": 1,
        "player_text": "Who ordered it?",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Runner",
    }
    rt["topic_pressure"] = {
        "crossroads_incident": {
            "repeat_count": 3,
            "low_progress_streak": 0,
            "progress_score_total": 0.0,
            "last_answer": "",
            "last_turn": 1,
            "speaker_targets": {},
        }
    }
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": False},
    )
    assert out["escalation_level"] == 3
    assert out["force_actionable_lead"] is True


def test_apply_escalation_merges_debug_metadata_after_register():
    scene = {"scene": {"id": "scene_investigate", "location": "Yard"}}
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Runner",
            "reply_kind": "refusal",
            "target_resolved": True,
        },
    }
    world = {
        "npcs": [
            {"id": "runner", "name": "Runner", "location": "scene_investigate", "topics": []},
        ]
    }
    session: dict = {"turn_counter": 9, "interaction_context": {"active_interaction_target_id": "runner"}}
    same_question = "Who really ordered the crossroads hit, exactly?"
    register_topic_probe(
        session=session,
        scene_envelope=scene,
        player_text=same_question,
        resolution=resolution,
    )
    register_topic_probe(
        session=session,
        scene_envelope=scene,
        player_text=same_question,
        resolution=resolution,
    )
    apply_social_topic_escalation_to_resolution(
        world=world,
        session=session,
        scene=scene,
        user_text=same_question,
        resolution=resolution,
    )
    esc = (resolution.get("social") or {}).get("social_escalation") or {}
    assert int(esc.get("escalation_level") or 0) >= 2
    assert esc.get("escalation_reason")
    assert esc.get("escalation_effect")
    assert (resolution.get("social") or {}).get("reply_kind") == "answer"


def test_excessive_grinding_triggers_suspicion_flag():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 5)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
    )
    assert out["add_suspicion"] is True
    assert out["trigger_scene_momentum"] is True
    assert "friction" in out["escalation_effect"] or "exhausted" in out["escalation_effect"]


def test_register_probe_then_escalation_integration():
    scene = {"scene": {"id": "scene_investigate", "location": "Yard"}}
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Runner",
            "reply_kind": "refusal",
        },
    }
    session: dict = {"turn_counter": 5, "interaction_context": {"active_interaction_target_id": "runner"}}
    for _ in range(3):
        register_topic_probe(
            session=session,
            scene_envelope=scene,
            player_text="Who really ordered the crossroads hit?",
            resolution=resolution,
        )
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key=None,
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
    )
    assert out["escalation_level"] == 3
    assert out["force_actionable_lead"] is True
    assert out["topic_exhausted"] is True


def test_valid_followup_sets_strategy_flag():
    soc = {
        "social_intent_class": "social_exchange",
        "reply_kind": "explanation",
        "npc_reply_expected": True,
        "target_resolved": True,
        "actor_addressable": True,
        "valid_followup_detected": True,
        "topic_exhausted_for_dimension": False,
    }
    sync_strategy_forced_to_answer_for_valid_followup_alignment(soc)
    assert soc.get("strategy_forced_to_answer") is True
    assert soc.get("forced_answer_reason") == "valid_followup_alignment"


def test_regression_runner_followup_sets_strategy_forced_to_answer():
    """Runner follow-up: explanation reply_kind + valid follow-up must set strategy_forced_to_answer."""
    session = _session_with_pressure("scene_investigate", "tavern_rumors", "runner", 2)
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    entry = rt["topic_pressure"]["tavern_rumors"]
    entry["last_answer"] = (
        "Word is, the Mossy Mire draws odd company. Not everyone there is friendly—watch your coin and your back."
    )
    entry["previous_probe_dimension"] = "general"
    entry["last_probe_dimension"] = "danger"
    q = "Dangerous? Why is that?"
    rt["topic_pressure_current"]["player_text"] = q
    scene = {"scene": {"id": "scene_investigate", "location": "Yard"}}
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Runner",
            "reply_kind": "explanation",
            "target_resolved": True,
            "npc_reply_expected": True,
            "actor_addressable": True,
        },
    }
    world = {
        "npcs": [
            {"id": "runner", "name": "Runner", "location": "scene_investigate", "topics": []},
        ]
    }
    apply_social_topic_escalation_to_resolution(
        world=world,
        session=session,
        scene=scene,
        user_text=q,
        resolution=resolution,
    )
    soc = resolution.get("social") or {}
    assert soc.get("reply_kind") == "explanation"
    assert soc.get("valid_followup_detected") is True
    assert soc.get("strategy_forced_to_answer") is True
    assert soc.get("forced_answer_reason") == "valid_followup_alignment"


def test_dangerous_why_is_that_not_topic_exhausted_on_second_probe():
    """Legitimate follow-up with a new axis vs prior probe must not mark topic_exhausted."""
    session = _session_with_pressure("scene_investigate", "tavern_rumors", "runner", 2)
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    entry = rt["topic_pressure"]["tavern_rumors"]
    entry["last_answer"] = (
        "Word is, the Mossy Mire draws odd company. Not everyone there is friendly—watch your coin and your back."
    )
    entry["previous_probe_dimension"] = "general"
    entry["last_probe_dimension"] = "danger"
    rt["topic_pressure_current"]["player_text"] = "Dangerous? Why is that?"
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key="tavern_rumors",
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
        player_text="Dangerous? Why is that?",
    )
    assert out["escalation_reason"] == "second_attempt_same_topic"
    assert out["topic_exhausted"] is False
    assert classify_social_followup_dimension("Dangerous? Why is that?") == "danger"


def test_steer_clear_for_sure_not_exhausted_on_second_probe():
    session = _session_with_pressure("scene_investigate", "tavern_rumors", "runner", 2)
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    entry = rt["topic_pressure"]["tavern_rumors"]
    entry["last_answer"] = "Try the Mossy Mire down the lane; stew and rumors for coin."
    rt["topic_pressure_current"]["player_text"] = 'Anyone I should steer clear of for sure?'
    q = 'Anyone I should steer clear of for sure?'
    assert is_valid_followup_question(q) is True
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key="tavern_rumors",
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
        player_text=q,
    )
    assert out["valid_followup_detected"] is True
    assert out["topic_exhausted"] is False
    assert classify_social_followup_dimension(q) == "avoidance"


def test_same_topic_new_dimension_not_exhausted_when_engine_topics_gone():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 2)
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    entry = rt["topic_pressure"]["crossroads_incident"]
    entry["last_answer"] = "Marla the broker was seen near the east gate before the incident."
    entry["previous_probe_dimension"] = "identity"
    entry["last_probe_dimension"] = "location"
    rt["topic_pressure_current"]["player_text"] = "Where exactly?"
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key="crossroads_incident",
        reply_kind="answer",
        progress_signals={"npc_knowledge_exhausted": True},
        player_text="Where exactly?",
    )
    assert out["topic_exhausted"] is False
    assert out["social_question_dimension"] == "location"


def test_repeated_same_dimension_after_answer_can_mark_exhausted():
    session = _session_with_pressure("scene_investigate", "crossroads_incident", "runner", 3)
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, "scene_investigate")
    entry = rt["topic_pressure"]["crossroads_incident"]
    entry["last_answer"] = "Word is, they call her Marla; she brokers for Verevin interests at the crossroads."
    entry["previous_probe_dimension"] = "identity"
    entry["last_probe_dimension"] = "identity"
    rt["topic_pressure_current"]["player_text"] = "Who is Marla really working for?"
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_investigate",
        npc_id="runner",
        topic_key="crossroads_incident",
        reply_kind="refusal",
        progress_signals={"npc_knowledge_exhausted": True},
        player_text="Who is Marla really working for?",
    )
    assert out["prior_same_dimension_answer_exists"] is True
    assert out["topic_exhausted"] is True
