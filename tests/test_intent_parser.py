"""Tests for the freeform intent parser (parse_freeform_to_action, parse_intent)."""
import pytest

from game.intent_parser import parse_freeform_to_action, parse_intent, segment_mixed_player_turn
from game.leads import LeadLifecycle, LeadStatus, create_lead, upsert_lead
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def test_look_at_altar_maps_to_investigate():
    """'look at altar' maps to investigate with target altar."""
    scene = {
        "scene": {
            "id": "chapel",
            "exits": [],
            "interactables": [{"id": "altar", "type": "investigate", "reveals_clue": "altar_secret"}],
            "visible_facts": [],
        }
    }
    parsed = parse_freeform_to_action("look at altar", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert "altar" in (parsed.get("prompt") or "").lower()
    # Target should be matched to interactable id when scene has altar
    assert parsed.get("target_id") == "altar" or "altar" in (parsed.get("prompt") or "").lower()


def test_inspect_bookshelf_maps_to_investigate():
    """'inspect bookshelf' maps to investigate bookshelf."""
    scene = {
        "scene": {
            "id": "library",
            "exits": [],
            "interactables": [{"id": "bookshelf", "type": "investigate", "reveals_clue": "hidden_tome"}],
            "visible_facts": [],
        }
    }
    parsed = parse_freeform_to_action("inspect bookshelf", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert "bookshelf" in (parsed.get("prompt") or "").lower()
    assert parsed.get("target_id") == "bookshelf" or "bookshelf" in (parsed.get("prompt") or "").lower()


def test_go_north_triggers_scene_transition_when_exit_exists():
    """'go north' triggers scene_transition when an exit with 'north' in label exists."""
    scene = {
        "scene": {
            "id": "gate",
            "exits": [
                {"label": "North gate", "target_scene_id": "north_area"},
                {"label": "Enter Cinderwatch", "target_scene_id": "market"},
            ],
        }
    }
    parsed = parse_freeform_to_action("go north", scene)
    assert parsed is not None
    assert parsed.get("type") in ("scene_transition", "travel")
    assert parsed.get("targetSceneId") == "north_area" or parsed.get("target_scene_id") == "north_area"
    assert "north" in (parsed.get("label") or "").lower()


def test_go_north_with_exit_label_match():
    """'go north' matches exit labeled 'Go north'."""
    scene = {
        "scene": {
            "id": "gate",
            "exits": [{"label": "Go north", "target_scene_id": "north_area"}],
        }
    }
    parsed = parse_freeform_to_action("go north", scene)
    assert parsed is not None
    assert parsed.get("type") in ("scene_transition", "travel")
    assert parsed.get("targetSceneId") == "north_area" or parsed.get("target_scene_id") == "north_area"


def test_ambiguous_text_falls_back_without_crashing():
    """Ambiguous or unrelated text returns None and does not crash."""
    scene = {"scene": {"id": "gate", "exits": []}}
    # Unrelated combat-like (when not in combat, parser may still return attack - that's ok)
    # Truly ambiguous
    assert parse_freeform_to_action("", scene) is None
    assert parse_freeform_to_action("   ", scene) is None
    # Gibberish
    parsed = parse_freeform_to_action("asdfghjkl qwerty", scene)
    assert parsed is None or parsed.get("type")  # May or may not match
    # Vague narrative
    parsed2 = parse_freeform_to_action("I ponder the meaning of life", scene)
    assert parsed2 is None


def test_look_around_maps_to_observe():
    """'look around' maps to observe (no specific target)."""
    scene = {"scene": {"id": "room", "exits": []}}
    parsed = parse_freeform_to_action("look around", scene)
    assert parsed is not None
    assert parsed.get("type") == "observe"


def test_investigate_notice_board_resolves():
    """'investigate the notice board' maps to investigate."""
    scene = {"scene": {"id": "gate", "exits": []}}
    parsed = parse_freeform_to_action("investigate the notice board", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert "notice" in (parsed.get("prompt") or "").lower() or "board" in (parsed.get("prompt") or "").lower()


def test_attack_returns_attack_type():
    """'I attack the guard' returns type attack (for API to route when in combat)."""
    scene = {"scene": {"id": "gate", "exits": []}}
    parsed = parse_freeform_to_action("I attack the guard with my sword", scene)
    assert parsed is not None
    assert parsed.get("type") == "attack"
    assert parsed.get("target_id") is not None or "guard" in (parsed.get("prompt") or "").lower()


def test_attack_without_target():
    """'attack' without target still returns attack type."""
    parsed = parse_freeform_to_action("attack", scene_envelope=None)
    assert parsed is not None
    assert parsed.get("type") == "attack"


def test_parse_intent_preserves_legacy_fallbacks():
    """parse_intent (no scene) still matches simple keywords."""
    assert parse_intent("search the room") is not None
    assert parse_intent("search the room").get("type") == "investigate"
    assert parse_intent("look around") is not None
    assert parse_intent("talk to the guard") is not None


def test_leave_or_exit_maps_to_travel():
    """'leave' or 'exit' maps to travel/scene_transition."""
    scene = {"scene": {"id": "room", "exits": [{"label": "Exit", "target_scene_id": "outside"}]}}
    parsed = parse_freeform_to_action("leave", scene)
    assert parsed is not None
    assert parsed.get("type") in ("travel", "scene_transition")


def test_structured_action_has_required_fields():
    """Parsed actions include id, type, label, prompt."""
    scene = {"scene": {"id": "room", "exits": []}}
    parsed = parse_freeform_to_action("observe the area", scene)
    assert parsed is not None
    assert "id" in parsed
    assert "type" in parsed
    assert "label" in parsed
    assert "prompt" in parsed
    assert parsed["type"] in ("observe", "investigate", "interact", "scene_transition", "travel", "attack", "custom")


def test_target_extraction_look_behind():
    """'look behind the altar' extracts target 'altar'."""
    scene = {
        "scene": {
            "id": "chapel",
            "exits": [],
            "interactables": [{"id": "altar", "type": "investigate", "reveals_clue": "x"}],
        }
    }
    parsed = parse_freeform_to_action("look behind the altar", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert "altar" in (parsed.get("prompt") or "").lower()


def test_segment_mixed_turn_dialogue_plus_action():
    segmented = segment_mixed_player_turn('"I have no quarrel with you," Galinor draws his blade and steps back.')
    assert segmented["spoken_text"] == "I have no quarrel with you,"
    assert segmented["declared_action_text"] is not None
    assert "draws his blade" in segmented["declared_action_text"].lower()
    assert segmented["adjudication_question_text"] is None


def test_segment_mixed_turn_action_plus_parenthetical_question():
    segmented = segment_mixed_player_turn("Galinor examines the lock (Is a Thievery check needed?)")
    assert segmented["declared_action_text"] is not None
    assert "examines the lock" in segmented["declared_action_text"].lower()
    assert segmented["adjudication_question_text"] == "Is a Thievery check needed?"


def test_segment_mixed_turn_conditional_clause():
    segmented = segment_mixed_player_turn("If the guard reaches for steel, Galinor dives behind the cart.")
    assert segmented["contingency_text"] is not None
    assert segmented["contingency_text"].lower().startswith("if the guard reaches for steel")
    assert segmented["declared_action_text"] == "Galinor dives behind the cart"


def test_segment_mixed_turn_secondary_observation_intent():
    segmented = segment_mixed_player_turn(
        "Galinor questions the courier and tries to identify the insignia on the satchel."
    )
    assert segmented["declared_action_text"] is not None
    assert "questions the courier" in segmented["declared_action_text"].lower()
    assert segmented["observation_intent_text"] is not None
    assert "identify the insignia" in segmented["observation_intent_text"].lower()


def test_segment_mixed_turn_ambiguous_fallback_is_conservative():
    text = "Galinor keeps things smooth and stays ready."
    segmented = segment_mixed_player_turn(text)
    assert segmented["spoken_text"] is None
    assert segmented["adjudication_question_text"] is None
    assert segmented["observation_intent_text"] is None
    assert segmented["contingency_text"] is None
    assert segmented["declared_action_text"] == text


def test_investigate_the_room_not_treated_as_explicit_pursuit():
    scene = {
        "scene": {
            "id": "room",
            "exits": [],
            "interactables": [],
        }
    }
    session = {}
    upsert_lead(
        session,
        create_lead(id="L1", title="x", summary="", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    rt = get_scene_runtime(session, "room")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "L1",
            "text": "Something else",
            "leads_to_scene": "elsewhere",
        }
    ]
    parsed = parse_freeform_to_action("investigate the room", scene, session=session)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert (parsed.get("metadata") or {}).get("authoritative_lead_id") is None


def test_look_around_no_pursuit_metadata_even_with_session():
    scene = {"scene": {"id": "room", "exits": []}}
    session = {}
    upsert_lead(session, create_lead(id="L1", title="x", summary="", lifecycle=LeadLifecycle.DISCOVERED))
    rt = get_scene_runtime(session, "room")
    rt["pending_leads"] = [
        {"clue_id": "c1", "authoritative_lead_id": "L1", "text": "t", "leads_to_scene": "x"},
    ]
    parsed = parse_freeform_to_action("look around", scene, session=session)
    assert parsed.get("type") == "observe"
    assert (parsed.get("metadata") or {}).get("authoritative_lead_id") is None


def test_pursue_the_x_lead_resolves_via_exact_pending_text_when_exit_unmatched():
    scene = {
        "scene": {
            "id": "gate",
            "exits": [{"label": "Unrelated exit", "target_scene_id": "other"}],
        }
    }
    session = {}
    upsert_lead(session, create_lead(id="exact_lead", title="E", summary="", lifecycle=LeadLifecycle.DISCOVERED))
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "exact_lead",
            "text": "Blue sigil on the door",
            "leads_to_scene": "old_milestone",
        }
    ]
    parsed = parse_freeform_to_action(
        "pursue the Blue sigil on the door lead", scene, session=session
    )
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert parsed.get("target_scene_id") == "old_milestone"
    assert (parsed.get("metadata") or {}).get("authoritative_lead_id") == "exact_lead"


def test_investigate_the_x_lead_maps_to_scene_transition_with_metadata():
    scene = {
        "scene": {
            "id": "gate",
            "exits": [{"label": "Old milestone trail", "target_scene_id": "old_milestone"}],
        }
    }
    session = {}
    upsert_lead(
        session,
        create_lead(id="m_lead", title="M", summary="", lifecycle=LeadLifecycle.DISCOVERED),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "m_lead",
            "text": "Rumor",
            "leads_to_scene": "old_milestone",
        }
    ]
    parsed = parse_freeform_to_action(
        "investigate the old milestone lead", scene, session=session
    )
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert parsed.get("target_scene_id") == "old_milestone"
    md = parsed.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "m_lead"
    assert md.get("commitment_source") == "explicit_player_pursuit"
    assert md.get("commitment_strength") == 2
