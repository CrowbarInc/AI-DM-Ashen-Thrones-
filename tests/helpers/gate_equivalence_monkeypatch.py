"""Centralized ``game.final_emission_gate`` monkeypatch entry points for S/T/U equivalence (Cycle AS6).

**Retained private gate seams (documented — do not redirect to smoke facade):**

- ``install_strict_social_trunk_phase_trackers`` — wraps private layer callables to prove strict-social
  trunk **ordering** (Block S).
- Consumers of ``post_speaker_finalize_probe.install_post_speaker_text_probes`` — post-speaker
  **divergence inventory** requires wrapping ``feg._apply_*`` / ``feg._strip_dialogue_from_text`` symbols.

**Public gate entry points used by helpers:**

- ``apply_final_emission_gate``, ``enforce_emitted_speaker_with_contract`` — tests call directly.
- ``get_speaker_selection_contract``, ``build_final_strict_social_response`` — patched on the gate
  module namespace because gate imports them for orchestration.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import game.final_emission_gate as feg

from tests.helpers.speaker_gate_order import (
    PHASE_ANTI_RAILROADING,
    PHASE_BUILD_SOCIAL,
    PHASE_NARRATIVE_AUTHENTICITY,
    PHASE_NARRATIVE_AUTHORITY,
    PHASE_RESPONSE_TYPE,
    PHASE_SCENE_STATE_ANCHOR,
    PHASE_SPEAKER,
    PHASE_TONE_ESCALATION,
)


def patch_get_speaker_selection_contract(monkeypatch: Any, contract: Mapping[str, Any]) -> None:
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(contract))


def patch_build_final_strict_social_response(
    monkeypatch: Any,
    *,
    line: str,
    strict_social_details: Mapping[str, Any] | Callable[[], Mapping[str, Any]],
    build_inputs: list[str] | None = None,
) -> None:
    def fake_build(
        candidate_text: str,
        *,
        resolution: dict[str, Any],
        tags: list[str],
        session: dict[str, Any],
        scene_id: str,
        world: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        if build_inputs is not None:
            build_inputs.append(str(candidate_text or ""))
        details = strict_social_details() if callable(strict_social_details) else strict_social_details
        return line, dict(details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)


def _wrap_phase(orig: Callable[..., Any], order: list[str], phase: str) -> Callable[..., Any]:
    def tracked(*args: Any, **kwargs: Any) -> Any:
        order.append(phase)
        return orig(*args, **kwargs)

    return tracked


def install_strict_social_trunk_phase_trackers(
    monkeypatch: Any,
    order: list[str],
    *,
    strict_social_details: Mapping[str, Any] | Callable[[], Mapping[str, Any]],
) -> None:
    """Record strict-social trunk phase order; stub social build (Block S ordering proof)."""

    def fake_build(
        candidate_text: str,
        *,
        resolution: dict[str, Any],
        tags: list[str],
        session: dict[str, Any],
        scene_id: str,
        world: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        del candidate_text, resolution, tags, session, scene_id, world
        order.append(PHASE_BUILD_SOCIAL)
        details = strict_social_details() if callable(strict_social_details) else strict_social_details
        return 'Tavern Runner says, "Order chain."', dict(details)

    orig_rt = feg._enforce_response_type_contract
    orig_nat = feg._apply_narrative_authenticity_layer
    orig_te = feg._apply_tone_escalation_layer
    orig_na = feg._apply_narrative_authority_layer
    orig_sp = feg.enforce_emitted_speaker_with_contract
    orig_ar = feg._apply_anti_railroading_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_enforce_response_type_contract", _wrap_phase(orig_rt, order, PHASE_RESPONSE_TYPE))
    monkeypatch.setattr(
        feg, "_apply_narrative_authenticity_layer", _wrap_phase(orig_nat, order, PHASE_NARRATIVE_AUTHENTICITY)
    )
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", _wrap_phase(orig_te, order, PHASE_TONE_ESCALATION))
    monkeypatch.setattr(
        feg, "_apply_narrative_authority_layer", _wrap_phase(orig_na, order, PHASE_NARRATIVE_AUTHORITY)
    )
    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", _wrap_phase(orig_sp, order, PHASE_SPEAKER))
    monkeypatch.setattr(feg, "_apply_anti_railroading_layer", _wrap_phase(orig_ar, order, PHASE_ANTI_RAILROADING))
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", _wrap_phase(orig_ssa, order, PHASE_SCENE_STATE_ANCHOR))
