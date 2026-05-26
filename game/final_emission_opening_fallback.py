"""Opening fallback selection and fail-closed policy used by final emission.

This module selects an existing upstream-prepared opening fallback snapshot or
the existing sealed fail-closed marker. It does not author opening prose,
package upstream payloads, write final output, or own gate orchestration.
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
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    is_structurally_usable_upstream_prepared_opening_fallback_payload,
)


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
        meta = {
            "opening_fallback_context_source": ctx.get("opening_fallback_context_source"),
            "opening_fallback_basis_count": len(facts),
            "opening_fallback_context_missing": not bool(facts),
            "opening_fallback_failed_closed": False,
            "opening_curated_facts_present": bool(facts),
            "opening_curated_facts_count": len(facts),
            "opening_curated_facts_source": ctx.get("opening_curated_facts_source") or "selector",
            "opening_selector_source_used": ctx.get("opening_selector_source_used") or "none",
            "opening_selector_selected_facts": list(ctx.get("opening_selector_selected_facts") or []),
            "opening_curated_facts": list(ctx.get("opening_curated_facts") or []),
            "opening_final_fallback_basis": list(ctx.get("opening_final_fallback_basis") or []),
            "opening_final_basis_matches_selector": bool(ctx.get("opening_final_basis_matches_selector")),
        }
        meta["opening_fallback_failed_closed"] = True
        meta["opening_fallback_context_source"] = "opening_curated_facts"
        meta["opening_fallback_missing_curated_facts"] = False
        meta.update(block_h)
        return meta
    meta = {
        "opening_fallback_context_source": "opening_curated_facts",
        "opening_fallback_basis_count": 0,
        "opening_fallback_context_missing": True,
        "opening_fallback_failed_closed": True,
        "opening_fallback_missing_curated_facts": True,
        "opening_curated_facts_present": False,
        "opening_curated_facts_count": 0,
        "opening_curated_facts_source": "selector",
        "opening_selector_source_used": "none",
        "opening_selector_selected_facts": [],
        "opening_curated_facts": [],
        "opening_final_fallback_basis": [],
        "opening_final_basis_matches_selector": True,
    }
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
            {
                "opening_fallback_context_source": "opening_curated_facts",
                "opening_fallback_basis_count": len(facts),
                "opening_fallback_context_missing": not bool(facts),
                "opening_curated_facts_present": bool(facts),
                "opening_curated_facts_count": len(facts),
                "opening_curated_facts_source": ctx.get("opening_curated_facts_source") or "selector",
                "opening_selector_source_used": ctx.get("opening_selector_source_used") or "none",
                "opening_selector_selected_facts": list(ctx.get("opening_selector_selected_facts") or []),
                "opening_curated_facts": list(ctx.get("opening_curated_facts") or []),
                "opening_final_fallback_basis": list(ctx.get("opening_final_fallback_basis") or []),
                "opening_final_basis_matches_selector": bool(ctx.get("opening_final_basis_matches_selector")),
            }
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
            {
                "opening_fallback_context_source": "opening_curated_facts",
                "opening_fallback_basis_count": len(facts),
                "opening_fallback_context_missing": not bool(facts),
                "opening_curated_facts_present": bool(facts),
                "opening_curated_facts_count": len(facts),
                "opening_curated_facts_source": ctx.get("opening_curated_facts_source") or "selector",
                "opening_selector_source_used": ctx.get("opening_selector_source_used") or "none",
                "opening_selector_selected_facts": list(ctx.get("opening_selector_selected_facts") or []),
                "opening_curated_facts": list(ctx.get("opening_curated_facts") or []),
                "opening_final_fallback_basis": list(ctx.get("opening_final_fallback_basis") or []),
                "opening_final_basis_matches_selector": bool(ctx.get("opening_final_basis_matches_selector")),
            }
        )
    return out


def _opening_scene_safe_fallback_tuple(
    gm_output: Mapping[str, Any] | None,
    *,
    fail_closed_composition_meta_factory: Callable[[], Dict[str, Any]],
) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    """Select the opening hard-replace tuple: upstream snapshot or sealed marker."""
    gm_dict = gm_output if isinstance(gm_output, dict) else None
    upstream, stub_patch = (
        _recover_upstream_opening_fallback_stub_payload(gm_dict)
        if gm_dict is not None
        else (None, {})
    )
    if upstream:
        composition_meta = dict(upstream["opening_fallback_composition_meta"])
        composition_meta.update(stub_patch)
        return (
            str(upstream["prepared_opening_fallback_text"]).strip(),
            "scene_opening_deterministic",
            "opening_deterministic_fallback",
            "opening_deterministic_fallback",
            "opening_scene_safe_fallback",
            "opening_deterministic_fallback",
            composition_meta,
        )
    classification = _opening_fallback_classification()
    if stub_patch.get("opening_fallback_upstream_payload_unusable") and stub_patch.get(
        "opening_fallback_upstream_payload_recovered"
    ) is False:
        fallback_text = OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
        fallback_meta = _opening_fail_closed_meta_upstream_stub_rebuild_failed(gm_output)
    elif _opening_maybe_attach_upstream_prepare_build_failed_on_emission_debug(gm_dict):
        fallback_text = OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
        fallback_meta = _opening_fail_closed_meta_upstream_maybe_attach_prepare_failed(gm_output)
    elif not _opening_curated_facts_have_attachable_non_empty_strings(gm_output):
        fallback_text = OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
        fallback_meta = _opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(gm_output)
    else:
        fallback_text = OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
        fallback_meta = _opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(gm_output)
    meta = fail_closed_composition_meta_factory()
    meta["fallback_family_used"] = classification.get("fallback_family")
    meta["fallback_temporal_frame"] = classification.get("temporal_frame")
    meta.update(fallback_meta)
    meta.update(stub_patch)
    meta["opening_fallback_authorship_source"] = None
    return (
        fallback_text,
        "scene_opening_deterministic",
        "opening_deterministic_fallback",
        "opening_deterministic_fallback",
        "opening_scene_safe_fallback",
        "opening_deterministic_fallback",
        meta,
    )
