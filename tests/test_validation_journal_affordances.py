import json

from game.gm import validate_gm_state_update, build_messages
from game.journal import build_player_journal
from game.affordances import generate_scene_affordances
from game.storage import get_scene_runtime
from game.scene_actions import normalize_scene_action, normalize_scene_actions_list
from tests.test_prompt_and_guard import FRONTIER_GATE_SCENE, _dummy_state


import pytest

pytestmark = pytest.mark.unit

def test_validate_gm_state_update_strips_unexpected_and_blocks_hidden_promotion():
    _, _, session, _, _, _ = _dummy_state()
    scene = FRONTIER_GATE_SCENE
    hidden = scene["scene"]["hidden_facts"][0]

    gm = {
        "player_facing_text": "x",
        "scene_update": {
            "visible_facts_add": [hidden, "New visible detail."],
            "hidden_facts_add": ["New secret."],
            "unexpected_key": ["should be stripped"],
            "mode": "exploration",
        },
        "world_updates": {
            "append_events": ["A long event text" * 100],
            "unexpected": "x",
        },
        "new_scene_draft": {
            "location": " New Place ",
            "summary": " S " * 500,
            "visible_facts": ["V1"],
            "hidden_facts": ["H1"],
            "extra": "ignore me",
        },
    }

    out = validate_gm_state_update(gm, session, scene)
    su = out["scene_update"]
    # Hidden fact should not have been promoted into visible_facts_add.
    assert hidden not in su.get("visible_facts_add", [])
    assert "New visible detail." in su.get("visible_facts_add", [])
    # Unexpected keys stripped.
    assert "unexpected_key" not in su

    wu = out["world_updates"]
    assert "append_events" in wu
    assert "unexpected" not in wu

    nd = out["new_scene_draft"]
    assert "extra" not in nd
    assert nd["location"].strip() == "New Place"
    assert len(nd["summary"]) <= 800


def test_journal_uses_journal_seed_facts_not_full_visible_list():
    _, world, session, _, _, _ = _dummy_state()
    session["active_scene_id"] = "test_gate"
    envelope = {
        "scene": {
            "id": "test_gate",
            "journal_seed_facts": ["Seed line A.", "Seed line B."],
            "visible_facts": [f"Visible {i}." for i in range(20)],
        }
    }
    journal = build_player_journal(session, world, envelope)
    assert journal["known_facts"] == ["Seed line A.", "Seed line B."]


def test_journal_caps_visible_facts_when_no_journal_seed():
    _, world, session, _, _, _ = _dummy_state()
    session["active_scene_id"] = "test_gate"
    envelope = {"scene": {"id": "test_gate", "visible_facts": [f"V{i}" for i in range(20)]}}
    journal = build_player_journal(session, world, envelope)
    assert len(journal["known_facts"]) == 8
    assert journal["known_facts"][0] == "V0" and journal["known_facts"][-1] == "V7"


def test_journal_merges_revealed_hidden_facts():
    _, world, session, _, _, _ = _dummy_state()
    session["active_scene_id"] = "frontier_gate"
    session["scene_runtime"] = {
        "frontier_gate": {"revealed_hidden_facts": ["A revealed secret."], "discovered_clues": []}
    }
    envelope = {"scene": {"id": "frontier_gate", "visible_facts": ["Only visible."], "journal_seed_facts": []}}
    journal = build_player_journal(session, world, envelope)
    assert "Only visible." in journal["known_facts"]
    assert "A revealed secret." in journal["known_facts"]


def test_journal_includes_discovered_clues_player_safe():
    campaign, world, session, character, combat, recent_log = _dummy_state()
    # Synthesize a runtime discovered clue.
    session["scene_runtime"] = {
        "frontier_gate": {"discovered_clues": ["A discovered clue."], "revealed_hidden_facts": [], "suspicion_flags": []}
    }
    world.setdefault("event_log", []).append({"type": "gm_event", "text": "World event."})

    journal = build_player_journal(session, world, FRONTIER_GATE_SCENE)
    assert "A discovered clue." in journal["discovered_clues"]
    # Hidden facts must not appear.
    for hf in FRONTIER_GATE_SCENE["scene"]["hidden_facts"]:
        assert hf not in json.dumps(journal)


def test_affordances_generated_and_exposed_structure():
    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene = FRONTIER_GATE_SCENE
    affs = generate_scene_affordances(scene, scene["scene"]["mode"], session)
    assert isinstance(affs, list)
    assert affs, "Expected at least one affordance"
    for a in affs:
        assert {"id", "label", "type", "prompt"} <= set(a.keys())
        assert isinstance(a["label"], str) and a["label"]
        assert isinstance(a["prompt"], str) and a["prompt"]
        assert a["type"] in ("scene_transition", "investigate", "interact", "travel", "observe", "custom")


def test_normalize_scene_action_legacy_string():
    """Legacy string actions normalize to structured with inferred type."""
    a = normalize_scene_action("Go: Enter Cinderwatch")
    assert a["label"] == "Go: Enter Cinderwatch"
    assert a["type"] == "scene_transition"
    assert a["id"]
    assert a["prompt"] == a["label"]

    a2 = normalize_scene_action("Investigate: the notice board")
    assert a2["type"] == "investigate"

    a3 = normalize_scene_action("Observe the area")
    assert a3["type"] == "observe"


def test_normalize_scene_action_legacy_affordance_dict():
    """Legacy affordance dict (id, label, category, prompt) normalizes with prompt in metadata and top-level."""
    raw = {"id": "go-gate", "label": "Go: Return to the Gate", "category": "travel", "prompt": "I take the route: Return to the Gate", "target_scene_id": "frontier_gate"}
    a = normalize_scene_action(raw)
    assert a["id"] == "go-gate"
    assert a["label"] == "Go: Return to the Gate"
    assert a["type"] == "scene_transition"
    assert a["targetSceneId"] == "frontier_gate"
    assert a["metadata"].get("prompt") == "I take the route: Return to the Gate"
    assert a["prompt"] == a["metadata"]["prompt"]


def test_normalize_scene_actions_list_skips_invalid():
    """normalize_scene_actions_list skips None and invalid; returns valid structured actions."""
    out = normalize_scene_actions_list([None, "Go: North", {"label": "Investigate", "prompt": "I investigate."}])
    assert len(out) == 2
    assert out[0]["type"] == "scene_transition"
    assert out[1]["type"] == "investigate"


def test_response_mode_instructions_change_prompt():
    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")

    # Default mode: standard.
    msgs_standard = build_messages(
        campaign, world, {"response_mode": "standard"}, character, FRONTIER_GATE_SCENE, combat, recent_log, "Look around.", None, scene_runtime=scene_rt
    )
    standard_payload = json.loads(msgs_standard[1]["content"])
    instr_standard = "\n".join(standard_payload["instructions"])
    assert "Narration mode: standard" in instr_standard

    # Tactical mode.
    msgs_tactical = build_messages(
        campaign, world, {"response_mode": "tactical"}, character, FRONTIER_GATE_SCENE, combat, recent_log, "Look around.", None, scene_runtime=scene_rt
    )
    tactical_payload = json.loads(msgs_tactical[1]["content"])
    instr_tactical = "\n".join(tactical_payload["instructions"])
    assert "Narration mode: tactical" in instr_tactical
    # Mechanics unchanged: we only touch instructions.
    assert tactical_payload["mechanical_resolution"] is None

