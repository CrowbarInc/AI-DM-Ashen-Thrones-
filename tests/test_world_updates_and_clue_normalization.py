"""Tests for world_updates hardening and clue surfaced detection normalization."""
from game.world import apply_world_updates, ensure_defaults
from game.gm import detect_surfaced_clues, _normalize_clue_match_text
from game.api import _apply_post_gm_updates


import pytest

pytestmark = pytest.mark.integration

def test_malformed_world_updates_projects_sanitized():
    """Malformed or partial projects in world_updates do not wipe existing; valid entries merged."""
    world = {"projects": [], "event_log": [], "factions": [{"id": "f1", "name": "Guild"}]}
    ensure_defaults(world)
    world["projects"] = [
        {"id": "p1", "name": "Existing", "category": "infrastructure", "status": "active", "progress": 1, "target": 3},
    ]

    # GPT sends partial/malformed: non-dict and one valid
    apply_world_updates(world, {
        "projects": [
            None,
            "not a dict",
            {"name": "New Project", "category": "research", "progress": 0, "target": 2},
        ],
    })

    assert len(world["projects"]) == 2
    ids = [p["id"] for p in world["projects"]]
    assert "p1" in ids
    assert "new_project" in ids  # slugify("New Project") -> new_project
    p1 = next(p for p in world["projects"] if p["id"] == "p1")
    assert p1["name"] == "Existing"
    assert world["factions"] == [{"id": "f1", "name": "Guild"}]


def test_valid_world_updates_projects_apply_normally():
    """Valid world_updates.projects merge: new appended, existing updated by id."""
    world = {"projects": [], "event_log": []}
    ensure_defaults(world)
    world["projects"] = [
        {"id": "a", "name": "Alpha", "category": "infrastructure", "status": "active", "progress": 0, "target": 4},
    ]

    apply_world_updates(world, {
        "projects": [
            {"id": "a", "name": "Alpha Updated", "category": "infrastructure", "progress": 2, "target": 4},
            {"id": "b", "name": "Beta", "category": "research", "progress": 0, "target": 2},
        ],
    })

    assert len(world["projects"]) == 2
    a = next(p for p in world["projects"] if p["id"] == "a")
    b = next(p for p in world["projects"] if p["id"] == "b")
    assert a["name"] == "Alpha Updated"
    assert a["progress"] == 2
    assert b["name"] == "Beta"
    assert b["target"] == 2


def test_non_project_collections_not_wiped_by_malformed_partial():
    """Sending world_updates with factions/settlements/assets does not replace world state."""
    world = {"projects": [], "event_log": [], "factions": [{"id": "f1"}], "settlements": [{"name": "Town"}], "assets": []}
    ensure_defaults(world)

    apply_world_updates(world, {
        "factions": [],
        "settlements": [],
        "assets": [{"junk": 1}],
        "world_flags": [],
    })

    assert world["factions"] == [{"id": "f1"}]
    assert world["settlements"] == [{"name": "Town"}]
    assert world["assets"] == []


def test_append_events_still_works():
    """append_events in world_updates still appends to event_log."""
    world = {"event_log": []}
    ensure_defaults(world)
    apply_world_updates(world, {"append_events": [{"type": "custom", "text": "Hello"}]})
    assert len(world["event_log"]) == 1
    assert world["event_log"][0]["text"] == "Hello"


def test_clue_surfaced_detection_whitespace_case_punctuation():
    """Surfaced clue detection matches across small whitespace, case, and punctuation differences."""
    scene = {
        "scene": {
            "id": "test",
            "discoverable_clues": [
                "A well-dressed onlooker near the gate seems interested in newcomers.",
                "Someone's secret motive is hidden here.",
            ],
        }
    }

    # Exact match still works
    found = detect_surfaced_clues("A well-dressed onlooker near the gate seems interested in newcomers.", scene)
    assert any("well-dressed onlooker" in c for c in found)

    # Case difference
    found = detect_surfaced_clues("A WELL-DRESSED ONLOOKER near the gate seems interested in newcomers.", scene)
    assert any("well-dressed onlooker" in c for c in found)

    # Collapsed whitespace / extra spaces
    found = detect_surfaced_clues(
        "A  well-dressed   onlooker near the gate  seems  interested in newcomers.", scene
    )
    assert any("well-dressed onlooker" in c for c in found)

    # Curly apostrophe in narration (normalized to straight)
    found = detect_surfaced_clues("Someone's secret motive is hidden here.", scene)
    assert any("Someone's secret" in c or "secret motive" in c for c in found)


def test_normalize_clue_match_text_helper():
    """_normalize_clue_match_text lowercases, trims, collapses whitespace."""
    assert _normalize_clue_match_text("  Foo   Bar  ") == "foo bar"
    assert _normalize_clue_match_text("UPPER") == "upper"
    assert _normalize_clue_match_text("") == ""
    assert _normalize_clue_match_text(None) == ""


def test_gpt_narration_surfacing_does_not_mutate_clue_state():
    """Narration clue mentions are telemetry-only and do not author clue knowledge."""
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": ["A coded mark is carved beneath the bridge rail."],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "You spot it clearly: a coded mark is carved beneath the bridge rail.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    _, session_after, _, surfaced, _narr_leads = _apply_post_gm_updates(gm, scene, session, world, combat)
    assert surfaced == ["A coded mark is carved beneath the bridge rail."]
    assert session_after.get("clue_knowledge") == {}
    assert (session_after.get("scene_runtime", {}).get("gate", {}).get("discovered_clue_ids") or []) == []
