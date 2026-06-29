"""Visibility fallback routing helpers. Terminal pipeline calls
:func:`apply_visibility_enforcement` directly. This module must not author fallback prose
or write final output.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
import re
from typing import Any, Dict, List, Literal, Sequence

from game.final_emission_ownership_schema import (
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
)
from game.final_emission_meta import (
    PRODUCER_REPAIR_KIND_FIRST_MENTION_ENFORCEMENT,
    PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_ENFORCEMENT,
    PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION,
    PRODUCER_REPAIR_KIND_VISIBILITY_ENFORCEMENT,
    append_semantic_mutation_write_site,
    stamp_producer_repair_kind,
    stamp_visibility_fallback_owner_bucket_from_fields,
)
from game.exploration import NPC_PURSUIT_CONTACT_SESSION_KEY
from game.final_emission_text_formatting import _normalize_text
from game.interaction_context import inspect as inspect_interaction_context
from game.narration_visibility import (
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
)

from game.final_emission_visibility_metadata import (
    FirstMentionReplacementLoggingPayload,
    FirstMentionSelectedFallbackMetadataPayload,
    ReferentialClarityReplacementLoggingPayload,
    ReferentialClaritySelectedFallbackMetadataPayload,
    VisibilityDefaultMetadataPayload,
    VisibilityFirstMentionDefaultMetadataPayload,
    VisibilityFirstMentionMetadataPayload,
    VisibilityHardReplacementLoggingPayload,
    VisibilityNonReplacementRouteContext,
    VisibilityPreRouteMetadataContext,
    VisibilityRouteMetadataOutcome,
    VisibilityValidationObservation,
    build_first_mention_replacement_logging_payload,
    build_first_mention_selected_fallback_metadata_payload,
    build_referential_clarity_replacement_logging_payload,
    build_referential_clarity_selected_fallback_metadata_payload,
    build_visibility_default_metadata_payload,
    build_visibility_first_mention_default_metadata_payload,
    build_visibility_first_mention_metadata_payload,
    build_visibility_hard_replacement_logging_payload,
    build_visibility_non_replacement_route_context,
    build_visibility_pre_route_metadata_context,
    build_visibility_route_metadata_outcome,
    build_visibility_validation_observation,
    stamp_visibility_fallback_metadata,
)

from game.social import SOCIAL_KINDS

_UNSET = object()

_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile("[\\\"\u201c\u201d'\u2018\u2019]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class VisibilityPreRouteValidationContext:
    candidate_text: str
    validation_result: Mapping[str, Any] | None
    observation: VisibilityValidationObservation


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


def default_first_mention_composition_layers() -> Dict[str, Any]:
    return {"environment": None, "motion": None, "entities": []}


def first_mention_composition_meta(
    *,
    used: bool = False,
    environment: str | None = None,
    motion: str | None = None,
    entities: List[str] | None = None,
) -> Dict[str, Any]:
    layers = default_first_mention_composition_layers()
    if environment:
        layers["environment"] = environment
    if motion:
        layers["motion"] = motion
    if isinstance(entities, list):
        layers["entities"] = [str(entity).strip() for entity in entities if isinstance(entity, str) and str(entity).strip()]
    return {
        "first_mention_composition_used": used,
        "first_mention_composition_layers": layers,
    }


def visibility_selected_fallback_candidate(
    fallback_text: str,
    fallback_pool: str,
    fallback_kind: str,
    final_emitted_source: str,
    fallback_strategy: str,
    fallback_candidate_source: str,
    composition_meta: Mapping[str, Any],
) -> VisibilitySelectedFallback:
    return VisibilitySelectedFallback(
        text=fallback_text,
        fallback_pool=fallback_pool,
        fallback_kind=fallback_kind,
        final_emitted_source=final_emitted_source,
        fallback_strategy=fallback_strategy,
        fallback_candidate_source=fallback_candidate_source,
        composition_meta=composition_meta,
    )


def opening_visibility_mode_safe_fallback_selection(
    gm_output: Mapping[str, Any] | None,
) -> VisibilitySelectedFallback:
    """Opening-mode visibility path: canonical selector with first-mention fail-closed layers."""
    from game.final_emission_opening_fallback import opening_scene_safe_fallback_selection

    return opening_scene_safe_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=first_mention_composition_meta,
    )


def strict_social_visibility_minimal_fallback_candidate(
    resolution: Dict[str, Any],
    *,
    composition_meta: Mapping[str, Any] | None | object = _UNSET,
) -> VisibilitySelectedFallback:
    """Canonical strict-social visibility minimal emergency fallback candidate."""
    from game.social_exchange_fallback_catalog import select_strict_social_emergency_fallback_line

    meta = (
        first_mention_composition_meta()
        if composition_meta is _UNSET
        else composition_meta
    )
    return visibility_selected_fallback_candidate(
        select_strict_social_emergency_fallback_line(resolution=resolution, surface="visibility"),
        "strict_social_visibility_minimal",
        "visibility_minimal_social_fallback",
        "minimal_social_emergency_fallback",
        "standard_safe_fallback",
        "minimal_social_emergency_fallback",
        meta if isinstance(meta, Mapping) else first_mention_composition_meta(),
    )


def social_active_interlocutor_visibility_fallback(
    *,
    world: Dict[str, Any],
    scene_id: str,
    active_interlocutor: str,
    composition_meta: Mapping[str, Any] | None | object = _UNSET,
) -> VisibilitySelectedFallback:
    """Canonical social-interlocutor minimal fallback candidate (visibility + sealed terminal)."""
    from game.social_exchange_fallback_catalog import minimal_social_emergency_fallback_line
    from game.social_exchange_policy import npc_display_name_for_emission

    sid = str(scene_id or "").strip()
    mini_res: Dict[str, Any] = {
        "kind": "question",
        "social": {
            "npc_id": active_interlocutor,
            "npc_name": npc_display_name_for_emission(world, sid, active_interlocutor),
            "social_intent_class": "social_exchange",
        },
    }
    meta = (
        first_mention_composition_meta()
        if composition_meta is _UNSET
        else composition_meta
    )
    return visibility_selected_fallback_candidate(
        minimal_social_emergency_fallback_line(mini_res),
        "social_active_interlocutor_minimal",
        "social_interlocutor_fallback",
        "social_interlocutor_minimal_fallback",
        "standard_safe_fallback",
        "social_interlocutor_minimal_fallback",
        meta if isinstance(meta, Mapping) else first_mention_composition_meta(),
    )


def passive_scene_pressure_visibility_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[VisibilitySelectedFallback]:
    """Canonical passive-scene-pressure fallback candidates."""
    from game.final_emission_passive_scene_pressure import _passive_scene_pressure_fallback_candidates

    return list(
        _passive_scene_pressure_fallback_candidates(
            session=session if isinstance(session, dict) else None,
            scene=scene,
            scene_id=scene_id,
        )
    )


def npc_pursuit_neutral_nonprogress_visibility_fallback(
    *,
    composition_meta: Mapping[str, Any] | None | object = _UNSET,
) -> VisibilitySelectedFallback:
    """Canonical NPC-pursuit neutral nonprogress fallback candidate."""
    from game.diegetic_fallback_narration import npc_pursuit_neutral_nonprogress_fallback_line

    meta = (
        first_mention_composition_meta()
        if composition_meta is _UNSET
        else composition_meta
    )
    return visibility_selected_fallback_candidate(
        npc_pursuit_neutral_nonprogress_fallback_line(),
        "npc_pursuit_fail_closed_neutral",
        "npc_pursuit_neutral_nonprogress",
        "npc_pursuit_neutral_fallback",
        "standard_safe_fallback",
        "npc_pursuit_neutral_fallback",
        meta if isinstance(meta, Mapping) else first_mention_composition_meta(),
    )


def anti_reset_local_continuation_visibility_fallback(
    *,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
    composition_meta: Mapping[str, Any] | None | object = _UNSET,
) -> VisibilitySelectedFallback:
    """Canonical anti-reset local continuation fallback candidate."""
    from game.anti_reset_emission_guard import local_exchange_continuation_fallback_line

    meta = (
        first_mention_composition_meta()
        if composition_meta is _UNSET
        else composition_meta
    )
    return visibility_selected_fallback_candidate(
        local_exchange_continuation_fallback_line(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=scene_id,
            resolution=resolution if isinstance(resolution, dict) else None,
        ),
        "anti_reset_local_continuation",
        "anti_reset_continuation_fallback",
        "anti_reset_local_continuation_fallback",
        "standard_safe_fallback",
        "anti_reset_local_continuation_fallback",
        meta if isinstance(meta, Mapping) else first_mention_composition_meta(),
    )


def scene_emit_integrity_global_visibility_fallback(
    *,
    scene: Dict[str, Any] | None,
    scene_id: str,
    authoritative_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    res_kind: str,
    response_type_required: str,
) -> VisibilitySelectedFallback:
    """Canonical global scene / scene-emit-integrity fallback candidate."""
    from game.final_emission_scene_emit_integrity import _scene_emit_integrity_global_fallback_selection

    return _scene_emit_integrity_global_fallback_selection(
        scene if isinstance(scene, dict) else None,
        str(scene_id or "").strip(),
        authoritative_resolution=authoritative_resolution if isinstance(authoritative_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=res_kind,
        response_type_required=response_type_required,
    )


def select_non_strict_terminal_fallback_for_sealed(
    *,
    gm_output: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_suppressed_non_social_turn: bool,
    res_kind: str,
    response_type_required: str,
    suppress_intro_replace: bool,
    interaction_mode: str,
    opening_visibility_fallback: Callable[[], VisibilitySelectedFallback],
) -> VisibilitySelectedFallback:
    """Select non-strict terminal fallback using sealed branch order and visibility-owned candidates.

    Sealed terminal replace paths consume this helper (Cycle BK3) instead of re-assembling
    overlapping provider graphs locally.
    """
    from game.final_emission_opening_mode import _opening_mode_active_for_turn
    from game.final_emission_sealed_fallback import select_non_strict_replace_path_terminal_sealed_fallback_branch
    from game.interaction_context import inspect as inspect_interaction_context

    sid = str(scene_id or "").strip()
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    mode = str(interaction_mode or (inspected or {}).get("interaction_mode") or "").strip().lower()
    opening_mode_active = _opening_mode_active_for_turn(
        gm_output if isinstance(gm_output, dict) else None,
        resolution if isinstance(resolution, dict) else None,
    )
    has_active_social_interlocutor = bool(
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
    )

    initial_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=opening_mode_active,
        has_active_social_interlocutor=has_active_social_interlocutor,
        passive_candidate_available=False,
        use_neutral_nonprogress=False,
        suppress_intro_replace=False,
    )
    if initial_branch == "opening_scene_safe_fallback":
        return opening_visibility_fallback()
    if initial_branch == "social_active_interlocutor_minimal":
        return social_active_interlocutor_visibility_fallback(
            world=world if isinstance(world, dict) else {},
            scene_id=sid,
            active_interlocutor=active_interlocutor,
            composition_meta=None,
        )

    passive_candidates = passive_scene_pressure_visibility_fallback_candidates(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=sid,
    )
    passive_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=False,
        has_active_social_interlocutor=False,
        passive_candidate_available=bool(passive_candidates),
        use_neutral_nonprogress=False,
        suppress_intro_replace=False,
    )
    if passive_branch == "passive_scene_pressure":
        return passive_candidates[0]

    use_neutral_nonprogress = _should_use_neutral_nonprogress_fallback_instead_of_global_stock(
        session if isinstance(session, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
    )
    final_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=False,
        has_active_social_interlocutor=False,
        passive_candidate_available=False,
        use_neutral_nonprogress=use_neutral_nonprogress,
        suppress_intro_replace=suppress_intro_replace,
    )
    if final_branch == "npc_pursuit_neutral_nonprogress":
        return npc_pursuit_neutral_nonprogress_visibility_fallback(composition_meta=None)
    if final_branch == "anti_reset_local_continuation":
        return anti_reset_local_continuation_visibility_fallback(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=sid,
            resolution=resolution if isinstance(resolution, dict) else None,
            composition_meta=None,
        )
    return scene_emit_integrity_global_visibility_fallback(
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        authoritative_resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=res_kind,
        response_type_required=response_type_required,
    )


@dataclass(frozen=True)
class VisibilityHardReplacementContext:
    replacement_plan: VisibilityHardReplacementPlan
    first_mention_payload: VisibilityFirstMentionMetadataPayload
    logging_payload: VisibilityHardReplacementLoggingPayload


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
    tag_list_gate: Sequence[str],
    dbg_gate: str,
) -> VisibilityEnforcementStageContext:
    pre_route_validation = build_visibility_pre_route_validation_context(
        candidate_text=candidate_text,
        validation_result=validation_result,
    )
    pre_route_metadata = build_visibility_pre_route_metadata_context(
        observation=pre_route_validation.observation,
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


def build_visibility_hard_replacement_context(
    *,
    observation: VisibilityValidationObservation,
    route: Literal[
        "continuity_lead_exemption",
        "concrete_interaction_no_hard_replace",
        "sealed_hard_replace",
    ],
    selected_fallback: VisibilitySelectedFallback,
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


def _should_use_neutral_nonprogress_fallback_instead_of_global_stock(
    session: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> bool:
    """True when parser-built NPC-target pursuit lacks grounded contact (avoid global stock fallback)."""
    if not isinstance(session, dict):
        return False
    ctx = session.get(NPC_PURSUIT_CONTACT_SESSION_KEY)
    if not isinstance(ctx, dict):
        return False
    if str(ctx.get("commitment_source") or "").strip() != "explicit_player_pursuit":
        return False
    if not isinstance(eff_resolution, dict):
        return False
    rk = str(eff_resolution.get("kind") or "").strip().lower()
    if rk not in SOCIAL_KINDS:
        return False
    target = str(ctx.get("target_npc_id") or "").strip()
    if not target:
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    if soc.get("offscene_target"):
        return True
    gs = str(soc.get("grounded_speaker_id") or "").strip()
    if gs and gs == target:
        return False
    if soc.get("target_resolved") is True and str(soc.get("npc_id") or "").strip() == target:
        return False
    return True


def standard_visibility_safe_fallback(
    *,
    gm_output: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    enforce_first_mentions: bool = False,
    enforce_referential_clarity: bool = False,
    prefer_grounded_scene_intro: bool = False,
    emit_integrity_authoritative_resolution: Dict[str, Any] | None = None,
    emit_integrity_res_kind: str = "",
    emit_integrity_response_type_required: str = "",
) -> VisibilitySelectedFallback:
    """Assemble and validate visibility-safe fallback candidates in canonical gate order."""
    from game.final_emission_sealed_fallback import select_visibility_safe_fallback

    return select_visibility_safe_fallback(
        gm_output=gm_output,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=enforce_first_mentions,
        enforce_referential_clarity=enforce_referential_clarity,
        prefer_grounded_scene_intro=prefer_grounded_scene_intro,
        emit_integrity_authoritative_resolution=emit_integrity_authoritative_resolution,
        emit_integrity_res_kind=emit_integrity_res_kind,
        emit_integrity_response_type_required=emit_integrity_response_type_required,
    )


def _standard_visibility_safe_fallback_core(
    *,
    gm_output: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    enforce_first_mentions: bool = False,
    enforce_referential_clarity: bool = False,
    prefer_grounded_scene_intro: bool = False,
    emit_integrity_authoritative_resolution: Dict[str, Any] | None = None,
    emit_integrity_res_kind: str = "",
    emit_integrity_response_type_required: str = "",
    opening_mode_active_for_turn: Callable[[Dict[str, Any] | None, Dict[str, Any] | None], bool],
    augment_scene_with_runtime_visible_leads: Callable[..., Any],
    anti_reset_suppresses_intro_style_fallbacks: Callable[..., bool],
    should_replace_candidate_intro_fallback: Callable[..., bool],
    grounded_scene_intro_fallback_candidates: Callable[..., Sequence[VisibilitySelectedFallback]],
    passive_scene_pressure_due_for_fallback: Callable[..., bool],
) -> VisibilitySelectedFallback:
    """Visibility-safe fallback assembly core; routing deps are resolved by sealed_fallback facade."""
    if opening_mode_active_for_turn(gm_output, eff_resolution):
        return opening_visibility_mode_safe_fallback_selection(gm_output)

    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    validation_scene = augment_scene_with_runtime_visible_leads(
        scene,
        session=session if isinstance(session, dict) else None,
        scene_id=scene_id,
    )
    suppress_intro = anti_reset_suppresses_intro_style_fallbacks(
        session,
        validation_scene if isinstance(validation_scene, dict) else scene,
        world,
        scene_id,
        eff_resolution,
    )
    auth_res = (
        emit_integrity_authoritative_resolution
        if isinstance(emit_integrity_authoritative_resolution, dict)
        else (eff_resolution if isinstance(eff_resolution, dict) else None)
    )
    rk_emit = str(emit_integrity_res_kind or "").strip().lower()
    if not rk_emit and isinstance(eff_resolution, dict):
        rk_emit = str(eff_resolution.get("kind") or "").strip().lower()
    rt_emit = str(emit_integrity_response_type_required or "").strip()
    fallback_candidates: List[VisibilitySelectedFallback] = []

    if strict_social_active and isinstance(eff_resolution, dict):
        fallback_candidates.append(
            strict_social_visibility_minimal_fallback_candidate(eff_resolution)
        )
    else:
        fallback_candidates.extend(
            passive_scene_pressure_visibility_fallback_candidates(
                session=session if isinstance(session, dict) else None,
                scene=scene,
                scene_id=scene_id,
            )
        )
        if prefer_grounded_scene_intro and not suppress_intro:
            fallback_candidates.extend(
                grounded_scene_intro_fallback_candidates(
                    session=session,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene,
                    world=world,
                    active_interlocutor=active_interlocutor,
                )
            )

    sid = str(scene_id or "").strip()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
        and not strict_social_active
    ):
        fallback_candidates.append(
            social_active_interlocutor_visibility_fallback(
                world=world,
                scene_id=sid,
                active_interlocutor=active_interlocutor,
            )
        )

    if _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
        fallback_candidates.append(npc_pursuit_neutral_nonprogress_visibility_fallback())
    elif not strict_social_active and not passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    ):
        if suppress_intro:
            fallback_candidates.append(
                anti_reset_local_continuation_visibility_fallback(
                    session=session if isinstance(session, dict) else None,
                    world=world if isinstance(world, dict) else None,
                    scene_id=scene_id,
                    resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                )
            )
        else:
            fallback_candidates.append(
                scene_emit_integrity_global_visibility_fallback(
                    scene=scene if isinstance(scene, dict) else None,
                    scene_id=sid,
                    authoritative_resolution=auth_res,
                    session=session if isinstance(session, dict) else None,
                    world=world if isinstance(world, dict) else None,
                    res_kind=rk_emit,
                    response_type_required=rt_emit,
                )
            )

    for selected in fallback_candidates:
        fallback_text = selected.text
        final_emitted_source = selected.final_emitted_source
        if not _normalize_text(fallback_text):
            continue
        if suppress_intro and should_replace_candidate_intro_fallback(
            fallback_text,
            scene_envelope=validation_scene if isinstance(validation_scene, dict) else scene,
            emitter_source=final_emitted_source,
            suppress_intro=True,
        ):
            continue
        validation = validate_player_facing_visibility(
            fallback_text,
            session=session if isinstance(session, dict) else None,
            scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            if enforce_first_mentions:
                first_mention_validation = validate_player_facing_first_mentions(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if first_mention_validation.get("ok") is not True:
                    continue
            if enforce_referential_clarity:
                referential_clarity_validation = validate_player_facing_referential_clarity(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if referential_clarity_validation.get("ok") is not True:
                    continue
            return selected

    if strict_social_active and isinstance(eff_resolution, dict):
        return strict_social_visibility_minimal_fallback_candidate(eff_resolution)

    passive_candidates = passive_scene_pressure_visibility_fallback_candidates(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    )
    if passive_candidates:
        return passive_candidates[0]

    if suppress_intro:
        return anti_reset_local_continuation_visibility_fallback(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=scene_id,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        )
    return scene_emit_integrity_global_visibility_fallback(
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        authoritative_resolution=auth_res,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=rk_emit,
        response_type_required=rt_emit,
    )


def apply_visibility_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
    emit_integrity_authoritative_resolution: Dict[str, Any] | None = None,
    emit_integrity_res_kind: str = "",
    emit_integrity_response_type_required: str = "",
    first_mention_enforcement_applier: Callable[..., Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Visibility enforcement orchestration owner; first-mention follow-up defaults in-module."""
    if first_mention_enforcement_applier is None:
        first_mention_enforcement_applier = apply_first_mention_enforcement
    from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
    from game.final_emission_meta import ensure_final_emission_meta_dict
    from game.final_emission_referential_clarity import (
        _apply_default_referential_clarity_meta,
        _referential_clarity_repair_meta_snapshot,
        _restore_referential_clarity_repair_meta,
    )
    from game.final_emission_sealed_fallback import prepare_sealed_replacement_route_meta
    from game.social_exchange_projection import (
        log_final_emission_decision,
        log_final_emission_trace,
    )

    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_visibility(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = ensure_final_emission_meta_dict(out)
    tag_list_gate = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    dbg_gate = str(out.get("debug_notes") or "")
    visibility_stage_context = build_visibility_enforcement_stage_context(
        candidate_text=candidate_text,
        validation_result=validation,
        tag_list_gate=tag_list_gate,
        dbg_gate=dbg_gate,
    )
    candidate_text = visibility_stage_context.pre_route_validation.candidate_text
    visibility_observation = visibility_stage_context.pre_route_validation.observation
    visibility_pre_route_metadata_context = visibility_stage_context.pre_route_metadata
    for key, value in visibility_pre_route_metadata_context.first_mention_defaults.meta_updates().items():
        meta[key] = value
    preserved_repair_meta = _referential_clarity_repair_meta_snapshot(meta)
    from game.final_emission_passive_scene_pressure import (
        passive_scene_concrete_beat_satisfier_meta_snapshot,
        passive_scene_concrete_beat_satisfier_preserves_upstream,
        restore_passive_scene_concrete_beat_satisfier_meta,
    )

    preserved_satisfier_meta = passive_scene_concrete_beat_satisfier_meta_snapshot(meta)
    _apply_default_referential_clarity_meta(meta, passed=None)
    _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)
    restore_passive_scene_concrete_beat_satisfier_meta(meta, preserved_satisfier_meta)
    stamp_visibility_fallback_metadata(
        meta,
        **visibility_pre_route_metadata_context.visibility_defaults.stamp_kwargs(),
    )

    first_mention_kwargs = {
        "session": session,
        "scene": scene,
        "world": world,
        "scene_id": scene_id,
        "eff_resolution": eff_resolution,
        "active_interlocutor": active_interlocutor,
        "strict_social_active": strict_social_active,
        "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
        "grounded_speaker_first_mention_exemption_entity_id": grounded_speaker_first_mention_exemption_entity_id,
        "emit_integrity_authoritative_resolution": emit_integrity_authoritative_resolution,
        "emit_integrity_res_kind": emit_integrity_res_kind,
        "emit_integrity_response_type_required": emit_integrity_response_type_required,
    }

    if visibility_observation.validation_passed:
        return first_mention_enforcement_applier(out, **first_mention_kwargs)

    visibility_route_decision_inputs = visibility_stage_context.route_decision_inputs
    route = route_visibility_enforcement_after_failed_validation(
        tag_list_gate=visibility_route_decision_inputs.tag_list_gate,
        dbg_gate=visibility_route_decision_inputs.dbg_gate,
        violation_kinds=visibility_route_decision_inputs.violation_kinds,
        checked_entities=visibility_route_decision_inputs.checked_entities,
        checked_facts=visibility_route_decision_inputs.checked_facts,
        candidate_text=visibility_route_decision_inputs.candidate_text,
    )
    visibility_route_dispatch_context = build_visibility_route_dispatch_context(
        observation=visibility_observation,
        route=route,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        emit_integrity_response_type_required=emit_integrity_response_type_required,
        response_type_required_meta=meta.get("response_type_required"),
    )
    if visibility_route_dispatch_context.route == "continuity_lead_exemption":
        non_replacement_context = visibility_route_dispatch_context.non_replacement_context
        assert non_replacement_context is not None
        stamp_visibility_fallback_metadata(
            meta,
            **non_replacement_context.route_metadata_outcome.stamp_kwargs(),
        )
        return first_mention_enforcement_applier(out, **first_mention_kwargs)

    if visibility_route_dispatch_context.route == "concrete_interaction_no_hard_replace":
        non_replacement_context = visibility_route_dispatch_context.non_replacement_context
        assert non_replacement_context is not None
        stamp_visibility_fallback_metadata(
            meta,
            **non_replacement_context.route_metadata_outcome.stamp_kwargs(),
        )
        return out

    visibility_selection_inputs = visibility_route_dispatch_context.selection_inputs
    assert visibility_selection_inputs is not None
    if passive_scene_concrete_beat_satisfier_preserves_upstream(meta, candidate_text):
        stamp_visibility_fallback_metadata(
            meta,
            validation_passed=None,
            replacement_applied=False,
            violation_kinds=list(visibility_observation.violation_kinds),
            violation_sample=list(visibility_observation.violation_sample),
            checked_entities=list(visibility_observation.checked_entities),
            checked_facts=list(visibility_observation.checked_facts),
        )
        _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)
        restore_passive_scene_concrete_beat_satisfier_meta(meta, preserved_satisfier_meta)
        return first_mention_enforcement_applier(out, **first_mention_kwargs)

    visibility_selected_fallback = standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=visibility_selection_inputs.strict_social_route,
        strict_social_suppressed_non_social_turn=visibility_selection_inputs.strict_social_suppressed_non_social_turn,
        emit_integrity_authoritative_resolution=emit_integrity_authoritative_resolution,
        emit_integrity_res_kind=emit_integrity_res_kind,
        emit_integrity_response_type_required=visibility_selection_inputs.emit_integrity_response_type_required,
    )
    assert_final_emission_mutation_allowed(
        "hard_replace_illegal_output_with_sealed_fallback",
        source="gate._apply_visibility_enforcement",
    )
    visibility_hard_replacement_context = build_visibility_hard_replacement_context(
        observation=visibility_observation,
        route=route,
        selected_fallback=visibility_selected_fallback,
        strict_social_active=strict_social_active,
        active_interlocutor=active_interlocutor,
    )
    visibility_hard_replacement_plan = visibility_hard_replacement_context.replacement_plan
    out["player_facing_text"] = visibility_hard_replacement_plan.fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)] + visibility_hard_replacement_plan.annotations.tags_to_add
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + visibility_hard_replacement_plan.annotations.debug_notes_to_add

    prepare_sealed_replacement_route_meta(
        meta,
        gm_output=out,
        pre_gate_candidate_text=candidate_text,
        final_emitted_source=visibility_hard_replacement_plan.final_emitted_source,
        strict_social_route=strict_social_active,
        composition_meta=None,
    )
    stamp_visibility_fallback_metadata(meta, **visibility_hard_replacement_plan.route_metadata_outcome.stamp_kwargs())
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_VISIBILITY_ENFORCEMENT)
    stamp_visibility_fallback_owner_bucket_from_fields(
        meta,
        fallback_pool=visibility_hard_replacement_plan.route_metadata_outcome.stamp_kwargs().get("fallback_pool"),
        fallback_kind=visibility_hard_replacement_plan.route_metadata_outcome.stamp_kwargs().get("fallback_kind"),
        final_emitted_source=visibility_hard_replacement_plan.final_emitted_source,
    )
    first_mention_metadata_payload = visibility_hard_replacement_context.first_mention_payload
    for key, value in first_mention_metadata_payload.meta_updates().items():
        meta[key] = value

    visibility_logging_payload = visibility_hard_replacement_context.logging_payload
    log_final_emission_decision(visibility_logging_payload.decision_payload())
    log_final_emission_trace(visibility_logging_payload.trace_payload(meta))
    return out


def apply_first_mention_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
    emit_integrity_authoritative_resolution: Dict[str, Any] | None = None,
    emit_integrity_res_kind: str = "",
    emit_integrity_response_type_required: str = "",
    referential_clarity_enforcement_applier: Callable[..., Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """First-mention enforcement orchestration owner; referential-clarity follow-up defaults in-module."""
    if referential_clarity_enforcement_applier is None:
        referential_clarity_enforcement_applier = apply_referential_clarity_enforcement
    from game.anti_reset_emission_guard import (
        _opening_scene_preference_active,
        anti_reset_suppresses_intro_style_fallbacks,
    )
    from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
    from game.final_emission_referential_clarity import (
        _apply_default_referential_clarity_meta,
        _referential_clarity_repair_meta_snapshot,
        _restore_referential_clarity_repair_meta,
    )
    from game.final_emission_sealed_fallback import prepare_sealed_replacement_route_meta
    from game.social_exchange_projection import (
        log_final_emission_decision,
        log_final_emission_trace,
    )

    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_first_mentions(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    leading_pronoun_detected = bool(validation.get("leading_pronoun_detected"))
    first_explicit_entity_offset = validation.get("first_explicit_entity_offset")
    if not isinstance(first_explicit_entity_offset, int):
        first_explicit_entity_offset = None

    meta["first_mention_validation_passed"] = validation.get("ok") is True
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = violation_kinds
    meta["first_mention_checked_entities"] = checked_entities
    meta["first_mention_leading_pronoun_detected"] = leading_pronoun_detected
    meta["first_mention_first_explicit_entity_offset"] = first_explicit_entity_offset
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = default_first_mention_composition_layers()
    meta["first_mention_strict_social_grounded_speaker_exemption_entity_id"] = (
        grounded_speaker_first_mention_exemption_entity_id
    )
    preserved_repair_meta = _referential_clarity_repair_meta_snapshot(meta)
    _apply_default_referential_clarity_meta(meta, passed=None)
    _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)

    referential_clarity_kwargs = {
        "session": session,
        "scene": scene,
        "world": world,
        "scene_id": scene_id,
        "eff_resolution": eff_resolution,
        "active_interlocutor": active_interlocutor,
        "strict_social_active": strict_social_active,
        "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
        "grounded_speaker_first_mention_exemption_entity_id": grounded_speaker_first_mention_exemption_entity_id,
        "emit_integrity_authoritative_resolution": emit_integrity_authoritative_resolution,
        "emit_integrity_res_kind": emit_integrity_res_kind,
        "emit_integrity_response_type_required": emit_integrity_response_type_required,
    }

    if validation.get("ok") is True:
        return referential_clarity_enforcement_applier(out, **referential_clarity_kwargs)

    from game.final_emission_passive_scene_pressure import (
        passive_scene_concrete_beat_satisfier_preserves_upstream,
    )

    if passive_scene_concrete_beat_satisfier_preserves_upstream(meta, candidate_text):
        meta["first_mention_validation_passed"] = None
        return referential_clarity_enforcement_applier(out, **referential_clarity_kwargs)

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        meta["first_mention_validation_passed"] = None
        return out

    opening_scene_preference_used = _opening_scene_preference_active(session)
    suppress_intro = anti_reset_suppresses_intro_style_fallbacks(
        session,
        scene,
        world,
        scene_id,
        eff_resolution,
    )
    prefer_grounded_scene_intro = not suppress_intro

    first_mention_selected_fallback = standard_visibility_safe_fallback(
        gm_output=out,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
        prefer_grounded_scene_intro=prefer_grounded_scene_intro,
        emit_integrity_authoritative_resolution=emit_integrity_authoritative_resolution,
        emit_integrity_res_kind=emit_integrity_res_kind,
        emit_integrity_response_type_required=str(
            emit_integrity_response_type_required or meta.get("response_type_required") or ""
        ),
    )
    assert_final_emission_mutation_allowed(
        "hard_replace_illegal_output_with_sealed_fallback",
        source="gate._apply_first_mention_enforcement",
    )
    out["player_facing_text"] = first_mention_selected_fallback.text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "first_mention_enforcement_replaced"]
        + [f"first_mention_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:first_mention_replaced:"
        + ",".join(violation_kinds[:8])
    )

    prepare_sealed_replacement_route_meta(
        meta,
        gm_output=out,
        pre_gate_candidate_text=candidate_text,
        final_emitted_source=first_mention_selected_fallback.final_emitted_source,
        strict_social_route=strict_social_active,
        composition_meta=first_mention_selected_fallback.composition_meta,
    )
    first_mention_selected_fallback_metadata_payload = build_first_mention_selected_fallback_metadata_payload(
        first_mention_selected_fallback,
        opening_scene_first_mention_preference_used=opening_scene_preference_used,
    )
    for key, value in first_mention_selected_fallback_metadata_payload.meta_updates().items():
        meta[key] = value
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_FIRST_MENTION_ENFORCEMENT)
    stamp_visibility_fallback_owner_bucket_from_fields(
        meta,
        fallback_pool=first_mention_selected_fallback.fallback_pool,
        fallback_kind=first_mention_selected_fallback.fallback_kind,
        final_emitted_source=first_mention_selected_fallback.final_emitted_source,
    )

    first_mention_replacement_logging_payload = build_first_mention_replacement_logging_payload(
        first_mention_selected_fallback,
        strict_social_active=strict_social_active,
        violation_kinds=violation_kinds,
        active_interlocutor=active_interlocutor,
    )
    log_final_emission_decision(
        first_mention_replacement_logging_payload.decision_payload()
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_first_mention_replace"})
    return referential_clarity_enforcement_applier(out, **referential_clarity_kwargs)


def apply_referential_clarity_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
    emit_integrity_authoritative_resolution: Dict[str, Any] | None = None,
    emit_integrity_res_kind: str = "",
    emit_integrity_response_type_required: str = "",
) -> Dict[str, Any]:
    """Referential-clarity enforcement orchestration owner."""
    from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
    from game.final_emission_meta import ensure_final_emission_meta_dict
    from game.final_emission_referential_clarity import (
        _apply_referential_clarity_local_repair_success_meta,
        _build_referential_clarity_violation_sample,
        _referential_clarity_repair_meta_snapshot,
        _referential_clarity_violations_have_multi_entity_candidates,
        _referential_clarity_violations_only_dialogue_attribution_they,
        _restore_referential_clarity_repair_meta,
        _try_non_strict_local_pronoun_substitution_repair,
        _try_strict_social_local_pronoun_substitution_repair,
    )
    from game.final_emission_sealed_fallback import prepare_sealed_replacement_route_meta
    from game.social_exchange_projection import (
        log_final_emission_decision,
        log_final_emission_trace,
    )

    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_referential_clarity(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = ensure_final_emission_meta_dict(out)
    preserved_repair_meta = _referential_clarity_repair_meta_snapshot(meta)
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    meta["referential_clarity_validation_passed"] = validation.get("ok") is True
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = violation_kinds
    meta["referential_clarity_checked_entities"] = checked_entities
    meta["referential_clarity_violation_sample"] = _build_referential_clarity_violation_sample(violations)
    meta["referential_clarity_local_substitution_attempted"] = False
    meta["referential_clarity_local_substitution_applied"] = False
    meta["referential_clarity_local_substitution_token"] = None
    meta["referential_clarity_local_substitution_replacement"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False

    if validation.get("ok") is True:
        _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)
        meta["referential_clarity_validation_passed"] = True
        meta["referential_clarity_violation_kinds"] = []
        meta["referential_clarity_violation_sample"] = []
        return out

    from game.final_emission_passive_scene_pressure import (
        passive_scene_concrete_beat_satisfier_preserves_upstream,
    )

    if passive_scene_concrete_beat_satisfier_preserves_upstream(meta, candidate_text):
        _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)
        meta["referential_clarity_validation_passed"] = None
        meta["referential_clarity_replacement_applied"] = False
        meta["referential_clarity_fallback_avoided"] = True
        return out

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        if not violations:
            meta["referential_clarity_validation_passed"] = None
            return out
        if not _referential_clarity_violations_have_multi_entity_candidates(violations) and (
            _referential_clarity_violations_only_dialogue_attribution_they(violations)
        ):
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            return out

    response_type_req = str(meta.get("response_type_required") or "").strip().lower()
    if (
        strict_social_active
        and response_type_req == "dialogue"
        and not strict_social_suppressed_non_social_turn
    ):
        repaired, subst_dbg = _try_strict_social_local_pronoun_substitution_repair(
            candidate_text,
            violations=[v for v in violations if isinstance(v, dict)],
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )
        for k, val in subst_dbg.items():
            meta[k] = val
        if repaired is not None:
            out["player_facing_text"] = repaired
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            tags = out.get("tags") if isinstance(out.get("tags"), list) else []
            out["tags"] = _dedupe_preserve_order(
                [str(t) for t in tags if isinstance(t, str)] + ["referential_clarity_local_substitution"]
            )
            gate_out_text = _normalize_text(out.get("player_facing_text"))
            meta["post_gate_mutation_detected"] = bool(meta.get("post_gate_mutation_detected")) or (
                candidate_text != gate_out_text
            )
            meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
            stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION)
            stamp_visibility_fallback_owner_bucket_from_fields(meta)
            append_semantic_mutation_write_site(
                meta,
                before_text=candidate_text,
                after_text=repaired,
                write_site_family="repair",
                write_site_file="game/final_emission_visibility_fallback.py",
                write_site_function="apply_referential_clarity_enforcement",
                owner="game.final_emission_visibility_fallback",
                source="referential_clarity_local_substitution",
                mutation_reason="strict_social_referential_clarity_local_substitution",
                compatibility_status="diagnostic_only",
                repair_family="referential_clarity_local_substitution",
            )
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate_referential_clarity",
                    "social_route": strict_social_active,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": "referential_clarity_local_substitution",
                    "fallback_kind": "none",
                    "active_interlocutor": active_interlocutor or None,
                }
            )
            log_final_emission_trace(
                {**meta, "stage": "final_emission_gate_referential_clarity_local_substitution"}
            )
            return out

    if not strict_social_active:
        repaired, subst_dbg = _try_non_strict_local_pronoun_substitution_repair(
            candidate_text,
            violations=[v for v in violations if isinstance(v, dict)],
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
            strict_social_active=False,
        )
        for k, val in subst_dbg.items():
            meta[k] = val
        if repaired is not None:
            _apply_referential_clarity_local_repair_success_meta(
                out,
                meta,
                candidate_text=candidate_text,
                repaired=repaired,
                subst_dbg=subst_dbg,
            )
            stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION)
            stamp_visibility_fallback_owner_bucket_from_fields(meta)
            append_semantic_mutation_write_site(
                meta,
                before_text=candidate_text,
                after_text=repaired,
                write_site_family="repair",
                write_site_file="game/final_emission_visibility_fallback.py",
                write_site_function="apply_referential_clarity_enforcement",
                owner="game.final_emission_visibility_fallback",
                source="referential_clarity_local_substitution",
                mutation_reason="referential_clarity_local_substitution",
                compatibility_status="diagnostic_only",
                repair_family="referential_clarity_local_substitution",
            )
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate_referential_clarity",
                    "social_route": strict_social_active,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": "referential_clarity_local_substitution",
                    "fallback_kind": "none",
                    "active_interlocutor": active_interlocutor or None,
                }
            )
            log_final_emission_trace(
                {**meta, "stage": "final_emission_gate_referential_clarity_local_substitution"}
            )
            return out

    referential_clarity_selected_fallback = standard_visibility_safe_fallback(
        gm_output=out,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
        emit_integrity_authoritative_resolution=emit_integrity_authoritative_resolution,
        emit_integrity_res_kind=emit_integrity_res_kind,
        emit_integrity_response_type_required=str(
            emit_integrity_response_type_required or meta.get("response_type_required") or ""
        ),
    )
    assert_final_emission_mutation_allowed(
        "hard_replace_illegal_output_with_sealed_fallback",
        source="gate._apply_referential_clarity_enforcement",
    )
    out["player_facing_text"] = referential_clarity_selected_fallback.text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "referential_clarity_enforcement_replaced"]
        + [f"referential_clarity_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:referential_clarity_replaced:"
        + ",".join(violation_kinds[:8])
    )

    prepare_sealed_replacement_route_meta(
        meta,
        gm_output=out,
        pre_gate_candidate_text=candidate_text,
        final_emitted_source=referential_clarity_selected_fallback.final_emitted_source,
        strict_social_route=strict_social_active,
        composition_meta=referential_clarity_selected_fallback.composition_meta,
    )
    referential_clarity_selected_fallback_metadata_payload = build_referential_clarity_selected_fallback_metadata_payload(
        referential_clarity_selected_fallback,
    )
    for key, value in referential_clarity_selected_fallback_metadata_payload.meta_updates().items():
        meta[key] = value
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_ENFORCEMENT)
    stamp_visibility_fallback_owner_bucket_from_fields(
        meta,
        fallback_pool=referential_clarity_selected_fallback.fallback_pool,
        fallback_kind=referential_clarity_selected_fallback.fallback_kind,
        final_emitted_source=referential_clarity_selected_fallback.final_emitted_source,
    )

    referential_clarity_replacement_logging_payload = build_referential_clarity_replacement_logging_payload(
        referential_clarity_selected_fallback,
        strict_social_active=strict_social_active,
        violation_kinds=violation_kinds,
        active_interlocutor=active_interlocutor,
        referential_clarity_fallback_after_failed_local_repair=bool(
            meta.get("referential_clarity_fallback_after_failed_local_repair")
        ),
    )
    log_final_emission_decision(
        referential_clarity_replacement_logging_payload.decision_payload()
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_referential_clarity_replace"})
    return out

