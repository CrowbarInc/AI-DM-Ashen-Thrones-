"""Speaker selection contract: validation, repair, metadata, and sync helpers.

Live strict-social orchestration (when enforcement runs, and relative to other gate layers)
remains in :mod:`game.final_emission_gate` (:func:`~game.final_emission_gate.apply_final_emission_gate`).
This module owns the speaker-contract implementation surface consumed by that orchestrator;
emitted text signature parsing lives in :mod:`game.emitted_speaker_signature`.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Optional

from game.emitted_speaker_signature import detect_emitted_speaker_signature
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS, neutral_reply_speaker_grounding_bridge_line
from game.social_exchange_emission import (
    _has_explicit_interruption_shape,
    _npc_display_name_for_emission,
    interruption_cue_present_in_text,
    strict_social_ownership_terminal_fallback,
)
from game.final_emission_text import _normalize_text

_SPEAKER_REASON_SPEAKER_CONTRACT_MATCH = "speaker_contract_match"
_SPEAKER_REASON_SPEAKER_BINDING_MISMATCH = "speaker_binding_mismatch"
_SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER = "forbidden_generic_fallback_speaker"
_SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH = "unjustified_speaker_switch"
_SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT = "interruption_without_contract_support"
_SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH = "interruption_justified_switch"
_SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR = "continuity_locked_speaker_repair"
_SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE = "canonical_speaker_rewrite"
_SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER = "narrator_neutral_no_allowed_speaker"

SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES: tuple[str, ...] = (
    _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
    _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
    _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
    _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
    _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
    _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
    _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR,
    _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE,
    _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
)

# Gate continuity-bridge comparisons (same token as enforcement taxonomy).
SPEAKER_REASON_SPEAKER_BINDING_MISMATCH = _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH

_SPEECH_VERB_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|asks|asked|adds|added)\b",
    re.IGNORECASE,
)
_BEAT_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
# Leading "…" dialogue + pronoun + attribution verb: label is the pronoun only (not the quoted span).
_QUOTED_THEN_PRONOUN_SPEECH_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|"
    r"asks|asked|adds|added|insists|insisted)\b",
    re.IGNORECASE,
)
_QUOTED_THEN_PRONOUN_BEAT_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
_NON_NAME_ATTRIBUTION_PREFIXES = frozenset(
    {
        "he",
        "she",
        "they",
        "it",
        "someone",
        "a voice",
        "the voice",
        "another voice",
    }
)


def _stable_seed_fingerprint(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:12]


def _empty_speaker_selection_contract() -> Dict[str, Any]:
    return {
        "primary_speaker_id": None,
        "primary_speaker_name": None,
        "allowed_speaker_ids": [],
        "continuity_locked": False,
        "continuity_lock_reason": None,
        "speaker_switch_allowed": True,
        "speaker_switch_reason": None,
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "generic_fallback_forbidden": False,
        "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": True},
    }


def get_speaker_selection_contract(
    resolution: Dict[str, Any] | None,
    metadata: Dict[str, Any] | None = None,
    trace: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Load Block 1 speaker contract: metadata emission_debug first, then resolution/trace copies."""
    empty = _empty_speaker_selection_contract()

    def _from_emission_debug(em: Any) -> Dict[str, Any] | None:
        if not isinstance(em, dict):
            return None
        c = em.get("speaker_selection_contract")
        return c if isinstance(c, dict) and c else None

    if isinstance(metadata, dict):
        hit = _from_emission_debug(metadata.get("emission_debug"))
        if hit is not None:
            return hit

    if isinstance(resolution, dict):
        md = resolution.get("metadata")
        if isinstance(md, dict):
            hit = _from_emission_debug(md.get("emission_debug"))
            if hit is not None:
                return hit

    if isinstance(trace, dict):
        tc = trace.get("speaker_selection_contract")
        if isinstance(tc, dict) and tc:
            return tc
        hit = _from_emission_debug(trace.get("emission_debug"))
        if hit is not None:
            return hit

    return empty


def _display_from_npc_id(npc_id: str | None) -> str:
    s = str(npc_id or "").strip()
    if not s:
        return ""
    return s.replace("_", " ").replace("-", " ").title()


def _label_matches_primary_speaker(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    if not str(label or "").strip():
        return False
    low = label.strip().lower()
    pn = str(contract.get("primary_speaker_name") or "").strip().lower()
    pid = str(contract.get("primary_speaker_id") or "").strip()
    pid_disp = _display_from_npc_id(pid).lower()
    if pn and low == pn:
        return True
    if pid_disp and low == pid_disp:
        return True
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        rn = str(soc.get("npc_name") or "").strip().lower()
        rid = _display_from_npc_id(str(soc.get("npc_id") or "")).lower()
        if rn and low == rn:
            return True
        if rid and low == rid:
            return True
    return False


def _label_in_allowed_speaker_ids(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    allowed = contract.get("allowed_speaker_ids")
    if not isinstance(allowed, list) or not allowed:
        return False
    low = label.strip().lower()
    for aid in allowed:
        disp = _display_from_npc_id(str(aid or "").strip()).lower()
        if disp and low == disp:
            return True
    pid = str(contract.get("primary_speaker_id") or "").strip()
    if pid in allowed and _label_matches_primary_speaker(label, contract, resolution):
        return True
    return False


def _emitted_invents_dialogue_ownership(text: str) -> bool:
    t = _normalize_text(text)
    if not t:
        return False
    if '"' in t:
        return True
    return bool(
        re.search(
            r"\b(?:says|replies|answers|mutters|whispers|asks|shakes|shrugs|frowns|grimaces)\b",
            t,
            re.IGNORECASE,
        )
    )


def _explicit_interruption_scene_event_framing(text: str) -> bool:
    return bool(_has_explicit_interruption_shape(_normalize_text(text)))


def validate_emitted_speaker_against_contract(
    text: str,
    speaker_selection: Dict[str, Any],
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Contract-first validation of final text vs Block 1 speaker_selection_contract."""
    c = speaker_selection if isinstance(speaker_selection, dict) else {}
    res = resolution if isinstance(resolution, dict) else None
    details: Dict[str, Any] = {"signature": detect_emitted_speaker_signature(text, res)}

    if isinstance(c.get("debug"), dict) and c["debug"].get("contract_missing"):
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": c.get("primary_speaker_id"),
            "canonical_speaker_name": c.get("primary_speaker_name"),
            "repair_mode": "none",
            "details": {**details, "skipped": "no_contract"},
        }

    allowed = [str(x).strip() for x in (c.get("allowed_speaker_ids") or []) if str(x).strip()]
    primary_id = str(c.get("primary_speaker_id") or "").strip() or None
    primary_name = str(c.get("primary_speaker_name") or "").strip() or None
    continuity_locked = bool(c.get("continuity_locked"))
    gen_ff = bool(c.get("generic_fallback_forbidden"))
    sw_ok = bool(c.get("speaker_switch_allowed"))
    intr_ok = bool(c.get("interruption_allowed"))
    intr_scene = bool(c.get("interruption_requires_scene_event"))
    offscene_forbid = bool(c.get("offscene_speakers_forbidden"))

    sig = details["signature"]
    label = str(sig.get("speaker_label") or "").strip()
    explicit = bool(sig.get("is_explicitly_attributed"))
    intr = bool(sig.get("has_interruption_framing"))
    explicit_scene = _explicit_interruption_scene_event_framing(text)

    canonical_id = primary_id
    canonical_name = primary_name
    if not canonical_name and res is not None:
        soc0 = res.get("social") if isinstance(res.get("social"), dict) else {}
        canonical_name = str(soc0.get("npc_name") or "").strip() or None
    if not canonical_name and primary_id:
        canonical_name = _display_from_npc_id(primary_id)

    # (b) Generic fallback speaker
    if gen_ff:
        flist = (
            c.get("forbidden_fallback_labels")
            if isinstance(c.get("forbidden_fallback_labels"), list)
            else list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
        )
        low_lab = label.lower() if label else ""
        hit = bool(sig.get("is_generic_fallback_label"))
        if explicit and low_lab and not hit:
            for fb in flist:
                fbs = str(fb or "").strip().lower()
                if fbs and (fbs == low_lab or fbs in low_lab or low_lab in fbs):
                    hit = True
                    break
        if hit:
            rm = "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral"
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "generic_fallback_forbidden"},
            }

    # Interruption policy (third-party / scene break)
    if intr:
        if not (sw_ok and intr_ok):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_not_permitted"},
            }
        # Continuity-locked strict-social: require explicit join only when dialogue ownership
        # is present (quoted speech or clear attribution), matching mixed-blob rejection policy.
        tnorm = _normalize_text(text)
        if intr_scene and not explicit_scene and ('"' in tnorm or explicit):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_requires_scene_event"},
            }

    # (e) No speaker allowed but dialogue ownership invented
    if not allowed:
        if _emitted_invents_dialogue_ownership(text):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
                "canonical_speaker_id": None,
                "canonical_speaker_name": None,
                "repair_mode": "narrator_neutral",
                "details": {**details, "rule": "no_allowed_speaker_dialogue"},
            }
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    # (a) Continuity locked + wrong explicit speaker
    if continuity_locked and explicit and label:
        if not _label_in_allowed_speaker_ids(label, c, res):
            if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
                return {
                    "ok": True,
                    "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                    "canonical_speaker_id": canonical_id,
                    "canonical_speaker_name": canonical_name,
                    "repair_mode": "none",
                    "details": {**details, "rule": "interruption_overrides_explicit_mismatch"},
                }
            salvage = bool(re.search(r"\"[^\"]{2,}\"", _normalize_text(text)))
            rm = "local_rebind" if (canonical_name and salvage) else ("canonical_rewrite" if canonical_id else "narrator_neutral")
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "continuity_locked_explicit_mismatch"},
            }

    # (c) New speaker not permitted
    if explicit and label and not _label_in_allowed_speaker_ids(label, c, res):
        if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
            return {
                "ok": True,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "none",
                "details": {**details, "rule": "switch_permitted_interruption"},
            }
        if not sw_ok:
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
                "details": {**details, "rule": "speaker_switch_disallowed"},
            }
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "unlisted_explicit_speaker"},
        }

    if offscene_forbid and explicit and label and not _label_in_allowed_speaker_ids(label, c, res) and not intr:
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "offscene_speakers_forbidden"},
        }

    if intr:
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    return {
        "ok": True,
        "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
        "canonical_speaker_id": canonical_id,
        "canonical_speaker_name": canonical_name,
        "repair_mode": "none",
        "details": details,
    }


def _try_local_rebind_opening_speaker(text: str, *, wrong_label: str, canonical_name: str) -> str | None:
    t = _normalize_text(text)
    w = str(wrong_label or "").strip()
    if not w or not canonical_name:
        return None
    if '"' in w or "“" in w or "”" in w:
        return None
    low_t = t.lower()
    low_w = w.lower()
    if low_t.startswith(low_w + " ") or low_t.startswith(low_w + ","):
        rest = t[len(w) :].lstrip()
        return _normalize_text(f"{canonical_name} {rest}")
    return None


def _apply_speaker_contract_repairs(
    text: str,
    validation: Dict[str, Any],
    *,
    contract: Dict[str, Any],
    eff_resolution: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> tuple[str, str, Dict[str, Any]]:
    """Returns (new_text, final_reason_code, repair_debug)."""
    dbg: Dict[str, Any] = {"initial_repair_mode": validation.get("repair_mode")}
    mode = str(validation.get("repair_mode") or "none")
    reason = str(validation.get("reason_code") or "")
    cid = validation.get("canonical_speaker_id")
    cname = str(validation.get("canonical_speaker_name") or "").strip()

    if mode == "local_rebind" and eff_resolution is not None:
        sig = (validation.get("details") or {}).get("signature") or {}
        wl = str(sig.get("speaker_label") or "").strip()
        if wl and cname:
            attempt = _try_local_rebind_opening_speaker(text, wrong_label=wl, canonical_name=cname)
            if attempt:
                dbg["local_rebind_applied"] = True
                if isinstance(eff_resolution.get("social"), dict):
                    soc = eff_resolution["social"]
                    if cid:
                        soc["npc_id"] = str(cid).strip()
                    soc["npc_name"] = cname
                return attempt, _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR, dbg

    if mode == "canonical_rewrite":
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = dict(eff_resolution["social"])
            if cid:
                soc["npc_id"] = str(cid).strip()
            if cname:
                soc["npc_name"] = cname
            elif cid:
                soc["npc_name"] = _npc_display_name_for_emission(
                    world if isinstance(world, dict) else {},
                    str(scene_id or "").strip(),
                    str(cid).strip(),
                )
            soc.pop("reply_speaker_grounding_neutral_bridge", None)
            eff_resolution["social"] = soc
            line = strict_social_ownership_terminal_fallback(eff_resolution)
            dbg["canonical_rewrite_applied"] = True
            return line, _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE, dbg
        line = _normalize_text(text)
        dbg["canonical_rewrite_failed_resolution"] = True
        return line, reason, dbg

    if mode == "narrator_neutral":
        seed = f"{scene_id}|{cid or ''}|{_stable_seed_fingerprint(_normalize_text(text))}"
        line = neutral_reply_speaker_grounding_bridge_line(seed=seed)
        dbg["narrator_neutral_applied"] = True
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = eff_resolution["social"]
            soc["reply_speaker_grounding_neutral_bridge"] = True
            soc.pop("npc_id", None)
            soc.pop("npc_name", None)
        return line, _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER, dbg

    return text, reason, dbg


def _sync_eff_social_to_resolution(
    eff_resolution: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> None:
    """Copy speaker fields from effective resolution back to the caller's resolution dict when distinct."""
    if not isinstance(eff_resolution, dict) or not isinstance(resolution, dict):
        return
    if resolution is eff_resolution:
        return
    src = eff_resolution.get("social")
    if not isinstance(src, dict):
        return
    dst = resolution.get("social")
    if not isinstance(dst, dict):
        resolution["social"] = {}
        dst = resolution["social"]
    if src.get("reply_speaker_grounding_neutral_bridge"):
        dst["reply_speaker_grounding_neutral_bridge"] = True
        dst.pop("npc_id", None)
        dst.pop("npc_name", None)
        return
    if "npc_id" in src:
        dst["npc_id"] = src.get("npc_id")
    if "npc_name" in src:
        dst["npc_name"] = src.get("npc_name")


def _merge_speaker_enforcement_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    enforcement_payload: Dict[str, Any],
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["speaker_contract_enforcement"] = enforcement_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["speaker_contract_enforcement"] = enforcement_payload

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["speaker_contract_enforcement"] = enforcement_payload
