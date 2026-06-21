"""Final emission packaging: sanitize, strip, FEM refresh, provenance containment, sidecars.

Last-mile player text normalization and fast-path eligibility owned here. Exit stacks
call :func:`finalize_emission_output` and :func:`final_emission_fast_path_eligible` directly.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping
from typing import Any, Dict

from game.fallback_provenance_debug import (
    finalize_upstream_fallback_overwrite_containment,
    record_final_emission_gate_exit,
)
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.final_emission_opening_fallback import reassert_scene_opening_accepted_candidate
from game.final_emission_meta import (
    ensure_final_emission_meta_dict,
    package_dead_turn_snapshot_into_final_emission_meta,
    package_emission_channel_sidecar,
    patch_final_emission_meta,
    refresh_final_emission_mutation_lineage,
)
from game.final_emission_text_formatting import (
    _normalize_text,
    _sanitize_output_text,
)
from game.final_emission_validators import _split_sentences_answer_complete
from game.stage_diff_telemetry import record_stage_snapshot
from game.state_channels import project_author_payload, project_debug_payload, project_public_payload


_GLOBAL_VISIBILITY_PLACEHOLDER_STOCK_RES: tuple[re.Pattern[str], ...] = (
    # Mirrors ``_global_narrative_fallback_stock_line`` and the empty-sanitizer stock in output_sanitizer.
    re.compile(
        r"^for\s+a\s+breath,?\s+the\s+scene\s+holds\s+while\s+voices\s+shift\s+around\s+you\.?$",
        re.IGNORECASE,
    ),
    re.compile(r"^for\s+a\s+breath,?\s+the\s+scene\s+stays\s+still\.?$", re.IGNORECASE),
)


def _sentence_is_global_visibility_placeholder_stock(sentence: str) -> bool:
    """True only for the known global visibility stock *sentence* (not quoted 'for a breath' asides)."""
    t = _normalize_text(str(sentence or "").strip()).rstrip(".!?").strip()
    if not t:
        return False
    return any(p.match(t) for p in _GLOBAL_VISIBILITY_PLACEHOLDER_STOCK_RES)


def strip_appended_route_illegal_contamination_sentences(text: str) -> str:
    """Drop matching global-visibility stock sentences when other sentences remain in the same block.

    Late-stage composition often appends ``_global_narrative_fallback_stock_line`` as its own sentence
    after valid narration; the same patterns may appear as a non-final sentence in a contaminated
    bundle. Strict-social paths reject this family upstream; generic narration relies on this
    helper from :func:`finalize_emission_output` so mixed bundles never reach players. Per-block
    single-sentence outputs are left unchanged. Paragraph breaks (``\\n\\n``) are preserved.
    """
    raw = str(text or "").strip()
    if not raw:
        return raw
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if not blocks:
        return raw
    out_blocks: list[str] = []
    changed = False
    for block in blocks:
        sents = [s.strip() for s in _split_sentences_answer_complete(block) if str(s).strip()]
        if len(sents) <= 1:
            out_blocks.append(block)
            continue
        kept = [s for s in sents if not _sentence_is_global_visibility_placeholder_stock(s)]
        if not kept or len(kept) == len(sents):
            out_blocks.append(block)
            continue
        changed = True
        out_blocks.append(_normalize_text(" ".join(kept)))
    if not changed:
        return raw
    return "\n\n".join(out_blocks).strip()


def _refresh_output_mutation_lineage(out: Mapping[str, Any] | None) -> None:
    if not isinstance(out, MutableMapping):
        return
    meta = ensure_final_emission_meta_dict(out)
    md = out.get("metadata") if isinstance(out.get("metadata"), Mapping) else {}
    sanitizer_trace = md.get("sanitizer_trace") if isinstance(md.get("sanitizer_trace"), Mapping) else None
    from game.final_emission_meta import apply_sanitizer_producer_attribution_to_fem

    apply_sanitizer_producer_attribution_to_fem(meta, sanitizer_trace)
    refresh_final_emission_mutation_lineage(meta, sanitizer_trace=sanitizer_trace)


def final_emission_fast_path_eligible(out: Dict[str, Any]) -> bool:
    if not isinstance(out, dict):
        return False
    meta = ensure_final_emission_meta_dict(out)
    if meta.get("final_route") != "accept_candidate":
        return False
    if meta.get("response_type_candidate_ok") is False:
        return False
    if (
        meta.get("answer_completeness_failed")
        or meta.get("narrative_authority_failed")
        or meta.get("narrative_authenticity_failed")
    ):
        return False
    if meta.get("fallback_behavior_failed") or meta.get("fallback_behavior_repaired"):
        return False
    if meta.get("fallback_behavior_uncertainty_active"):
        return False
    if meta.get("response_type_repair_used"):
        return False
    if any(
        meta.get(key)
        for key in (
            "answer_completeness_repaired",
            "response_delta_repaired",
            "social_response_structure_repair_applied",
            "narrative_authenticity_repaired",
            "tone_escalation_repaired",
            "anti_railroading_repaired",
            "context_separation_repaired",
            "player_facing_narration_purity_repaired",
            "answer_shape_primacy_repaired",
            "candidate_quality_degraded",
        )
    ):
        return False
    if str(meta.get("speaker_contract_enforcement_reason") or "").strip():
        return False
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    if any(
        ("fallback" in tag) or ("retry" in tag)
        for tag in tags
    ):
        return False
    icv = meta.get("interaction_continuity_validation")
    if not isinstance(icv, dict):
        md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
        icv = em.get("interaction_continuity_validation")
    if isinstance(icv, dict) and icv.get("ok") is False:
        return False
    return True


def finalize_emission_output(
    out: Dict[str, Any],
    *,
    pre_gate_text: str,
    fast_path: bool = False,
    scene_emit_integrity_bundle: Dict[str, Any] | None = None,
    accepted_scene_opening_text: str | None = None,
) -> Dict[str, Any]:
    if isinstance(out, dict):
        record_stage_snapshot(out, "final_emission_gate_exit")
    out.pop("_gate_turn_packet_cache", None)
    final_text = str(out.get("player_facing_text") or "")
    assert_final_emission_mutation_allowed(
        "sanitize_html_to_text",
        source="gate._finalize_emission_output",
    )
    sanitized_text = _sanitize_output_text(final_text)
    if fast_path:
        smoothed_text = sanitized_text
        fragment_repair_applied = False
        sentence_decompression_applied = False
        sentence_micro_smoothing_applied = False
    else:
        # C2 Block C: no decompress / participial / micro-smooth semantic finalize at the boundary.
        smoothed_text = sanitized_text
        fragment_repair_applied = False
        sentence_decompression_applied = False
        sentence_micro_smoothing_applied = False
    assert_final_emission_mutation_allowed(
        "strip_route_illegal_contamination",
        source="gate._finalize_emission_output",
    )
    pre_route_strip_text = smoothed_text
    smoothed_text = strip_appended_route_illegal_contamination_sentences(smoothed_text)
    route_illegal_strip_applied = smoothed_text != pre_route_strip_text
    sanitization_applied = sanitized_text != final_text
    assert_final_emission_mutation_allowed(
        "normalize_whitespace",
        source="gate._finalize_emission_output.assign",
    )
    out["player_facing_text"] = smoothed_text

    gate_out_text = _normalize_text(smoothed_text)
    meta = ensure_final_emission_meta_dict(out)
    if isinstance(scene_emit_integrity_bundle, dict) and scene_emit_integrity_bundle:
        meta.update(dict(scene_emit_integrity_bundle))
    meta.update(
        {
            "final_emission_fast_path_used": bool(fast_path),
            "output_sanitization_applied": sanitization_applied,
            "finalize_route_illegal_strip_applied": route_illegal_strip_applied,
            "sentence_decompression_applied": sentence_decompression_applied,
            "sentence_fragment_repair_applied": fragment_repair_applied,
            "sentence_micro_smoothing_applied": sentence_micro_smoothing_applied,
            "final_emission_boundary_semantic_repair_disabled": True,
            "final_emission_finalize_semantic_repair_used": False,
            "final_emission_semantic_repair_skip_reason": "finalize_packaging_only_no_sentence_recompose",
            "post_gate_mutation_detected": pre_gate_text != gate_out_text,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
        }
    )
    _refresh_output_mutation_lineage(out)
    record_final_emission_gate_exit(out, final_normalized_text=gate_out_text)
    finalize_upstream_fallback_overwrite_containment(out, pre_gate_normalized=pre_gate_text)
    # Block I containment restores the upstream selector snapshot when exit fingerprints diverge.
    # Legitimate finalize-time edits (including appended stock removal) must not be undone, so
    # re-apply the same narrow strip as the absolute last write on ``player_facing_text``.
    pre_seal = str(out.get("player_facing_text") or "")
    assert_final_emission_mutation_allowed(
        "strip_route_illegal_contamination",
        source="gate._finalize_emission_output.reseal",
    )
    sealed = strip_appended_route_illegal_contamination_sentences(pre_seal)
    if sealed != pre_seal:
        assert_final_emission_mutation_allowed(
            "normalize_whitespace",
            source="gate._finalize_emission_output.reseal_assign",
        )
        out["player_facing_text"] = sealed
        gate_norm_final = _normalize_text(sealed)
        patch_final_emission_meta(
            out,
            {
                "post_gate_mutation_detected": pre_gate_text != gate_norm_final,
                "finalize_route_illegal_strip_applied": True,
                "final_text_preview": (gate_norm_final[:120] + "…") if len(gate_norm_final) > 120 else gate_norm_final,
            },
        )
    reassert_scene_opening_accepted_candidate(
        out,
        accepted_scene_opening_text=accepted_scene_opening_text,
        source="gate._finalize_emission_output.scene_opening_candidate_reseal",
    )
    package_dead_turn_snapshot_into_final_emission_meta(out)
    debug_lane = project_debug_payload(out)
    author_lane = project_author_payload(out)
    public_out = project_public_payload(out)
    sidecar = package_emission_channel_sidecar(debug_top_level=debug_lane, author_top_level=author_lane)
    if sidecar:
        public_out["internal_state"] = sidecar
    return public_out
