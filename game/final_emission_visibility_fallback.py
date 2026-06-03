"""Visibility fallback routing helpers. This module must not author fallback prose or write final output."""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
import re
from typing import Any, Literal, Sequence

from game.final_emission_meta import (
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
)

_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile("[\\\"\u201c\u201d'\u2018\u2019]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)


_UNSET = object()


@dataclass(frozen=True)
class VisibilityValidationObservation:
    validation_passed: bool
    violation_kinds: list[str]
    violation_sample: list[dict[str, Any]]
    checked_entities: list[Any]
    checked_facts: list[Any]


@dataclass(frozen=True)
class VisibilityPreRouteValidationContext:
    candidate_text: str
    validation_result: Mapping[str, Any] | None
    observation: VisibilityValidationObservation


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
class VisibilityReplacementAnnotations:
    tags_to_add: list[str]
    debug_notes_to_add: str


@dataclass(frozen=True)
class VisibilityHardReplacementPlan:
    fallback_text: str
    fallback_pool: str
    fallback_kind: str
    final_emitted_source: str
    observation: VisibilityValidationObservation
    route_metadata_outcome: VisibilityRouteMetadataOutcome
    annotations: VisibilityReplacementAnnotations


@dataclass(frozen=True)
class VisibilitySelectedFallback:
    text: str
    fallback_pool: str
    fallback_kind: str
    final_emitted_source: str
    fallback_strategy: str
    fallback_candidate_source: str
    composition_meta: Mapping[str, Any]

    @classmethod
    def from_legacy_tuple(
        cls,
        value: tuple[str, str, str, str, str, str, Mapping[str, Any]],
    ) -> "VisibilitySelectedFallback":
        (
            text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            fallback_strategy,
            fallback_candidate_source,
            composition_meta,
        ) = value
        return cls(
            text=text,
            fallback_pool=fallback_pool,
            fallback_kind=fallback_kind,
            final_emitted_source=final_emitted_source,
            fallback_strategy=fallback_strategy,
            fallback_candidate_source=fallback_candidate_source,
            composition_meta=composition_meta,
        )

    def as_legacy_tuple(self) -> tuple[str, str, str, str, str, str, Mapping[str, Any]]:
        return (
            self.text,
            self.fallback_pool,
            self.fallback_kind,
            self.final_emitted_source,
            self.fallback_strategy,
            self.fallback_candidate_source,
            self.composition_meta,
        )


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
class VisibilityHardReplacementContext:
    replacement_plan: VisibilityHardReplacementPlan
    first_mention_payload: VisibilityFirstMentionMetadataPayload
    logging_payload: VisibilityHardReplacementLoggingPayload


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


@dataclass(frozen=True)
class VisibilityFallbackSelectionInputs:
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ]
    strict_social_route: bool
    strict_social_suppressed_non_social_turn: bool
    has_active_social_interlocutor: bool
    violation_kinds: list[str]
    checked_entities: list[Any]
    checked_facts: list[Any]
    emit_integrity_response_type_required: str


@dataclass(frozen=True)
class VisibilityRouteDispatchContext:
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ]
    observation: VisibilityValidationObservation
    non_replacement_context: VisibilityNonReplacementRouteContext | None
    selection_inputs: VisibilityFallbackSelectionInputs | None


@dataclass(frozen=True)
class VisibilityRouteDecisionInputs:
    tag_list_gate: list[str]
    dbg_gate: str
    violation_kinds: list[str]
    checked_entities: list[Any]
    checked_facts: list[Any]
    candidate_text: str


@dataclass(frozen=True)
class VisibilityEnforcementStageContext:
    pre_route_validation: VisibilityPreRouteValidationContext
    pre_route_metadata: VisibilityPreRouteMetadataContext
    route_decision_inputs: VisibilityRouteDecisionInputs


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


def build_visibility_pre_route_validation_context(
    *,
    candidate_text: str,
    validation_result: Mapping[str, Any] | None,
) -> VisibilityPreRouteValidationContext:
    return VisibilityPreRouteValidationContext(
        candidate_text=candidate_text,
        validation_result=validation_result,
        observation=build_visibility_validation_observation(validation_result),
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


def build_visibility_first_mention_default_metadata_payload(
    *,
    default_first_mention_composition_layers: Any,
) -> VisibilityFirstMentionDefaultMetadataPayload:
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
        first_mention_composition_layers=default_first_mention_composition_layers,
    )


def build_visibility_pre_route_metadata_context(
    *,
    observation: VisibilityValidationObservation,
    default_first_mention_composition_layers: Any,
) -> VisibilityPreRouteMetadataContext:
    return VisibilityPreRouteMetadataContext(
        first_mention_defaults=build_visibility_first_mention_default_metadata_payload(
            default_first_mention_composition_layers=default_first_mention_composition_layers,
        ),
        visibility_defaults=build_visibility_default_metadata_payload(observation),
    )


def build_visibility_route_decision_inputs(
    *,
    tag_list_gate: Sequence[str],
    dbg_gate: str,
    observation: VisibilityValidationObservation,
    candidate_text: str,
) -> VisibilityRouteDecisionInputs:
    return VisibilityRouteDecisionInputs(
        tag_list_gate=[str(tag) for tag in tag_list_gate],
        dbg_gate=str(dbg_gate or ""),
        violation_kinds=list(observation.violation_kinds),
        checked_entities=list(observation.checked_entities),
        checked_facts=list(observation.checked_facts),
        candidate_text=candidate_text,
    )


def build_visibility_enforcement_stage_context(
    *,
    candidate_text: str,
    validation_result: Mapping[str, Any] | None,
    default_first_mention_composition_layers: Any,
    tag_list_gate: Sequence[str],
    dbg_gate: str,
) -> VisibilityEnforcementStageContext:
    pre_route_validation = build_visibility_pre_route_validation_context(
        candidate_text=candidate_text,
        validation_result=validation_result,
    )
    pre_route_metadata = build_visibility_pre_route_metadata_context(
        observation=pre_route_validation.observation,
        default_first_mention_composition_layers=default_first_mention_composition_layers,
    )
    route_decision_inputs = build_visibility_route_decision_inputs(
        tag_list_gate=tag_list_gate,
        dbg_gate=dbg_gate,
        observation=pre_route_validation.observation,
        candidate_text=pre_route_validation.candidate_text,
    )
    return VisibilityEnforcementStageContext(
        pre_route_validation=pre_route_validation,
        pre_route_metadata=pre_route_metadata,
        route_decision_inputs=route_decision_inputs,
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def route_visibility_enforcement_after_failed_validation(
    *,
    tag_list_gate: Sequence[str],
    dbg_gate: str,
    violation_kinds: Sequence[str],
    checked_entities: Sequence[Any],
    checked_facts: Sequence[Any],
    candidate_text: str,
) -> Literal[
    "continuity_lead_exemption",
    "concrete_interaction_no_hard_replace",
    "sealed_hard_replace",
]:
    """Branch selector after visibility validation fails (order-sensitive; snapshots depend on it)."""
    if (
        "known_fact_guard" in tag_list_gate
        and "recent_dialogue_continuity" in dbg_gate
        and violation_kinds == ["unseen_entity_reference"]
    ):
        return "continuity_lead_exemption"
    if not checked_entities and not checked_facts and _reply_already_has_concrete_interaction(candidate_text):
        return "concrete_interaction_no_hard_replace"
    return "sealed_hard_replace"


def classify_visibility_fallback_owner_bucket(
    *,
    fallback_pool: str,
    fallback_kind: str,
    final_emitted_source: str,
) -> str:
    pool = str(fallback_pool or "").strip()
    kind = str(fallback_kind or "").strip()
    source = str(final_emitted_source or "").strip()
    if not (pool or kind or source):
        return VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE
    if pool == "scene_opening_deterministic" or kind == "opening_deterministic_fallback":
        return VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY
    if pool == "strict_social_visibility_minimal" or kind == "visibility_minimal_social_fallback":
        return VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
    return VISIBILITY_FALLBACK_OWNER_SEALED_GATE


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
    fallback_owner_bucket = classify_visibility_fallback_owner_bucket(
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


def build_visibility_replacement_annotations(
    observation: VisibilityValidationObservation,
) -> VisibilityReplacementAnnotations:
    return VisibilityReplacementAnnotations(
        tags_to_add=["final_emission_gate_replaced", "visibility_enforcement_replaced"]
        + [f"visibility_violation:{kind}" for kind in observation.violation_kinds],
        debug_notes_to_add="final_emission_gate:visibility_replaced:" + ",".join(observation.violation_kinds[:8]),
    )


def build_visibility_hard_replacement_plan(
    *,
    observation: VisibilityValidationObservation,
    route_metadata_outcome: VisibilityRouteMetadataOutcome,
    annotations: VisibilityReplacementAnnotations,
    selected_fallback: VisibilitySelectedFallback,
) -> VisibilityHardReplacementPlan:
    return VisibilityHardReplacementPlan(
        fallback_text=selected_fallback.text,
        fallback_pool=selected_fallback.fallback_pool,
        fallback_kind=selected_fallback.fallback_kind,
        final_emitted_source=selected_fallback.final_emitted_source,
        observation=observation,
        route_metadata_outcome=route_metadata_outcome,
        annotations=annotations,
    )


def build_visibility_first_mention_metadata_payload(
    *,
    composition_meta: Mapping[str, Any],
    default_first_mention_composition_layers: Any,
) -> VisibilityFirstMentionMetadataPayload:
    return VisibilityFirstMentionMetadataPayload(
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_first_mention_composition_layers,
        ),
    )


def build_first_mention_selected_fallback_metadata_payload(
    selected_fallback: VisibilitySelectedFallback,
    *,
    opening_scene_first_mention_preference_used: bool,
    default_first_mention_composition_layers: Any,
) -> FirstMentionSelectedFallbackMetadataPayload:
    composition_meta = selected_fallback.composition_meta
    return FirstMentionSelectedFallbackMetadataPayload(
        first_mention_validation_passed=False,
        first_mention_replacement_applied=True,
        first_mention_fallback_strategy=selected_fallback.fallback_strategy,
        first_mention_fallback_candidate_source=selected_fallback.fallback_candidate_source,
        opening_scene_first_mention_preference_used=opening_scene_first_mention_preference_used,
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_first_mention_composition_layers,
        ),
    )


def build_referential_clarity_selected_fallback_metadata_payload(
    selected_fallback: VisibilitySelectedFallback,
    *,
    default_first_mention_composition_layers: Any,
) -> ReferentialClaritySelectedFallbackMetadataPayload:
    composition_meta = selected_fallback.composition_meta
    return ReferentialClaritySelectedFallbackMetadataPayload(
        referential_clarity_validation_passed=False,
        referential_clarity_replacement_applied=True,
        first_mention_composition_used=bool(composition_meta.get("first_mention_composition_used")),
        first_mention_composition_layers=composition_meta.get(
            "first_mention_composition_layers",
            default_first_mention_composition_layers,
        ),
    )


def build_first_mention_replacement_logging_payload(
    selected_fallback: VisibilitySelectedFallback,
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
    selected_fallback: VisibilitySelectedFallback,
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


def build_visibility_hard_replacement_context(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ],
    selected_fallback: VisibilitySelectedFallback,
    default_first_mention_composition_layers: Any,
    strict_social_active: bool,
    active_interlocutor: str,
) -> VisibilityHardReplacementContext:
    annotations = build_visibility_replacement_annotations(observation)
    route_metadata_outcome = build_visibility_route_metadata_outcome(
        observation=observation,
        route=route,
        fallback_pool=selected_fallback.fallback_pool,
        fallback_kind=selected_fallback.fallback_kind,
        final_emitted_source=selected_fallback.final_emitted_source,
    )
    replacement_plan = build_visibility_hard_replacement_plan(
        observation=observation,
        route_metadata_outcome=route_metadata_outcome,
        annotations=annotations,
        selected_fallback=selected_fallback,
    )
    first_mention_payload = build_visibility_first_mention_metadata_payload(
        composition_meta=selected_fallback.composition_meta,
        default_first_mention_composition_layers=default_first_mention_composition_layers,
    )
    logging_payload = build_visibility_hard_replacement_logging_payload(
        strict_social_active=strict_social_active,
        observation=observation,
        fallback_pool=selected_fallback.fallback_pool,
        fallback_kind=selected_fallback.fallback_kind,
        active_interlocutor=active_interlocutor,
    )
    return VisibilityHardReplacementContext(
        replacement_plan=replacement_plan,
        first_mention_payload=first_mention_payload,
        logging_payload=logging_payload,
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


def build_visibility_fallback_selection_inputs(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ],
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    emit_integrity_response_type_required: str,
    response_type_required_meta: Any,
) -> VisibilityFallbackSelectionInputs:
    return VisibilityFallbackSelectionInputs(
        route=route,
        strict_social_route=bool(strict_social_active),
        strict_social_suppressed_non_social_turn=bool(strict_social_suppressed_non_social_turn),
        has_active_social_interlocutor=bool(str(active_interlocutor or "").strip()),
        violation_kinds=list(observation.violation_kinds),
        checked_entities=list(observation.checked_entities),
        checked_facts=list(observation.checked_facts),
        emit_integrity_response_type_required=str(
            emit_integrity_response_type_required or response_type_required_meta or ""
        ),
    )


def build_visibility_route_dispatch_context(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ],
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    emit_integrity_response_type_required: str,
    response_type_required_meta: Any,
) -> VisibilityRouteDispatchContext:
    non_replacement_context: VisibilityNonReplacementRouteContext | None = None
    selection_inputs: VisibilityFallbackSelectionInputs | None = None
    if route in {"continuity_lead_exemption", "concrete_interaction_no_hard_replace"}:
        non_replacement_context = build_visibility_non_replacement_route_context(
            observation=observation,
            route=route,
        )
    else:
        selection_inputs = build_visibility_fallback_selection_inputs(
            observation=observation,
            route=route,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            emit_integrity_response_type_required=emit_integrity_response_type_required,
            response_type_required_meta=response_type_required_meta,
        )
    return VisibilityRouteDispatchContext(
        route=route,
        observation=observation,
        non_replacement_context=non_replacement_context,
        selection_inputs=selection_inputs,
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
        meta["visibility_fallback_owner_bucket"] = classify_visibility_fallback_owner_bucket(
            fallback_pool=fallback_pool or "",
            fallback_kind=fallback_kind or "",
            final_emitted_source=final_emitted_source or "",
        )
