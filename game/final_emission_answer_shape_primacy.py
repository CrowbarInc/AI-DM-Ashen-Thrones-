"""Final-emission answer-shape primacy layer (ASP heuristics + boundary apply).

This module owns gate-layer ASP regex heuristics, validation, metadata merge, and
validate-only boundary application before scene state anchoring.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_player_facing_narration_purity import gate_text_preview
from game.final_emission_text import (
    _ACTION_RESULT_PATTERNS,
    _ANSWER_DIRECT_PATTERNS,
    _normalize_text,
)
from game.final_emission_validators import _content_tokens, _split_sentences_answer_complete
from game.response_policy_contracts import _last_player_input
from game.social_exchange_emission import merged_player_prompt_for_gate

_ASP_PRESSURE_LEX_RE = re.compile(
    r"\b(?:tension|confrontation|crackdown|border\s+war|the\s+war\b|unrest|factions|politics|"
    r"stakes|consequences|pressure|looms|mounts|swallows|brittle|tear\s+at|invasion|rumors?\s+outrun|"
    r"everyone\s+on\s+edge|nothing\s+feels\s+clean|the\s+city\s+watches|choose\s+your\s+next)\b",
    re.IGNORECASE,
)
_ASP_OBSERVE_PAYLOAD_RE = re.compile(
    r"\b(?:see|hear|notice|spot|smell|taste|feel|watch|scan|survey|glimpse|make\s+out)\b",
    re.IGNORECASE,
)
_ASP_SPATIAL_OR_EXISTENTIAL_RE = re.compile(
    r"\b(?:there\s+is|there\s+are|ahead|behind|above|below|to\s+your\s+(?:left|right)|"
    r"at\s+the|under\s+the|over\s+the|along\s+the)\b",
    re.IGNORECASE,
)
_ASP_ARRIVAL_RE = re.compile(
    r"\b(?:step|steps|arrive|arriving|enter|entering|cross|crossing|reach|reaching|pass|passing|emerge)\b",
    re.IGNORECASE,
)
_ASP_SCENE_TEXTURE_RE = re.compile(
    r"\b(?:rain|mud|cobble|torchlight|torch|smoke|arch|door|cart|boots|slate|roof|gutter|bell|hammer|iron)\b",
    re.IGNORECASE,
)
_ASP_AMBIENT_STATE_RE = re.compile(
    r"\b(?:silence|stillness|quiet|hush|calm|pause)\b",
    re.IGNORECASE,
)
_ASP_INFORMATIVE_DETAIL_RE = re.compile(
    r"\b(?:lead|leads|clue|clues|keeper|office|lighthouse|warehouse|checkpoint|register|captain|sergeant|"
    r"customs|harbor|quay|stall|merchant|barracks|alley|roofline|bridge|fold|archive|priest|cellar)\b",
    re.IGNORECASE,
)

ANSWER_SHAPE_PRIMACY_RESOLUTION_KINDS = frozenset(
    {
        "observe",
        "investigate",
        "interact",
        "travel",
        "scene_transition",
        "discover_clue",
        "already_searched",
        "search",
        "scene_opening",
    }
)


def default_answer_shape_primacy_meta() -> Dict[str, Any]:
    return {
        "answer_shape_primacy_skip_reason": None,
        "answer_shape_primacy_checked": False,
        "answer_shape_primacy_failed": False,
        "answer_shape_primacy_repaired": False,
        "answer_shape_primacy_repair_mode": None,
        "answer_shape_primacy_failure_reasons": [],
        "answer_shape_primacy_preview_before": None,
        "answer_shape_primacy_preview_after": None,
    }


def merge_answer_shape_primacy_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    if not dbg:
        return
    for k, v in dbg.items():
        if str(k).startswith("answer_shape_primacy_"):
            meta[k] = v


def merge_answer_shape_primacy_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if str(k).startswith("answer_shape_primacy_"):
            flat[k] = v
    nested: Dict[str, Any] = {
        "checked": bool(gate_meta.get("answer_shape_primacy_checked")),
        "passed": not bool(gate_meta.get("answer_shape_primacy_failed")),
        "failure_reasons": list(gate_meta.get("answer_shape_primacy_failure_reasons") or []),
    }
    sr = gate_meta.get("answer_shape_primacy_skip_reason")
    if sr:
        nested["skip_reason"] = sr

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["answer_shape_primacy"] = nested
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


def answer_shape_primacy_applies(
    *,
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
) -> bool:
    if strict_social_details is not None:
        return False
    rtr = str((response_type_debug or {}).get("response_type_required") or "").strip().lower()
    if rtr in {"action_outcome", "neutral_narration"}:
        return True
    if not isinstance(resolution, dict):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    return kind in ANSWER_SHAPE_PRIMACY_RESOLUTION_KINDS


def asp_sentence_has_payload(
    sentence: str,
    *,
    player_tokens: set[str],
    res_kind: str,
    required_rt: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if len(_content_tokens(s) & player_tokens) >= 2:
        return True
    if any(p.search(s) for p in _ACTION_RESULT_PATTERNS):
        return True
    if _ASP_OBSERVE_PAYLOAD_RE.search(s):
        return True
    if _ASP_SPATIAL_OR_EXISTENTIAL_RE.search(s):
        return True
    if _ASP_SCENE_TEXTURE_RE.search(s):
        return True
    if _ASP_AMBIENT_STATE_RE.search(s):
        return True
    if _ASP_INFORMATIVE_DETAIL_RE.search(s):
        return True
    if re.search(r'["“”]', s) and len(s) >= 20:
        return True
    if required_rt == "action_outcome" and re.search(r"\b(?:you|your)\b", s, re.IGNORECASE):
        if any(p.search(s) for p in _ACTION_RESULT_PATTERNS):
            return True
        if re.search(
            r"\b(?:latch|door|lock|hinge|snap|give|gives|hold|holds|refuse|refuses)\b",
            s,
            re.IGNORECASE,
        ):
            return True
    st = resolution.get("state_changes") if isinstance(resolution, dict) and isinstance(resolution.get("state_changes"), dict) else {}
    travelish = bool(
        isinstance(resolution, dict)
        and (
            bool(resolution.get("resolved_transition"))
            or bool(st.get("scene_transition_occurred"))
            or bool(st.get("arrived_at_scene"))
        )
    )
    if res_kind in {"travel", "scene_transition"} and travelish and _ASP_ARRIVAL_RE.search(s):
        return True
    return False


def asp_sentence_is_pressure_only(
    sentence: str,
    *,
    player_tokens: set[str],
    res_kind: str,
    required_rt: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if asp_sentence_has_payload(
        s,
        player_tokens=player_tokens,
        res_kind=res_kind,
        required_rt=required_rt,
        resolution=resolution,
    ):
        return False
    return bool(_ASP_PRESSURE_LEX_RE.search(s))


def validate_answer_shape_primacy(
    text: str,
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"passed": True, "failure_reasons": [], "repairable_pressure_lead": False}
    res = resolution if isinstance(resolution, dict) else None
    res_kind = str((res or {}).get("kind") or "").strip().lower()
    required_rt = str((response_type_debug or {}).get("response_type_required") or "").strip().lower()
    player_tokens = _content_tokens(player_input)
    sentences = _split_sentences_answer_complete(str(text or ""))
    if not sentences:
        out["passed"] = False
        out["failure_reasons"].append("empty_text")
        return out

    payload_hits = [
        asp_sentence_has_payload(
            sent,
            player_tokens=player_tokens,
            res_kind=res_kind,
            required_rt=required_rt,
            resolution=res,
        )
        for sent in sentences
    ]
    if not any(payload_hits):
        wc = len(_normalize_text(text).split())
        any_pressure = any(
            asp_sentence_is_pressure_only(
                sent,
                player_tokens=player_tokens,
                res_kind=res_kind,
                required_rt=required_rt,
                resolution=res,
            )
            for sent in sentences
        )
        if wc <= 8 and not any_pressure:
            return out
        low = _normalize_text(text).lower()
        if "for a breath" in low and "voices shift" in low:
            out["passed"] = False
            out["failure_reasons"].append("missing_observation_or_result_payload")
            return out
        if _ASP_INFORMATIVE_DETAIL_RE.search(text) or any(p.search(text) for p in _ANSWER_DIRECT_PATTERNS):
            return out
        if wc >= 10 and not any_pressure:
            return out
        out["passed"] = False
        out["failure_reasons"].append("missing_observation_or_result_payload")
        return out

    opener = sentences[0]
    opener_payload = payload_hits[0]
    if not opener_payload and asp_sentence_is_pressure_only(
        opener,
        player_tokens=player_tokens,
        res_kind=res_kind,
        required_rt=required_rt,
        resolution=res,
    ):
        out["passed"] = False
        out["failure_reasons"].append("pressure_or_consequence_before_payload")
        if any(payload_hits[1:]):
            out["repairable_pressure_lead"] = True
        return out

    return out


def apply_answer_shape_primacy_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    _ = gm_output
    meta = default_answer_shape_primacy_meta()
    if not answer_shape_primacy_applies(
        resolution=resolution,
        response_type_debug=response_type_debug,
        strict_social_details=strict_social_details,
    ):
        meta["answer_shape_primacy_skip_reason"] = "turn_not_in_scope"
        return text, meta, []

    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        meta["answer_shape_primacy_skip_reason"] = "response_type_contract_failed"
        return text, meta, []

    sid = str(scene_id or "").strip()
    player_input = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    if not str(player_input or "").strip():
        player_input = _last_player_input(
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )

    before = str(text or "")
    meta["answer_shape_primacy_preview_before"] = gate_text_preview(before)
    meta["answer_shape_primacy_checked"] = True

    v0 = validate_answer_shape_primacy(
        before,
        player_input=player_input,
        resolution=resolution,
        response_type_debug=response_type_debug,
    )
    if v0.get("passed"):
        meta["answer_shape_primacy_failed"] = False
        meta["answer_shape_primacy_preview_after"] = gate_text_preview(before)
        return text, meta, []

    meta["answer_shape_primacy_boundary_semantic_repair_disabled"] = True
    meta["answer_shape_primacy_failed"] = True
    meta["answer_shape_primacy_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["answer_shape_primacy_preview_after"] = gate_text_preview(before)
    extra: List[str] = ["answer_shape_primacy_violation"]
    return text, meta, extra
