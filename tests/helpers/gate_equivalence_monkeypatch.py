"""Centralized ``game.final_emission_gate`` monkeypatch entry points for S/T/U equivalence (Cycle AS6).

**Retained private gate seams (documented — do not redirect to smoke facade):**

- ``install_strict_social_trunk_phase_trackers`` — wraps private layer callables to prove strict-social
  trunk **ordering** (Block S).
- Consumers of ``post_speaker_finalize_probe.install_post_speaker_text_probes`` — post-speaker
  **divergence inventory** wraps canonical stack / terminal-pipeline owner symbols (BJ-123).

**Allowed ``feg.*`` patch seams (BJ-123):**

- ``get_speaker_selection_contract`` — live compatibility re-export; patch both ``feg`` and ``sce``.
- ``apply_final_emission_gate`` — orchestration entry for direct calls (not a monkeypatch target).

**Public gate entry points used by helpers:**

- ``apply_final_emission_gate`` — tests call directly.
- ``get_speaker_selection_contract`` — patched on the gate module namespace when tests still
  resolve it through ``feg``; also patched on ``game.speaker_contract_enforcement`` when enforcement
  runs through the owner entrypoint.
- ``build_final_strict_social_response`` — patched on ``game.final_emission_strict_social_stack``
  (canonical owner seam after BJ-116/BJ-120).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import game.final_emission_gate as feg
import game.final_emission_repairs as emission_repairs
import game.final_emission_response_type as response_type
import game.final_emission_strict_social_stack as strict_social_stack
import game.speaker_contract_enforcement as sce

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
    loader = lambda *a, **kw: dict(contract)
    monkeypatch.setattr(feg, "get_speaker_selection_contract", loader)
    monkeypatch.setattr(sce, "get_speaker_selection_contract", loader)


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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)


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

    orig_rt = response_type.enforce_response_type_contract
    orig_nat = emission_repairs._apply_narrative_authenticity_layer
    orig_te = strict_social_stack.apply_tone_escalation_layer
    orig_na = strict_social_stack.apply_narrative_authority_layer
    orig_sp = strict_social_stack.enforce_emitted_speaker_with_contract
    orig_ar = strict_social_stack.apply_anti_railroading_layer
    orig_ssa = strict_social_stack.apply_scene_state_anchor_layer

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(response_type, "enforce_response_type_contract", _wrap_phase(orig_rt, order, PHASE_RESPONSE_TYPE))
    monkeypatch.setattr(
        emission_repairs,
        "_apply_narrative_authenticity_layer",
        _wrap_phase(orig_nat, order, PHASE_NARRATIVE_AUTHENTICITY),
    )
    monkeypatch.setattr(
        strict_social_stack, "apply_tone_escalation_layer", _wrap_phase(orig_te, order, PHASE_TONE_ESCALATION)
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_narrative_authority_layer",
        _wrap_phase(orig_na, order, PHASE_NARRATIVE_AUTHORITY),
    )
    monkeypatch.setattr(
        strict_social_stack, "enforce_emitted_speaker_with_contract", _wrap_phase(orig_sp, order, PHASE_SPEAKER)
    )
    monkeypatch.setattr(
        strict_social_stack, "apply_anti_railroading_layer", _wrap_phase(orig_ar, order, PHASE_ANTI_RAILROADING)
    )
    monkeypatch.setattr(
        strict_social_stack, "apply_scene_state_anchor_layer", _wrap_phase(orig_ssa, order, PHASE_SCENE_STATE_ANCHOR)
    )
