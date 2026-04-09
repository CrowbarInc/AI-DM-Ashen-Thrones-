"""Unit tests for ``game.context_separation`` (context separation contract + validator)."""
from __future__ import annotations

import pytest

from game.context_separation import (
    build_context_separation_contract,
    context_separation_repair_hints,
    validate_context_separation,
)

pytestmark = pytest.mark.unit


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
