"""Visibility fallback FEM metadata stamping and diagnostic payload construction.

This module owns visibility fallback FEM metadata stamping and diagnostic payload
construction. It does **not** select fallback text or run visibility enforcement.
"""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, Dict, Literal

from game.final_emission_owner_bucket_views import visibility_fallback_owner_bucket_from_fields

_UNSET = object()


def _default_first_mention_composition_layers() -> dict[str, Any]:
    from game.final_emission_visibility_fallback import default_first_mention_composition_layers

    return default_first_mention_composition_layers()


@dataclass(frozen=True)
class VisibilityValidationObservation:
    validation_passed: bool
    violation_kinds: list[str]
    violation_sample: list[dict[str, Any]]
    checked_entities: list[Any]
    checked_facts: list[Any]


@dataclass(frozen=True)
class VisibilityDefaultMetadataPayload:
    validation_passed: bool
    replacement_applied: bool
    violation_kinds: list[str]
    violation_sample: list[dict[str, Any]]
    checked_entities: list[Any]
    checked_facts: list[Any]

    def stamp_kwargs(self) -> dict[str, Any]:
        return {
            "validation_passed": self.validation_passed,
            "replacement_applied": self.replacement_applied,
            "violation_kinds": list(self.violation_kinds),
            "violation_sample": [dict(item) if isinstance(item, Mapping) else item for item in self.violation_sample],
            "checked_entities": list(self.checked_entities),
            "checked_facts": list(self.checked_facts),
        }


@dataclass(frozen=True)
class VisibilityFirstMentionDefaultMetadataPayload:
    first_mention_validation_passed: Any
    first_mention_replacement_applied: bool
    first_mention_violation_kinds: list[str]
    first_mention_checked_entities: list[Any]
    first_mention_leading_pronoun_detected: bool
    first_mention_first_explicit_entity_offset: Any
    first_mention_fallback_strategy: Any
    first_mention_fallback_candidate_source: Any
    opening_scene_first_mention_preference_used: bool
    first_mention_composition_used: bool
    first_mention_composition_layers: Any

    def meta_updates(self) -> dict[str, Any]:
        return {
            "first_mention_validation_passed": self.first_mention_validation_passed,
            "first_mention_replacement_applied": self.first_mention_replacement_applied,
            "first_mention_violation_kinds": list(self.first_mention_violation_kinds),
            "first_mention_checked_entities": list(self.first_mention_checked_entities),
            "first_mention_leading_pronoun_detected": self.first_mention_leading_pronoun_detected,
            "first_mention_first_explicit_entity_offset": self.first_mention_first_explicit_entity_offset,
            "first_mention_fallback_strategy": self.first_mention_fallback_strategy,
            "first_mention_fallback_candidate_source": self.first_mention_fallback_candidate_source,
            "opening_scene_first_mention_preference_used": self.opening_scene_first_mention_preference_used,
            "first_mention_composition_used": self.first_mention_composition_used,
            "first_mention_composition_layers": self.first_mention_composition_layers,
        }


@dataclass(frozen=True)
class VisibilityPreRouteMetadataContext:
    first_mention_defaults: VisibilityFirstMentionDefaultMetadataPayload
    visibility_defaults: VisibilityDefaultMetadataPayload


@dataclass(frozen=True)
class VisibilityRouteMetadataOutcome:
    validation_passed: Any = None
    replacement_applied: Any = _UNSET
    continuity_lead_exemption: bool | None = None
    fallback_pool: str | None = None
    fallback_kind: str | None = None
    fallback_owner_bucket: str | None = None

    def stamp_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"validation_passed": self.validation_passed}
        if self.replacement_applied is not _UNSET:
            kwargs["replacement_applied"] = self.replacement_applied
        if self.continuity_lead_exemption is not None:
            kwargs["continuity_lead_exemption"] = self.continuity_lead_exemption
        if self.fallback_pool is not None:
            kwargs["fallback_pool"] = self.fallback_pool
        if self.fallback_kind is not None:
            kwargs["fallback_kind"] = self.fallback_kind
        if self.fallback_owner_bucket is not None:
            kwargs["fallback_owner_bucket"] = self.fallback_owner_bucket
        return kwargs


@dataclass(frozen=True)
class VisibilityFirstMentionMetadataPayload:
    first_mention_composition_used: bool
    first_mention_composition_layers: Any

    def meta_updates(self) -> dict[str, Any]:
        return {
            "first_mention_composition_used": self.first_mention_composition_used,
            "first_mention_composition_layers": self.first_mention_composition_layers,
        }


@dataclass(frozen=True)
class FirstMentionSelectedFallbackMetadataPayload:
    first_mention_validation_passed: bool
    first_mention_replacement_applied: bool
    first_mention_fallback_strategy: str
    first_mention_fallback_candidate_source: str
    opening_scene_first_mention_preference_used: bool
    first_mention_composition_used: bool
    first_mention_composition_layers: Any

    def meta_updates(self) -> dict[str, Any]:
        return {
            "first_mention_validation_passed": self.first_mention_validation_passed,
            "first_mention_replacement_applied": self.first_mention_replacement_applied,
            "first_mention_fallback_strategy": self.first_mention_fallback_strategy,
            "first_mention_fallback_candidate_source": self.first_mention_fallback_candidate_source,
            "opening_scene_first_mention_preference_used": self.opening_scene_first_mention_preference_used,
            "first_mention_composition_used": self.first_mention_composition_used,
            "first_mention_composition_layers": self.first_mention_composition_layers,
        }


@dataclass(frozen=True)
class ReferentialClaritySelectedFallbackMetadataPayload:
    referential_clarity_validation_passed: bool
    referential_clarity_replacement_applied: bool
    first_mention_composition_used: bool
    first_mention_composition_layers: Any

    def meta_updates(self) -> dict[str, Any]:
        return {
            "referential_clarity_validation_passed": self.referential_clarity_validation_passed,
            "referential_clarity_replacement_applied": self.referential_clarity_replacement_applied,
            "first_mention_composition_used": self.first_mention_composition_used,
            "first_mention_composition_layers": self.first_mention_composition_layers,
        }


@dataclass(frozen=True)
class FirstMentionReplacementLoggingPayload:
    social_route: bool
    candidate_ok: bool
    rejection_reasons: list[str]
    fallback_pool: str
    fallback_kind: str
    active_interlocutor: str | None

    def decision_payload(self) -> dict[str, Any]:
        return {
            "stage": "final_emission_gate_first_mention",
            "social_route": self.social_route,
            "candidate_ok": self.candidate_ok,
            "rejection_reasons": list(self.rejection_reasons),
            "fallback_pool": self.fallback_pool,
            "fallback_kind": self.fallback_kind,
            "active_interlocutor": self.active_interlocutor,
        }


@dataclass(frozen=True)
class ReferentialClarityReplacementLoggingPayload:
    social_route: bool
    candidate_ok: bool
    rejection_reasons: list[str]
    fallback_pool: str
    fallback_kind: str
    active_interlocutor: str | None
    referential_clarity_fallback_after_failed_local_repair: bool

    def decision_payload(self) -> dict[str, Any]:
        return {
            "stage": "final_emission_gate_referential_clarity",
            "social_route": self.social_route,
            "candidate_ok": self.candidate_ok,
            "rejection_reasons": list(self.rejection_reasons),
            "fallback_pool": self.fallback_pool,
            "fallback_kind": self.fallback_kind,
            "active_interlocutor": self.active_interlocutor,
            "referential_clarity_fallback_after_failed_local_repair": (
                self.referential_clarity_fallback_after_failed_local_repair
            ),
        }


@dataclass(frozen=True)
class VisibilityHardReplacementLoggingPayload:
    social_route: bool
    candidate_ok: bool
    rejection_reasons: list[str]
    fallback_pool: str
    fallback_kind: str
    active_interlocutor: str | None
    trace_stage: str

    def decision_payload(self) -> dict[str, Any]:
        return {
            "stage": "final_emission_gate_visibility",
            "social_route": self.social_route,
            "candidate_ok": self.candidate_ok,
            "rejection_reasons": list(self.rejection_reasons),
            "fallback_pool": self.fallback_pool,
            "fallback_kind": self.fallback_kind,
            "active_interlocutor": self.active_interlocutor,
        }

    def trace_payload(self, meta: Mapping[str, Any]) -> dict[str, Any]:
        return {**meta, "stage": self.trace_stage}

@dataclass(frozen=True)
class VisibilityNonReplacementRouteContext:
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
    ]
    observation: VisibilityValidationObservation
    route_metadata_outcome: VisibilityRouteMetadataOutcome
    return_token: Literal[
        "apply_first_mention_enforcement",
        "return_current_output",
    ]
    debug_notes_to_add: str | None = None


def _dedupe_preserve_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _build_visibility_violation_sample(violations: Sequence[Any]) -> list[dict[str, Any]]:
    sample: list[dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, Mapping):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "matched_entity_id": violation.get("matched_entity_id"),
                "matched_fact": violation.get("matched_fact"),
            }
        )
    return sample


def build_visibility_validation_observation(
    validation: Mapping[str, Any] | None,
) -> VisibilityValidationObservation:
    validation_map = validation if isinstance(validation, Mapping) else {}
    violations = validation_map.get("violations") if isinstance(validation_map.get("violations"), list) else []
    checked_entities = (
        validation_map.get("visibility_checked_entities")
        if isinstance(validation_map.get("visibility_checked_entities"), list)
        else []
    )
    checked_facts = (
        validation_map.get("visibility_checked_facts")
        if isinstance(validation_map.get("visibility_checked_facts"), list)
        else []
    )
    violation_kinds = _dedupe_preserve_order(
        [
            str(v.get("kind") or "")
            for v in violations
            if isinstance(v, Mapping) and str(v.get("kind") or "").strip()
        ]
    )
    return VisibilityValidationObservation(
        validation_passed=validation_map.get("ok") is True,
        violation_kinds=violation_kinds,
        violation_sample=_build_visibility_violation_sample(violations),
        checked_entities=checked_entities,
        checked_facts=checked_facts,
    )


def build_visibility_default_metadata_payload(
    observation: VisibilityValidationObservation,
) -> VisibilityDefaultMetadataPayload:
    return VisibilityDefaultMetadataPayload(
        validation_passed=observation.validation_passed,
        replacement_applied=False,
        violation_kinds=list(observation.violation_kinds),
        violation_sample=[
            dict(item) if isinstance(item, Mapping) else item
            for item in observation.violation_sample
        ],
        checked_entities=list(observation.checked_entities),
        checked_facts=list(observation.checked_facts),
    )


def build_visibility_first_mention_default_metadata_payload() -> VisibilityFirstMentionDefaultMetadataPayload:
    return VisibilityFirstMentionDefaultMetadataPayload(
        first_mention_validation_passed=None,
        first_mention_replacement_applied=False,
        first_mention_violation_kinds=[],
        first_mention_checked_entities=[],
        first_mention_leading_pronoun_detected=False,
        first_mention_first_explicit_entity_offset=None,
        first_mention_fallback_strategy=None,
        first_mention_fallback_candidate_source=None,
        opening_scene_first_mention_preference_used=False,
        first_mention_composition_used=False,
        first_mention_composition_layers=_default_first_mention_composition_layers(),
    )


def build_visibility_pre_route_metadata_context(
    *,
    observation: VisibilityValidationObservation,
) -> VisibilityPreRouteMetadataContext:
    return VisibilityPreRouteMetadataContext(
        first_mention_defaults=build_visibility_first_mention_default_metadata_payload(),
        visibility_defaults=build_visibility_default_metadata_payload(observation),
    )


def build_visibility_route_metadata_outcome(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ],
    fallback_pool: str | None = None,
    fallback_kind: str | None = None,
    final_emitted_source: str | None = None,
) -> VisibilityRouteMetadataOutcome:
    if route == "continuity_lead_exemption":
        return VisibilityRouteMetadataOutcome(
            validation_passed=True,
            replacement_applied=False,
            continuity_lead_exemption=True,
        )
    if route == "concrete_interaction_no_hard_replace":
        return VisibilityRouteMetadataOutcome(validation_passed=None)
    fallback_owner_bucket = visibility_fallback_owner_bucket_from_fields(
        fallback_pool=fallback_pool or "",
        fallback_kind=fallback_kind or "",
        final_emitted_source=final_emitted_source or "",
    )
    return VisibilityRouteMetadataOutcome(
        validation_passed=observation.validation_passed,
        replacement_applied=True,
        fallback_pool=fallback_pool,
        fallback_kind=fallback_kind,
        fallback_owner_bucket=fallback_owner_bucket,
    )


def build_visibility_first_mention_metadata_payload(
    *,
    composition_meta: Mapping[str, Any],
) -> VisibilityFirstMentionMetadataPayload:
    default_layers = _default_first_mention_composition_layers()
    return VisibilityFirstMentionMetadataPayload(
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_layers,
        ),
    )


def build_first_mention_selected_fallback_metadata_payload(
    selected_fallback: Any,
    *,
    opening_scene_first_mention_preference_used: bool,
) -> FirstMentionSelectedFallbackMetadataPayload:
    composition_meta = selected_fallback.composition_meta
    default_layers = _default_first_mention_composition_layers()
    return FirstMentionSelectedFallbackMetadataPayload(
        first_mention_validation_passed=False,
        first_mention_replacement_applied=True,
        first_mention_fallback_strategy=selected_fallback.fallback_strategy,
        first_mention_fallback_candidate_source=selected_fallback.fallback_candidate_source,
        opening_scene_first_mention_preference_used=opening_scene_first_mention_preference_used,
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_layers,
        ),
    )


def build_referential_clarity_selected_fallback_metadata_payload(
    selected_fallback: Any,
) -> ReferentialClaritySelectedFallbackMetadataPayload:
    composition_meta = selected_fallback.composition_meta
    default_layers = _default_first_mention_composition_layers()
    return ReferentialClaritySelectedFallbackMetadataPayload(
        referential_clarity_validation_passed=False,
        referential_clarity_replacement_applied=True,
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_layers,
        ),
    )


def build_first_mention_replacement_logging_payload(
    selected_fallback: Any,
    *,
    strict_social_active: bool,
    violation_kinds: Sequence[str],
    active_interlocutor: str,
) -> FirstMentionReplacementLoggingPayload:
    return FirstMentionReplacementLoggingPayload(
        social_route=strict_social_active,
        candidate_ok=False,
        rejection_reasons=list(violation_kinds[:12]),
        fallback_pool=selected_fallback.fallback_pool,
        fallback_kind=selected_fallback.fallback_kind,
        active_interlocutor=active_interlocutor or None,
    )


def build_referential_clarity_replacement_logging_payload(
    selected_fallback: Any,
    *,
    strict_social_active: bool,
    violation_kinds: Sequence[str],
    active_interlocutor: str,
    referential_clarity_fallback_after_failed_local_repair: bool,
) -> ReferentialClarityReplacementLoggingPayload:
    return ReferentialClarityReplacementLoggingPayload(
        social_route=strict_social_active,
        candidate_ok=False,
        rejection_reasons=list(violation_kinds[:12]),
        fallback_pool=selected_fallback.fallback_pool,
        fallback_kind=selected_fallback.fallback_kind,
        active_interlocutor=active_interlocutor or None,
        referential_clarity_fallback_after_failed_local_repair=bool(
            referential_clarity_fallback_after_failed_local_repair
        ),
    )


def build_visibility_hard_replacement_logging_payload(
    *,
    strict_social_active: bool,
    observation: VisibilityValidationObservation,
    fallback_pool: str,
    fallback_kind: str,
    active_interlocutor: str,
) -> VisibilityHardReplacementLoggingPayload:
    return VisibilityHardReplacementLoggingPayload(
        social_route=strict_social_active,
        candidate_ok=False,
        rejection_reasons=observation.violation_kinds[:12],
        fallback_pool=fallback_pool,
        fallback_kind=fallback_kind,
        active_interlocutor=active_interlocutor or None,
        trace_stage="final_emission_gate_visibility_replace",
    )


def build_visibility_non_replacement_route_context(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
    ],
) -> VisibilityNonReplacementRouteContext:
    route_metadata_outcome = build_visibility_route_metadata_outcome(
        observation=observation,
        route=route,
    )
    return_token: Literal["apply_first_mention_enforcement", "return_current_output"]
    if route == "continuity_lead_exemption":
        return_token = "apply_first_mention_enforcement"
    else:
        return_token = "return_current_output"
    return VisibilityNonReplacementRouteContext(
        route=route,
        observation=observation,
        route_metadata_outcome=route_metadata_outcome,
        return_token=return_token,
        debug_notes_to_add=None,
    )


def stamp_visibility_fallback_metadata(
    meta: MutableMapping[str, Any],
    *,
    validation_passed: Any = _UNSET,
    replacement_applied: Any = _UNSET,
    violation_kinds: Sequence[str] | None = None,
    violation_sample: Sequence[Mapping[str, Any]] | None = None,
    checked_entities: Sequence[Any] | None = None,
    checked_facts: Sequence[Any] | None = None,
    continuity_lead_exemption: bool | None = None,
    fallback_pool: str | None = None,
    fallback_kind: str | None = None,
    fallback_owner_bucket: str | None = None,
    final_emitted_source: str | None = None,
) -> None:
    if not isinstance(meta, MutableMapping):
        return
    if validation_passed is not _UNSET:
        meta["visibility_validation_passed"] = validation_passed
    if replacement_applied is not _UNSET:
        meta["visibility_replacement_applied"] = replacement_applied
    if violation_kinds is not None:
        meta["visibility_violation_kinds"] = list(violation_kinds)
    if violation_sample is not None:
        meta["visibility_violation_sample"] = [dict(item) if isinstance(item, Mapping) else item for item in violation_sample]
    if checked_entities is not None:
        meta["visibility_checked_entities"] = list(checked_entities)
    if checked_facts is not None:
        meta["visibility_checked_facts"] = list(checked_facts)
    if continuity_lead_exemption is not None:
        meta["visibility_continuity_lead_exemption"] = bool(continuity_lead_exemption)
    if fallback_pool is not None:
        meta["visibility_fallback_pool"] = fallback_pool
    if fallback_kind is not None:
        meta["visibility_fallback_kind"] = fallback_kind
    if fallback_owner_bucket is not None:
        meta["visibility_fallback_owner_bucket"] = fallback_owner_bucket
    elif fallback_pool is not None or fallback_kind is not None or final_emitted_source is not None:
        meta["visibility_fallback_owner_bucket"] = visibility_fallback_owner_bucket_from_fields(
            fallback_pool=fallback_pool or "",
            fallback_kind=fallback_kind or "",
            final_emitted_source=final_emitted_source or "",
        )

