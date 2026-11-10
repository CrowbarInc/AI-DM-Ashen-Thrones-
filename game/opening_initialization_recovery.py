"""Deterministic recovery for a rejected campaign opening.

The engine keeps the opening resolution and the selector's curated facts.
Rejected provider narration, declarations, and effect fields are not inputs.
Prose comes only from :func:`game.opening_deterministic_fallback.deterministic_opening_fallback_text_and_meta`.

Eligibility is an explicit classification. Malformed envelopes, transport
failures, invalid structured declarations, mechanical contradictions,
hidden-information failures, and unknown integrity failures stay on the
existing hard-fail path. A semantic narration rejection with valid
declarations can be replaced by the composer.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_text_formatting import _normalize_text
from game.opening_deterministic_fallback import (
    OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
    _actionable_hook_from_opening_context,
    _pick_opening_fallback_fact,
    deterministic_opening_fallback_text_and_meta,
    opening_context_from_gm_output,
)

OPENING_SOURCE_AI = "ai"
OPENING_SOURCE_DETERMINISTIC = "deterministic_fallback"
PROVENANCE_DETERMINISTIC_OPENING_RECOVERY = "deterministic_opening_recovery"

_NARRATIVE_REASONS = frozenset(
    {
        "unauthorized_resolution_decision_fact",
        "malformed_or_truncated",
        "consequential_invention",
        "ungrounded_authoritative_rule",
        "player_text_splice",
        "structured_envelope",
    }
)
_MECHANICAL_REASONS = frozenset({"mechanical_contradiction"})
_HIDDEN_REASONS = frozenset({"hidden_information"})
_STATE_REASONS = frozenset({"impossible_entity_state"})
_UNUSABLE_NARRATION_REASONS = frozenset(
    {
        "scene_opening_empty",
        "scene_opening_generic_fallback_text",
        "scene_opening_not_scene_establishing",
        "scene_opening_is_question",
        "scene_opening_contract_rejected",
        "generic_information_request_fallback",
    }
)
_MALFORMED_REASONS = frozenset(
    {
        "structured_contract_rejected",
        "opening_renderer_configuration_invalid",
        "opening_fallback_failed_closed",
    }
)
_TRANSPORT_REASONS = frozenset({"provider_opening_not_delivered", "missing_opening_response"})
_BLOCKING_TAGS = frozenset(
    {
        "structured_contract_failure",
        "structured_output_rejected",
        "fast_fallback",
        "upstream_api_fast_fallback",
        "provider_calls_disabled",
    }
)
_EFFECT_KEYS = (
    "scene_update",
    "world_updates",
    "activate_scene_id",
    "new_scene_draft",
    "suggested_action",
)
_ENVIRONMENT_NEEDLES = (
    "gate",
    "district",
    "market",
    "road",
    "square",
    "rain",
    "mist",
    "banners",
    "street",
    "yard",
)
_ACTIVITY_NEEDLES = (
    "guard",
    "refugee",
    "wagon",
    "crowd",
    "runner",
    "stranger",
    "observer",
    "watch",
    "hawking",
)
_HOOK_NEEDLES = (
    "notice",
    "curfew",
    "tax",
    "missing",
    "patrol",
    "offers",
    "signals",
    "speak",
    "coin",
    "risk",
)


def _string_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = item.strip()
        key = clean.lower()
        if not clean or key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _metadata(gm: Mapping[str, Any]) -> dict[str, Any]:
    meta = gm.get("metadata")
    return dict(meta) if isinstance(meta, Mapping) else {}


def _hard_reasons(gm: Mapping[str, Any]) -> list[str]:
    meta = _metadata(gm)
    found: list[str] = []
    attempt = meta.get("hard_validation_attempt_1")
    if isinstance(attempt, Mapping):
        found.extend(str(item) for item in (attempt.get("reasons") or []) if str(item).strip())
    accepted = meta.get("accepted_response")
    if isinstance(accepted, Mapping):
        rejected = accepted.get("rejected_candidate")
        if isinstance(rejected, Mapping):
            found.extend(
                str(item) for item in (rejected.get("hard_invalid_reasons") or []) if str(item).strip()
            )
        hard = accepted.get("hard_validation")
        if isinstance(hard, Mapping):
            found.extend(str(item) for item in (hard.get("reasons") or []) if str(item).strip())
    ordered: list[str] = []
    for reason in found:
        if reason not in ordered:
            ordered.append(reason)
    return ordered


def _decision_audit(gm: Mapping[str, Any]) -> Mapping[str, Any] | None:
    meta = _metadata(gm)
    attempt = meta.get("hard_validation_attempt_1")
    if isinstance(attempt, Mapping) and isinstance(attempt.get("gm_resolution_decision_audit"), Mapping):
        return attempt.get("gm_resolution_decision_audit")
    review = meta.get("decision_review")
    if isinstance(review, Mapping):
        row = review.get("attempt_1")
        if isinstance(row, Mapping) and isinstance(row.get("gm_resolution_decision_audit"), Mapping):
            return row.get("gm_resolution_decision_audit")
    return None


def _declaration_hard_valid(gm: Mapping[str, Any]) -> bool | None:
    audit = _decision_audit(gm)
    if not isinstance(audit, Mapping):
        return None
    declaration = audit.get("declaration_validation")
    if not isinstance(declaration, Mapping) or "hard_valid" not in declaration:
        return None
    return bool(declaration.get("hard_valid"))


def _provider_request_count(gm: Mapping[str, Any]) -> int:
    meta = _metadata(gm)
    try:
        return int(meta.get("narration_provider_calls") or 0)
    except (TypeError, ValueError):
        return 0


def _authoritative_facts_ready(gm: Mapping[str, Any]) -> bool:
    return bool(_string_list(gm.get("opening_curated_facts")))


def classify_opening_initialization_failure(
    gm: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    response_type_contract: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Classify one opening result. Does not mutate state or call a provider."""
    from game.api import _opening_operation_required, _opening_response_rejection

    if not _opening_operation_required(
        resolution if isinstance(resolution, dict) else None,
        response_type_contract if isinstance(response_type_contract, dict) else None,
    ):
        return {
            "recovery_eligibility": "not_an_opening",
            "recoverable": False,
            "original_rejection_code": None,
            "opening_source": OPENING_SOURCE_AI,
        }
    if not isinstance(gm, dict):
        return {
            "recovery_eligibility": "provider_transport_failure",
            "recoverable": False,
            "original_rejection_code": "missing_opening_response",
            "opening_source": OPENING_SOURCE_AI,
        }
    surface = _opening_response_rejection(
        gm,
        resolution if isinstance(resolution, dict) else None,
        response_type_contract if isinstance(response_type_contract, dict) else None,
    )
    reasons = _hard_reasons(gm)
    if surface is None:
        return {
            "recovery_eligibility": "ai_accepted",
            "recoverable": False,
            "original_rejection_code": None,
            "opening_source": OPENING_SOURCE_AI,
            "semantic_reasons": reasons,
        }
    blocking = _blocking_class(surface, reasons, gm)
    if blocking is not None:
        return {
            "recovery_eligibility": blocking,
            "recoverable": False,
            "original_rejection_code": surface,
            "opening_source": OPENING_SOURCE_AI,
            "semantic_reasons": reasons,
        }
    if not _authoritative_facts_ready(gm):
        return {
            "recovery_eligibility": "missing_authoritative_opening_facts",
            "recoverable": False,
            "original_rejection_code": surface,
            "opening_source": OPENING_SOURCE_AI,
            "semantic_reasons": reasons,
        }
    narrative_class = _narrative_class(surface, reasons, gm)
    if narrative_class is None:
        return {
            "recovery_eligibility": "uncertain_rejection",
            "recoverable": False,
            "original_rejection_code": surface,
            "opening_source": OPENING_SOURCE_AI,
            "semantic_reasons": reasons,
        }
    # An unauthorized declaration is an authoritative-fact request. The existing
    # opening contract rejects that attempt and leaves the campaign retryable.
    # Substituting a fallback would commit initialization before the corrected
    # narration can be admitted.
    if narrative_class == "invalid_declarations":
        return {
            "recovery_eligibility": "invalid_declarations",
            "recoverable": False,
            "original_rejection_code": surface,
            "opening_source": OPENING_SOURCE_AI,
            "semantic_reasons": reasons,
        }
    return {
        "recovery_eligibility": narrative_class,
        "recoverable": True,
        "original_rejection_code": surface,
        "opening_source": OPENING_SOURCE_AI,
        "semantic_reasons": reasons,
    }


def _blocking_class(surface: str, reasons: list[str], gm: Mapping[str, Any]) -> str | None:
    reason_set = set(reasons)
    if surface == "provider_budget_refused":
        return "provider_budget_refused"
    if surface in _TRANSPORT_REASONS:
        return "provider_transport_failure"
    if surface in _MALFORMED_REASONS or surface.startswith("malformed") or surface.startswith("missing_"):
        return "malformed_provider_response"
    meta = _metadata(gm)
    if meta.get("structured_contract_failure") or meta.get("structured_output_rejected"):
        return "malformed_provider_response"
    if reason_set & _MECHANICAL_REASONS:
        return "mechanical_validation_failure"
    if reason_set & _HIDDEN_REASONS:
        return "hidden_information_failure"
    if reason_set & _STATE_REASONS:
        return "state_integrity_failure"
    return None


def _narrative_class(surface: str, reasons: list[str], gm: Mapping[str, Any]) -> str | None:
    reason_set = set(reasons)
    if surface in _UNUSABLE_NARRATION_REASONS:
        if reason_set and not reason_set <= _NARRATIVE_REASONS:
            return None
        return "unusable_player_facing_narration"
    if surface != "safe_nonresolution":
        return None
    if not reason_set:
        return None
    unknown = reason_set - _NARRATIVE_REASONS
    if unknown:
        return None
    declaration_valid = _declaration_hard_valid(gm)
    if declaration_valid is False:
        return "invalid_declarations"
    return "semantic_narration_rejection"


def _record_from(classification: Mapping[str, Any], gm: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "opening_source": classification.get("opening_source") or OPENING_SOURCE_AI,
        "original_rejection_code": classification.get("original_rejection_code"),
        "recovery_eligibility": classification.get("recovery_eligibility"),
        "fallback_attempted": False,
        "fallback_succeeded": False,
        "fallback_error": None,
        "provider_requests_consumed": _provider_request_count(gm) if isinstance(gm, Mapping) else 0,
        "initialization_outcome": "pending",
        "state_integrity": "not_committed",
        "semantic_reasons": list(classification.get("semantic_reasons") or []),
    }


def _authoritative_composer_input(gm: Mapping[str, Any]) -> dict[str, Any]:
    """Selector facts only. Provider narration and effect fields are omitted."""
    facts = _string_list(gm.get("opening_curated_facts"))
    selector = _string_list(gm.get("opening_selector_selected_facts")) or list(facts)
    meta = _metadata(gm)
    emission = meta.get("emission_debug") if isinstance(meta.get("emission_debug"), Mapping) else {}
    source = str(emission.get("opening_curated_facts_source") or "selector")
    selector_source = str(emission.get("opening_selector_source_used") or source or "selector")
    return {
        "opening_curated_facts": facts,
        "opening_selector_selected_facts": selector,
        "metadata": {
            "emission_debug": {
                "opening_curated_facts_source": source,
                "opening_selector_source_used": selector_source,
                "opening_selector_selected_facts": list(selector),
            }
        },
    }


def _template_text(composer_input: Mapping[str, Any]) -> str:
    """Same fact/hook selection as the composer. Extra sentences fail this check."""
    context = opening_context_from_gm_output(composer_input)
    facts = [str(item).strip().rstrip(".") for item in (context.get("visible_facts") or []) if str(item).strip()]
    used: set[str] = set()
    environment = _pick_opening_fallback_fact(facts, used=used, needles=_ENVIRONMENT_NEEDLES)
    activity = _pick_opening_fallback_fact(facts, used=used, needles=_ACTIVITY_NEEDLES)
    hook_fact = _pick_opening_fallback_fact(facts, used=used, needles=_HOOK_NEEDLES)
    hook = _actionable_hook_from_opening_context(context)
    parts = [str(part).strip().rstrip(".") for part in (environment, activity, hook_fact, hook) if str(part).strip()]
    return _normalize_text(". ".join(parts) + ".")


def _validate_fallback(text: str, meta: Mapping[str, Any], composer_input: Mapping[str, Any]) -> str | None:
    if not isinstance(text, str) or not text.strip():
        return "empty_fallback_text"
    if text.strip() == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER or OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER in text:
        return "empty_curated_facts"
    if not meta.get("opening_final_basis_matches_selector"):
        return "selector_diverged"
    if meta.get("opening_fallback_failed_closed"):
        return "opening_fallback_failed_closed"
    if list(meta.get("opening_curated_facts") or []) != list(composer_input.get("opening_curated_facts") or []):
        return "fallback_basis_not_authoritative"
    expected = _template_text(composer_input)
    if text != expected:
        return "fallback_text_not_template"
    from game.final_emission_validators import candidate_satisfies_scene_opening_contract

    accepted, reasons = candidate_satisfies_scene_opening_contract(text)
    if not accepted:
        return str((reasons or ["scene_opening_contract_rejected"])[0])
    return None


def _strip_rejected_prose(gm: dict[str, Any]) -> None:
    meta = gm.get("metadata")
    if not isinstance(meta, dict):
        return
    attempt = meta.get("hard_validation_attempt_1")
    if isinstance(attempt, dict):
        attempt.pop("text", None)
        attempt.pop("gm_resolution_decision_audit", None)
    meta.pop("decision_review", None)
    meta.pop("regeneration_feedback", None)
    envelope = meta.get("realization_envelope")
    if isinstance(envelope, dict):
        envelope["narration"] = ""
        envelope["declared_claims"] = []
        envelope["discarded_before_deterministic_recovery"] = True


def _install_fallback(gm: dict[str, Any], text: str, record: Mapping[str, Any]) -> None:
    from game.immutable_valid_response import seal_accepted_response, seal_delivery_contract

    _strip_rejected_prose(gm)
    for key in _EFFECT_KEYS:
        gm[key] = None
    gm.pop("improvisation_proposals", None)
    gm.pop("bounded_improvisation_authority", None)
    gm.pop("upstream_prepared_emission", None)
    gm.pop("upstream_prepared_opening_fallback", None)
    tags = [tag for tag in (gm.get("tags") or []) if isinstance(tag, str) and tag not in _BLOCKING_TAGS]
    gm["tags"] = tags
    meta = gm.setdefault("metadata", {})
    if not isinstance(meta, dict):
        meta = {}
        gm["metadata"] = meta
    for key in ("structured_contract_failure", "structured_output_rejected", "structured_contract_reason"):
        meta.pop(key, None)
    notes = str(gm.get("debug_notes") or "")
    if notes.startswith("call_gpt error") or "provider_calls_disabled" in notes or "provider_budget_refused" in notes:
        gm["debug_notes"] = "Deterministic opening recovery."
    emission = meta.get("emission_debug")
    if isinstance(emission, dict):
        emission.pop("opening_fallback_failed_closed", None)
        if emission.get("response_type_candidate_ok") is False:
            emission["response_type_candidate_ok"] = True
    seal_accepted_response(
        gm,
        text=text,
        provenance=PROVENANCE_DETERMINISTIC_OPENING_RECOVERY,
        attempt=1,
        validation={
            "hard_valid": True,
            "reasons": [],
            "soft_flags": [],
            "speaker": "GM",
            "addressee": "player",
            "operation": "scene_opening",
            "interaction_complete": True,
            "contract_satisfying": True,
            "authority": ["authoritative_opening_facts"],
        },
        contract={"operation": "scene_opening"},
        player_text="",
        resolution={"kind": "scene_opening"},
    )
    seal_delivery_contract(gm)
    stamp_opening_recovery_debug(gm, record)


def stamp_opening_recovery_debug(gm: dict[str, Any] | None, record: Mapping[str, Any] | None) -> None:
    if not isinstance(gm, dict) or not isinstance(record, Mapping):
        return
    meta = gm.setdefault("metadata", {})
    if not isinstance(meta, dict):
        return
    meta["opening_recovery_debug"] = diagnostic_opening_recovery(record)


def diagnostic_opening_recovery(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Code-only view for the existing opening diagnostic. No narration text."""
    if not isinstance(record, Mapping):
        return None
    return {
        "opening_source": record.get("opening_source"),
        "original_rejection_code": record.get("original_rejection_code"),
        "recovery_eligibility": record.get("recovery_eligibility"),
        "fallback_attempted": bool(record.get("fallback_attempted")),
        "fallback_succeeded": bool(record.get("fallback_succeeded")),
        "fallback_error": record.get("fallback_error"),
        "provider_requests_consumed": record.get("provider_requests_consumed"),
        "initialization_outcome": record.get("initialization_outcome"),
        "state_integrity": record.get("state_integrity"),
    }


def apply_opening_initialization_recovery(
    gm: dict[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    response_type_contract: Mapping[str, Any] | None,
    *,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Recover an eligible opening, or leave a nonrecoverable result unchanged.

    The composer runs only after the existing validator has already sealed a
    recoverable rejection. This function does not re-validate or reseal a
    response the pipeline has not rejected. Scene, world, and session are
    accepted so the initialization caller can pass them without a second read;
    recovery does not mutate them.
    """
    del scene, world, session
    classification = classify_opening_initialization_failure(gm, resolution, response_type_contract)
    record = _record_from(classification, gm)
    if not classification.get("recoverable"):
        if classification.get("recovery_eligibility") == "ai_accepted" and isinstance(gm, dict):
            record["initialization_outcome"] = "pending_commit"
            record["state_integrity"] = "ai_opening_accepted"
            stamp_opening_recovery_debug(gm, record)
        else:
            record["initialization_outcome"] = "rejected"
        return gm, record
    record["fallback_attempted"] = True
    composer_input = _authoritative_composer_input(gm if isinstance(gm, Mapping) else {})
    try:
        text, meta = deterministic_opening_fallback_text_and_meta(composer_input)
    except Exception as exc:
        record["fallback_error"] = type(exc).__name__
        record["initialization_outcome"] = "failed"
        record["state_integrity"] = "not_committed"
        return gm, record
    if not isinstance(meta, Mapping):
        record["fallback_error"] = "fallback_meta_missing"
        record["initialization_outcome"] = "failed"
        record["state_integrity"] = "not_committed"
        return gm, record
    problem = _validate_fallback(text, meta, composer_input)
    if problem:
        record["fallback_error"] = problem
        record["initialization_outcome"] = "failed"
        record["state_integrity"] = "not_committed"
        return gm, record
    if not isinstance(gm, dict):
        record["fallback_error"] = "missing_opening_response"
        record["initialization_outcome"] = "failed"
        record["state_integrity"] = "not_committed"
        return gm, record
    record["fallback_succeeded"] = True
    record["opening_source"] = OPENING_SOURCE_DETERMINISTIC
    record["initialization_outcome"] = "pending_commit"
    record["state_integrity"] = "provider_result_discarded"
    _install_fallback(gm, text, record)
    return gm, record
