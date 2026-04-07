"""Block 3: strict-social dialogue + local pronoun substitution before referential fallback."""
from __future__ import annotations

import re

import pytest

import game.final_emission_gate as final_emission_gate
from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narration_visibility import validate_player_facing_referential_clarity
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _strict_social_bundle_with_runner():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = default_scene(sid)
    set_social_target(session, "tavern_runner")
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Runner, what do you hear about the patrol?"
    resolution = {
        "kind": "question",
        "prompt": "Runner, what do you hear about the patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
        },
        "metadata": {
            "response_type_contract": {"required_response_type": "dialogue", "allow_escalation": True},
        },
    }
    return session, world, scene, sid, resolution


def test_strict_social_guarded_dialogue_single_she_gets_local_substitution_not_emergency_fallback():
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = '"Keep your wits about you," she insists, glancing nervously at the crowd.'
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    text = out["player_facing_text"]
    meta = out["_final_emission_meta"]
    low = f" {text.lower()} "
    assert " she " not in low and " she," not in text.lower()
    assert "the tavern runner" in text.lower()
    assert "starts to answer" not in text.lower()
    assert meta.get("final_emitted_source") != "minimal_social_emergency_fallback"
    assert meta.get("referential_clarity_local_substitution_applied") is True
    assert meta.get("referential_clarity_local_substitution_attempted") is True
    assert meta.get("referential_clarity_fallback_after_failed_local_repair") is not True
    assert meta.get("referential_clarity_fallback_avoided") is True
    assert meta.get("referential_clarity_replacement_applied") is False
    assert meta.get("referential_clarity_validation_passed") is True
    assert "referential_clarity_enforcement_replaced" not in out.get("tags", [])
    assert "Keep your wits about you" in text


def test_strict_social_local_substitution_preserves_substantive_guarded_payload():
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = (
        '"I cannot name names here," she mutters, eyes on the door - east road talk only.'
    )
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    text = out["player_facing_text"]
    meta = out["_final_emission_meta"]
    assert "east road" in text.lower()
    assert "name" in text.lower()
    assert meta.get("referential_clarity_local_substitution_applied") is True


def test_strict_social_local_substitution_changes_only_the_ambiguous_pronoun():
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = (
        '"I cannot name names here," she mutters, eyes on the door - east road talk only.'
    )
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    text = out["player_facing_text"]
    meta = out["_final_emission_meta"]
    rep = str(meta.get("referential_clarity_local_substitution_replacement") or "")
    assert rep
    expected = re.sub(r"(?<!\w)she(?!\w)", rep, candidate, count=1, flags=re.IGNORECASE)
    assert text == expected


def test_multi_entity_ambiguous_pronoun_does_not_apply_local_repair():
    """Competing person referents: validator yields multi-id violation; helper must not substitute."""
    session, world, scene, sid, _resolution = _strict_social_bundle_with_runner()
    candidate = "Guard Captain and Tavern Runner trade hard looks. He steps forward."
    val = validate_player_facing_referential_clarity(
        candidate,
        session=session,
        scene=scene,
        world=world,
    )
    assert val.get("ok") is False
    violations = [v for v in (val.get("violations") or []) if isinstance(v, dict)]
    repaired, dbg = final_emission_gate._try_strict_social_local_pronoun_substitution_repair(
        candidate,
        violations=violations,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution={"social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"}},
        active_interlocutor="tavern_runner",
    )
    assert repaired is None
    assert dbg.get("referential_clarity_local_substitution_applied") is False
    assert dbg.get("referential_clarity_local_substitution_attempted") is False


def test_strict_social_stall_acknowledgement_not_local_repaired():
    """Pure acknowledgement without clue/refusal/direction payload must not be token-rescued."""
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = (
        '"I understand completely," she says, smiling politely while leaving your request unresolved.'
    )
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    meta = out["_final_emission_meta"]
    assert meta.get("referential_clarity_local_substitution_applied") is not True
    assert meta.get("referential_clarity_local_substitution_attempted") is not True
    assert meta.get("referential_clarity_replacement_applied") is True
    assert "referential_clarity_enforcement_replaced" in out.get("tags", [])


def test_strict_social_local_substitution_uses_speaker_label_not_invented_facts():
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = '"Not a word more," she whispers, sliding the note away.'
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    meta = out["_final_emission_meta"]
    rep = str(meta.get("referential_clarity_local_substitution_replacement") or "")
    assert "innkeeper" not in rep.lower()
    assert "mysterious stranger" not in rep.lower()
    assert "tavern runner" in rep.lower()


def test_strict_social_local_substitution_response_type_and_delta_meta_remain_consistent():
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = '"Keep your wits about you," she insists, glancing nervously at the crowd.'
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    meta = out["_final_emission_meta"]
    assert meta.get("response_type_required") == "dialogue"
    assert meta.get("response_type_candidate_ok") is not False
    assert meta.get("referential_clarity_local_substitution_applied") is True
    rd_checked = meta.get("response_delta_checked")
    if rd_checked is True:
        assert meta.get("response_delta_failed") is not True


def test_strict_social_second_pass_referential_fail_falls_back_without_chaining(monkeypatch):
    """One substitution attempt; if re-validation fails, use standard fallback meta."""
    session, world, scene, sid, resolution = _strict_social_bundle_with_runner()
    candidate = '"Keep your wits about you," she insists, glancing nervously at the crowd.'
    gm = {
        "player_facing_text": candidate,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    orig = final_emission_gate.validate_player_facing_referential_clarity
    calls: list[str] = []

    def wrapped_validate(text: str, **kwargs):
        calls.append(text)
        if len(calls) >= 2:
            return {
                "ok": False,
                "violations": [
                    {
                        "kind": "ambiguous_entity_reference",
                        "token": "forced",
                        "candidate_entity_ids": ["tavern_runner"],
                        "candidate_aliases": [],
                        "sentence_text": text,
                        "offset": 0,
                    }
                ],
                "checked_entities": [],
            }
        return orig(text, **kwargs)

    monkeypatch.setattr(
        final_emission_gate,
        "validate_player_facing_referential_clarity",
        wrapped_validate,
    )
    out = final_emission_gate.apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    meta = out["_final_emission_meta"]
    assert meta.get("referential_clarity_local_substitution_attempted") is True
    assert meta.get("referential_clarity_local_substitution_applied") is False
    assert meta.get("referential_clarity_fallback_after_failed_local_repair") is True
    assert meta.get("referential_clarity_replacement_applied") is True
    assert len(calls) >= 2
