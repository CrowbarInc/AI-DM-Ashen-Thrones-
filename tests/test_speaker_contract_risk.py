"""BT1 — Speaker Contract Risk observation helper tests."""
from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_visibility_fallback as visibility_fallback
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS
from game.speaker_contract_enforcement import enforce_emitted_speaker_with_contract
from game.storage import get_scene_runtime
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.narrative_mode_validator_fixtures import (
    build_validator_narrative_mode_contract,
    minimal_ctir_continuation,
)
from tests.helpers.post_speaker_finalize_probe import (
    LayerTextDelta,
    chain_enforce_phase_marker,
    install_post_speaker_text_probes,
)
from tests.helpers.speaker_contract_risk import (
    CHECKPOINT_FINAL,
    CHECKPOINT_POST_SPEAKER,
    CHECKPOINT_PRE_SPEAKER,
    CHECKPOINT_REPLAY,
    SpeakerContractObservation,
    checkpoint_text_hash,
    final_replay_parity_record,
    observe_final_to_replay_speaker_contract,
    observe_speaker_contract,
    replay_speaker_evidence_unavailable,
    score_speaker_contract_risk,
    speaker_contract_family_risk_rows,
)
from tests.helpers.speaker_relocation_shadow_harness import (
    ShadowEnforceCapture,
    build_finalize_stack_fixture,
    install_dual_run_enforce,
)
from tests.helpers.strict_social_harness import runner_strict_bundle

pytestmark = pytest.mark.unit

_MATCH_LINE = 'Tavern Runner says, "No names, only rumors."'


def test_no_divergence_scores_zero() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
        replay_observation={
            "final_text": _MATCH_LINE,
            "selected_speaker_id": "runner",
            "selected_speaker_source": "turn_trace.social_contract_trace",
        },
    )

    assert obs.mismatch_present is False
    assert obs.first_divergence_checkpoint_id is None
    assert obs.risk.total == 0
    assert obs.risk.band == "low"


def test_dialogue_plan_strip_localizes_first_divergence() -> None:
    post = 'Tavern Runner says, "No names, only rumors."'
    final = "Tavern Runner studies the room."
    events = [
        LayerTextDelta(
            layer_id="dialogue_plan_subtractive_strip",
            normalized_changed=True,
            normalized_input_hash=checkpoint_text_hash(post),
            normalized_output_hash=checkpoint_text_hash(final),
            normalized_input_text=post,
            normalized_output_text=final,
            input_speaker_signature={"speaker_label": "Tavern Runner", "speaker_name": "Tavern Runner"},
            output_speaker_signature={"speaker_label": "Tavern Runner", "speaker_name": "Tavern Runner"},
        )
    ]

    obs = observe_speaker_contract(
        pre_speaker_text=post,
        gate_post_speaker_text=post,
        final_player_text=final,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
        layer_events=events,
    )

    assert obs.first_divergence_layer_id == "dialogue_plan_subtractive_strip"
    assert obs.first_divergence_checkpoint_id == "P2_dialogue_plan_subtractive_strip"
    assert obs.mismatch_present is True
    assert obs.risk.D == 0
    assert obs.risk.T == 10


def test_dialogue_plan_strip_live_fixture_when_observed(local_rebind_strict_bundle, monkeypatch) -> None:
    """When runtime emits subtractive-strip probe events, observation localizes them."""
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
    strip_events = [e for e in events if e.layer_id == "dialogue_plan_subtractive_strip" and e.normalized_changed]
    if not strip_events:
        pytest.skip("post-speaker subtractive strip deferred or absent on this branch")

    final_text = (out.get("player_facing_text") or "").strip()
    obs = observe_speaker_contract(
        pre_speaker_text=cap.equivalence.pre_speaker_text,
        gate_post_speaker_text=cap.equivalence.gate_post_speaker_text,
        final_player_text=final_text,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
        layer_events=events,
    )

    assert obs.first_divergence_layer_id == "dialogue_plan_subtractive_strip"


def test_unresolved_speaker_increments_s_without_crash() -> None:
    line = '"No names, only rumors," he replies.'
    obs = observe_speaker_contract(
        pre_speaker_text=line,
        gate_post_speaker_text=line,
        final_player_text=line,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
    )

    post = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_POST_SPEAKER)
    assert post.speaker_status in {"unresolved", "ambiguous", "unattributed"}
    assert obs.risk.S == 20
    assert obs.risk.total >= 20


def test_missing_owner_source_increments_a() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        replay_observation={
            "final_text": _MATCH_LINE,
            "selected_speaker_id": "runner",
        },
    )

    assert obs.risk.A >= 10
    assert obs.risk.A <= 20


def test_text_mismatch_without_layer_evidence_increments_t() -> None:
    post = _MATCH_LINE
    final = 'Tavern Runner says, "Different final wording."'
    obs = observe_speaker_contract(
        pre_speaker_text=post,
        gate_post_speaker_text=post,
        final_player_text=final,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
        layer_events=[],
    )

    assert obs.mismatch_present is True
    assert obs.first_divergence_checkpoint_id == CHECKPOINT_FINAL
    assert obs.first_divergence_layer_id is None
    assert obs.risk.T == 25
    assert obs.risk.D == 0


def test_mismatch_without_checkpoint_localization_scores_d() -> None:
    partial = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text='Tavern Runner says, "Changed downstream."',
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        layer_events=[],
    )
    risk = score_speaker_contract_risk(
        SpeakerContractObservation(
            checkpoints=partial.checkpoints,
            layer_events=partial.layer_events,
            expected_speaker_id=partial.expected_speaker_id,
            expected_speaker_source=None,
            enforcement_owner=None,
            replay_selected_speaker_id=None,
            replay_selected_speaker_source=None,
            first_text_divergence_checkpoint_id=None,
            first_speaker_divergence_checkpoint_id=None,
            first_divergence_checkpoint_id=None,
            first_divergence_layer_id=None,
            mismatch_present=True,
            risk=partial.risk,
        )
    )
    assert risk.D == 15
    assert risk.T == 25


@pytest.fixture
def local_rebind_strict_bundle(monkeypatch):
    return build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
    )


def test_example_observation_record_shape() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text='Ragged stranger says, "No names, only rumors."',
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
    )
    record = obs.as_record()
    assert record["checkpoints"][0]["checkpoint_id"] == CHECKPOINT_PRE_SPEAKER
    assert "risk" in record
    assert set(record["risk"]) >= {"D", "S", "T", "A", "total", "band"}


def _parity_resolution(*, npc_id: str = "runner") -> dict[str, object]:
    return {"kind": "social", "social": {"npc_id": npc_id, "npc_name": "Tavern Runner"}}


def test_bt2_final_text_hash_parity_between_p3_and_p4() -> None:
    obs = observe_final_to_replay_speaker_contract(
        gm_output={"player_facing_text": _MATCH_LINE, "_final_emission_meta": {}},
        resolution=_parity_resolution(),
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="resolution.social.npc_id",
    )
    final_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_FINAL)
    replay_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_REPLAY)

    assert final_cp.normalized_text_hash == replay_cp.normalized_text_hash
    assert obs.risk.T == 0


def test_bt2_final_emitted_speaker_matches_replay_selected_speaker_id() -> None:
    obs = observe_final_to_replay_speaker_contract(
        gm_output={"player_facing_text": _MATCH_LINE, "_final_emission_meta": {}},
        resolution=_parity_resolution(npc_id="runner"),
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="resolution.social.npc_id",
        enforcement_owner="game.final_emission_finalize",
    )

    assert obs.replay_selected_speaker_id == "runner"
    final_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_FINAL)
    assert final_cp.resolved_speaker_id == "runner"
    assert obs.risk.S == 0


def test_bt2_emitted_speaker_mismatch_scores_s40() -> None:
    obs = observe_final_to_replay_speaker_contract(
        gm_output={"player_facing_text": _MATCH_LINE, "_final_emission_meta": {}},
        resolution=_parity_resolution(npc_id="guard"),
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="resolution.social.npc_id",
    )

    final_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_FINAL)
    assert final_cp.resolved_speaker_id == "runner"
    assert obs.replay_selected_speaker_id == "guard"
    assert obs.risk.S == 40


def test_bt2_missing_selected_speaker_source_increments_attribution_risk() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="resolution.social.npc_id",
        enforcement_owner="game.final_emission_finalize",
        replay_observation={
            "final_text": _MATCH_LINE,
            "selected_speaker_id": "runner",
            "final_text_hash": checkpoint_text_hash(_MATCH_LINE, use_golden=True),
        },
        align_final_replay_normalization=True,
    )

    assert obs.replay_selected_speaker_source is None
    assert obs.risk.A >= 5


def test_bt2_final_replay_text_mismatch_increments_t25() -> None:
    gate_text = _MATCH_LINE
    replay_text = 'Tavern Runner says, "Different replay wording."'
    obs = observe_speaker_contract(
        pre_speaker_text=gate_text,
        gate_post_speaker_text=gate_text,
        final_player_text=gate_text,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        replay_observation={
            "final_text": replay_text,
            "selected_speaker_id": "runner",
            "selected_speaker_source": "resolution.social.npc_id",
            "final_text_hash": checkpoint_text_hash(replay_text, use_golden=True),
        },
        align_final_replay_normalization=True,
    )

    assert obs.mismatch_present is True
    assert obs.first_divergence_checkpoint_id == CHECKPOINT_REPLAY
    assert obs.risk.T == 25


def test_bt2_unavailable_replay_speaker_is_explicit_not_silent_match() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        replay_observation={
            "final_text": _MATCH_LINE,
            "selected_speaker_id": None,
            "final_text_hash": checkpoint_text_hash(_MATCH_LINE, use_golden=True),
            "unavailable": ["selected_speaker_id"],
        },
        align_final_replay_normalization=True,
    )
    replay_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_REPLAY)
    replay_obs = {
        "final_text": _MATCH_LINE,
        "selected_speaker_id": None,
        "unavailable": ["selected_speaker_id"],
    }

    assert replay_speaker_evidence_unavailable(replay_obs) is True
    assert replay_cp.resolved_speaker_id is None
    assert replay_cp.speaker_status == "unresolved"
    assert replay_cp.source is None
    parity = final_replay_parity_record(obs, replay_observation=replay_obs)
    assert parity["p4_speaker_unavailable"] is True
    assert parity["speaker_id_match"] is False


def test_bt2_observe_final_to_replay_produces_p3_p4_checkpoints() -> None:
    obs = observe_final_to_replay_speaker_contract(
        gm_output={"player_facing_text": _MATCH_LINE, "_final_emission_meta": {}},
        resolution=_parity_resolution(),
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
    )
    ids = {cp.checkpoint_id for cp in obs.checkpoints}
    assert CHECKPOINT_FINAL in ids
    assert CHECKPOINT_REPLAY in ids
    record = final_replay_parity_record(obs)
    assert record["p3_final_text"] == _MATCH_LINE
    assert record["p4_final_text"] == _MATCH_LINE
    assert record["text_hash_match"] is True


# ---------------------------------------------------------------------------
# BT3 — Replacement/fallback speaker contract fixture matrix (diagnostic only)
# ---------------------------------------------------------------------------


def _runner_enforcement_contract(**overrides: object) -> dict[str, Any]:
    contract = locked_runner_contract()
    contract["generic_fallback_forbidden"] = True
    contract["forbidden_fallback_labels"] = list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
    contract.update(overrides)
    return contract


def _runner_enforcement_eff(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "question",
        "social": {
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
            "social_intent_class": "social_exchange",
        },
        "metadata": {"emission_debug": {"speaker_selection_contract": contract}},
    }


def _observe_enforcement_family(
    text_in: str,
    *,
    contract: dict[str, Any],
    expected_speaker_id: str | None,
    expected_speaker_name: str | None,
    final_player_text: str | None = None,
    enforcement_reason: str | None = None,
    narrator_neutral: bool = False,
    layer_events: list[LayerTextDelta] | None = None,
) -> SpeakerContractObservation:
    eff = _runner_enforcement_eff(contract)
    gm: dict[str, Any] = {"metadata": deepcopy(eff["metadata"]), "trace": {}}
    post_text, payload = enforce_emitted_speaker_with_contract(
        text_in,
        gm_output=gm,
        resolution=eff,
        eff_resolution=eff,
        world={},
        scene_id="scene_x",
    )
    reason = enforcement_reason or payload.get("final_reason_code")
    final = final_player_text if final_player_text is not None else post_text
    return observe_speaker_contract(
        pre_speaker_text=text_in,
        gate_post_speaker_text=post_text,
        final_player_text=final,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        expected_speaker_source="contract.primary_speaker_id" if expected_speaker_id else None,
        enforcement_owner="game.speaker_contract_enforcement",
        enforcement_reason=str(reason) if reason else None,
        narrator_neutral=narrator_neutral or reason == "narrator_neutral_no_allowed_speaker",
        layer_events=layer_events or [],
    )


def _observe_gate_with_probes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    session: dict[str, Any],
    world: dict[str, Any],
    scene_id: str,
    resolution: dict[str, Any],
    line: str,
    scene: dict[str, Any] | None = None,
    gm_extra: dict[str, Any] | None = None,
    expected_speaker_id: str | None,
    expected_speaker_name: str | None,
) -> tuple[SpeakerContractObservation, dict[str, Any]]:
    events: list[LayerTextDelta] = []
    phase = SimpleNamespace(after_enforce=False)
    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    gm: dict[str, Any] = {"player_facing_text": line, "tags": []}
    if gm_extra:
        gm.update(gm_extra)

    if scene is not None:
        out, _ = apply_final_emission_gate_consumer(
            gm,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            scene=scene,
            world=world,
        )
    else:
        out = apply_final_emission_gate(
            gm,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
        )

    eq = cap.equivalence
    assert eq is not None
    final_text = (out.get("player_facing_text") or "").strip()
    obs = observe_speaker_contract(
        pre_speaker_text=eq.pre_speaker_text,
        gate_post_speaker_text=eq.gate_post_speaker_text,
        final_player_text=final_text,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        expected_speaker_source="contract.primary_speaker_id" if expected_speaker_id else None,
        enforcement_owner="game.speaker_contract_enforcement",
        layer_events=events,
    )
    return obs, out


def _referential_local_substitution_bundle() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = default_scene(sid)
    set_social_target(session, "tavern_runner")
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Runner, what do you hear about the patrol?"
    resolution = {
        "kind": "question",
        "prompt": "Runner, what do you hear about the patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
        },
        "metadata": {
            "response_type_contract": {"required_response_type": "dialogue", "allow_escalation": True},
        },
    }
    return session, world, scene, sid, resolution


def _minimal_n4_narrative_plan(*, acceptance_quality: dict[str, Any] | None = None) -> dict[str, Any]:
    nmc = build_validator_narrative_mode_contract(ctir=minimal_ctir_continuation())
    plan: dict[str, Any] = {"narrative_mode_contract": nmc}
    if acceptance_quality is not None:
        plan["acceptance_quality_contract"] = acceptance_quality
    return plan


def _assert_bt3_common(family: str, obs: SpeakerContractObservation, *, expect_owner: bool) -> None:
    assert obs is not None, family
    rescored = score_speaker_contract_risk(obs)
    assert rescored == obs.risk, family
    assert obs.first_divergence_checkpoint_id is None or isinstance(obs.first_divergence_checkpoint_id, str), family

    for cp in obs.checkpoints:
        if cp.checkpoint_id in {CHECKPOINT_POST_SPEAKER, CHECKPOINT_FINAL, CHECKPOINT_REPLAY}:
            assert cp.speaker_status in {"resolved", "neutral", "unattributed", "ambiguous", "unresolved"}, family

    if expect_owner:
        post_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_POST_SPEAKER)
        assert post_cp.owner is not None, family


def test_bt3_replacement_fallback_fixture_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each replacement/fallback family yields a measurable SpeakerContractObservation."""
    cases: list[tuple[str, SpeakerContractObservation, dict[str, Any]]] = []

    contract = _runner_enforcement_contract()
    cases.append(
        (
            "local_rebind",
            _observe_enforcement_family(
                'Merchant says, "I know nothing."',
                contract=contract,
                expected_speaker_id="runner",
                expected_speaker_name="Tavern Runner",
            ),
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    cases.append(
        (
            "canonical_rewrite",
            _observe_enforcement_family(
                "Merchant mutters under his breath without giving a straight answer.",
                contract=contract,
                expected_speaker_id="runner",
                expected_speaker_name="Tavern Runner",
            ),
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    neutral_contract = _runner_enforcement_contract(
        allowed_speaker_ids=[],
        primary_speaker_id=None,
        primary_speaker_name=None,
    )
    cases.append(
        (
            "narrator_neutral",
            _observe_enforcement_family(
                'Someone says, "Hello."',
                contract=neutral_contract,
                expected_speaker_id=None,
                expected_speaker_name=None,
                narrator_neutral=True,
                enforcement_reason="narrator_neutral_no_allowed_speaker",
            ),
            {"expect_owner": True, "expect_neutral": True, "expect_s40": False},
        )
    )

    cases.append(
        (
            "forbidden_generic_fallback",
            _observe_enforcement_family(
                'Ragged stranger mutters, "Maybe."',
                contract=contract,
                expected_speaker_id="runner",
                expected_speaker_name="Tavern Runner",
            ),
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    session, world, scene, sid, resolution = _referential_local_substitution_bundle()
    ref_line = '"Keep your wits about you," she insists, glancing nervously at the crowd.'
    ref_gm: dict[str, Any] = {
        "player_facing_text": ref_line,
        "tags": [],
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    ref_out, _ = apply_final_emission_gate_consumer(
        ref_gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    ref_final = (ref_out.get("player_facing_text") or "").strip()
    ref_meta = final_emission_meta_from_output(ref_out) or {}
    assert ref_meta.get("referential_clarity_local_substitution_applied") is True
    ref_obs = observe_speaker_contract(
        pre_speaker_text=ref_line,
        gate_post_speaker_text=ref_line,
        final_player_text=ref_final,
        expected_speaker_id="tavern_runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
    )
    cases.append(
        (
            "referential_visibility_local_substitution",
            ref_obs,
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    lr_bundle = build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
    )
    session_lr, world_lr, sid_lr, resolution_lr, line_lr = lr_bundle
    gate_lr_obs, _ = _observe_gate_with_probes(
        monkeypatch,
        session=session_lr,
        world=world_lr,
        scene_id=sid_lr,
        resolution=resolution_lr,
        line=line_lr,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
    )
    cases.append(
        (
            "local_rebind_gate",
            gate_lr_obs,
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    ss_session, ss_world, ss_sid, ss_resolution = runner_strict_bundle()
    stub_details = dict(stub_strict_social_details())
    nmc = build_validator_narrative_mode_contract(ctir=minimal_ctir_continuation())

    def _bad_build(candidate_text: str, *, resolution, tags, session, scene_id, world):
        bad = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
        return bad, dict(stub_details)

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", _bad_build)
    emerg_obs, emerg_out = _observe_gate_with_probes(
        monkeypatch,
        session=ss_session,
        world=ss_world,
        scene_id=ss_sid,
        resolution=ss_resolution,
        line="stub",
        gm_extra={"prompt_context": {"narrative_plan": {"narrative_mode_contract": nmc}}},
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
    )
    emerg_meta = final_emission_meta_from_output(emerg_out) or {}
    assert emerg_meta.get("final_emitted_source") == "minimal_social_emergency_fallback"
    cases.append(
        (
            "strict_social_emergency_fallback",
            emerg_obs,
            {"expect_owner": True, "expect_neutral": False, "expect_s40": False},
        )
    )

    monkeypatch.setattr(
        visibility_fallback,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    trailer = "Nothing will ever be the same."
    sealed_out = apply_final_emission_gate(
        {
            "player_facing_text": trailer,
            "tags": [],
            "prompt_context": {"narrative_plan": _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})},
        },
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    sealed_final = (sealed_out.get("player_facing_text") or "").strip()
    sealed_meta = final_emission_meta_from_output(sealed_out) or {}
    assert sealed_meta.get("acceptance_quality_gate_replaced_candidate") is True
    sealed_obs = observe_speaker_contract(
        pre_speaker_text=trailer,
        gate_post_speaker_text=trailer,
        final_player_text=sealed_final,
        expected_speaker_id=None,
        expected_speaker_name=None,
    )
    cases.append(
        (
            "sealed_replacement",
            sealed_obs,
            {"expect_owner": False, "expect_neutral": False, "expect_s40": False},
        )
    )

    mismatch_obs = observe_final_to_replay_speaker_contract(
        gm_output={"player_facing_text": _MATCH_LINE, "_final_emission_meta": {}},
        resolution=_parity_resolution(npc_id="guard"),
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="resolution.social.npc_id",
    )
    cases.append(
        (
            "replay_speaker_mismatch",
            mismatch_obs,
            {"expect_owner": False, "expect_neutral": False, "expect_s40": True},
        )
    )

    rows = speaker_contract_family_risk_rows([(family, obs) for family, obs, _ in cases])
    assert len(rows) == len(cases)
    families = {row["family"] for row in rows}
    assert "local_rebind" in families
    assert "canonical_rewrite" in families
    assert "narrator_neutral" in families
    assert "forbidden_generic_fallback" in families
    assert "referential_visibility_local_substitution" in families
    assert "strict_social_emergency_fallback" in families
    assert "sealed_replacement" in families

    for family, obs, expect in cases:
        _assert_bt3_common(family, obs, expect_owner=expect["expect_owner"])

        post_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_POST_SPEAKER)
        final_cp = next(cp for cp in obs.checkpoints if cp.checkpoint_id == CHECKPOINT_FINAL)

        if expect["expect_neutral"]:
            assert final_cp.speaker_status == "neutral", family
            assert obs.risk.S == 0, family

        if expect["expect_s40"]:
            assert obs.risk.S == 40, family

        if family in {"local_rebind", "canonical_rewrite", "forbidden_generic_fallback", "local_rebind_gate"}:
            assert post_cp.speaker_status == "resolved", family
            assert final_cp.resolved_speaker_id == "runner", family

        if family == "narrator_neutral":
            assert obs.first_divergence_checkpoint_id in {CHECKPOINT_POST_SPEAKER, None}, family

        if family in {"referential_visibility_local_substitution", "strict_social_emergency_fallback", "sealed_replacement"}:
            assert obs.first_divergence_checkpoint_id is not None or not obs.mismatch_present, family

        if family == "sealed_replacement":
            assert obs.first_divergence_checkpoint_id == CHECKPOINT_FINAL, family
            assert "nothing will ever be the same" not in final_cp.normalized_text.lower(), family


def test_bt3_family_risk_rows_summary_shape() -> None:
    obs = observe_speaker_contract(
        pre_speaker_text=_MATCH_LINE,
        gate_post_speaker_text=_MATCH_LINE,
        final_player_text=_MATCH_LINE,
        expected_speaker_id="runner",
        expected_speaker_name="Tavern Runner",
        expected_speaker_source="contract.primary_speaker_id",
        enforcement_owner="game.speaker_contract_enforcement",
    )
    rows = speaker_contract_family_risk_rows([("baseline", obs)])
    assert rows == [
        {
            "family": "baseline",
            "total": 0,
            "band": "low",
            "first_divergence": None,
            "speaker_status": "resolved",
            "text_parity": True,
            "attribution_score": 0,
        }
    ]
