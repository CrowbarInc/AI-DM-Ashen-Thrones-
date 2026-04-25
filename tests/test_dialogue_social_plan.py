"""C1-D dialogue/social plan: deterministic, derivative-only structural artifact."""

from __future__ import annotations

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import SESSION_NARRATION_PLAN_BUNDLE_KEY
from game.dialogue_social_plan import validate_dialogue_social_plan
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


pytestmark = pytest.mark.unit


def _minimal_narration_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {"npcs": [{"id": "npc_x", "name": "NPC X", "location": "s1"}]},
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


def _attach_social_ctir(session: dict, *, kind: str, engagement_level: str = "engaged") -> None:
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="What do you know?",
        builder_source="tests.test_dialogue_social_plan",
        intent={"raw_text": "What do you know?", "labels": ["general"], "mode": "social"},
        resolution={
            "kind": kind,
            "label": "social",
            "action_id": "ctir-social",
            "noncombat_resolution": {
                "framework_version": "2026.04.noncombat.v1",
                "kind": "social_probe",
                "subkind": kind,
                "authority_domain": "interaction_state",
                "deterministic_resolved": True,
                "requires_check": False,
                "outcome_type": "closed",
                "success_state": "neutral",
                "discovered_entities": [{"entity_kind": "npc", "entity_id": "npc_x"}],
                "surfaced_facts": [],
                "state_changes": {},
                "blocked_reason_codes": [],
                "ambiguous_reason_codes": [],
                "unsupported_reason_codes": [],
                "authoritative_outputs": [],
                "narration_constraints": {"npc_reply_expected": True, "reply_kind": "answer"},
            },
        },
        interaction={
            "active_target_id": "npc_x",
            "interaction_mode": "social",
            "interaction_kind": kind,
            "continuity": {"engagement_level": engagement_level},
            "speaker_target": {"id": "npc_x", "name": "NPC X"},
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
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"


def test_social_exchange_produces_applies_true_with_speaker_and_intent() -> None:
    kw = _minimal_narration_kwargs()
    session = dict(kw["session"])
    _attach_social_ctir(session, kind="question", engagement_level="engaged")
    kw["session"] = session
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    dsp = ctx.get("dialogue_social_plan")
    assert isinstance(dsp, dict)
    assert dsp.get("applies") is True
    assert dsp.get("speaker_id") == "npc_x"
    assert dsp.get("dialogue_intent") in ("question", "social_probe")
    ok, errs = validate_dialogue_social_plan(dsp, strict=False)
    assert ok is True
    assert errs == []


def test_non_social_narration_produces_applies_false() -> None:
    kw = _minimal_narration_kwargs(resolution={"kind": "travel", "label": "move", "action_id": "raw-walk"})
    session = dict(kw["session"])
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="I walk.",
        builder_source="tests.test_dialogue_social_plan",
        intent={"raw_text": "I walk.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "travel", "label": "move", "action_id": "ctir-travel"},
        interaction={"active_target_id": None, "interaction_mode": "activity", "interaction_kind": "travel"},
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
    kw["user_text"] = "I walk."
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    dsp = ctx.get("dialogue_social_plan")
    assert isinstance(dsp, dict)
    assert dsp.get("applies") is False
    # Speaker may still be present due to continuity subject signals; "applies" is the gating flag.
    ok, errs = validate_dialogue_social_plan(dsp, strict=False)
    assert ok is True
    assert errs == []


def test_malformed_plan_missing_speaker_fails_validation() -> None:
    bad = {
        "version": 1,
        "applies": True,
        "speaker_id": None,
        "speaker_name": None,
        "speaker_source": "unresolved",
        "dialogue_intent": "question",
        "reply_kind": "answer",
        "pressure_state": "low",
        "relationship_codes": ["unknown"],
        "tone_bounds": ["neutral"],
        "prohibited_content_codes": ["no_prompt_text"],
        "derivation_codes": ["test"],
        "validator": {},
    }
    ok, errs = validate_dialogue_social_plan(bad, strict=False)
    assert ok is False
    assert "missing_required:speaker_id" in errs


def test_malformed_plan_with_prose_like_text_field_fails_validation() -> None:
    bad = {
        "version": 1,
        "applies": False,
        "speaker_id": None,
        "speaker_name": None,
        "speaker_source": "unresolved",
        "dialogue_intent": None,
        "reply_kind": "unknown",
        "pressure_state": "none",
        "relationship_codes": ["unknown"],
        "tone_bounds": ["neutral"],
        "prohibited_content_codes": ["no_prompt_text"],
        "derivation_codes": ["test"],
        "validator": {},
        "text": "This should never appear here.",
    }
    ok, errs = validate_dialogue_social_plan(bad, strict=False)
    assert ok is False
    assert any(e.startswith("rejected_field_name:") for e in errs)


def test_intimidation_carries_pressure_and_tone_bounds_but_no_spoken_line_text() -> None:
    kw = _minimal_narration_kwargs()
    session = dict(kw["session"])
    # Focused engagement drives "high" pressure; intimidation drives threatening tone.
    _attach_social_ctir(session, kind="intimidate", engagement_level="focused")
    kw["session"] = session
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    dsp = ctx.get("dialogue_social_plan")
    assert isinstance(dsp, dict)
    assert dsp.get("applies") is True
    assert dsp.get("dialogue_intent") == "intimidate"
    assert dsp.get("pressure_state") == "high"
    assert "threatening" in (dsp.get("tone_bounds") or [])
    # Structural-only: reject obvious prose keys at the plan root.
    for forbidden in ("text", "prompt", "message", "dialogue_line", "instructions", "narration"):
        assert forbidden not in dsp


def test_social_ctir_build_messages_projects_structural_dialogue_social_plan_only() -> None:
    from game.gm import build_messages

    kw = _minimal_narration_kwargs()
    session = dict(kw["session"])
    _attach_social_ctir(session, kind="question", engagement_level="engaged")
    kw["session"] = session
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        msgs = build_messages(
            campaign=kw["campaign"],
            world=kw["world"],
            session=kw["session"],
            character=kw["character"],
            scene=kw["scene"],
            combat=kw["combat"],
            recent_log=kw["recent_log"],
            user_text=kw["user_text"],
            resolution=kw["resolution"],
            scene_runtime=kw["scene_runtime"],
            prompt_profile="full",
            narration_context_call_kwargs=kw,
        )
    finally:
        detach_ctir(session)
    assert isinstance(msgs, list) and len(msgs) >= 2
    user_payload = msgs[1].get("content") or ""
    assert "NPC reacts" not in user_payload
    import json

    parsed = json.loads(user_payload)
    dsp = parsed.get("dialogue_social_plan")
    assert isinstance(dsp, dict)
    assert set(dsp.keys()) <= {
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
    for forbidden in ("version", "applies", "validator"):
        assert forbidden not in dsp


def test_missing_dialogue_social_plan_on_ctir_social_turn_records_seam_audit() -> None:
    kw = _minimal_narration_kwargs()
    session = dict(kw["session"])
    _attach_social_ctir(session, kind="question", engagement_level="engaged")
    kw["session"] = session
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = dict(session[SESSION_NARRATION_PLAN_BUNDLE_KEY])
        ri = dict(bundle.get("renderer_inputs") or {})
        ri.pop("dialogue_social_plan", None)
        bundle["renderer_inputs"] = ri
        session[SESSION_NARRATION_PLAN_BUNDLE_KEY] = bundle
        ctx = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    audit = ctx.get("narration_seam_audit")
    assert isinstance(audit, dict)
    assert audit.get("dialogue_social_plan_contract_blocked") is True
    assert audit.get("dialogue_social_plan_present") is False
    assert audit.get("dialogue_social_plan_failure_codes")

