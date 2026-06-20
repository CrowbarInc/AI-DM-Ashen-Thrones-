"""Block U — post-speaker divergence probes; Block V/W — dialogue-social plan vs local_rebind ordering."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from game.final_emission_gate import apply_final_emission_gate
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output
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
pytestmark = pytest.mark.unit


@pytest.fixture
def local_rebind_strict_bundle(monkeypatch):
    return build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
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
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
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
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
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
    meta = final_emission_meta_from_output(out) or {}
    strip_deferred = bool(meta.get("dialogue_plan_subtractive_strip_deferred"))
    strip_changed = any(
        e.layer_id == "dialogue_plan_subtractive_strip" and e.normalized_changed for e in events
    )
    if strip_changed:
        assert first == "dialogue_plan_subtractive_strip"
        assert first in POST_SPEAKER_PROBE_ORDER
    else:
        assert first != "dialogue_plan_subtractive_strip"
        if strip_deferred:
            assert not strip_changed

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

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert cap.equivalence is not None

    post_only = post_speaker_events_only(events)
    first_idx = next((i for i, e in enumerate(post_only) if e.normalized_changed), None)
    strip_changed = any(
        e.layer_id == "dialogue_plan_subtractive_strip" and e.normalized_changed for e in post_only
    )
    if strip_changed:
        assert first_idx is not None
        for e in post_only[:first_idx]:
            assert not e.normalized_changed, e.layer_id
    else:
        assert not any(e.normalized_changed for e in post_only)


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
    build_inputs: list[str] = []

    def configure_resolution(resolution: dict) -> None:
        attach_dialogue_social_plan_to_resolution(
            resolution,
            make_valid_dialogue_social_plan(
                speaker_id="tavern_runner",
                speaker_name="Tavern Runner",
                dialogue_intent="question",
            ),
        )

    session, world, sid, resolution, pre_gate_line = build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
        configure_resolution=configure_resolution,
        build_inputs=build_inputs,
    )
    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any(str(r).startswith("attributed_speaker_mismatch:") for r in reasons)
    assert build_inputs and build_inputs[0] != pre_gate_line.strip()


def test_block_z_canonical_plan_with_declared_alias_passes_dialogue_plan_gate(monkeypatch):
    """Phase 2: declared ``allowed_pregate_speaker_labels`` accepts pregate alias before speaker repair."""
    build_inputs: list[str] = []

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

    session, world, sid, resolution, pre_gate_line = build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
        configure_resolution=configure_resolution,
        build_inputs=build_inputs,
    )

    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    meta = final_emission_meta_from_output(out) or {}
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
