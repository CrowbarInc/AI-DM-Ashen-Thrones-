"""Canonical owner for prompt-context assembly and prompt-contract bundle semantics.

Direct prompt-contract semantics live here, including the canonical prompt-facing
public homes for shipped helpers such as ``build_social_response_structure_contract()``
and ``peek_response_type_contract_from_resolution()``. Downstream gate, emission,
social-adjacent, guard, and transcript suites should consume shipped/exported
behavior rather than re-own helper semantics; they may keep smoke/regression
coverage, but should not read as the primary semantic owner for prompt contracts.
"""
from __future__ import annotations

import copy
from types import SimpleNamespace
from unittest.mock import patch

import game.response_policy_contracts as response_policy_contracts
from game.campaign_state import create_fresh_session_document
from game.defaults import default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    create_lead,
    reconcile_session_lead_progression,
    refresh_lead_touch,
    resolve_lead,
)
from game.prompt_context import (
    CONVERSATIONAL_MEMORY_SOFT_LIMIT,
    NO_VALIDATOR_VOICE_RULE,
    RESPONSE_RULE_PRIORITY,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    _answer_pressure_followup_details,
    _compress_recent_log,
    _extract_npc_introduced_anchor_tokens,
    build_active_interlocutor_export,
    build_authoritative_lead_prompt_context,
    build_interlocutor_lead_discussion_context,
    build_narration_context,
    build_response_policy,
    build_social_response_structure_contract,
    build_social_interlocutor_profile,
    derive_narration_obligations,
    deterministic_interlocutor_answer_style_hints,
    deterministic_interlocutor_lead_behavior_hints,
    peek_response_type_contract_from_resolution,
)
from game.social import (
    compute_social_target_profile_hints,
    mark_player_acknowledged_npc_lead,
    record_npc_lead_discussion,
)
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
            "escalation_level",
            "escalation_reason",
            "escalated_at_turn",
            "unlocked_by_lead_id",
            "obsolete_by_lead_id",
            "superseded_by",
            "stale_after_turns",
            "last_transition_reason",
            "last_transition_category",
            "last_transition_turn",
            "last_transition_from_lifecycle",
            "last_transition_to_lifecycle",
            "last_transition_from_status",
            "last_transition_to_status",
            "last_progression_effects",
        }
    )


def _expected_follow_up_pressure_from_leads(**overrides: bool) -> dict:
    base = {
        "has_pursued": False,
        "has_stale": False,
        "npc_has_relevant": False,
        "has_escalated_threat": False,
        "has_newly_unlocked": False,
        "has_supersession_cleanup": False,
    }
    base.update(overrides)
    return base


def _answer_pressure_details(player: str, recent_compact: list, *, active_id: str = "runner") -> dict:
    return _answer_pressure_followup_details(
        player_input=player,
        recent_log_compact=recent_compact,
        narration_obligations={},
        session_view={"active_interaction_target_id": active_id},
    )


def test_prompt_contract_owner_canonical_public_home_preserves_compatibility_with_downstream_helpers() -> None:
    rtc = {"required_response_type": "dialogue"}
    resolution = {"metadata": {"response_type_contract": dict(rtc)}}

    assert build_social_response_structure_contract(
        rtc,
        debug_inputs={"scene_id": "s1"},
    ) == response_policy_contracts.build_social_response_structure_contract(
        rtc,
        debug_inputs={"scene_id": "s1"},
    )
    assert peek_response_type_contract_from_resolution(
        resolution
    ) == response_policy_contracts.peek_response_type_contract_from_resolution(resolution)


def test_prompt_contract_owner_peeks_validated_response_type_contract_from_resolution_metadata() -> None:
    resolution = {"metadata": {"response_type_contract": {"required_response_type": "Dialogue"}}}

    assert peek_response_type_contract_from_resolution(resolution) == {
        "required_response_type": "dialogue"
    }


def test_prompt_contract_owner_peek_rejects_invalid_response_type_contract_metadata() -> None:
    resolution = {"metadata": {"response_type_contract": {"required_response_type": "soliloquy"}}}

    assert peek_response_type_contract_from_resolution(resolution) is None


def test_prompt_contract_owner_social_response_structure_contract_requires_dialogue() -> None:
    contract = build_social_response_structure_contract(
        {"required_response_type": "Dialogue"},
        debug_inputs={"scene_id": "gate_yard"},
    )

    assert contract == {
        "enabled": True,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": True,
        "discourage_expository_monologue": True,
        "require_natural_cadence": True,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2,
        "max_dialogue_paragraphs_before_break": 2,
        "prefer_single_speaker_turn": True,
        "forbid_bulleted_or_list_like_dialogue": True,
        "required_response_type": "dialogue",
        "debug_reason": "response_type_contract_requires_dialogue",
        "debug_inputs": {"scene_id": "gate_yard"},
    }


def test_prompt_contract_owner_social_response_structure_contract_disables_non_dialogue_turns() -> None:
    contract = build_social_response_structure_contract(
        {"required_response_type": "action_outcome"},
        debug_inputs={"scene_id": "alley"},
    )

    assert contract == {
        "enabled": False,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": False,
        "discourage_expository_monologue": False,
        "require_natural_cadence": False,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": None,
        "max_dialogue_paragraphs_before_break": None,
        "prefer_single_speaker_turn": False,
        "forbid_bulleted_or_list_like_dialogue": False,
        "required_response_type": "action_outcome",
        "debug_reason": "response_type_not_dialogue:action_outcome",
        "debug_inputs": {"scene_id": "alley"},
    }


def test_prompt_contract_owner_includes_structured_turn_summary_and_no_restatement_guidance() -> None:
    resolution = {
        "kind": "question",
        "action_id": "ask-guard",
        "label": "Question the guard",
        "prompt": 'Galinor asks, "Who signed this order?"',
        "social": {"target_id": "guard_captain"},
        "requires_check": False,
    }
    user_text = 'Galinor asks, "Who signed this order?" while examining the notice board.'
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            user_text=user_text,
            resolution=resolution,
            intent={"labels": ["social_probe"]},
        )
    )
    turn_summary = ctx["turn_summary"]
    obligations = ctx["narration_obligations"]
    instructions = " ".join(ctx.get("instructions", [])).lower()

    assert turn_summary["action_descriptor"] == "Question the guard"
    assert turn_summary["resolution_kind"] == "question"
    assert turn_summary["raw_player_input"] == user_text
    assert obligations["avoid_player_action_restatement"] is True
    assert obligations["prefer_structured_turn_summary"] is True
    assert "avoid_player_action_restatement" in instructions
    assert "prefer_structured_turn_summary" in instructions


@pytest.mark.unit
def test_prompt_contract_owner_marks_wait_turn_as_active_reply_expected_when_social_engagement_is_live() -> None:
    obligations = derive_narration_obligations(
        {
            "turn_counter": 5,
            "visited_scene_count": 2,
            "active_interaction_target_id": "rian",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
        },
        resolution={"kind": "observe", "action_id": "wait"},
        intent={"labels": ["passive_pause", "observation"]},
        recent_log_for_prompt=[],
        scene_runtime={},
    )
    assert obligations["active_npc_reply_expected"] is True
    assert obligations["suppress_non_social_emitters"] is True
    assert obligations["scene_momentum_due"] is False


def test_prompt_contract_owner_exports_player_expression_contract_for_quoted_third_person_input() -> None:
    user_text = 'Galinor asks, "Who signed this order?" while examining the notice board.'
    ctx = build_narration_context(**_narration_minimal_kwargs(user_text=user_text))

    contract = ctx["player_expression_contract"]
    assert contract["default_action_style"] == "third_person"
    assert contract["quoted_speech_allowed"] is True
    assert contract["preserve_user_expression_format"] is True
    assert ctx["player_input"] == user_text


def test_prompt_contract_owner_exposes_rule_priority_hierarchy() -> None:
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            user_text='Galinor asks, "Who signed this order?"',
            intent={"labels": ["social_probe"]},
        )
    )
    policy = ctx["response_policy"]
    instructions = " ".join(ctx.get("instructions", []))

    assert policy["rule_priority_order"] == [label for _, label in RESPONSE_RULE_PRIORITY]
    rd = policy.get("response_delta") or {}
    assert rd.get("enabled") is False
    assert rd.get("trigger_source") == "none"
    assert RULE_PRIORITY_COMPACT_INSTRUCTION in instructions
    assert "avoid unjustified certainty" in instructions.lower()
    assert "response_policy.rule_priority_order" in instructions
    assert NO_VALIDATOR_VOICE_RULE in instructions
    assert policy["no_validator_voice"]["enabled"] is True
    assert policy["no_validator_voice"]["applies_to"] == "standard_narration"
    assert policy["no_validator_voice"]["rules_explanation_only_in"] == ["oc", "adjudication"]
    assert (
        "rules_explanation_outside_oc_or_adjudication"
        in policy["no_validator_voice"]["prohibited_perspectives"]
    )


def test_prompt_contract_owner_enables_response_delta_for_same_topic_follow_up_question() -> None:
    prior_chat = "What did the guards report about the north gate before the gates were barred?"
    prior_gm = (
        "The night sergeant filed a short report noting extra cart traffic and one sealed "
        "warrant shown at the north gate before compline bells."
    )
    recent_log_for_prompt = [
        {
            "log_meta": {"player_input": prior_chat},
            "gm_output": {"player_facing_text": prior_gm},
        }
    ]
    ctx = build_narration_context(
        {
            "title": "Test Campaign",
            "premise": "A test premise.",
            "character_role": "A test role.",
            "gm_guidance": ["g1", "g2", "g3", "g4", "g5"],
            "world_pressures": ["p1", "p2", "p3", "p4"],
            "magic_style": "Rare and mysterious.",
        },
        {
            "settlements": [{"id": "s1", "name": "City"}],
            "factions": [{"id": "f1", "name": "Faction A"}, {"id": "f2", "name": "Faction B"}],
            "event_log": [
                {"type": "event", "text": "Event 1"},
                {"type": "event", "text": "Event 2"},
            ],
            "world_state": {"flags": {"flag1": True}, "counters": {"c1": 5}, "clocks": {}},
        },
        {"active_scene_id": "frontier_gate", "response_mode": "standard", "turn_counter": 10},
        {"name": "Galinor", "hp": {"current": 8, "max": 8}, "ac": {"normal": 12}},
        {
            "scene": {
                "id": "frontier_gate",
                "location": "Gate District",
                "summary": "A crowded gate.",
                "visible_facts": ["Fact 1", "Fact 2"],
                "discoverable_clues": [{"id": "c1", "text": "A discoverable clue."}],
                "hidden_facts": ["A secret motivation."],
                "exits": [],
                "enemies": [],
            }
        },
        {"in_combat": False},
        [],
        "Okay but what happened at the north gate after that?",
        None,
        {},
        public_scene={
            "id": "frontier_gate",
            "location": "Gate District",
            "summary": "A crowded gate.",
            "visible_facts": ["Fact 1", "Fact 2"],
            "exits": [],
            "enemies": [],
        },
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["social_probe"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=recent_log_for_prompt,
    )
    rd = ctx["response_policy"].get("response_delta") or {}
    assert rd.get("enabled") is True
    assert rd.get("delta_required") is True
    assert rd.get("trigger_source") == "same_topic_direct_question"
    assert rd.get("forbid_semantic_restatement") is True
    assert set(rd.get("allowed_delta_kinds") or []) == {
        "new_information",
        "refinement",
        "consequence",
        "clarified_uncertainty",
    }
    trace = rd.get("trace") or {}
    assert trace.get("follow_up_pressure_detected") is True
    assert trace.get("prior_answer_available") is True
    assert "response_policy.response_delta.enabled" in " ".join(ctx.get("instructions", [])).lower()


def test_prompt_contract_owner_exposes_typed_uncertainty_policy_and_hint() -> None:
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            user_text="Where is the patrol report?",
            intent={"labels": ["social_probe"]},
            uncertainty_hint={
                "category": "unknown_location",
                "known_edge": "The trail points past the notice board, not to a final door.",
                "unknown_edge": "After that, the last stop drops into rumor.",
                "next_lead": "Start at the missing patrol notice and pin down the last sighting tied to it.",
            },
        )
    )
    policy = ctx["response_policy"]
    instructions = " ".join(ctx.get("instructions", [])).lower()

    assert policy["uncertainty"]["enabled"] is True
    assert policy["uncertainty"]["categories"] == [
        "unknown_identity",
        "unknown_location",
        "unknown_motive",
        "unknown_method",
        "unknown_quantity",
        "unknown_feasibility",
    ]
    assert policy["uncertainty"]["answer_shape"] == [
        "known_edge",
        "unknown_edge",
        "next_lead",
    ]
    assert policy["uncertainty"]["sources"] == [
        "npc_ignorance",
        "scene_ambiguity",
        "procedural_insufficiency",
    ]
    assert policy["uncertainty"]["context_inputs"] == [
        "turn_context",
        "speaker",
        "scene_snapshot",
    ]
    assert ctx["uncertainty_hint"]["category"] == "unknown_location"
    assert "response_policy.uncertainty.categories" in instructions
    assert "response_policy.uncertainty.sources" in instructions
    assert "response_policy.uncertainty.answer_shape" in instructions
    assert "uncertainty_hint.turn_context" in instructions
    assert "uncertainty_hint.speaker" in instructions
    assert "uncertainty_hint.scene_snapshot" in instructions
    assert "frame uncertainty as world-facing limits only" in instructions
    assert "vary sentence count and cadence naturally" in instructions


def test_prompt_contract_owner_exports_promoted_npc_identity_and_social_profile() -> None:
    world = {
        "settlements": [{"id": "s1", "name": "City"}],
        "factions": [{"id": "f1", "name": "Faction A"}, {"id": "f2", "name": "Faction B"}],
        "event_log": [
            {"type": "event", "text": "Event 1"},
            {"type": "event", "text": "Event 2"},
        ],
        "world_state": {"flags": {"flag1": True}, "counters": {"c1": 5}, "clocks": {}},
        "npcs": [
            {
                "id": "frontier_gate__ragged_stranger",
                "name": "Keene",
                "location": "frontier_gate",
                "stance_toward_player": "wary",
                "information_reliability": "partial",
                "knowledge_scope": ["scene:frontier_gate", "rumor"],
                "affiliation": "",
                "current_agenda": "watch the gate",
                "promoted_from_actor_id": "ragged_stranger",
                "origin_kind": "scene_actor",
            }
        ],
    }
    session = {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 3,
        "interaction_context": {
            "active_interaction_target_id": "ragged_stranger",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
        },
        "scene_state": {
            "promoted_actor_npc_map": {"ragged_stranger": "frontier_gate__ragged_stranger"},
        },
    }
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            world=world,
            session=session,
            user_text="What did you hear?",
            intent={"labels": ["question"], "allow_discoverable_clues": False},
            gm_only_hidden_facts=["A secret motivation."],
            gm_only_discoverable_locked=["A discoverable clue."],
            undiscovered_clue_records=[{"id": "c1", "text": "A discoverable clue."}],
            mode_instruction="Narration mode: standard.",
        )
    )
    assert ctx["session"]["active_interaction_target_id"] == "frontier_gate__ragged_stranger"
    assert ctx["session"]["active_interaction_target_name"] == "Keene"
    profile = ctx["social_context"]["interlocutor_profile"]
    assert profile["npc_is_promoted"] is True
    assert profile["reliability"] == "partial"
    assert profile["stance"] == "wary"
    assert "scene:frontier_gate" in profile["knowledge_scope"]
    active = ctx["active_interlocutor"]
    assert active["npc_id"] == "frontier_gate__ragged_stranger"
    assert active["raw_interaction_target_id"] == "ragged_stranger"
    assert active["promoted_from_actor_id"] == "ragged_stranger"
    hints = ctx["social_context"]["answer_style_hints"]
    assert any("INFORMATION_RELIABILITY partial" in hint for hint in hints)
    assert any("INTERLOCUTOR KNOWLEDGE GATE" in hint for hint in hints)
    assert any("NAMING CONTINUITY (engine)" in line for line in ctx["instructions"])


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


def _record_discussion(
    session: dict,
    *,
    scene_id: str,
    npc_id: str,
    lead_id: str,
    turn: int,
    disclosure_level: str = "hinted",
    acknowledged: bool = False,
) -> None:
    record_npc_lead_discussion(
        session,
        scene_id,
        npc_id,
        lead_id,
        disclosure_level=disclosure_level,
        turn_counter=turn,
    )
    if acknowledged:
        mark_player_acknowledged_npc_lead(
            session,
            scene_id,
            npc_id,
            lead_id,
            turn_counter=turn,
        )


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_active_and_pursued_ranking():
    """Top active slice ranks by effective lead pressure, then last_updated_turn, last_touched_turn, stable tie."""
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
def test_build_interlocutor_lead_discussion_context_only_active_npc_rows():
    session = _session_with_registry(
        {"id": "lead_a", "title": "Lead A", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
        {"id": "lead_b", "title": "Lead B", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_a", turn=9)
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_other", lead_id="lead_b", turn=9)
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    assert out["active_npc_id"] == "npc_dockmaster"
    assert [r["lead_id"] for r in out["introduced_by_npc"]] == ["lead_a"]


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_joins_registry_fields():
    session = _session_with_registry(
        {
            "id": "lead_smuggler_drop",
            "title": "Smuggler Drop",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_smuggler_drop",
        turn=10,
        disclosure_level="explicit",
    )
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    row = out["introduced_by_npc"][0]
    assert row["title"] == "Smuggler Drop"
    assert row["status"] == LeadStatus.ACTIVE.value
    assert row["lifecycle"] == LeadLifecycle.COMMITTED.value


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_unacknowledged_sorts_first():
    session = _session_with_registry(
        {"id": "lead_unack", "title": "A Lead", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
        {"id": "lead_ack", "title": "B Lead", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_ack", turn=10, acknowledged=True)
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_unack", turn=10)
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    assert [r["lead_id"] for r in out["introduced_by_npc"]][:2] == ["lead_unack", "lead_ack"]
    assert [r["lead_id"] for r in out["unacknowledged_from_npc"]] == ["lead_unack"]


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_recent_window_and_repeat_suppression():
    session = _session_with_registry(
        {"id": "lead_recent", "title": "Recent", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
        {"id": "lead_old", "title": "Old", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_recent", turn=9)
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_old", turn=6)
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    recency_by_id = {r["lead_id"]: r["recently_discussed"] for r in out["introduced_by_npc"]}
    assert recency_by_id["lead_recent"] is True
    assert recency_by_id["lead_old"] is False
    assert out["repeat_suppression"]["has_recent_repeat_risk"] is True
    assert out["repeat_suppression"]["recent_lead_ids"] == ["lead_recent"]
    assert out["repeat_suppression"]["prefer_progress_over_restatement"] is True


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_excludes_terminal_from_actionable():
    session = _session_with_registry(
        {"id": "lead_active", "title": "Active", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
        {"id": "lead_done", "title": "Done", "status": LeadStatus.RESOLVED.value, "lifecycle": LeadLifecycle.RESOLVED.value},
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_active", turn=10)
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_done", turn=10)
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    actionable_ids = {r["lead_id"] for r in out["introduced_by_npc"]}
    terminal_ids = {r["lead_id"] for r in out["recent_terminal_reference"]}
    assert "lead_active" in actionable_ids
    assert "lead_done" not in actionable_ids
    assert "lead_done" in terminal_ids


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_neutral_when_no_active_npc():
    session = _session_with_registry()
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id=None,
    )
    assert out["active_npc_id"] is None
    assert out["introduced_by_npc"] == []
    assert out["unacknowledged_from_npc"] == []
    assert out["recently_discussed_with_npc"] == []
    assert out["repeat_suppression"] == {
        "has_recent_repeat_risk": False,
        "recent_lead_ids": [],
        "prefer_progress_over_restatement": False,
    }


@pytest.mark.unit
def test_build_interlocutor_lead_discussion_context_skips_missing_registry_row():
    session = _session_with_registry(
        {"id": "lead_present", "title": "Present", "status": LeadStatus.ACTIVE.value, "lifecycle": LeadLifecycle.COMMITTED.value},
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 10
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_present", turn=10)
    _record_discussion(session, scene_id="scene_docks", npc_id="npc_dockmaster", lead_id="lead_missing", turn=10)
    out = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": "scene_docks"},
        recent_log=[],
        active_npc_id="npc_dockmaster",
    )
    ids = [r["lead_id"] for r in out["introduced_by_npc"]]
    assert ids == ["lead_present"]


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_repeat_risk_prefers_progression():
    hints = deterministic_interlocutor_lead_behavior_hints(
        {
            "active_npc_id": "npc_dockmaster",
            "introduced_by_npc": [{"lead_id": "lead_recent"}],
            "unacknowledged_from_npc": [],
            "recently_discussed_with_npc": [{"lead_id": "lead_recent", "disclosure_level": "hinted"}],
            "recent_terminal_reference": [],
            "repeat_suppression": {"has_recent_repeat_risk": True},
        }
    )
    assert any("prefer advancement" in hint and "over repetition" in hint for hint in hints)


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_recent_explicit_not_brand_new():
    hints = deterministic_interlocutor_lead_behavior_hints(
        {
            "active_npc_id": "npc_dockmaster",
            "introduced_by_npc": [{"lead_id": "lead_explicit"}],
            "unacknowledged_from_npc": [],
            "recently_discussed_with_npc": [{"lead_id": "lead_explicit", "disclosure_level": "explicit"}],
            "recent_terminal_reference": [],
            "repeat_suppression": {"has_recent_repeat_risk": False},
        }
    )
    assert any("already discussed explicitly as brand-new" in hint for hint in hints)


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_hinted_unack_allows_narrowing():
    hints = deterministic_interlocutor_lead_behavior_hints(
        {
            "active_npc_id": "npc_dockmaster",
            "introduced_by_npc": [{"lead_id": "lead_hint"}],
            "unacknowledged_from_npc": [
                {
                    "lead_id": "lead_hint",
                    "disclosure_level": "hinted",
                    "player_acknowledged": False,
                }
            ],
            "recently_discussed_with_npc": [],
            "recent_terminal_reference": [],
            "repeat_suppression": {"has_recent_repeat_risk": False},
        }
    )
    assert any("continued hinting or narrowing is allowed" in hint for hint in hints)
    assert any("full disclosure is not required" in hint for hint in hints)


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_acknowledged_is_shared_context():
    hints = deterministic_interlocutor_lead_behavior_hints(
        {
            "active_npc_id": "npc_dockmaster",
            "introduced_by_npc": [{"lead_id": "lead_ack", "player_acknowledged": True}],
            "unacknowledged_from_npc": [],
            "recently_discussed_with_npc": [],
            "recent_terminal_reference": [],
            "repeat_suppression": {"has_recent_repeat_risk": False},
        }
    )
    assert any("treat it as shared context" in hint for hint in hints)
    assert any("move beyond basic re-introduction" in hint for hint in hints)


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_terminal_only_returns_empty():
    hints = deterministic_interlocutor_lead_behavior_hints(
        {
            "active_npc_id": "npc_dockmaster",
            "introduced_by_npc": [],
            "unacknowledged_from_npc": [],
            "recently_discussed_with_npc": [],
            "recent_terminal_reference": [{"lead_id": "lead_done"}],
            "repeat_suppression": {"has_recent_repeat_risk": False},
        }
    )
    assert hints == []


@pytest.mark.unit
def test_interlocutor_lead_behavior_hints_neutral_returns_empty():
    neutral = {
        "active_npc_id": None,
        "introduced_by_npc": [],
        "unacknowledged_from_npc": [],
        "recently_discussed_with_npc": [],
        "recent_terminal_reference": [],
        "repeat_suppression": {
            "has_recent_repeat_risk": False,
            "recent_lead_ids": [],
            "prefer_progress_over_restatement": False,
        },
    }
    assert deterministic_interlocutor_lead_behavior_hints(neutral) == []
    assert deterministic_interlocutor_lead_behavior_hints(None) == []


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
def test_build_authoritative_lead_prompt_context_compact_row_surfaces_engine_metadata_inspection():
    """Compact rows copy transition/progression inspection keys from lead['metadata'] read-only."""
    meta_full = {
        "last_transition_reason": "reconcile:stale",
        "last_transition_category": "staleness",
        "last_transition_turn": 7,
        "last_transition_from_lifecycle": "discovered",
        "last_transition_to_lifecycle": "committed",
        "last_transition_from_status": "active",
        "last_transition_to_status": "pursued",
        "last_progression_effects": ["escalation:0->1", "touch:refresh"],
    }
    meta_bad_effects = {"last_progression_effects": "not-a-list"}
    session = _session_with_registry(
        {
            "id": "inspected",
            "title": "Inspected",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 5,
            "last_updated_turn": 10,
            "metadata": meta_full,
        },
        {
            "id": "plain",
            "title": "Plain",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 1,
        },
        {
            "id": "bad_fx",
            "title": "Bad fx",
            "status": LeadStatus.STALE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 0,
            "last_updated_turn": 5,
            "metadata": meta_bad_effects,
        },
    )
    session["turn_counter"] = 10
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    by_id = {r["id"]: r for r in out["top_active_leads"] + out["recent_lead_changes"] + out["urgent_or_stale_leads"]}
    row = by_id["inspected"]
    assert row["last_transition_reason"] == "reconcile:stale"
    assert row["last_transition_category"] == "staleness"
    assert row["last_transition_turn"] == 7
    assert row["last_transition_from_lifecycle"] == "discovered"
    assert row["last_transition_to_lifecycle"] == "committed"
    assert row["last_transition_from_status"] == "active"
    assert row["last_transition_to_status"] == "pursued"
    assert row["last_progression_effects"] == ["escalation:0->1", "touch:refresh"]
    assert isinstance(row["last_progression_effects"], list)
    assert row["last_progression_effects"] is not meta_full["last_progression_effects"]

    plain = by_id["plain"]
    for k in (
        "last_transition_reason",
        "last_transition_category",
        "last_transition_turn",
        "last_transition_from_lifecycle",
        "last_transition_to_lifecycle",
        "last_transition_from_status",
        "last_transition_to_status",
        "last_progression_effects",
    ):
        assert plain.get(k) is None

    bad = by_id["bad_fx"]
    assert bad["last_progression_effects"] is None

    recent_row = next(r for r in out["recent_lead_changes"] if r["id"] == "inspected")
    assert recent_row["last_transition_reason"] == "reconcile:stale"
    assert isinstance(recent_row["last_progression_effects"], list)


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_inspection_metadata_does_not_alter_ranking_slices():
    """Metadata enrichment must not change pursued selection, top-active order, or urgent composition."""
    session = _session_with_registry(
        {
            "id": "z_pursued_same_pri",
            "title": "Zebra",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 19,
            "last_touched_turn": 10,
            "metadata": {"last_transition_reason": "heavy", "last_progression_effects": ["a"]},
        },
        {
            "id": "a_pursued_same_pri",
            "title": "Alpha",
            "status": LeadStatus.PURSUED.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 3,
            "last_updated_turn": 20,
            "last_touched_turn": 10,
            "metadata": {"last_transition_reason": "light"},
        },
        {
            "id": "top_active",
            "title": "Active top",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 10,
            "last_updated_turn": 1,
            "last_touched_turn": 99,
        },
    )
    session["turn_counter"] = 100
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert [r["id"] for r in out["top_active_leads"]] == ["top_active", "a_pursued_same_pri", "z_pursued_same_pri"]
    assert out["currently_pursued_lead"]["id"] == "a_pursued_same_pri"
    assert out["currently_pursued_lead"]["last_transition_reason"] == "light"


@pytest.mark.unit
def test_build_authoritative_lead_prompt_context_compact_effects_list_mutation_isolated_from_registry():
    reg = _session_with_registry(
        {
            "id": "mut",
            "title": "M",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 1,
            "metadata": {"last_progression_effects": ["one"]},
        }
    )
    snap_fx = list(reg[SESSION_LEAD_REGISTRY_KEY]["mut"]["metadata"]["last_progression_effects"])
    out = build_authoritative_lead_prompt_context(
        reg, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    row = out["top_active_leads"][0]
    assert row["last_progression_effects"] == ["one"]
    row["last_progression_effects"].append("injected")
    assert reg[SESSION_LEAD_REGISTRY_KEY]["mut"]["metadata"]["last_progression_effects"] == snap_fx


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
    assert [r["id"] for r in out["npc_relevant_leads"]] == ["rel_a", "rel_b"]


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
def test_escalated_threat_outranks_high_priority_rumor_in_top_active():
    session = _session_with_registry(
        {
            "id": "rumor",
            "title": "Rumor",
            "type": LeadType.RUMOR.value,
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "priority": 5,
            "last_updated_turn": 10,
            "last_touched_turn": 10,
        },
        {
            "id": "threat",
            "title": "Threat",
            "type": LeadType.THREAT.value,
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "priority": 0,
            "escalation_level": 3,
            "last_updated_turn": 1,
            "last_touched_turn": 1,
        },
    )
    session["turn_counter"] = 20
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert out["top_active_leads"][0]["id"] == "threat"
    assert out["follow_up_pressure_from_leads"]["has_escalated_threat"] is True


@pytest.mark.unit
def test_newly_unlocked_lead_surfaces_first_in_recent_lead_changes():
    session = _session_with_registry(
        {
            "id": "older",
            "title": "Older",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "last_updated_turn": 50,
        },
        {
            "id": "unlocked",
            "title": "Unlocked",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "last_updated_turn": 60,
            "unlocked_by_lead_id": "resolver_lead",
        },
    )
    session["turn_counter"] = 60
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert out["recent_lead_changes"][0]["id"] == "unlocked"
    assert out["follow_up_pressure_from_leads"]["has_newly_unlocked"] is True


@pytest.mark.unit
def test_obsolete_superseded_lead_excluded_from_active_emphasis_views():
    session = _session_with_registry(
        {
            "id": "dead",
            "title": "Superseded thread",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.OBSOLETE.value,
            "priority": 999,
            "last_updated_turn": 200,
            "obsolete_reason": "superseded",
            "superseded_by": "replacer",
            "related_npc_ids": ["npc_1"],
        },
        {
            "id": "live",
            "title": "Live thread",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "priority": 1,
            "last_updated_turn": 1,
            "related_npc_ids": ["npc_1"],
        },
    )
    session["turn_counter"] = 201
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id="npc_1"
    )
    for bucket in ("top_active_leads", "urgent_or_stale_leads", "npc_relevant_leads"):
        assert all(r["id"] != "dead" for r in out[bucket])
    assert out["currently_pursued_lead"] is None


@pytest.mark.unit
def test_supersession_cleanup_sets_follow_up_pressure_flag():
    session = _session_with_registry(
        {
            "id": "gone",
            "title": "Gone",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.OBSOLETE.value,
            "last_updated_turn": 7,
            "obsolete_reason": "superseded",
            "superseded_by": "new_lead",
        },
    )
    session["turn_counter"] = 7
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert out["follow_up_pressure_from_leads"]["has_supersession_cleanup"] is True


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
    assert out["follow_up_pressure_from_leads"] == _expected_follow_up_pressure_from_leads()


@patch("game.leads.reconcile_session_lead_progression")
@pytest.mark.unit
def test_prompt_builders_do_not_invoke_session_lead_reconciliation(mock_reconcile):
    """Lead prompt paths are registry read-only; progression belongs to the authoritative API layer."""
    session = _session_with_registry(
        {
            "id": "x",
            "title": "X",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 1,
            "last_updated_turn": 1,
        }
    )
    session["turn_counter"] = 2
    build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    mock_reconcile.assert_not_called()
    build_narration_context(**_narration_minimal_kwargs(session=session))
    mock_reconcile.assert_not_called()


@pytest.mark.unit
def test_double_authoritative_lead_prompt_context_is_read_only_on_registry():
    row = {
        "id": "r",
        "title": "R",
        "status": LeadStatus.ACTIVE.value,
        "lifecycle": LeadLifecycle.DISCOVERED.value,
        "priority": 1,
        "last_updated_turn": 3,
        "first_discovered_turn": 0,
    }
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 4,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {"r": dict(row)},
    }
    snap = copy.deepcopy(session[SESSION_LEAD_REGISTRY_KEY])
    build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert session[SESSION_LEAD_REGISTRY_KEY] == snap


@pytest.mark.unit
def test_stale_lead_in_urgent_and_recent_not_in_top_active():
    """Stale threads stay visible via urgent/recent slices; they drop out of the active top-3 emphasis."""
    session = _session_with_registry(
        {
            "id": "gone_stale",
            "title": "Forgotten thread",
            "status": LeadStatus.STALE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "priority": 2,
            "last_updated_turn": 20,
            "last_touched_turn": 0,
        },
        {
            "id": "still_hot",
            "title": "Hot",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.DISCOVERED.value,
            "priority": 1,
            "last_updated_turn": 19,
        },
    )
    session["turn_counter"] = 20
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert any(r["id"] == "gone_stale" for r in out["urgent_or_stale_leads"])
    assert any(r["id"] == "gone_stale" for r in out["recent_lead_changes"])
    assert all(r["id"] != "gone_stale" for r in out["top_active_leads"])
    assert out["follow_up_pressure_from_leads"]["has_stale"] is True


@pytest.mark.unit
def test_threat_touch_refresh_clears_escalated_threat_prompt_flag():
    row = create_lead(
        title="T",
        summary="",
        id="t",
        type=LeadType.THREAT,
        first_discovered_turn=0,
    )
    session = {
        "turn_counter": 9,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {"t": row},
    }
    reconcile_session_lead_progression(session, turn=9)
    pc1 = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert pc1["follow_up_pressure_from_leads"]["has_escalated_threat"] is True
    assert pc1["top_active_leads"] and pc1["top_active_leads"][0]["id"] == "t"

    refresh_lead_touch(session[SESSION_LEAD_REGISTRY_KEY]["t"], turn=9)
    reconcile_session_lead_progression(session, turn=9)
    pc2 = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert pc2["follow_up_pressure_from_leads"]["has_escalated_threat"] is False


@pytest.mark.unit
def test_multi_effect_reconcile_then_prompt_context_all_pressure_flags():
    """After one reconciliation pass, prompt slices expose stale, threat, unlock, and supersession signals."""
    parent = resolve_lead(
        create_lead(title="Src", summary="", id="src_u", unlocks=["child_u"]),
        resolution_type="done",
        turn=1,
    )
    child_u = create_lead(title="Ch", summary="", id="child_u", lifecycle=LeadLifecycle.HINTED)
    stale_me = create_lead(
        title="S",
        summary="",
        id="stale_me",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    threat_e = create_lead(
        title="Th",
        summary="",
        id="threat_e",
        type=LeadType.THREAT,
        first_discovered_turn=0,
    )
    newer_m = create_lead(title="New", summary="", id="newer_m", supersedes=["old_m"])
    old_m = create_lead(
        title="Old",
        summary="",
        id="old_m",
        lifecycle=LeadLifecycle.DISCOVERED,
        superseded_by="newer_m",
    )
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 10,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {
            "src_u": parent,
            "child_u": child_u,
            "stale_me": stale_me,
            "threat_e": threat_e,
            "newer_m": newer_m,
            "old_m": old_m,
        },
    }
    reconcile_session_lead_progression(session, turn=10)
    reg = session[SESSION_LEAD_REGISTRY_KEY]
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    pressure = out["follow_up_pressure_from_leads"]
    assert pressure["has_stale"] is True
    assert pressure["has_escalated_threat"] is True
    assert pressure["has_newly_unlocked"] is True
    assert pressure["has_supersession_cleanup"] is True

    assert any(r["id"] == "stale_me" for r in out["urgent_or_stale_leads"])
    assert any(r["id"] == "threat_e" for r in out["urgent_or_stale_leads"])
    assert any(r["id"] == "child_u" for r in out["top_active_leads"])
    assert reg["child_u"]["lifecycle"] == LeadLifecycle.DISCOVERED.value
    assert reg["child_u"]["lifecycle"] != LeadLifecycle.COMMITTED.value

    for bucket in ("top_active_leads", "urgent_or_stale_leads", "npc_relevant_leads"):
        assert all(r["id"] != "old_m" for r in out[bucket])

    recent_ids = [r["id"] for r in out["recent_lead_changes"]]
    assert "old_m" in recent_ids
    assert "stale_me" in recent_ids
    assert "child_u" in recent_ids


@pytest.mark.unit
def test_missing_ref_after_reconcile_prompt_context_still_builds():
    src = resolve_lead(
        create_lead(title="S", summary="", id="src_x", unlocks=["nope"]),
        resolution_type="z",
        turn=1,
    )
    orphan = create_lead(title="O", summary="", id="orphan_x", superseded_by="ghost")
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 2,
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
        SESSION_LEAD_REGISTRY_KEY: {"src_x": src, "orphan_x": orphan},
    }
    reconcile_session_lead_progression(session, turn=2)
    out = build_authoritative_lead_prompt_context(
        session, world={}, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    assert isinstance(out["top_active_leads"], list)
    assert isinstance(out["follow_up_pressure_from_leads"], dict)


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


@pytest.mark.unit
def test_build_narration_context_narration_visibility_minimal_export():
    hidden_text = "the baron is the cult leader"
    discover_text = "loose brick in the fireplace"
    inner = {
        "id": "test_scene",
        "visible_facts": ["Banner hangs above the door."],
        "discoverable_clues": [{"text": discover_text}],
        "hidden_facts": [hidden_text],
        "exits": [],
        "enemies": [],
    }
    session = _session_with_registry()
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_gate_guard",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            scene={"scene": inner},
            public_scene={
                "id": "test_scene",
                "visible_facts": inner["visible_facts"],
                "exits": [],
                "enemies": [],
            },
            gm_only_hidden_facts=[hidden_text],
        )
    )
    assert "narration_visibility" in ctx
    assert ctx["discoverable_hinting"] is True
    nv = ctx["narration_visibility"]
    assert "visible_entities" in nv and isinstance(nv["visible_entities"], list)
    assert "visible_facts" in nv and isinstance(nv["visible_facts"], list)
    assert nv["rules"] == {
        "no_unseen_entities": True,
        "no_hidden_facts": True,
        "no_undiscovered_facts": True,
    }
    for forbidden in (
        "visible_entity_aliases",
        "hidden_fact_strings",
        "discoverable_fact_strings",
        "hidden_facts",
    ):
        assert forbidden not in nv
    assert "banner hangs above the door" in nv["visible_facts"]
    assert hidden_text.lower() not in nv["visible_facts"]
    assert discover_text.lower() not in nv["visible_facts"]
    assert nv.get("active_interlocutor_id") == "npc_gate_guard"
    instr = "\n".join(ctx["instructions"])
    assert "MUST NOT reference entities outside narration_visibility.visible_entities" in instr
    assert "MUST NOT assert facts outside narration_visibility.visible_facts" in instr
    assert "discoverable_hinting is true" in instr
    lr = ctx["scene"]["layering_rules"]
    assert "only visible facts may be directly asserted" in lr["visible_facts"].lower()


@pytest.mark.unit
def test_build_narration_context_exports_first_mention_contract_and_instructions():
    ctx = build_narration_context(**_narration_minimal_kwargs())

    assert "first_mention_contract" in ctx
    assert ctx["first_mention_contract"] == {
        "enabled": True,
        "requires_explicit_intro": True,
        "requires_grounding": True,
        "disallow_pronoun_first_reference": True,
        "disallow_unearned_familiarity": True,
    }

    instr = "\n".join(ctx["instructions"]).lower()
    assert "first reference to any entity must be explicit" in instr
    assert "first reference must use a visible name or a visible descriptor" in instr
    assert "first reference must include grounding by location, behavior, or relation" in instr
    assert "pronouns may be used only after explicit introduction" in instr
    assert "unearned familiarity phrases" in instr
    assert "unless supported by narration_visibility.visible_facts" in instr


@pytest.mark.unit
def test_build_narration_context_keeps_narration_visibility_separate_from_first_mention_contract():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    nv = ctx["narration_visibility"]

    assert set(nv.keys()) == {
        "visible_entities",
        "active_interlocutor_id",
        "visible_facts",
        "rules",
    }
    assert "first_mention_contract" in ctx
    assert "first_mention_contract" not in nv
    assert "requires_explicit_intro" not in nv
    assert "disallow_pronoun_first_reference" not in nv


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
    assert "interlocutor_lead_context" in ctx
    assert "interlocutor_lead_behavior_hints" in ctx
    assert isinstance(ctx["interlocutor_lead_behavior_hints"], list)
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


def test_build_narration_context_filters_terminal_pending_leads_from_prompt_export():
    session = _session_with_registry(
        {
            "id": "done_pl",
            "title": "Done",
            "status": LeadStatus.RESOLVED.value,
            "lifecycle": LeadLifecycle.RESOLVED.value,
            "resolution_type": "confirmed",
            "resolved_at_turn": 1,
        }
    )
    pending = [
        {
            "clue_id": "c",
            "authoritative_lead_id": "done_pl",
            "text": "Should not surface as active",
            "leads_to_scene": "x",
        }
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            scene_runtime={"pending_leads": pending},
            pending_leads=pending,
        )
    )
    scene_block = ctx["scene"]
    assert scene_block["pending_leads"] == []
    assert scene_block["runtime"]["pending_leads"] == []


def test_build_narration_context_repeat_continuity_alignment_across_export_and_hints():
    session = _session_with_registry(
        {
            "id": "lead_smuggler_drop",
            "title": "Smuggler Drop",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 11
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_dockmaster",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_smuggler_drop",
        turn=10,
        disclosure_level="hinted",
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_smuggler_drop",
        turn=11,
        disclosure_level="hinted",
    )
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc = ctx["interlocutor_lead_context"]
    assert [r["lead_id"] for r in ilc["recently_discussed_with_npc"]] == ["lead_smuggler_drop"]
    assert ilc["repeat_suppression"]["has_recent_repeat_risk"] is True
    assert ilc["repeat_suppression"]["recent_lead_ids"] == ["lead_smuggler_drop"]
    assert any("prefer advancement" in h and "over repetition" in h for h in ctx["interlocutor_lead_behavior_hints"])


def test_build_narration_context_recent_discussion_flags_repeat_risk_without_filtering_npc_relevant_leads():
    session = _session_with_registry(
        {
            "id": "lead_recent",
            "title": "Recent Lead",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "related_npc_ids": ["npc_dockmaster"],
            "priority": 1,
        },
        {
            "id": "lead_other",
            "title": "Other Lead",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "related_npc_ids": ["npc_dockmaster"],
            "priority": 0,
        },
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 11
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_dockmaster",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_recent",
        turn=10,
        disclosure_level="hinted",
    )
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc = ctx["interlocutor_lead_context"]
    assert [r["lead_id"] for r in ilc["recently_discussed_with_npc"]] == ["lead_recent"]
    assert ilc["repeat_suppression"]["recent_lead_ids"] == ["lead_recent"]
    assert {r["id"] for r in ctx["lead_context"]["npc_relevant_leads"]} == {
        "lead_recent",
        "lead_other",
    }


def test_build_narration_context_disclosure_upgrade_and_acknowledgement_behavior_alignment():
    session = _session_with_registry(
        {
            "id": "lead_patrol",
            "title": "Missing Patrol",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        },
        {
            "id": "lead_unack",
            "title": "Unacknowledged Lead",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        },
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 9
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_dockmaster",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_patrol",
        turn=7,
        disclosure_level="hinted",
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_patrol",
        turn=8,
        disclosure_level="explicit",
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_patrol",
        turn=9,
        disclosure_level="hinted",
        acknowledged=True,
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_unack",
        turn=9,
        disclosure_level="hinted",
    )

    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc = ctx["interlocutor_lead_context"]
    by_id = {r["lead_id"]: r for r in ilc["introduced_by_npc"]}
    assert by_id["lead_patrol"]["disclosure_level"] == "explicit"
    assert by_id["lead_patrol"]["player_acknowledged"] is True
    assert by_id["lead_unack"]["player_acknowledged"] is False
    assert [r["lead_id"] for r in ilc["introduced_by_npc"]][:2] == ["lead_unack", "lead_patrol"]
    hints = ctx["interlocutor_lead_behavior_hints"]
    assert any("already discussed explicitly as brand-new" in h for h in hints)
    assert any("treat it as shared context" in h for h in hints)


def test_build_narration_context_npc_slice_strict_scoping_for_context_and_hints():
    session = _session_with_registry(
        {
            "id": "lead_gate_watch",
            "title": "Gate Watch",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 12
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_a",
        lead_id="lead_gate_watch",
        turn=12,
        disclosure_level="hinted",
        acknowledged=True,
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_b",
        lead_id="lead_gate_watch",
        turn=12,
        disclosure_level="hinted",
        acknowledged=False,
    )

    session["interaction_context"] = {
        "active_interaction_target_id": "npc_a",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    ctx_a = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc_a = ctx_a["interlocutor_lead_context"]
    assert ilc_a["active_npc_id"] == "npc_a"
    assert [r["lead_id"] for r in ilc_a["introduced_by_npc"]] == ["lead_gate_watch"]
    assert ilc_a["introduced_by_npc"][0]["player_acknowledged"] is True
    assert any("shared context" in h for h in ctx_a["interlocutor_lead_behavior_hints"])

    session["interaction_context"]["active_interaction_target_id"] = "npc_b"
    ctx_b = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc_b = ctx_b["interlocutor_lead_context"]
    assert ilc_b["active_npc_id"] == "npc_b"
    assert [r["lead_id"] for r in ilc_b["introduced_by_npc"]] == ["lead_gate_watch"]
    assert ilc_b["introduced_by_npc"][0]["player_acknowledged"] is False
    assert not any("shared context" in h for h in ctx_b["interlocutor_lead_behavior_hints"])


def test_build_narration_context_terminal_missing_and_neutral_paths_are_safe():
    session = _session_with_registry(
        {
            "id": "lead_done",
            "title": "Done Lead",
            "status": LeadStatus.RESOLVED.value,
            "lifecycle": LeadLifecycle.RESOLVED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 14
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_dockmaster",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_done",
        turn=14,
        disclosure_level="explicit",
    )
    _record_discussion(
        session,
        scene_id="scene_docks",
        npc_id="npc_dockmaster",
        lead_id="lead_missing",
        turn=14,
        disclosure_level="hinted",
    )
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    ilc = ctx["interlocutor_lead_context"]
    assert ilc["introduced_by_npc"] == []
    assert ilc["unacknowledged_from_npc"] == []
    assert ilc["recently_discussed_with_npc"] == []
    assert ilc["repeat_suppression"] == {
        "has_recent_repeat_risk": False,
        "recent_lead_ids": [],
        "prefer_progress_over_restatement": False,
    }
    assert [r["lead_id"] for r in ilc["recent_terminal_reference"]] == ["lead_done"]
    assert ctx["interlocutor_lead_behavior_hints"] == []

    session["interaction_context"]["active_interaction_target_id"] = None
    neutral_ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
        )
    )
    assert neutral_ctx["interlocutor_lead_context"] == {
        "active_npc_id": None,
        "introduced_by_npc": [],
        "unacknowledged_from_npc": [],
        "recently_discussed_with_npc": [],
        "recent_terminal_reference": [],
        "repeat_suppression": {
            "has_recent_repeat_risk": False,
            "recent_lead_ids": [],
            "prefer_progress_over_restatement": False,
        },
    }
    assert neutral_ctx["interlocutor_lead_behavior_hints"] == []


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
    assert set(fup["from_leads"].keys()) == set(_expected_follow_up_pressure_from_leads().keys())
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
    assert fup == {"from_leads": _expected_follow_up_pressure_from_leads(has_pursued=True)}
    assert "pressed" not in fup


def test_follow_up_pressure_none_when_no_log_and_no_lead_booleans():
    session = _session_with_registry()
    ctx = build_narration_context(**_narration_minimal_kwargs(session=session))
    assert ctx["follow_up_pressure"] is None


def test_social_lock_merges_log_escalation_when_answer_pressure_followup():
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
    assert fup["from_leads"] == _expected_follow_up_pressure_from_leads(
        has_pursued=True, npc_has_relevant=True
    )
    assert fup.get("pressed") is True


@pytest.mark.unit
def test_prompt_contract_owner_detects_anchor_followup_for_recent_milestone_explanation():
    prev_gm = (
        "The watch captain jerks his chin toward the treeline. Most folk hurry past the old milestone; "
        "few linger after dark."
    )
    compact = [{"player_input": "What marks the patrol route?", "gm_snippet": prev_gm}]
    ap = _answer_pressure_details("What's so special about the old milestone?", compact)
    assert ap["explanation_of_recent_anchor_followup"] is True
    assert ap["anchor_followup_detected"] is True
    assert ap["answer_pressure_followup_detected"] is True
    assert "milestone" in ap["anchor_tokens_extracted"] or "old milestone" in ap["anchor_tokens_extracted"]
    assert ap["anchor_token_matched"] == "milestone"
    assert ap["answer_pressure_family"] == "explanation_of_recent_anchor_followup"


@pytest.mark.unit
def test_prompt_contract_owner_matches_short_anchor_followups_to_recent_npc_tokens():
    g1 = _answer_pressure_details(
        "Why the milestone?",
        [{"player_input": "x", "gm_snippet": "Keep clear of the old milestone after dusk; caravans don't stop there."}],
    )
    assert g1["anchor_followup_detected"] is True
    assert g1["anchor_token_matched"] == "milestone"

    g2 = _answer_pressure_details(
        "Ghost stories?",
        [{"player_input": "x", "gm_snippet": "Sailors swap ghost stories about the alley behind the seal-house."}],
    )
    assert g2["anchor_followup_detected"] is True
    assert g2["anchor_token_matched"] == "ghost"


@pytest.mark.unit
def test_prompt_contract_owner_detects_deictic_anchor_followups():
    prev_gm = "Everyone knows the checkpoint by the east pier; guards gossip about what happened there last week."
    ap = _answer_pressure_details(
        "What happened there?",
        [{"player_input": "Tell me about the pier.", "gm_snippet": prev_gm}],
    )
    assert ap["anchor_followup_detected"] is True
    assert "checkpoint" in ap["anchor_tokens_extracted"]


@pytest.mark.unit
def test_prompt_contract_owner_requires_anchor_overlap_for_anchor_followups():
    prev_gm = "The road is muddy and the wind is cold tonight."
    ap = _answer_pressure_details(
        "What's the tax rate in the capital?",
        [{"player_input": "How is business?", "gm_snippet": prev_gm}],
    )
    assert ap["anchor_followup_detected"] is False
    assert ap["explanation_of_recent_anchor_followup"] is False
    assert ap["anchor_tokens_extracted"] == []


@pytest.mark.unit
def test_prompt_contract_owner_ignores_non_questions_even_when_anchor_words_repeat():
    ap = _answer_pressure_details(
        "The old milestone is just a rock.",
        [{"player_input": "x", "gm_snippet": "Folk call it the old milestone near the north bend."}],
    )
    assert ap["anchor_followup_detected"] is False


@pytest.mark.unit
def test_prompt_contract_owner_excludes_generic_roles_from_anchor_followup_detection():
    prev_gm = (
        "The Tavern Runner squints at you. The watch captain said little; travelers hurry past "
        "the tavern sign and the road stays quiet."
    )
    compact = [{"player_input": "Anything unusual on the north road tonight?", "gm_snippet": prev_gm}]
    ap = _answer_pressure_details("What did the captain say exactly?", compact)
    assert ap["explanation_of_recent_anchor_followup"] is False
    assert ap["anchor_followup_detected"] is False
    assert "captain" not in ap["anchor_tokens_extracted"]
    assert "tavern" not in ap["anchor_tokens_extracted"]
    assert "runner" not in ap["anchor_tokens_extracted"]


@pytest.mark.unit
def test_prompt_contract_owner_excludes_generic_roles_from_anchor_token_extraction():
    s = "The watch captain jerks his chin; the Tavern Runner listens by the tavern door."
    toks = _extract_npc_introduced_anchor_tokens(s)
    assert "captain" not in toks
    assert "runner" not in toks
    assert "tavern" not in toks


@pytest.mark.unit
def test_prompt_contract_owner_does_not_pair_unmatched_role_words_with_real_clues():
    prev_gm = "The guard at the checkpoint shrugs; runners come and go."
    compact = [{"player_input": "Tell me about the pier.", "gm_snippet": prev_gm}]
    for q in ("Why the runner?", "What about the captain?", "And the guard?"):
        ap = _answer_pressure_details(q, compact)
        assert ap["explanation_of_recent_anchor_followup"] is False, q
        assert ap["anchor_followup_detected"] is False, q


@pytest.mark.unit
def test_prompt_contract_owner_suppresses_uncertainty_hint_during_live_social_lock():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    world = default_world()
    scene = {
        "scene": {
            "id": "frontier_gate",
            "visible_facts": [],
            "discoverable_clues": [],
            "exits": [],
            "enemies": [],
        }
    }
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            world=world,
            session=session,
            scene=scene,
            public_scene=scene["scene"],
            user_text="What do you know?",
            resolution={"kind": "question", "social": {"npc_id": "tavern_runner"}},
            scene_runtime={"momentum_exchanges_since": 3, "momentum_next_due_in": 2},
            intent={"labels": ["social_probe"]},
            uncertainty_hint={"speaker": {"role": "narrator"}, "turn_context": {}},
        )
    )
    assert ctx["uncertainty_hint"] is None
    assert ctx["response_policy"]["uncertainty"]["enabled"] is False
    assert ctx["response_policy"]["prefer_scene_momentum"] is False
    assert any("SOCIAL INTERACTION LOCK" in line for line in ctx["instructions"])


@pytest.mark.unit
def test_prompt_contract_owner_filters_absent_lead_salience_from_interlocutor_export():
    session = _session_with_registry(
        {
            "id": "lead_runner_thread",
            "title": "Runner Thread",
            "summary": "Local watch movement near the gate.",
            "related_npc_ids": ["tavern_runner"],
        },
        {
            "id": "lead_aldric_thread",
            "title": "Aldric Thread",
            "summary": "Lord Aldric influence over patrol choices.",
            "related_npc_ids": ["lord_aldric"],
        },
    )
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["turn_counter"] = 6
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
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
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            user_text="Runner, does Aldric still inspect the east road?",
            scene_runtime={},
            pending_leads=[],
            recent_log=[],
            recent_log_for_prompt=[],
            intent={"labels": ["question"]},
        )
    )
    ilc = ctx["interlocutor_lead_context"]
    assert ilc["active_npc_id"] == "tavern_runner"
    assert all(r.get("lead_id") != "lead_aldric_thread" for r in ilc["introduced_by_npc"])
    assert all("Aldric" not in h for h in (ctx.get("interlocutor_lead_behavior_hints") or []))


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


@pytest.mark.unit
def test_build_narration_context_exports_anti_railroading_contract():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    assert "anti_railroading_contract" in ctx
    arc = ctx["anti_railroading_contract"]
    assert isinstance(arc, dict)
    assert arc.get("enabled") is True
    assert "forbid_player_decision_override" in arc
    assert "surfaced_lead_ids" in arc and "surfaced_lead_labels" in arc
    policy = ctx["response_policy"]
    assert policy.get("anti_railroading") is arc
    pd = ctx.get("prompt_debug") or {}
    assert "anti_railroading" in pd


@pytest.mark.unit
def test_anti_railroading_contract_reflects_surfaced_leads_from_prompt_context_state():
    session = _session_with_registry(
        {
            "id": "reg_lead_x",
            "title": "Harbor Thread",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
            "priority": 2,
            "last_updated_turn": 1,
        }
    )
    session["turn_counter"] = 3
    session["follow_surface"] = {"lead_ids": ["fs_surface"], "labels": ["Wharf rumor"]}
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            pending_leads=[
                {"authoritative_lead_id": "reg_lead_x", "surface": "pending beat"},
            ],
        )
    )
    arc = ctx["anti_railroading_contract"]
    ids = list(arc.get("surfaced_lead_ids") or [])
    labels = list(arc.get("surfaced_lead_labels") or [])
    assert "reg_lead_x" in ids
    assert "fs_surface" in ids
    assert "Harbor Thread" in labels
    assert "Wharf rumor" in labels


@pytest.mark.unit
def test_anti_railroading_instruction_text_differentiates_constraint_lead_and_forced_direction():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    block = "\n".join(ctx["instructions"])
    assert "HARD WORLD CONSTRAINT" in block
    assert "SALIENT LEAD" in block
    assert "FORCED PLAYER DIRECTION" in block


@pytest.mark.unit
def test_anti_railroading_instructions_preserve_explicit_commitment_exception():
    ctx = build_narration_context(
        **_narration_minimal_kwargs(user_text="I'll go to the harbor and look for the contact.")
    )
    arc = ctx["anti_railroading_contract"]
    assert arc.get("allow_commitment_language_when_player_explicitly_committed") is True
    block = "\n".join(ctx["instructions"])
    assert "allow_commitment_language_when_player_explicitly_committed" in block
    assert "explicit commitment" in block.lower()


@pytest.mark.unit
def test_anti_railroading_instructions_forbid_only_unjustified_forced_direction():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    block = "\n".join(ctx["instructions"]).lower()
    assert "not globally banned" in block
    assert "unjustified forced direction" in block
    assert "never use directional" not in block


@pytest.mark.unit
def test_context_separation_contract_wired_to_response_policy_and_payload():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    rp = ctx["response_policy"]
    assert "context_separation" in rp
    assert rp["context_separation"] is ctx["context_separation_contract"]
    assert isinstance(rp["context_separation"], dict)
    assert "debug_flags" in rp["context_separation"]
    pd = ctx["prompt_debug"]
    assert "context_separation" in pd
    assert pd["context_separation"].get("enabled") is True


@pytest.mark.unit
def test_prompt_contract_owner_materializes_response_policy_bundle_for_downstream_consumers():
    policy = build_response_policy(
        narration_obligations={"scene_momentum_due": True},
        player_text="I study the gate.",
        resolution={"kind": "observe", "prompt": "I study the gate."},
        session_view={"turn_counter": 2, "visited_scene_count": 1},
        recent_log_compact=[],
    )
    assert policy["rule_priority_order"] == [label for _, label in RESPONSE_RULE_PRIORITY]
    assert isinstance(policy["response_delta"], dict)
    assert isinstance(policy["answer_completeness"], dict)
    assert policy["uncertainty"]["enabled"] is True


@pytest.mark.unit
def test_build_narration_context_surfaces_interaction_continuity_contract():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    ic = ctx.get("interaction_continuity_contract")
    assert isinstance(ic, dict)
    assert ic.get("continuity_strength") in ("none", "soft", "strong")
    assert isinstance(ic.get("enabled"), bool)
    assert "anchored_interlocutor_id" in ic
    assert "continuity_reasons" in ic and isinstance(ic["continuity_reasons"], list)
    assert "break_signals_present" in ic and isinstance(ic["break_signals_present"], list)
    rp = ctx["response_policy"]
    assert rp.get("interaction_continuity") is ic
    pd = ctx.get("prompt_debug") or {}
    assert "interaction_continuity" in pd
    assert "continuity_strength" in pd["interaction_continuity"]


@pytest.mark.unit
def test_context_separation_instruction_priority_and_pressure_rules():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    block = "\n".join(ctx["instructions"])
    assert "CONTEXT SEPARATION (POLICY)" in block
    assert "local exchange first" in block.lower()
    assert "briefly color" in block.lower()
    assert "must not replace the substantive reply" in block.lower()
    assert "not from generic scene mood alone" in block.lower()


@pytest.mark.unit
def test_context_separation_instructions_no_social_probe_exemption_heuristic():
    """Instructions must not encode interaction-kind shortcuts (e.g. social_probe as auto world-focus)."""
    session = _session_with_registry()
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_x",
        "active_interaction_kind": "social_probe",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            user_text="What do you charge for a room?",
            resolution={"kind": "social_probe"},
            intent={"labels": ["social_probe"]},
        )
    )
    sep_lines = [ln for ln in ctx["instructions"] if "CONTEXT SEPARATION (POLICY)" in ln]
    assert len(sep_lines) == 1
    low = sep_lines[0].lower()
    assert "social_probe" not in low
    assert "investigation" not in low
    assert "travel" not in low
    cs = ctx["response_policy"]["context_separation"]
    assert cs.get("interaction_kind") == "social_probe"
    assert cs.get("debug_flags", {}).get("pressure_focus_allowed") is False


@pytest.mark.unit
def test_context_separation_debug_mirror_lists_explicit_relevance_not_mood():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    pd_cs = ctx["prompt_debug"]["context_separation"]
    assert "pressure_focus_allowed" in pd_cs


@pytest.mark.unit
def test_player_facing_narration_purity_contract_wired_to_response_policy_payload_and_debug():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    c = ctx["player_facing_narration_purity_contract"]
    rp = ctx["response_policy"]
    assert rp["player_facing_narration_purity"] is c
    assert isinstance(c, dict)
    assert c.get("enabled") is True
    assert c.get("diegetic_only") is True
    assert c.get("forbid_scaffold_headers") is True
    assert c.get("forbid_coaching_language") is True
    pd = ctx["prompt_debug"]["player_facing_narration_purity"]
    assert pd.get("enabled") is True
    assert "forbid_scaffold_headers" in pd


@pytest.mark.unit
def test_player_facing_narration_purity_instruction_text_forbids_scaffold_menus_and_coaching():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    block = "\n".join(ctx["instructions"])
    low = block.lower()
    assert "PLAYER-FACING NARRATION PURITY (POLICY)" in block
    assert "response_policy.player_facing_narration_purity" in block
    assert "consequence/opportunity" in block
    assert "speak only in player-facing diegetic prose" in low
    assert "engine/ui guidance" in low
    assert "menu labels" in low
    assert "bulleted/numbered choice lists" in block


@pytest.mark.unit
def test_player_facing_narration_purity_instruction_order_after_context_separation_before_anchoring():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    text = "\n".join(ctx["instructions"])
    idx_sep = text.find("CONTEXT SEPARATION (POLICY)")
    idx_purity = text.find("PLAYER-FACING NARRATION PURITY (POLICY)")
    idx_anchor = text.find("SCENE ANCHORING (POLICY)")
    assert 0 <= idx_sep < idx_purity < idx_anchor


# --- Objective #15: conversational memory window (prompt integration) ---------


@pytest.mark.unit
def test_narration_payload_includes_conversational_memory_window_and_selection():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    assert "conversational_memory_window" in ctx
    assert "selected_conversational_memory" in ctx
    assert isinstance(ctx["conversational_memory_window"], dict)
    assert isinstance(ctx["selected_conversational_memory"], list)
    pd = ctx.get("prompt_debug") or {}
    cm = pd.get("conversational_memory") or {}
    assert "candidate_count" in cm and "selected_count" in cm
    assert cm["selected_count"] == len(ctx["selected_conversational_memory"])


@pytest.mark.unit
def test_conversational_memory_window_mirrored_on_response_policy_object_identity():
    ctx = build_narration_context(**_narration_minimal_kwargs())
    win = ctx["conversational_memory_window"]
    rp = ctx.get("response_policy") or {}
    assert rp.get("conversational_memory_window") is win
    assert "selected_conversational_memory" not in rp


@pytest.mark.unit
@patch("game.prompt_context._compress_recent_log")
def test_response_policy_path_uses_compress_recent_log(mock_compress):
    """Policy / lead slices use compressed log; selector still receives the full recent_log_for_prompt."""
    mock_compress.return_value = [{"player_input": "c1", "gm_snippet": "g1"}]
    rich = [
        {
            "log_meta": {"player_input": "alpha " * 80, "turn_counter": 3},
            "gm_output": {"player_facing_text": "gm " * 100},
            "extra_payload": {"should_not": "appear_in_policy_compress_input"},
        }
    ]
    ctx = build_narration_context(**_narration_minimal_kwargs(recent_log_for_prompt=rich))
    mock_compress.assert_called_once()
    assert mock_compress.call_args[0][0] is rich
    pd = ctx.get("prompt_debug") or {}
    assert pd.get("conversational_memory", {}).get("candidate_count", 0) >= 1
    assert ctx["recent_log"] != mock_compress.return_value


@pytest.mark.unit
def test_payload_recent_log_is_selector_shaped_not_raw_duplicate_dump():
    """recent_log in the prompt payload is derived from selection + extras, not a parallel full dump."""
    log = [
        {
            "log_meta": {"player_input": "p0", "turn_counter": 5},
            "gm_output": {"player_facing_text": "g0"},
        },
        {
            "log_meta": {"player_input": "p1", "turn_counter": 6},
            "gm_output": {"player_facing_text": "g1"},
        },
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(session={"turn_counter": 6}, recent_log_for_prompt=log)
    )
    for row in ctx["recent_log"]:
        assert set(row.keys()) <= {"player_input", "gm_snippet"}
    assert len(ctx["recent_log"]) == len(ctx["selected_conversational_memory"])
    assert len(ctx["recent_log"]) <= CONVERSATIONAL_MEMORY_SOFT_LIMIT


@pytest.mark.unit
def test_compress_recent_log_trims_to_player_snippet_shape():
    raw = [
        {"log_meta": {"player_input": "  ask  "}, "gm_output": {"player_facing_text": "narration " * 50}},
    ]
    out = _compress_recent_log(raw)
    long_gm = "narration " * 50
    assert out[0]["player_input"] == "  ask  "[:300]
    assert out[0]["gm_snippet"] == long_gm[:200]
    assert len(out[0]["gm_snippet"]) == 200


@pytest.mark.unit
def test_recent_log_payload_entries_match_selected_kinds_for_mixed_candidates():
    """Interlocutor lead rows can contribute when scored into the window."""
    session = _session_with_registry(
        {
            "id": "lead_x",
            "title": "Harbor Smuggling",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 20
    record_npc_lead_discussion(
        session,
        "scene_docks",
        "npc_dock",
        "lead_x",
        disclosure_level="hinted",
        turn_counter=18,
    )
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_dock",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    log = [
        {
            "log_meta": {"player_input": "hello", "turn_counter": 19},
            "gm_output": {"player_facing_text": "hi"},
        }
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
            recent_log_for_prompt=log,
        )
    )
    kinds = [x.get("kind") for x in ctx["selected_conversational_memory"]]
    assert "recent_turn" in kinds
    assert "npc_lead_discussion" in kinds


@pytest.mark.unit
def test_runtime_recent_contextual_leads_can_enter_selection():
    session = _session_with_registry()
    session["turn_counter"] = 30
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            scene_runtime={
                "recent_contextual_leads": [
                    {
                        "subject": "River Crossing",
                        "key": "crossing:01",
                        "last_turn": 28,
                        "kind": "travel",
                    }
                ]
            },
        )
    )
    kinds = [x.get("kind") for x in ctx["selected_conversational_memory"]]
    assert "contextual_thread" in kinds


@pytest.mark.unit
@patch("game.prompt_context._extract_explicit_reintroductions")
def test_reintroduced_stale_entity_can_surface_selected_memory(mock_re):
    """Stale NPC re-grounded via explicit reintroduction lists gets a scoring bonus (contract wiring)."""
    mock_re.return_value = (["npc_stale"], [], {"matched_entity_ids": ["npc_stale"]})
    session = _session_with_registry(
        {
            "id": "lead_stale",
            "title": "Cold Harbor Lead",
            "status": LeadStatus.ACTIVE.value,
            "lifecycle": LeadLifecycle.COMMITTED.value,
        }
    )
    session["active_scene_id"] = "scene_docks"
    session["turn_counter"] = 50
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_stale",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    record_npc_lead_discussion(
        session,
        "scene_docks",
        "npc_stale",
        "lead_stale",
        disclosure_level="hinted",
        turn_counter=5,
    )
    ctx = build_narration_context(
        **_narration_minimal_kwargs(
            session=session,
            world={},
            public_scene={"id": "scene_docks", "visible_facts": [], "exits": [], "enemies": []},
            user_text="we discussed the harbor earlier",
            recent_log_for_prompt=[],
        )
    )
    win = ctx["conversational_memory_window"]
    assert "npc_stale" in (win.get("explicit_reintroduced_entity_ids") or [])
    sel = ctx["selected_conversational_memory"]
    assert any(
        "npc_stale" in (s.get("entity_ids") or []) and s.get("kind") == "npc_lead_discussion" for s in sel
    )


@pytest.mark.unit
@patch("game.prompt_context._extract_explicit_reintroductions")
def test_non_reintroduced_stale_thread_can_rank_out(mock_re):
    mock_re.return_value = ([], [], {})
    session = _session_with_registry()
    session["turn_counter"] = 100
    # Only the last MAX_RECENT_LOG lines become candidates; include a very old exchange there
    # so it competes with newer lines and sinks to the bottom of the ranked window.
    log = [
        {
            "log_meta": {"player_input": "stale side", "turn_counter": 10},
            "gm_output": {"player_facing_text": "noise"},
        },
        {
            "log_meta": {"player_input": "mid96", "turn_counter": 96},
            "gm_output": {"player_facing_text": "a"},
        },
        {
            "log_meta": {"player_input": "mid97", "turn_counter": 97},
            "gm_output": {"player_facing_text": "b"},
        },
        {
            "log_meta": {"player_input": "mid98", "turn_counter": 98},
            "gm_output": {"player_facing_text": "c"},
        },
        {
            "log_meta": {"player_input": "fresh", "turn_counter": 99},
            "gm_output": {"player_facing_text": "now"},
        },
    ]
    ctx = build_narration_context(
        **_narration_minimal_kwargs(session=session, recent_log_for_prompt=log)
    )
    sel = ctx["selected_conversational_memory"]
    assert sel
    assert sel[0]["source_turn"] == 99
    by_turn = {s["source_turn"]: s for s in sel if isinstance(s.get("source_turn"), int)}
    assert by_turn[10]["score"] < by_turn[99]["score"]
    assert sel[-1]["source_turn"] == 10
