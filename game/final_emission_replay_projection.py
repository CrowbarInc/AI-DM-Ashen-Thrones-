"""Read-side FEM replay/runtime-lineage projection helpers. This module must not select fallbacks, mutate output, or stamp write-time FEM."""
from __future__ import annotations

from typing import Any, Mapping

from game.runtime_lineage_telemetry import (
    RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED,
    RUNTIME_LINEAGE_EVENT_GATE_OUTCOME,
    RUNTIME_LINEAGE_EVENT_MUTATION,
    RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR,
    make_runtime_lineage_event,
)
from game.telemetry_vocab import normalize_reason_list

FINAL_EMISSION_MUTATION_LINEAGE_KEY: str = "final_emission_mutation_lineage"


def _opening_fallback_owner_bucket_from_meta(meta: Mapping[str, Any] | None) -> str:
    from game.final_emission_meta import opening_fallback_owner_bucket_from_meta

    return opening_fallback_owner_bucket_from_meta(meta)


def _fem_lineage_source(fem: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = fem.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _fem_selected_fallback_projection(fem: Mapping[str, Any]) -> tuple[str, str, str, str, str | None] | None:
    """Return ``(fallback_kind, gate_path, stage, owner, source)`` only for proven selection."""
    final_route = str(fem.get("final_route") or "").strip().lower()
    final_source = _fem_lineage_source(fem, "final_emitted_source")
    source_token = str(final_source or "").strip().lower()
    repair_kind = str(fem.get("response_type_repair_kind") or "").strip().lower()

    # Sanitizer fallback projection keeps sanitizer stage/owner even when surfaced through final-emission telemetry.
    if fem.get("sanitizer_strict_social_fallback_used") is True:
        return (
            "sanitizer_strict_social",
            "sanitizer_fallback",
            "sanitizer",
            "game.output_sanitizer",
            _fem_lineage_source(fem, "sanitizer_strict_social_source"),
        )
    if fem.get("sanitizer_empty_fallback_used") is True or fem.get("sanitizer_lineage_empty_fallback_used") is True:
        return (
            "sanitizer_empty_output",
            "sanitizer_fallback",
            "sanitizer",
            "game.output_sanitizer",
            _fem_lineage_source(fem, "sanitizer_empty_fallback_source"),
        )

    # Opening projection separates gate selection ownership from upstream-prepared prose authorship.
    if (
        fem.get("opening_fallback_failed_closed") is True
        or repair_kind == "opening_deterministic_fallback_failed_closed"
        or "opening_fallback_failed_closed" in source_token
    ):
        return (
            "opening_failed_closed",
            "opening_failed_closed",
            "gate",
            "game.final_emission_gate",
            final_source,
        )
    if fem.get("opening_recovered_via_fallback") is True or source_token == "opening_deterministic_fallback":
        return ("scene_opening", "opening_fallback", "gate", "game.final_emission_gate", final_source)

    # Projection only: infer fallback selection from finalized FEM evidence, never from prepared payload availability alone.
    if fem.get("upstream_prepared_emission_used") is True and repair_kind in {
        "answer_upstream_prepared_repair",
        "action_outcome_upstream_prepared_repair",
    }:
        return (
            "response_type_prepared_emission",
            "prepared_repair",
            "gate",
            "game.final_emission_gate",
            final_source,
        )

    if source_token == "minimal_social_emergency_fallback":
        return (
            "minimal_social_emergency_fallback",
            "strict_social_emergency",
            "gate",
            "game.final_emission_gate",
            final_source,
        )
    if (
        source_token
        in {
            "deterministic_social_fallback",
            "social_emission_integrity_fallback",
            "strict_social_deterministic_fallback",
            "strict_social_replacement",
        }
        or (fem.get("response_type_repair_used") is True and repair_kind == "strict_social_dialogue_repair")
    ):
        return ("strict_social_fallback", "strict_social_fallback", "gate", "game.final_emission_gate", final_source)

    if (
        fem.get("visibility_replacement_applied") is True
        or fem.get("first_mention_replacement_applied") is True
        or fem.get("referential_clarity_replacement_applied") is True
    ):
        return (
            "visibility_or_scene_replacement",
            "visibility_or_scene_replaced",
            "gate",
            "game.final_emission_gate",
            final_source,
        )

    provenance = fem.get("fallback_provenance_trace")
    if isinstance(provenance, Mapping) and str(provenance.get("source") or "").strip().lower() == "fallback":
        return ("upstream_fast_fallback", "unknown", "retry", "game.api", "fallback_provenance_trace")

    if final_route == "replaced":
        return (
            "sealed_or_global_replacement",
            "replaced_or_sealed",
            "gate",
            "game.final_emission_gate",
            final_source,
        )
    return None


def _append_fem_lineage_event(events: list[dict[str, Any]], event: dict[str, Any]) -> None:
    recurrence_key = event.get("recurrence_key")
    if any(existing.get("recurrence_key") == recurrence_key for existing in events):
        return
    events.append(event)


def _fem_speaker_repair_projections(fem: Mapping[str, Any]) -> list[tuple[str, str, str | None, list[str]]]:
    """Return explicit ``(repair_kind, owner, source, notes)`` speaker repair evidence."""
    projections: list[tuple[str, str, str | None, list[str]]] = []
    reason = str(fem.get("speaker_contract_enforcement_reason") or "").strip().lower()
    reason_to_kind = {
        "continuity_locked_speaker_repair": "local_rebind",
        "canonical_speaker_rewrite": "canonical_rewrite",
        "narrator_neutral_no_allowed_speaker": "narrator_neutral",
    }
    repair_kind = reason_to_kind.get(reason)
    if repair_kind:
        projections.append((repair_kind, "game.speaker_contract_enforcement", reason, [reason]))

    continuity = fem.get("interaction_continuity_repair")
    if isinstance(continuity, Mapping) and continuity.get("applied") is True:
        raw_type = str(continuity.get("repair_type") or "").strip().lower()
        continuity_kind = {
            "repair_malformed_speaker_attribution": "continuity_malformed_attribution",
            "strip_uncued_interruption": "continuity_strip_uncued_interruption",
            "insert_explicit_bridge": "continuity_insert_bridge",
            "narration_to_dialogue": "continuity_wrap_dialogue",
        }.get(raw_type, "unknown_speaker_repair")
        projections.append(
            (
                continuity_kind,
                "game.interaction_continuity",
                raw_type or "interaction_continuity_repair",
                normalize_reason_list(continuity.get("violations"))[:8],
            )
        )
    return projections


def _fem_mutation_lineage_tokens(fem: Mapping[str, Any]) -> list[str]:
    raw = fem.get(FINAL_EMISSION_MUTATION_LINEAGE_KEY)
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw[:16]:
        if not isinstance(item, str):
            continue
        token = item.strip().lower()
        if token and token not in out:
            out.append(token)
    return out


def _append_fem_mutation_event(
    events: list[dict[str, Any]],
    *,
    mutation_kind: str,
    stage: str = "gate",
    owner: str = "game.final_emission_gate",
    source: str | None = None,
    notes: Any = None,
) -> None:
    _append_fem_lineage_event(
        events,
        make_runtime_lineage_event(
            event_kind=RUNTIME_LINEAGE_EVENT_MUTATION,
            stage=stage,
            owner=owner,
            source=source,
            mutation_kind=mutation_kind,
            notes=notes,
        ),
    )


def _append_fem_mutation_projections(
    events: list[dict[str, Any]],
    fem: Mapping[str, Any],
    *,
    fallback: tuple[str, str, str, str, str | None] | None,
    speaker_projections: list[tuple[str, str, str | None, list[str]]],
) -> None:
    """Append bounded mutation projections for explicit finalized evidence only."""
    if fallback is not None:
        fallback_kind, _gate_path, stage, owner, source = fallback
        _append_fem_mutation_event(
            events,
            mutation_kind="fallback_mutation",
            stage=stage,
            owner=owner,
            source=source,
            notes=[fallback_kind],
        )

    for repair_kind, owner, source, notes in speaker_projections:
        mutation_kind = "continuity_repair_mutation" if owner == "game.interaction_continuity" else "speaker_repair_mutation"
        _append_fem_mutation_event(
            events,
            mutation_kind=mutation_kind,
            owner=owner,
            source=source,
            notes=[repair_kind, *notes],
        )

    if fem.get("response_type_repair_used") is True:
        _append_fem_mutation_event(
            events,
            mutation_kind="response_type_repair_mutation",
            source=_fem_lineage_source(fem, "response_type_repair_kind", "final_emitted_source"),
            notes=[fem.get("response_type_repair_kind")] if isinstance(fem.get("response_type_repair_kind"), str) else [],
        )

    sanitizer_changed = fem.get("sanitizer_lineage_changed_count")
    has_sanitizer_mutation = (
        isinstance(sanitizer_changed, (int, float))
        and not isinstance(sanitizer_changed, bool)
        and sanitizer_changed > 0
    ) or fem.get("sanitizer_empty_fallback_used") is True or fem.get("sanitizer_strict_social_fallback_used") is True
    if has_sanitizer_mutation:
        _append_fem_mutation_event(
            events,
            mutation_kind="sanitizer_mutation",
            stage="sanitizer",
            owner="game.output_sanitizer",
            source=_fem_lineage_source(fem, "sanitizer_empty_fallback_source", "sanitizer_strict_social_source"),
        )

    if fem.get("output_sanitization_applied") is True or fem.get("finalize_route_illegal_strip_applied") is True:
        _append_fem_mutation_event(
            events,
            mutation_kind="final_emission_mutation",
            source=(
                "finalize_route_illegal_strip"
                if fem.get("finalize_route_illegal_strip_applied") is True
                else "finalize_html_strip"
            ),
        )

    repair_flag_keys = (
        "answer_completeness_repaired",
        "response_delta_repaired",
        "social_response_structure_repair_applied",
        "narrative_authenticity_repaired",
        "tone_escalation_repaired",
        "anti_railroading_repaired",
        "context_separation_repaired",
        "player_facing_narration_purity_repaired",
        "answer_shape_primacy_repaired",
        "fallback_behavior_repaired",
        "narrative_authority_repaired",
    )
    active_repair_flags = [key for key in repair_flag_keys if fem.get(key) is True]
    if active_repair_flags:
        _append_fem_mutation_event(
            events,
            mutation_kind="repair_only_mutation",
            source=active_repair_flags[0],
            notes=active_repair_flags,
        )

    tokens = _fem_mutation_lineage_tokens(fem)
    token_kind_map = {
        "response_type_repair": ("response_type_repair_mutation", "gate", "game.final_emission_gate"),
        "prepared_emission_selection": ("fallback_mutation", "gate", "game.final_emission_gate"),
        "opening_fallback_selection": ("fallback_mutation", "gate", "game.final_emission_gate"),
        "sealed_fallback_replacement": ("fallback_mutation", "gate", "game.final_emission_gate"),
        "sanitizer_empty_fallback": ("fallback_mutation", "sanitizer", "game.output_sanitizer"),
        "fallback_behavior_repair": ("repair_only_mutation", "gate", "game.final_emission_gate"),
        "finalize_html_strip": ("final_emission_mutation", "gate", "game.final_emission_gate"),
        "finalize_route_illegal_strip": ("final_emission_mutation", "gate", "game.final_emission_gate"),
    }
    for token in tokens:
        classification = token_kind_map.get(token)
        if classification is None:
            continue
        kind, stage, owner = classification
        _append_fem_mutation_event(
            events,
            mutation_kind=kind,
            stage=stage,
            owner=owner,
            source=token,
            notes=[token],
        )

    if fem.get("post_gate_mutation_detected") is True and not any(
        event.get("event_kind") == RUNTIME_LINEAGE_EVENT_MUTATION for event in events
    ):
        _append_fem_mutation_event(
            events,
            mutation_kind="final_emission_mutation",
            source="post_gate_mutation_detected",
            notes=["post_gate_mutation_detected"],
        )


def build_fem_runtime_lineage_events(fem: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Project finalized FEM lineage evidence into H1 runtime lineage events.

    Read-side only: prepared payload presence alone is not selection evidence, and no
    output/gate/evaluator behavior is consulted or changed here.
    """
    if not isinstance(fem, Mapping):
        return []

    events: list[dict[str, Any]] = []
    fallback = _fem_selected_fallback_projection(fem)
    if fallback is not None:
        fallback_kind, gate_path, stage, owner, source = fallback
        fallback_authorship_source: str | None = None
        fallback_owner_bucket: str | None = None
        if fallback_kind == "scene_opening":
            fallback_authorship_source = _fem_lineage_source(fem, "opening_fallback_authorship_source")
            fallback_owner_bucket = _opening_fallback_owner_bucket_from_meta(fem)
        elif fallback_kind == "opening_failed_closed":
            fallback_owner_bucket = _opening_fallback_owner_bucket_from_meta(fem)
        _append_fem_lineage_event(
            events,
            make_runtime_lineage_event(
                event_kind=RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED,
                stage=stage,
                owner=owner,
                source=source,
                fallback_kind=fallback_kind,
                fallback_authorship_source=fallback_authorship_source,
                fallback_owner_bucket=fallback_owner_bucket,
            ),
        )
        if gate_path != "unknown":
            _append_fem_lineage_event(
                events,
                make_runtime_lineage_event(
                    event_kind=RUNTIME_LINEAGE_EVENT_GATE_OUTCOME,
                    stage=stage,
                    owner=owner,
                    source=source,
                    gate_path=gate_path,
                ),
            )

    final_route = str(fem.get("final_route") or "").strip().lower()
    final_source = _fem_lineage_source(fem, "final_emitted_source")
    gate_path: str | None = None
    if fem.get("referential_clarity_local_substitution_applied") is True:
        gate_path = "visibility_local_repair"
    elif final_route == "accept_candidate" and fem.get("strict_social_active") is True:
        gate_path = "strict_social_accept"
    elif final_route == "accept_candidate" and (
        fem.get("post_gate_mutation_detected") is True or fem.get("response_type_repair_used") is True
    ):
        gate_path = "accept_repaired"
    elif final_route == "accept_candidate" and fem.get("post_gate_mutation_detected") is False:
        gate_path = "accept_unchanged"

    if gate_path is not None and not any(event.get("event_kind") == RUNTIME_LINEAGE_EVENT_GATE_OUTCOME for event in events):
        _append_fem_lineage_event(
            events,
            make_runtime_lineage_event(
                event_kind=RUNTIME_LINEAGE_EVENT_GATE_OUTCOME,
                stage="gate",
                owner="game.final_emission_gate",
                source=final_source,
                gate_path=gate_path,
            ),
        )

    speaker_projections = _fem_speaker_repair_projections(fem)
    for repair_kind, owner, source, notes in speaker_projections:
        _append_fem_lineage_event(
            events,
            make_runtime_lineage_event(
                event_kind=RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR,
                stage="gate",
                owner=owner,
                source=source,
                repair_kind=repair_kind,
                notes=notes,
            ),
        )
    _append_fem_mutation_projections(events, fem, fallback=fallback, speaker_projections=speaker_projections)
    return events[:16]
