"""Lead-lifecycle recency stays aligned in exported narration context for NPC follow-up flows."""

from __future__ import annotations

import pytest

from game.exploration import process_investigation_discovery
from game.leads import add_lead_relation
from game.prompt_context import build_narration_context
from game.social import record_npc_lead_discussion

pytestmark = pytest.mark.integration


def _base_session(turn: int = 1) -> dict:
    return {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": turn}


def _base_world() -> dict:
    return {"inference_rules": [], "clues": {}}


def _base_scene(scene_id: str, discoverable_clues: list | None = None) -> dict:
    scene: dict = {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}
    if discoverable_clues is not None:
        scene["discoverable_clues"] = discoverable_clues
    return {"scene": scene}


def _exported_npc_relevant_ids(ctx: dict) -> list[str]:
    lead_context = ctx.get("lead_context") or {}
    return [str(r.get("id") or "") for r in (lead_context.get("npc_relevant_leads") or []) if isinstance(r, dict)]


def _exported_narration_context(session: dict, world: dict, scene_id: str, npc_id: str) -> dict:
    session["active_scene_id"] = scene_id
    session["interaction_context"] = {
        "active_interaction_target_id": npc_id,
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    return build_narration_context(
        campaign={"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        world=world,
        session=session,
        character={"name": "Hero", "hp": {}, "ac": {}},
        scene={"scene": {"id": scene_id, "visible_facts": [], "exits": [], "enemies": [], "mode": "exploration"}},
        combat={"in_combat": False},
        recent_log=[],
        user_text="Ask about the lead.",
        resolution=None,
        scene_runtime={},
        public_scene={"id": scene_id, "visible_facts": [], "exits": [], "enemies": []},
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["social_probe"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="",
        recent_log_for_prompt=[],
    )


def _exported_interlocutor_context(ctx: dict) -> dict:
    return ctx.get("interlocutor_lead_context") or {}


def _assert_repeat_suppression_flags(ilc: dict, lead_id: str) -> None:
    rs = ilc.get("repeat_suppression")
    assert isinstance(rs, dict)
    assert rs.get("has_recent_repeat_risk") is True
    assert rs.get("prefer_progress_over_restatement") is True
    recent_ids = [str(x) for x in (rs.get("recent_lead_ids") or [])]
    assert lead_id in recent_ids, (
        f"repeat_suppression.recent_lead_ids: expected {lead_id!r}; got {recent_ids!r}"
    )
    rows = [r for r in (ilc.get("introduced_by_npc") or []) if isinstance(r, dict)]
    match = [r for r in rows if str(r.get("lead_id") or "") == lead_id]
    assert match, (
        f"introduced_by_npc: expected a row for lead_id {lead_id!r}; "
        f"lead_ids={[str(r.get('lead_id') or '') for r in rows]!r}"
    )
    assert all(bool(r.get("recently_discussed")) for r in match), (
        f"introduced_by_npc: expected recently_discussed=True for {lead_id!r}; rows={match!r}"
    )


def _discover_two_leads(session: dict, world: dict, scene_id: str, clue_a: str, clue_b: str) -> tuple[str, str]:
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[
            {"id": clue_a, "text": "Brass tag stamped with a guild mark."},
            {"id": clue_b, "text": "Chalk tally marks near the postern."},
        ],
    )
    first = process_investigation_discovery(envelope, session, world=world)
    second = process_investigation_discovery(envelope, session, world=world)
    assert len(first) == 1 and len(second) == 1
    return clue_a, clue_b


def test_exported_narration_context_marks_recent_discussion_for_repeat_suppression():
    scene_id = "npc_repeat_scene_a"
    npc_id = "npc_repeat_alice"
    lead_a = "repeat_lifecycle_clue_a"
    lead_b = "repeat_lifecycle_clue_b"
    current_turn = 10
    session = _base_session(turn=current_turn)
    world = _base_world()

    la, lb = _discover_two_leads(session, world, scene_id, lead_a, lead_b)
    assert la == lead_a and lb == lead_b

    add_lead_relation(session, lead_a, "related_npc_ids", npc_id, turn=current_turn)
    add_lead_relation(session, lead_b, "related_npc_ids", npc_id, turn=current_turn)

    record_npc_lead_discussion(
        session,
        scene_id,
        npc_id,
        lead_a,
        disclosure_level="hinted",
        turn_counter=current_turn - 1,
    )

    ctx = _exported_narration_context(session, world, scene_id, npc_id)
    ilc = _exported_interlocutor_context(ctx)
    _assert_repeat_suppression_flags(ilc, lead_a)
    rel_ids = _exported_npc_relevant_ids(ctx)
    assert lead_b in rel_ids, (
        f"exported npc_relevant_leads: expected non-discussed NPC-linked lead {lead_b!r}; ids={rel_ids!r}"
    )


def test_exported_narration_context_clears_repeat_suppression_after_old_discussion():
    scene_id = "npc_repeat_scene_b"
    npc_id = "npc_repeat_bob"
    lead_a = "repeat_lifecycle_clue_c"
    lead_b = "repeat_lifecycle_clue_d"
    last_discussed = 1
    expired_turn = 20

    session = _base_session(turn=expired_turn)
    world = _base_world()

    _discover_two_leads(session, world, scene_id, lead_a, lead_b)
    add_lead_relation(session, lead_a, "related_npc_ids", npc_id, turn=expired_turn)
    add_lead_relation(session, lead_b, "related_npc_ids", npc_id, turn=expired_turn)

    record_npc_lead_discussion(
        session,
        scene_id,
        npc_id,
        lead_a,
        disclosure_level="hinted",
        turn_counter=last_discussed,
    )

    ctx = _exported_narration_context(session, world, scene_id, npc_id)
    ilc = _exported_interlocutor_context(ctx)
    rs = ilc.get("repeat_suppression")
    assert isinstance(rs, dict)
    assert rs.get("has_recent_repeat_risk") is False
    recent = rs.get("recent_lead_ids")
    assert recent in ([], None) or recent == [], (
        f"repeat_suppression.recent_lead_ids: expected empty for an old discussion "
        f"(last_discussed={last_discussed!r}, current_turn={expired_turn!r}); got {recent!r}"
    )
    assert rs.get("prefer_progress_over_restatement") is False

    rows = [r for r in (ilc.get("introduced_by_npc") or []) if isinstance(r, dict)]
    row_a = next((r for r in rows if str(r.get("lead_id") or "") == lead_a), None)
    assert row_a is not None
    assert row_a.get("recently_discussed") is False

    rel_ids = _exported_npc_relevant_ids(ctx)
    assert lead_a in rel_ids, (
        f"exported npc_relevant_leads: expected {lead_a!r} still eligible after recency expiry; ids={rel_ids!r}"
    )


def test_exported_narration_context_scopes_repeat_suppression_to_active_npc():
    scene_id = "npc_repeat_scene_c"
    npc_a = "npc_repeat_carl"
    npc_b = "npc_repeat_dana"
    lead_shared = "repeat_lifecycle_clue_e"

    session = _base_session(turn=11)
    world = _base_world()

    envelope = _base_scene(
        scene_id,
        discoverable_clues=[{"id": lead_shared, "text": "Split seal wax—two houses."}],
    )
    revealed = process_investigation_discovery(envelope, session, world=world)
    assert len(revealed) == 1

    add_lead_relation(session, lead_shared, "related_npc_ids", npc_a, turn=11)
    add_lead_relation(session, lead_shared, "related_npc_ids", npc_b, turn=11)

    record_npc_lead_discussion(
        session,
        scene_id,
        npc_a,
        lead_shared,
        disclosure_level="explicit",
        turn_counter=10,
    )

    ctx_a = _exported_narration_context(session, world, scene_id, npc_a)
    ilc_a = _exported_interlocutor_context(ctx_a)
    _assert_repeat_suppression_flags(ilc_a, lead_shared)

    ctx_b = _exported_narration_context(session, world, scene_id, npc_b)
    ilc_b = _exported_interlocutor_context(ctx_b)
    rs_b = ilc_b.get("repeat_suppression")
    assert isinstance(rs_b, dict)
    assert rs_b.get("has_recent_repeat_risk") is False
    recent_b = list(rs_b.get("recent_lead_ids") or [])
    assert recent_b == [], (
        f"repeat_suppression.recent_lead_ids for other NPC: expected []; "
        f"npc_b={npc_b!r}, got {recent_b!r}"
    )

    rel_b = _exported_npc_relevant_ids(ctx_b)
    assert lead_shared in rel_b, (
        f"exported npc_relevant_leads for npc_b: expected shared lead {lead_shared!r}; ids={rel_b!r}"
    )


def test_exported_narration_context_marks_only_discussed_lead_as_recent_repeat_risk():
    scene_id = "npc_repeat_scene_d"
    npc_id = "npc_repeat_erin"
    lead_hot = "repeat_lifecycle_clue_f"
    lead_cold = "repeat_lifecycle_clue_g"
    turn = 20

    session = _base_session(turn=turn)
    world = _base_world()

    _discover_two_leads(session, world, scene_id, lead_hot, lead_cold)
    add_lead_relation(session, lead_hot, "related_npc_ids", npc_id, turn=turn)
    add_lead_relation(session, lead_cold, "related_npc_ids", npc_id, turn=turn)

    record_npc_lead_discussion(
        session,
        scene_id,
        npc_id,
        lead_hot,
        disclosure_level="hinted",
        turn_counter=turn - 1,
    )

    ctx = _exported_narration_context(session, world, scene_id, npc_id)
    ilc = _exported_interlocutor_context(ctx)
    rs = ilc.get("repeat_suppression")
    assert isinstance(rs, dict)
    recent = list(rs.get("recent_lead_ids") or [])
    assert recent == [lead_hot], (
        f"repeat_suppression.recent_lead_ids: expected only discussed lead {[lead_hot]!r}; got {recent!r}"
    )

    introduced = [r for r in (ilc.get("introduced_by_npc") or []) if isinstance(r, dict)]
    by_id = {str(r.get("lead_id") or ""): r for r in introduced}
    assert by_id[lead_hot].get("recently_discussed") is True
    assert lead_cold not in by_id, (
        f"introduced_by_npc: undiscussed lead {lead_cold!r} should not appear; "
        f"lead_ids={list(by_id)!r}"
    )

    rel_ids = _exported_npc_relevant_ids(ctx)
    rel_set = set(rel_ids)
    assert lead_hot in rel_set and lead_cold in rel_set, (
        f"exported npc_relevant_leads: expected both {lead_hot!r} and {lead_cold!r}; ids={rel_ids!r}"
    )
