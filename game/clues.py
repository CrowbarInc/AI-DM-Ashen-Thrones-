"""Structured clues that drive world progression.

Clues augment session state; narrative output is preserved via mark_clue_discovered.
Supports a knowledge-state layer: discovered, inferred, known_to_player.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from game.storage import mark_clue_discovered


CLUE_PRESENTATION_LEVELS: tuple[str, ...] = ("implicit", "explicit", "actionable")


def _normalize_presentation(value: Any, *, default: str = "implicit") -> str:
    raw = str(value or "").strip().lower()
    if raw in CLUE_PRESENTATION_LEVELS:
        return raw
    return default


def _presentation_rank(level: str) -> int:
    norm = _normalize_presentation(level)
    return CLUE_PRESENTATION_LEVELS.index(norm)


def _resolve_known_clue_id(
    session: Dict[str, Any],
    *,
    clue_id: str | None = None,
    clue_text: str | None = None,
) -> str | None:
    cid = str(clue_id or "").strip()
    if cid:
        return cid
    text = str(clue_text or "").strip()
    if not text:
        return None
    knowledge = session.get("clue_knowledge") or {}
    if not isinstance(knowledge, dict):
        return None
    for known_id, entry in knowledge.items():
        if not isinstance(known_id, str):
            continue
        if isinstance(entry, dict) and str(entry.get("text") or "").strip() == text:
            return known_id
    return None


def _ensure_clue_knowledge(session: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Ensure session has clue_knowledge dict. Returns mutable clue_knowledge."""
    if "clue_knowledge" not in session or not isinstance(session["clue_knowledge"], dict):
        session["clue_knowledge"] = {}
    return session["clue_knowledge"]


def add_clue_to_knowledge(
    session: Dict[str, Any],
    clue_id: str,
    state: str,
    *,
    clue_text: str | None = None,
    source_scene: str | None = None,
) -> bool:
    """Add or update a clue in the knowledge layer. Returns True if newly added.

    state: "discovered" (found via exploration) or "inferred" (deduced from other clues).
    """
    if not clue_id or not isinstance(clue_id, str):
        return False
    clue_id = clue_id.strip()
    if not clue_id:
        return False
    if state not in ("discovered", "inferred"):
        state = "discovered"

    knowledge = _ensure_clue_knowledge(session)
    if clue_id in knowledge:
        return False
    presentation = "explicit" if state == "discovered" else "implicit"
    entry: Dict[str, Any] = {"state": state, "source_scene": source_scene, "presentation": presentation}
    if clue_text and isinstance(clue_text, str) and clue_text.strip():
        entry["text"] = clue_text.strip()
    knowledge[clue_id] = entry
    return True


def set_clue_presentation(
    session: Dict[str, Any],
    *,
    clue_id: str | None = None,
    clue_text: str | None = None,
    level: str = "implicit",
) -> bool:
    """Promote clue presentation level (implicit -> explicit -> actionable)."""
    knowledge = _ensure_clue_knowledge(session)
    resolved_id = _resolve_known_clue_id(session, clue_id=clue_id, clue_text=clue_text)
    if not resolved_id or resolved_id not in knowledge:
        return False
    entry = knowledge.get(resolved_id)
    if not isinstance(entry, dict):
        return False
    target = _normalize_presentation(level)
    current = _normalize_presentation(entry.get("presentation"), default="implicit")
    if _presentation_rank(target) <= _presentation_rank(current):
        entry["presentation"] = current
        return False
    entry["presentation"] = target
    return True


def get_clue_presentation(
    session: Dict[str, Any],
    *,
    clue_id: str | None = None,
    clue_text: str | None = None,
    default: str = "implicit",
) -> str:
    """Return clue presentation level for a known clue, defaulting to implicit."""
    knowledge = session.get("clue_knowledge") or {}
    if not isinstance(knowledge, dict):
        return _normalize_presentation(default)
    resolved_id = _resolve_known_clue_id(session, clue_id=clue_id, clue_text=clue_text)
    if not resolved_id:
        return _normalize_presentation(default)
    entry = knowledge.get(resolved_id)
    if not isinstance(entry, dict):
        return _normalize_presentation(default)
    return _normalize_presentation(entry.get("presentation"), default=default)


def get_known_clues_with_presentation(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return known clues as [{id, state, text?, source_scene?, presentation}] records."""
    out: List[Dict[str, Any]] = []
    knowledge = session.get("clue_knowledge") or {}
    if not isinstance(knowledge, dict):
        return out
    for cid, entry in knowledge.items():
        if not isinstance(cid, str) or not cid.strip() or not isinstance(entry, dict):
            continue
        rec: Dict[str, Any] = {
            "id": cid.strip(),
            "state": str(entry.get("state") or "discovered"),
            "presentation": _normalize_presentation(entry.get("presentation"), default="implicit"),
            "source_scene": entry.get("source_scene"),
        }
        txt = entry.get("text")
        if isinstance(txt, str) and txt.strip():
            rec["text"] = txt.strip()
        out.append(rec)
    return out


def get_all_known_clue_ids(session: Dict[str, Any]) -> Set[str]:
    """Return set of all clue ids known to the player (discovered + inferred).

    Aggregates from scene_runtime.discovered_clue_ids and session.clue_knowledge.
    """
    known: Set[str] = set()
    runtime = session.get("scene_runtime") or {}
    if isinstance(runtime, dict):
        for rdata in runtime.values():
            if isinstance(rdata, dict):
                for cid in rdata.get("discovered_clue_ids") or []:
                    if cid and isinstance(cid, str):
                        known.add(str(cid).strip())
    knowledge = session.get("clue_knowledge") or {}
    if isinstance(knowledge, dict):
        for cid in knowledge:
            if cid and isinstance(cid, str):
                known.add(str(cid).strip())
    return known


def get_all_known_clue_texts(session: Dict[str, Any]) -> Set[str]:
    """Return set of all clue texts known to the player (discovered + inferred).

    Aggregates from scene_runtime.discovered_clues and session.clue_knowledge.
    """
    known: Set[str] = set()
    runtime = session.get("scene_runtime") or {}
    if isinstance(runtime, dict):
        for rdata in runtime.values():
            if isinstance(rdata, dict):
                for ct in rdata.get("discovered_clues") or []:
                    if ct and isinstance(ct, str) and ct.strip():
                        known.add(ct.strip())
    knowledge = session.get("clue_knowledge") or {}
    if isinstance(knowledge, dict):
        for entry in knowledge.values():
            if isinstance(entry, dict):
                ct = entry.get("text")
                if ct and isinstance(ct, str) and ct.strip():
                    known.add(ct.strip())
    return known


def is_clue_known(session: Dict[str, Any], clue_id_or_text: str) -> bool:
    """Return True if the player knows this clue (by id or text)."""
    if not clue_id_or_text or not isinstance(clue_id_or_text, str):
        return False
    s = clue_id_or_text.strip()
    if not s:
        return False
    return s in get_all_known_clue_ids(session) or s in get_all_known_clue_texts(session)


def run_inference(session: Dict[str, Any], world: Dict[str, Any]) -> List[str]:
    """Check inference rules and add newly inferred clues. Returns list of newly inferred clue ids.

    Rules: world.inference_rules = [{"inferred_clue_id": "B", "requires": ["A", "C"], "inferred_clue_text": "..."}]
    Clue text for inferred clues: rule.inferred_clue_text or world.clues[id].text.
    """
    rules = world.get("inference_rules") or []
    if not isinstance(rules, list):
        return []
    clues_registry = world.get("clues") or {}
    if not isinstance(clues_registry, dict):
        clues_registry = {}

    known_ids = get_all_known_clue_ids(session)
    knowledge = _ensure_clue_knowledge(session)
    newly_inferred: List[str] = []

    changed = True
    while changed:
        changed = False
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            inferred_id = str(rule.get("inferred_clue_id") or "").strip()
            requires = rule.get("requires")
            if not inferred_id or not isinstance(requires, list):
                continue
            required_set = {str(r).strip() for r in requires if r and isinstance(r, str)}
            if not required_set:
                continue
            if inferred_id in knowledge:
                continue
            if not required_set.issubset(known_ids):
                continue
            # All prerequisites met
            text = rule.get("inferred_clue_text")
            if not text or not isinstance(text, str):
                clue_def = clues_registry.get(inferred_id) if isinstance(clues_registry.get(inferred_id), dict) else None
                text = (clue_def.get("text") or "").strip() if clue_def else ""
            add_clue_to_knowledge(session, inferred_id, "inferred", clue_text=text or None)
            knowledge = _ensure_clue_knowledge(session)
            known_ids.add(inferred_id)
            newly_inferred.append(inferred_id)
            changed = True
            print("[CLUE INFERRED]", inferred_id)

    return newly_inferred


def reveal_clue(
    session: Dict[str, Any],
    scene_id: str,
    clue_id: str,
    clue_text: str | None = None,
    world: Dict[str, Any] | None = None,
) -> str:
    """Record that a structured clue was discovered. Augments scene_runtime and clue_knowledge.

    Backward compatible: clue_text and world are optional.
    When world is provided, runs inference after adding the clue.

    Returns:
        clue_id (for convenience).
    """
    if not clue_id or not isinstance(clue_id, str):
        return clue_id or ""
    clue_id = clue_id.strip()
    if not clue_id:
        return ""

    runtime = session.setdefault("scene_runtime", {})
    if not isinstance(runtime, dict):
        session["scene_runtime"] = {}
        runtime = session["scene_runtime"]
    scene_rt = runtime.setdefault(scene_id, {})
    if not isinstance(scene_rt, dict):
        runtime[scene_id] = {}
        scene_rt = runtime[scene_id]
    clue_ids: List[str] = scene_rt.setdefault("discovered_clue_ids", [])

    if clue_id not in clue_ids:
        clue_ids.append(clue_id)

    add_clue_to_knowledge(session, clue_id, "discovered", clue_text=clue_text, source_scene=scene_id)
    set_clue_presentation(session, clue_id=clue_id, level="explicit")

    print("[CLUE DISCOVERED]", clue_id)

    if world and isinstance(world, dict):
        run_inference(session, world)

    return clue_id


def apply_authoritative_clue_discovery(
    session: Dict[str, Any],
    scene_id: str,
    *,
    clue_id: str | None = None,
    clue_text: str | None = None,
    discovered_clues: List[str] | None = None,
    world: Dict[str, Any] | None = None,
) -> List[str]:
    """Single authoritative clue mutation gateway.

    This is the only engine-owned path that should mutate clue discovery state.
    GPT narration text detection can still exist for telemetry, but must not call this.

    Returns:
        Newly-added discovered clue texts (deduplicated, in insertion order).
    """
    added_texts: List[str] = []

    normalized_texts: List[str] = []
    if isinstance(clue_text, str) and clue_text.strip():
        normalized_texts.append(clue_text.strip())
    for raw in discovered_clues or []:
        if isinstance(raw, str) and raw.strip():
            txt = raw.strip()
            if txt not in normalized_texts:
                normalized_texts.append(txt)

    normalized_clue_id = str(clue_id or "").strip()
    primary_text = normalized_texts[0] if normalized_texts else None
    if normalized_clue_id:
        reveal_clue(
            session,
            scene_id,
            normalized_clue_id,
            clue_text=primary_text,
            world=world,
        )
        if primary_text:
            set_clue_presentation(session, clue_id=normalized_clue_id, clue_text=primary_text, level="explicit")

    for txt in normalized_texts:
        if mark_clue_discovered(session, scene_id, txt):
            added_texts.append(txt)
        set_clue_presentation(session, clue_id=normalized_clue_id or None, clue_text=txt, level="explicit")

    return added_texts
