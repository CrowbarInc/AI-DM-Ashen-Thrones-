"""Context Separation contract, validator, and gate-layer ownership coverage.

Unit tests cover ``game.context_separation`` directly. Gate-layer helpers live on
``game.final_emission_context_separation``. Gate-integration tests cover
pass/repair/fail/replace semantics through the downstream emission facade without
owning gate ordering.
"""
from __future__ import annotations

import game.final_emission_visibility_fallback as visibility_fallback
import pytest

from game.context_separation import (
    build_context_separation_contract,
    context_separation_repair_hints,
    validate_context_separation,
)
from game.final_emission_context_separation import (
    apply_context_separation_layer,
    resolve_context_separation_contract,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


def _contract(**kwargs):
    return build_context_separation_contract(**kwargs)


def test_build_contract_shape_and_debug():
    c = _contract(
        player_text="How much for the loaf?",
        scene_summary="A cramped stall under a soot-stained arch.",
        resolution={"kind": "barter"},
        compressed_world_pressures=["Border musters"],
        prompt_leads=[{"title": "Harbor rumor"}],
    )
    assert c["enabled"] is True
    assert isinstance(c["primary_topics"], tuple)
    assert isinstance(c["allowed_contextual_topics"], tuple)
    assert isinstance(c["ambient_pressure_topics"], tuple)
    assert "Harbor rumor" in c["allowed_contextual_topics"]
    assert "Border musters" in c["ambient_pressure_topics"]
    assert c["forbid_topic_hijack"] is True
    assert "debug_inputs" in c and "debug_flags" in c and "debug_reason" in c
    assert "tone_escalation_contract" in c


# --- PASS cases ---


def test_pass_npc_answers_then_brief_unrest():
    pt = "What does the loaf cost today?"
    c = _contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        'She names a price flatly. "Two coppers," she says. '
        "The ward's tense tonight—patrols everywhere—but bread is still bread."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["checked"] is True
    assert out["passed"] is True
    assert out["failure_reasons"] == []


def test_pass_local_action_with_one_tension_sentence():
    pt = "I pay and tuck the bundle under my arm."
    c = _contract(player_text=pt, resolution={"kind": "barter", "success": True})
    text = (
        "The exchange is quick, hands to hands. "
        "Distant drums mark the muster, a thin sound under the market noise."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is True


def test_pass_player_asks_about_danger_in_town():
    pt = "Is it safe to linger here with the patrols?"
    c = _contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "He doesn't laugh. 'Safe is a small word for a big war,' he says. "
        "Unrest has the factions eyeing each other; tonight, nowhere feels clean."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is True


def test_pass_scene_already_crisis_allows_pressure_focus():
    pt = "Where is the exit?"
    c = _contract(
        player_text=pt,
        scene_summary="A raid tears through the lower ward; panic and smoke choke the alleys.",
        resolution={"kind": "travel"},
    )
    text = (
        "A guardsman points past a splintered door. "
        "The crackdown is still rolling house to house; you move or you are moved."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is True


# --- FAIL cases ---


def test_fail_concrete_question_pivots_to_war_tension():
    pt = "What does the loaf cost today?"
    c = _contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        "Factions trade rumors faster than grain, and the capital's politics swallow small questions whole."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is False
    assert "topic_hijack_background_pressure" in out["failure_reasons"]


def test_fail_neutral_exchange_escalates_due_to_city_tension():
    pt = "Good morning. A loaf, please."
    c = _contract(
        player_text=pt,
        resolution={"kind": "barter"},
        tone_escalation_contract={
            "allow_verbal_pressure": False,
            "allow_explicit_threat": False,
        },
    )
    text = (
        "The city is on edge tonight, so back off and drop it—this is not the time for questions."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is False
    assert out["assertion_flags"]["ambient_pressure_forced_tone_shift"] is True
    assert "ambient_pressure_forced_tone_shift" in out["failure_reasons"]


def test_fail_substitution_instability_over_answer():
    pt = "What is the price today?"
    c = _contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "It is impossible to say with the unrest what the price is; "
        "any answer is swallowed by the instability of the war."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is False
    assert "pressure_answer_substitution" in out["failure_reasons"]


def test_fail_pressure_overweights_response():
    pt = "What is your name?"
    c = _contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "The border war reshapes every oath. "
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps. "
        "Empire scouts watch the passes, and the realm tears at its seams."
    )
    out = validate_context_separation(text, c, player_text=pt)
    assert out["passed"] is False
    assert "pressure_overweighting" in out["failure_reasons"]


def test_repair_hints_nonempty():
    hints = context_separation_repair_hints(
        ["topic_hijack_background_pressure", "pressure_overweighting"],
        contract=None,
    )
    assert hints
    assert any("local" in h.lower() for h in hints)


def test_repair_hints_empty_when_no_violations():
    assert context_separation_repair_hints([], contract=None) == []


def test_invalid_contract_soft_pass():
    out = validate_context_separation("Any text.", None)
    assert out["checked"] is False
    assert out["passed"] is True
    assert "invalid_contract" in out["failure_reasons"]


# --- Gate-layer integration (Context Separation ownership) ---


def test_gate_context_separation_pass_brief_pressure_after_direct_answer(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        'She names a price flatly. "Two coppers," she says. '
        "The ward's tense tonight—patrols everywhere—but bread is still bread."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True
    assert (final_emission_meta_from_output(out) or {}).get("final_route") == "accept_candidate"


def test_gate_context_separation_pass_crisis_scene_pressure_focus(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Where is the exit?"
    cs = build_context_separation_contract(
        player_text=pt,
        scene_summary="A raid tears through the lower ward; panic and smoke choke the alleys.",
        resolution={"kind": "travel"},
    )
    text = (
        "A guardsman points past a splintered door. "
        "The crackdown is still rolling house to house; you move or you are moved."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "travel", "prompt": pt},
        session=None,
        scene_id="ward_raid",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_pass_player_asks_danger(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Is it safe to linger here with the patrols?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "He doesn't laugh. 'Safe is a small word for a big war,' he says. "
        "Unrest has the factions eyeing each other; tonight, nowhere feels clean."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="street",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_repair_drops_pressure_lead_in(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        'She still says, "Two coppers," flat as slate.'
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("context_separation_repaired") is False
    assert meta.get("final_route") == "replaced"
    assert "context_separation_unsatisfied_at_boundary_no_lead_drop" in (meta.get("rejection_reasons_sample") or [])


def test_gate_context_separation_fail_pressure_monologue_replaces_non_social(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        "Factions trade rumors faster than grain, and the capital's politics swallow small questions whole."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_substitution_fail_then_replace(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is the price today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "It is impossible to say with the unrest what the price is; "
        "any answer is swallowed by the instability of the war."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_pressure_overweight_replaces(monkeypatch):
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is your name?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "The border war reshapes every oath. "
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps. "
        "Empire scouts watch the passes, and the realm tears at its seams."
    )
    out = _apply_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="scene",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("context_separation_failed") is True
    assert "pressure_overweighting" in (meta.get("context_separation_failure_reasons") or [])


def test_bj34_resolve_context_separation_contract_from_direct_field() -> None:
    c = _contract(player_text="What does the loaf cost today?", resolution={"kind": "barter"})
    gm = {"context_separation_contract": c}
    got, src = resolve_context_separation_contract(gm)
    assert got is c
    assert src == "context_separation_contract"


def test_bj34_apply_context_separation_layer_boundary_no_lead_drop_on_failure() -> None:
    pt = "What does the loaf cost today?"
    c = _contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        "Factions trade rumors faster than grain, and the capital's politics swallow small questions whole."
    )
    out_text, meta, extra = apply_context_separation_layer(
        text,
        gm_output={"context_separation_contract": c},
        resolution={"kind": "barter", "prompt": pt},
        session={},
        scene_id="market_stall",
        response_type_debug={
            "response_type_required": None,
            "response_type_contract_source": None,
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "response_type_repair_kind": None,
            "response_type_rejection_reasons": [],
        },
        strict_social_details=None,
    )
    assert out_text == text
    assert meta.get("context_separation_failed") is True
    assert meta.get("context_separation_repaired") is False
    assert "context_separation_unsatisfied_at_boundary_no_lead_drop" in extra
