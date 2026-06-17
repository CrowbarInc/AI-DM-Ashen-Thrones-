"""Unit tests for ``game.player_facing_narration_purity`` and gate-layer integration (BH-5).

Gate-layer helpers live on ``game.final_emission_player_facing_narration_purity``.
ASP gate-layer helpers live on ``game.final_emission_answer_shape_primacy`` (see
``tests/test_answer_shape_primacy.py``). Gate-order purity/ASP pins remain in ``tests/test_final_emission_gate.py``."""
from __future__ import annotations

import pytest

import game.final_emission_terminal_pipeline as terminal_pipeline
from game.final_emission_player_facing_narration_purity import (
    apply_player_facing_narration_purity_layer,
    resolve_player_facing_narration_purity_contract,
)
from tests.helpers.emission_smoke_assertions import (
    apply_final_emission_gate_consumer,
    final_emission_meta_from_output,
    response_type_contract,
)

from game.player_facing_narration_purity import (
    build_player_facing_narration_purity_contract,
    minimal_repair_player_facing_narration_purity,
    player_facing_narration_purity_repair_hints,
    validate_player_facing_narration_purity,
)

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


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
    assert "debug_inputs" not in c and "debug_reason" not in c


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

# ---------------------------------------------------------------------------
# BH-5: extracted from tests/test_final_emission_gate.py
# ---------------------------------------------------------------------------

def test_resolve_player_facing_narration_purity_contract_from_response_policy():
    c = _contract()
    gm = {"response_policy": {"player_facing_narration_purity": c}}
    got, src = resolve_player_facing_narration_purity_contract(gm)
    assert got is c
    assert src == "response_policy"


def test_bj35_apply_player_facing_narration_purity_layer_boundary_no_minimal_repair_on_failure():
    raw = "Consequence / Opportunity:\nThe patrol's torchlight sweeps the far arch."
    text, meta, extra = apply_player_facing_narration_purity_layer(
        raw,
        gm_output={"player_facing_narration_purity_contract": _contract()},
        resolution={"kind": "observe", "prompt": "I look around."},
        response_type_debug={
            "response_type_required": "neutral_narration",
            "response_type_contract_source": None,
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "response_type_repair_kind": None,
            "response_type_rejection_reasons": [],
        },
    )
    assert text == raw
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("player_facing_narration_purity_repaired") is False
    assert "player_facing_narration_purity_unsatisfied_at_boundary_no_minimal_repair" in extra


def test_gate_purity_and_asp_pass_clean_observation(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    out = _apply_gate(
        {
            "player_facing_text": "Rain hammers the slate roof; torchlight shivers in the gutter below.",
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I look around the street."},
        session={},
        scene_id="market_lane",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert meta.get("answer_shape_primacy_failed") is False
    assert "Rain" in (out.get("player_facing_text") or "")


def test_gate_purity_and_asp_pass_scene_transition_arrival(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    out = _apply_gate(
        {
            "player_facing_text": (
                "You emerge into the lower ward—smoke, shouted names, the harbor's brine on the wind."
            ),
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={
            "kind": "travel",
            "prompt": "I take the postern into the ward.",
            "resolved_transition": True,
        },
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "emerge" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_pass_npc_quoted_command_in_observe(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        'The sergeant does not raise her voice. "Move toward the gate, now," she says, '
        "and the line stiffens as if pulled by a single wire."
    )
    out = _apply_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I watch the line."},
        session={},
        scene_id="gate_yard",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert "gate" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_and_asp_pass_action_outcome_then_brief_consequence(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        "You thumb the latch; it gives with a dry snap. "
        "Patrol whistles tighten two streets over, a thin urgent sound against the rain."
    )
    out = _apply_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("action_outcome")},
        },
        resolution={"kind": "interact", "prompt": "I try the latch on the side door."},
        session={},
        scene_id="alley_door",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "latch" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_repairs_scaffold_header_leak(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Consequence / Opportunity:\nThe patrol's torchlight sweeps the far arch."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I glance up the street."},
        session={},
        scene_id="arch_lane",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("player_facing_narration_purity_repaired") is False
    assert meta.get("final_route") == "replaced"


def test_gate_purity_repairs_coaching_language(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "You weigh what you just tried near the checkpoint; rain drums on the slate roof."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen at the checkpoint."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_purity_repairs_ui_label_leak(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Take the exit labeled North and you smell cold river air beyond the arch."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I scan for a way out."},
        session={},
        scene_id="river_arch",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_asp_repairs_observe_when_pressure_leads_concrete_observation(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "The ward's tension mounts; confrontation feels inevitable. "
        "You hear boots on wet cobbles to your left, uneven and hurried."
    )
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen for movement."},
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_purity_strips_transition_scaffold_on_travel(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "The next beat is yours. You emerge onto the quay, ropes creaking, gulls wheeling overhead."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "travel", "prompt": "I head down to the quay.", "resolved_transition": True},
        session={},
        scene_id="stone_quay",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_asp_triggers_replace_when_no_observation_payload(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps."
    )
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "What do I see on the street?"},
        session={},
        scene_id="market_square",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("final_route") == "replaced"
