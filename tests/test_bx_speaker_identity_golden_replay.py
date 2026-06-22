"""BX5 — Protected golden replay and Speaker Contract Risk gate for guard speaker parity.

Locks gate→replay projection fields for frontier_gate guard matrix cases A–D and
asserts ambiguous guard cannot regress to low-risk aligned parity.
"""
from __future__ import annotations

import pytest

from game.defaults import default_world
from tests.helpers.bx_guard_speaker_parity import (
    AMBIGUOUS_GUARD_PLAYER_TEXT,
    ambiguous_guard_scene_bundle,
    assert_ambiguous_guard_golden_parity,
    assert_resolved_guard_golden_parity,
    frontier_gate_base_session_scene,
    gate_guard_addressable,
    observe_ambiguous_guard_gate_replay,
    observe_guard_lifecycle,
    route_authoritative,
)
from tests.helpers.golden_replay import (
    assert_protected_golden_turn_observation,
    protected_bx_ambiguous_guard_parity_expectation,
    protected_bx_resolved_speaker_parity_expectation,
)
from tests.helpers.speaker_contract_risk import speaker_contract_family_risk_rows

pytestmark = pytest.mark.bx_speaker_parity


def _assert_protected_resolved_turn(
    obs,
    *,
    scenario_id: str,
    expected_speaker_id: str,
) -> None:
    assert_protected_golden_turn_observation(
        obs.replay_observation,
        protected_bx_resolved_speaker_parity_expectation(expected_speaker_id),
        scenario_id=scenario_id,
        debug_context=obs.as_checkpoint_record().__repr__(),
    )
    assert_resolved_guard_golden_parity(obs, expected_speaker_id=expected_speaker_id)


def test_bx5_protected_golden_role_alias_guard_to_guard_captain(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, scene = frontier_gate_base_session_scene()
    scenario_id = "bx5_guard_role_alias_guard_captain"
    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text="Guard, who posted that notice?",
        gm_line='Guard Captain says, "The captain posted it at dawn."',
        scenario_id=scenario_id,
    )

    assert obs.routed_speaker_id == "guard_captain"
    _assert_protected_resolved_turn(obs, scenario_id=scenario_id, expected_speaker_id="guard_captain")


def test_bx5_protected_golden_canonical_guard_captain(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, scene = frontier_gate_base_session_scene()
    scenario_id = "bx5_guard_canonical_guard_captain"
    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text="guard_captain, who posted that notice?",
        gm_line='Guard Captain says, "I posted it at dawn."',
        scenario_id=scenario_id,
    )

    assert obs.routed_speaker_id == "guard_captain"
    _assert_protected_resolved_turn(obs, scenario_id=scenario_id, expected_speaker_id="guard_captain")


def test_bx5_protected_golden_gate_guard_distinct_from_guard_captain(monkeypatch: pytest.MonkeyPatch) -> None:
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "topics": [],
        }
    ]
    session, world, scene = frontier_gate_base_session_scene(
        extra_addressables=[gate_guard_addressable()],
        extra_active_entities=["gate_guard"],
        world=world,
    )
    player_text = "Gate Guard, what is your post?"
    auth = route_authoritative(session, world, scene, player_text)
    assert auth.get("npc_id") == "gate_guard"
    assert auth.get("npc_id") != "guard_captain"

    scenario_id = "bx5_guard_gate_guard_distinct"
    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text=player_text,
        gm_line='Gate Guard says, "North arch, mud lane."',
        pre_set_target="gate_guard",
        scenario_id=scenario_id,
    )

    assert obs.routed_speaker_id == "gate_guard"
    _assert_protected_resolved_turn(obs, scenario_id=scenario_id, expected_speaker_id="gate_guard")
    assert obs.replay_selected_speaker_id != "guard_captain"
    assert obs.final_resolved_speaker_id != "guard_captain"


def test_bx5_protected_golden_ambiguous_guard_no_false_parity() -> None:
    session, world, scene = ambiguous_guard_scene_bundle()
    scenario_id = "bx5_guard_ambiguous_multi_guard"
    obs = observe_ambiguous_guard_gate_replay(
        session=session,
        world=world,
        scene=scene,
        scenario_id=scenario_id,
    )

    assert obs.routed_resolved is False
    assert obs.contract_primary_speaker_id in (None, "")
    assert_protected_golden_turn_observation(
        obs.replay_observation,
        protected_bx_ambiguous_guard_parity_expectation(),
        scenario_id=scenario_id,
        debug_context=obs.as_checkpoint_record().__repr__(),
    )
    assert_ambiguous_guard_golden_parity(
        obs,
        expected_candidates=frozenset({"guard_captain", "gate_sentry"}),
    )


def test_bx5_ambiguous_guard_risk_family_report_includes_parity_fields() -> None:
    session, world, scene = ambiguous_guard_scene_bundle()
    obs = observe_ambiguous_guard_gate_replay(
        session=session,
        world=world,
        scene=scene,
        scenario_id="bx5_guard_ambiguous_risk_report",
    )
    rows = speaker_contract_family_risk_rows([("ambiguous_multi_guard", obs.speaker_contract)])
    assert rows == [
        {
            "family": "ambiguous_multi_guard",
            "total": obs.risk.total,
            "band": obs.risk.band,
            "risk_S": obs.risk.S,
            "first_divergence": obs.speaker_contract.first_divergence_checkpoint_id,
            "speaker_status": "ambiguous",
            "text_parity": True,
            "attribution_score": obs.risk.A,
            "replay_selected_speaker_id": None,
            "replay_selected_speaker_source": obs.replay_selected_speaker_source,
            "speaker_projection_parity_status": "final_ambiguous",
            "final_observed_speaker_id": None,
            "final_observed_status": "ambiguous",
        }
    ]
    assert rows[0]["risk_S"] >= 20
    assert rows[0]["band"] in {"guarded", "elevated", "high"}
    assert rows[0]["speaker_projection_parity_status"] != "aligned"


def test_bx5_resolved_guard_risk_family_report_low_band() -> None:
    session, world, scene = frontier_gate_base_session_scene()
    obs = observe_ambiguous_guard_gate_replay(
        session=session,
        world=world,
        scene=scene,
        player_text="guard_captain, status?",
        gm_line='Guard Captain says, "All clear."',
        scenario_id="bx5_guard_resolved_risk_report",
    )
    rows = speaker_contract_family_risk_rows([("canonical_guard_captain", obs.speaker_contract)])
    assert rows[0]["risk_S"] == 0
    assert rows[0]["band"] == "low"
    assert rows[0]["speaker_projection_parity_status"] == "aligned"
    assert rows[0]["replay_selected_speaker_id"] == "guard_captain"
    assert rows[0]["final_observed_speaker_id"] == "guard_captain"
