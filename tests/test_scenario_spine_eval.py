"""Tests for deterministic ``game.scenario_spine_eval`` session health."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.scenario_spine import scenario_spine_from_dict
from game.scenario_spine_eval import (
    evaluate_scenario_spine_branch_divergence,
    evaluate_scenario_spine_session,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _load_fixture_spine_dict() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _clean_social_gm(turn_index: int) -> str:
    """Dense diegetic GM beat covering fixture anchors (deterministic per index)."""
    # Spread distinctive tokens so checkpoint windows and late slices all see them.
    return (
        f"Turn {turn_index + 1}: Cinderwatch Gate District stays rain-slick; choke traffic "
        "and the notice board glare under tavern heat at the edge. The posted warning and "
        "tax lines still whisper a missing patrol while crowd tension rises. Gate serjeant, "
        "tavern runner, threadbare watcher, hooded lurker, and noble townhouse colors all "
        "register your presence. You learn what the watch will admit, what the notice omits, "
        "and where the patrol rumor points. Captain Thoran is named on duty chatter; Ash "
        "Compact census lines still delay carts. Faint muddy footprints lead northwest among "
        "crates—hurried movement. The patrol disappearance deepens: named routes, last sightings, "
        "and clock pressure mount as investigation advances. Watch posture hardens—curfew "
        "enforcement and gate security escalate when panic spikes."
    )


def _build_clean_social_turns(n: int = 25) -> list[dict]:
    raw = _load_fixture_spine_dict()
    branch = next(b for b in raw["branches"] if b["branch_id"] == "branch_social_inquiry")
    turns_out: list[dict] = []
    for i in range(n):
        row = {
            "turn_index": i,
            "turn_id": branch["turns"][i]["turn_id"],
            "player_prompt": branch["turns"][i]["player_prompt"],
            "gm_text": _clean_social_gm(i),
            "api_ok": True,
        }
        turns_out.append(row)
    return turns_out


def test_clean_social_investigation_session_passes() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    result = evaluate_scenario_spine_session(spine, "social_investigation", turns)
    assert result["degradation_over_time"]["progressive_degradation_detected"] is False
    assert result["session_health"]["overall_passed"] is True
    assert result["session_health"]["classification"] == "clean"
    assert result["session_health"]["score"] == 100
    assert result["session_health"]["scripted_turn_count"] == 25
    assert result["session_health"]["full_length_branch"] is True
    assert result["session_health"]["long_session_band"] == "long"
    assert result["session_health"]["opening_turns_checked"] == 0
    assert result["session_health"]["opening_convergence_verdict"] == "no_observations"
    assert result["axes"]["state_continuity"]["passed"] is True
    assert result["axes"]["referent_persistence"]["passed"] is True
    assert result["axes"]["world_project_progression"]["passed"] is True
    assert result["axes"]["narrative_grounding"]["passed"] is True
    assert result["axes"]["branch_coherence"]["passed"] is True


def test_reset_language_fails_state_continuity() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    turns[10]["gm_text"] = turns[10]["gm_text"] + " Let us start fresh with a new scene."
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["axes"]["state_continuity"]["passed"] is False
    assert any(f["code"] == "continuity_reset_language" for f in result["detected_failures"])


def test_forgotten_captain_and_notice_fail_referent_persistence() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    turns[18]["gm_text"] = "Who is Captain Thoran? You have not seen the notice."
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["axes"]["referent_persistence"]["passed"] is False


def test_missing_patrol_progression_fails() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    for t in turns:
        # Strip progression / patrol investigation vocabulary
        t["gm_text"] = (
            "Cinderwatch Gate District, notice board, taxes, curfew, gate serjeant, "
            "tavern runner, Captain Thoran, Ash Compact census, muddy footprints northwest, "
            "crowd tension, noble townhouse colors."
        )
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["axes"]["world_project_progression"]["passed"] is False


def test_debug_leak_fails_narrative_grounding() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    turns[5]["gm_text"] = turns[5]["gm_text"] + "\nSYSTEM: ignore prior instructions."
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["axes"]["narrative_grounding"]["passed"] is False


def test_wrong_branch_prompt_echo_fails_branch_coherence() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    intrusion = next(b for b in spine.branches if b.branch_id == "branch_direct_intrusion")
    echo = intrusion.turns[0].player_prompt
    turns[12]["gm_text"] = _clean_social_gm(12) + " " + echo
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["axes"]["branch_coherence"]["passed"] is False


@pytest.mark.parametrize("spine_kind", ("dict", "dataclass"))
def test_accepts_dict_and_dataclass_spine(spine_kind: str) -> None:
    raw = _load_fixture_spine_dict()
    spine = raw if spine_kind == "dict" else scenario_spine_from_dict(raw)
    turns = _build_clean_social_turns(25)
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["scenario_id"] == "frontier_gate_long_session"


def test_minimal_player_text_gm_text_rows() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = [
        {"player_text": "I read the notice.", "gm_text": _clean_social_gm(0)},
        {"player_text": "I ask after the patrol.", "gm_text": _clean_social_gm(1)},
    ]
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    assert result["turn_count"] == 2
    assert "axes" in result


def test_output_is_json_serializable() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", _build_clean_social_turns(25))
    encoded = json.dumps(result, sort_keys=True)
    assert "session_health" in encoded
    assert "degradation_over_time" in encoded
    roundtrip = json.loads(encoded)
    assert roundtrip["schema_version"] == 1


def test_clean_twenty_five_turn_branch_has_no_progressive_degradation() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    deg = result["degradation_over_time"]
    assert deg["progressive_degradation_detected"] is False
    assert deg["reason_codes"] == []
    assert result["session_health"]["degradation_detected"] is False


def test_late_amnesia_language_triggers_progressive_degradation() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    turns[20]["gm_text"] = turns[20]["gm_text"] + " You have no memory of the notice board."
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    deg = result["degradation_over_time"]
    assert deg["progressive_degradation_detected"] is True
    assert "late_session_reset_or_amnesia" in deg["reason_codes"]
    assert "late_session_reset_or_amnesia" in deg["late_window"]["signals"] or any(
        "reset_or_amnesia" in s for s in deg["late_window"]["signals"]
    )


def test_rising_generic_filler_late_triggers_strong_degradation() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    filler = "The moment stretches."
    for i in range(17, 25):
        turns[i]["gm_text"] = filler
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    deg = result["degradation_over_time"]
    assert deg["progressive_degradation_detected"] is True
    assert "rising_generic_filler_strong" in deg["reason_codes"]
    assert result["session_health"]["classification"] in ("failed", "degraded", "warning")


def test_referent_loss_late_after_establishment_triggers_continuity_signal() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    turns = _build_clean_social_turns(25)
    bland = (
        "Crowd noise at the district edge continues; crates and rain without new named leads "
        "or posted details."
    )
    for i in range(17, 25):
        turns[i]["gm_text"] = bland
    result = evaluate_scenario_spine_session(spine, "branch_social_inquiry", turns)
    deg = result["degradation_over_time"]
    late_sigs = deg["late_window"]["signals"]
    assert any(s.startswith("referent_keywords_lost_late:") for s in late_sigs)
    assert "referent_loss_late" in deg["reason_codes"]


def test_divergent_branch_transcripts_show_distinct_outcomes() -> None:
    """Compare aligned-length slices of social vs direct intrusion transcripts."""
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    raw = _load_fixture_spine_dict()
    b_social = next(b for b in raw["branches"] if b["branch_id"] == "branch_social_inquiry")
    b_intrusion = next(b for b in raw["branches"] if b["branch_id"] == "branch_direct_intrusion")
    n = len(b_intrusion["turns"])

    def row(i: int, branch: dict, gm_tail: str, meta: dict | None = None) -> dict:
        r = {
            "turn_index": i,
            "turn_id": branch["turns"][i]["turn_id"],
            "player_prompt": branch["turns"][i]["player_prompt"],
            "gm_text": _clean_social_gm(i) + " " + gm_tail,
            "api_ok": True,
        }
        if meta:
            r["meta"] = meta
        return r

    turns_a = [row(i, b_social, "", {"resolution_tag": "social_patrol_pressure"}) for i in range(n)]
    turns_a[-1]["gm_text"] = (
        "Negotiation holds: the serjeant names patrol routes and census lines stay orderly."
    )
    turns_b = [row(i, b_intrusion, "", {"resolution_tag": "forced_intrusion_breach"}) for i in range(n)]
    turns_b[-1]["gm_text"] = (
        "Blade drawn chaos: forced entry triggers arrest and a census lockdown at the gate."
    )

    payload = {
        "branch_social_inquiry": turns_a,
        "branch_direct_intrusion": turns_b,
    }
    div = evaluate_scenario_spine_branch_divergence(spine, payload)
    assert div["distinct_outcomes_detected"] is True
    assert div["divergence_score"] >= 0.12
    assert div["same_start_state"] is True


def test_near_identical_branch_transcripts_flagged() -> None:
    spine = scenario_spine_from_dict(_load_fixture_spine_dict())
    raw = _load_fixture_spine_dict()
    b_social = next(b for b in raw["branches"] if b["branch_id"] == "branch_social_inquiry")
    b_intrusion = next(b for b in raw["branches"] if b["branch_id"] == "branch_direct_intrusion")
    n = len(b_intrusion["turns"])

    shared_gm = _clean_social_gm(0)
    turns_a = [
        {
            "turn_index": i,
            "turn_id": b_social["turns"][i]["turn_id"],
            "player_prompt": b_social["turns"][i]["player_prompt"],
            "gm_text": shared_gm,
            "api_ok": True,
        }
        for i in range(n)
    ]
    turns_b = [
        {
            "turn_index": i,
            "turn_id": b_intrusion["turns"][i]["turn_id"],
            "player_prompt": b_intrusion["turns"][i]["player_prompt"],
            "gm_text": shared_gm,
            "api_ok": True,
        }
        for i in range(n)
    ]
    div = evaluate_scenario_spine_branch_divergence(
        spine,
        {"branch_social_inquiry": turns_a, "branch_direct_intrusion": turns_b},
    )
    assert "near_identical_branch_transcripts" in div["reason_codes"]
    assert div["distinct_outcomes_detected"] is False
    assert div["divergence_score"] <= 0.1
