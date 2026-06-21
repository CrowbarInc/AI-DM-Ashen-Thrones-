"""Interaction Continuity repair and emission-step ownership coverage.

This suite owns IC validation attachment, emission-step bridge/repair/enforcement
semantics, validate-only repair isolation, and strict-social continuity fallback.

It does NOT own:

* gate ordering (response-type vs continuity placement)
* repair derivation logic in ``game.interaction_continuity``

Gate ordering remains in ``tests/test_final_emission_gate.py``.
"""
from __future__ import annotations

import pytest

import game.interaction_continuity as ic
from game.interaction_continuity import (
    apply_interaction_continuity_emission_step,
    attach_interaction_continuity_validation,
    repair_interaction_continuity,
    validate_interaction_continuity,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.emission_smoke_assertions import (
    assert_continuity_validation_failed_without_repair,
    assert_final_route_not_replaced_smoke,
    assert_final_route_present_smoke,
)

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


def _strong_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def _soft_contract() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "soft",
        "anchored_interlocutor_id": "",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


_IC_BRIDGE_LIVE_MALFORMED = 'South road." Tavern Runner nods once. "Old Millstone.'


def _strong_interaction_continuity_contract(*, anchor: str = "npc_melka") -> dict:
    return _strong_contract(anchor=anchor)


def _ssc_locked_tavern_runner() -> dict:
    return {
        "continuity_locked": True,
        "primary_speaker_id": "tavern_runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["tavern_runner"],
        "speaker_switch_allowed": False,
    }


def _strong_runner_interaction_continuity() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": "tavern_runner",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": _ssc_locked_tavern_runner(),
    }


def _speaker_binding_mismatch_malformed_enforcement() -> dict:
    return {
        "validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
        "post_validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
    }


def _assert_interaction_continuity_validation_shape(v: dict) -> None:
    assert set(v.keys()) == {
        "ok",
        "enabled",
        "continuity_strength",
        "violations",
        "warnings",
        "facts",
        "debug",
    }
    assert isinstance(v["violations"], list)
    assert isinstance(v["warnings"], list)
    assert isinstance(v["facts"], dict)
    assert isinstance(v["debug"], dict)
    for k in (
        "anchored_interlocutor_id",
        "anchor_required",
        "speaker_switch_detected",
        "explicit_switch_cue_present",
        "thread_drop_detected",
        "narrator_bridge_present",
        "multi_speaker_pattern_present",
        "dialogue_presence",
    ):
        assert k in v["facts"]
    assert "speaker_labels_detected" in v["debug"]
    assert "cue_labels" in v["debug"]
    assert "reason_path" in v["debug"]


def _interaction_continuity_gate_payload(text: str, *, ic: dict | None = None) -> tuple[dict, dict]:
    return (
        {
            "player_facing_text": text,
            "metadata": {"emission_debug": {"speaker_contract_enforcement": _speaker_binding_mismatch_malformed_enforcement()}},
            "response_policy": {"interaction_continuity": ic or _strong_runner_interaction_continuity()},
        },
        {"metadata": {"emission_debug": {}}},
    )


def test_attach_interaction_continuity_validation_populates_debug_and_final_meta():
    out = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}}}

    attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
    )

    assert out["player_facing_text"] == "The scene holds."
    icv = out["metadata"]["emission_debug"]["interaction_continuity_validation"]
    _assert_interaction_continuity_validation_shape(icv)
    assert final_emission_meta_from_output(out)["interaction_continuity_validation"] is icv
    assert resolution["metadata"]["emission_debug"]["interaction_continuity_validation"] is icv


def test_attach_interaction_continuity_validation_wires_validate_only_emission_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attach path delegates validate-only emission step inside interaction_continuity owner (BJ-51)."""
    calls: list[str] = []

    def _step_stub(out: dict, *, text: str, validate_only: bool, strict_social_path: bool, **_kwargs: object):
        calls.append(f"step:validate_only={validate_only}:strict={strict_social_path}")
        return text, [], False

    monkeypatch.setattr(
        "game.interaction_continuity.apply_interaction_continuity_emission_step",
        _step_stub,
    )
    out = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }

    attach_interaction_continuity_validation(
        out,
        resolution_for_contracts={"metadata": {"emission_debug": {}}},
        eff_resolution=None,
        session=None,
    )

    assert calls == ["step:validate_only=True:strict=False"]


def test_apply_interaction_continuity_step_records_bridge_metadata_when_bridge_fires():
    out, resolution = _interaction_continuity_gate_payload(_IC_BRIDGE_LIVE_MALFORMED)

    apply_interaction_continuity_emission_step(
        out,
        text=_IC_BRIDGE_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    bridge = (out["metadata"].get("emission_debug") or {}).get("interaction_continuity_speaker_binding_bridge")
    assert isinstance(bridge, dict)
    assert bridge.get("applied") is True
    assert bridge.get("synthetic_violation") == "malformed_speaker_attribution_under_continuity"
    assert bridge.get("malformed_attribution_detected") is True


def test_apply_interaction_continuity_step_repairs_malformed_bridge_case_before_enforcement():
    out, resolution = _interaction_continuity_gate_payload(_IC_BRIDGE_LIVE_MALFORMED)

    apply_interaction_continuity_emission_step(
        out,
        text=_IC_BRIDGE_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    em = out["metadata"]["emission_debug"]
    icv = em.get("interaction_continuity_validation") or {}
    rep = em.get("interaction_continuity_repair") or {}
    assert icv.get("ok") is True
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "repair_malformed_speaker_attribution"
    assert "malformed_speaker_attribution_under_continuity" in (rep.get("violations") or [])
    assert em.get("interaction_continuity_enforced") is not True
    assert em.get("interaction_continuity_speaker_binding_bridge", {}).get("applied") is True


def test_apply_interaction_continuity_step_enforces_when_bridge_failure_is_unrepairable():
    unrecoverable = 'South road." Stranger waits. "Old Millstone.'
    out, resolution = _interaction_continuity_gate_payload(unrecoverable)

    apply_interaction_continuity_emission_step(
        out,
        text=unrecoverable,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_enforced") is True
    assert em.get("interaction_continuity_repair", {}).get("applied") is not True
    assert em.get("interaction_continuity_speaker_binding_bridge", {}).get("applied") is True


def test_block_d_validate_only_attach_never_calls_repair_interaction_continuity(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("repair_interaction_continuity must not run on validate_only attach paths")

    monkeypatch.setattr(ic, "repair_interaction_continuity", boom)
    out = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
    )
    assert out["player_facing_text"] == "The scene holds."


def test_apply_final_emission_gate_validate_only_ic_never_calls_repair_interaction_continuity(monkeypatch):
    """Orchestration path attaches IC validation with validate_only=True; repair helper stays cold."""

    def boom(*_a, **_k):
        raise AssertionError("repair_interaction_continuity must not run on live gate validate-only IC paths")

    monkeypatch.setattr(ic, "repair_interaction_continuity", boom)
    gm = {
        "player_facing_text": "Short.",
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    _apply_gate(
        gm,
        resolution={"kind": "observe", "prompt": "Hi."},
        session=None,
        scene_id="s1",
        scene={},
        world={},
    )


def test_block_d_strict_social_continuity_hard_fallback_applies_sealed_line(monkeypatch):
    """When repair cannot fix strong continuity failure under strict-social, sealed fallback is applied."""
    ic_contract = _strong_runner_interaction_continuity()
    out = {
        "player_facing_text": "You can't go there.",
        "metadata": {},
        "response_policy": {"interaction_continuity": ic_contract},
    }
    resolution = {
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
        "metadata": {"emission_debug": {}},
    }

    monkeypatch.setattr(
        ic,
        "repair_interaction_continuity",
        lambda *_a, **_k: {"applied": False, "repaired_text": "unused"},
    )
    txt, extra, strict_fb = apply_interaction_continuity_emission_step(
        out,
        text="You can't go there.",
        resolution_for_contracts=resolution,
        eff_resolution=resolution,
        session={"turn_counter": "1"},
        validate_only=False,
        strict_social_path=True,
        strict_fallback_resolution=resolution,
    )
    assert strict_fb is True
    assert extra == []
    assert '"' in txt
    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_enforced") is True


def test_output_exhibits_stripped_uncued_interruption_with_labeled_anchor():
    c = _strong_contract()
    # Avoid phrases that count as explicit handoff cues (e.g. "someone behind you").
    text = 'Guard: "Stay where you are."\nA sharp yell from the alley: "Run!"'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "strip_uncued_interruption"
    assert "alley" not in r["repaired_text"]
    assert "Guard:" in r["repaired_text"]


def test_output_exhibits_continuity_repaired_structure_narration_to_dialogue():
    c = _strong_contract()
    text = "You can't go there."
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "dialogue_absent_under_continuity" in v["violations"]
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "narration_to_dialogue"
    assert "says" in r["repaired_text"].lower()
    assert '"' in r["repaired_text"] or "\u201c" in r["repaired_text"]


def test_emitted_output_exhibits_continuity_repaired_structure_strong_short_narration():
    """C2: gate records continuity validation; structural repairs are upstream-owned."""
    ic = _strong_contract()
    gm = {
        "player_facing_text": "You can't go there.",
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "Can I pass?"}}
    out, fem = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    assert_continuity_validation_failed_without_repair(em)
    assert out.get("player_facing_text") == "You can't go there."


def test_emitted_output_preserves_continuity_constraints_under_strong_complex_narration():
    ic = _strong_contract()
    long_narration = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": long_narration,
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What do you know?"}}
    out, fem = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    assert_continuity_validation_failed_without_repair(em)
    assert_final_route_not_replaced_smoke(fem)


def test_emitted_output_preserves_continuity_constraints_soft_strength_on_violation():
    ic = _soft_contract()
    text = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": text,
        "tags": [],
        "metadata": {},
        "response_policy": {
            "interaction_continuity": ic,
            "response_type_contract": {"required_response_type": "dialogue"},
        },
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What news?"}}
    out, fem = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    icv = em.get("interaction_continuity_validation") or {}
    assert icv.get("ok") is False
    assert em.get("interaction_continuity_enforced") is not True


def test_emitted_output_surfaces_stripped_interruption_repair_metadata():
    c = _strong_contract()
    text = 'Guard: "Halt."\nMerchant: "Wait—he is with me."'
    gm = {
        "player_facing_text": text,
        "metadata": {},
        "response_policy": {"interaction_continuity": c},
    }
    resolution = {"metadata": {"emission_debug": {}}, "player_input": "Who called out?"}
    out, fem = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    assert_continuity_validation_failed_without_repair(em)
    assert_final_route_present_smoke(fem)
    assert "final_emission_gate_replaced" in out.get("tags", [])
