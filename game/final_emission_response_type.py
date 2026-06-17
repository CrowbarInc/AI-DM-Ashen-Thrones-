"""Response-type contract helpers and enforcement for final emission.

Upstream prepared text/kind resolution, opening-mode validation context,
response-type validator dispatch, debug observability merges, and the
:func:`enforce_response_type_contract` repair ladder. Production stacks
(:mod:`game.final_emission_non_strict_stack`, :mod:`game.final_emission_strict_social_stack`)
and test harnesses call the owner entrypoint directly.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Dict, List

from game.final_emission_meta import default_response_type_debug as _default_response_type_debug
from game.final_emission_opening_fallback import (
    _gm_output_normalized_for_opening_context,
    _opening_curated_facts_schema_ok,
    _opening_fallback_classification,
    opening_fail_closed_composition_meta_empty,
    opening_scene_safe_fallback_contract,
)
from game.final_emission_opening_mode import _opening_mode_active_for_turn
from game.final_emission_text import (
    _normalize_text,
    _normalize_text_preserve_paragraphs,
)
from game.final_emission_validators import (
    candidate_satisfies_action_outcome_contract,
    candidate_satisfies_answer_contract,
    candidate_satisfies_dialogue_contract,
    candidate_satisfies_scene_opening_contract,
    is_valid_opening,
    validate_opening_output,
)
from game.opening_deterministic_fallback import opening_context_from_gm_output as _opening_context_from_gm_output
from game.realization_provenance import (
    LEGACY_DIEGETIC_FALLBACK,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
    attach_realization_fallback_family,
)
from game.response_policy_contracts import (
    _last_player_input,
    _resolve_response_type_contract,
)
from game.social_exchange_emission import (
    minimal_social_emergency_fallback_line,
    strict_social_ownership_terminal_fallback,
)
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_EMISSION_KEY,
    build_social_fallback_resolution,
)


_OPENING_UPSTREAM_PREPARE_ATTACH_OBSERVABILITY_KEYS: tuple[str, ...] = (
    "opening_upstream_prepare_attach_build_failed",
    "opening_upstream_prepare_attach_failure_exc_type",
    "opening_upstream_prepare_attach_no_usable_payload_after_attempt",
)


def _upstream_prepared_emission_field_source(upstream: Dict[str, Any], field_name: str) -> str:
    """Stable attribution for telemetry: explicit ``upstream_prepared_emission_attribution`` or field path."""
    raw = upstream.get("upstream_prepared_emission_attribution")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()[:160]
    return f"upstream_prepared_emission.{field_name}"


def _upstream_prepared_emission_dict(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(gm_output, Mapping):
        return {}
    upstream = gm_output.get(UPSTREAM_PREPARED_EMISSION_KEY)
    return dict(upstream) if isinstance(upstream, dict) else {}


def _merge_opening_upstream_prepare_attach_observability_into_response_type_debug(
    gm_output: Mapping[str, Any] | None,
    response_type_debug: Dict[str, Any],
) -> None:
    """Copy Block M upstream opening attach telemetry from ``metadata.emission_debug`` into RT debug / FEM."""
    if not isinstance(gm_output, dict):
        return
    md = gm_output.get("metadata")
    em = md.get("emission_debug") if isinstance(md, dict) else None
    if not isinstance(em, dict):
        return
    for k in _OPENING_UPSTREAM_PREPARE_ATTACH_OBSERVABILITY_KEYS:
        if k in em:
            response_type_debug[k] = em[k]


def _response_type_opening_mode_active(
    required: str,
    gm_output: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
) -> bool:
    return required == "scene_opening" or _opening_mode_active_for_turn(gm_output, resolution)


def _seed_opening_response_type_debug(debug: Dict[str, Any], *, opening_mode: bool) -> None:
    debug["opening_generic_action_repair_blocked"] = False
    debug["opening_specific_repair_used"] = False
    debug["opening_fallback_skipped"] = False
    debug["blocked_repair_kind"] = None
    debug["opening_repair_source"] = "not_opening" if not opening_mode else None


def _prepare_opening_response_type_validation(
    gm_output: Mapping[str, Any] | None,
    current: str,
) -> tuple[Dict[str, Any], List[str], bool]:
    opening_facts_schema_ok = _opening_curated_facts_schema_ok(gm_output if isinstance(gm_output, dict) else None)
    gm_for_opening_ctx = _gm_output_normalized_for_opening_context(
        gm_output if isinstance(gm_output, dict) else None
    )
    opening_context = _opening_context_from_gm_output(gm_for_opening_ctx)
    opening_failures = validate_opening_output(current, opening_context)
    if not opening_facts_schema_ok and not opening_failures:
        opening_failures = ["opening_curated_facts_missing"]
    return opening_context, opening_failures, opening_facts_schema_ok


def _opening_generic_action_repair_block_debug_patch(upstream: Mapping[str, Any]) -> Dict[str, Any]:
    cand = upstream.get("prepared_action_fallback_text")
    if isinstance(cand, str) and cand.strip():
        return {
            "opening_generic_action_repair_blocked": True,
            "blocked_repair_kind": "action_outcome_upstream_prepared_repair",
        }
    return {}


@dataclass(frozen=True)
class _UpstreamPreparedRepairResolution:
    repaired: str | None
    repair_kind: str | None
    upstream_src_label: str | None
    upstream_absent: bool = False


def _resolve_upstream_prepared_answer_action_repair(
    required: str,
    upstream: Mapping[str, Any],
) -> _UpstreamPreparedRepairResolution:
    if required == "answer":
        cand = upstream.get("prepared_answer_fallback_text")
        if isinstance(cand, str) and cand.strip():
            return _UpstreamPreparedRepairResolution(
                repaired=cand.strip(),
                repair_kind="answer_upstream_prepared_repair",
                upstream_src_label=_upstream_prepared_emission_field_source(
                    dict(upstream),
                    "prepared_answer_fallback_text",
                ),
            )
        return _UpstreamPreparedRepairResolution(None, None, "absent", True)
    if required == "action_outcome":
        cand = upstream.get("prepared_action_fallback_text")
        if isinstance(cand, str) and cand.strip():
            return _UpstreamPreparedRepairResolution(
                repaired=cand.strip(),
                repair_kind="action_outcome_upstream_prepared_repair",
                upstream_src_label=_upstream_prepared_emission_field_source(
                    dict(upstream),
                    "prepared_action_fallback_text",
                ),
            )
        return _UpstreamPreparedRepairResolution(None, None, "absent", True)
    return _UpstreamPreparedRepairResolution(None, None, None, False)


def _stamp_upstream_prepared_emission_absent_debug(debug: Dict[str, Any]) -> None:
    debug["response_type_upstream_prepared_absent"] = True
    debug["upstream_prepared_emission_source"] = "absent"


def _stamp_upstream_prepared_emission_success_debug(
    debug: Dict[str, Any],
    *,
    repair_kind: str,
    upstream_src_label: str | None,
) -> None:
    debug["upstream_prepared_emission_used"] = True
    debug["upstream_prepared_emission_valid"] = True
    debug["upstream_prepared_emission_source"] = upstream_src_label
    debug["upstream_prepared_emission_reject_reason"] = None


def _stamp_upstream_prepared_emission_rejected_debug(
    debug: Dict[str, Any],
    *,
    upstream_src_label: str | None,
    reject_reason: str,
) -> None:
    debug["upstream_prepared_emission_used"] = False
    debug["upstream_prepared_emission_valid"] = False
    debug["upstream_prepared_emission_source"] = upstream_src_label or "upstream_prepared_emission"
    debug["upstream_prepared_emission_reject_reason"] = reject_reason


def _evaluate_required_response_type_validator(
    required: str,
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    player_input: str,
    response_type_debug: Dict[str, Any] | None = None,
) -> tuple[bool, List[str]]:
    if required == "dialogue":
        return candidate_satisfies_dialogue_contract(
            text,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
        )
    if required == "answer":
        return candidate_satisfies_answer_contract(text)
    if required == "action_outcome":
        return candidate_satisfies_action_outcome_contract(text, player_input=player_input)
    if required == "scene_opening":
        validator_ok, validator_reasons = candidate_satisfies_scene_opening_contract(text)
        if isinstance(response_type_debug, dict):
            response_type_debug["scene_opening_candidate_contract_passed"] = bool(validator_ok)
            response_type_debug["scene_opening_candidate_len"] = len(text)
        return validator_ok, validator_reasons
    return True, []


def _stamp_preserved_opening_candidate_debug(
    debug: Dict[str, Any],
    *,
    required: str,
    validator_ok: bool,
    repair_source: str,
    rejection_reasons: List[str] | None = None,
) -> None:
    debug["response_type_candidate_ok"] = True
    debug["response_type_repair_used"] = False
    debug["response_type_repair_kind"] = None
    debug["opening_repair_source"] = repair_source
    debug["opening_fallback_skipped"] = True
    debug["final_emission_boundary_repair_used"] = False
    debug["final_emission_boundary_semantic_repair_disabled"] = True
    if rejection_reasons is not None:
        debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in rejection_reasons if r))
    if required == "scene_opening" and validator_ok:
        debug["scene_opening_accepted_candidate_promoted"] = True


def enforce_response_type_contract(
    candidate_text: str,
    *,
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    strict_social_turn: bool,
    strict_social_suppressed_non_social_turn: bool,
    active_interlocutor: str,
) -> tuple[str, Dict[str, Any]]:
    # C2 Block B: answer/action contract-shaped fallback text is read from ``upstream_prepared_emission``
    # (see :mod:`game.upstream_response_repairs`). Scene-opening prose is composed by
    # :mod:`game.opening_deterministic_fallback`, packaged by :mod:`game.upstream_response_repairs`, and
    # selected from ``upstream_prepared_opening_fallback`` via the opening fallback adapter.
    contract, source = _resolve_response_type_contract(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    debug = _default_response_type_debug(contract, source)
    if not contract:
        return candidate_text, debug

    required = str(contract.get("required_response_type") or "").strip().lower()
    _norm = (
        _normalize_text_preserve_paragraphs
        if strict_social_turn and required == "dialogue"
        else _normalize_text
    )
    player_input = _last_player_input(
        resolution=resolution,
        session=session,
        scene_id=scene_id,
    )
    current = _norm(candidate_text)
    reasons: List[str] = []
    opening_mode = _response_type_opening_mode_active(required, gm_output, resolution)
    _seed_opening_response_type_debug(debug, opening_mode=opening_mode)

    validator_ok = True
    validator_reasons: List[str] = []
    if required == "dialogue":
        if strict_social_suppressed_non_social_turn:
            debug["response_type_candidate_ok"] = None
            debug["response_type_repair_kind"] = "dialogue_enforcement_skipped_due_to_social_suppression"
            return current, debug
        validator_ok, validator_reasons = _evaluate_required_response_type_validator(
            required,
            current,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
            player_input=player_input,
        )
    else:
        validator_ok, validator_reasons = _evaluate_required_response_type_validator(
            required,
            current,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
            player_input=player_input,
            response_type_debug=debug,
        )
    reasons.extend(validator_reasons)

    opening_context: Dict[str, Any] = {}
    opening_failures: List[str] = []
    opening_facts_schema_ok = True
    if opening_mode:
        opening_context, opening_failures, opening_facts_schema_ok = _prepare_opening_response_type_validation(
            gm_output if isinstance(gm_output, dict) else None,
            current,
        )
        if not opening_facts_schema_ok:
            debug["opening_fallback_missing_curated_facts"] = True
        debug["opening_validation_failed"] = bool(opening_failures)
        debug["opening_failure_reasons"] = list(opening_failures)
        if not opening_failures:
            _stamp_preserved_opening_candidate_debug(
                debug,
                required=required,
                validator_ok=validator_ok,
                repair_source="preserved_candidate",
            )
            return current, debug
        reasons.extend(opening_failures)

    if validator_ok and not reasons:
        debug["response_type_candidate_ok"] = True
        debug["opening_repair_source"] = "not_opening"
        debug["final_emission_boundary_repair_used"] = False
        debug["final_emission_boundary_semantic_repair_disabled"] = True
        return current, debug

    if opening_mode:
        # Opening guard: never replace an opening with generic action-outcome prepared prose.
        upstream = _upstream_prepared_emission_dict(gm_output if isinstance(gm_output, dict) else None)
        debug.update(_opening_generic_action_repair_block_debug_patch(upstream))

        curated_facts = opening_context.get("visible_facts") if isinstance(opening_context, Mapping) else []
        if is_valid_opening(current, curated_facts if isinstance(curated_facts, Sequence) else []):
            _stamp_preserved_opening_candidate_debug(
                debug,
                required=required,
                validator_ok=validator_ok,
                repair_source="preserved_candidate_validity_check",
                rejection_reasons=reasons,
            )
            debug["opening_specific_repair_used"] = False
            debug["opening_recovered_via_fallback"] = False
            return current, debug

        # Otherwise, select opening fallback via canonical opening selector (shared with visibility).
        _, (
            fallback,
            fallback_meta,
            stub_patch,
            upstream_opening_selected,
            _,
        ) = opening_scene_safe_fallback_contract(
            gm_output if isinstance(gm_output, dict) else None,
            fail_closed_composition_meta_factory=opening_fail_closed_composition_meta_empty,
        )
        debug.update(stub_patch)
        debug.update(fallback_meta)
        if (
            not opening_facts_schema_ok
            and not upstream_opening_selected
            and fallback_meta.get("blocked_repair_kind") != "opening_upstream_prepare_attach_failed"
        ):
            debug["blocked_repair_kind"] = "opening_missing_curated_facts"
        # Mirror authorship from adapter/upstream composition meta only; do not infer on success path.
        if not upstream_opening_selected:
            debug["opening_fallback_authorship_source"] = None
        fallback_failures = validate_opening_output(fallback, opening_context)
        if fallback and not fallback_failures and not fallback_meta.get("opening_fallback_failed_closed"):
            classification = _opening_fallback_classification()
            debug["response_type_candidate_ok"] = True
            debug["response_type_repair_used"] = True
            debug["response_type_repair_kind"] = "opening_deterministic_fallback"
            debug["opening_specific_repair_used"] = True
            debug["opening_recovered_via_fallback"] = True
            debug["opening_repair_source"] = "deterministic_fallback"
            debug["fallback_family_used"] = classification.get("fallback_family")
            debug["fallback_temporal_frame"] = classification.get("temporal_frame")
            attach_realization_fallback_family(
                debug,
                UPSTREAM_PREPARED_EMISSION if upstream_opening_selected else LEGACY_DIEGETIC_FALLBACK,
            )
            debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
            return fallback, debug

        debug["response_type_candidate_ok"] = False
        debug["response_type_repair_used"] = bool(fallback_meta.get("opening_fallback_failed_closed"))
        debug["response_type_repair_kind"] = (
            "opening_deterministic_fallback_failed_closed"
            if fallback_meta.get("opening_fallback_failed_closed")
            else None
        )
        debug["opening_repair_source"] = (
            "fallback_failed_closed"
            if fallback_meta.get("opening_fallback_failed_closed")
            else "fallback_failed_validation"
        )
        reasons.extend(f"fallback_{r}" for r in fallback_failures)
        debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
        return fallback if fallback_meta.get("opening_fallback_failed_closed") else current, debug

    repaired: str | None = None
    repair_kind: str | None = None
    upstream_src_label: str | None = None
    upstream = _upstream_prepared_emission_dict(gm_output if isinstance(gm_output, dict) else None)
    if required == "dialogue":
        social_resolution = build_social_fallback_resolution(
            resolution=resolution,
            active_interlocutor=active_interlocutor,
            world=world,
            scene_id=scene_id,
        )
        if strict_social_turn and isinstance(social_resolution, dict):
            repaired = strict_social_ownership_terminal_fallback(social_resolution)
            repair_kind = "strict_social_dialogue_repair"
        elif isinstance(social_resolution, dict):
            repaired = minimal_social_emergency_fallback_line(social_resolution)
            repair_kind = "dialogue_minimal_repair"
    elif required in {"answer", "action_outcome"}:
        prepared = _resolve_upstream_prepared_answer_action_repair(required, upstream)
        repaired = prepared.repaired
        repair_kind = prepared.repair_kind
        upstream_src_label = prepared.upstream_src_label
        if prepared.upstream_absent:
            debug["response_type_upstream_prepared_absent"] = True
            _stamp_upstream_prepared_emission_absent_debug(debug)

    if repaired:
        repaired = _norm(repaired)
        repaired_ok, validator_reasons = _evaluate_required_response_type_validator(
            required,
            repaired,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
            player_input=player_input,
        )
        repaired_reasons = list(validator_reasons)
        if repaired_ok and not repaired_reasons:
            debug["response_type_candidate_ok"] = True
            debug["response_type_repair_used"] = True
            debug["response_type_repair_kind"] = repair_kind
            debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
            if repair_kind in {"answer_upstream_prepared_repair", "action_outcome_upstream_prepared_repair"}:
                _stamp_upstream_prepared_emission_success_debug(
                    debug,
                    repair_kind=str(repair_kind),
                    upstream_src_label=upstream_src_label,
                )
                attach_realization_fallback_family(debug, UPSTREAM_PREPARED_EMISSION)
            else:
                debug["upstream_prepared_emission_used"] = False
                debug["upstream_prepared_emission_valid"] = False
                debug["upstream_prepared_emission_source"] = None
                debug["upstream_prepared_emission_reject_reason"] = None
                if repair_kind in {"strict_social_dialogue_repair", "dialogue_minimal_repair"}:
                    attach_realization_fallback_family(debug, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
            debug["final_emission_boundary_repair_used"] = False
            debug["final_emission_boundary_semantic_repair_disabled"] = True
            return repaired, debug

        if repair_kind in {"answer_upstream_prepared_repair", "action_outcome_upstream_prepared_repair"}:
            rr0 = repaired_reasons[0] if repaired_reasons else "upstream_prepared_failed_contract"
            _stamp_upstream_prepared_emission_rejected_debug(
                debug,
                upstream_src_label=upstream_src_label,
                reject_reason=str(rr0),
            )
            debug["final_emission_boundary_repair_used"] = False
            debug["final_emission_boundary_semantic_repair_disabled"] = True

    debug["response_type_candidate_ok"] = False
    debug["response_type_repair_kind"] = repair_kind
    debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
    return current, debug
