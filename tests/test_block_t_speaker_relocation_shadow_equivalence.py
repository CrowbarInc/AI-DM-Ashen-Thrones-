"""Block T — shadow dual-run: Gate speaker enforcement vs isolated ``speaker_contract_enforcement`` repairs.

Infrastructure only; does not change production ordering or emitted prose defaults.
"""
from __future__ import annotations

import copy

import pytest

import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from tests.helpers.speaker_relocation_shadow_harness import (
    ShadowEnforceCapture,
    build_finalize_stack_fixture,
    install_dual_run_enforce,
    run_isolated_enforce_mirror,
    with_finalize_delta,
)
from tests.helpers.speaker_gate_order import normalized_player_text_equal
from tests.test_block_s_speaker_local_rebind_equivalence import (
    _locked_runner_contract,
    _stub_strict_social_details,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.final_emission_gate_fixtures import runner_strict_bundle

pytestmark = pytest.mark.unit


def _eff_runner_aligned(resolution: dict) -> dict:
    er = copy.deepcopy(resolution)
    er.setdefault("social", {})
    er["social"]["npc_id"] = "runner"
    er["social"]["npc_name"] = "Tavern Runner"
    return er


def test_block_t_dual_run_gate_matches_isolated_continuity_locked_opening_mismatch(monkeypatch):
    """Fixture: continuity-locked wrong opening label → ``local_rebind``; Gate vs isolated equivalence."""
    session, world, sid, resolution, line = build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
    )

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    eq = cap.equivalence
    assert eq is not None
    assert eq.normalized_text_match is True
    assert eq.repair_flags_match is True
    assert eq.final_reason_match is True
    assert eq.post_validation_match is True
    assert eq.repair_flags_gate.get("local_rebind_applied") is True
    assert eq.repair_flags_gate.get("canonical_rewrite_applied") is not True
    assert eq.repair_flags_gate.get("narrator_neutral_applied") is not True

    final = (out.get("player_facing_text") or "").strip()
    eq2 = with_finalize_delta(eq, final)
    assert isinstance(eq2.downstream_finalize_delta, bool)
    assert "Tavern Runner" in final


def test_block_aa_dual_run_declared_alias_dialogue_plan_shadow_equivalence(monkeypatch):
    """Block AA closeout: Block Z declared aliases + passing dialogue plan + local_rebind → shadow equivalence holds."""
    def configure_resolution(resolution: dict) -> None:
        attach_dialogue_social_plan_to_resolution(
            resolution,
            make_valid_dialogue_social_plan(
                speaker_id="tavern_runner",
                speaker_name="Tavern Runner",
                dialogue_intent="question",
                allowed_pregate_speaker_labels=["Ragged stranger"],
                speaker_alias_resolution_source="manual_bundle_override",
            ),
        )

    session, world, sid, resolution, line = build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
        configure_resolution=configure_resolution,
    )

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    eq = cap.equivalence
    assert eq is not None
    assert eq.normalized_text_match is True
    assert eq.repair_flags_match is True
    assert eq.final_reason_match is True
    assert eq.post_validation_match is True
    assert eq.repair_flags_gate.get("local_rebind_applied") is True
    assert eq.repair_flags_gate.get("canonical_rewrite_applied") is not True
    assert eq.repair_flags_gate.get("narrator_neutral_applied") is not True

    final = (out.get("player_facing_text") or "").strip()
    eq2 = with_finalize_delta(eq, final)
    assert isinstance(eq2.downstream_finalize_delta, bool)
    assert "Tavern Runner" in final


def test_block_t_quoted_dialogue_layers_shadow_records_downstream_delta(monkeypatch):
    """Fixture: quoted strict-social line through NA/tone/authority (validation-only); finalize may reshape."""
    session, world, sid, resolution, line = build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
        line='Ragged stranger says, "The east lanes hear everything late."',
    )

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    eq = cap.equivalence
    assert eq is not None
    assert eq.normalized_text_match is True
    final = (out.get("player_facing_text") or "").strip()
    eqf = with_finalize_delta(eq, final)
    # Downstream stack may change normalized text after speaker enforcement (visibility, N4, finalize, …).
    assert eqf.downstream_finalize_delta in (True, False)


def test_block_t_unit_isolated_mirror_matches_gate_enforce_direct(monkeypatch):
    """Direct gate entry vs isolated mirror (no full gate): same repair metadata slice."""
    session, world, sid, resolution = runner_strict_bundle()
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(_locked_runner_contract()))

    line = 'Ragged stranger says, "No names, only rumors."'
    gm: dict = {"metadata": {}}
    eff = _eff_runner_aligned(resolution)

    gate_text, gate_p = feg.enforce_emitted_speaker_with_contract(
        line,
        gm_output=gm,
        resolution=resolution,
        eff_resolution=eff,
        world=world,
        scene_id=sid,
    )

    gm2: dict = {"metadata": {}}
    eff2 = _eff_runner_aligned(resolution)
    iso_text, iso_p = run_isolated_enforce_mirror(
        line,
        gm_output=gm2,
        resolution=copy.deepcopy(resolution),
        eff_resolution=eff2,
        world=world,
        scene_id=sid,
    )

    assert normalized_player_text_equal(gate_text, iso_text)
    assert gate_p.get("final_reason_code") == iso_p.get("final_reason_code")
    gr = gate_p.get("repair") or {}
    ir = iso_p.get("repair") or {}
    assert gr.get("local_rebind_applied") == ir.get("local_rebind_applied")
