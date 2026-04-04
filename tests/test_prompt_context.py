"""Prompt-layer exports for promoted interlocutors (Block 2 profile + hint contracts)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from game.campaign_state import create_fresh_session_document
from game.interaction_context import set_social_target
from game.leads import SESSION_LEAD_REGISTRY_KEY, LeadLifecycle, LeadStatus
from game.prompt_context import (
    build_active_interlocutor_export,
    build_authoritative_lead_prompt_context,
    build_narration_context,
    build_social_interlocutor_profile,
    deterministic_interlocutor_answer_style_hints,
)
from game.social import compute_social_target_profile_hints
from game.world import upsert_world_npc


import pytest

pytestmark = pytest.mark.integration


def _minimal_lead_row_keys() -> frozenset[str]:
    return frozenset(
        {
            "id",
            "title",
            "summary",
            "type",
            "status",
            "lifecycle",
            "confidence",
            "priority",
            "next_step",
            "last_updated_turn",
            "last_touched_turn",
            "related_npc_ids",
            "related_location_ids",
        }
    )


def _session_with_registry(*leads: dict) -> dict:
    reg = {}
    for L in leads:
        lid = str(L.get("id") or "lead")
        reg[lid] = dict(L)
    return {
        "active_scene_id": "frontier_gate",
        "turn_counter": 0,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: reg,
    }


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_active_and_pursued_ranking():
    """Top active slice ranks by priority, then last_updated_turn, then last_touched_turn, then stable tie."""
    session = _session_with_registry(
        {
            "id": "z_pursued_same_pri",
            "title": "Zebra",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 19,
            "last_touched_turn": 10,
        },
        {
            "id": "a_pursued_same_pri",
            "title": "Alpha",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 20,
            "last_touched_turn": 10,
        },
        {
            "id": "low_pursued",
            "title": "Low",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 99,
            "last_touched_turn": 99,
        },
        {
            "id": "top_active",
            "title": "Active top",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 10,
            "last_updated_turn": 1,
            "last_touched_turn": 1,
        },
    )
    session["turn_counter"] = 100
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert len(out["top_active_leads"]) <= 3
    ids_top = [r["id"] for r in out["top_active_leads"]]
    assert ids_top == ["top_active", "a_pursued_same_pri", "z_pursued_same_pri"]
    assert out["currently_pursued_lead"] is not None
    assert out["currently_pursued_lead"]["id"] == "a_pursued_same_pri"


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_stale_and_untouched_high_priority_active():
    """STALE leads always qualify; ACTIVE with priority>=1 and last_touched stale by >=2 turns qualifies."""
    session = _session_with_registry(
        {
            "id": "st_one",
            "title": "Stale thread",
            "status": LeadStatus.STALE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 0,
            "last_updated_turn": 1,
            "last_touched_turn": 0,
        },
        {
            "id": "active_press",
            "title": "High pri untouched",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 2,
            "last_updated_turn": 5,
            "last_touched_turn": 3,
        },
    )
    session["turn_counter"] = 10
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    urgent_ids = {r["id"] for r in out["urgent_or_stale_leads"]}
    assert "st_one" in urgent_ids
    assert "active_press" in urgent_ids
    assert out["follow_up_pressure_from_leads"]["has_stale"] is True


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_recent_changes_order_and_compact_shape():
    rows = (
        {
            "id": "old_active",
            "title": "Old",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 0,
            "last_updated_turn": 5,
        },
        {
            "id": "terminal",
            "title": "Done",
            "status": LeadStatus.RESOLVED.value,
            "lifecycle": LeadLifecycle.RESOLVED.value,
            "priority": 0,
            "last_updated_turn": 50,
        },
        {
            "id": "mid",
            "title": "Mid",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 0,
            "last_updated_turn": 30,
        },
    )
    session = _session_with_registry(*rows)
    session["turn_counter"] = 60
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert len(out["recent_lead_changes"]) <= 5
    turns = [int(r["last_updated_turn"] or 0) for r in out["recent_lead_changes"]]
    assert turns == sorted(turns, reverse=True)
    keys = _minimal_lead_row_keys()
    for r in out["recent_lead_changes"]:
        assert isinstance(r, dict)
        assert set(r.keys()) == keys
        assert "id" in r and "title" in r and "status" in r and "priority" in r


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_npc_relevance_cap_and_filter():
    session = _session_with_registry(
        {
            "id": "rel_a",
            "title": "Related A",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "related_npc_ids": ["npc_1"],
            "last_updated_turn": 1,
        },
        {
            "id": "rel_b",
            "title": "Related B",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 0,
            "related_npc_ids": ["npc_1", "other"],
            "last_updated_turn": 2,
        },
        {
            "id": "unrelated_hot",
            "title": "Unrelated",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 99,
            "related_npc_ids": ["npc_2"],
            "last_updated_turn": 99,
        },
    )
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id="npc_1"
    )
    assert len(out["npc_relevant_leads"]) <= 3
    rel_ids = {r["id"] for r in out["npc_relevant_leads"]}
    assert rel_ids <= {"rel_a", "rel_b"}
    assert "unrelated_hot" not in rel_ids


@patch("game.prompt_context.list_session_leads")
@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_tolerates_mixed_mapping_and_attr_leads(mock_list_leads):
    """``_lead_get`` supports Mapping or attribute rows; mixed lists must not crash."""
    mock_list_leads.return_value = [
        {
            "id": "dict_lead",
            "title": "From dict",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 2,
            "last_updated_turn": 5,
            "last_touched_turn": 1,
        },
        SimpleNamespace(
            id="ns_lead",
            title="From namespace",
            status=LeadStatus.ACTIVE.value,
            lifecycle=LeadLifecycle.COMMITTED.value,
            priority=1,
            last_updated_turn=10,
            last_touched_turn=2,
        ),
    ]
    session = {"turn_counter": 20, SESSION_LEAD_REGISTRY_KEY: {}}
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    ids_top = [r["id"] for r in out["top_active_leads"]]
    assert "dict_lead" in ids_top and "ns_lead" in ids_top
    for row in out["top_active_leads"] + out["recent_lead_changes"]:
        assert set(row.keys()) == _minimal_lead_row_keys()


@patch("game.prompt_context.list_session_leads")
@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_sparse_lead_rows_remain_deterministic(mock_list_leads):
    """Omitted optional fields still compact and sort stably (registry-normalization bypass)."""
    mock_list_leads.return_value = [
        {
            "id": "sparse_a",
            "title": "Sparse A",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        },
        {
            "id": "sparse_b",
            "title": "Sparse B",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 2,
        },
    ]
    session = {"turn_counter": 0, SESSION_LEAD_REGISTRY_KEY: {}}
    out1 = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    out2 = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert [r["id"] for r in out1["top_active_leads"]] == [r["id"] for r in out2["top_active_leads"]]
    assert [r["id"] for r in out1["recent_lead_changes"]] == [r["id"] for r in out2["recent_lead_changes"]]
    for r in out1["top_active_leads"] + out1["recent_lead_changes"]:
        assert set(r.keys()) == _minimal_lead_row_keys()
        assert r["related_npc_ids"] == [] and r["related_location_ids"] == []


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_terminal_in_recent_only_not_active_or_pursued_slice():
    """Terminal lifecycle rows may appear in recent_lead_changes but not active/pursued prompt slices."""
    session = _session_with_registry(
        {
            "id": "still_active",
            "title": "Ongoing",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 10,
            "last_touched_turn": 0,
        },
        {
            "id": "pursued_thread",
            "title": "Pursued",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 20,
            "last_touched_turn": 0,
        },
        {
            "id": "wrapped_up",
            "title": "Resolved thread",
            "status": LeadStatus.RESOLVED.value,
            "lifecycle": LeadLifecycle.RESOLVED.value,
            "priority": 0,
            "last_updated_turn": 100,
            "last_touched_turn": 0,
        },
    )
    session["turn_counter"] = 101
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    recent_ids = [r["id"] for r in out["recent_lead_changes"]]
    active_ids = {r["id"] for r in out["top_active_leads"]}
    assert "wrapped_up" in recent_ids
    assert "wrapped_up" not in active_ids
    assert out["currently_pursued_lead"] is not None
    assert out["currently_pursued_lead"]["id"] == "pursued_thread"


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_title_tie_break_when_scores_equal():
    """When priority and turn keys tie, ordering follows the final string tie-break (title, else id)."""
    session = _session_with_registry(
        {
            "id": "id_z",
            "title": "gamma",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 7,
            "last_touched_turn": 2,
        },
        {
            "id": "id_y",
            "title": "alpha",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 7,
            "last_touched_turn": 2,
        },
        {
            "id": "id_x",
            "title": "beta",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 7,
            "last_touched_turn": 2,
        },
    )
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert [r["title"] for r in out["top_active_leads"]] == ["alpha", "beta", "gamma"]


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_empty_registry():
    session = {
        "turn_counter": 0,
        SESSION_LEAD_REGISTRY_KEY: {},
    }
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert set(out.keys()) == {
        "top_active_leads",
        "currently_pursued_lead",
        "urgent_or_stale_leads",
        "recent_lead_changes",
        "npc_relevant_leads",
        "follow_up_pressure_from_leads",
    }
    assert out["currently_pursued_lead"] is None
    assert out["top_active_leads"] == []
    assert out["urgent_or_stale_leads"] == []
    assert out["recent_lead_changes"] == []
    assert out["npc_relevant_leads"] == []
    assert out["follow_up_pressure_from_leads"] == {
        "has_pursued": False,
        "has_stale": False,
        "npc_has_relevant": False,
    }


def _narration_minimal_kwargs(**overrides):
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": _session_with_registry(),
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "frontier_gate", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Look around.",
        "resolution": None,
        "scene_runtime": {"pending_leads": [{"hint": "legacy pending"}]},
        "public_scene": {"id": "frontier_gate", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [{"surface": "scene hook"}],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    base.update(overrides)
    return base


def test_build_narration_context_exposes_lead_context_and_preserves_pending_surfaces():
    session = _session_with_registry(
        {
            "id": "reg_lead",
            "title": "Registry lead",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 3,
            "related_npc_ids": [],
        }
    )
    session["turn_counter"] = 5
    session["interaction_context"] = {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session))
    assert "lead_context" in ctx
    lc = ctx["lead_context"]
    for key in (
        "top_active_leads",
        "currently_pursued_lead",
        "urgent_or_stale_leads",
        "recent_lead_changes",
        "npc_relevant_leads",
        "follow_up_pressure_from_leads",
    ):
        assert key in lc
    assert ctx["scene"]["pending_leads"] == [{"surface": "scene hook"}]
    assert ctx["scene"]["runtime"]["pending_leads"] == [{"hint": "legacy pending"}]


def test_follow_up_pressure_merges_log_pressure_with_from_leads():
    session = _session_with_registry()
    session["turn_counter"] = 5
    log = [
        {
            "log_meta": {"player_input": "What happened at the north gate yesterday?"},
            "gm_output": {"player_facing_text": "Guards doubled the watch and turned merchants away."},
        }
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            user_text="Again, what happened at the north gate yesterday?",
            recent_log_for_prompt=log,
        )
    )
    fup = ctx["follow_up_pressure"]
    assert isinstance(fup, dict)
    assert fup.get("pressed") is True
    assert "from_leads" in fup
    assert set(fup["from_leads"].keys()) == {"has_pursued", "has_stale", "npc_has_relevant"}
    assert all(isinstance(fup["from_leads"][k], bool) for k in fup["from_leads"])


def test_follow_up_pressure_from_leads_only_when_no_log_pressure():
    session = _session_with_registry(
        {
            "id": "p_only",
            "title": "Pursued only",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 1,
        }
    )
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session, recent_log_for_prompt=[]))
    fup = ctx["follow_up_pressure"]
    assert fup == {
        "from_leads": {
            "has_pursued": True,
            "has_stale": False,
            "npc_has_relevant": False,
        }
    }
    assert "pressed" not in fup


def test_follow_up_pressure_none_when_no_log_and_no_lead_booleans():
    session = _session_with_registry()
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session))
    assert ctx["follow_up_pressure"] is None


def test_social_lock_keeps_from_leads_without_log_escalation():
    world: dict = {"npcs": []}
    upsert_world_npc(
        world,
        {
            "id": "npc_social",
            "name": "Social NPC",
            "location": "frontier_gate",
            "role": "guard",
            "availability": "available",
            "topics": [],
        },
    )
    session = _session_with_registry(
        {
            "id": "soc_pursued",
            "title": "Social pursued",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 2,
            "related_npc_ids": ["npc_social"],
        }
    )
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"] = {"active_scene_id": "frontier_gate", "promoted_actor_npc_map": {}}
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_social",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    session["turn_counter"] = 4
    log = [
        {
            "log_meta": {"player_input": "Tell me about the patrol route and the north gate."},
            "gm_output": {"player_facing_text": "Two teams rotate; the north gate is sealed after dark."},
        }
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world=world,
            user_text="Again, tell me about the patrol route and the north gate.",
            recent_log_for_prompt=log,
        )
    )
    fup = ctx["follow_up_pressure"]
    assert fup == {
        "from_leads": {
            "has_pursued": True,
            "has_stale": False,
            "npc_has_relevant": True,
        }
    }
    assert "pressed" not in fup


def test_active_npc_id_from_interlocutor_export_npc_id():
    world: dict = {"npcs": []}
    upsert_world_npc(
        world,
        {
            "id": "npc_from_export",
            "name": "Export NPC",
            "location": "frontier_gate",
            "role": "merchant",
            "availability": "available",
            "topics": [],
        },
    )
    session = _session_with_registry(
        {
            "id": "tie_export",
            "title": "Tied to export npc",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "related_npc_ids": ["npc_from_export"],
            "last_updated_turn": 1,
        },
        {
            "id": "noise",
            "title": "Noise",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 99,
            "related_npc_ids": ["someone_else"],
            "last_updated_turn": 9,
        },
    )
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"] = {"active_scene_id": "frontier_gate", "promoted_actor_npc_map": {}}
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_from_export",
        "active_interaction_kind": "question",
        "interaction_mode": "explore",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    session["turn_counter"] = 2
    public_scene = {"id": "frontier_gate", "visible_facts": [], "exits": [], "enemies": []}
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session, world=world, public_scene=public_scene))
    rel = ctx["lead_context"]["npc_relevant_leads"]
    assert len(rel) == 1
    assert rel[0]["id"] == "tie_export"


@patch("game.prompt_context.build_active_interlocutor_export")
def test_active_npc_id_falls_back_to_session_view_target(mock_export):
    """When interlocutor export omits npc_id, narration uses compressed session active_interaction_target_id."""
    mock_export.return_value = {
        "npc_id": "",
        "raw_interaction_target_id": "npc_fallback",
        "display_name": "",
    }
    session = _session_with_registry(
        {
            "id": "tie_fb",
            "title": "Fallback npc tie",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "related_npc_ids": ["npc_fallback"],
            "last_updated_turn": 1,
        }
    )
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_fallback",
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    session["turn_counter"] = 1
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session))
    assert ctx["lead_context"]["npc_relevant_leads"]
    assert ctx["lead_context"]["npc_relevant_leads"][0]["id"] == "tie_fb"


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_npc_relevant_empty_without_active_npc_id():
    """Same slice the narration wiring passes when no active NPC id is derived (e.g. no mapping-like scene branch)."""
    session = _session_with_registry(
        {
            "id": "only_related_rows",
            "title": "Related rows ignored without active id",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 9,
            "related_npc_ids": ["npc_1"],
            "last_updated_turn": 1,
        }
    )
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert out["npc_relevant_leads"] == []


def test_active_npc_id_empty_when_no_usable_target_even_if_public_scene_is_mapping():
    session = _session_with_registry(
        {
            "id": "lonely",
            "title": "Lonely",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 5,
            "related_npc_ids": ["ghost_npc"],
            "last_updated_turn": 1,
        }
    )
    session["interaction_context"] = {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session))
    assert ctx["lead_context"]["npc_relevant_leads"] == []

def test_prompt_context_exports_promoted_interlocutor_profile():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    session["scene_state"]["promoted_actor_npc_map"]["crowd_snitch"] = "gate__crowd_snitch"

    world: dict = {"npcs": []}
    upsert_world_npc(
        world,
        {
            "id": "gate__crowd_snitch",
            "name": "Crowd snitch",
            "location": "frontier_gate",
            "role": "informant",
            "affiliation": "ash_cowl",
            "availability": "available",
            "current_agenda": "sell a name",
            "disposition": "neutral",
            "stance_toward_player": "wary",
            "information_reliability": "partial",
            "knowledge_scope": ["scene:frontier_gate", "rumor"],
            "origin_kind": "crowd_actor",
            "origin_scene_id": "frontier_gate",
            "promoted_from_actor_id": "crowd_snitch",
            "topics": [],
        },
    )
    set_social_target(session, "crowd_snitch")

    public_scene = {"id": "frontier_gate"}
    export = build_active_interlocutor_export(session, world, public_scene)
    assert export is not None
    assert export["npc_id"] == "gate__crowd_snitch"
    assert export["raw_interaction_target_id"] == "crowd_snitch"

    profile = build_social_interlocutor_profile(export)
    assert profile["npc_is_promoted"] is True
    assert profile["stance"] == "wary"
    assert profile["reliability"] == "partial"
    assert "scene:frontier_gate" in profile["knowledge_scope"]
    assert profile["agenda"] == "sell a name"
    assert profile["affiliation"] == "ash_cowl"


def test_knowledge_scope_and_reliability_change_social_hints_deterministically():
    sid = "frontier_gate"
    base_export = {
        "npc_id": "n1",
        "stance_toward_player": "neutral",
        "knowledge_scope": ["scene:frontier_gate", "patrol"],
        "origin_kind": "scene_actor",
        "promoted_from_actor_id": "actor_a",
    }
    truthful = {**base_export, "information_reliability": "truthful"}
    partial = {**base_export, "information_reliability": "partial"}
    misleading = {**base_export, "information_reliability": "misleading"}

    ht = compute_social_target_profile_hints(truthful, sid)
    hp = compute_social_target_profile_hints(partial, sid)
    hm = compute_social_target_profile_hints(misleading, sid)
    assert ht["answer_reliability_tier"] == "high"
    assert hp["answer_reliability_tier"] == "medium"
    assert hm["answer_reliability_tier"] == "low"
    assert ht["speaks_authoritatively_for_scene"] is True
    assert hm["guardedness"] == "medium"

    lines_t = deterministic_interlocutor_answer_style_hints(truthful, scene_id=sid)
    lines_p = deterministic_interlocutor_answer_style_hints(partial, scene_id=sid)
    lines_m = deterministic_interlocutor_answer_style_hints(misleading, scene_id=sid)
    assert any("INFORMATION_RELIABILITY truthful" in x for x in lines_t)
    assert any("INFORMATION_RELIABILITY partial" in x for x in lines_p)
    assert any("INFORMATION_RELIABILITY misleading" in x for x in lines_m)
    assert not any("misleading" in x for x in lines_t)
    assert not any("truthful" in x for x in lines_m)
