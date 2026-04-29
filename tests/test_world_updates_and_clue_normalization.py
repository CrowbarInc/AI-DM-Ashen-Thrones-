"""Tests for world_updates hardening and clue surfaced detection normalization."""
from game.world import apply_world_updates, ensure_defaults
from game.gm import detect_surfaced_clues, _normalize_clue_match_text
from game.api import _apply_authoritative_resolution_state_mutation, _apply_post_gm_updates
from game.campaign_state import create_fresh_combat_state, create_fresh_session_document
from game.storage import build_effective_scene


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
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
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
    telemetry_trace = next(
        t for t in session_after["debug_traces"] if t.get("source") == "post_emission_surfaced_clue_telemetry"
    )
    assert telemetry_trace["provenance_class"] == "telemetry_only"
    assert telemetry_trace["adoption_status"] == "telemetry_only"
    assert telemetry_trace["risk_class"] == "low"
    assert telemetry_trace["needs_gateway"] is False
    assert telemetry_trace["proposed_future_owner"] == "telemetry_only"
    assert "gateway_present" not in telemetry_trace
    assert telemetry_trace["surfaced_clue_count"] == 1
    assert "coded mark is carved" not in str(telemetry_trace)


def test_apply_post_gm_updates_scene_update_runs_under_api_scene_state_guard():
    """``game.api`` asserts SCENE_STATE ownership before merging GM scene_update layers."""
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": ["Existing."],
            "discoverable_clues": [],
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
        "player_facing_text": "",
        "tags": [],
        "scene_update": {
            "visible_facts_add": ["New fact from GM layer."],
            "discoverable_clues_add": [],
            "hidden_facts_add": [],
        },
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, scene, session, world, combat)
    facts = scene_out["scene"]["visible_facts"]
    assert "Existing." in facts
    assert "New fact from GM layer." in facts
    assert scene["scene"]["visible_facts"] == ["Existing."]
    assert session["runtime_scene_overlays"]["gate"]["visible_facts_add"] == ["New fact from GM layer."]


def test_apply_post_gm_updates_records_compact_scene_update_trace():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "The private passphrase is amber glass.",
        "tags": [],
        "scene_update": {
            "visible_facts_add": ["A new public fact."],
            "discoverable_clues_add": ["A compact clue."],
            "hidden_facts_add": ["A hidden private fact."],
        },
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, scene, session, world, combat, resolution={"kind": "observe"})

    scene_update_trace = next(
        t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update"
    )
    assert scene_update_trace["seam"] == "post_gm_updates"
    assert scene_update_trace["operation"] == "apply_gm_scene_update_layers"
    assert scene_update_trace["authority"] == "authoritative"
    assert scene_update_trace["affected_domains"] == ["scene_state", "player_visible_state", "hidden_state"]
    assert scene_update_trace["provenance_class"] == "model_structured_proposal"
    assert scene_update_trace["adoption_status"] == "authoritative_adopted"
    assert scene_update_trace["risk_class"] == "high"
    assert scene_update_trace["needs_gateway"] is True
    assert scene_update_trace["proposed_future_owner"] == "post_gm_adoption_gateway"
    assert scene_update_trace["gateway_present"] is True
    assert scene_update_trace["gateway_decision"] == "allow_validated_legacy_scene_update"
    assert scene_update_trace["gateway_mode"] == "observe_only"
    assert scene_update_trace["future_blocking_candidate"] is True
    assert scene_update_trace["validation_reason_codes"] == ["gm_scene_update:legacy_shape_allowed"]
    assert scene_update_trace["scene_id"] == "gate"
    assert scene_update_trace["resolution"] == {"kind": "observe"}
    assert scene_update_trace["visible_facts_add_count"] == 1
    assert scene_update_trace["discoverable_clues_add_count"] == 1
    assert scene_update_trace["hidden_facts_add_count"] == 1
    assert "amber glass" not in str(scene_update_trace)
    assert "A hidden private fact." not in str(scene_update_trace)


def test_apply_post_gm_updates_scene_update_preserves_discoverable_and_hidden_adds():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {
            "discoverable_clues_add": ["A chalk mark points toward the sluice."],
            "hidden_facts_add": ["The lock answers to the old bell sequence."],
        },
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, scene, session, world, combat)

    overlay_mutations = session["runtime_scene_overlays"]["gate"]["mutations"]
    assert overlay_mutations["discoverable_clues_add"] == ["A chalk mark points toward the sluice."]
    assert overlay_mutations["hidden_facts_add"] == ["The lock answers to the old bell sequence."]
    assert "A chalk mark points toward the sluice." in scene_out["scene"]["discoverable_clues"]
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["gateway_decision"] == "allow_validated_legacy_scene_update"
    assert trace["discoverable_clues_add_count"] == 1
    assert trace["hidden_facts_add_count"] == 1
    assert "old bell sequence" not in str(trace)


def test_apply_post_gm_updates_rejects_non_dict_scene_update_without_overlay_mutation():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Do not copy this narration.",
        "tags": [],
        "scene_update": "A hidden private fact should not become overlay state.",
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, scene, session, world, combat)

    assert scene_out["scene"]["visible_facts"] == []
    overlay = (session.get("runtime_scene_overlays") or {}).get("gate") or {}
    assert overlay.get("visible_facts_add") == []
    assert overlay.get("mutations") == {}
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_decision"] == "reject_unsafe_scene_update"
    assert trace["validation_reason_codes"] == ["gm_scene_update:not_a_dict"]
    assert "hidden private fact" not in str(trace)
    assert "Do not copy this narration." not in str(trace)


def test_apply_post_gm_updates_rejects_nested_scene_update_fact_payload():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {"visible_facts_add": [{"text": "Nested fact should be rejected."}]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, scene, session, world, combat)

    assert scene_out["scene"]["visible_facts"] == []
    overlay = (session.get("runtime_scene_overlays") or {}).get("gate") or {}
    assert overlay.get("visible_facts_add") == []
    assert overlay.get("mutations") == {}
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_decision"] == "reject_unsafe_scene_update"
    assert "gm_scene_update:visible_facts_add:non_string_entry" in trace["validation_reason_codes"]
    assert "Nested fact" not in str(trace)


def test_apply_post_gm_updates_records_world_update_trace_without_changing_updates():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "No payload text should be copied.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": {"append_events": [{"type": "note", "text": "World event text."}]},
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, scene, session, world, combat)

    assert world["event_log"] == [{"type": "gm_event", "text": "World event text."}]
    world_update_trace = next(
        t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates"
    )
    assert world_update_trace["seam"] == "post_gm_updates"
    assert world_update_trace["operation"] == "apply_gm_world_updates"
    assert world_update_trace["authority"] == "authoritative"
    assert world_update_trace["affected_domains"] == ["world_state"]
    assert world_update_trace["provenance_class"] == "model_structured_proposal"
    assert world_update_trace["adoption_status"] == "authoritative_adopted"
    assert world_update_trace["risk_class"] == "high"
    assert world_update_trace["needs_gateway"] is True
    assert world_update_trace["proposed_future_owner"] == "post_gm_adoption_gateway"
    assert world_update_trace["gateway_present"] is True
    assert world_update_trace["gateway_decision"] == "allow_validated_legacy_world_updates"
    assert world_update_trace["gateway_mode"] == "observe_only"
    assert world_update_trace["future_blocking_candidate"] is True
    assert world_update_trace["validation_reason_codes"] == ["gm_world_updates:legacy_shape_allowed"]
    assert world_update_trace["append_events_count"] == 1
    assert "No payload text should be copied." not in str(world_update_trace)
    assert "World event text." not in str(world_update_trace)


def test_apply_post_gm_updates_rejects_non_dict_world_updates_without_mutation():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": "The hidden cult controls the docks.",
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, scene, session, world, combat)

    assert world["event_log"] == []
    world_update_trace = next(
        t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates"
    )
    assert world_update_trace["adoption_status"] == "rejected"
    assert world_update_trace["gateway_decision"] == "reject_unsafe_world_updates"
    assert world_update_trace["validation_reason_codes"] == ["gm_world_updates:not_a_dict"]
    assert world_update_trace["append_events_count"] == 0
    assert "hidden cult" not in str(world_update_trace)


def test_apply_post_gm_updates_rejects_unknown_prose_world_update_payload():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": {"hidden_facts": "The sealed vault is below the shrine."},
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, scene, session, world, combat)

    assert world["event_log"] == []
    world_update_trace = next(
        t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates"
    )
    assert world_update_trace["adoption_status"] == "rejected"
    assert world_update_trace["gateway_decision"] == "reject_unsafe_world_updates"
    assert "gm_world_updates:unknown_keys_parked" in world_update_trace["validation_reason_codes"]
    assert "gm_world_updates:unsafe_unknown_prose_key" in world_update_trace["validation_reason_codes"]
    assert world_update_trace["raw_unknown_key_count"] == 1
    assert "sealed vault" not in str(world_update_trace)


def test_apply_post_gm_updates_records_transition_proposals_as_advisory_only():
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    session = {"active_scene_id": "gate", "scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": "market",
        "new_scene_draft": {"title": "Market"},
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, scene, session, world, combat)

    assert session["active_scene_id"] == "gate"
    proposal_trace = next(
        t for t in session["debug_traces"] if t.get("source") == "gm_transition_proposal_ignored"
    )
    assert proposal_trace["authority"] == "advisory-only"
    assert proposal_trace["provenance_class"] == "advisory_only"
    assert proposal_trace["adoption_status"] == "advisory_ignored"
    assert proposal_trace["risk_class"] == "low"
    assert proposal_trace["needs_gateway"] is False
    assert proposal_trace["proposed_future_owner"] == "no_change"
    assert "gateway_present" not in proposal_trace
    assert proposal_trace["proposal_count"] == 2
    assert proposal_trace["has_new_scene_draft"] is True
    assert proposal_trace["has_activate_scene_id"] is True


def test_build_effective_scene_merges_overlay_without_mutating_canon():
    canon = {
        "scene": {
            "id": "gate",
            "visible_facts": ["Existing."],
            "discoverable_clues": ["Old clue."],
            "hidden_facts": [],
            "mode": "exploration",
        }
    }
    overlay = {
        "scene_id": "gate",
        "visible_facts_add": ["New fact."],
        "discovered_clues": ["Found clue."],
        "state_flags": {"alarm": True},
        "runtime_entities": [{"id": "ash_hound"}],
        "mutations": {"mode": "social", "discoverable_clues_add": ["New clue."]},
    }

    effective = build_effective_scene(canon, overlay)

    assert effective["scene"]["visible_facts"] == ["Existing.", "New fact."]
    assert effective["scene"]["discoverable_clues"] == ["Old clue.", "New clue."]
    assert effective["scene"]["discovered_clues"] == ["Found clue."]
    assert effective["scene"]["runtime_entities"] == [{"id": "ash_hound"}]
    assert effective["scene"]["state_flags"] == {"alarm": True}
    assert effective["scene"]["mode"] == "social"
    assert not effective.get("_is_canon")
    assert canon["scene"]["visible_facts"] == ["Existing."]
    effective["scene"]["visible_facts"].append("Effective-only mutation.")
    assert canon["scene"]["visible_facts"] == ["Existing."]


def test_apply_post_gm_updates_rejects_canon_scene_mutation_attempt():
    scene = {
        "_is_canon": True,
        "scene": {
            "id": "gate",
            "visible_facts": ["Existing."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
        },
    }
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {"visible_facts_add": ["New fact from GM layer."]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    with pytest.raises(RuntimeError, match="Canonical scene mutation attempted"):
        _apply_post_gm_updates(gm, scene, session, world, combat)
    assert session["runtime_scene_overlays"] == {}


def test_apply_authoritative_resolution_state_mutation_world_and_scene_guards_observe():
    """Non-transition resolution exercises dual assert_owner for world_state + scene_state in api."""
    session = create_fresh_session_document()
    session["active_scene_id"] = "gate"
    session["scene_state"]["active_scene_id"] = "gate"
    world: dict = {"npcs": [], "world_state": {"flags": {}, "counters": {}, "clocks": {}}}
    combat = create_fresh_combat_state()
    scene = {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {"kind": "observe", "success": True, "action_id": "act-observe"}
    normalized_action = {"id": "act-observe", "type": "observe", "prompt": "Look around."}

    _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=normalized_action,
    )
    rt = session.get("scene_runtime", {}).get("gate", {})
    assert isinstance(rt, dict)
    assert rt.get("last_resolution_kind") == "observe"
