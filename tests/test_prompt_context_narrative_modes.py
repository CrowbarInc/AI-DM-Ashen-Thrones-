"""Mode-aware prompt construction (Objective #6): narrative_mode_contract drives structural deltas."""

from __future__ import annotations

import pytest

from game import ctir
from game.ctir_runtime import attach_ctir, detach_ctir
from game.narrative_mode_contract import build_narrative_mode_contract
from game.prompt_context import _build_narrative_mode_instructions, build_narration_context


def _minimal_narration_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 5,
            "visited_scene_ids": ["s0", "s1"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Continue.",
        "resolution": {"kind": "travel", "label": "move", "action_id": "raw-walk"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    base.update(overrides)
    return base


def _attach_ctir(session: dict, c: dict) -> None:
    attach_ctir(session, c)


def _instr_blob(ctx: dict) -> str:
    return "\n".join(ctx.get("instructions") or [])


@pytest.mark.parametrize(
    "mode,contract_kwargs,required_markers,forbidden_markers",
    [
        (
            "opening",
            {"narration_obligations": {"is_opening_scene": True}},
            ("struct:opening:first_impression", "struct:contract_obligation:require_scene_grounding"),
            ("struct:continuation:suppress_language_that_resets_the_scene",),
        ),
        (
            "continuation",
            {},
            ("struct:continuation:carry_active_thread_forward",),
            ("struct:opening:first_impression",),
        ),
        (
            "action_outcome",
            {
                "ctir": {
                    "resolution": {
                        "kind": "attack",
                        "skill_check": {"dc": 12},
                        "authoritative_outputs": {},
                    }
                }
            },
            ("struct:action_outcome:lead_early", "struct:contract_obligation:lead_with_outcome_signal"),
            ("struct:opening:first_impression",),
        ),
        (
            "dialogue",
            {
                "narration_obligations": {"active_npc_reply_expected": True},
                "response_policy": {"response_type_contract": {"required_response_type": "dialogue"}},
            },
            ("struct:dialogue:preserve_active_interlocutor", "struct:contract_obligation:preserve_interlocutor_continuity"),
            ("struct:opening:first_impression",),
        ),
        (
            "transition",
            {
                "narration_obligations": {"must_advance_scene": True},
            },
            ("struct:transition:foreground_departure", "struct:contract_obligation:foreground_scene_change"),
            ("struct:continuation:suppress_language_that_resets_the_scene",),
        ),
        (
            "exposition_answer",
            {"response_policy": {"answer_completeness": {"answer_required": True, "answer_must_come_first": True}}},
            ("struct:exposition_answer:lead_with_clear_information", "struct:contract_obligation:answer_first"),
            ("struct:action_outcome:lead_early",),
        ),
    ],
)
def test_build_narrative_mode_instructions_distinct_by_contract_mode(
    mode: str,
    contract_kwargs: dict,
    required_markers: tuple[str, ...],
    forbidden_markers: tuple[str, ...],
) -> None:
    c = build_narrative_mode_contract(**contract_kwargs)
    assert c.get("mode") == mode, (mode, c)
    rp = dict(contract_kwargs.get("response_policy") or {})
    if mode == "dialogue" and "social_response_structure" not in rp:
        rp["social_response_structure"] = {"enabled": True}
    lines = _build_narrative_mode_instructions(
        narrative_mode_contract=c,
        response_policy=rp or None,
        narration_obligations=contract_kwargs.get("narration_obligations"),
        resolution_sem=(contract_kwargs.get("ctir") or {}).get("resolution")
        if isinstance(contract_kwargs.get("ctir"), dict)
        else None,
    )
    blob = "\n".join(lines)
    for frag in required_markers:
        assert frag in blob, (mode, frag, blob)
    for frag in forbidden_markers:
        assert frag not in blob, (mode, frag, blob)
    assert "generic narration" not in blob.lower()


def test_opening_scene_with_player_question_stays_opening_mode_and_merges_answer_pressure() -> None:
    """Opening precedence beats direct-question / answer_completeness pressure for narrative_mode only."""
    session = dict(_minimal_narration_kwargs()["session"])
    session["turn_counter"] = 1
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="Who runs the docks?",
        builder_source="tests.narrative_modes.opening_question",
        resolution={"kind": "question", "label": "ask", "action_id": "q1", "authoritative_outputs": {}, "metadata": {}},
        intent={"raw_text": "Who runs the docks?", "labels": ["general"], "mode": "social"},
        interaction={"active_target_id": "npc_x", "interaction_mode": "social", "interaction_kind": "question"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="Who runs the docks?",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "opening"
    blob = _instr_blob(ctx)
    assert "struct:opening:first_impression" in blob
    assert "struct:opening:answer_completeness_if_active" in blob
    assert "struct:exposition_answer:lead_with_clear_information" not in blob


def test_transition_beats_active_npc_reply_pressure_for_narrative_mode() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_x",
        "active_interaction_kind": "question",
        "interaction_mode": "social",
    }
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I push through the crowd into the hall.",
        builder_source="tests.narrative_modes.transition_vs_dialogue",
        resolution={
            "kind": "travel",
            "label": "enter",
            "state_changes": {"scene_transition_occurred": True},
        },
        intent={"labels": ["general"]},
        interaction={"active_target_id": "npc_x", "interaction_mode": "social", "interaction_kind": "question"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="I push through the crowd into the hall.",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "transition"
    blob = _instr_blob(ctx)
    assert "struct:transition:foreground_departure" in blob
    assert "struct:dialogue:preserve_active_interlocutor" not in blob


def test_opening_integration_excludes_continuation_framing() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    session["turn_counter"] = 1
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="I look around.",
        builder_source="tests.narrative_modes.opening",
        resolution={"kind": "observe", "label": "look"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session=session, user_text="I look around.", include_non_public_prompt_keys=True)
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "opening"
    blob = _instr_blob(ctx)
    assert "struct:opening:first_impression" in blob
    assert "struct:continuation:suppress_language_that_resets_the_scene" not in blob


def test_continuation_integration_suppresses_opening_framing_markers() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    session["turn_counter"] = 5
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I nod.",
        builder_source="tests.narrative_modes.continuation",
        resolution={"kind": "observe", "label": "nod"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session=session, user_text="I nod.", include_non_public_prompt_keys=True)
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "continuation"
    blob = _instr_blob(ctx)
    assert "struct:continuation:carry_active_thread_forward" in blob
    assert "struct:opening:first_impression" not in blob


def test_action_outcome_integration_has_result_first_guidance() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I strike.",
        builder_source="tests.narrative_modes.action_outcome",
        resolution={
            "kind": "attack",
            "label": "strike",
            "skill_check": {"outcome": "hit"},
            "authoritative_outputs": {},
        },
        intent={"labels": ["combat"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session=session, user_text="I strike.", include_non_public_prompt_keys=True)
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "action_outcome"
    blob = _instr_blob(ctx)
    assert "struct:action_outcome:lead_early" in blob


def test_dialogue_integration_has_speaker_continuity_guidance() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_x",
        "active_interaction_kind": "question",
        "interaction_mode": "social",
    }
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="What do you hear?",
        builder_source="tests.narrative_modes.dialogue",
        resolution={
            "kind": "question",
            "label": "ask",
            "action_id": "ctir-q",
            "authoritative_outputs": {},
            "metadata": {},
        },
        intent={"raw_text": "What do you hear?", "labels": ["general"], "mode": "social"},
        interaction={"active_target_id": "npc_x", "interaction_mode": "social", "interaction_kind": "question"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="What do you hear?",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "dialogue"
    blob = _instr_blob(ctx)
    assert "struct:dialogue:preserve_active_interlocutor" in blob


def test_transition_integration_has_scene_change_guidance() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I enter the hall.",
        builder_source="tests.narrative_modes.transition",
        resolution={
            "kind": "travel",
            "label": "enter",
            "state_changes": {"scene_transition_occurred": True},
        },
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="I enter the hall.",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "transition"
    blob = _instr_blob(ctx)
    assert "struct:transition:foreground_departure" in blob


def test_exposition_answer_integration_has_answer_first_guidance() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="When was the north gate sealed?",
        builder_source="tests.narrative_modes.exposition",
        resolution={"kind": "investigate", "label": "ask_history"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="When was the north gate sealed?",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    assert ctx.get("narrative_plan", {}).get("narrative_mode") == "exposition_answer"
    blob = _instr_blob(ctx)
    assert "struct:exposition_answer:lead_with_clear_information" in blob


def test_pending_check_does_not_emit_action_outcome_style_instructions() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I try to pick the lock.",
        builder_source="tests.narrative_modes.pending_check",
        resolution={
            "kind": "interact",
            "label": "pick_lock",
            "requires_check": True,
            "check_request": {"kind": "skill", "skill": "thieves_tools"},
        },
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(
                session=session,
                user_text="I try to pick the lock.",
                include_non_public_prompt_keys=True,
            )
        )
    finally:
        detach_ctir(session)
    plan = ctx.get("narrative_plan") or {}
    assert plan.get("narrative_mode") != "action_outcome"
    blob = _instr_blob(ctx)
    assert "struct:action_outcome:lead_early" not in blob


def test_prompt_debug_narrative_mode_instructions_is_compact() -> None:
    session = dict(_minimal_narration_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="Hello there.",
        builder_source="tests.narrative_modes.debug",
        resolution={"kind": "social_probe", "label": "greet"},
        intent={"labels": ["social"]},
        interaction={
            "active_target_id": "npc_x",
            "interaction_mode": "social",
            "interaction_kind": "social_probe",
        },
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir(session, c)
    try:
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session=session, user_text="Hello there.", include_non_public_prompt_keys=True)
        )
    finally:
        detach_ctir(session)
    dbg = (ctx.get("prompt_debug") or {}).get("narrative_mode_instructions") or {}
    assert dbg.get("present") is True
    assert dbg.get("mode") == "dialogue"
    assert isinstance(dbg.get("instruction_count"), int) and dbg["instruction_count"] > 0
    assert isinstance(dbg.get("sample_prompt_obligation_keys"), list)
    assert isinstance(dbg.get("sample_forbidden_moves"), list)


def test_no_narrative_mode_instruction_contains_generic_narration_fallback_phrase() -> None:
    """Regression: mode deltas must not introduce a 'generic narration' fallback lane."""
    for kwargs in (
        {"narration_obligations": {"is_opening_scene": True}},
        {},
        {
            "ctir": {
                "resolution": {
                    "kind": "attack",
                    "skill_check": {"dc": 10},
                    "authoritative_outputs": {},
                }
            }
        },
        {"narration_obligations": {"active_npc_reply_expected": True}},
        {"narration_obligations": {"must_advance_scene": True}},
        {"response_policy": {"answer_completeness": {"answer_required": True}}},
    ):
        c = build_narrative_mode_contract(**kwargs)
        lines = _build_narrative_mode_instructions(
            narrative_mode_contract=c,
            response_policy={"social_response_structure": {"enabled": True}},
            narration_obligations=None,
            resolution_sem=None,
        )
        blob = "\n".join(lines).lower()
        assert "generic narration" not in blob
