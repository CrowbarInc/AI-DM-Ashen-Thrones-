from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Tuple

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.defaults import default_session, default_world
from game.dialogue_social_plan import validate_dialogue_social_plan
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.gm import build_messages
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.prompt_context import build_narration_context
from game.storage import get_scene_runtime
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


pytestmark = pytest.mark.unit


_MODEL_FACING_DSP_KEYS = {
    "speaker_id",
    "speaker_name",
    "speaker_source",
    "dialogue_intent",
    "reply_kind",
    "pressure_state",
    "relationship_codes",
    "tone_bounds",
    "prohibited_content_codes",
    "derivation_codes",
}


def _minimal_narration_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {
            "npcs": [
                {"id": "npc_x", "name": "NPC X", "location": "s1"},
                {"id": "gate_guard", "name": "Gate Guard", "location": "s1"},
            ]
        },
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 3,
            "visited_scene_ids": ["s0", "s1"],
            "interaction_context": {
                "active_interaction_target_id": "npc_x",
                "active_interaction_kind": "social",
                "interaction_mode": "social",
                "engagement_level": "engaged",
                "conversation_privacy": "public",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "What do you know?",
        "resolution": {"kind": "question", "label": "ask", "action_id": "raw-q"},
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
        "include_non_public_prompt_keys": True,
    }
    base.update(overrides)
    return base


def _build_social_ctir(
    *,
    turn_id: int,
    scene_id: str,
    player_input: str,
    kind: str,
    engagement_level: str,
    speaker_id: str,
    speaker_name: str,
    reply_kind: str = "answer",
) -> dict:
    return ctir.build_ctir(
        turn_id=turn_id,
        scene_id=scene_id,
        player_input=player_input,
        builder_source="tests.test_dialogue_social_convergence",
        intent={"raw_text": player_input, "labels": ["general"], "mode": "social"},
        resolution={
            "kind": kind,
            "label": "social",
            "action_id": f"ctir-social-{kind}",
            "noncombat_resolution": {
                "framework_version": "2026.04.noncombat.v1",
                "kind": "social_probe",
                "subkind": kind,
                "authority_domain": "interaction_state",
                "deterministic_resolved": True,
                "requires_check": False,
                "outcome_type": "closed",
                "success_state": "neutral",
                "discovered_entities": [{"entity_kind": "npc", "entity_id": speaker_id}],
                "surfaced_facts": [],
                "state_changes": {},
                "blocked_reason_codes": [],
                "ambiguous_reason_codes": [],
                "unsupported_reason_codes": [],
                "authoritative_outputs": [],
                "narration_constraints": {"npc_reply_expected": True, "reply_kind": reply_kind},
            },
        },
        interaction={
            "active_target_id": speaker_id,
            "interaction_mode": "social",
            "interaction_kind": kind,
            "continuity": {"engagement_level": engagement_level},
            "speaker_target": {"id": speaker_id, "name": speaker_name},
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


def _strict_social_resolution(npc_id: str, npc_name: str, prompt: str) -> dict:
    return {
        "kind": "question",
        "prompt": prompt,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": npc_name,
            "npc_reply_expected": True,
        },
        "metadata": {"response_type_contract": {"required_response_type": "dialogue"}},
    }


def _run_social_chain(
    *,
    kind: str,
    engagement_level: str,
    speaker_id: str,
    speaker_name: str,
    user_text: str,
    reply_kind: str = "answer",
) -> Tuple[dict, dict, dict, dict]:
    """Return (ctx, full_dialogue_social_plan, model_payload_dsp_projection, strict_social_resolution_with_emission_debug)."""
    kw = _minimal_narration_kwargs(user_text=user_text)
    session = dict(kw["session"])
    session["interaction_context"] = {
        **dict(session.get("interaction_context") or {}),
        "active_interaction_target_id": speaker_id,
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": engagement_level,
    }

    c = _build_social_ctir(
        turn_id=3,
        scene_id="s1",
        player_input=user_text,
        kind=kind,
        engagement_level=engagement_level,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        reply_kind=reply_kind,
    )
    attach_ctir(session, c)
    session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    kw["session"] = session

    strict_res = _strict_social_resolution(speaker_id, speaker_name, user_text)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
        # Build a model payload and also preserve the full plan in emission_debug for FEM validation.
        msgs = build_messages(
            campaign=kw["campaign"],
            world=kw["world"],
            session=kw["session"],
            character=kw["character"],
            scene=kw["scene"],
            combat=kw["combat"],
            recent_log=kw["recent_log"],
            user_text=kw["user_text"],
            resolution=strict_res,
            scene_runtime=kw["scene_runtime"],
            prompt_profile="full",
            narration_context_call_kwargs=kw,
        )
    finally:
        detach_ctir(session)

    dsp_full = ctx.get("dialogue_social_plan")
    assert isinstance(dsp_full, dict)
    ok, errs = validate_dialogue_social_plan(dsp_full, strict=False)
    assert ok is True, errs

    assert isinstance(msgs, list) and len(msgs) >= 2
    model_payload = json.loads(msgs[1].get("content") or "{}")
    dsp_model = model_payload.get("dialogue_social_plan")
    assert isinstance(dsp_model, dict)
    return ctx, dsp_full, dsp_model, strict_res


def _assert_social_chain(
    *,
    ctx: dict,
    dsp_full: dict,
    dsp_model: dict,
    strict_res: dict,
    expected_intent: str,
    expected_pressure: str | None = None,
    expected_tone_contains: str | None = None,
) -> None:
    # CTIR owns semantic intent: plan must declare CTIR-only derivation.
    assert "intent:ctir_only" in (dsp_full.get("derivation_codes") or [])

    # Bundle → prompt_context shipping: when CTIR-backed and required, the plan must apply.
    assert dsp_full.get("applies") is True
    assert str(dsp_full.get("speaker_id") or "").strip()
    assert str(dsp_full.get("dialogue_intent") or "").strip()
    assert dsp_full.get("dialogue_intent") == expected_intent

    if expected_pressure is not None:
        assert dsp_full.get("pressure_state") == expected_pressure
    if expected_tone_contains is not None:
        assert expected_tone_contains in (dsp_full.get("tone_bounds") or [])

    # Model-facing projection must be structural allowlist only.
    assert set(dsp_model.keys()) <= _MODEL_FACING_DSP_KEYS
    assert dsp_model.get("speaker_id") == dsp_full.get("speaker_id")
    assert dsp_model.get("dialogue_intent") == dsp_full.get("dialogue_intent")
    for forbidden in ("version", "applies", "validator", "bounded_session_hints"):
        assert forbidden not in dsp_model

    # prompt_context must not permit generic glue as a compensating behavior.
    instr = "\n".join([str(x) for x in (ctx.get("instructions") or [])])
    assert "generic conversational glue" in instr
    low = instr.lower()
    # Wording may evolve; keep assertions semantic and constrained to the non-improvisation rule.
    assert (
        ("do not invent speaker" in low)
        or ("must not choose the speaker" in low)
        or ("must not choose speaker" in low)
    )

    # Final-emission gate must trace the dialogue plan invariant and accept valid plan.
    sess = default_session()
    world = default_world()
    scene_id = "frontier_gate"
    set_social_target(sess, dsp_full["speaker_id"])
    rebuild_active_scene_entities(sess, world, scene_id)
    rt = get_scene_runtime(sess, scene_id)
    rt["last_player_action_text"] = strict_res["prompt"]

    out = apply_final_emission_gate(
        {"player_facing_text": f'{dsp_full["speaker_name"]} says, "Answer."', "tags": []},
        resolution=strict_res,
        session=sess,
        scene_id=scene_id,
        world=world,
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("dialogue_plan_checked") is True
    assert meta.get("dialogue_plan_required") is True
    assert meta.get("dialogue_plan_present") is True
    assert meta.get("dialogue_plan_valid") is True
    # No generic friendly glue should appear in dialogue-bearing strict-social output.
    assert " nods " not in f" {out.get('player_facing_text','')} ".lower()


def test_direct_npc_question_chain_complete() -> None:
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="question",
        engagement_level="engaged",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="Where did they go?",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="question",
        expected_pressure="moderate",
        expected_tone_contains="direct",
    )


def test_ongoing_conversation_follow_up_chain_complete() -> None:
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="question",
        engagement_level="engaged",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="And after that—who paid you?",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="question",
        expected_pressure="moderate",
    )


def test_persuasion_attempt_chain_complete() -> None:
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="persuade",
        engagement_level="engaged",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="Help me and I can make this worth your while.",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="persuade",
        expected_pressure="moderate",
        expected_tone_contains="guarded",
    )


def test_intimidation_attempt_chain_complete() -> None:
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="intimidate",
        engagement_level="focused",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="Tell me now, or you’ll regret it.",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="intimidate",
        expected_pressure="high",
        expected_tone_contains="threatening",
    )


def test_ambiguous_generic_role_address_guard_resolves_via_ctir_speaker_target() -> None:
    # "Guard" as a generic role should not trigger any new taxonomy/mapping; CTIR must bind to a real NPC id.
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="question",
        engagement_level="engaged",
        speaker_id="gate_guard",
        speaker_name="Gate Guard",
        user_text="Guard, who’s in charge here?",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="question",
        expected_pressure="moderate",
    )
    assert dsp_full.get("speaker_source") == "ctir.interaction.speaker_target"


def test_scene_directed_question_does_not_force_npc_dialogue() -> None:
    # Scene-directed perceptual question: "question" in English, but not a social probe in CTIR.
    kw = _minimal_narration_kwargs(
        user_text="What do I see in the street?",
        resolution={"kind": "observe", "label": "look", "action_id": "raw-look"},
    )
    session = dict(kw["session"])
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="What do I see in the street?",
        builder_source="tests.test_dialogue_social_convergence",
        intent={"raw_text": "What do I see in the street?", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "observe", "label": "look", "action_id": "ctir-look"},
        interaction={"active_target_id": None, "interaction_mode": "activity", "interaction_kind": "observe"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    kw["session"] = session
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)

    dsp = ctx.get("dialogue_social_plan")
    assert isinstance(dsp, dict)
    assert dsp.get("applies") is False
    instr = "\n".join([str(x) for x in (ctx.get("instructions") or [])])
    assert "DIALOGUE SOCIAL PLAN (HARD RULE)" not in instr

    out = apply_final_emission_gate(
        {"player_facing_text": "You see a wet cobblestone street under grey light.", "tags": []},
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="s1",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    # Not strict-social: no unnecessary dialogue-plan requirement or enforcement.
    assert meta.get("dialogue_plan_checked") in (None, False)


def test_social_refusal_under_pressure_traces_to_plan_reply_kind() -> None:
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="question",
        engagement_level="focused",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="Answer me. Now.",
        reply_kind="refusal",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="question",
        expected_pressure="high",
    )
    assert dsp_full.get("reply_kind") == "refusal"


def test_relationship_tension_constrains_tone_bounds_via_intent_only() -> None:
    # "Tension" is represented structurally (pressure_state + engagement relationship codes).
    ctx, dsp_full, dsp_model, strict_res = _run_social_chain(
        kind="intimidate",
        engagement_level="focused",
        speaker_id="npc_x",
        speaker_name="NPC X",
        user_text="Last chance. Speak.",
    )
    _assert_social_chain(
        ctx=ctx,
        dsp_full=dsp_full,
        dsp_model=dsp_model,
        strict_res=strict_res,
        expected_intent="intimidate",
        expected_pressure="high",
        expected_tone_contains="threatening",
    )
    assert any(str(x).startswith("engagement_") for x in (dsp_full.get("relationship_codes") or []))


def test_non_dialogue_narration_unaffected_and_no_unnecessary_plan_requirement() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain beads on the checkpoint stones.", "tags": []},
        resolution=None,
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("dialogue_plan_checked") in (None, False)
    assert out["player_facing_text"] == "Rain beads on the checkpoint stones."

