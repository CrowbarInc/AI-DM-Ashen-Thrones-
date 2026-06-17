"""Block S — local_rebind relocation equivalence harness (ordering + fixtures, no upstream move)."""
from __future__ import annotations

import copy

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.speaker_contract_enforcement import enforce_emitted_speaker_with_contract
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output
from tests.helpers.gate_equivalence_monkeypatch import (
    install_strict_social_trunk_phase_trackers,
    patch_get_speaker_selection_contract,
)
from tests.helpers.speaker_gate_order import (
    CHAIN_SOCIAL_TO_POST_SPEAKER,
    assert_phase_subsequence,
    normalized_player_text_equal,
)
from tests.helpers.speaker_relocation_shadow_harness import build_finalize_stack_fixture
from tests.helpers.strict_social_harness import runner_strict_bundle

pytestmark = pytest.mark.unit


def test_block_s_strict_social_phase_order_wrapped_build(monkeypatch):
    """Same chain when social build is wrapped (avoid overwriting tracked build)."""
    session, world, sid, resolution = runner_strict_bundle()
    order: list[str] = []
    install_strict_social_trunk_phase_trackers(
        monkeypatch, order, strict_social_details=stub_strict_social_details
    )

    apply_final_emission_gate(
        {'player_facing_text': 'Tavern Runner says, "Order chain."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert_phase_subsequence(order, CHAIN_SOCIAL_TO_POST_SPEAKER)


def test_block_s_local_rebind_full_gate_metadata_not_canonical_or_neutral(monkeypatch):
    """Wrong opening label + continuity lock → local_rebind; no canonical_rewrite / narrator_neutral flags."""
    session, world, sid, resolution, line = build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
    )

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = (out.get("player_facing_text") or "").strip()

    em = (out.get("metadata") or {}).get("emission_debug") or {}
    sp = em.get("speaker_contract_enforcement") or {}
    repair = sp.get("repair") or {}
    assert repair.get("local_rebind_applied") is True
    assert repair.get("canonical_rewrite_applied") is not True
    assert repair.get("narrator_neutral_applied") is not True
    assert (final_emission_meta_from_output(out) or {}).get("speaker_contract_enforcement_reason") == "continuity_locked_speaker_repair"
    # Opening attribution repair ran (labels canonicalized); downstream Gate layers may still reshape
    # quoted payloads for unrelated boundary reasons — metadata proves the local_rebind branch, not final prose.
    assert "Tavern Runner" in text


def test_block_s_comparison_helper_self_consistent_with_direct_string():
    assert normalized_player_text_equal("  A  \n", "A")
    assert not normalized_player_text_equal("A", "B")


def test_block_s_local_rebind_gate_entry_preserves_full_line_same_as_block_b_direct(monkeypatch):
    """Speaker boundary only: canonical opening label + quoted span unchanged (matches Block B direct test)."""
    session, world, sid, resolution = runner_strict_bundle()
    eff_resolution = copy.deepcopy(resolution)
    eff_resolution["social"]["npc_id"] = "runner"
    eff_resolution["social"]["npc_name"] = "Tavern Runner"
    gm: dict = {"metadata": {}}
    patch_get_speaker_selection_contract(monkeypatch, locked_runner_contract())

    repaired, payload = enforce_emitted_speaker_with_contract(
        'Ragged stranger says, "No names, only rumors."',
        gm_output=gm,
        resolution=resolution,
        eff_resolution=eff_resolution,
        world=world,
        scene_id=sid,
    )
    assert normalized_player_text_equal(repaired, 'Tavern Runner says, "No names, only rumors."')
    assert payload["repair"]["local_rebind_applied"] is True
    assert payload["repair"].get("canonical_rewrite_applied") is not True
    assert payload["repair"].get("narrator_neutral_applied") is not True
