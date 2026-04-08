"""Single source of truth for scene-state anchoring (prompting + future enforcement).

Builds a compact, deterministic contract from authoritative session/scene/world state only.
Does not read hidden facts, undiscovered clues, or non-public scene layers.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Mapping, Sequence, Set

from game.narration_visibility import (
    _coerce_scene_envelope,
    _inner_scene,
    _resolve_scene_id,
    build_narration_visibility_contract,
)
from game.storage import get_scene_runtime, get_scene_state
from game.world import get_world_npc_by_id
from game.interaction_context import build_speaker_selection_contract

_ANCHOR_STOPWORDS: frozenset[str] = frozenset({
    "what", "where", "when", "why", "how", "who", "which", "with", "from", "that", "this",
    "they", "them", "their", "there", "here", "have", "has", "had", "was", "were", "are",
    "the", "and", "for", "not", "but", "you", "your", "into", "about", "just", "very",
})

_MAX_LOCATION_TOKENS = 24
_MAX_ACTOR_TOKENS = 18
_MAX_PLAYER_ACTION_TOKENS = 14
_MAX_RUNTIME_ACTION_CHARS = 200


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _canonical_interaction_target_npc_id(session: Mapping[str, Any] | None, raw_target_id: str) -> str:
    raw = str(raw_target_id or "").strip()
    if not raw or not isinstance(session, Mapping):
        return raw
    st = get_scene_state(session)
    pmap = st.get("promoted_actor_npc_map")
    if not isinstance(pmap, dict):
        return raw
    mapped = pmap.get(raw)
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw


def _normalize_match_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split()).strip().lower()
    if not text:
        return ""
    return text


def _dedupe_preserve(items: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        low = item.strip().lower()
        if not low or low in seen:
            continue
        seen.add(low)
        out.append(low)
    return out


def _strip_edge_punct(token: str) -> str:
    text = token.strip().lower()
    while text and text[0] in string.punctuation:
        text = text[1:].strip().lower()
    while text and text[-1] in string.punctuation:
        text = text[:-1].strip().lower()
    return text


def _phrase_tokens_from_label(label: str, *, max_phrases: int = 4) -> List[str]:
    s = _strip_edge_punct(label)
    if not s or len(s) < 2:
        return []
    words = [w for w in re.split(r"\s+", s) if w]
    out: List[str] = []
    if words:
        out.append(" ".join(words))
    for i in range(len(words)):
        w = words[i]
        if len(w) >= 3 and w not in _ANCHOR_STOPWORDS:
            out.append(w)
        if i + 1 < len(words):
            pair = f"{words[i]} {words[i + 1]}"
            if len(pair) >= 5:
                out.append(pair)
    return _dedupe_preserve(out)[:max_phrases]


def _content_keywords(text: str, *, max_words: int = 8) -> List[str]:
    s = _clean_string(text)[:_MAX_RUNTIME_ACTION_CHARS]
    if not s:
        return []
    lowered = s.lower()
    words = re.findall(r"[a-z][a-z']{2,}", lowered)
    picked: List[str] = []
    for w in words:
        if w in _ANCHOR_STOPWORDS:
            continue
        picked.append(w)
        if len(picked) >= max_words:
            break
    return _dedupe_preserve(picked)


def _collect_location_tokens(
    inner: Mapping[str, Any],
    *,
    debug_sources: Dict[str, List[str]],
) -> List[str]:
    tokens: List[str] = []
    sid = _clean_string(inner.get("id"))
    if sid:
        debug_sources.setdefault("location", []).append("scene.id")
        tokens.append(sid.lower())
        if "_" in sid:
            tokens.append(sid.replace("_", " ").lower())
    loc = _clean_string(inner.get("location"))
    if loc:
        debug_sources.setdefault("location", []).append("scene.location")
        tokens.append(loc.lower())
        words = [w for w in re.split(r"\s+", loc.lower()) if len(w) >= 3]
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]} {words[i + 1]}")
    vf = inner.get("visible_facts")
    if isinstance(vf, list) and vf:
        fact0 = vf[0]
        if isinstance(fact0, str):
            debug_sources.setdefault("location", []).append("visible_facts")
            snippet = fact0[:120].lower()
            for w in re.findall(r"[a-z]{4,}", snippet):
                if w in _ANCHOR_STOPWORDS:
                    continue
                tokens.append(w)
                if len(tokens) >= _MAX_LOCATION_TOKENS:
                    break
    return _dedupe_preserve(tokens)[:_MAX_LOCATION_TOKENS]


def _collect_actor_tokens(
    *,
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    scene_envelope: Mapping[str, Any],
    scene_id: str,
    resolution: Mapping[str, Any] | None,
    visibility: Mapping[str, Any],
    debug_sources: Dict[str, List[str]],
) -> List[str]:
    tokens: List[str] = []
    w = world if isinstance(world, Mapping) else None
    vis_names = visibility.get("visible_entity_names") if isinstance(visibility, Mapping) else None
    if isinstance(vis_names, list):
        for name in vis_names:
            if not isinstance(name, str):
                continue
            n = _strip_edge_punct(name)
            if len(n) >= 2:
                tokens.append(n.lower())
                debug_sources.setdefault("actor", []).append("narration_visibility.visible_entity_names")
    aliases = visibility.get("visible_entity_aliases") if isinstance(visibility, Mapping) else None
    if isinstance(aliases, dict):
        for _eid, names in list(aliases.items())[:12]:
            if not isinstance(names, list):
                continue
            for alt in names[:2]:
                if isinstance(alt, str):
                    a = _strip_edge_punct(alt)
                    if len(a) >= 2:
                        tokens.append(a.lower())
                        debug_sources.setdefault("actor", []).append("visible_entity_aliases")

    env = scene_envelope if isinstance(scene_envelope, Mapping) else {}
    sp = build_speaker_selection_contract(
        session if isinstance(session, Mapping) else None,
        w,
        scene_id,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        scene_envelope=env,
    )
    psid = _clean_string(sp.get("primary_speaker_id"))
    if psid and isinstance(w, Mapping):
        row = get_world_npc_by_id(w, psid)
        if isinstance(row, dict):
            nm = _clean_string(row.get("name"))
            if nm:
                tokens.insert(0, nm.lower())
                debug_sources.setdefault("actor", []).insert(0, "speaker_selection.primary_speaker_id")

    if isinstance(session, Mapping):
        ic = session.get("interaction_context")
        if isinstance(ic, Mapping):
            raw = _clean_string(ic.get("active_interaction_target_id"))
            if raw:
                cid = _canonical_interaction_target_npc_id(session, raw)
                if cid and isinstance(w, Mapping):
                    row = get_world_npc_by_id(w, cid)
                    if isinstance(row, dict):
                        nm = _clean_string(row.get("name"))
                        if nm:
                            tokens.insert(0, nm.lower())
                            debug_sources.setdefault("actor", []).append("interaction_context.active_interaction_target_id")

    return _dedupe_preserve(tokens)[:_MAX_ACTOR_TOKENS]


def _collect_player_action_tokens(
    *,
    session: Mapping[str, Any] | None,
    scene_id: str,
    resolution: Mapping[str, Any] | None,
    debug_sources: Dict[str, List[str]],
) -> List[str]:
    tokens: List[str] = []
    res = resolution if isinstance(resolution, Mapping) else None
    if res:
        kind = _clean_string(res.get("kind")).lower()
        if kind:
            tokens.append(kind)
            debug_sources.setdefault("player_action", []).append("resolution.kind")
        label = _clean_string(res.get("label"))
        for p in _phrase_tokens_from_label(label):
            tokens.append(p)
            debug_sources.setdefault("player_action", []).append("resolution.label")
        prompt = _clean_string(res.get("prompt"))
        for w in _content_keywords(prompt, max_words=5):
            tokens.append(w)
            debug_sources.setdefault("player_action", []).append("resolution.prompt")
        aid = _clean_string(res.get("action_id"))
        if aid:
            tokens.append(aid.lower())
            if "_" in aid:
                tokens.append(aid.replace("_", " ").lower())
            debug_sources.setdefault("player_action", []).append("resolution.action_id")

    if isinstance(session, Mapping) and scene_id:
        rt = get_scene_runtime(session, scene_id)
        lat = _clean_string(rt.get("last_player_action_text"))
        for w in _content_keywords(lat, max_words=8):
            tokens.append(w)
            debug_sources.setdefault("player_action", []).append("scene_runtime.last_player_action_text")

    return _dedupe_preserve(tokens)[:_MAX_PLAYER_ACTION_TOKENS]


def _match_tokens(normalized_text: str, tokens: Sequence[str]) -> List[str]:
    if not normalized_text or not tokens:
        return []
    hits: List[str] = []
    for raw in tokens:
        phrase = _strip_edge_punct(str(raw))
        if len(phrase) < 2:
            continue
        if " " in phrase:
            pattern = re.escape(phrase).replace(r"\ ", r"\s+")
            if re.search(rf"(?<!\w){pattern}(?!\w)", normalized_text):
                hits.append(phrase)
        else:
            if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_text):
                hits.append(phrase)
    return hits


def build_scene_state_anchor_contract(
    session: Any,
    scene: Any,
    world: Any,
    resolution: Any = None,
) -> Dict[str, Any]:
    """Assemble an inspectable anchoring contract for the current turn."""
    env = _coerce_scene_envelope(scene if isinstance(scene, Mapping) else None)
    inner = _inner_scene(env)
    sid = _resolve_scene_id(env, session if isinstance(session, Mapping) else None)
    scene_location_label = _clean_string(inner.get("location")) if isinstance(inner, Mapping) else ""

    debug_sources: Dict[str, List[str]] = {"location": [], "actor": [], "player_action": []}

    visibility = build_narration_visibility_contract(
        session=session if isinstance(session, Mapping) else None,
        scene=scene if isinstance(scene, Mapping) else None,
        world=world if isinstance(world, Mapping) else None,
    )

    location_tokens = _collect_location_tokens(inner if isinstance(inner, Mapping) else {}, debug_sources=debug_sources)
    res = resolution if isinstance(resolution, Mapping) else None

    actor_tokens = _collect_actor_tokens(
        session=session if isinstance(session, Mapping) else None,
        world=world if isinstance(world, Mapping) else None,
        scene_envelope=env,
        scene_id=sid,
        resolution=res,
        visibility=visibility if isinstance(visibility, Mapping) else {},
        debug_sources=debug_sources,
    )
    player_action_tokens = _collect_player_action_tokens(
        session=session if isinstance(session, Mapping) else None,
        scene_id=sid,
        resolution=res,
        debug_sources=debug_sources,
    )

    total = len(location_tokens) + len(actor_tokens) + len(player_action_tokens)
    enabled = total > 0
    debug_reason = (
        f"scene_state_anchor: loc={len(location_tokens)} actor={len(actor_tokens)} "
        f"player_action={len(player_action_tokens)} enabled={enabled}"
    )

    return {
        "enabled": enabled,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": sid or None,
        "scene_location_label": scene_location_label or None,
        "location_tokens": location_tokens,
        "actor_tokens": actor_tokens,
        "player_action_tokens": player_action_tokens,
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": debug_reason,
        "debug_sources": {k: _dedupe_preserve(v) for k, v in debug_sources.items()},
    }


def validate_scene_state_anchoring(text: str, contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Check whether *text* matches at least one anchor bucket (whole-text, not first sentence)."""
    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "matched_anchor_kinds": [],
            "missing_anchor_kinds": [],
            "matched_tokens": [],
            "failure_reasons": ["invalid_contract"],
        }

    if not contract.get("enabled"):
        return {
            "checked": False,
            "passed": True,
            "matched_anchor_kinds": [],
            "missing_anchor_kinds": [],
            "matched_tokens": [],
            "failure_reasons": [],
        }

    normalized = _normalize_match_text(str(text or ""))
    req = list(contract.get("required_any_of") or ["location", "actor", "player_action"])

    if not normalized:
        return {
            "checked": True,
            "passed": False,
            "matched_anchor_kinds": [],
            "missing_anchor_kinds": list(req),
            "matched_tokens": [],
            "failure_reasons": ["empty_text"],
        }

    loc_hits = _match_tokens(normalized, list(contract.get("location_tokens") or []))
    act_hits = _match_tokens(normalized, list(contract.get("actor_tokens") or []))
    pa_hits = _match_tokens(normalized, list(contract.get("player_action_tokens") or []))

    matched_kinds: List[str] = []
    matched_tokens: List[str] = []
    if loc_hits:
        matched_kinds.append("location")
        matched_tokens.extend(loc_hits)
    if act_hits:
        matched_kinds.append("actor")
        matched_tokens.extend(act_hits)
    if pa_hits:
        matched_kinds.append("player_action")
        matched_tokens.extend(pa_hits)

    passed = bool(loc_hits or act_hits or pa_hits)

    missing: List[str] = []
    if not passed:
        if "location" in req and not loc_hits:
            missing.append("location")
        if "actor" in req and not act_hits:
            missing.append("actor")
        if "player_action" in req and not pa_hits:
            missing.append("player_action")

    failure_reasons: List[str] = []
    if not passed:
        failure_reasons.append("no_anchor_match")

    return {
        "checked": True,
        "passed": passed,
        "matched_anchor_kinds": matched_kinds,
        "missing_anchor_kinds": missing,
        "matched_tokens": _dedupe_preserve(matched_tokens),
        "failure_reasons": failure_reasons,
    }
