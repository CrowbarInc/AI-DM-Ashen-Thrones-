"""BX1 — Canonical speaker observation contract and guard matrix.

Test-only coverage proving (or measuring gaps in) speaker identity parity across:

routing → enforcement → finalization → replay projection

Focus: frontier_gate guard/captain roster — role alias ``guard``, canonical
``guard_captain``, distinct ``gate_guard``, and ambiguous multi-guard rosters.
Does not modify production behavior.
"""
from __future__ import annotations

import pytest

from game.defaults import default_world
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_speaker_observation import read_final_speaker_observation
from tests.helpers.bx_guard_speaker_parity import (
    AMBIGUOUS_GUARD_PLAYER_TEXT,
    ambiguous_guard_scene_bundle,
    assert_ambiguous_guard_golden_parity,
    assert_resolved_guard_golden_parity,
    checkpoint_by_id,
    frontier_gate_base_session_scene,
    gate_guard_addressable,
    observe_ambiguous_guard_gate_replay,
    observe_guard_lifecycle,
    reconciled_resolution,
    route_authoritative,
    second_guard_addressable,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.speaker_contract_risk import (
    CHECKPOINT_FINAL,
    observe_final_to_replay_speaker_contract,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Case A — role alias routes canonically (guard → guard_captain)
# ---------------------------------------------------------------------------


def test_case_a_role_alias_guard_routes_to_guard_captain(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, scene = frontier_gate_base_session_scene()
    player_text = "Guard, who posted that notice?"
    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text=player_text,
        gm_line='Guard says, "The captain posted it at dawn."',
    )

    assert obs.routed_speaker_id == "guard_captain"
    assert_resolved_guard_golden_parity(obs, expected_speaker_id="guard_captain")
    assert obs.final_emitted_speaker_label == "Guard Captain"
    assert obs.final_speaker_observation is not None
    assert obs.final_speaker_observation.get("status") == "resolved"
    assert obs.final_speaker_observation.get("canonical_speaker_id") == "guard_captain"
    assert obs.risk.band == "low"


# ---------------------------------------------------------------------------
# Case B — canonical ID remains canonical (guard_captain)
# ---------------------------------------------------------------------------


def test_case_b_canonical_id_guard_captain_remains_canonical(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, scene = frontier_gate_base_session_scene()
    player_text = "guard_captain, who posted that notice?"
    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text=player_text,
        gm_line='Guard Captain says, "I posted it at dawn."',
    )

    assert obs.routed_speaker_id == "guard_captain"
    assert_resolved_guard_golden_parity(obs, expected_speaker_id="guard_captain")
    assert obs.final_emitted_speaker_label == "Guard Captain"
    assert obs.final_speaker_observation is not None
    assert obs.final_speaker_observation.get("status") == "resolved"
    assert obs.final_speaker_observation.get("canonical_speaker_id") == "guard_captain"


# ---------------------------------------------------------------------------
# Case C — distinct gate_guard must not collapse into guard_captain
# ---------------------------------------------------------------------------


def test_case_c_gate_guard_distinct_from_guard_captain(monkeypatch: pytest.MonkeyPatch) -> None:
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

    obs = observe_guard_lifecycle(
        monkeypatch,
        session=session,
        world=world,
        scene=scene,
        player_text=player_text,
        gm_line='Gate Guard says, "North arch, mud lane."',
        pre_set_target="gate_guard",
    )

    assert obs.routed_speaker_id == "gate_guard"
    assert obs.contract_primary_speaker_id == "gate_guard"
    assert obs.final_resolved_speaker_id == "gate_guard"
    assert obs.replay_selected_speaker_id == "gate_guard"
    assert obs.enforcement_post_speaker_id == "gate_guard"
    assert obs.final_emitted_speaker_label == "Gate Guard"
    assert_resolved_guard_golden_parity(obs, expected_speaker_id="gate_guard")

    assert obs.replay_selected_speaker_id != "guard_captain"
    assert obs.final_resolved_speaker_id != "guard_captain"
    assert obs.final_speaker_observation is not None
    assert obs.final_speaker_observation.get("status") == "resolved"
    assert obs.final_speaker_observation.get("canonical_speaker_id") == "gate_guard"


# ---------------------------------------------------------------------------
# Case D — ambiguous multi-guard roster must not guess
# ---------------------------------------------------------------------------


def test_case_d_ambiguous_guard_roster_routing_unresolved() -> None:
    session, world, scene = ambiguous_guard_scene_bundle()
    auth = route_authoritative(session, world, scene, AMBIGUOUS_GUARD_PLAYER_TEXT)

    assert auth.get("target_resolved") is False
    assert auth.get("npc_id") in (None, "")
    assert auth.get("source") == "none"


def test_case_d_ambiguous_guard_reconcile_preserves_routing_ambiguity() -> None:
    session, world, scene = ambiguous_guard_scene_bundle()
    _resolution, contract, eff = reconciled_resolution(session, world, AMBIGUOUS_GUARD_PLAYER_TEXT)
    auth = route_authoritative(session, world, scene, AMBIGUOUS_GUARD_PLAYER_TEXT)

    assert auth.get("target_resolved") is False
    assert contract.get("primary_speaker_id") in (None, "")
    assert (eff or {}).get("social", {}).get("npc_id") in (None, "")


def test_case_d_ambiguous_guard_speaker_contract_risk_reports_unresolved() -> None:
    session, world, scene = ambiguous_guard_scene_bundle()
    player_text = AMBIGUOUS_GUARD_PLAYER_TEXT
    resolution, contract, eff = reconciled_resolution(session, world, player_text)
    out = apply_final_emission_gate(
        {"player_facing_text": 'Guard says, "Maybe."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
    )
    fso = read_final_speaker_observation(out)
    assert fso is not None
    assert fso.get("status") in {"ambiguous", "unresolved"}
    assert fso.get("routing_speaker_id") in (None, "")
    assert fso.get("contract_primary_speaker_id") in (None, "")
    assert len(fso.get("candidates") or []) >= 2

    speaker_obs = observe_final_to_replay_speaker_contract(
        gm_output=out,
        resolution=eff,
        player_text=player_text,
        expected_speaker_id=contract.get("primary_speaker_id"),
        expected_speaker_name=contract.get("primary_speaker_name"),
        expected_speaker_source=contract.get("primary_speaker_source"),
        enforcement_owner="game.speaker_contract_enforcement",
    )

    final_cp = checkpoint_by_id(speaker_obs, CHECKPOINT_FINAL)
    assert final_cp.speaker_status in {"ambiguous", "unresolved"}
    assert speaker_obs.risk.S >= 20
    replay_parity = speaker_obs.replay_speaker_projection_parity
    assert isinstance(replay_parity, dict)
    assert replay_parity.get("status") in {"final_ambiguous", "final_unresolved"}


def test_case_d_ambiguous_guard_measured_convergence_record() -> None:
    """BX4: ambiguous generic role stays unresolved through reconcile, stamp, and replay parity."""
    session, world, scene = ambiguous_guard_scene_bundle()
    auth = route_authoritative(session, world, scene, AMBIGUOUS_GUARD_PLAYER_TEXT)
    obs = observe_ambiguous_guard_gate_replay(session=session, world=world, scene=scene)

    assert auth.get("target_resolved") is False
    assert obs.contract_primary_speaker_id in (None, "")
    fso = obs.final_speaker_observation
    assert fso is not None
    assert fso.get("status") == "ambiguous"
    assert fso.get("canonical_speaker_id") is None
    assert fso.get("routing_speaker_id") in (None, "")
    assert "guard_captain" in (fso.get("candidates") or [])
    assert "gate_sentry" in (fso.get("candidates") or [])
    assert "routing_unresolved_contract_primary_present" not in (fso.get("notes") or [])

    assert_ambiguous_guard_golden_parity(
        obs,
        expected_candidates=frozenset({"guard_captain", "gate_sentry"}),
    )

    meta = final_emission_meta_from_output(obs.gate_output) or {}
    assert meta.get("speaker_contract_enforcement_reason") is not None
