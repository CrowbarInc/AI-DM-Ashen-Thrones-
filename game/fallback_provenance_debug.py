"""Upstream fast-fallback provenance packaging and overwrite-containment traces.

**BK6 stable provenance owner.** The historical ``*_debug`` module name is retained for
import stability; this module is the canonical write-time packager for upstream API
fast-fallback provenance. It does not select fallback prose, assign owner buckets,
or drive gate routing policy.

Ownership semantics:
- **Selection/application**: ``game.api`` (``_fast_fallback_for_upstream_error``)
  invokes terminal retry fallback selection before calling
  :func:`attach_upstream_fast_fallback_provenance`.
- **Provenance packaging** (this module): selector-boundary fingerprints,
  ``metadata["fallback_provenance"]`` snapshots, gate-entry/exit drift traces,
  overwrite containment, and FEM ``fallback_provenance_trace`` projection via
  :func:`record_final_emission_gate_exit`.
- **Field/ownership registry**: ``game.final_emission_meta`` (BK6).
- **Content authorship**: not individually stamped on FEM. ``content_fingerprint``
  and ``selector_player_facing_text`` are the authoritative selector-boundary
  evidence; read-side lineage may conservatively attribute content to
  ``game.gm_retry`` (terminal fallback prose selection) when projecting split
  owners.

``metadata["fallback_provenance"]`` is merged non-destructively alongside
``metadata["turn_packet"]`` and ``metadata["stage_diff_telemetry"]``; stage-diff
helpers may append ``stage_diff_last_transition`` without dropping other provenance
fields.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.final_emission_meta import (
    FEM_FALLBACK_PROVENANCE_TRACE_KEY,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN,
    UPSTREAM_FAST_FALLBACK_PROVENANCE_METADATA_KEY,
    UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER,
    UPSTREAM_FAST_FALLBACK_PROVENANCE_SELECTOR_KEYS,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    patch_final_emission_meta,
)
from game.final_emission_text import _normalize_text, _sanitize_output_text

_LOG = logging.getLogger(__name__)

# Stable import aliases (registry canonical in ``game.final_emission_meta``).
METADATA_KEY = UPSTREAM_FAST_FALLBACK_PROVENANCE_METADATA_KEY
FEM_TRACE_KEY = FEM_FALLBACK_PROVENANCE_TRACE_KEY
FALLBACK_PROVENANCE_SELECTOR_KEYS = UPSTREAM_FAST_FALLBACK_PROVENANCE_SELECTOR_KEYS
FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN = UPSTREAM_FAST_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN


def fingerprint_for_normalized_text(norm: str) -> str:
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def fingerprint_player_facing(raw: str) -> str:
    return fingerprint_for_normalized_text(_normalize_text(raw))


def attach_upstream_fast_fallback_provenance(gm: Dict[str, Any]) -> None:
    """Stamp selector-boundary provenance for upstream API fast fallback (post-repair text).

    Called by ``game.api._fast_fallback_for_upstream_error`` after terminal retry fallback
    selection. Does not select fallback prose.
    """
    if not isinstance(gm, dict):
        return
    pft = str(gm.get("player_facing_text") or "")
    fp = fingerprint_player_facing(pft)
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    prov: Dict[str, Any] = {
        "source": "fallback",
        "stage": "fallback_selector",
        "content_fingerprint": fp,
        # Canonical snapshot for Block I containment (same key namespace as fallback_provenance).
        "selector_player_facing_text": pft,
    }
    gm["metadata"] = {**md, METADATA_KEY: prov}
    preview = (pft[:120] + "…") if len(pft) > 120 else pft
    payload = {
        "event": "FALLBACK_SELECTED",
        "source": prov["source"],
        "stage": prov["stage"],
        "content_fingerprint": fp,
        "text_preview": preview,
    }
    _LOG.info("FALLBACK SELECTED %s", json.dumps(payload, default=str, ensure_ascii=False))
    print("FALLBACK SELECTED", json.dumps(payload, default=str, ensure_ascii=False))


def realign_fallback_provenance_selector_to_current_text(
    gm: Dict[str, Any],
    *,
    text: str,
    reason: str,
) -> None:
    """After an in-gate repair of upstream fast-fallback narration, refresh the Block I selector snapshot."""
    if not isinstance(gm, dict):
        return
    pft = str(text or "")
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if not isinstance(prov, dict) or str(prov.get("source") or "") != "fallback":
        return
    fp = fingerprint_player_facing(pft)
    prov2 = {
        **prov,
        "selector_player_facing_text": pft,
        "content_fingerprint": fp,
        "selector_realigned_reason": str(reason or "").strip() or "unknown",
    }
    gm["metadata"] = {**md, METADATA_KEY: prov2}


def preserve_fallback_provenance_metadata(dst: Dict[str, Any], *sources: Optional[Dict[str, Any]]) -> None:
    """If *dst* lacks ``fallback_provenance``, copy from the first *sources* dict that has it."""
    if not isinstance(dst, dict):
        return
    md_dst = dst.get("metadata") if isinstance(dst.get("metadata"), dict) else {}
    existing = md_dst.get(METADATA_KEY) if isinstance(md_dst.get(METADATA_KEY), dict) else None
    if existing and str(existing.get("source") or "") == "fallback":
        return
    for src in sources:
        if not isinstance(src, dict):
            continue
        md_src = src.get("metadata") if isinstance(src.get("metadata"), dict) else {}
        prov = md_src.get(METADATA_KEY)
        if isinstance(prov, dict) and str(prov.get("source") or "") == "fallback":
            dst["metadata"] = {**md_dst, METADATA_KEY: dict(prov)}
            return


def record_final_emission_gate_entry(out: Dict[str, Any]) -> None:
    """Compare current ``player_facing_text`` fingerprint to selector fingerprint (gate ingress)."""
    if not isinstance(out, dict):
        return
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if not isinstance(prov, dict) or str(prov.get("source") or "") != "fallback":
        return
    original_fp = str(prov.get("content_fingerprint") or "")
    original_stage = str(prov.get("stage") or "fallback_selector")
    entry_fp = fingerprint_player_facing(str(out.get("player_facing_text") or ""))
    entry_match = bool(original_fp) and entry_fp == original_fp
    prov = {
        **prov,
        "gate_entry_fingerprint": entry_fp,
        "gate_entry_vs_selector_match": entry_match,
        "stage_diff_gate_stage": "final_emission_gate_entry",
    }
    out["metadata"] = {**md, METADATA_KEY: prov}
    if not entry_match and original_fp:
        msg = {
            "event": "OVERWRITE_DETECTED",
            "mismatch_detected": True,
            "original_stage": original_stage,
            "current_stage": "final_emission_gate_entry",
            "original_fingerprint": original_fp,
            "current_fingerprint": entry_fp,
        }
        _LOG.warning("OVERWRITE DETECTED %s", json.dumps(msg, default=str, ensure_ascii=False))
        print("OVERWRITE DETECTED", json.dumps(msg, default=str, ensure_ascii=False))


def record_final_emission_gate_exit(out: Dict[str, Any], *, final_normalized_text: str) -> None:
    """Compare final emitted fingerprint to selector; classify pre-gate vs in-gate vs finalize."""
    if not isinstance(out, dict):
        return
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov_in = md.get(METADATA_KEY)
    if not isinstance(prov_in, dict) or str(prov_in.get("source") or "") != "fallback":
        return
    prev = dict(prov_in)
    original_fp = str(prev.get("content_fingerprint") or "")
    original_stage = str(prev.get("stage") or "fallback_selector")
    exit_fp = fingerprint_for_normalized_text(final_normalized_text)
    entry_fp = str(prev.get("gate_entry_fingerprint") or "")
    entry_match = bool(prev.get("gate_entry_vs_selector_match"))
    exit_vs_selector = bool(original_fp) and exit_fp == original_fp
    mutation_hint: str | None = None
    mismatch_detected = False

    if original_fp and not exit_vs_selector:
        current_stage = "final_emission_gate_exit"
        if not entry_match:
            hint = "mutation_before_or_during_gate_entry"
        elif entry_fp and exit_fp != entry_fp:
            hint = "mutation_inside_gate_or_finalize"
        else:
            hint = "mutation_unknown"
        mutation_hint = hint
        mismatch_detected = True
        msg = {
            "event": "OVERWRITE_DETECTED",
            "mismatch_detected": True,
            "original_stage": original_stage,
            "current_stage": current_stage,
            "original_fingerprint": original_fp,
            "current_fingerprint": exit_fp,
            "gate_entry_fingerprint": entry_fp or None,
            "gate_entry_vs_selector_match": entry_match,
            "mutation_hint": hint,
        }
        _LOG.warning("OVERWRITE DETECTED %s", json.dumps(msg, default=str, ensure_ascii=False))
        print("OVERWRITE DETECTED", json.dumps(msg, default=str, ensure_ascii=False))

    prov = {
        **prev,
        "gate_exit_fingerprint": exit_fp,
        "gate_exit_vs_selector_match": exit_vs_selector,
        "mutation_hint": mutation_hint,
        "mismatch_detected": mismatch_detected,
    }
    out["metadata"] = {**md, METADATA_KEY: prov}
    patch_final_emission_meta(out, {FEM_TRACE_KEY: dict(prov)})


def upstream_fallback_canonical_provenance(out: Dict[str, Any]) -> Dict[str, Any] | None:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if isinstance(prov, dict) and str(prov.get("source") or "") == "fallback":
        return prov
    return None


def apply_upstream_fallback_pregate_containment(out: Dict[str, Any]) -> bool:
    """When canonical provenance shows gate-entry drift vs selector, restore selector text (Block I)."""
    prov = upstream_fallback_canonical_provenance(out)
    if not prov:
        return False
    original_fp = str(prov.get("content_fingerprint") or "")
    if not original_fp or prov.get("gate_entry_vs_selector_match") is not False:
        return False
    snap = str(prov.get("selector_player_facing_text") or "")
    if not snap or fingerprint_player_facing(snap) != original_fp:
        return False
    assert_final_emission_mutation_allowed(
        "preserve_candidate_text",
        source="game.fallback_provenance_debug.apply_upstream_fallback_pregate_containment",
    )
    out["player_facing_text"] = snap
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov2 = dict(md.get(METADATA_KEY) or prov)
    prov2["overwrite_containment_applied"] = "pre_gate"
    out["metadata"] = {**md, METADATA_KEY: prov2}
    print("FALLBACK OVERWRITE CONTAINED: pre-gate")
    record_final_emission_gate_entry(out)
    return True


def finalize_upstream_fallback_overwrite_containment(
    out: Dict[str, Any],
    *,
    pre_gate_normalized: str,
) -> bool:
    """When exit trace proves post-selector divergence, revert to selector snapshot with sanitizer-only cleanup."""
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if not isinstance(prov, dict) or str(prov.get("source") or "") != "fallback":
        return False
    if not prov.get("mismatch_detected"):
        return False
    hint = str(prov.get("mutation_hint") or "")
    if hint not in FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN:
        return False
    snap = str(prov.get("selector_player_facing_text") or "")
    original_fp = str(prov.get("content_fingerprint") or "")
    if not snap or not original_fp or fingerprint_player_facing(snap) != original_fp:
        return False
    assert_final_emission_mutation_allowed(
        "sanitize_html_to_text",
        source="game.fallback_provenance_debug.finalize_upstream_fallback_overwrite_containment",
    )
    snap_san = _sanitize_output_text(snap)
    if fingerprint_player_facing(snap_san) == original_fp:
        chosen = snap_san
    elif fingerprint_player_facing(snap) == original_fp:
        chosen = snap
    else:
        chosen = snap_san
    assert_final_emission_mutation_allowed(
        "preserve_candidate_text",
        source="game.fallback_provenance_debug.finalize_upstream_fallback_overwrite_containment",
    )
    out["player_facing_text"] = chosen
    gate_norm = _normalize_text(chosen)
    contained_kind = (
        "in_gate_finalize"
        if hint in ("mutation_inside_gate_or_finalize", "mutation_unknown")
        else "pre_gate"
    )
    patch_final_emission_meta(
        out,
        {
            "fallback_overwrite_contained": contained_kind,
            "fallback_overwrite_finalize_containment": True,
            "post_gate_mutation_detected": pre_gate_normalized != gate_norm,
            "final_text_preview": (gate_norm[:120] + "…") if len(gate_norm) > 120 else gate_norm,
        },
    )
    print(
        "FALLBACK OVERWRITE CONTAINED: in-gate/finalize"
        if contained_kind == "in_gate_finalize"
        else "FALLBACK OVERWRITE CONTAINED: pre-gate"
    )
    record_final_emission_gate_exit(out, final_normalized_text=gate_norm)
    md2 = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov3 = dict(md2.get(METADATA_KEY) or {})
    prov3["overwrite_containment_applied"] = contained_kind
    out["metadata"] = {**md2, METADATA_KEY: prov3}
    return True


__all__ = [
    "METADATA_KEY",
    "FEM_TRACE_KEY",
    "FALLBACK_PROVENANCE_SELECTOR_KEYS",
    "FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN",
    "UPSTREAM_FAST_FALLBACK_SELECTION_OWNER",
    "UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER",
    "UPSTREAM_FAST_FALLBACK_CONTENT_OWNER",
    "fingerprint_for_normalized_text",
    "fingerprint_player_facing",
    "attach_upstream_fast_fallback_provenance",
    "realign_fallback_provenance_selector_to_current_text",
    "preserve_fallback_provenance_metadata",
    "record_final_emission_gate_entry",
    "record_final_emission_gate_exit",
    "upstream_fallback_canonical_provenance",
    "apply_upstream_fallback_pregate_containment",
    "finalize_upstream_fallback_overwrite_containment",
]
