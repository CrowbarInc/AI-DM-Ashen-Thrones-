"""Opening fallback selection and fail-closed policy used by final emission.

This module selects an existing upstream-prepared opening fallback snapshot or
the existing sealed fail-closed marker. It does not author opening prose,
package upstream payloads, write final output, or own gate orchestration.

Success-path ``opening_fallback_authorship_source`` is written once upstream by
:func:`game.upstream_response_repairs.build_upstream_prepared_opening_fallback_payload`
and mirrored here from ``opening_fallback_composition_meta`` when a prepared
payload is selected. Fail-closed paths leave authorship absent or ``None``.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from game.diegetic_fallback_narration import (
    fallback_template_metadata as diegetic_classified_fallback_meta,
    opening_scene_fallback_template_allowed as diegetic_opening_scene_template_allowed,
)
from game.opening_deterministic_fallback import (
    OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
    opening_context_from_gm_output as _opening_context_from_gm_output,
)
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    is_structurally_usable_upstream_prepared_opening_fallback_payload,
)

_OPENING_SCENE_SAFE_FALLBACK_POOL = "scene_opening_deterministic"
_OPENING_SCENE_SAFE_FALLBACK_KIND = "opening_deterministic_fallback"
_OPENING_SCENE_SAFE_FALLBACK_SOURCE = "opening_deterministic_fallback"
_OPENING_SCENE_SAFE_FALLBACK_STRATEGY = "opening_scene_safe_fallback"
_OPENING_SCENE_SAFE_FALLBACK_CANDIDATE_SOURCE = "opening_deterministic_fallback"


def build_opening_fallback_result_meta(
    *,
    context: Mapping[str, Any] | None = None,
    facts: list[str] | None = None,
    opening_fallback_failed_closed: bool = False,
    force_fail_closed_context_source: bool = False,
) -> Dict[str, Any]:
    """Canonical opening fallback result metadata (selection/FEM projection core).

    Aligns with :data:`game.final_emission_meta.OPENING_FALLBACK_RESULT_META_FIELDS`
    (subset of ``OPENING_FALLBACK_PROJECTION_FIELDS``). Authorship is stamped only
    upstream on the success path; selection mirrors it from composition meta.
    """
    if context is None:
        return {
            "opening_fallback_context_source": "opening_curated_facts",
            "opening_fallback_basis_count": 0,
            "opening_fallback_context_missing": True,
            "opening_fallback_failed_closed": True,
            "opening_curated_facts_present": False,
            "opening_curated_facts_count": 0,
            "opening_curated_facts_source": "selector",
            "opening_selector_source_used": "none",
            "opening_selector_selected_facts": [],
            "opening_curated_facts": [],
            "opening_final_fallback_basis": [],
            "opening_final_basis_matches_selector": True,
        }
    resolved_facts = (
        facts
        if facts is not None
        else [
            str(x).strip().rstrip(".")
            for x in (context.get("visible_facts") or [])
            if str(x).strip()
        ]
    )
    meta: Dict[str, Any] = {
        "opening_fallback_context_source": context.get("opening_fallback_context_source"),
        "opening_fallback_basis_count": len(resolved_facts),
        "opening_fallback_context_missing": not bool(resolved_facts),
        "opening_fallback_failed_closed": opening_fallback_failed_closed,
        "opening_curated_facts_present": bool(resolved_facts),
        "opening_curated_facts_count": len(resolved_facts),
        "opening_curated_facts_source": context.get("opening_curated_facts_source") or "selector",
        "opening_selector_source_used": context.get("opening_selector_source_used") or "none",
        "opening_selector_selected_facts": list(context.get("opening_selector_selected_facts") or []),
        "opening_curated_facts": list(context.get("opening_curated_facts") or []),
        "opening_final_fallback_basis": list(context.get("opening_final_fallback_basis") or []),
        "opening_final_basis_matches_selector": bool(context.get("opening_final_basis_matches_selector")),
    }
    if opening_fallback_failed_closed and (
        force_fail_closed_context_source or not resolved_facts
    ):
        meta["opening_fallback_context_source"] = "opening_curated_facts"
    return meta


def build_upstream_prepared_opening_composition_meta(
    result_meta: Mapping[str, Any],
    *,
    fallback_family_used: str | None,
    fallback_temporal_frame: str | None,
    opening_fallback_authorship_source: str,
) -> Dict[str, Any]:
    """Assemble ``opening_fallback_composition_meta`` from canonical result metadata + upstream layers."""
    composition_meta: Dict[str, Any] = {
        "first_mention_composition_used": False,
        "first_mention_composition_layers": {"environment": None, "motion": None, "entities": []},
        "fallback_family_used": fallback_family_used,
        "fallback_temporal_frame": fallback_temporal_frame,
        "opening_fallback_authorship_source": opening_fallback_authorship_source,
    }
    composition_meta.update(dict(result_meta))
    return composition_meta


def opening_fallback_authorship_source_from_composition_meta(
    composition_meta: Mapping[str, Any] | None,
) -> str | None:
    """Read authorship from upstream composition meta without inferring defaults."""
    if not isinstance(composition_meta, Mapping):
        return None
    value = composition_meta.get("opening_fallback_authorship_source")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _result_meta_from_upstream_prepared_payload(upstream: Mapping[str, Any]) -> Dict[str, Any]:
    """Build adapter result meta from upstream prepared opening payload (mirror only)."""
    result_meta = dict(upstream["opening_fallback_meta"])
    authorship = opening_fallback_authorship_source_from_composition_meta(
        upstream.get("opening_fallback_composition_meta")
    )
    if authorship is not None:
        result_meta["opening_fallback_authorship_source"] = authorship
    return result_meta


def _opening_fallback_classification() -> Dict[str, str]:
    template_id = "opening_deterministic_fallback"
    if not diegetic_opening_scene_template_allowed(template_id):
        raise AssertionError("opening deterministic fallback template is not opening-scene classified")
    return diegetic_classified_fallback_meta(template_id)


def _opening_curated_facts_have_attachable_non_empty_strings(gm_output: Mapping[str, Any] | None) -> bool:
    """Aligned with upstream prepared-opening payload attachment preconditions."""
    if not isinstance(gm_output, dict):
        return False
    facts = gm_output.get("opening_curated_facts")
    if not isinstance(facts, list):
        return False
    return any(isinstance(x, str) and x.strip() for x in facts)


def _opening_curated_facts_schema_ok(gm_output: Mapping[str, Any] | None) -> bool:
    """True when ``opening_curated_facts`` is present and a list (empty list is valid schema)."""
    return (
        isinstance(gm_output, dict)
        and "opening_curated_facts" in gm_output
        and isinstance(gm_output.get("opening_curated_facts"), list)
    )


def _gm_output_normalized_for_opening_context(gm_output: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Normalize missing/non-list curated facts to ``[]`` before context extraction."""
    if not isinstance(gm_output, dict):
        return {"opening_curated_facts": []}
    if _opening_curated_facts_schema_ok(gm_output):
        return gm_output
    merged = dict(gm_output)
    merged["opening_curated_facts"] = []
    return merged


def _opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(
    gm_output: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Meta for the sealed opening marker when an upstream payload cannot be selected."""
    block_h = {
        "opening_fallback_compatibility_local_disabled": True,
        "opening_fallback_missing_upstream_prepared_payload": True,
    }
    if isinstance(gm_output, dict) and isinstance(gm_output.get("opening_curated_facts"), list):
        ctx = _opening_context_from_gm_output(gm_output)
        facts = [str(x).strip().rstrip(".") for x in (ctx.get("visible_facts") or []) if str(x).strip()]
        meta = build_opening_fallback_result_meta(
            context=ctx,
            facts=facts,
            opening_fallback_failed_closed=True,
            force_fail_closed_context_source=True,
        )
        meta["opening_fallback_missing_curated_facts"] = False
        meta.update(block_h)
        return meta
    meta = build_opening_fallback_result_meta(context=None)
    meta["opening_fallback_missing_curated_facts"] = True
    meta.update(block_h)
    return meta


def _upstream_prepared_opening_fallback_payload_if_usable(
    gm_output: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    """Return the prepared opening snapshot if structurally consumable by the gate."""
    if not isinstance(gm_output, dict):
        return None
    raw = gm_output.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY)
    return raw if is_structurally_usable_upstream_prepared_opening_fallback_payload(raw) else None


def _recover_upstream_opening_fallback_stub_payload(
    gm_output: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, Dict[str, Any]]:
    """Return a usable opening payload or mark a gate-arriving stub fail-closed."""
    patch: Dict[str, Any] = {}
    if not isinstance(gm_output, dict):
        return None, patch
    usable = _upstream_prepared_opening_fallback_payload_if_usable(gm_output)
    if usable:
        return usable, patch
    if UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm_output:
        return None, patch
    patch["opening_fallback_upstream_payload_unusable"] = True
    patch["opening_fallback_upstream_payload_recovered"] = False
    patch["opening_fallback_compatibility_local_disabled"] = True
    return None, patch


def _opening_maybe_attach_upstream_prepare_build_failed_on_emission_debug(
    gm_output: Mapping[str, Any] | None,
) -> bool:
    """True when upstream attach recorded a prepared-opening build failure."""
    if not isinstance(gm_output, dict):
        return False
    md = gm_output.get("metadata")
    em = md.get("emission_debug") if isinstance(md, dict) else None
    if not isinstance(em, dict):
        return False
    return bool(em.get("opening_upstream_prepare_attach_build_failed"))


def _opening_fail_closed_meta_upstream_maybe_attach_prepare_failed(
    gm_output: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Sealed marker meta when upstream attach was attempted but failed."""
    out: Dict[str, Any] = {
        "opening_fallback_failed_closed": True,
        "opening_fallback_compatibility_local_disabled": True,
        "opening_fallback_missing_upstream_prepared_payload": True,
        "blocked_repair_kind": "opening_upstream_prepare_attach_failed",
    }
    if isinstance(gm_output, dict) and isinstance(gm_output.get("opening_curated_facts"), list):
        ctx = _opening_context_from_gm_output(gm_output)
        facts = [str(x).strip().rstrip(".") for x in (ctx.get("visible_facts") or []) if str(x).strip()]
        out.update(
            build_opening_fallback_result_meta(
                context=ctx,
                facts=facts,
                opening_fallback_failed_closed=True,
                force_fail_closed_context_source=True,
            )
        )
    return out


def _opening_fail_closed_meta_upstream_stub_rebuild_failed(
    gm_output: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Sealed marker meta when an unusable upstream stub reaches the gate."""
    out: Dict[str, Any] = {
        "opening_fallback_failed_closed": True,
        "opening_fallback_compatibility_local_disabled": True,
        "opening_fallback_upstream_payload_unusable": True,
        "opening_fallback_upstream_payload_recovered": False,
        "opening_fallback_missing_upstream_prepared_payload": False,
    }
    if isinstance(gm_output, dict) and isinstance(gm_output.get("opening_curated_facts"), list):
        ctx = _opening_context_from_gm_output(gm_output)
        facts = [str(x).strip().rstrip(".") for x in (ctx.get("visible_facts") or []) if str(x).strip()]
        out.update(
            build_opening_fallback_result_meta(
                context=ctx,
                facts=facts,
                opening_fallback_failed_closed=True,
                force_fail_closed_context_source=True,
            )
        )
    return out


def select_opening_fallback_for_response_type_contract(
    gm_output: Mapping[str, Any] | None,
) -> tuple[str, Dict[str, Any], Dict[str, Any], bool, Dict[str, Any] | None]:
    """Select opening fallback text and debug metadata for response-type enforcement.

    Returns ``fallback_text``, ``result_meta`` (``opening_fallback_meta`` shape on upstream
    success), ``stub_patch``, whether upstream-prepared was selected, and the upstream payload
    snapshot when selected (else ``None``).
    """
    gm_dict = gm_output if isinstance(gm_output, dict) else None
    upstream, stub_patch = (
        _recover_upstream_opening_fallback_stub_payload(gm_dict)
        if gm_dict is not None
        else (None, {})
    )
    if upstream:
        return (
            str(upstream["prepared_opening_fallback_text"]).strip(),
            _result_meta_from_upstream_prepared_payload(upstream),
            stub_patch,
            True,
            upstream,
        )
    if stub_patch.get("opening_fallback_upstream_payload_unusable") and stub_patch.get(
        "opening_fallback_upstream_payload_recovered"
    ) is False:
        return (
            OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
            _opening_fail_closed_meta_upstream_stub_rebuild_failed(gm_output),
            stub_patch,
            False,
            None,
        )
    if _opening_maybe_attach_upstream_prepare_build_failed_on_emission_debug(gm_dict):
        return (
            OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
            _opening_fail_closed_meta_upstream_maybe_attach_prepare_failed(gm_output),
            stub_patch,
            False,
            None,
        )
    fail_closed_meta = _opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(gm_output)
    return (
        OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
        fail_closed_meta,
        stub_patch,
        False,
        None,
    )


def opening_scene_safe_fallback_selection(
    gm_output: Mapping[str, Any] | None,
    *,
    fail_closed_composition_meta_factory: Callable[[], Dict[str, Any]],
) -> VisibilitySelectedFallback:
    """Canonical opening hard-replace selection: upstream snapshot or sealed marker."""
    fallback_text, fallback_meta, stub_patch, upstream_selected, upstream_payload = (
        select_opening_fallback_for_response_type_contract(gm_output)
    )
    if upstream_selected and upstream_payload is not None:
        composition_meta = dict(upstream_payload["opening_fallback_composition_meta"])
        composition_meta.update(stub_patch)
        return VisibilitySelectedFallback(
            text=fallback_text,
            fallback_pool=_OPENING_SCENE_SAFE_FALLBACK_POOL,
            fallback_kind=_OPENING_SCENE_SAFE_FALLBACK_KIND,
            final_emitted_source=_OPENING_SCENE_SAFE_FALLBACK_SOURCE,
            fallback_strategy=_OPENING_SCENE_SAFE_FALLBACK_STRATEGY,
            fallback_candidate_source=_OPENING_SCENE_SAFE_FALLBACK_CANDIDATE_SOURCE,
            composition_meta=composition_meta,
        )
    classification = _opening_fallback_classification()
    meta = fail_closed_composition_meta_factory()
    meta["fallback_family_used"] = classification.get("fallback_family")
    meta["fallback_temporal_frame"] = classification.get("temporal_frame")
    meta.update(fallback_meta)
    meta.update(stub_patch)
    meta["opening_fallback_authorship_source"] = None
    return VisibilitySelectedFallback(
        text=fallback_text,
        fallback_pool=_OPENING_SCENE_SAFE_FALLBACK_POOL,
        fallback_kind=_OPENING_SCENE_SAFE_FALLBACK_KIND,
        final_emitted_source=_OPENING_SCENE_SAFE_FALLBACK_SOURCE,
        fallback_strategy=_OPENING_SCENE_SAFE_FALLBACK_STRATEGY,
        fallback_candidate_source=_OPENING_SCENE_SAFE_FALLBACK_CANDIDATE_SOURCE,
        composition_meta=meta,
    )
