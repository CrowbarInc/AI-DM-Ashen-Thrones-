"""Tests for deterministic ``game.scenario_spine_eval`` session health."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.scenario_spine import scenario_spine_from_dict
from game.scenario_spine_eval import evaluate_scenario_spine_session

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
    assert result["session_health"]["overall_passed"] is True
    assert result["session_health"]["classification"] == "clean"
    assert result["session_health"]["score"] == 100
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
    roundtrip = json.loads(encoded)
    assert roundtrip["schema_version"] == 1
