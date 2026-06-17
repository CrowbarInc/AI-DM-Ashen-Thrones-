"""Block T — speaker relocation shadow-equivalence harness (tests only).

Compares, at the strict-social **pre-speaker** snapshot:

- **Gate path:** :func:`~game.final_emission_gate.enforce_emitted_speaker_with_contract`
  (current orchestration entry; unchanged in production).
- **Isolated path:** same validation + :func:`~game.speaker_contract_enforcement._apply_speaker_contract_repairs`
  on **deep-cloned** ``gm_output`` / ``eff_resolution`` / ``resolution`` captured **before** enforcement
  mutates live objects or merges FEM.

Recording **downstream reshaping**: after :func:`~game.final_emission_gate.apply_final_emission_gate` returns,
compare normalized post-speaker text vs normalized final ``player_facing_text``.

Does **not** move ``local_rebind`` upstream or alter gate ordering.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Iterator, Mapping, Optional

import game.final_emission_strict_social_stack as strict_social_stack
import game.speaker_contract_enforcement as sce

from tests.helpers.gate_equivalence_monkeypatch import (
    patch_build_final_strict_social_response,
    patch_get_speaker_selection_contract,
)
from tests.helpers.strict_social_harness import runner_strict_bundle
from tests.helpers.speaker_gate_order import normalized_player_text_equal


def _repair_flag_slice(repair: Mapping[str, Any] | None) -> dict[str, Any]:
    """Comparable repair subset for relocation equivalence logs."""
    if not isinstance(repair, dict):
        return {}
    keys = (
        "local_rebind_applied",
        "canonical_rewrite_applied",
        "narrator_neutral_applied",
        "canonical_rewrite_failed_resolution",
        "initial_repair_mode",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in repair:
            out[k] = repair.get(k)
    return out


def run_isolated_enforce_mirror(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    contract_loader: Optional[Callable[..., Dict[str, Any]]] = None,
) -> tuple[str, Dict[str, Any]]:
    """Mirror :func:`~game.final_emission_gate.enforce_emitted_speaker_with_contract` without FEM merge."""
    loader = contract_loader or sce.get_speaker_selection_contract
    trace = gm_output.get("trace") if isinstance(gm_output.get("trace"), dict) else None
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else None
    contract = loader(
        eff_resolution if isinstance(eff_resolution, dict) else None,
        metadata=md,
        trace=trace,
    )
    val = sce.validate_emitted_speaker_against_contract(
        text,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    payload: Dict[str, Any] = {
        "contract_present": not (
            isinstance(contract.get("debug"), dict) and contract["debug"].get("contract_missing")
        ),
        "validation": val,
    }

    if val.get("ok") is True:
        payload["final_reason_code"] = val.get("reason_code")
        return text, payload

    repaired, final_rc, rdbg = sce._apply_speaker_contract_repairs(
        text,
        val,
        contract=contract,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        scene_id=scene_id,
        world=world,
    )
    payload["repair"] = rdbg
    payload["final_reason_code"] = final_rc
    payload["post_validation"] = sce.validate_emitted_speaker_against_contract(
        repaired,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    return repaired, payload


@dataclass(frozen=True)
class SpeakerShadowEquivalence:
    """Recorded dimensions for Gate vs isolated speaker repair at the same pre-speaker snapshot."""

    pre_speaker_text: str
    gate_post_speaker_text: str
    isolated_post_speaker_text: str
    normalized_text_match: bool
    repair_flags_gate: dict[str, Any]
    repair_flags_isolated: dict[str, Any]
    repair_flags_match: bool
    final_reason_code_gate: Any
    final_reason_code_isolated: Any
    final_reason_match: bool
    post_validation_ok_gate: Any
    post_validation_ok_isolated: Any
    post_validation_match: bool
    final_player_text: str | None = None
    downstream_finalize_delta: bool = False


def compare_gate_vs_isolated_payloads(
    *,
    gate_payload: Mapping[str, Any],
    isolated_payload: Mapping[str, Any],
    gate_post_text: str,
    isolated_post_text: str,
    pre_speaker_text: str,
    final_player_text: str | None = None,
) -> SpeakerShadowEquivalence:
    """Build an equivalence record from two enforcement payloads and texts."""
    rg = gate_payload.get("repair") if isinstance(gate_payload.get("repair"), dict) else {}
    ri = isolated_payload.get("repair") if isinstance(isolated_payload.get("repair"), dict) else {}
    sl_g = _repair_flag_slice(rg)
    sl_i = _repair_flag_slice(ri)
    fr_g = gate_payload.get("final_reason_code")
    fr_i = isolated_payload.get("final_reason_code")
    pv_g = (gate_payload.get("post_validation") or {}).get("ok") if isinstance(gate_payload.get("post_validation"), dict) else None
    pv_i = (isolated_payload.get("post_validation") or {}).get("ok") if isinstance(isolated_payload.get("post_validation"), dict) else None

    downstream = False
    if final_player_text is not None:
        downstream = not normalized_player_text_equal(gate_post_text, final_player_text)

    return SpeakerShadowEquivalence(
        pre_speaker_text=pre_speaker_text,
        gate_post_speaker_text=gate_post_text,
        isolated_post_speaker_text=isolated_post_text,
        normalized_text_match=normalized_player_text_equal(gate_post_text, isolated_post_text),
        repair_flags_gate=dict(sl_g),
        repair_flags_isolated=dict(sl_i),
        repair_flags_match=sl_g == sl_i,
        final_reason_code_gate=fr_g,
        final_reason_code_isolated=fr_i,
        final_reason_match=fr_g == fr_i,
        post_validation_ok_gate=pv_g,
        post_validation_ok_isolated=pv_i,
        post_validation_match=pv_g == pv_i,
        final_player_text=final_player_text,
        downstream_finalize_delta=downstream,
    )


def with_finalize_delta(eq: SpeakerShadowEquivalence, final_player_text: str) -> SpeakerShadowEquivalence:
    """Attach final gate output and recompute downstream reshaping delta."""
    downstream = not normalized_player_text_equal(eq.gate_post_speaker_text, final_player_text)
    return replace(eq, final_player_text=final_player_text, downstream_finalize_delta=downstream)


@dataclass(frozen=True)
class FinalizeStackFixture:
    """Shared strict-social finalize-stack inputs used by Block S/T/U tests."""

    session: dict[str, Any]
    world: dict[str, Any]
    scene_id: str
    resolution: dict[str, Any]
    line: str

    def __iter__(self) -> Iterator[Any]:
        """Preserve tuple-unpacking readability in existing tests."""
        yield self.session
        yield self.world
        yield self.scene_id
        yield self.resolution
        yield self.line


def build_finalize_stack_fixture(
    monkeypatch: Any,
    *,
    contract: Mapping[str, Any],
    strict_social_details: Mapping[str, Any] | Callable[[], Mapping[str, Any]],
    line: str = 'Ragged stranger says, "No names, only rumors."',
    configure_resolution: Callable[[dict[str, Any]], None] | None = None,
    build_inputs: list[str] | None = None,
) -> FinalizeStackFixture:
    """Build the common strict-social finalize-stack fixture without owning assertions."""
    session, world, scene_id, resolution = runner_strict_bundle()
    if configure_resolution is not None:
        configure_resolution(resolution)

    patch_get_speaker_selection_contract(monkeypatch, contract)
    patch_build_final_strict_social_response(
        monkeypatch,
        line=line,
        strict_social_details=strict_social_details,
        build_inputs=build_inputs,
    )
    return FinalizeStackFixture(session=session, world=world, scene_id=scene_id, resolution=resolution, line=line)


@dataclass
class ShadowEnforceCapture:
    """Mutable holder populated by :func:`install_dual_run_enforce`."""

    equivalence: SpeakerShadowEquivalence | None = None


def install_dual_run_enforce(monkeypatch, holder: ShadowEnforceCapture) -> None:
    """Wrap ``enforce_emitted_speaker_with_contract``: snapshot pre-merge state, then dual-run compare."""

    orig = strict_social_stack.enforce_emitted_speaker_with_contract

    def wrapped(text: str, **kwargs: Any) -> tuple[str, Dict[str, Any]]:
        gm_snap = copy.deepcopy(kwargs["gm_output"])
        eff_snap = copy.deepcopy(kwargs["eff_resolution"])
        res_snap = copy.deepcopy(kwargs.get("resolution"))

        iso_text, iso_payload = run_isolated_enforce_mirror(
            text,
            gm_output=gm_snap,
            resolution=res_snap,
            eff_resolution=eff_snap,
            world=kwargs.get("world"),
            scene_id=kwargs["scene_id"],
        )

        gate_text, gate_payload = orig(text, **kwargs)

        holder.equivalence = compare_gate_vs_isolated_payloads(
            gate_payload=gate_payload,
            isolated_payload=iso_payload,
            gate_post_text=gate_text,
            isolated_post_text=iso_text,
            pre_speaker_text=text,
            final_player_text=None,
        )
        return gate_text, gate_payload

    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", wrapped)
