"""BX guard-matrix speaker parity fixtures and gate→replay observation (test-only).

Shared by BX end-to-end parity tests and BX5 protected golden replay coverage.
Does not modify runtime behavior.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.final_emission_speaker_observation import read_final_speaker_observation
from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    set_social_target,
)
from game.social_exchange_policy import (
    effective_strict_social_resolution_for_emission,
    reconcile_strict_social_resolution_speaker,
)
from game.storage import load_scene
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.post_speaker_finalize_probe import (
    LayerTextDelta,
    chain_enforce_phase_marker,
    install_post_speaker_text_probes,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.speaker_contract_risk import (
    CHECKPOINT_FINAL,
    CHECKPOINT_POST_SPEAKER,
    CHECKPOINT_REPLAY,
    SpeakerContractObservation,
    final_replay_parity_record,
    observe_final_to_replay_speaker_contract,
    observe_speaker_contract,
    project_final_emission_for_replay,
)
from tests.helpers.speaker_relocation_shadow_harness import (
    ShadowEnforceCapture,
    install_dual_run_enforce,
)

_SCENE_ID = "frontier_gate"
AMBIGUOUS_GUARD_PLAYER_TEXT = "Tell me guard, who posted that notice?"
BX_GUARD_SCENARIO_PREFIX = "bx_guard_speaker_parity"


@dataclass(frozen=True)
class GuardLifecycleObservation:
    """Lifecycle checkpoints for one guard-matrix turn."""

    player_text: str
    routed_speaker_id: str | None
    routed_source: str | None
    routed_resolved: bool
    contract_primary_speaker_id: str | None
    contract_primary_speaker_source: str | None
    enforcement_post_speaker_id: str | None
    final_emitted_speaker_label: str | None
    final_resolved_speaker_id: str | None
    replay_selected_speaker_id: str | None
    replay_selected_speaker_source: str | None
    final_speaker_observation: dict[str, Any] | None
    speaker_contract: SpeakerContractObservation
    gate_output: dict[str, Any]
    replay_observation: dict[str, Any]

    @property
    def risk(self):
        return self.speaker_contract.risk

    def as_checkpoint_record(self) -> dict[str, Any]:
        return {
            "routed_speaker_id": self.routed_speaker_id,
            "contract_primary_speaker_id": self.contract_primary_speaker_id,
            "enforcement_post_speaker_id": self.enforcement_post_speaker_id,
            "final_emitted_speaker_label": self.final_emitted_speaker_label,
            "final_resolved_speaker_id": self.final_resolved_speaker_id,
            "replay_selected_speaker_id": self.replay_selected_speaker_id,
            "replay_selected_speaker_source": self.replay_selected_speaker_source,
            "final_speaker_observation_status": (self.final_speaker_observation or {}).get("status"),
            "risk": {
                "D": self.risk.D,
                "S": self.risk.S,
                "T": self.risk.T,
                "A": self.risk.A,
                "total": self.risk.total,
                "band": self.risk.band,
            },
        }


def frontier_gate_base_session_scene(
    *,
    extra_addressables: list[dict[str, Any]] | None = None,
    extra_active_entities: list[str] | None = None,
    world: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Scene-roster-bound frontier_gate bundle; no global guard alias table."""
    w = dict(world) if isinstance(world, dict) else {"npcs": []}
    session = default_session()
    session["active_scene_id"] = _SCENE_ID
    session["interaction_context"] = {}
    scene = load_scene(_SCENE_ID)
    st = dict(session["scene_state"])
    st["active_scene_id"] = _SCENE_ID
    active = [
        "guard_captain",
        "tavern_runner",
        "refugee",
        "threadbare_watcher",
    ]
    if extra_active_entities:
        for entity_id in extra_active_entities:
            if entity_id not in active:
                active.append(entity_id)
    st["active_entities"] = active
    st["entity_presence"] = {entity_id: "active" for entity_id in active}

    if extra_addressables:
        sc = deepcopy(scene.get("scene") or {})
        addr = list(sc.get("addressables") or [])
        addr.extend(extra_addressables)
        sc["addressables"] = addr
        scene = {"scene": sc, "scene_state": dict(st)}
    else:
        scene["scene_state"] = dict(st)

    rebuild_active_scene_entities(session, w, _SCENE_ID, scene_envelope=scene)
    if extra_addressables:
        st_live = session.setdefault("scene_state", {})
        if not isinstance(st_live, dict):
            st_live = {}
            session["scene_state"] = st_live
        emergent = list(st_live.get("emergent_addressables") or [])
        for spec in extra_addressables:
            if isinstance(spec, dict) and spec not in emergent:
                emergent.append(spec)
        st_live["emergent_addressables"] = emergent
        if isinstance(scene.get("scene_state"), dict):
            scene["scene_state"]["emergent_addressables"] = list(emergent)
    return session, w, scene


def gate_guard_addressable(*, address_priority: int = 4) -> dict[str, Any]:
    return {
        "id": "gate_guard",
        "name": "Gate Guard",
        "scene_id": _SCENE_ID,
        "kind": "npc",
        "addressable": True,
        "address_priority": address_priority,
        "address_roles": ["gatekeeper"],
        "aliases": [],
    }


def second_guard_addressable(*, address_priority: int = 0) -> dict[str, Any]:
    """Second guard-like roster row sharing the bare ``guard`` role token."""
    return {
        "id": "gate_sentry",
        "name": "Gate Sentry",
        "scene_id": _SCENE_ID,
        "kind": "scene_actor",
        "addressable": True,
        "address_priority": address_priority,
        "address_roles": ["guard", "sentry"],
        "aliases": [],
    }


def route_authoritative(
    session: dict[str, Any],
    world: dict[str, Any],
    scene: dict[str, Any],
    player_text: str,
) -> dict[str, Any]:
    return resolve_authoritative_social_target(
        session,
        world,
        _SCENE_ID,
        player_text=player_text,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )


def reconciled_resolution(
    session: dict[str, Any],
    world: dict[str, Any],
    player_text: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    resolution: dict[str, Any] = {
        "kind": "question",
        "prompt": player_text,
        "social": {"social_intent_class": "social_exchange"},
    }
    reconciled = reconcile_strict_social_resolution_speaker(resolution, session, world, _SCENE_ID)
    contract = get_speaker_selection_contract(reconciled, metadata=None, trace=None)
    eff, _route, _ = effective_strict_social_resolution_for_emission(reconciled, session, world, _SCENE_ID)
    return reconciled, contract, eff if isinstance(eff, dict) else reconciled


def checkpoint_by_id(obs: SpeakerContractObservation, checkpoint_id: str):
    return next(cp for cp in obs.checkpoints if cp.checkpoint_id == checkpoint_id)


def observe_guard_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    *,
    session: dict[str, Any],
    world: dict[str, Any],
    scene: dict[str, Any],
    player_text: str,
    gm_line: str,
    pre_set_target: str | None = None,
    scenario_id: str = BX_GUARD_SCENARIO_PREFIX,
) -> GuardLifecycleObservation:
    if pre_set_target:
        set_social_target(session, pre_set_target)

    auth = route_authoritative(session, world, scene, player_text)
    resolution, contract, eff_resolution = reconciled_resolution(session, world, player_text)

    events: list[LayerTextDelta] = []
    phase = SimpleNamespace(after_enforce=False)
    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, events, phase=phase)

    out, _fem = apply_final_emission_gate_consumer(
        {"player_facing_text": gm_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=_SCENE_ID,
        scene=scene,
        world=world,
    )
    eq = cap.equivalence
    assert eq is not None

    final_text = (out.get("player_facing_text") or "").strip()
    expected_id = contract.get("primary_speaker_id")
    expected_name = contract.get("primary_speaker_name")
    expected_source = contract.get("primary_speaker_source")

    replay_observation = project_final_emission_for_replay(
        gm_output=out,
        resolution=eff_resolution,
        scenario_id=scenario_id,
        player_text=player_text,
    )
    speaker_obs = observe_speaker_contract(
        pre_speaker_text=eq.pre_speaker_text,
        gate_post_speaker_text=eq.gate_post_speaker_text,
        final_player_text=final_text,
        expected_speaker_id=str(expected_id) if expected_id else None,
        expected_speaker_name=str(expected_name) if expected_name else None,
        expected_speaker_source=str(expected_source) if expected_source else None,
        enforcement_owner="game.speaker_contract_enforcement",
        layer_events=events,
        replay_observation=replay_observation,
        resolution=eff_resolution,
        align_final_replay_normalization=True,
        final_speaker_observation=read_final_speaker_observation(out),
    )

    post_cp = checkpoint_by_id(speaker_obs, CHECKPOINT_POST_SPEAKER)
    final_cp = checkpoint_by_id(speaker_obs, CHECKPOINT_FINAL)
    fso = read_final_speaker_observation(out)

    return GuardLifecycleObservation(
        player_text=player_text,
        routed_speaker_id=str(auth.get("npc_id") or "").strip() or None,
        routed_source=str(auth.get("source") or "").strip() or None,
        routed_resolved=bool(auth.get("target_resolved")),
        contract_primary_speaker_id=str(contract.get("primary_speaker_id") or "").strip() or None,
        contract_primary_speaker_source=str(contract.get("primary_speaker_source") or "").strip() or None,
        enforcement_post_speaker_id=post_cp.resolved_speaker_id,
        final_emitted_speaker_label=str(final_cp.emitted_speaker_signature.get("speaker_label") or "") or None,
        final_resolved_speaker_id=final_cp.resolved_speaker_id,
        replay_selected_speaker_id=speaker_obs.replay_selected_speaker_id,
        replay_selected_speaker_source=speaker_obs.replay_selected_speaker_source,
        final_speaker_observation=fso,
        speaker_contract=speaker_obs,
        gate_output=out,
        replay_observation=replay_observation,
    )


def observe_ambiguous_guard_gate_replay(
    *,
    session: dict[str, Any],
    world: dict[str, Any],
    scene: dict[str, Any],
    player_text: str = AMBIGUOUS_GUARD_PLAYER_TEXT,
    gm_line: str = 'Guard says, "Maybe."',
    scenario_id: str = f"{BX_GUARD_SCENARIO_PREFIX}_ambiguous",
) -> GuardLifecycleObservation:
    """Gate→replay observation for ambiguous multi-guard roster without enforce shadow."""
    auth = route_authoritative(session, world, scene, player_text)
    resolution, contract, eff = reconciled_resolution(session, world, player_text)
    out = apply_final_emission_gate(
        {"player_facing_text": gm_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=_SCENE_ID,
        scene=scene,
        world=world,
    )
    replay_observation = project_final_emission_for_replay(
        gm_output=out,
        resolution=eff,
        scenario_id=scenario_id,
        player_text=player_text,
    )
    speaker_obs = observe_final_to_replay_speaker_contract(
        gm_output=out,
        resolution=eff,
        player_text=player_text,
        expected_speaker_id=contract.get("primary_speaker_id"),
        expected_speaker_name=contract.get("primary_speaker_name"),
        expected_speaker_source=contract.get("primary_speaker_source"),
        enforcement_owner="game.speaker_contract_enforcement",
        scenario_id=scenario_id,
    )
    fso = read_final_speaker_observation(out)
    final_cp = checkpoint_by_id(speaker_obs, CHECKPOINT_FINAL)
    return GuardLifecycleObservation(
        player_text=player_text,
        routed_speaker_id=str(auth.get("npc_id") or "").strip() or None,
        routed_source=str(auth.get("source") or "").strip() or None,
        routed_resolved=bool(auth.get("target_resolved")),
        contract_primary_speaker_id=str(contract.get("primary_speaker_id") or "").strip() or None,
        contract_primary_speaker_source=str(contract.get("primary_speaker_source") or "").strip() or None,
        enforcement_post_speaker_id=None,
        final_emitted_speaker_label=str(final_cp.emitted_speaker_signature.get("speaker_label") or "") or None,
        final_resolved_speaker_id=final_cp.resolved_speaker_id,
        replay_selected_speaker_id=speaker_obs.replay_selected_speaker_id,
        replay_selected_speaker_source=speaker_obs.replay_selected_speaker_source,
        final_speaker_observation=fso,
        speaker_contract=speaker_obs,
        gate_output=out,
        replay_observation=replay_observation,
    )


def ambiguous_guard_scene_bundle() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return frontier_gate_base_session_scene(
        extra_addressables=[second_guard_addressable()],
        extra_active_entities=["gate_sentry"],
    )


def resolved_guard_parity_locked_fields(expected_speaker_id: str) -> dict[str, Any]:
    """Exact replay observation paths locked for resolved BX guard cases."""
    return {
        "selected_speaker_id": expected_speaker_id,
        "speaker_projection_parity.status": "aligned",
        "speaker_projection_parity.selected_speaker_id": expected_speaker_id,
        "speaker_projection_parity.final_observed_speaker_id": expected_speaker_id,
        "speaker_projection_parity.final_observed_status": "resolved",
        "final_speaker_observation.status": "resolved",
        "final_speaker_observation.canonical_speaker_id": expected_speaker_id,
    }


def ambiguous_guard_parity_locked_fields() -> dict[str, Any]:
    """Exact replay observation paths locked for ambiguous multi-guard roster."""
    return {
        "selected_speaker_id": None,
        "selected_speaker_source": None,
        "speaker_projection_parity.status": "final_ambiguous",
        "speaker_projection_parity.selected_speaker_id": None,
        "speaker_projection_parity.final_observed_speaker_id": None,
        "speaker_projection_parity.final_observed_status": "ambiguous",
        "final_speaker_observation.status": "ambiguous",
        "final_speaker_observation.canonical_speaker_id": None,
    }


def assert_resolved_guard_golden_parity(
    obs: GuardLifecycleObservation,
    *,
    expected_speaker_id: str,
    max_risk_total: int = 19,
) -> None:
    """Assert resolved guard-matrix lifecycle + replay parity fields."""
    assert obs.routed_resolved is True
    assert obs.routed_speaker_id == expected_speaker_id
    assert obs.contract_primary_speaker_id == expected_speaker_id
    assert obs.enforcement_post_speaker_id == expected_speaker_id
    assert obs.final_resolved_speaker_id == expected_speaker_id
    assert obs.replay_selected_speaker_id == expected_speaker_id
    assert obs.replay_selected_speaker_source is not None
    assert obs.risk.total <= max_risk_total, obs.as_checkpoint_record()
    assert obs.risk.S == 0, obs.as_checkpoint_record()
    assert obs.speaker_contract.mismatch_present is False

    parity = final_replay_parity_record(obs.speaker_contract, replay_observation=obs.replay_observation)
    assert parity.get("speaker_id_match") is True, parity
    assert parity.get("text_hash_match") is True, parity
    replay_parity = obs.replay_observation.get("speaker_projection_parity")
    assert isinstance(replay_parity, dict)
    for path, expected in resolved_guard_parity_locked_fields(expected_speaker_id).items():
        actual = obs.replay_observation
        for part in path.split("."):
            actual = actual.get(part) if isinstance(actual, dict) else None
        assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"

    final_cp = checkpoint_by_id(obs.speaker_contract, CHECKPOINT_FINAL)
    replay_cp = checkpoint_by_id(obs.speaker_contract, CHECKPOINT_REPLAY)
    assert final_cp.checkpoint_id == CHECKPOINT_FINAL
    assert replay_cp.checkpoint_id == CHECKPOINT_REPLAY
    assert final_cp.resolved_speaker_id == replay_cp.resolved_speaker_id == expected_speaker_id


def assert_ambiguous_guard_golden_parity(
    obs: GuardLifecycleObservation,
    *,
    expected_candidates: frozenset[str] | set[str],
) -> None:
    """Assert ambiguous guard cannot pass as low-risk aligned parity."""
    for path, expected in ambiguous_guard_parity_locked_fields().items():
        actual = obs.replay_observation
        for part in path.split("."):
            actual = actual.get(part) if isinstance(actual, dict) else None
        assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"

    fso_candidates = set(obs.final_speaker_observation.get("candidates") or [])
    replay_candidates = set(
        (obs.replay_observation.get("speaker_projection_parity") or {}).get("final_observed_candidates") or []
    )
    assert expected_candidates <= fso_candidates, (fso_candidates, expected_candidates)
    assert expected_candidates <= replay_candidates, (replay_candidates, expected_candidates)

    assert obs.risk.S >= 20, obs.as_checkpoint_record()
    assert obs.risk.band in {"guarded", "elevated", "high"}, obs.as_checkpoint_record()
    assert obs.risk.total > 19, obs.as_checkpoint_record()

    replay_parity = obs.replay_observation.get("speaker_projection_parity") or {}
    assert replay_parity.get("status") != "aligned"
    assert obs.risk.band != "low" or obs.risk.S >= 20
