"""Temporary debug instrumentation: upstream fast-fallback fingerprint + overwrite tracing.

Not used for selection or narration — only logging and metadata markers.

Metadata under ``fallback_provenance`` is merged non-destructively alongside
``metadata["turn_packet"]`` and ``metadata["stage_diff_telemetry"]``; stage-diff
helpers may append ``stage_diff_last_transition`` without dropping other provenance
fields.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from game.final_emission_text import _normalize_text
from game.final_emission_meta import patch_final_emission_meta

_LOG = logging.getLogger(__name__)

METADATA_KEY = "fallback_provenance"


def fingerprint_for_normalized_text(norm: str) -> str:
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def fingerprint_player_facing(raw: str) -> str:
    return fingerprint_for_normalized_text(_normalize_text(raw))


def attach_upstream_fast_fallback_provenance(gm: Dict[str, Any]) -> None:
    """Mark GM output from :func:`game.api` upstream API fast fallback (post-repair text)."""
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
    patch_final_emission_meta(out, {"fallback_provenance_trace": dict(prov)})
