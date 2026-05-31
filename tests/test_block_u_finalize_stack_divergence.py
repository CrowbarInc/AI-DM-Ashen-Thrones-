"""Block U — post-speaker divergence probes; Block V/W — dialogue-social plan vs local_rebind ordering."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.post_speaker_finalize_probe import (
    POST_SPEAKER_PROBE_ORDER,
    chain_enforce_phase_marker,
    first_post_speaker_normalized_divergence,
    install_post_speaker_text_probes,
    post_speaker_events_only,
)
from tests.helpers.speaker_relocation_shadow_harness import (
    ShadowEnforceCapture,
    build_finalize_stack_fixture,
    install_dual_run_enforce,
)
from tests.test_block_s_speaker_local_rebind_equivalence import (
    _locked_runner_contract,
    _stub_strict_social_details,
)
from tests.helpers.final_emission_gate_fixtures import runner_strict_bundle

pytestmark = pytest.mark.unit


@pytest.fixture
def local_rebind_strict_bundle(monkeypatch):
    return build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
    )


@pytest.fixture
def local_rebind_canonical_plan_with_declared_alias_bundle(monkeypatch):
    """Canonical ``speaker_id`` / ``speaker_name`` (Tavern Runner) + declared pregate alias (Block Z)."""
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

    return build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
        configure_resolution=configure_resolution,
    )


@pytest.fixture
def local_rebind_passing_dialogue_plan_bundle(monkeypatch):
    """Same as default local_rebind bundle plus a **valid** ``dialogue_social_plan`` on resolution (Block V).

    Plan speakers must match **pregate** attribution (`Ragged stranger`), not post-``local_rebind``
    canonicalization (`Tavern Runner`): dialogue-plan invariant runs before strict-social build/speaker repair.
    """
    def configure_resolution(resolution: dict) -> None:
        attach_dialogue_social_plan_to_resolution(
            resolution,
            make_valid_dialogue_social_plan(
                speaker_id="ragged_stranger",
                speaker_name="Ragged stranger",
                dialogue_intent="question",
            ),
        )

    return build_finalize_stack_fixture(
        monkeypatch,
        contract=_locked_runner_contract(),
        strict_social_details=_stub_strict_social_details,
        configure_resolution=configure_resolution,
    )


def test_block_u_first_post_speaker_divergence_is_dialogue_plan_strip(local_rebind_strict_bundle, monkeypatch):
    """Inventory anchor: inline dialogue-plan subtractive strip changes normalized text before late-stack layers."""
    session, world, sid, resolution, line = local_rebind_strict_bundle
    events = []
    phase = SimpleNamespace(after_enforce=False)

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert cap.equivalence is not None
    assert cap.equivalence.normalized_text_match is True

    first = first_post_speaker_normalized_divergence(events)
    assert first == "dialogue_plan_subtractive_strip"
    assert first in POST_SPEAKER_PROBE_ORDER

    final = (out.get("player_facing_text") or "").strip()
    assert "Tavern Runner" in final


def test_block_u_safe_layers_before_first_post_speaker_change(local_rebind_strict_bundle, monkeypatch):
    """Strict-social trunk layers before subtractive strip: no normalized text change at probe granularity."""
    session, world, sid, resolution, line = local_rebind_strict_bundle
    events = []
    phase = SimpleNamespace(after_enforce=False)

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert cap.equivalence is not None

    post_only = post_speaker_events_only(events)
    first_idx = next((i for i, e in enumerate(post_only) if e.normalized_changed), None)
    assert first_idx is not None
    for e in post_only[:first_idx]:
        assert not e.normalized_changed, e.layer_id


def test_block_v_passing_dialogue_plan_avoids_subtractive_strip_as_first_diverger(
    local_rebind_passing_dialogue_plan_bundle, monkeypatch
):
    """With a passing dialogue-social plan, subtractive strip is not the first post-speaker diverger."""
    session, world, sid, resolution, line = local_rebind_passing_dialogue_plan_bundle
    events = []
    phase = SimpleNamespace(after_enforce=False)

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert cap.equivalence is not None
    assert cap.equivalence.normalized_text_match is True

    first = first_post_speaker_normalized_divergence(events)
    assert first != "dialogue_plan_subtractive_strip"
    # Empirical: no probed layer changes normalized text vs post-speaker baseline for this bundle.
    assert first is None
    strip_hits = [e for e in events if e.layer_id == "dialogue_plan_subtractive_strip"]
    assert not any(e.normalized_changed for e in strip_hits)
    assert '"' in (out.get("player_facing_text") or "")


def test_block_w_canonical_only_plan_still_mismatch_without_declared_alias(monkeypatch):
    """Canonical plan without declared alias rows still fails closed on pregate writer alias."""
    session, world, sid, resolution = runner_strict_bundle()
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
        ),
    )
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(_locked_runner_contract()))

    build_inputs: list[str] = []

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        build_inputs.append(str(candidate_text or ""))
        return 'Ragged stranger says, "No names, only rumors."', _stub_strict_social_details()

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any(str(r).startswith("attributed_speaker_mismatch:") for r in reasons)
    assert build_inputs and build_inputs[0] != pre_gate_line.strip()


def test_block_z_canonical_plan_with_declared_alias_passes_dialogue_plan_gate(monkeypatch):
    """Phase 2: declared ``allowed_pregate_speaker_labels`` accepts pregate alias before speaker repair."""
    session, world, sid, resolution = runner_strict_bundle()
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
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(_locked_runner_contract()))

    build_inputs: list[str] = []

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        build_inputs.append(str(candidate_text or ""))
        return 'Ragged stranger says, "No names, only rumors."', _stub_strict_social_details()

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("dialogue_plan_valid") is True
    assert build_inputs and build_inputs[0].strip() == pre_gate_line.strip()


def test_block_z_canonical_plus_declared_alias_avoids_subtractive_strip_first(
    local_rebind_canonical_plan_with_declared_alias_bundle, monkeypatch
):
    """Block Z + Block U: canonical id + declared alias → dialogue-plan strip is not first diverger."""
    session, world, sid, resolution, line = local_rebind_canonical_plan_with_declared_alias_bundle
    events = []
    phase = SimpleNamespace(after_enforce=False)

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert cap.equivalence is not None
    first = first_post_speaker_normalized_divergence(events)
    assert first != "dialogue_plan_subtractive_strip"
    assert first is None
    strip_hits = [e for e in events if e.layer_id == "dialogue_plan_subtractive_strip"]
    assert not any(e.normalized_changed for e in strip_hits)
    assert '"' in (out.get("player_facing_text") or "")
