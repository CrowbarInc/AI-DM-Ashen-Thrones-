"""Read-side FEM replay/runtime-lineage projection helpers.

This module must not select fallbacks, mutate output, or stamp write-time FEM.

Owner semantics for projected runtime-lineage events:
- ``projection_owner`` is this module: it derives lineage from already-finalized FEM.
- Projected event ``owner`` preserves the current event-owner meaning: selector or
  application owner for fallback paths, not necessarily fallback content owner.
- Opening fallback can therefore project ``owner="game.final_emission_gate"`` while
  carrying ``fallback_owner_bucket="upstream-prepared"`` and
  ``fallback_authorship_source="upstream_prepared_opening_fallback"``.
- Runtime FEM may carry both ``fallback_family_used`` (diegetic) and
  ``realization_fallback_family`` (governed provenance). Lineage ``fallback_kind``
  for opening uses diegetic ``scene_opening`` and does not collapse the two FEM fields.
  Golden replay observed ``fallback_family`` uses diegetic-first precedence via
  ``tests.helpers.golden_replay_projection.project_replay_fallback_family_from_fem``
  (read-side only; not applied here).
- Successful opening fallback and gate-selected strict-social fallback carry
  explicit ``fallback_selection_owner`` and ``fallback_content_owner`` fields.
  Sanitizer and sealed terminal replacement paths project the same split fields
  when content ownership is knowable from finalized FEM / sanitizer trace evidence.
  Upstream API fast fallback projects ``fallback_selection_owner="game.api"`` and
  ``fallback_content_owner="game.gm_retry"`` when ``fallback_provenance_trace``
  survives to FEM; ``owner`` remains ``game.api`` for event identity continuity.
  Provenance packaging is owned by ``game.fallback_provenance_debug``.
  Fail-closed opening keeps gate/sealed ownership and is not treated as
  upstream-authored content.
- ``fallback_owner_bucket`` for opening paths delegates to
  :func:`game.final_emission_meta.opening_fallback_owner_bucket_from_meta`; this module
  does not re-derive bucket rules from scratch.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.runtime_lineage_telemetry import (
    RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED,
    RUNTIME_LINEAGE_EVENT_GATE_OUTCOME,
    RUNTIME_LINEAGE_EVENT_MUTATION,
    RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR,
    make_runtime_lineage_event,
)
from game.telemetry_vocab import normalize_owner, normalize_reason_list

FINAL_EMISSION_MUTATION_LINEAGE_KEY: str = "final_emission_mutation_lineage"
OPENING_FALLBACK_SELECTION_OWNER: str = "game.final_emission_gate"
OPENING_FALLBACK_CONTENT_OWNER: str = "game.opening_deterministic_fallback"
OPENING_FAIL_CLOSED_CONTENT_OWNER: str = "game.final_emission_gate"
STRICT_SOCIAL_FALLBACK_SELECTION_OWNER: str = "game.final_emission_gate"
STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: str = "game.social_exchange_emission"
SANITIZER_FALLBACK_SELECTION_OWNER: str = "game.output_sanitizer"
SANITIZER_STRICT_SOCIAL_CONTENT_OWNER: str = "game.social_exchange_emission"
SEALED_FALLBACK_SELECTION_OWNER: str = OPENING_FALLBACK_SELECTION_OWNER
SEALED_FALLBACK_MODULE_CONTENT_OWNER: str = "game.final_emission_sealed_fallback"
SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: str = OPENING_FALLBACK_SELECTION_OWNER
UPSTREAM_FAST_FALLBACK_SELECTION_OWNER: str = "game.api"
UPSTREAM_FAST_FALLBACK_CONTENT_OWNER: str = "game.gm_retry"

# Short names stamped on sanitizer FEM/trace surfaces → canonical lineage module owners.
_SANITIZER_TRACE_OWNER_TO_LINEAGE: dict[str, str] = {
    "output_sanitizer": SANITIZER_FALLBACK_SELECTION_OWNER,
    "strict_social_emission": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
}

# Read-side sealed replacement sub-kinds (Cycle AB6). Runtime FEM keeps
# ``final_emitted_source`` / ``final_route`` unchanged; lineage projection refines
# the former catch-all ``sealed_or_global_replacement`` bucket.
SEALED_REPLACEMENT_SUBKIND_OPENING: str = "sealed_opening_fallback"
SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR: str = "sealed_social_interlocutor_fallback"
SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE: str = "sealed_passive_scene_pressure_fallback"
SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL: str = "sealed_npc_pursuit_neutral_fallback"
SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION: str = "sealed_anti_reset_continuation_fallback"
SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE: str = "sealed_global_scene_fallback"
SEALED_REPLACEMENT_SUBKIND_UNKNOWN: str = "sealed_unknown_replacement"
SEALED_REPLACEMENT_SUBKINDS: frozenset[str] = frozenset(
    {
        SEALED_REPLACEMENT_SUBKIND_OPENING,
        SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
        SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
        SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
        SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
        SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
        SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
    }
)
SEALED_REPLACEMENT_CONTENT_OWNER_BY_SUBKIND: dict[str, str] = {
    SEALED_REPLACEMENT_SUBKIND_OPENING: OPENING_FALLBACK_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR: STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE: SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL: SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION: SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE: SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN: SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
}
_LEGACY_SEALED_OR_GLOBAL_REPLACEMENT: str = "sealed_or_global_replacement"


def read_side_lineage_projection_surface() -> dict[str, object]:
    """Summarize stable read-side projection-owned surfaces (diagnostic only).

    Does not inspect live runtime state, select fallbacks, or mutate output.
    """
    return {
        "sealed_replacement_subkind_count": len(SEALED_REPLACEMENT_SUBKINDS),
        "sealed_replacement_subkind_tokens": sorted(SEALED_REPLACEMENT_SUBKINDS),
        "opening_fallback_selection_owner": OPENING_FALLBACK_SELECTION_OWNER,
        "opening_fallback_content_owner": OPENING_FALLBACK_CONTENT_OWNER,
        "strict_social_fallback_selection_owner": STRICT_SOCIAL_FALLBACK_SELECTION_OWNER,
        "strict_social_fallback_content_owner": STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        "sanitizer_fallback_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
        "sanitizer_strict_social_content_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        "sealed_fallback_selection_owner": SEALED_FALLBACK_SELECTION_OWNER,
        "sealed_replacement_content_owner_by_subkind": dict(
            sorted(SEALED_REPLACEMENT_CONTENT_OWNER_BY_SUBKIND.items())
        ),
        "upstream_fast_fallback_selection_owner": UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        "upstream_fast_fallback_content_owner": UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        "upstream_fast_fallback_provenance_packager": "game.fallback_provenance_debug",
        "mutation_lineage_key": FINAL_EMISSION_MUTATION_LINEAGE_KEY,
        "legacy_sealed_or_global_replacement_token": _LEGACY_SEALED_OR_GLOBAL_REPLACEMENT,
    }


def _norm_projection_token(value: Any) -> str:
    return str(value or "").strip().lower()


def is_sealed_replacement_lineage_kind(fallback_kind: Any) -> bool:
    """True when *fallback_kind* is a sealed replacement read-side projection bucket."""
    token = _norm_projection_token(fallback_kind)
    if not token:
        return False
    if token == _LEGACY_SEALED_OR_GLOBAL_REPLACEMENT:
        return True
    return token in SEALED_REPLACEMENT_SUBKINDS


def project_sealed_replacement_subkind_from_fem(fem: Mapping[str, Any]) -> str | None:
    """Map finalized sealed/gate-terminal replace FEM evidence to a stable read-side sub-kind.

    Returns ``None`` when *fem* is not a ``final_route == replaced`` terminal replace turn.
    Does not mutate *fem* or alter runtime selection metadata.
    """
    if _norm_projection_token(fem.get("final_route")) != "replaced":
        return None

    final_source = _norm_projection_token(fem.get("final_emitted_source"))
    fallback_kind = _norm_projection_token(
        fem.get("fallback_kind") or fem.get("visibility_fallback_kind")
    )

    if final_source == "opening_deterministic_fallback":
        return SEALED_REPLACEMENT_SUBKIND_OPENING
    if final_source == "social_interlocutor_minimal_fallback":
        return SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR
    if (
        final_source == "passive_scene_pressure_fallback"
        or fallback_kind.startswith("passive_scene_pressure")
    ):
        return SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE
    if (
        final_source == "npc_pursuit_neutral_fallback"
        or fallback_kind == "npc_pursuit_neutral_nonprogress"
    ):
        return SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL
    if (
        final_source == "anti_reset_local_continuation_fallback"
        or fallback_kind == "anti_reset_continuation_fallback"
    ):
        return SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION
    if final_source in {
        "global_scene_fallback",
        "scene_emit_integrity_safe_fallback",
        "narrative_safe_fallback",
        "acceptance_quality_global_scene_fallback",
    } or fallback_kind in {
        "narrative_safe_fallback",
        "scene_emit_integrity_safe_fallback",
    }:
        return SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE
    return SEALED_REPLACEMENT_SUBKIND_UNKNOWN


def _lineage_module_owner_from_trace(value: str | None, *, default: str) -> str:
    """Map sanitizer trace short owner names to canonical ``game.*`` lineage owners."""
    if not value:
        return default
    mapped = _SANITIZER_TRACE_OWNER_TO_LINEAGE.get(value)
    if mapped:
        return mapped
    normalized = normalize_owner(value)
    if normalized and normalized.startswith("game."):
        return normalized
    if normalized:
        return f"game.{normalized}"
    return default


def _fallback_split_owners_for_kind(
    fem: Mapping[str, Any],
    fallback_kind: str,
) -> tuple[str | None, str | None]:
    """Return ``(fallback_selection_owner, fallback_content_owner)`` for a projected kind."""
    if fallback_kind == "scene_opening":
        return OPENING_FALLBACK_SELECTION_OWNER, OPENING_FALLBACK_CONTENT_OWNER
    if fallback_kind == "opening_failed_closed":
        return OPENING_FALLBACK_SELECTION_OWNER, OPENING_FAIL_CLOSED_CONTENT_OWNER
    if fallback_kind in {"strict_social_fallback", "minimal_social_emergency_fallback"}:
        return STRICT_SOCIAL_FALLBACK_SELECTION_OWNER, STRICT_SOCIAL_FALLBACK_CONTENT_OWNER
    if fallback_kind == "sanitizer_strict_social":
        return (
            _lineage_module_owner_from_trace(
                _fem_lineage_source(fem, "sanitizer_strict_social_selection_owner"),
                default=SANITIZER_FALLBACK_SELECTION_OWNER,
            ),
            _lineage_module_owner_from_trace(
                _fem_lineage_source(fem, "sanitizer_strict_social_prose_owner"),
                default=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            ),
        )
    if fallback_kind == "sanitizer_empty_output":
        owner = _lineage_module_owner_from_trace(
            _fem_lineage_source(fem, "sanitizer_empty_fallback_owner"),
            default=SANITIZER_FALLBACK_SELECTION_OWNER,
        )
        return owner, owner
    if fallback_kind == "upstream_fast_fallback":
        return UPSTREAM_FAST_FALLBACK_SELECTION_OWNER, UPSTREAM_FAST_FALLBACK_CONTENT_OWNER
    if is_sealed_replacement_lineage_kind(fallback_kind):
        content_owner = SEALED_REPLACEMENT_CONTENT_OWNER_BY_SUBKIND.get(
            fallback_kind,
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        )
        return SEALED_FALLBACK_SELECTION_OWNER, content_owner
    return None, None


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
    """Return ``(fallback_kind, gate_path, stage, owner, source)`` only for proven selection.

    The returned ``owner`` is selection/application ownership for the projected
    event. Content authorship, when known, is attached later via fallback-specific
    attribution fields without changing replay event identity.
    """
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
    # Preserve ``owner`` as gate selection for P1; P2 may add or consume split-owner fields.
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
        sealed_subkind = project_sealed_replacement_subkind_from_fem(fem)
        if sealed_subkind is not None:
            return (
                sealed_subkind,
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
        fallback_selection_owner, fallback_content_owner = _fallback_split_owners_for_kind(
            fem,
            fallback_kind,
        )
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
                fallback_selection_owner=fallback_selection_owner,
                fallback_content_owner=fallback_content_owner,
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
