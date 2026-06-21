"""Metadata and route stamping helpers for sealed final-emission fallback replacement.

This module must not author or select fallback prose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Mapping, MutableMapping

from game.final_emission_ownership_schema import (
    SEALED_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
)
from game.final_emission_meta import (
    refresh_final_emission_mutation_lineage,
    sealed_fallback_owner_bucket_from_fields,
)
import game.final_emission_visibility_fallback as visibility_fallback
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.final_emission_text import _normalize_text
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    attach_realization_fallback_family,
)


@dataclass(frozen=True)
class SealedFallbackSelection:
    """Selected sealed fallback data; carries prose selected by existing owners but does not author it."""

    text: str
    fallback_pool: str
    fallback_kind: str
    final_emitted_source: str
    composition_meta: Mapping[str, Any] | None = None

    @classmethod
    def from_legacy_tuple(cls, value: tuple[Any, ...]) -> "SealedFallbackSelection":
        """Adapt the existing five-field sealed fallback tuple without changing its meaning."""
        text, fallback_pool, fallback_kind, final_emitted_source, composition_meta = value
        return cls(
            text=str(text),
            fallback_pool=str(fallback_pool),
            fallback_kind=str(fallback_kind),
            final_emitted_source=str(final_emitted_source),
            composition_meta=composition_meta if isinstance(composition_meta, Mapping) else None,
        )

    def as_legacy_tuple(self) -> tuple[str, str, str, str, Mapping[str, Any] | None]:
        """Return the historical tuple shape consumed by compatibility wrappers."""
        return (
            self.text,
            self.fallback_pool,
            self.fallback_kind,
            self.final_emitted_source,
            self.composition_meta,
        )

    @classmethod
    def from_visibility_selection(cls, selected: VisibilitySelectedFallback) -> "SealedFallbackSelection":
        """Project visibility selection into sealed selection (strategy/candidate fields are visibility-only)."""
        return cls(
            text=selected.text,
            fallback_pool=selected.fallback_pool,
            fallback_kind=selected.fallback_kind,
            final_emitted_source=selected.final_emitted_source,
            composition_meta=selected.composition_meta,
        )

    @classmethod
    def from_visibility_tuple(cls, value: tuple[Any, ...]) -> "SealedFallbackSelection":
        """Adapt a 7-field visibility tuple without changing sealed selection semantics."""
        (
            text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            _fallback_strategy,
            _fallback_candidate_source,
            composition_meta,
        ) = value
        return cls(
            text=str(text),
            fallback_pool=str(fallback_pool),
            fallback_kind=str(fallback_kind),
            final_emitted_source=str(final_emitted_source),
            composition_meta=composition_meta if isinstance(composition_meta, Mapping) else None,
        )


def select_visibility_safe_fallback(
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
    """Facade for visibility-safe fallback selection; hoists cross-owner routing lazy imports."""
    from game.anti_reset_emission_guard import (
        anti_reset_suppresses_intro_style_fallbacks,
        should_replace_candidate_intro_fallback,
    )
    from game.final_emission_first_mention_composition import _grounded_scene_intro_fallback_candidates
    from game.final_emission_opening_mode import _opening_mode_active_for_turn
    from game.final_emission_passive_scene_pressure import _passive_scene_pressure_due_for_fallback
    from game.final_emission_scene_facts import _augment_scene_with_runtime_visible_leads

    return visibility_fallback._standard_visibility_safe_fallback_core(
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
        opening_mode_active_for_turn=_opening_mode_active_for_turn,
        augment_scene_with_runtime_visible_leads=_augment_scene_with_runtime_visible_leads,
        anti_reset_suppresses_intro_style_fallbacks=anti_reset_suppresses_intro_style_fallbacks,
        should_replace_candidate_intro_fallback=should_replace_candidate_intro_fallback,
        grounded_scene_intro_fallback_candidates=_grounded_scene_intro_fallback_candidates,
        passive_scene_pressure_due_for_fallback=_passive_scene_pressure_due_for_fallback,
    )


def _opening_visibility_fallback_for_sealed_terminal(
    gm_output: Dict[str, Any],
    opening_sealed_fallback_provider: Callable[[Dict[str, Any]], SealedFallbackSelection],
) -> VisibilitySelectedFallback:
    """Project injected or default sealed opening selection into visibility shape for BK3 consumption."""
    sealed_opening = opening_sealed_fallback_provider(gm_output)
    return visibility_fallback.visibility_selected_fallback_candidate(
        sealed_opening.text,
        sealed_opening.fallback_pool,
        sealed_opening.fallback_kind,
        sealed_opening.final_emitted_source,
        "opening_scene_safe_fallback",
        sealed_opening.final_emitted_source,
        sealed_opening.composition_meta
        if isinstance(sealed_opening.composition_meta, Mapping)
        else visibility_fallback.first_mention_composition_meta(),
    )


def _default_opening_sealed_fallback_provider() -> Callable[[Dict[str, Any]], SealedFallbackSelection]:
    from game.final_emission_opening_fallback import make_opening_sealed_fallback_provider
    from game.final_emission_visibility_fallback import first_mention_composition_meta

    return make_opening_sealed_fallback_provider(
        fail_closed_composition_meta_factory=first_mention_composition_meta,
    )


def select_non_strict_replace_path_terminal_sealed_fallback_selection(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    sid: str,
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_suppressed_non_social_turn: bool,
    res_kind: str,
    response_type_required: str,
    suppress_intro_replace: bool,
    interaction_mode: str,
    opening_sealed_fallback_provider: Callable[[Dict[str, Any]], SealedFallbackSelection] | None = None,
) -> SealedFallbackSelection:
    """Select the non-strict sealed fallback; consumes visibility-owned terminal candidates (BK3)."""
    from game.final_emission_opening_mode import _opening_mode_active_for_turn

    opening_provider = (
        opening_sealed_fallback_provider
        if opening_sealed_fallback_provider is not None
        else _default_opening_sealed_fallback_provider()
    )
    mode = str(interaction_mode or "").strip().lower()
    opening_mode_active = _opening_mode_active_for_turn(out, resolution if isinstance(resolution, dict) else None)
    if opening_mode_active:
        return opening_provider(out)

    selected = visibility_fallback.select_non_strict_terminal_fallback_for_sealed(
        gm_output=out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        resolution=resolution,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        res_kind=res_kind,
        response_type_required=response_type_required,
        suppress_intro_replace=suppress_intro_replace,
        interaction_mode=mode,
        opening_visibility_fallback=lambda: _opening_visibility_fallback_for_sealed_terminal(
            out,
            opening_provider,
        ),
    )
    return SealedFallbackSelection.from_visibility_selection(selected)


def non_strict_sealed_replacement_realization_family_token() -> str:
    """Canonical ``realization_fallback_family`` for generic sealed terminal replace paths."""
    return GATE_TERMINAL_REPAIR


def stamp_non_strict_sealed_replacement_realization_family(
    meta: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Stamp gate-terminal repair family on non-strict sealed replacement FEM fragments."""
    attach_realization_fallback_family(meta, GATE_TERMINAL_REPAIR)
    if not str(meta.get("sealed_fallback_owner_bucket") or "").strip():
        from game.final_emission_meta import sealed_fallback_owner_bucket_from_fields

        meta["sealed_fallback_owner_bucket"] = sealed_fallback_owner_bucket_from_fields(
            final_emitted_source=str(meta.get("final_emitted_source") or ""),
            strict_social_route=bool(meta.get("strict_social_active")),
        )
    return meta


def stamp_sealed_fallback_realization_family(
    meta: MutableMapping[str, Any],
    *,
    final_emitted_source: str,
    strict_social_route: bool,
) -> None:
    """Telemetry-only: classify sealed hard-replace prose for ``realization_fallback_family``.

    Matches terminal replace-path policy: gate-terminal repair for generic sealed tuples; strict-social
    deterministic only when the emitted source id is the strict-social minimal emergency pool.
    """
    src = str(final_emitted_source or "").strip()
    if strict_social_route and src == "minimal_social_emergency_fallback":
        attach_realization_fallback_family(meta, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
    else:
        attach_realization_fallback_family(meta, GATE_TERMINAL_REPAIR)
    meta["sealed_fallback_owner_bucket"] = sealed_fallback_owner_bucket_from_fields(
        final_emitted_source=src,
        strict_social_route=strict_social_route,
    )


def prepare_sealed_replacement_route_meta(
    meta: MutableMapping[str, Any],
    *,
    gm_output: Mapping[str, Any],
    pre_gate_candidate_text: str,
    final_emitted_source: str,
    strict_social_route: bool,
    composition_meta: Mapping[str, Any] | None,
) -> None:
    """Shared FEM assembly after ``player_facing_text`` is swapped to sealed fallback (visibility-safe paths).

    When *composition_meta* is ``None``, diegetic ``fallback_family_used`` / ``fallback_temporal_frame``
    are left untouched (visibility enforcement historically omits them here).
    """
    gate_out_text = _normalize_text(gm_output.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    stamp_sealed_fallback_realization_family(
        meta,
        final_emitted_source=final_emitted_source,
        strict_social_route=strict_social_route,
    )
    if composition_meta is not None:
        meta["fallback_family_used"] = composition_meta.get("fallback_family_used")
        meta["fallback_temporal_frame"] = composition_meta.get("fallback_temporal_frame")
    meta["post_gate_mutation_detected"] = pre_gate_candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    refresh_final_emission_mutation_lineage(meta)


def finalize_n4_sealed_replace_fem_route_meta(
    fem: MutableMapping[str, Any],
    *,
    strict_social_path: bool,
) -> None:
    """Route-level FEM keys for acceptance-quality N4 hard replace (selection happens upstream)."""
    fe_src = (
        "minimal_social_emergency_fallback"
        if strict_social_path
        else "acceptance_quality_global_scene_fallback"
    )
    fem["final_route"] = "replaced"
    fem["candidate_validation_passed"] = False
    fem["final_emitted_source"] = fe_src
    stamp_sealed_fallback_realization_family(
        fem,
        final_emitted_source=fe_src,
        strict_social_route=strict_social_path,
    )


def select_acceptance_quality_n4_sealed_fallback_line(
    *,
    strict_social_path: bool,
    eff_resolution: Mapping[str, Any] | None,
    scene: dict[str, Any] | None,
    scene_id: str,
    resolution: Mapping[str, Any] | None,
    session: dict[str, Any] | None,
    world: dict[str, Any] | None,
    res_kind: str,
    response_type_required: str,
) -> str:
    """Select the N4 sealed fallback line via owner modules; this helper must not author prose."""
    if strict_social_path:
        from game.social_exchange_emission import minimal_social_emergency_fallback_line

        return minimal_social_emergency_fallback_line(
            eff_resolution if isinstance(eff_resolution, dict) else None,
        )
    from game.final_emission_scene_emit_integrity import _scene_emit_integrity_global_fallback_selection

    return _scene_emit_integrity_global_fallback_selection(
        scene if isinstance(scene, dict) else None,
        str(scene_id or "").strip(),
        authoritative_resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=res_kind,
        response_type_required=response_type_required,
    ).text


def select_non_strict_replace_path_terminal_sealed_fallback_branch(
    *,
    opening_mode_active: bool,
    has_active_social_interlocutor: bool,
    passive_candidate_available: bool,
    use_neutral_nonprogress: bool,
    suppress_intro_replace: bool,
) -> Literal[
    "opening_scene_safe_fallback",
    "social_active_interlocutor_minimal",
    "passive_scene_pressure",
    "npc_pursuit_neutral_nonprogress",
    "anti_reset_local_continuation",
    "scene_emit_integrity_global",
]:
    """Select the non-strict sealed fallback branch; candidate prose is still built by the gate."""
    if opening_mode_active:
        return "opening_scene_safe_fallback"
    if has_active_social_interlocutor:
        return "social_active_interlocutor_minimal"
    if passive_candidate_available:
        return "passive_scene_pressure"
    if use_neutral_nonprogress:
        return "npc_pursuit_neutral_nonprogress"
    if suppress_intro_replace:
        return "anti_reset_local_continuation"
    return "scene_emit_integrity_global"
