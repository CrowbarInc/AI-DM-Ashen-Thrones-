"""Scene state anchor contract resolution, metadata, apply layer, and rebind helpers.

Pure contract read paths, FEM metadata shapes, skip predicates, opening-tether
repair helpers, and gate-layer apply orchestration.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List

from game.final_emission_text import _normalize_text
from game.scene_state_anchoring import validate_scene_state_anchoring


def _resolve_scene_state_anchor_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Read the shipped contract from *gm_output* / narration payload copies only (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None
    direct = gm_output.get("scene_state_anchor_contract")
    if isinstance(direct, dict):
        return direct
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if isinstance(pl, dict):
            sac = pl.get("scene_state_anchor_contract")
            if isinstance(sac, dict):
                return sac
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        sac = md.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        sac = tr.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    return None


def _resolve_scene_state_anchor_debug(gm_output: Dict[str, Any] | None) -> Dict[str, Any]:
    """Compact upstream summary (e.g. gm emission_debug.scene_state_anchor) for metadata merge."""
    if not isinstance(gm_output, dict):
        return {}
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            dbg = em.get("scene_state_anchor")
            if isinstance(dbg, dict):
                return dict(dbg)
    return {}


def _default_scene_state_anchor_meta(
    skip: str | None,
    upstream_debug: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "scene_state_anchor_checked": False,
        "scene_state_anchor_passed": False,
        "scene_state_anchor_failed": False,
        "scene_state_anchor_skip_reason": skip,
        "scene_state_anchor_matched_kinds": [],
        "scene_state_anchor_failure_reasons": [],
        "scene_state_anchor_repaired": False,
        "scene_state_anchor_repair_mode": None,
        "scene_state_anchor_upstream_debug": dict(upstream_debug),
    }


def _merge_scene_state_anchor_meta(meta: Dict[str, Any], ssa_dbg: Dict[str, Any]) -> None:
    if not ssa_dbg:
        return
    keys = (
        "scene_state_anchor_checked",
        "scene_state_anchor_passed",
        "scene_state_anchor_failed",
        "scene_state_anchor_skip_reason",
        "scene_state_anchor_matched_kinds",
        "scene_state_anchor_failure_reasons",
        "scene_state_anchor_repaired",
        "scene_state_anchor_repair_mode",
        "scene_state_anchor_upstream_debug",
    )
    for k in keys:
        if k in ssa_dbg:
            meta[k] = ssa_dbg[k]


def _merge_scene_state_anchor_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    """Attach gate fields and preserve/merge compact upstream ``scene_state_anchor`` summaries."""
    upstream: Any = None
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("scene_state_anchor_"):
            continue
        if k == "scene_state_anchor_upstream_debug":
            upstream = v
            continue
        flat[k] = v
    if not flat and not (isinstance(upstream, dict) and upstream):
        return

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        base = em.get("scene_state_anchor")
        if isinstance(upstream, dict) and upstream:
            if isinstance(base, dict):
                merged = {**upstream, **base}
            else:
                merged = dict(upstream)
            em["scene_state_anchor"] = merged
        for fk, fv in flat.items():
            em[fk] = fv

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def _skip_scene_state_anchor_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not isinstance(contract, dict):
        return "missing_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            return "strict_social_structured_or_bridge_source"
    return None


def apply_scene_state_anchor_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    contract = _resolve_scene_state_anchor_contract(gm_output)
    upstream = _resolve_scene_state_anchor_debug(gm_output)
    norm = _normalize_text(text).strip()
    tags_ssa = [str(t) for t in (gm_output.get("tags") or []) if isinstance(t, str)]
    dbg_ssa = str(gm_output.get("debug_notes") or "")
    if norm and re.fullmatch(r"\[[^\]]{1,120}\]", norm):
        meta = _default_scene_state_anchor_meta("bracketed_production_stub", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "bracketed_production_stub"
        return text, meta
    if "known_fact_guard" in tags_ssa and "recent_dialogue_continuity" in dbg_ssa:
        meta = _default_scene_state_anchor_meta("known_fact_recent_dialogue_continuity", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "known_fact_recent_dialogue_continuity"
        return text, meta
    skip = _skip_scene_state_anchor_layer(
        text,
        contract,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
    )
    meta = _default_scene_state_anchor_meta(skip, upstream)
    if skip:
        return text, meta

    assert contract is not None
    v0 = validate_scene_state_anchoring(text, contract)
    meta["scene_state_anchor_checked"] = bool(v0.get("checked"))
    meta["scene_state_anchor_passed"] = bool(v0.get("passed"))
    meta["scene_state_anchor_matched_kinds"] = list(v0.get("matched_anchor_kinds") or [])
    meta["scene_state_anchor_failure_reasons"] = list(v0.get("failure_reasons") or [])
    if v0.get("passed"):
        return text, meta

    meta["scene_state_anchor_boundary_semantic_repair_disabled"] = True
    meta["scene_state_anchor_failed"] = True
    meta["scene_state_anchor_repaired"] = False
    meta["scene_state_anchor_repair_mode"] = None
    return text, meta


def _title_case_anchor_phrase(phrase: str) -> str:
    parts = [p for p in str(phrase or "").strip().split() if p]
    if not parts:
        return ""
    out: List[str] = []
    for w in parts:
        if not w:
            continue
        out.append(w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return " ".join(out)


def _opening_has_token_hint(text: str, token_lower: str) -> bool:
    if not token_lower or not str(text or "").strip():
        return False
    low = str(text).lower()
    head = low[: min(len(low), 280)]
    if " " in token_lower:
        return token_lower in head
    return bool(re.search(rf"(?<!\w){re.escape(token_lower)}(?!\w)", head))


def _pick_actor_token(actor_tokens: Sequence[Any]) -> str | None:
    for raw in actor_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3 and not s.isdigit():
            return s
    return None


def _pick_action_tether_token(player_action_tokens: Sequence[Any]) -> str | None:
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if " " in s and 5 <= len(s) <= 96:
            return s
    skip_one = frozenset({"question", "answer", "observe", "investigate", "action", "kind"})
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 4 and s not in skip_one:
            return s
    return None


def _pick_location_phrase(contract: Mapping[str, Any]) -> str | None:
    lab = str(contract.get("scene_location_label") or "").strip()
    if lab and len(lab) >= 2:
        return lab.lower()
    for raw in contract.get("location_tokens") or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3:
            return s
    return None


def _repair_actor_opening(text: str, actor_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_actor_token(actor_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    display = _title_case_anchor_phrase(tok)
    if not display:
        return None, None
    return _normalize_text(f"{display} {text}"), "actor_rebind"


def _repair_action_tether(text: str, player_action_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_action_tether_token(player_action_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    lead = _title_case_anchor_phrase(tok) if " " in tok else tok.capitalize()
    return _normalize_text(f"{lead} — {text}"), "action_rebind"


def _repair_location_opening(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"At {disp}, {text}"), "location_rebind"


def _repair_narrator_neutral_location(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"Here at {disp}, {text}"), "narrator_neutral_scene_rebind"


def _repair_scene_state_anchor_minimal(
    text: str,
    contract: Mapping[str, Any],
    *,
    gm_output: Dict[str, Any] | None = None,
    strict_social_details: Dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Opening-tether repairs only; uses contract token buckets (no new facts)."""
    tags_ssa = [str(t) for t in ((gm_output or {}).get("tags") or []) if isinstance(t, str)]
    fast_fallback_neutral = (
        not strict_social_details
        and any(tag in tags_ssa for tag in ("upstream_api_fast_fallback", "forced_retry_fallback", "retry_escape_hatch"))
    )
    actors = list(contract.get("actor_tokens") or [])
    actions = list(contract.get("player_action_tokens") or [])
    if not fast_fallback_neutral:
        # Repair ladder: A actor → B action → C location → D narrator-neutral + location.
        r, mode = _repair_actor_opening(text, actors)
        if r:
            return r, mode
        r, mode = _repair_action_tether(text, actions)
        if r:
            return r, mode
    r, mode = _repair_location_opening(text, contract)
    if r:
        return r, mode
    r, mode = _repair_narrator_neutral_location(text, contract)
    if r:
        return r, mode
    return None, None
