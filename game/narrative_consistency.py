"""Player-facing narration must agree with authoritative state.

The check uses the active location, other locations, committed transitions,
known discoveries, and recorded object positions. It does not look for one
scene's opening sentence.
"""
from __future__ import annotations

import re
from typing import Any

_PRESENCE = re.compile(
    r"\b(?:across|spatters|you are|you stand|you arrive|you reach|you enter|you find yourself)\b",
    re.I,
)
_TRAVEL_DONE = re.compile(r"\byou (?:travel|set out|arrive|reach|enter)\b", re.I)
_SKIP_LOCATION = {"", "unnamed scene"}


def _inner(scene) -> dict:
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return scene["scene"]
    return scene if isinstance(scene, dict) else {}


def _transition_committed(resolution) -> bool:
    if not isinstance(resolution, dict):
        return False
    if resolution.get("resolved_transition") is True:
        return True
    changes = resolution.get("state_changes")
    return isinstance(changes, dict) and bool(changes.get("scene_changed"))


def _locations() -> dict[str, str]:
    rows: dict[str, str] = {}
    try:
        from game.storage import list_scene_ids, load_scene
        for scene_id in list_scene_ids():
            try:
                inner = (load_scene(scene_id) or {}).get("scene") or {}
            except Exception:
                continue
            place = str(inner.get("location") or "").strip()
            if place.casefold() not in _SKIP_LOCATION:
                rows[str(scene_id)] = place
    except Exception:
        return {}
    return rows


def _known_texts(session, resolution) -> set[str]:
    known: set[str] = set()
    knowledge = session.get("clue_knowledge") if isinstance(session, dict) else None
    if isinstance(knowledge, dict):
        for item in knowledge.values():
            if isinstance(item, dict) and str(item.get("state") or "") in {"discovered", "known"}:
                known.add(str(item.get("text") or "").casefold())
            elif isinstance(item, str):
                known.add(item.casefold())
    if isinstance(resolution, dict):
        clue = str(resolution.get("clue_text") or "").strip()
        if clue:
            known.add(clue.casefold())
        for item in resolution.get("discovered_clues") or []:
            if isinstance(item, str) and item.strip():
                known.add(item.casefold())
    return known


def _hidden_conflict(text: str, session, resolution, scene) -> str | None:
    inner = _inner(scene)
    if not inner:
        active = str((session or {}).get("active_scene_id") or "")
        if not active:
            return None
        try:
            from game.storage import load_scene
            inner = _inner(load_scene(active))
        except Exception:
            return None
    known = {item.rstrip(".!?") for item in _known_texts(session, resolution)}
    visible = " ".join(str(item) for item in (inner.get("visible_facts") or [])).casefold()
    low = text.casefold()
    phrases = []
    for fact in list(inner.get("hidden_facts") or []):
        if isinstance(fact, str):
            phrases.append(fact)
    for item in inner.get("discoverable_clues") or []:
        if isinstance(item, dict) and item.get("text"):
            phrases.append(str(item.get("text")))
    for fact in phrases:
        sample = fact.casefold().strip().rstrip(".!?")
        words = sample.split()
        if len(words) < 4 or sample in known or sample in visible:
            continue
        comparable = low.replace(",", " ").replace(";", " ")
        if sample in low or sample in comparable:
            return "hidden_fact"
    return None


def _object_conflict(text: str, session, resolution) -> str | None:
    changes = (resolution or {}).get("state_changes") if isinstance(resolution, dict) else None
    if isinstance(changes, dict) and (changes.get("mutation") or changes.get("physical")):
        return None
    try:
        from game.bounded_improvisation import LEDGER_KEY
    except Exception:
        return None
    ledger = (session or {}).get(LEDGER_KEY) if isinstance(session, dict) else None
    if not isinstance(ledger, dict):
        return None
    low = text.casefold()
    for entry in ledger.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "").strip()
        position = str((entry.get("properties") or {}).get("position") or "")
        if len(label) < 4 or label.casefold() not in low:
            continue
        if re.search(r"\b(?:aside|moved aside)\b", low) and position and not position.startswith("aside"):
            if re.search(r"\bnot\b.{0,24}\baside\b|\bhas not been moved\b", low):
                continue
            return "object_state:" + label
    return None


def _place_conflict(text: str, session) -> str | None:
    active = str((session or {}).get("active_scene_id") or "")
    if not active:
        return None
    places = _locations()
    current = places.get(active, "")
    low = text.casefold()
    if current and current.casefold() in low:
        return None
    present = bool(_PRESENCE.search(text))
    traveled = bool(_TRAVEL_DONE.search(text))
    if not present and not traveled:
        return None
    current_tokens = set(re.findall(r"[a-z]{8,}", current.casefold()))
    for scene_id, place in places.items():
        if scene_id == active:
            continue
        if place.casefold() in low:
            return "other_location:" + scene_id
        head = re.findall(r"[a-z]{8,}", place.casefold())
        token = head[0] if head else ""
        if token and token not in current_tokens and (
            re.search(r"\b" + re.escape(token) + r"\b", low) or (token + "'") in low or (token + "’") in low
        ):
            return "other_location:" + scene_id
    return None


def _fingerprint_conflict(text: str, session) -> str | None:
    active = str((session or {}).get("active_scene_id") or "")
    low = text.casefold()
    try:
        from game.storage import list_scene_ids, load_scene
    except Exception:
        return None
    try:
        scene_ids = list_scene_ids()
    except Exception:
        return None
    for scene_id in scene_ids:
        if str(scene_id) == active:
            continue
        try:
            inner = (load_scene(scene_id) or {}).get("scene") or {}
        except Exception:
            continue
        for item in list(inner.get("opening_seed_facts") or []) + [inner.get("summary") or ""]:
            fact = str(item or "").strip()
            if len(fact) >= 48 and fact.casefold() in low:
                return "foreign_scene_fact:" + str(scene_id)
    return None


def publication_conflict(text: str, *, session, resolution=None, scene=None) -> str | None:
    """Return a reason when player-facing text contradicts committed state."""
    raw = re.sub(r"\s+", " ", text or "").strip()
    if len(raw) < 40 or not isinstance(session, dict):
        return None
    if _transition_committed(resolution):
        return None
    reason = _place_conflict(raw, session)
    if reason:
        return reason
    reason = _object_conflict(raw, session, resolution)
    if reason:
        return reason
    reason = _hidden_conflict(raw, session, resolution, scene)
    if reason:
        return reason
    return _fingerprint_conflict(raw, session)

