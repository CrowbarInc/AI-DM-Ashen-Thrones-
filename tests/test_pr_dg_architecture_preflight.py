"""PR-DG harness safety. No provider calls. No production-save writes."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from experiments.pr_dg.candidate_c import dispatch_tool
from experiments.pr_dg.runner import run_preflight
from experiments.pr_dg.state import combat_bundle, state_hash
from game.storage import CAMPAIGN_PATH, CHARACTER_PATH, COMBAT_PATH, SESSION_LOG_PATH, SESSION_PATH, WORLD_PATH

pytestmark = pytest.mark.unit

WATCHED = (SESSION_PATH, WORLD_PATH, COMBAT_PATH, SESSION_LOG_PATH, CHARACTER_PATH, CAMPAIGN_PATH)


def _fingerprint() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for path in WATCHED:
        if path.exists():
            out[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            out[path.name] = None
    return out


def test_preview_does_not_roll(monkeypatch) -> None:
    def _boom(_sides: int) -> int:
        raise AssertionError("read-only preview called roll_die")

    monkeypatch.setattr("game.combat.roll_die", _boom)
    bundle = combat_bundle()
    before = state_hash(bundle)
    result = dispatch_tool(
        bundle,
        "request_rules_adjudication",
        {"kind": "attack", "target_id": "goblin_1", "raw": "I attack the goblin with my quarterstaff."},
        turn_state={},
    )
    assert result["code"] == "ok"
    assert result["mutation"] == "none"
    assert state_hash(bundle) == before
    assert "dc" not in result["result"]


def test_preflight_stays_inside_the_authority_contract() -> None:
    before = _fingerprint()
    payload = run_preflight(measure_narration=False)
    assert _fingerprint() == before
    assert payload["live_provider_calls"] == 0
    assert payload["isolation"]["verified"] is True
    assert payload["decision"]["unauthorized_controls"] == []
    assert payload["decision"]["authority_rows"] == []
    assert len(payload["scenarios"]) == 14
    for scenario in payload["scenarios"]:
        hashes = {scenario["gold"][label]["initial_state_hash"] for label in ("A", "B", "C")}
        assert len(hashes) == 1
    assert all(item["match"] for item in payload["decision"]["mechanical_matches"])
    combat = next(item for item in payload["scenarios"] if item["scenario_id"] == "B1")
    hp = {label: combat["gold"][label]["after"]["enemy_hp"] for label in ("A", "B", "C")}
    assert hp["A"] == hp["B"] == hp["C"]
    assert "resolve_attack" in combat["gold"]["A"]["operations"]
    dump = next(item for item in payload["scenarios"] if item["number"] == "14")
    assert dump["gold"]["A"]["after"]["enemy_hp"]["goblin_1"] == 6
    assert dump["gold"]["B"]["after"]["enemy_hp"]["goblin_1"] == 6
    assert dump["gold"]["C"]["after"]["enemy_hp"]["goblin_1"] == 6
    preview = next(item for item in payload["transactions"] if item["name"] == "read_only_combat_preview")
    assert preview["hp_unchanged"] is True
    assert preview["mutation"] == "none"
    hidden = next(item for item in payload["transactions"] if item["name"] == "hidden_information_request")
    assert hidden["hidden_in_results"] is False
    assert hidden["field_code"] == "permission"
    compound = next(item for item in payload["transactions"] if item["name"] == "partially_valid_compound")
    assert compound["transaction"] == "partially_committed"
    second = next(item for item in payload["transactions"] if item["name"] == "invalid_second_step")
    assert second["transaction"] == "partially_committed"
    assert second["steps"][0]["status"] == "committed"
    assert second["steps"][1]["status"] == "rejected"
    assert all(row["committed_unauthorized"] is False for row in payload["adversarial"])
    courier = next(item for item in payload["scenarios"] if item["scenario_id"] == "courier")
    locations = {label: courier["gold"][label]["after"]["npc_locations"]["df_mobile_courier"] for label in ("A", "B", "C")}
    assert len(set(locations.values())) == 1
    assert locations["A"] != "frontier_gate"
