"""Unit tests for ``game.player_facing_narration_purity``."""
from __future__ import annotations

import pytest

from game.player_facing_narration_purity import (
    build_player_facing_narration_purity_contract,
    minimal_repair_player_facing_narration_purity,
    player_facing_narration_purity_repair_hints,
    validate_player_facing_narration_purity,
)

pytestmark = pytest.mark.unit


def _contract(**kwargs):
    return build_player_facing_narration_purity_contract(**kwargs)


def test_build_contract_shape_and_defaults():
    c = _contract(
        debug_inputs={"source": "test"},
        debug_reason="unit_test",
        response_type_required="neutral_narration",
        interaction_kind="explore",
    )
    assert c["enabled"] is True
    assert c["diegetic_only"] is True
    assert c["allow_structured_choice_labels"] is False
    assert c["allow_explicit_ui_references"] is False
    assert c["allow_meta_transition_bridges"] is False
    assert c["forbid_scaffold_headers"] is True
    assert c["forbid_coaching_language"] is True
    assert c["forbid_engine_choice_framing"] is True
    assert c["forbid_non_diegetic_action_prompting"] is True
    assert c["response_type_required"] == "neutral_narration"
    assert c["interaction_kind"] == "explore"
    assert c["debug_inputs"]["source"] == "test"
    assert c["debug_reason"] == "unit_test"


# --- PASS cases ---


def test_pass_ordinary_diegetic_narration():
    c = _contract()
    text = (
        "Rain hammers the slate roofs; torchlight shivers along the runoff in the gutter. "
        "A patrol's boots slap the far arch, too quick to be casual."
    )
    out = validate_player_facing_narration_purity(text, c)
    assert out["checked"] is True
    assert out["passed"] is True
    assert out["failure_reasons"] == []


def test_pass_npc_command_in_quotes():
    c = _contract()
    text = (
        'The sergeant does not raise her voice. "Move toward the gate, now," she says, '
        "and the line stiffens as if pulled by a single wire."
    )
    out = validate_player_facing_narration_purity(text, c, player_text="I wait.")
    assert out["passed"] is True
    assert out["assertion_flags"]["coaching_language_leak"] is False


def test_pass_concrete_scene_transition_arrival():
    c = _contract()
    text = (
        "You step through the postern and into Cinderwatch's outer ward—smoke, shouted names, "
        "the brine-stink of the harbor bleeding in on the wind."
    )
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is True


def test_pass_short_in_world_consequence_line():
    c = _contract()
    text = "The lock gives with a dry snap; the door eases inward on hinges that have forgotten oil."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is True


def test_pass_choose_one_in_non_menu_prose():
    c = _contract()
    text = "Rumor says the syndicate will choose one harbor lane tonight and choke the rest."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is True


# --- FAIL cases ---


def test_fail_consequence_opportunity_header():
    c = _contract()
    text = "Consequence / Opportunity: the patrol's torchlight sweeps your alley."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "scaffold_header_leak" in out["failure_reasons"]
    assert out["assertion_flags"]["scaffold_header_leak"] is True


def test_fail_next_beat_is_yours():
    c = _contract()
    text = "You weigh what you just tried near Cinderwatch Gate District; the next beat is yours."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "engine_transition_scaffold_leak" in out["failure_reasons"]


def test_fail_commit_to_one_concrete_move():
    c = _contract()
    text = "Commit to one concrete move before the bell marks third hour."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "scaffold_header_leak" in out["failure_reasons"]


def test_fail_take_the_exit_labeled():
    c = _contract()
    text = "When the crowd thins, take the exit labeled Market Lane and keep your cloak close."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "ui_choice_label_leak" in out["failure_reasons"]


def test_fail_menu_like_option_list():
    c = _contract()
    text = (
        "The ward offers forks.\n"
        "- Slip the east alley\n"
        "- Hold at the chapel steps\n"
        "- Cut back toward the gate"
    )
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "non_diegetic_prompting_leak" in out["failure_reasons"]


def test_fail_line_start_choose_one():
    c = _contract()
    text = "The street holds its breath.\n\nChoose one.\n\nEast is louder; west smells like the sea."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is False
    assert "coaching_language_leak" in out["failure_reasons"]


def test_invalid_contract():
    out = validate_player_facing_narration_purity("hello", None)
    assert out["checked"] is False
    assert out["failure_reasons"] == ["invalid_contract"]


def test_non_diegetic_interaction_skips_check():
    c = _contract(interaction_kind="oc")
    text = "Consequence / Opportunity: (OOC) Roll initiative."
    out = validate_player_facing_narration_purity(text, c)
    assert out["checked"] is False
    assert out["passed"] is True


def test_allow_meta_transition_bridges():
    c = _contract(allow_meta_transition_bridges=True)
    text = "The alley tightens; the next beat is yours once you pick a pressure point."
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is True


def test_allow_structured_choice_labels():
    c = _contract(allow_structured_choice_labels=True)
    text = "Options:\n- East\n- West"
    out = validate_player_facing_narration_purity(text, c)
    assert out["passed"] is True


def test_repair_hints_cover_violations():
    hints = player_facing_narration_purity_repair_hints(
        ["scaffold_header_leak", "ui_choice_label_leak"],
        _contract(),
    )
    joined = " ".join(hints).lower()
    assert "scaffold" in joined or "labeled" in joined or "ui" in joined or "menu" in joined


def test_minimal_repair_keeps_prose_after_header_on_one_line():
    """Whitespace-normalized gate text often merges header + narration into a single line."""
    c = _contract()
    raw = "Consequence / Opportunity: The patrol's torchlight sweeps the far arch."
    fixed, dbg = minimal_repair_player_facing_narration_purity(raw, c)
    assert dbg.get("still_failing") is False
    assert "Consequence" not in fixed
    assert "torchlight" in fixed.lower()
