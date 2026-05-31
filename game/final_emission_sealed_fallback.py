"""Metadata and route stamping helpers for sealed final-emission fallback replacement.

This module must not author or select fallback prose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Mapping, MutableMapping, NamedTuple, Sequence

from game.final_emission_meta import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    refresh_final_emission_mutation_lineage,
)
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


class NonStrictSealedFallbackProviders(NamedTuple):
    passive_candidates_provider: Callable[[], Sequence[SealedFallbackSelection]]
    use_neutral_nonprogress_provider: Callable[[], bool]
    opening_provider: Callable[[], SealedFallbackSelection]
    social_interlocutor_provider: Callable[[], SealedFallbackSelection]
    neutral_nonprogress_provider: Callable[[], SealedFallbackSelection]
    anti_reset_provider: Callable[[], SealedFallbackSelection]
    global_provider: Callable[[], SealedFallbackSelection]


def build_non_strict_sealed_fallback_providers(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    sid: str,
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    res_kind: str,
    response_type_required: str,
    opening_scene_safe_fallback_tuple: Callable[[Dict[str, Any]], tuple[Any, ...]],
    passive_scene_pressure_fallback_candidates: Callable[..., list[tuple[Any, ...]]],
    should_use_neutral_nonprogress_fallback_instead_of_global_stock: Callable[[Any, Any], bool],
    scene_emit_integrity_global_fallback_tuple: Callable[..., tuple[Any, ...]],
    minimal_social_emergency_fallback_line: Callable[[Dict[str, Any] | None], str],
    npc_display_name_for_emission: Callable[[Any, str, str], str],
    npc_pursuit_neutral_nonprogress_fallback_line: Callable[[], str],
    local_exchange_continuation_fallback_line: Callable[..., str],
) -> NonStrictSealedFallbackProviders:
    """Assemble sealed fallback branch providers; prose comes from injected gate-owned builders."""

    def _opening_provider() -> SealedFallbackSelection:
        (
            fallback_text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            _fb_strat_ie,
            _fb_cand_ie,
            fallback_composition_meta,
        ) = opening_scene_safe_fallback_tuple(out)
        return SealedFallbackSelection(
            text=fallback_text,
            fallback_pool=fallback_pool,
            fallback_kind=fallback_kind,
            final_emitted_source=final_emitted_source,
            composition_meta=fallback_composition_meta,
        )

    def _social_interlocutor_provider() -> SealedFallbackSelection:
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_pool = "social_active_interlocutor_minimal"
        fallback_text = minimal_social_emergency_fallback_line(mini_res)
        fallback_kind = "social_interlocutor_fallback"
        final_emitted_source = "social_interlocutor_minimal_fallback"
        return SealedFallbackSelection(fallback_text, fallback_pool, fallback_kind, final_emitted_source, None)

    def _passive_candidates_provider() -> list[SealedFallbackSelection]:
        passive_candidates = passive_scene_pressure_fallback_candidates(
            session=session if isinstance(session, dict) else None,
            scene=scene,
            scene_id=sid,
        )
        selections: list[SealedFallbackSelection] = []
        for candidate in passive_candidates:
            (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                _fallback_strategy,
                _fallback_candidate_source,
                _composition_meta,
            ) = candidate
            selections.append(
                SealedFallbackSelection(
                    fallback_text, fallback_pool, fallback_kind, final_emitted_source, None
                )
            )
        return selections

    def _use_neutral_nonprogress_provider() -> bool:
        return should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution)

    def _neutral_nonprogress_provider() -> SealedFallbackSelection:
        fallback_pool = "npc_pursuit_fail_closed_neutral"
        fallback_text = npc_pursuit_neutral_nonprogress_fallback_line()
        fallback_kind = "npc_pursuit_neutral_nonprogress"
        final_emitted_source = "npc_pursuit_neutral_fallback"
        return SealedFallbackSelection(fallback_text, fallback_pool, fallback_kind, final_emitted_source, None)

    def _anti_reset_provider() -> SealedFallbackSelection:
        fallback_pool = "anti_reset_local_continuation"
        fallback_text = local_exchange_continuation_fallback_line(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=sid,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
        fallback_kind = "anti_reset_continuation_fallback"
        final_emitted_source = "anti_reset_local_continuation_fallback"
        return SealedFallbackSelection(fallback_text, fallback_pool, fallback_kind, final_emitted_source, None)

    def _global_provider() -> SealedFallbackSelection:
        (
            fallback_text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            _fb_strat_ie,
            _fb_cand_ie,
            _comp_ie,
        ) = scene_emit_integrity_global_fallback_tuple(
            scene if isinstance(scene, dict) else None,
            sid,
            authoritative_resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            res_kind=res_kind,
            response_type_required=response_type_required,
        )
        return SealedFallbackSelection(fallback_text, fallback_pool, fallback_kind, final_emitted_source, None)

    return NonStrictSealedFallbackProviders(
        passive_candidates_provider=_passive_candidates_provider,
        use_neutral_nonprogress_provider=_use_neutral_nonprogress_provider,
        opening_provider=_opening_provider,
        social_interlocutor_provider=_social_interlocutor_provider,
        neutral_nonprogress_provider=_neutral_nonprogress_provider,
        anti_reset_provider=_anti_reset_provider,
        global_provider=_global_provider,
    )


def non_strict_sealed_replacement_realization_family_token() -> str:
    """Canonical ``realization_fallback_family`` for generic sealed terminal replace paths."""
    return GATE_TERMINAL_REPAIR


def stamp_non_strict_sealed_replacement_realization_family(
    meta: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Stamp gate-terminal repair family on non-strict sealed replacement FEM fragments."""
    return attach_realization_fallback_family(meta, GATE_TERMINAL_REPAIR)


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
        meta["sealed_fallback_owner_bucket"] = SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
    else:
        attach_realization_fallback_family(meta, GATE_TERMINAL_REPAIR)
        meta["sealed_fallback_owner_bucket"] = SEALED_FALLBACK_OWNER_SEALED_GATE


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
    minimal_social_fallback_builder: Callable[[dict[str, Any] | None], str],
    global_fallback_tuple_builder: Callable[..., tuple[Any, ...]],
) -> str:
    """Select the N4 sealed fallback line via injected prose owners; this helper must not author prose."""
    if strict_social_path:
        return minimal_social_fallback_builder(eff_resolution if isinstance(eff_resolution, dict) else None)
    return global_fallback_tuple_builder(
        scene if isinstance(scene, dict) else None,
        str(scene_id or "").strip(),
        authoritative_resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        res_kind=res_kind,
        response_type_required=response_type_required,
    )[0]


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


def assemble_non_strict_sealed_fallback_selection(
    *,
    opening_mode_active: bool,
    has_active_social_interlocutor: bool,
    passive_candidates_provider: Callable[[], Sequence[SealedFallbackSelection]],
    use_neutral_nonprogress_provider: Callable[[], bool],
    suppress_intro_replace: bool,
    opening_provider: Callable[[], SealedFallbackSelection],
    social_interlocutor_provider: Callable[[], SealedFallbackSelection],
    neutral_nonprogress_provider: Callable[[], SealedFallbackSelection],
    anti_reset_provider: Callable[[], SealedFallbackSelection],
    global_provider: Callable[[], SealedFallbackSelection],
) -> SealedFallbackSelection:
    """Choose among provided fallback candidates. It must not author fallback prose."""
    initial_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=opening_mode_active,
        has_active_social_interlocutor=has_active_social_interlocutor,
        passive_candidate_available=False,
        use_neutral_nonprogress=False,
        suppress_intro_replace=False,
    )
    if initial_branch == "opening_scene_safe_fallback":
        return opening_provider()
    if initial_branch == "social_active_interlocutor_minimal":
        return social_interlocutor_provider()

    passive_candidates = list(passive_candidates_provider() or ())
    passive_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=False,
        has_active_social_interlocutor=False,
        passive_candidate_available=bool(passive_candidates),
        use_neutral_nonprogress=False,
        suppress_intro_replace=False,
    )
    if passive_branch == "passive_scene_pressure":
        return passive_candidates[0]

    final_branch = select_non_strict_replace_path_terminal_sealed_fallback_branch(
        opening_mode_active=False,
        has_active_social_interlocutor=False,
        passive_candidate_available=False,
        use_neutral_nonprogress=use_neutral_nonprogress_provider(),
        suppress_intro_replace=suppress_intro_replace,
    )
    if final_branch == "npc_pursuit_neutral_nonprogress":
        return neutral_nonprogress_provider()
    if final_branch == "anti_reset_local_continuation":
        return anti_reset_provider()
    return global_provider()
