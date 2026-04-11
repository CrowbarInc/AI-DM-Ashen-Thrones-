"""Authoritative interaction-context mutation API.

This module is the single owner for interaction-context runtime mutations.
Callers may read context elsewhere, but all writes should route through these
functions so behavior remains deterministic and inspectable.

**Authoritative social target resolution** (precedence-ordered binding for strict-social
and dialogue) lives in :func:`resolve_authoritative_social_target` **here** — not in
:mod:`game.dialogue_targeting`. Keeping it with roster/state avoids import cycles and
keeps vocative parsing adjacent to the context it mutates. :mod:`game.dialogue_targeting`
only re-exports vocative-facing helpers implemented below.

Social-commitment **break** classification and session hooks are implemented in
:mod:`game.social_continuity_routing` and re-exported here for compatibility.

Promotion: ``game.npc_promotion.promote_scene_actor_to_npc`` (also exported from
``game.world``), plus hooks ``should_promote_scene_actor`` and
``maybe_promote_active_social_target`` in this module and ``game.npc_promotion``.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from game.utils import slugify

from game.npc_promotion import maybe_promote_active_social_target, should_promote_scene_actor
from game.storage import get_interaction_context, get_scene_runtime


SOCIAL_INTERACTION_KINDS = frozenset(
    {
        "social",
        "question",
        "social_probe",
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
    }
)

NON_SOCIAL_ACTIVITY_KINDS = frozenset(
    {
        "observe",
        "investigate",
        "interact",
        "travel",
        "scene_transition",
        "attack",
        "combat",
    }
)

IMPLIED_HINT_LOWERED_VOICE = "lowered_voice"
IMPLIED_HINT_SEATED_WITH_TARGET = "seated_with_target"

INTERACTION_MODES = frozenset({"none", "social", "activity"})
ENGAGEMENT_LEVELS = frozenset({"none", "engaged", "focused"})
CONVERSATION_PRIVACY_VALUES = frozenset({"public", "lowered_voice", "private"})
FOCUSED_ACTIVITY_KINDS = frozenset({"observe", "investigate", "interact", "travel", "scene_transition"})
_LOWERED_VOICE_TOKENS = (
    "lower my voice",
    "lowered my voice",
    "keep my voice low",
    "speak quietly",
    "say quietly",
    "quietly",
    "whisper",
)
_SIT_WITH_TOKENS = (
    "sit with",
    "sit down with",
    "take a seat with",
    "sit beside",
    "sit next to",
)
_COURTESY_MOVE_TOKENS = ("bring", "carry", "place", "set down", "hand")
_COURTESY_ITEM_TOKENS = ("drink", "ale", "beer", "wine", "mug", "cup", "glass", "item")
_COURTESY_TARGET_PREPOSITIONS = (" to ", " for ", " beside ", " next to ", " in front of ")


def _clean_string(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    clean = value.strip()
    return clean or None


SCENE_ADDRESSABLE_KINDS = frozenset({"npc", "scene_actor", "crowd_actor"})

EmergentActorSource = Literal["emergent_narration", "authored", "promoted_visible_figure"]
_EMERGENT_ACTOR_SOURCES: Set[str] = {
    "emergent_narration",
    "authored",
    "promoted_visible_figure",
}
_EMERGENT_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,80}$")


def _scene_npcs(world: Dict[str, Any], scene_id: str) -> list[Dict[str, Any]]:
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return []
    out: list[Dict[str, Any]] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if not nid:
            continue
        loc = _clean_string(npc.get("location")) or _clean_string(npc.get("scene_id"))
        if loc != scene_id:
            continue
        out.append(npc)
    return out


def effective_in_scene_npc_roster(world: Dict[str, Any] | None, scene_id: str) -> list[Dict[str, Any]]:
    """NPC dicts in ``scene_id`` for dialogue binding, active-entity rebuild, and strict-social routing.

    Uses persisted ``world["npcs"]`` when that list is non-empty; otherwise falls back to
    :func:`game.defaults.default_world` for the same location filter. Keeping this roster
    identical across interaction binding and strict-social emission prevents one subsystem
    from seeing an empty scene (no bindable target) while the other still resolves vocative
    lines—``active_interaction_target_id`` and speaker authority must agree.
    """
    sid = _clean_string(scene_id) or ""
    if not sid:
        return []
    w = world if isinstance(world, dict) else {}
    roster = _scene_npcs(w, sid)
    if roster:
        return roster
    # Persisted empty NPC list: do not inject default-world NPCs (scene addressables / active_entities own scope).
    npcs_key = w.get("npcs")
    if isinstance(npcs_key, list) and len(npcs_key) == 0:
        return []
    from game.defaults import default_world

    return _scene_npcs(default_world(), sid)


def _all_world_npc_ids(world: Dict[str, Any]) -> List[str]:
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return []
    out: List[str] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if not nid or nid in out:
            continue
        out.append(nid)
    return out


def _scene_authored_entity_ids(scene_envelope: Dict[str, Any] | None) -> List[str]:
    if not isinstance(scene_envelope, dict):
        return []
    authored: List[str] = []

    def _consume_list(raw: Any) -> None:
        if not isinstance(raw, list):
            return
        for item in raw:
            ent_id = ""
            if isinstance(item, str):
                ent_id = item.strip()
            elif isinstance(item, dict):
                ent_id = str(item.get("id") or "").strip()
            if ent_id and ent_id not in authored:
                authored.append(ent_id)

    scene = scene_envelope.get("scene")
    if isinstance(scene, dict):
        for key in ("active_entities", "entities", "npcs"):
            _consume_list(scene.get(key))

    top_state = scene_envelope.get("scene_state")
    if isinstance(top_state, dict):
        _consume_list(top_state.get("active_entities"))
        _consume_list(top_state.get("entities"))

    return authored


def _normalize_scene_addressable_actor(raw: Dict[str, Any], scene_id: str) -> Optional[Dict[str, Any]]:
    """Normalize scene JSON into the canonical addressable-actor shape (lightweight roster row)."""
    if not isinstance(raw, dict):
        return None
    eid = _clean_string(raw.get("id"))
    if not eid:
        return None
    sid = _clean_string(raw.get("scene_id")) or _clean_string(scene_id) or ""
    name = _clean_string(raw.get("name")) or eid.replace("_", " ").replace("-", " ").title()
    kind = str(raw.get("kind") or "scene_actor").strip().lower()
    if kind not in SCENE_ADDRESSABLE_KINDS:
        kind = "scene_actor"
    roles_in: Any = raw.get("address_roles")
    roles: List[str] = []
    if isinstance(roles_in, list):
        for r in roles_in:
            if isinstance(r, str) and r.strip():
                roles.append(r.strip().lower())
    aliases_in: Any = raw.get("aliases")
    aliases: List[str] = []
    if isinstance(aliases_in, list):
        for a in aliases_in:
            if isinstance(a, str) and a.strip():
                aliases.append(a.strip())
    addressable = raw.get("addressable")
    if addressable is None:
        addressable = True
    priority_raw = raw.get("address_priority")
    try:
        address_priority = int(priority_raw) if priority_raw is not None else 100
    except (TypeError, ValueError):
        address_priority = 100
    row: Dict[str, Any] = {
        "id": eid,
        "name": name,
        "scene_id": sid,
        "address_roles": roles,
        "aliases": aliases,
        "kind": kind,
        "addressable": bool(addressable),
        "address_priority": address_priority,
    }
    if "role" in raw and isinstance(raw.get("role"), str) and raw["role"].strip():
        row["role"] = raw["role"].strip()
    if "topics" in raw:
        row["topics"] = raw["topics"]
    if "disposition" in raw:
        row["disposition"] = raw["disposition"]
    return row


def scene_addressables_from_envelope(scene_envelope: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Return normalized addressable actors from ``scene.addressables``."""
    if not isinstance(scene_envelope, dict):
        return []
    scene = scene_envelope.get("scene")
    if not isinstance(scene, dict):
        return []
    raw = scene.get("addressables")
    if not isinstance(raw, list):
        return []
    sid = _clean_string(scene.get("id")) or ""
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        norm = _normalize_scene_addressable_actor(item, sid)
        if not norm or not norm.get("addressable", True):
            continue
        if norm.get("address_priority", 100) == 100 and "address_priority" not in item:
            norm["address_priority"] = 100 + i
        out.append(norm)
    return out


def _scene_state(session: Dict[str, Any]) -> Dict[str, Any]:
    state = session.get("scene_state")
    if not isinstance(state, dict):
        state = {}
        session["scene_state"] = state
    if not isinstance(state.get("active_entities"), list):
        state["active_entities"] = []
    if not isinstance(state.get("entity_presence"), dict):
        state["entity_presence"] = {}
    if not isinstance(state.get("emergent_addressables"), list):
        state["emergent_addressables"] = []
    if "active_scene_id" not in state:
        state["active_scene_id"] = str(session.get("active_scene_id") or "").strip()
    if "current_interlocutor" not in state:
        state["current_interlocutor"] = None
    if not isinstance(state.get("promoted_actor_npc_map"), dict):
        state["promoted_actor_npc_map"] = {}
    return state


_SOCIAL_EXCHANGE_INTERRUPTION_TRACKER_KEY = "social_exchange_interruption_tracker"


def get_social_exchange_interruption_tracker(session: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return exchange-local interruption tracking for the active scene."""
    if not isinstance(session, dict):
        return {}
    tracker = _scene_state(session).get(_SOCIAL_EXCHANGE_INTERRUPTION_TRACKER_KEY)
    if not isinstance(tracker, dict):
        return {}
    return dict(tracker)


def set_social_exchange_interruption_tracker(
    session: Dict[str, Any] | None,
    tracker: Dict[str, Any] | None,
) -> None:
    """Persist or clear exchange-local interruption tracking for the active scene."""
    if not isinstance(session, dict):
        return
    state = _scene_state(session)
    if isinstance(tracker, dict) and tracker:
        state[_SOCIAL_EXCHANGE_INTERRUPTION_TRACKER_KEY] = dict(tracker)
        return
    state.pop(_SOCIAL_EXCHANGE_INTERRUPTION_TRACKER_KEY, None)


def clear_social_exchange_interruption_tracker(session: Dict[str, Any] | None) -> None:
    """Drop interruption repetition tracking when the active exchange truly changes."""
    set_social_exchange_interruption_tracker(session, None)


def _clear_emergent_addressables(session: Dict[str, Any]) -> None:
    st = _scene_state(session)
    st["emergent_addressables"] = []


def enroll_emergent_scene_actor(
    *,
    session: dict,
    scene: dict,
    actor_hint: dict,
) -> Optional[str]:
    """Enroll a single concrete, socially relevant scene figure into the session roster.

    Persists a lightweight addressable row under ``session["scene_state"]["emergent_addressables"]``,
    rebuilds-friendly via :func:`rebuild_active_scene_entities` and dialogue via
    :func:`canonical_scene_addressable_roster`. Callers must pass conservative hints only.
    """
    if not isinstance(session, dict) or not isinstance(scene, dict) or not isinstance(actor_hint, dict):
        return None
    sc = scene.get("scene")
    if not isinstance(sc, dict):
        return None
    sid = _clean_string(sc.get("id"))
    if not sid:
        return None
    hint_sid = _clean_string(actor_hint.get("scene_id"))
    if hint_sid and hint_sid != sid:
        return None

    src = str(actor_hint.get("source") or "").strip()
    if src not in _EMERGENT_ACTOR_SOURCES:
        return None

    display = _clean_string(actor_hint.get("display_name")) or _clean_string(actor_hint.get("name"))
    if not display or len(display) > 80 or len(display) < 2:
        return None

    raw_id = _clean_string(actor_hint.get("actor_id")) or _clean_string(actor_hint.get("id"))
    eid = ""
    if raw_id and _EMERGENT_ID_RE.match(raw_id):
        eid = raw_id
    else:
        base = slugify(display)
        if not base or len(base) < 3:
            return None
        eid = f"emergent_{base}"[:80]
        if not _EMERGENT_ID_RE.match(eid):
            return None

    addressable = actor_hint.get("addressable")
    if addressable is not None and not bool(addressable):
        return None

    from game.storage import load_world

    world = load_world()
    if not isinstance(world, dict):
        world = {}

    for npc in effective_in_scene_npc_roster(world, sid):
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if not nid:
            continue
        if nid == eid:
            return None
        nm = _clean_string(npc.get("name"))
        if nm and slugify(nm) == slugify(display):
            return None
        if slugify(nid) == slugify(display):
            return None

    for spec in scene_addressables_from_envelope(scene):
        if not isinstance(spec, dict):
            continue
        if str(spec.get("id") or "").strip() == eid:
            return None

    state = _scene_state(session)
    emergent: List[Dict[str, Any]] = list(state.get("emergent_addressables") or [])
    existing_ids = {str(r.get("id") or "").strip() for r in emergent if isinstance(r, dict)}
    if eid in existing_ids:
        return eid

    roles_in: Any = actor_hint.get("address_roles")
    roles: List[str] = []
    if isinstance(roles_in, list):
        for r in roles_in:
            if isinstance(r, str) and r.strip():
                rl = r.strip().lower()
                if rl not in roles:
                    roles.append(rl)
    aliases_in: Any = actor_hint.get("aliases")
    aliases: List[str] = []
    if isinstance(aliases_in, list):
        for a in aliases_in:
            if isinstance(a, str) and a.strip() and a.strip() not in aliases:
                aliases.append(a.strip())
    low_display = display.strip().lower()
    if low_display and low_display not in [x.lower() for x in aliases]:
        aliases.append(display.strip())

    row: Dict[str, Any] = {
        "id": eid,
        "name": display.strip(),
        "scene_id": sid,
        "address_roles": roles,
        "aliases": aliases,
        "kind": "scene_actor",
        "addressable": True,
        "address_priority": 40,
        "emergent_source": src,
    }
    hint_role = actor_hint.get("role")
    if isinstance(hint_role, str) and hint_role.strip():
        row["role"] = hint_role.strip()

    emergent.append(row)
    state["emergent_addressables"] = emergent

    active_raw = state.get("active_entities")
    if isinstance(active_raw, list) and eid not in {str(x).strip() for x in active_raw if isinstance(x, str)}:
        active_raw = list(active_raw)
        active_raw.append(eid)
        state["active_entities"] = active_raw
    presence = state.get("entity_presence")
    if isinstance(presence, dict):
        presence[eid] = "active"

    return eid


_TITLED_GIVEN_NAME_RE = re.compile(
    r"\b(Lord|Lady|Sir|Ser|Dame)\s+([A-Z][a-z]{2,20})\b",
)
_WELL_DRESSED_WATCHER_RE = re.compile(r"\b(?:a|the)\s+well[- ]dressed\s+watcher\b", re.IGNORECASE)
_TOWN_CRIER_RE = re.compile(r"\b(?:a|the)\s+(?:town\s+)?crier\b", re.IGNORECASE)
_SPOTLIGHT_VERB_RE = re.compile(
    r"(?i)\b(you\s+notice|your\s+eye\s+catches|you\s+spot|nearby\s+stands|standing\s+nearby\s+is)\b",
)


def _hint_from_titled_name(match: Any, *, source: str, source_text: str) -> Dict[str, Any]:
    title = match.group(1).strip()
    given = match.group(2).strip()
    display = f"{title} {given}"
    base = slugify(f"{title}_{given}")
    eid = f"emergent_{base}"[:80]
    if not _EMERGENT_ID_RE.match(eid):
        eid = f"emergent_{slugify(given)}"
    role_slug = slugify(title)
    roles = [role_slug] if role_slug else []
    return {
        "actor_id": eid,
        "display_name": display,
        "address_roles": roles,
        "aliases": [display, given.lower(), f"{title.lower()} {given.lower()}"],
        "source": source,
        "scene_id": None,
        "_source_text": source_text,
    }


def _collect_emergent_hints_from_text(
    text: str,
    *,
    source: EmergentActorSource,
) -> List[Dict[str, Any]]:
    if not isinstance(text, str):
        return []
    s = text.strip()
    if len(s) < 12:
        return []
    hints: List[Dict[str, Any]] = []
    seen_slug: Set[str] = set()

    def _add(h: Dict[str, Any]) -> None:
        eid = str(h.get("actor_id") or "").strip()
        if not eid:
            return
        sl = slugify(eid)
        if sl in seen_slug:
            return
        seen_slug.add(sl)
        hints.append(h)

    for m in _TITLED_GIVEN_NAME_RE.finditer(s):
        h = _hint_from_titled_name(m, source=source, source_text=m.group(0).strip())
        _add(h)

    wm = _WELL_DRESSED_WATCHER_RE.search(s)
    if wm:
        verb_ok = bool(_SPOTLIGHT_VERB_RE.search(s)) or source == "promoted_visible_figure"
        if verb_ok:
            _add(
                {
                    "actor_id": "emergent_well_dressed_watcher",
                    "display_name": "Well-Dressed Watcher",
                    "address_roles": ["watcher"],
                    "aliases": ["well-dressed watcher", "the well-dressed watcher", "watcher"],
                    "source": source,
                    "scene_id": None,
                    "_source_text": wm.group(0).strip(),
                }
            )

    cm = _TOWN_CRIER_RE.search(s)
    if cm:
        verb_ok = bool(_SPOTLIGHT_VERB_RE.search(s)) or source == "promoted_visible_figure"
        if verb_ok:
            _add(
                {
                    "actor_id": "emergent_town_crier",
                    "display_name": "Town Crier",
                    "address_roles": ["crier", "town crier"],
                    "aliases": ["town crier", "the town crier", "crier"],
                    "source": source,
                    "scene_id": None,
                    "_source_text": cm.group(0).strip(),
                }
            )

    return hints


def extract_conservative_emergent_actor_hints(
    *,
    scene_id: str,
    narration_text: Optional[str],
    visible_fact_strings: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Derive at most a few enrollable actor hints from narration and visible facts (strict heuristics)."""
    sid = _clean_string(scene_id) or ""
    if not sid:
        return []
    ordered: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def _extend(src: EmergentActorSource, chunk: str) -> None:
        for h in _collect_emergent_hints_from_text(chunk, source=src):
            eid = str(h.get("actor_id") or "").strip()
            if not eid or eid in seen:
                continue
            seen.add(eid)
            nh = dict(h)
            nh["scene_id"] = sid
            ordered.append(nh)
            if len(ordered) >= 3:
                return

    vf = visible_fact_strings if isinstance(visible_fact_strings, list) else []
    for fact in vf:
        if isinstance(fact, str) and fact.strip():
            _extend("promoted_visible_figure", fact.strip())
            if len(ordered) >= 3:
                return list(ordered)

    narr = _clean_string(narration_text)
    if narr:
        _extend("emergent_narration", narr)

    return ordered


def apply_conservative_emergent_enrollment_from_gm_output(
    *,
    session: dict,
    scene: dict,
    narration_text: Optional[str],
) -> Dict[str, Any]:
    """Run detection after GM output; enroll up to a few new figures per call (conservative hints only)."""
    debug: Dict[str, Any] = {
        "emergent_actor_enrolled": False,
        "emergent_actor_id": None,
        "emergent_actor_source_text": None,
    }
    if not isinstance(session, dict) or not isinstance(scene, dict):
        return debug
    sc = scene.get("scene")
    if not isinstance(sc, dict):
        return debug
    sid = _clean_string(sc.get("id"))
    if not sid:
        return debug

    vf: List[str] = []
    vis = sc.get("visible_facts")
    if isinstance(vis, list):
        vf = [str(x) for x in vis if isinstance(x, str)]

    hints = extract_conservative_emergent_actor_hints(
        scene_id=sid,
        narration_text=narration_text,
        visible_fact_strings=vf,
    )
    for raw in hints:
        src_txt = str(raw.get("_source_text") or "").strip()
        hint = {k: v for k, v in raw.items() if not (isinstance(k, str) and k.startswith("_"))}
        enrolled = enroll_emergent_scene_actor(session=session, scene=scene, actor_hint=hint)
        if enrolled:
            debug["emergent_actor_enrolled"] = True
            debug["emergent_actor_id"] = enrolled
            debug["emergent_actor_source_text"] = src_txt or str(hint.get("display_name") or "")
    return debug
def _scene_envelope_for_addressability(
    session: Dict[str, Any] | None, scene_envelope: Dict[str, Any] | None
) -> Dict[str, Any]:
    """Resolve a scene envelope with ``scene`` + ``scene_state`` for addressability checks."""
    if isinstance(scene_envelope, dict) and isinstance(scene_envelope.get("scene"), dict):
        return scene_envelope
    sid = ""
    if isinstance(session, dict):
        st = session.get("scene_state")
        if isinstance(st, dict):
            sid = _clean_string(st.get("active_scene_id"))
        if not sid:
            sid = _clean_string(session.get("active_scene_id"))
    if sid:
        from game.storage import load_scene

        return load_scene(sid)
    return scene_envelope if isinstance(scene_envelope, dict) else {}


def scene_addressable_entity_ids_from_envelope(scene_envelope: Dict[str, Any] | None) -> Set[str]:
    """Ids listed under ``scene.addressables`` with ``addressable`` true (normalized)."""
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    return {
        str(n.get("id") or "").strip()
        for n in scene_addressables_from_envelope(env)
        if isinstance(n, dict) and str(n.get("id") or "").strip()
    }


def addressable_scene_npc_id_universe(
    session: Dict[str, Any] | None,
    scene_envelope: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    *,
    debug_checked: Optional[List[str]] = None,
) -> Set[str]:
    """Canonical id set: active_entities ∪ presence(active|nearby) ∪ scene addressables ∪ valid continuity.

    Used for social authority, strict speaker checks, and adjudication presence hints.
    """
    out: Set[str] = set()
    checked: List[str] = []
    if not isinstance(session, dict):
        if debug_checked is not None:
            debug_checked.extend(["(no session)"])
        return out

    env = _scene_envelope_for_addressability(session, scene_envelope)
    scene = env.get("scene") if isinstance(env.get("scene"), dict) else {}
    sid = _clean_string(scene.get("id"))
    if not sid:
        st0 = session.get("scene_state")
        if isinstance(st0, dict):
            sid = _clean_string(st0.get("active_scene_id")) or _clean_string(session.get("active_scene_id"))

    state = _scene_state(session)
    active_raw = state.get("active_entities")
    if isinstance(active_raw, list):
        for raw in active_raw:
            if isinstance(raw, str) and raw.strip():
                out.add(raw.strip())
    checked.append("active_entities")

    presence = state.get("entity_presence")
    if isinstance(presence, dict):
        for pid, pv in presence.items():
            peid = _clean_string(str(pid))
            if not peid:
                continue
            pv_s = str(pv or "").strip().lower()
            if pv_s in {"active", "nearby"}:
                out.add(peid)
        checked.append("entity_presence_active_or_nearby")

    spec_ids = scene_addressable_entity_ids_from_envelope(env)
    out.update(spec_ids)
    checked.append("scene_addressables")

    w = world if isinstance(world, dict) else {}
    for npc in effective_in_scene_npc_roster(w, sid or ""):
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if nid:
            out.add(nid)
    checked.append("world_roster_in_scene")

    ctx = inspect(session)
    continuity_ids: List[str] = []
    t_ctx = _clean_string(ctx.get("active_interaction_target_id"))
    if t_ctx:
        continuity_ids.append(t_ctx)
    t_il = _clean_string(state.get("current_interlocutor"))
    if t_il:
        continuity_ids.append(t_il)
    for cid in continuity_ids:
        if not cid or cid in out:
            continue
        if entity_presence_state(session, cid) == "offscene":
            continue
        if cid in spec_ids:
            out.add(cid)
            continue
        if isinstance(active_raw, list) and cid in {str(x).strip() for x in active_raw if isinstance(x, str)}:
            out.add(cid)
            continue
        if entity_presence_state(session, cid) in {"active", "nearby"}:
            out.add(cid)
            continue
        for npc in effective_in_scene_npc_roster(w, sid or ""):
            if isinstance(npc, dict) and _clean_string(npc.get("id")) == cid:
                out.add(cid)
                break
    if continuity_ids:
        checked.append("interaction_continuity")

    if debug_checked is not None:
        debug_checked.extend(checked)
    return out


def is_actor_addressable_in_current_scene(
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any] | None,
    actor_id: Optional[str],
    *,
    world: Dict[str, Any] | None = None,
    debug: Optional[Dict[str, Any]] = None,
) -> bool:
    """True when *actor_id* is part of the canonical in-scene addressable universe."""
    eid = _clean_string(actor_id)
    if not eid:
        if isinstance(debug, dict):
            debug["actor_addressable"] = False
            debug["addressability_checked_against"] = []
        return False

    checked: List[str] = []
    universe = addressable_scene_npc_id_universe(session, scene_envelope, world, debug_checked=checked)
    ok = eid in universe
    if isinstance(debug, dict):
        debug["actor_addressable"] = ok
        debug["addressability_checked_against"] = list(checked)
    return ok


def synchronize_scene_addressability(
    session: Dict[str, Any],
    scene_envelope: Optional[Dict[str, Any]],
    world: Dict[str, Any],
) -> Dict[str, Any]:
    """Rebuild active scope, align ``entity_presence`` for scene actors, clear only truly invalid interlocutors."""
    meta: Dict[str, Any] = {
        "stale_interlocutor_cleared": False,
        "addressability_checked_against": [],
    }
    env = _scene_envelope_for_addressability(session, scene_envelope)
    scene = env.get("scene") if isinstance(env.get("scene"), dict) else {}
    sid = _clean_string(scene.get("id"))
    if not sid:
        st = session.get("scene_state") if isinstance(session, dict) else None
        if isinstance(st, dict):
            sid = _clean_string(st.get("active_scene_id")) or _clean_string(
                (session or {}).get("active_scene_id")
            )
    if not sid:
        return meta

    pre_tgt = _clean_string(inspect(session).get("active_interaction_target_id"))
    rebuild_active_scene_entities(session, world, sid, scene_envelope=env)
    post_rebuild_tgt = _clean_string(inspect(session).get("active_interaction_target_id"))
    if pre_tgt and not post_rebuild_tgt:
        meta["stale_interlocutor_cleared"] = True

    universe = addressable_scene_npc_id_universe(session, env, world, debug_checked=meta["addressability_checked_against"])

    ctx = inspect(session)
    tgt = _clean_string(ctx.get("active_interaction_target_id"))
    if tgt and tgt not in universe:
        clear_for_scene_change(session)
        meta["stale_interlocutor_cleared"] = True
    else:
        st = _scene_state(session)
        if tgt:
            st["current_interlocutor"] = tgt
    return meta


def is_entity_active(session: Dict[str, Any], entity_id: Optional[str]) -> bool:
    eid = _clean_string(entity_id)
    if not eid:
        return False
    state = _scene_state(session)
    active_ids = state.get("active_entities")
    if not isinstance(active_ids, list):
        return False
    return eid in {str(x).strip() for x in active_ids if isinstance(x, str)}


def entity_presence_state(session: Dict[str, Any], entity_id: Optional[str]) -> str:
    eid = _clean_string(entity_id)
    if not eid:
        return "unknown"
    state = _scene_state(session)
    presence = state.get("entity_presence")
    if not isinstance(presence, dict):
        return "unknown"
    value = str(presence.get(eid) or "").strip().lower()
    return value if value in {"active", "nearby", "offscene", "unknown"} else "unknown"


def assert_valid_speaker(
    candidate: Optional[str],
    session: Dict[str, Any],
    *,
    scene_envelope: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
) -> bool:
    """True when *candidate* is in the canonical addressable universe (not only ``active_entities``)."""
    return is_actor_addressable_in_current_scene(session, scene_envelope, candidate, world=world)


def rebuild_active_scene_entities(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    *,
    scene_envelope: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Rebuild explicit active-scene entity scope and invalidate stale interlocutors."""
    sid = _clean_string(scene_id) or ""
    state = _scene_state(session)
    active_ids: List[str] = []
    for npc in effective_in_scene_npc_roster(world, sid):
        nid = _clean_string(npc.get("id"))
        if nid and nid not in active_ids:
            active_ids.append(nid)

    # Scene-authored entities may be present even when world location is not explicit.
    for ent_id in _scene_authored_entity_ids(scene_envelope):
        if ent_id not in active_ids:
            active_ids.append(ent_id)

    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    for ent_id in sorted(scene_addressable_entity_ids_from_envelope(env)):
        if ent_id not in active_ids:
            active_ids.append(ent_id)

    st_em = _scene_state(session)
    for row in st_em.get("emergent_addressables") or []:
        if not isinstance(row, dict):
            continue
        rsid = _clean_string(row.get("scene_id"))
        if rsid and rsid != sid:
            continue
        eid = _clean_string(row.get("id"))
        if eid and eid not in active_ids:
            active_ids.append(eid)

    presence: Dict[str, str] = {}
    active_set = set(active_ids)
    for npc_id in _all_world_npc_ids(world):
        if npc_id in active_set:
            presence[npc_id] = "active"
        else:
            presence[npc_id] = "offscene"

    for eid in active_set:
        if eid not in presence:
            presence[eid] = "active"

    state["active_scene_id"] = sid
    state["active_entities"] = active_ids
    state["entity_presence"] = presence

    ctx = inspect(session)
    current_target = _clean_string(ctx.get("active_interaction_target_id"))
    if current_target and current_target not in active_set:
        # Target left scene scope; clear social continuity so off-scene NPCs cannot answer.
        clear_for_scene_change(session)
        current_target = None

    state["current_interlocutor"] = current_target if current_target in active_set else None
    return state


def _extract_target_from_text(text: str, world: Dict[str, Any], scene_id: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    text_slug = slugify(text)
    if not text_slug:
        return None
    for npc in effective_in_scene_npc_roster(world, scene_id):
        npc_id = _clean_string(npc.get("id")) or ""
        npc_name = _clean_string(npc.get("name")) or ""
        npc_id_slug = slugify(npc_id)
        npc_name_slug = slugify(npc_name)
        if npc_id_slug and npc_id_slug in text_slug:
            return npc_id
        if npc_name_slug and npc_name_slug in text_slug:
            return npc_id
    return None


def _normalize_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize context shape and constrained literals in place."""
    target_id = _clean_string(ctx.get("active_interaction_target_id"))
    kind_raw = _clean_string(ctx.get("active_interaction_kind"))
    kind = kind_raw.lower() if kind_raw else None
    if kind and kind not in SOCIAL_INTERACTION_KINDS and kind not in NON_SOCIAL_ACTIVITY_KINDS:
        kind = None

    privacy_raw = _clean_string(ctx.get("conversation_privacy"))
    privacy = privacy_raw.lower() if privacy_raw else None
    if privacy and privacy not in CONVERSATION_PRIVACY_VALUES:
        privacy = None

    position = _clean_string(ctx.get("player_position_context"))

    mode_raw = _clean_string(ctx.get("interaction_mode"))
    mode = mode_raw.lower() if mode_raw else None
    if mode and mode not in INTERACTION_MODES:
        mode = None

    engagement_raw = _clean_string(ctx.get("engagement_level"))
    engagement = engagement_raw.lower() if engagement_raw else None
    if engagement and engagement not in ENGAGEMENT_LEVELS:
        engagement = None

    # Derive missing mode from kind for backward-compatible sessions.
    if mode is None:
        if kind in SOCIAL_INTERACTION_KINDS:
            mode = "social"
        elif kind in NON_SOCIAL_ACTIVITY_KINDS:
            mode = "activity"
        else:
            mode = "none"

    # Derive missing engagement from mode/kind for backward-compatible sessions.
    if engagement is None:
        if mode == "social":
            engagement = "engaged"
        elif mode == "activity":
            engagement = "focused" if kind in FOCUSED_ACTIVITY_KINDS else "engaged"
        else:
            engagement = "none"

    ctx["active_interaction_target_id"] = target_id
    ctx["active_interaction_kind"] = kind
    ctx["interaction_mode"] = mode
    ctx["engagement_level"] = engagement
    ctx["conversation_privacy"] = privacy
    ctx["player_position_context"] = position
    return ctx


def inspect(session: Dict[str, Any]) -> Dict[str, Any]:
    """Return normalized, mutable interaction context."""
    return _normalize_context(get_interaction_context(session))


def response_type_context_snapshot(session: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return the compact interaction snapshot used by response-type gating."""
    ctx = inspect(session if isinstance(session, dict) else {})
    return {
        "active_interaction_target_id": _clean_string(ctx.get("active_interaction_target_id")),
        "active_interaction_kind": _clean_string(ctx.get("active_interaction_kind")),
        "interaction_mode": _clean_string(ctx.get("interaction_mode")),
        "engagement_level": _clean_string(ctx.get("engagement_level")),
        "conversation_privacy": _clean_string(ctx.get("conversation_privacy")),
        "player_position_context": _clean_string(ctx.get("player_position_context")),
    }


_TURN_START_ACTIVE_INTERACTION_TARGET_KEY = "__turn_start_active_interaction_target_id"


def snapshot_turn_start_interlocutor(session: Dict[str, Any] | None) -> None:
    """Capture ``active_interaction_target_id`` before turn handlers rebind dialogue (e.g. establish)."""
    if not isinstance(session, dict):
        return
    ctx = inspect(session)
    tid = str((ctx or {}).get("active_interaction_target_id") or "").strip()
    session[_TURN_START_ACTIVE_INTERACTION_TARGET_KEY] = tid


def clear_turn_start_interlocutor_snapshot(session: Dict[str, Any] | None) -> None:
    if isinstance(session, dict) and _TURN_START_ACTIVE_INTERACTION_TARGET_KEY in session:
        del session[_TURN_START_ACTIVE_INTERACTION_TARGET_KEY]


def prior_interlocutor_for_turn_metadata(session: Dict[str, Any] | None) -> Optional[str]:
    """Binding used for continuity override metadata: turn-start snapshot, else live inspect."""
    if not isinstance(session, dict):
        return None
    snap = str(session.get(_TURN_START_ACTIVE_INTERACTION_TARGET_KEY) or "").strip()
    if snap:
        return snap
    return _clean_string(inspect(session).get("active_interaction_target_id"))


def set_interaction_mode(session: Dict[str, Any], mode: Optional[str]) -> Dict[str, Any]:
    """Set interaction mode to one of: none, social, activity."""
    ctx = inspect(session)
    clean_mode = str(mode).strip().lower() if isinstance(mode, str) else "none"
    if clean_mode not in INTERACTION_MODES:
        clean_mode = "none"
    ctx["interaction_mode"] = clean_mode
    if clean_mode == "none" and ctx.get("engagement_level") != "none":
        ctx["engagement_level"] = "none"
    return _normalize_context(ctx)


def set_engagement_level(session: Dict[str, Any], level: Optional[str]) -> Dict[str, Any]:
    """Set engagement level to one of: none, engaged, focused."""
    ctx = inspect(session)
    clean_level = str(level).strip().lower() if isinstance(level, str) else "none"
    if clean_level not in ENGAGEMENT_LEVELS:
        clean_level = "none"
    ctx["engagement_level"] = clean_level
    return _normalize_context(ctx)


def set_social_target(session: Dict[str, Any], target_id: Optional[str]) -> Dict[str, Any]:
    """Set or clear the active social target; marks interaction kind as social."""
    ctx = inspect(session)
    prior_target = _clean_string(ctx.get("active_interaction_target_id"))
    ctx["active_interaction_target_id"] = _clean_string(target_id)
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    st = _scene_state(session)
    tid = _clean_string(target_id)
    if tid != prior_target:
        clear_social_exchange_interruption_tracker(session)
    st["current_interlocutor"] = tid if tid else None
    return _normalize_context(ctx)


def clear_stale_social_interlocutor_continuity(session: Dict[str, Any]) -> Dict[str, Any]:
    """Drop active interlocutor anchor after a visible speaker mismatch (no scene transition)."""
    if not isinstance(session, dict):
        return {}
    ctx = inspect(session)
    ctx["active_interaction_target_id"] = None
    ctx["active_interaction_kind"] = None
    ctx["interaction_mode"] = "none"
    ctx["engagement_level"] = "none"
    _scene_state(session)["current_interlocutor"] = None
    clear_social_exchange_interruption_tracker(session)
    return _normalize_context(ctx)


def set_privacy(session: Dict[str, Any], privacy: Optional[str]) -> Dict[str, Any]:
    """Set conversation privacy hint; pass None to clear."""
    ctx = inspect(session)
    clean_privacy = str(privacy).strip().lower() if isinstance(privacy, str) else ""
    ctx["conversation_privacy"] = clean_privacy if clean_privacy in CONVERSATION_PRIVACY_VALUES else None
    return _normalize_context(ctx)


def set_position_context(session: Dict[str, Any], position_context: Optional[str]) -> Dict[str, Any]:
    """Set or clear player position context."""
    ctx = inspect(session)
    ctx["player_position_context"] = _clean_string(position_context)
    return _normalize_context(ctx)


def clear_emergent_scene_actors_on_scene_change(session: Dict[str, Any]) -> None:
    """Drop session-local emergent addressables when the active location changes."""
    _clear_emergent_addressables(session)


def clear_for_scene_change(session: Dict[str, Any]) -> Dict[str, Any]:
    """Clear all interaction continuity fields during scene transitions."""
    ctx = inspect(session)
    ctx["active_interaction_target_id"] = None
    ctx["active_interaction_kind"] = None
    ctx["interaction_mode"] = "none"
    ctx["engagement_level"] = "none"
    ctx["conversation_privacy"] = None
    ctx["player_position_context"] = None
    state = _scene_state(session)
    state["current_interlocutor"] = None
    clear_social_exchange_interruption_tracker(session)
    return _normalize_context(ctx)


def set_non_social_activity(session: Dict[str, Any], kind: Optional[str]) -> Dict[str, Any]:
    """Switch context to a deterministic non-social activity kind.

    Unknown kinds are ignored to avoid speculative state mutation.
    """
    ctx = inspect(session)
    clean_kind = str(kind).strip().lower() if isinstance(kind, str) else ""
    if clean_kind not in NON_SOCIAL_ACTIVITY_KINDS:
        return ctx
    ctx["active_interaction_target_id"] = None
    ctx["active_interaction_kind"] = clean_kind
    ctx["interaction_mode"] = "activity"
    ctx["engagement_level"] = "focused" if clean_kind in FOCUSED_ACTIVITY_KINDS else "engaged"
    ctx["conversation_privacy"] = None
    ctx["player_position_context"] = None
    _scene_state(session)["current_interlocutor"] = None
    clear_social_exchange_interruption_tracker(session)
    return _normalize_context(ctx)


def update_after_resolved_action(
    session: Dict[str, Any],
    kind: Optional[str],
    *,
    preserve_continuity: bool = False,
) -> Dict[str, Any]:
    """Apply deterministic continuity changes after engine resolution.

    Rules:
    - social kinds preserve social continuity and mark engagement as active.
    - non-social kinds clear active target unless continuity is explicitly preserved.
    - unknown kinds are ignored.
    """
    clean_kind = str(kind).strip().lower() if isinstance(kind, str) else ""
    ctx = inspect(session)
    if clean_kind in SOCIAL_INTERACTION_KINDS:
        if clean_kind != "social":
            ctx["active_interaction_kind"] = "social"
        ctx["interaction_mode"] = "social"
        if ctx.get("engagement_level") == "none":
            ctx["engagement_level"] = "engaged"
        return _normalize_context(ctx)
    if preserve_continuity:
        return ctx
    return set_non_social_activity(session, clean_kind)


def apply_implied_hint(
    session: Dict[str, Any],
    hint: str,
    *,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply one supported implied continuity hint.

    Supported hints:
    - lowered_voice
    - seated_with_target
    """
    ctx = inspect(session)
    clean_hint = str(hint).strip().lower()
    clean_target = str(target_id).strip() if isinstance(target_id, str) else ""

    if clean_hint == IMPLIED_HINT_LOWERED_VOICE:
        set_privacy(session, IMPLIED_HINT_LOWERED_VOICE)
        if clean_target:
            set_social_target(session, clean_target)
        return ctx

    if clean_hint == IMPLIED_HINT_SEATED_WITH_TARGET:
        set_position_context(session, IMPLIED_HINT_SEATED_WITH_TARGET)
        if clean_target:
            set_social_target(session, clean_target)
        return ctx

    return ctx


def apply_turn_input_implied_context(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    text: Optional[str],
) -> Dict[str, Any]:
    """Apply narrow implied-action continuity from raw player input.

    Scope is intentionally conservative and deterministic. This helper may only
    adjust interaction continuity fields; it must not invent targets, resolve
    mechanics, or create world outcomes.
    """
    if not isinstance(text, str):
        return {"applied": False, "cases": [], "target_id": None}
    low = text.lower().strip()
    if not low:
        return {"applied": False, "cases": [], "target_id": None}

    ctx = inspect(session)
    target_id = _extract_target_from_text(low, world, scene_id)
    active_target_id = _clean_string(ctx.get("active_interaction_target_id"))
    if target_id is None and active_target_id:
        target_id = active_target_id

    applied_cases: list[str] = []

    if any(token in low for token in _LOWERED_VOICE_TOKENS):
        apply_implied_hint(session, IMPLIED_HINT_LOWERED_VOICE, target_id=target_id)
        applied_cases.append(IMPLIED_HINT_LOWERED_VOICE)

    if target_id and any(token in low for token in _SIT_WITH_TOKENS):
        apply_implied_hint(session, IMPLIED_HINT_SEATED_WITH_TARGET, target_id=target_id)
        applied_cases.append(IMPLIED_HINT_SEATED_WITH_TARGET)

    # Courtesy/object handling remains narrow: explicit carry/place verb, item noun,
    # and target-oriented phrasing to avoid speculative interpretation.
    if (
        target_id
        and any(token in low for token in _COURTESY_MOVE_TOKENS)
        and any(token in low for token in _COURTESY_ITEM_TOKENS)
        and any(token in low for token in _COURTESY_TARGET_PREPOSITIONS)
    ):
        set_social_target(session, target_id)
        applied_cases.append("courtesy_item_to_target")

    return {
        "applied": bool(applied_cases),
        "cases": applied_cases,
        "target_id": target_id,
    }


# --- Dialogue addressing (engine-owned; keeps active_interaction_target_id in sync) ---

_NPC_REFERENCE_TITLES: tuple[str, ...] = (
    "captain",
    "guard",
    "runner",
    "footman",
    "lady",
    "lord",
    "sir",
    "madam",
)

_WORLD_ACTION_DIALOGUE_BLOCKERS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:search|sneak|attack|follow|track|cast|inspect|examine|check|investigate)\b",
    r"\b(?:i|we)\s+(?:grab|seize|shove|push|pull|pin|restrain|force|coerce|threaten)\b",
    r"\b(?:i|we)\s+(?:pick up|open|unlock|break|climb|jump|hide|steal|manipulate)\b",
    # Imperative exploration verbs (no "I …" prefix) must not hijack interlocutor continuity.
    r"^\s*(?:investigate|inspect|examine|search)\b",
)

# --- Vocative helpers (implementation); thin re-exports in game.dialogue_targeting ---

_HAILING_RE = re.compile(
    r"\b(?:you\s+there|hey\s+you|hey,?\s*you|excuse me|pardon me|pardon you|oi)\b",
    re.IGNORECASE,
)

_DIALOGUE_INFO_HINTS: tuple[str, ...] = (
    "your name",
    "their name",
    "who are you",
    "what's your name",
    "what is your name",
    "who attacked",
    "what happened",
    "tell me",
)


_VOCATIVE_PREFIX_RE = re.compile(r"^\s*([^,:\n]{1,64})\s*,")


def line_opens_with_comma_vocative(text: str) -> bool:
    """True when the line begins with a ``Name, …`` clause (syntax only; no roster)."""
    return _VOCATIVE_PREFIX_RE.match(str(text or "").strip()) is not None


def _all_npc_ids_matching_vocative_raw(
    raw: str,
    roster: List[Dict[str, Any]],
    *,
    addr_ids: Set[str] | None = None,
) -> List[str]:
    """Roster NPC ids matching a vocative ``raw`` token/phrase (same rules as comma vocative binding)."""
    voc_slug = slugify(str(raw or "").strip())
    if not voc_slug:
        return []
    out: List[str] = []
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if addr_ids is not None and nid not in addr_ids:
            continue
        hit = False
        if slugify(nid) == voc_slug or (nm and slugify(nm) == voc_slug):
            hit = True
        if not hit:
            for word in re.split(r"\s+", nm):
                w = slugify(word)
                if w and w == voc_slug:
                    hit = True
                    break
        if not hit:
            for part in slugify(nid).split("_"):
                if part and part == voc_slug:
                    hit = True
                    break
        if not hit:
            for role in npc.get("address_roles") or []:
                if isinstance(role, str) and slugify(role.strip()) == voc_slug:
                    hit = True
                    break
        if not hit:
            for alias in npc.get("aliases") or []:
                if not isinstance(alias, str):
                    continue
                if slugify(alias.strip()) == voc_slug:
                    hit = True
                    break
                for word in re.split(r"\s+", alias.strip()):
                    w = slugify(word)
                    if w and w == voc_slug:
                        hit = True
                        break
                if hit:
                    break
        if hit and nid not in out:
            out.append(nid)
    return out


def npc_id_from_vocative_line(text: str, roster: List[Dict[str, Any]]) -> str:
    """Match leading ``Name, …`` to a roster NPC id (shared with strict-social emission)."""
    m = _VOCATIVE_PREFIX_RE.match(str(text or "").strip())
    if not m:
        return ""
    raw = m.group(1).strip()
    ids = _all_npc_ids_matching_vocative_raw(raw, roster, addr_ids=None)
    return ids[0] if ids else ""


# Discourse-softened spoken vocatives:
# - ``Well, Captain, …`` — discourse word + comma, then ``Name, …``
# - ``Alright Runner, …`` — discourse word + space + ``Name, …`` (no comma after discourse)
_DISCOURSE_VOCATIVE_PREFIX_RE = re.compile(
    r"^\s*(?:alright|all\s*right|well|ok|okay|look|listen|now\s+then|so|hey)\s*,\s*",
    re.IGNORECASE,
)
_DISCOURSE_SPACE_THEN_NAME_COMMA_RE = re.compile(
    r"^\s*(?:alright|all\s*right|well|ok|okay|look|listen|now\s+then|so|hey)\s+([^,:\n]{1,64}?)\s*,",
    re.IGNORECASE,
)

_VOCATIVE_BAD_LEADING_SLUGS = frozenset(
    {"i", "we", "me", "us", "the", "a", "an", "my", "your", "it", "its", "this", "that"}
)

# Spoken label -> generic role slug for roster match (scene-local, ambiguity-aware).
_VOCATIVE_TOKEN_TO_GENERIC_ROLE: Dict[str, str] = {
    "captain": "guard",
    "watchman": "guard",
    "guardsman": "guard",
    "guardswoman": "guard",
    "sentry": "guard",
    "guard": "guard",
    "stranger": "stranger",
    "refugee": "refugee",
    "runner": "runner",
}


def _is_plausible_spoken_vocative_label(raw: str) -> bool:
    s = str(raw or "").strip()
    if len(s) < 2:
        return False
    first = s.split(None, 1)[0]
    if slugify(first) in _VOCATIVE_BAD_LEADING_SLUGS:
        return False
    return True


def _strip_leading_quotes_for_vocative(s: str) -> str:
    return re.sub(r'^[\s"\']+', "", str(s or "").strip())


def _extract_comma_vocative_phrase_after_discourse(sentence: str) -> Optional[str]:
    """Return ``Name`` from ``Name, …`` or ``<discourse>, Name, …`` at sentence start."""
    s = _strip_leading_quotes_for_vocative(str(sentence or ""))
    if not s:
        return None
    m_d = _DISCOURSE_VOCATIVE_PREFIX_RE.match(s)
    if m_d:
        s = s[m_d.end() :].lstrip()
    else:
        m_sp = _DISCOURSE_SPACE_THEN_NAME_COMMA_RE.match(s)
        if m_sp:
            raw = m_sp.group(1).strip()
            if _is_plausible_spoken_vocative_label(raw):
                return raw
            return None
    m_v = _VOCATIVE_PREFIX_RE.match(s)
    if not m_v:
        return None
    raw = m_v.group(1).strip()
    if not _is_plausible_spoken_vocative_label(raw):
        return None
    return raw


def _sentences_for_vocative_scan(text: str) -> List[str]:
    t = str(text or "").strip()
    if not t:
        return []
    chunks = re.split(r"(?<=[.!?])\s+", t)
    return [c.strip() for c in chunks if c.strip()]


def _resolve_vocative_phrase_to_roster_id(
    phrase: str,
    roster: List[Dict[str, Any]],
    addr_ids: Set[str],
) -> str:
    """Map a single vocative name/role phrase to at most one addressable roster id."""
    phrase = str(phrase or "").strip()
    if not phrase or not roster:
        return ""
    probe = f"{phrase}, "
    nid = npc_id_from_vocative_line(probe, roster)
    if nid and nid in addr_ids:
        return nid
    sl = slugify(phrase)
    if not sl:
        return ""
    role = _VOCATIVE_TOKEN_TO_GENERIC_ROLE.get(sl)
    if role:
        gr = match_generic_role_address(f"to the {role}", roster)
        if gr.get("ambiguous"):
            return ""
        gid = str(gr.get("npc_id") or "").strip()
        if gid and gid in addr_ids:
            return gid
    return ""


def _text_for_spoken_vocative_scan(
    segmented_turn: Dict[str, Any] | None,
    merged_addressing_text: str,
) -> str:
    """Prefer quoted ``spoken_text``, else declared clause, else merged addressing text."""
    if isinstance(segmented_turn, dict):
        st = _clean_string(segmented_turn.get("spoken_text"))
        if st:
            return st
        decl_only = _clean_string(segmented_turn.get("declared_action_text"))
        if decl_only:
            return decl_only
    return str(merged_addressing_text or "").strip()


def resolve_spoken_vocative_target(
    *,
    session: dict,
    scene: dict | None,
    spoken_text: str | None,
) -> dict:
    """Resolve an explicit spoken comma vocative (optionally discourse-prefixed) against the scene roster.

    Callers should pass in-character addressing text: quoted ``spoken_text`` when segmented, otherwise
    merged declared/spoken addressing text so unquoted lines like ``Alright Runner, …`` are visible.

    Returns:
        has_spoken_vocative, target_actor_id, target_source (``spoken_vocative`` when matched), reason.
    """
    out: Dict[str, Any] = {
        "has_spoken_vocative": False,
        "target_actor_id": None,
        "target_source": None,
        "reason": "",
    }
    raw = str(spoken_text or "").strip()
    if not raw:
        out["reason"] = "empty_spoken_text"
        return out
    if not isinstance(session, dict):
        out["reason"] = "no_session"
        return out
    env = scene if isinstance(scene, dict) else {}
    sc = env.get("scene")
    if not isinstance(sc, dict):
        out["reason"] = "no_scene_envelope"
        return out
    sid = _clean_string(sc.get("id"))
    if not sid:
        st = session.get("scene_state")
        if isinstance(st, dict):
            sid = _clean_string(st.get("active_scene_id")) or _clean_string(session.get("active_scene_id"))
    if not sid:
        out["reason"] = "empty_scene_id"
        return out

    from game.storage import load_world

    world = load_world()
    if not isinstance(world, dict):
        world = {}

    roster = canonical_scene_addressable_roster(
        world, sid, scene_envelope=env, session=session
    )
    universe = addressable_scene_npc_id_universe(session, env, world)
    addr_ids = universe | scene_addressable_actor_ids(world, sid, scene_envelope=env, session=session)

    sents = _sentences_for_vocative_scan(raw)
    scan_order = list(reversed(sents)) if sents else [raw]
    best_id = ""
    best_reason = "no_spoken_vocative_pattern_or_no_roster_match"
    for sent in scan_order:
        phrase = _extract_comma_vocative_phrase_after_discourse(sent)
        if not phrase:
            continue
        nid = _resolve_vocative_phrase_to_roster_id(phrase, roster, addr_ids)
        if nid:
            best_id = nid
            best_reason = "spoken_vocative_resolved_to_addressable_actor"
            break
    if not best_id:
        out["reason"] = best_reason
        return out
    if not is_actor_addressable_in_current_scene(session, env, best_id, world=world):
        out["reason"] = "spoken_vocative_target_not_addressable_in_scene"
        return out
    out["has_spoken_vocative"] = True
    out["target_actor_id"] = best_id
    out["target_source"] = "spoken_vocative"
    out["reason"] = best_reason
    return out


def _recover_conservative_emergent_actor_from_player_vocative(
    *,
    session: Dict[str, Any] | None,
    scene_envelope: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    player_text: str | None,
) -> Optional[str]:
    """Recover a missing scene-emergent actor from an exact direct vocative.

    This is intentionally narrow: only an explicit comma/discourse vocative that
    matches the existing conservative titled-name enrollment rules may mint a
    scene-local emergent addressable, and only when it would not collide with an
    authored world NPC.
    """
    if not isinstance(session, dict):
        return None
    raw = _clean_string(player_text)
    if not raw:
        return None
    phrase = _extract_comma_vocative_phrase_after_discourse(raw)
    if not phrase:
        return None

    env = _scene_envelope_for_addressability(session, scene_envelope)
    scene = env if isinstance(env, dict) else {}
    sc = scene.get("scene")
    if not isinstance(sc, dict):
        return None
    sid = _clean_string(sc.get("id"))
    if not sid:
        return None

    hints = extract_conservative_emergent_actor_hints(
        scene_id=sid,
        narration_text=phrase,
        visible_fact_strings=[],
    )
    if len(hints) != 1:
        return None

    hint = hints[0]
    eid = _clean_string(hint.get("actor_id"))
    display = _clean_string(hint.get("display_name")) or _clean_string(hint.get("name"))
    if not eid or not display:
        return None
    if _find_world_npc_dict_loose(world if isinstance(world, dict) else {}, display):
        return None
    if is_actor_addressable_in_current_scene(
        session,
        scene,
        eid,
        world=world if isinstance(world, dict) else None,
    ):
        return eid
    enrolled = enroll_emergent_scene_actor(session=session, scene=scene, actor_hint=hint)
    return _clean_string(enrolled) or None


def _merged_text_has_resolvable_spoken_vocative(merged_text: str, roster: List[Dict[str, Any]]) -> bool:
    """Roster-only cue for explicit spoken address (softened or per-sentence), without session/world."""
    if not roster:
        return False
    addr_ids = {str(x.get("id") or "").strip() for x in roster if isinstance(x, dict) and str(x.get("id") or "").strip()}
    for sent in reversed(_sentences_for_vocative_scan(str(merged_text or "").strip()) or [str(merged_text or "").strip()]):
        phrase = _extract_comma_vocative_phrase_after_discourse(sent)
        if not phrase:
            continue
        if _resolve_vocative_phrase_to_roster_id(phrase, roster, addr_ids):
            return True
    return False


# Narrow embedded vocative: "Tell me runner, who …" — leading ``Name,`` regex wrongly captures
# ``Tell me runner`` (first comma). Recover the addressed name phrase and reuse roster resolution.
_EMBEDDED_IMPERATIVE_VOCATIVE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*tell\s+me\s+([^,:\n]{1,64})\s*,", re.IGNORECASE),
    re.compile(r"^\s*let\s+me\s+ask\s+([^,:\n]{1,64})\s*,", re.IGNORECASE),
    re.compile(r"^\s*ask\s+([^,:\n]{1,64})\s*,", re.IGNORECASE),
    re.compile(r"^\s*say\s+to\s+([^,:\n]{1,64})\s*,", re.IGNORECASE),
)
_INLINE_TOKEN_COMMA_WH_RE = re.compile(
    r"(?<![\w-])([a-z][a-z0-9_-]{0,62})\s*,\s*(?:who|what|where|when|why|how|which)\b",
    re.IGNORECASE,
)


def _normalize_embedded_vocative_phrase(phrase: str) -> str:
    p = str(phrase or "").strip()
    if not p:
        return ""
    low = p.lower().strip()
    for art in ("the ", "a ", "an "):
        if low.startswith(art):
            return low[len(art) :].strip()
    return p.strip()


def _collect_embedded_direct_address_phrase_candidates(line: str) -> List[str]:
    raw = str(line or "").strip()
    if not raw:
        return []
    out: List[str] = []
    sents = _sentences_for_vocative_scan(raw) or [raw]
    for sent in sents:
        sl = sent.strip().lower()
        if not sl:
            continue
        for rx in _EMBEDDED_IMPERATIVE_VOCATIVE_RES:
            m = rx.match(sl)
            if m:
                phrase = _normalize_embedded_vocative_phrase(m.group(1))
                if phrase and _is_plausible_spoken_vocative_label(phrase):
                    out.append(phrase)
        for m in _INLINE_TOKEN_COMMA_WH_RE.finditer(sl):
            phrase = _normalize_embedded_vocative_phrase(m.group(1))
            if phrase and _is_plausible_spoken_vocative_label(phrase):
                out.append(phrase)
    seen: Set[str] = set()
    uniq: List[str] = []
    for p in out:
        key = p.casefold()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def _resolve_vocative_phrase_for_embedded_recovery(
    phrase: str,
    roster: List[Dict[str, Any]],
    addr_ids: Set[str],
) -> str:
    """Resolve a vocative phrase; fail closed when multiple roster rows match the same raw token."""
    raw = str(phrase or "").strip()
    if not raw:
        return ""
    raw_matches = _all_npc_ids_matching_vocative_raw(raw, roster, addr_ids=addr_ids)
    if len(raw_matches) > 1:
        return ""
    if len(raw_matches) == 1:
        return raw_matches[0]
    return _resolve_vocative_phrase_to_roster_id(phrase, roster, addr_ids)


def _resolve_unique_embedded_direct_address_target(
    line: str,
    roster: List[Dict[str, Any]],
    addr_ids: Set[str],
) -> str:
    """If embedded cues resolve to exactly one addressable roster id, return it; else ``''``."""
    resolved_ids: List[str] = []
    for phrase in _collect_embedded_direct_address_phrase_candidates(line):
        nid = _resolve_vocative_phrase_for_embedded_recovery(phrase, roster, addr_ids)
        if nid:
            resolved_ids.append(nid)
    uniq = list(dict.fromkeys(resolved_ids))
    if len(uniq) == 1:
        return uniq[0]
    return ""


def npc_id_from_substring_line(text: str, roster: List[Dict[str, Any]]) -> str:
    """Match full-line slug to NPC id/name (long tokens only; same rules as strict-social)."""
    text_slug = slugify(str(text or ""))
    if not text_slug:
        return ""
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        ns = slugify(nid)
        if len(ns) >= 5 and ns in text_slug:
            return nid
        if nm:
            ms = slugify(nm)
            if len(ms) >= 5 and ms in text_slug:
                return nid
    return ""


def _world_npc_dicts_for_addressing(world: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return []
    return [n for n in npcs if isinstance(n, dict) and str(n.get("id") or "").strip()]


def _active_entity_scope_ids_from_scene_envelope(scene: Dict[str, Any] | None) -> Optional[Set[str]]:
    """Non-empty active_entities on the envelope narrows addressing; empty/absent means full location roster."""
    if not isinstance(scene, dict):
        return None
    scene_state = scene.get("scene_state")
    if not isinstance(scene_state, dict):
        return None
    raw = scene_state.get("active_entities")
    if not isinstance(raw, list) or not raw:
        return None
    ids = {str(v).strip() for v in raw if isinstance(v, str) and str(v).strip()}
    return ids or None


def _active_entity_scope_ids_from_session(session: Dict[str, Any] | None, scene_id: str) -> Optional[Set[str]]:
    """Mirror of scene envelope scope using synced session.scene_state (strict-social path has no envelope)."""
    if not isinstance(session, dict):
        return None
    state = session.get("scene_state")
    if not isinstance(state, dict):
        return None
    sid = _clean_string(scene_id) or ""
    active_sid = str(state.get("active_scene_id") or "").strip()
    if sid and active_sid and active_sid != sid:
        return None
    raw = state.get("active_entities")
    if not isinstance(raw, list) or not raw:
        return None
    ids = {str(v).strip() for v in raw if isinstance(v, str) and str(v).strip()}
    return ids or None


def npc_roster_for_dialogue_addressing(
    world: Dict[str, Any],
    scene_id: str,
    *,
    scene: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Location roster optionally narrowed by active entity scope (same rules as :func:`scene_npcs_in_active_scene`)."""
    sid = _clean_string(scene_id) or ""
    roster = effective_in_scene_npc_roster(world if isinstance(world, dict) else {}, sid)
    scope: Optional[Set[str]] = None
    if scene is not None:
        scope = _active_entity_scope_ids_from_scene_envelope(scene)
    elif session is not None:
        scope = _active_entity_scope_ids_from_session(session, sid)
    if not scope:
        return list(roster)
    return [n for n in roster if isinstance(n, dict) and str(n.get("id") or "").strip() in scope]


def npc_dict_by_id(world: Dict[str, Any] | None, npc_id: str) -> Optional[Dict[str, Any]]:
    """Return the world NPC dict for ``npc_id`` if present in persisted/default npcs."""
    eid = _clean_string(npc_id)
    if not eid:
        return None
    for n in _world_npc_dicts_for_addressing(world or {}):
        if str(n.get("id") or "").strip() == eid:
            return n if isinstance(n, dict) else None
    return None


def _merge_addressable_spec_onto_row(base: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Merge scene-authored addressable metadata onto a roster row (roles, aliases, priority)."""
    out = dict(base)
    if not isinstance(spec, dict):
        return out
    for k in ("name", "role", "topics", "disposition", "affiliation"):
        if spec.get(k) is not None and (k not in out or out.get(k) in (None, "", [])):
            out[k] = spec[k]
    ar: List[str] = []
    for src in (out.get("address_roles"), spec.get("address_roles")):
        if not isinstance(src, list):
            continue
        for r in src:
            if isinstance(r, str) and r.strip():
                rl = r.strip().lower()
                if rl not in ar:
                    ar.append(rl)
    if ar:
        out["address_roles"] = ar
    al: List[str] = []
    for src in (out.get("aliases"), spec.get("aliases")):
        if not isinstance(src, list):
            continue
        for a in src:
            if isinstance(a, str) and a.strip() and a.strip() not in al:
                al.append(a.strip())
    if al:
        out["aliases"] = al
    try:
        bp = int(out.get("address_priority", 999))
    except (TypeError, ValueError):
        bp = 999
    try:
        sp = int(spec.get("address_priority", 100))
    except (TypeError, ValueError):
        sp = 100
    out["address_priority"] = min(bp, sp)
    if spec.get("kind") in SCENE_ADDRESSABLE_KINDS:
        out["kind"] = spec["kind"]
    return out


def canonical_scene_addressable_roster(
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Addressable actors for dialogue binding: in-scene world NPCs, scene ``addressables``, active scope.

    Scene ``addressables`` need not exist in ``world.npcs``. Rows match the lightweight schema
    (``id``, ``name``, ``address_roles``, ``aliases``, ``kind``, ``address_priority``, …).
    """
    sid = _clean_string(scene_id) or ""
    env = scene_envelope if isinstance(scene_envelope, dict) else None
    specs = scene_addressables_from_envelope(env) if env else []
    spec_by_id: Dict[str, Dict[str, Any]] = {}
    for s in specs:
        if not isinstance(s, dict):
            continue
        eid = str(s.get("id") or "").strip()
        if eid:
            spec_by_id[eid] = s

    emergent_by_id: Dict[str, Dict[str, Any]] = {}
    if isinstance(session, dict):
        st = session.get("scene_state")
        if isinstance(st, dict):
            active_sid = str(st.get("active_scene_id") or "").strip()
            if (not sid or not active_sid or active_sid == sid):
                for row in st.get("emergent_addressables") or []:
                    if not isinstance(row, dict):
                        continue
                    eid = str(row.get("id") or "").strip()
                    rsid = _clean_string(row.get("scene_id"))
                    if not eid or (rsid and rsid != sid):
                        continue
                    norm = _normalize_scene_addressable_actor(row, sid)
                    if norm and norm.get("addressable", True):
                        emergent_by_id[eid] = norm

    base = npc_roster_for_dialogue_addressing(
        world or {},
        sid,
        scene=env,
        session=session if isinstance(session, dict) else None,
    )
    acc: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []

    def _put(row: Dict[str, Any]) -> None:
        nid = str(row.get("id") or "").strip()
        if not nid:
            return
        if nid not in acc:
            acc[nid] = dict(row)
            order.append(nid)
        else:
            acc[nid] = _merge_addressable_spec_onto_row(acc[nid], row)

    for n in base:
        if not isinstance(n, dict):
            continue
        row = dict(n)
        nid = str(row.get("id") or "").strip()
        if nid and nid in spec_by_id:
            row = _merge_addressable_spec_onto_row(row, spec_by_id[nid])
        if nid and nid in emergent_by_id:
            row = _merge_addressable_spec_onto_row(row, emergent_by_id[nid])
        _put(row)

    for s in specs:
        nid = str(s.get("id") or "").strip()
        if nid and nid not in acc:
            _put(dict(s))

    for eid, em in emergent_by_id.items():
        if eid not in acc:
            _put(dict(em))

    seen_ids = set(acc.keys())
    if isinstance(session, dict):
        state = session.get("scene_state")
        if isinstance(state, dict):
            active_sid = str(state.get("active_scene_id") or "").strip()
            if (not sid or not active_sid or active_sid == sid) and isinstance(state.get("active_entities"), list):
                for raw in state["active_entities"]:
                    eid = str(raw).strip() if isinstance(raw, str) else ""
                    if not eid or eid in seen_ids:
                        continue
                    npc = npc_dict_by_id(world, eid)
                    spec = spec_by_id.get(eid)
                    em = emergent_by_id.get(eid)
                    if npc:
                        row = dict(npc)
                        if spec:
                            row = _merge_addressable_spec_onto_row(row, spec)
                        if em:
                            row = _merge_addressable_spec_onto_row(row, em)
                        _put(row)
                    elif spec:
                        row = dict(spec)
                        if em:
                            row = _merge_addressable_spec_onto_row(row, em)
                        _put(row)
                    elif em:
                        _put(dict(em))
                    else:
                        _put({"id": eid, "name": eid.replace("_", " ").title()})
                    seen_ids.add(eid)

    return [acc[i] for i in order if i in acc]


def scene_addressable_actor_ids(
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> Set[str]:
    """Set of NPC ids from :func:`canonical_scene_addressable_roster`."""
    return {
        str(n.get("id") or "").strip()
        for n in canonical_scene_addressable_roster(
            world, scene_id, scene_envelope=scene_envelope, session=session
        )
        if isinstance(n, dict) and str(n.get("id") or "").strip()
    }


def _find_world_npc_dict_loose(world: Dict[str, Any] | None, hint: str) -> Optional[Dict[str, Any]]:
    """Match an NPC anywhere in the world by id or name slug (ignores scene)."""
    h = _clean_string(hint)
    if not h:
        return None
    hs = slugify(h)
    for npc in _world_npc_dicts_for_addressing(world or {}):
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if nid == h or nid.lower() == h.lower():
            return npc
        if hs and (slugify(nid) == hs or hs in slugify(nid)):
            return npc
        if nm and (nm.lower() == h.lower() or slugify(nm) == hs or hs in slugify(nm)):
            return npc
    return None


def _display_name_for_npc_entry(npc: Dict[str, Any] | None, npc_id: str) -> Optional[str]:
    if isinstance(npc, dict):
        nm = _clean_string(npc.get("name"))
        if nm:
            return nm
    nid = _clean_string(npc_id)
    if not nid:
        return None
    return nid.replace("_", " ").replace("-", " ").title()


def session_allows_implicit_social_reply_authority(session: Dict[str, Any] | None) -> bool:
    """True when continuity-based and first-roster ambient targeting may license NPC reply authority.

    After an explicit non-social activity (``interaction_mode`` is ``activity`` or
    ``active_interaction_kind`` is in :data:`NON_SOCIAL_ACTIVITY_KINDS`), implicit paths must not
    resurrect stale NPC dialogue. Cold-open sessions (mode ``none`` without a non-social kind)
    still allow :func:`resolve_authoritative_social_target` section G when enabled.
    """
    if not isinstance(session, dict):
        return False
    ctx = inspect(session)
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
    if mode == "activity":
        return False
    if kind in NON_SOCIAL_ACTIVITY_KINDS:
        return False
    return True


AuthoritativeSocialSource = Literal[
    "explicit_target",
    "declared_action",
    "spoken_vocative",
    "vocative",
    "generic_role",
    "continuity",
    "substring",
    "first_roster",
    "none",
]

# --- Authoritative target resolver (single precedence-ordered engine binding; stays here: cycle-safe) ---


def resolve_authoritative_social_target(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    player_text: str | None = None,
    normalized_action: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    merged_player_prompt: str | None = None,
    allow_first_roster_fallback: bool = False,
    segmented_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Single precedence-ordered resolver for who the player is addressing in-scene.

    Precedence: explicit normalized target → declared-action actor switch → spoken vocative
    (comma / discourse-prefixed, roster-aware) → comma vocative / directed name → embedded direct
    address (``tell me X, …``, ``X, who|what|…`` when uniquely resolvable) → generic role →
    active interaction continuity → conservative substring → optional first roster → none.

    Owns: final ``npc_id`` / ``npc_name`` for engine social resolution and strict-social emission
    alignment. Downstream narration may paraphrase; it must not substitute a different NPC id.

    Callers that emit or validate social output should use this result instead of re-deriving
    ``npc_id`` in a different order (prevents wiping a valid engine target on follow-up lines).
    """
    sid = _clean_string(scene_id) or ""
    w = world if isinstance(world, dict) else {}

    line_raw = _clean_string(merged_player_prompt) or _clean_string(player_text) or ""
    p_voc = str(line_raw).strip()
    low = line_raw.lower()
    prior_interlocutor: Optional[str] = prior_interlocutor_for_turn_metadata(
        session if isinstance(session, dict) else None
    )

    decl_sw: Dict[str, Any] = {}
    voc_res: Dict[str, Any] = {}

    def _result(
        npc_id: Optional[str],
        npc_name: Optional[str],
        *,
        target_resolved: bool,
        offscene_target: bool,
        source: AuthoritativeSocialSource,
        reason: str,
        generic_role_rebind: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        nid = _clean_string(npc_id)
        nm = _clean_string(npc_name)
        vr = voc_res if isinstance(voc_res, dict) else {}
        out: Dict[str, Any] = {
            "npc_id": nid,
            "npc_name": nm,
            "target_resolved": bool(target_resolved),
            "offscene_target": bool(offscene_target),
            "source": source,
            "reason": reason,
        }
        if generic_role_rebind is not None:
            out["generic_role_rebind"] = generic_role_rebind
        out["declared_switch_detected"] = bool(decl_sw.get("has_declared_switch"))
        out["declared_switch_target_actor_id"] = (
            decl_sw.get("target_actor_id") if decl_sw.get("has_declared_switch") else None
        )
        decl_tid = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
        out["continuity_overridden_by_declared_switch"] = bool(
            prior_interlocutor
            and nid
            and prior_interlocutor != nid
            and (
                source == "declared_action"
                or (
                    source == "explicit_target"
                    and decl_tid
                    and decl_tid == nid
                )
            )
        )
        out["spoken_vocative_detected"] = bool(vr.get("has_spoken_vocative"))
        out["spoken_vocative_target_actor_id"] = (
            vr.get("target_actor_id") if vr.get("has_spoken_vocative") else None
        )
        voc_tid = str(vr.get("target_actor_id") or "").strip()
        out["continuity_overridden_by_spoken_vocative"] = bool(
            prior_interlocutor
            and nid
            and prior_interlocutor != nid
            and (
                source == "spoken_vocative"
                or (
                    source == "explicit_target"
                    and vr.get("has_spoken_vocative")
                    and voc_tid
                    and voc_tid == nid
                )
            )
        )
        return out

    if not sid:
        return _result(
            None,
            None,
            target_resolved=False,
            offscene_target=False,
            source="none",
            reason="empty scene_id",
        )

    sess = session if isinstance(session, dict) else None
    env = _scene_envelope_for_addressability(
        sess,
        scene_envelope if isinstance(scene_envelope, dict) else None,
    )
    _recover_conservative_emergent_actor_from_player_vocative(
        session=sess,
        scene_envelope=env,
        world=w,
        player_text=line_raw,
    )

    def _roster_context() -> tuple[List[Dict[str, Any]], Set[str]]:
        roster_local = canonical_scene_addressable_roster(
            w, sid, scene_envelope=env, session=sess
        )
        universe_local = addressable_scene_npc_id_universe(
            sess,
            env,
            w,
        )
        seen_roster_local = {
            str(x.get("id") or "").strip() for x in roster_local if isinstance(x, dict)
        }
        env_for_specs = env if isinstance(env, dict) else {}
        addr_specs = {
            str(s.get("id") or "").strip(): s
            for s in scene_addressables_from_envelope(env_for_specs)
            if isinstance(s, dict)
        }
        for uid in sorted(universe_local):
            if not uid or uid in seen_roster_local:
                continue
            seen_roster_local.add(uid)
            n = npc_dict_by_id(w, uid)
            if isinstance(n, dict):
                roster_local.append(dict(n))
                continue
            spec = addr_specs.get(uid)
            if isinstance(spec, dict):
                roster_local.append(dict(spec))
            else:
                roster_local.append({"id": uid, "name": _display_name_for_npc_entry(None, uid) or uid})
        addr_ids_local = universe_local | scene_addressable_actor_ids(
            w, sid, scene_envelope=env, session=sess
        )
        return roster_local, addr_ids_local

    roster, addr_ids = _roster_context()

    decl_sw = resolve_declared_actor_switch(
        session=sess or {},
        scene=env if isinstance(env, dict) else {},
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=line_raw,
    )
    voc_scan = _text_for_spoken_vocative_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        line_raw,
    )
    voc_res = resolve_spoken_vocative_target(
        session=sess or {},
        scene=env if isinstance(env, dict) else None,
        spoken_text=voc_scan,
    )

    na = normalized_action if isinstance(normalized_action, dict) else {}
    explicit = _clean_string(na.get("target_id")) or _clean_string(na.get("targetEntityId"))

    # --- A. Explicit normalized target_id / targetEntityId ---
    if explicit:
        if explicit in addr_ids:
            npc = npc_dict_by_id(w, explicit) or next(
                (x for x in roster if str(x.get("id") or "").strip() == explicit), None
            )
            return _result(
                explicit,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, explicit),
                target_resolved=True,
                offscene_target=False,
                source="explicit_target",
                reason="normalized target_id matches scene-addressable roster",
            )
        slug_matched_id = ""
        exs = slugify(explicit)
        if exs:
            for npc in roster:
                if not isinstance(npc, dict):
                    continue
                nid = str(npc.get("id") or "").strip()
                nm = str(npc.get("name") or "").strip()
                if not nid:
                    continue
                if exs == slugify(nid) or (nm and exs == slugify(nm)):
                    slug_matched_id = nid
                    break
        if slug_matched_id:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == slug_matched_id), None)
            return _result(
                slug_matched_id,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, slug_matched_id),
                target_resolved=True,
                offscene_target=False,
                source="explicit_target",
                reason="normalized target string slug-matched a scene-addressable NPC",
            )
        known = _find_world_npc_dict_loose(w, explicit)
        if isinstance(known, dict):
            kid = str(known.get("id") or "").strip()
            knm = _display_name_for_npc_entry(known, kid)
            return _result(
                kid or None,
                knm,
                target_resolved=False,
                offscene_target=True,
                source="explicit_target",
                reason="explicit target names a known NPC not in scene-addressable roster",
            )
        # Unrecognized explicit hint: fall through to text-based resolution.

    # --- B. Declared-action actor switch (segmented declared clause beats continuity) ---
    decl_id = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
    if decl_id and decl_id in addr_ids:
        npc = npc_dict_by_id(w, decl_id) or next(
            (x for x in roster if str(x.get("id") or "").strip() == decl_id), None
        )
        return _result(
            decl_id,
            _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, decl_id),
            target_resolved=True,
            offscene_target=False,
            source="declared_action",
            reason="declared_action_phrase_resolved_before_vocative_or_continuity",
        )

    # --- B2. Spoken vocative (discourse-prefixed or late-sentence comma address; beats continuity) ---
    voc_tid = _clean_string(voc_res.get("target_actor_id")) if voc_res.get("has_spoken_vocative") else ""
    if voc_tid and voc_tid in addr_ids:
        npc = npc_dict_by_id(w, voc_tid) or next(
            (x for x in roster if str(x.get("id") or "").strip() == voc_tid), None
        )
        return _result(
            voc_tid,
            _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, voc_tid),
            target_resolved=True,
            offscene_target=False,
            source="spoken_vocative",
            reason=str(voc_res.get("reason") or "spoken_vocative_resolved_to_addressable_actor"),
        )

    # --- C. Comma vocative or leading/directed named address (roster then world) ---
    if p_voc:
        voc = npc_id_from_vocative_line(p_voc, roster)
        if voc and voc in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == voc), None)
            return _result(
                voc,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, voc),
                target_resolved=True,
                offscene_target=False,
                source="vocative",
                reason="comma vocative matched scene-addressable roster",
            )
        emb = _resolve_unique_embedded_direct_address_target(p_voc, roster, addr_ids)
        if emb and emb in addr_ids and is_actor_addressable_in_current_scene(
            sess or {},
            env if isinstance(env, dict) else {},
            emb,
            world=w,
        ):
            npc = next((x for x in roster if str(x.get("id") or "").strip() == emb), None)
            return _result(
                emb,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, emb),
                target_resolved=True,
                offscene_target=False,
                source="vocative",
                reason="embedded direct address recovered unique scene-addressable target",
            )
        wroster = _world_npc_dicts_for_addressing(w)
        voc_w = npc_id_from_vocative_line(p_voc, wroster)
        if voc_w:
            if voc_w in addr_ids:
                npc = npc_dict_by_id(w, voc_w)
                return _result(
                    voc_w,
                    _display_name_for_npc_entry(npc, voc_w),
                    target_resolved=True,
                    offscene_target=False,
                    source="vocative",
                    reason="comma vocative matched world NPC present in scene",
                )
            npc_off = npc_dict_by_id(w, voc_w)
            return _result(
                voc_w,
                _display_name_for_npc_entry(npc_off, voc_w),
                target_resolved=False,
                offscene_target=True,
                source="vocative",
                reason="comma vocative matched an NPC not addressable in this scene",
            )
        if roster and low:
            lead = _explicit_addressed_npc_id_leading_or_directed(low, roster)
            if lead and lead in addr_ids:
                npc = next((x for x in roster if str(x.get("id") or "").strip() == lead), None)
                return _result(
                    lead,
                    _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, lead),
                    target_resolved=True,
                    offscene_target=False,
                    source="vocative",
                    reason="leading or directed named address matched roster",
                )

    # --- D. Explicit generic role address ---
    if low and roster:
        gr = match_generic_role_address(low, roster)
        if gr.get("ambiguous"):
            return _result(
                None,
                None,
                target_resolved=False,
                offscene_target=False,
                source="none",
                reason="ambiguous generic role address among scene addressables",
            )
        gen = str(gr.get("npc_id") or "").strip()
        if not gen and prior_interlocutor:
            spoken_slug = _last_spoken_generic_role_slug(low)
            norm_spoken = _normalize_spoken_generic_role_slug(spoken_slug)
            if norm_spoken == "guard":
                guard_hits = [
                    str(n.get("id") or "").strip()
                    for n in roster
                    if isinstance(n, dict) and _npc_matches_normalized_generic_role(n, "guard")
                ]
                guard_hits = [g for g in guard_hits if g and g in addr_ids]
                if len(guard_hits) == 1:
                    gen = guard_hits[0]
                    gr = {
                        "npc_id": gen,
                        "matched_role": spoken_slug or norm_spoken,
                        "ambiguous": False,
                    }
        if gen and gen in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == gen), None)
            rebind_meta = {
                "source": "generic_role",
                "matched_role": gr.get("matched_role"),
                "matched_actor_id": gen,
                "continuity_overridden": bool(prior_interlocutor and prior_interlocutor != gen),
            }
            return _result(
                gen,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, gen),
                target_resolved=True,
                offscene_target=False,
                source="generic_role",
                reason="generic role phrase matched a scene-addressable actor",
                generic_role_rebind=rebind_meta,
            )
        role_spoken = _last_spoken_generic_role_slug(low)
        if role_spoken and not gen:
            return _result(
                None,
                None,
                target_resolved=False,
                offscene_target=False,
                source="none",
                reason="generic role address had no matching scene actor",
            )

    # --- E. Active interaction continuity ---
    if isinstance(session, dict) and session_allows_implicit_social_reply_authority(session):
        ctx = inspect(session)
        active = _clean_string(ctx.get("active_interaction_target_id"))
        if active and active in addr_ids:
            npc = npc_dict_by_id(w, active) or next(
                (x for x in roster if str(x.get("id") or "").strip() == active), None
            )
            return _result(
                active,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, active),
                target_resolved=True,
                offscene_target=False,
                source="continuity",
                reason="active_interaction_target_id is scene-addressable",
            )

    # --- F. Conservative substring / name overlap ---
    if line_raw and roster:
        sub = npc_id_from_substring_line(line_raw, roster)
        if sub and sub in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == sub), None)
            return _result(
                sub,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, sub),
                target_resolved=True,
                offscene_target=False,
                source="substring",
                reason="conservative slug substring matched one roster NPC",
            )

    # --- G. First roster (strict-social emission fallback only) ---
    if (
        allow_first_roster_fallback
        and roster
        and isinstance(session, dict)
        and session_allows_implicit_social_reply_authority(session)
    ):
        first = str(roster[0].get("id") or "").strip()
        if first:
            npc = roster[0] if isinstance(roster[0], dict) else None
            return _result(
                first,
                _display_name_for_npc_entry(npc, first),
                target_resolved=True,
                offscene_target=False,
                source="first_roster",
                reason="first scene-addressable roster NPC (strict-social fallback)",
            )

    return _result(
        None,
        None,
        target_resolved=False,
        offscene_target=False,
        source="none",
        reason="no addressable target resolved",
    )


def _session_turn_counter_for_speaker_contract(session: Dict[str, Any] | None) -> int:
    if not isinstance(session, dict):
        return 0
    try:
        return int(session.get("turn_counter") or 0)
    except (TypeError, ValueError):
        return 0


def _compose_speaker_selection_contract(
    *,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    scene_envelope: Dict[str, Any] | None,
    merged_player_prompt: str,
    resolution: Dict[str, Any] | None,
    authoritative_target: Dict[str, Any],
    social_grounding_slice: Dict[str, Any],
    strict_social_active: bool,
    debug_extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the public speaker-selection dict from post-promotion auth + grounded social slice."""
    from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

    sid = _clean_string(scene_id) or ""
    auth = authoritative_target if isinstance(authoritative_target, dict) else {}
    soc = social_grounding_slice if isinstance(social_grounding_slice, dict) else {}
    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else {}
    env = scene_envelope if isinstance(scene_envelope, dict) else None

    neutral_bridge = bool(soc.get("reply_speaker_grounding_neutral_bridge"))
    pid = _clean_string(soc.get("npc_id"))
    primary_id: Optional[str] = None
    if not neutral_bridge and pid:
        primary_id = pid

    if bool(auth.get("offscene_target")):
        primary_id = None

    allowed: List[str] = []
    if primary_id and sid and sess is not None:
        if is_actor_addressable_in_current_scene(sess, env, primary_id, world=w):
            allowed = [primary_id]
        else:
            primary_id = None
    elif primary_id and sess is None:
        primary_id = None

    auth_src = str(auth.get("source") or "").strip()
    primary_name: Optional[str] = None
    primary_source: Optional[str] = None
    if primary_id:
        primary_name = _clean_string(soc.get("npc_name")) or _clean_string(auth.get("npc_name"))
        if not primary_name:
            primary_name = _display_name_for_npc_entry(None, primary_id)
        primary_source = auth_src or None

    generic_fallback_forbidden = not bool(allowed)
    if strict_social_active and neutral_bridge:
        generic_fallback_forbidden = True

    continuity_locked = len(allowed) == 1
    continuity_lock_reason: Optional[str] = None
    if continuity_locked:
        continuity_lock_reason = "single_grounded_in_scene_speaker"
    elif strict_social_active and not allowed:
        continuity_lock_reason = "strict_social_no_grounded_in_scene_speaker"

    decl = bool(auth.get("declared_switch_detected")) or bool(auth.get("continuity_overridden_by_declared_switch"))
    voc = bool(auth.get("spoken_vocative_detected")) or bool(auth.get("continuity_overridden_by_spoken_vocative"))
    speaker_switch_allowed = False
    speaker_switch_reason: Optional[str] = None
    if decl:
        speaker_switch_allowed = True
        speaker_switch_reason = "declared_actor_switch"
    elif voc:
        speaker_switch_allowed = True
        speaker_switch_reason = "spoken_vocative_or_explicit_address"
    elif auth_src in ("explicit_target", "declared_action", "spoken_vocative", "vocative", "generic_role", "substring"):
        speaker_switch_allowed = True
        speaker_switch_reason = f"authoritative_source:{auth_src}"
    elif auth_src == "first_roster":
        speaker_switch_allowed = False
        speaker_switch_reason = "first_roster_ambient_no_explicit_player_redirect"
    elif auth_src == "continuity":
        speaker_switch_allowed = False
        speaker_switch_reason = "continuity_preserves_active_interlocutor"
    elif auth_src in ("none",):
        speaker_switch_allowed = True
        speaker_switch_reason = "no_authoritative_pin"
    elif not auth_src:
        speaker_switch_allowed = True
        speaker_switch_reason = "no_authoritative_pin"
    else:
        speaker_switch_allowed = True
        speaker_switch_reason = f"authoritative_source:{auth_src or 'unknown'}"

    tracker = get_social_exchange_interruption_tracker(sess)
    tracker_substantive = bool(
        str(tracker.get("interruption_signature") or "").strip()
        or str(tracker.get("last_emitted_text") or "").strip()
    )
    if tracker_substantive:
        speaker_switch_allowed = True
        speaker_switch_reason = "session_interruption_tracker_suggests_scene_breakoff_continuity"

    interruption_allowed = bool(strict_social_active or primary_id)
    interruption_requires_scene_event = bool(strict_social_active and continuity_locked)

    why_speaker = (
        f"grounded_in_scene_npc:{primary_id};authority_source={auth_src};grounding={str(soc.get('grounding_reason_code') or '').strip() or 'n/a'}"
        if primary_id
        else (
            "no_in_scene_speaker_after_authoritative_resolution_and_grounding"
            if bool(auth.get("target_resolved"))
            else "authoritative_target_unresolved"
        )
    )
    dbg: Dict[str, Any] = {
        "merged_player_prompt_preview": (merged_player_prompt[:140] + "…")
        if len(merged_player_prompt) > 140
        else merged_player_prompt,
        "strict_social_active": strict_social_active,
        "authoritative_source": auth_src or None,
        "authoritative_reason": str(auth.get("reason") or "").strip() or None,
        "grounding_reason_code": str(soc.get("grounding_reason_code") or "").strip() or None,
        "grounding_fallback_applied": bool(soc.get("grounding_fallback_applied")),
        "neutral_reply_bridge": neutral_bridge,
        "why_speaker_chosen": why_speaker,
        "why_continuity_locked_or_not": continuity_lock_reason,
        "why_switch_permitted_or_not": speaker_switch_reason,
        "interruption_tracker_active": tracker_substantive,
    }
    if isinstance(debug_extras, dict) and debug_extras:
        dbg = {**dbg, **debug_extras}

    return {
        "primary_speaker_id": primary_id,
        "primary_speaker_name": primary_name,
        "primary_speaker_source": primary_source,
        "allowed_speaker_ids": list(allowed),
        "continuity_locked": continuity_locked,
        "continuity_lock_reason": continuity_lock_reason,
        "speaker_switch_allowed": speaker_switch_allowed,
        "speaker_switch_reason": speaker_switch_reason,
        "generic_fallback_forbidden": generic_fallback_forbidden,
        "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
        "interruption_allowed": interruption_allowed,
        "interruption_requires_scene_event": interruption_requires_scene_event,
        "offscene_speakers_forbidden": True,
        "debug": dbg,
    }


def build_speaker_selection_contract(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    resolution: Optional[Dict[str, Any]] = None,
    normalized_action: Optional[Dict[str, Any]] = None,
    scene_envelope: Optional[Dict[str, Any]] = None,
    merged_player_prompt: Optional[str] = None,
    _engine_authoritative_target: Optional[Dict[str, Any]] = None,
    _engine_grounded_social: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Engine-authored contract: who may speak, continuity lock, switch and interruption policy.

    Downstream prompting and emission should read this object instead of re-deriving speaker
    authority from scattered flags.

    When ``_engine_authoritative_target`` and ``_engine_grounded_social`` are provided (strict-social
    reconcile path), authoritative resolution is not re-run.
    """
    from game.social import apply_social_reply_speaker_grounding, finalize_social_target_with_promotion
    from game.social_exchange_emission import merged_player_prompt_for_gate, should_apply_strict_social_exchange_emission

    sid = _clean_string(scene_id) or ""
    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else {}
    if not sid:
        return _compose_speaker_selection_contract(
            session=sess,
            world=w,
            scene_id=sid,
            scene_envelope=None,
            merged_player_prompt="",
            resolution=resolution if isinstance(resolution, dict) else None,
            authoritative_target={},
            social_grounding_slice={},
            strict_social_active=False,
            debug_extras={"contract_aborted": "empty_scene_id"},
        )

    res = resolution if isinstance(resolution, dict) else None
    na = normalized_action if isinstance(normalized_action, dict) else None
    if na is None and res is not None:
        meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
        na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else None

    env = scene_envelope if isinstance(scene_envelope, dict) else None
    if env is None and sess is not None:
        env = _scene_envelope_for_addressability(sess, None)

    merged = str(merged_player_prompt or "").strip()
    if not merged and res is not None and sess is not None:
        merged = merged_player_prompt_for_gate(res, sess, sid)

    hint = ""
    if sess is not None:
        from game.storage import get_scene_runtime

        rt = get_scene_runtime(sess, sid)
        hint = str(rt.get("last_player_action_text") or "").strip()

    strict_social = False
    if sess is not None:
        strict_social = should_apply_strict_social_exchange_emission(
            res,
            sess,
            scene_runtime_prompt=hint or None,
            scene_id=sid,
            world=w,
        )

    if _engine_authoritative_target is not None and _engine_grounded_social is not None:
        return _compose_speaker_selection_contract(
            session=sess,
            world=w,
            scene_id=sid,
            scene_envelope=env,
            merged_player_prompt=merged,
            resolution=res,
            authoritative_target=_engine_authoritative_target,
            social_grounding_slice=_engine_grounded_social,
            strict_social_active=strict_social,
            debug_extras={"resolution_path": "engine_reuse_strict_reconcile"},
        )

    allow_fr = bool(strict_social)
    auth = resolve_authoritative_social_target(
        sess,
        w,
        sid,
        player_text=merged,
        normalized_action=na,
        scene_envelope=env,
        merged_player_prompt=merged,
        allow_first_roster_fallback=allow_fr,
    )
    res_kind = str((res or {}).get("kind") or "").strip()
    auth, _, _ = finalize_social_target_with_promotion(
        sess if sess is not None else {},
        w,
        sid,
        auth,
        action_type=res_kind,
        turn_counter=_session_turn_counter_for_speaker_contract(sess),
        scene_envelope=env,
        raw_player_text=merged or None,
    )

    soc_probe: Dict[str, Any] = {
        "npc_id": _clean_string(auth.get("npc_id")),
        "target_resolved": bool(auth.get("target_resolved")),
        "npc_name": _clean_string(auth.get("npc_name")),
    }
    apply_social_reply_speaker_grounding(
        soc_probe,
        sess if sess is not None else {},
        w,
        sid,
        env,
        auth,
        proposed_reply_speaker_id=_clean_string(auth.get("npc_id")),
    )

    return _compose_speaker_selection_contract(
        session=sess,
        world=w,
        scene_id=sid,
        scene_envelope=env,
        merged_player_prompt=merged,
        resolution=res,
        authoritative_target=auth,
        social_grounding_slice=soc_probe,
        strict_social_active=strict_social,
        debug_extras={"resolution_path": "full_authoritative_resolve_plus_grounding"},
    )


# Narrow spoken roles for explicit generic addressing (scene-local roster match only).
_GENERIC_ADDRESS_ROLE_ALT = r"(?:guardsman|guardswoman|watchman|sentry|stranger|refugee|merchant|runner|guard)"
_GENERIC_ADDRESS_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(rf"\byou\s*,\s*({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\byou\s+there,?\s*({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\bto\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\btowards?\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"^\s*({_GENERIC_ADDRESS_ROLE_ALT})\b(?:\s*[,:?!]|\s+)"),
)

_SPOKEN_ROLE_TO_CANONICAL: Dict[str, str] = {
    "guardsman": "guard",
    "guardswoman": "guard",
    "watchman": "guard",
    "sentry": "guard",
}


def _normalize_spoken_generic_role_slug(raw: str) -> str:
    s = str(raw or "").strip().lower()
    return _SPOKEN_ROLE_TO_CANONICAL.get(s, s)


def generic_address_slugs_for_npc(npc: Dict[str, Any]) -> Set[str]:
    """Deterministic role tokens from authored NPC fields (id/name/role) for generic-address matching."""
    out: Set[str] = set()
    if not isinstance(npc, dict):
        return out
    role = npc.get("role")
    if isinstance(role, str) and role.strip():
        rs = slugify(role.strip())
        if rs:
            out.add(rs)
    nid = str(npc.get("id") or "").strip()
    for part in nid.split("_"):
        ps = slugify(part)
        if ps and len(ps) >= 3:
            out.add(ps)
    name = str(npc.get("name") or "").strip()
    for word in re.split(r"\s+", name):
        ws = slugify(word)
        if ws and len(ws) >= 3:
            out.add(ws)
    for r in npc.get("address_roles") or []:
        if isinstance(r, str) and r.strip():
            rs = slugify(r.strip())
            if rs and len(rs) >= 3:
                out.add(rs)
    for a in npc.get("aliases") or []:
        if isinstance(a, str) and a.strip():
            for word in re.split(r"\s+", a.strip()):
                ws = slugify(word)
                if ws and len(ws) >= 3:
                    out.add(ws)
    return out


def _npc_matches_normalized_generic_role(npc: Dict[str, Any], normalized_slug: str) -> bool:
    if not normalized_slug:
        return False
    slugs = generic_address_slugs_for_npc(npc)
    return normalized_slug in slugs


def _last_spoken_generic_role_slug(low: str) -> str:
    """Return the last explicit generic role token in the line (so ``… to the runner`` beats earlier mentions)."""
    best_end = -1
    best_slug = ""
    for pat in _GENERIC_ADDRESS_PATTERNS:
        for m in pat.finditer(low):
            if m.end() > best_end:
                best_end = m.end()
                best_slug = _normalize_spoken_generic_role_slug(m.group(1))
    return best_slug


def match_generic_role_address(low: str, addressable_npcs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve generic role phrases to a single roster id, or mark ``ambiguous`` when priorities tie."""
    line = str(low or "").strip().lower()
    out: Dict[str, Any] = {}
    if not line or not addressable_npcs:
        return out
    role = _last_spoken_generic_role_slug(line)
    if not role:
        return out
    out["matched_role"] = role
    scored: List[Tuple[str, int]] = []
    for n in addressable_npcs:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or "").strip()
        if not nid or not _npc_matches_normalized_generic_role(n, role):
            continue
        try:
            pri = int(n.get("address_priority", 500))
        except (TypeError, ValueError):
            pri = 500
        scored.append((nid, pri))
    if not scored:
        return {}
    best_pri = min(p for _, p in scored)
    tier = [nid for nid, p in scored if p == best_pri]
    tier.sort()
    if len(tier) > 1:
        out["ambiguous"] = True
        return out
    out["npc_id"] = tier[0]
    out["ambiguous"] = False
    return out


def npc_id_from_explicit_generic_role_address(low: str, addressable_npcs: List[Dict[str, Any]]) -> str:
    """Resolve a scene-local NPC from narrow generic address forms (comma ``you, <role>``, ``to the <role>``, etc.).

    Explicit generic redirection must override stale active-target continuity: otherwise ``you`` in
    ``you, stranger, …`` is misread as pronoun continuation to the prior interlocutor.
    """
    m = match_generic_role_address(low, addressable_npcs)
    if m.get("ambiguous"):
        return ""
    return str(m.get("npc_id") or "").strip()


def _explicit_addressed_npc_id_leading_or_directed(low: str, roster: List[Dict[str, Any]]) -> str:
    """Line-leading name/title or ``to/at <ref>`` against roster (no comma required)."""
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        npc_id = str(npc.get("id") or "").strip()
        if not npc_id:
            continue
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if _residual_directed_prep_npc_should_bind(low, ref):
                return npc_id
    return ""


def scene_npcs_in_active_scene(scene: Dict[str, Any] | None, world: Dict[str, Any]) -> List[Dict[str, Any]]:
    """NPCs present in the active scene envelope (matches api routing)."""
    if not isinstance(scene, dict):
        return []
    scene_id = str(((scene or {}).get("scene") or {}).get("id") or "").strip()
    if not scene_id:
        return []
    return npc_roster_for_dialogue_addressing(world or {}, scene_id, scene=scene, session=None)


def extract_npc_reference_tokens(npc: Dict[str, Any]) -> Set[str]:
    refs: Set[str] = set()
    npc_id = str(npc.get("id") or "").strip().lower()
    npc_name = str(npc.get("name") or "").strip().lower()
    if npc_id:
        refs.add(npc_id)
    if npc_name:
        refs.add(npc_name)
    for token in re.split(r"[\s\-_]+", f"{npc_id} {npc_name}"):
        token = token.strip().lower()
        if len(token) >= 3:
            refs.add(token)
    for title in _NPC_REFERENCE_TITLES:
        if title in npc_name:
            refs.add(title)
    for role in npc.get("address_roles") or []:
        if isinstance(role, str) and role.strip() and len(role.strip()) >= 3:
            refs.add(role.strip().lower())
    for alias in npc.get("aliases") or []:
        if isinstance(alias, str) and alias.strip():
            al = alias.strip().lower()
            refs.add(al)
            for token in re.split(r"[\s\-_]+", al):
                t = token.strip().lower()
                if len(t) >= 3:
                    refs.add(t)
    return refs


def _line_blocks_dialogue_addressing(low: str) -> bool:
    if not low.strip():
        return True
    return any(re.search(pattern, low) for pattern in _WORLD_ACTION_DIALOGUE_BLOCKERS)


def _information_seeking_dialogue_line(low: str) -> bool:
    if "?" in low:
        return True
    if any(h in low for h in _DIALOGUE_INFO_HINTS):
        return True
    return bool(re.search(r"\b(who|what|where|when|why|how|which)\b", low))


def _directed_prep_npc_hit_for_ref(low: str, ref: str) -> Optional[re.Match[str]]:
    return re.search(
        rf"\b(?:to|toward|towards|at)\s+(?:the\s+|a\s+|an\s+)?{re.escape(ref)}\b",
        low,
        re.IGNORECASE,
    )


def _residual_directed_prep_npc_should_bind(low: str, ref: str) -> bool:
    """True when ``to/toward/at <ref>`` is a real address, not gaze-turn / escape-choreography residue."""
    dm = _directed_prep_npc_hit_for_ref(low, ref)
    if not dm:
        return False
    if _residual_weak_bind_escape_tail(low, dm.end()):
        return False
    if _observation_subject_before_weak_turn(low, dm.start()) and re.search(
        rf"\bturns?\s+(?:to|toward|towards)\s+(?:the\s+|a\s+|an\s+)?{re.escape(ref)}\b",
        low,
        re.IGNORECASE,
    ):
        return False
    return True


def _residual_slug_npc_binding_suppressed(low: str, *, original_text: str) -> bool:
    """Suppress roster slug overlap when movement/evasion dominates with only a weak NPC mention."""
    stressful = _merged_text_has_world_action_movement_or_evade(low) or bool(
        re.search(r"\bwhile\s+(?:edging|backing)\s+away\b", low, re.IGNORECASE)
    )
    if not stressful:
        return False
    if _information_seeking_dialogue_line(low):
        return False
    if '"' in original_text:
        return False
    if re.search(
        r"\b(?:watch|watches|watching|glance|glances|gaze|look|looks|looking)\s+(?:at\s+)?(?:the\s+|a\s+|an\s+)?",
        low,
        re.IGNORECASE,
    ):
        return True
    if re.search(r"\bturns?\s+(?:to|toward|towards)\s+", low, re.IGNORECASE):
        return True
    if re.search(r"\bapproach(?:es|ing)?\s+", low, re.IGNORECASE):
        return True
    return False


def find_world_npc_reference_id_in_text(text: str, world: Dict[str, Any]) -> Optional[str]:
    """Match world NPC id/name tokens anywhere in the line (same rules as api dialogue routing)."""
    low = str(text or "").strip().lower()
    if not low:
        return None
    text_slug = slugify(low)
    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return None
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        npc_id = str(npc.get("id") or "").strip()
        npc_name = str(npc.get("name") or "").strip()
        if not npc_id:
            continue
        npc_slug = slugify(f"{npc_id} {npc_name}")
        if npc_slug and npc_slug in text_slug:
            if not _residual_slug_npc_binding_suppressed(low, original_text=text):
                return npc_id
            continue
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if _residual_directed_prep_npc_should_bind(low, ref):
                return npc_id
    return None


def find_addressed_npc_id_for_turn(
    text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any] | None,
) -> Optional[str]:
    """Resolve which scene NPC the player is addressing (vocative, name, proximity, pronouns, hailing)."""
    low = str(text or "").strip().lower()
    if not low or not isinstance(session, dict):
        return None
    envelope = _scene_envelope_for_addressability(session, scene if isinstance(scene, dict) else None)
    scene_id = str(((envelope or {}).get("scene") or {}).get("id") or "").strip()
    p = str(text or "").strip()
    w = world if isinstance(world, dict) else {}
    _recover_conservative_emergent_actor_from_player_vocative(
        session=session,
        scene_envelope=envelope,
        world=w,
        player_text=p,
    )
    roster_canon = (
        canonical_scene_addressable_roster(w, scene_id, scene_envelope=envelope, session=session)
        if scene_id else []
    )

    if roster_canon and isinstance(scene, dict):
        voc_res = resolve_spoken_vocative_target(session=session, scene=scene, spoken_text=p)
        if voc_res.get("has_spoken_vocative") and voc_res.get("target_actor_id"):
            vt = str(voc_res["target_actor_id"]).strip()
            if vt and is_actor_addressable_in_current_scene(session, scene, vt, world=w):
                return vt

    # Highest priority: comma vocative. Canonical roster includes scene addressables; then any world NPC.
    if roster_canon:
        v_loc = npc_id_from_vocative_line(p, roster_canon)
        if v_loc:
            return v_loc
    world_roster = _world_npc_dicts_for_addressing(w)
    v_world = npc_id_from_vocative_line(p, world_roster)
    if v_world:
        return v_world

    # Line-leading / directed address (respects active_entities scope via canonical roster).
    if roster_canon:
        lead = _explicit_addressed_npc_id_leading_or_directed(low, roster_canon)
        if lead:
            return lead

    # Generic role beats substring overlap and pronoun continuation for lines like ``you, stranger, …``.
    gr_match = match_generic_role_address(low, roster_canon)
    if gr_match.get("ambiguous"):
        return None
    gen_id = str(gr_match.get("npc_id") or "").strip()
    if gen_id:
        if not _residual_slug_npc_binding_suppressed(low, original_text=p):
            return gen_id

    if not roster_canon:
        return None
    text_slug = slugify(low)
    interaction = inspect(session)
    active_target_id = str(interaction.get("active_interaction_target_id") or "").strip()

    for npc in roster_canon:
        npc_id = str(npc.get("id") or "").strip()
        npc_name = str(npc.get("name") or "").strip()
        if not npc_id:
            continue
        npc_slug = slugify(f"{npc_id} {npc_name}")
        if npc_slug and npc_slug in text_slug:
            if not _residual_slug_npc_binding_suppressed(low, original_text=p):
                return npc_id
            continue
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if _residual_directed_prep_npc_should_bind(low, ref):
                return npc_id

    if active_target_id and re.search(r"\b(you|your|him|her|them)\b", low):
        if assert_valid_speaker(active_target_id, session, scene_envelope=envelope, world=w):
            return active_target_id

    world_ref = find_world_npc_reference_id_in_text(str(text or ""), world)
    if len(roster_canon) == 1 and not _line_blocks_dialogue_addressing(low):
        only_id = str(roster_canon[0].get("id") or "").strip()
        if world_ref and only_id and world_ref != only_id:
            return None
        if only_id and (_HAILING_RE.search(low) or _information_seeking_dialogue_line(low)):
            return only_id

    return None


def resolve_dialogue_lock_action_target_id(
    player_text: str,
    *,
    scene: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
) -> Optional[str]:
    """Hint ``target_id`` for dialogue-lane structured actions (see :func:`game.api._build_dialogue_first_action`).

    Precedence matches the historical API behavior: declared-action switch → addressed line → world
    name/id mention → active interlocutor (when valid) → sole present NPC. This does **not** replace
    :func:`resolve_authoritative_social_target`, which owns the final NPC at social resolution time;
    emission and validation must not pick a different NPC afterward.
    """
    from game.intent_parser import segment_mixed_player_turn

    seg = segment_mixed_player_turn(player_text)
    decl = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=seg,
        raw_text=player_text,
    )
    if decl.get("has_declared_switch") and decl.get("target_actor_id"):
        tid0 = str(decl["target_actor_id"]).strip()
        if tid0 and is_actor_addressable_in_current_scene(session, scene, tid0, world=world):
            return tid0

    voc_scan = _text_for_spoken_vocative_scan(seg, merge_turn_segments_for_directed_social_entry(seg, player_text))
    voc = resolve_spoken_vocative_target(session=session, scene=scene, spoken_text=voc_scan)
    if voc.get("has_spoken_vocative") and voc.get("target_actor_id"):
        tid1 = str(voc["target_actor_id"]).strip()
        if tid1 and is_actor_addressable_in_current_scene(session, scene, tid1, world=world):
            return tid1

    target_id = find_addressed_npc_id_for_turn(player_text, session, world, scene)
    if not target_id:
        target_id = find_world_npc_reference_id_in_text(player_text, world)
    if not target_id:
        interaction = inspect(session)
        active_target_id = str(interaction.get("active_interaction_target_id") or "").strip()
        if active_target_id and assert_valid_speaker(active_target_id, session, scene_envelope=scene, world=world):
            target_id = active_target_id
    if not target_id:
        scene_npcs = scene_npcs_in_active_scene(scene, world)
        if len(scene_npcs) == 1:
            target_id = str(scene_npcs[0].get("id") or "").strip() or None
    return target_id


def build_intent_route_debug_social_exchange(
    *,
    should_route_meta: Dict[str, Any] | None,
    resolved_target_id: str | None,
) -> Dict[str, Any]:
    """Assemble ``metadata.intent_route_debug`` for dialogue-lock → social exchange turns."""
    m = should_route_meta if isinstance(should_route_meta, dict) else {}
    route_reason = m.get("route_reason") or "dialogue_lane"
    addressed_id = resolved_target_id or (str(m.get("addressed_actor_id") or "").strip() or None)
    addressed_src = m.get("addressed_actor_source")
    if addressed_src is None:
        addressed_src = "dialogue_target_resolution" if resolved_target_id else None
    return {
        "routed_to": "social_exchange",
        "route_reason": route_reason,
        "addressed_actor_id": addressed_id,
        "addressed_actor_source": addressed_src,
    }


def build_intent_route_debug_adjudication_query(*, category: str | None) -> Dict[str, Any]:
    """Assemble ``metadata.intent_route_debug`` when the turn resolves as procedural adjudication."""
    return {
        "routed_to": "adjudication_query",
        "route_reason": f"procedural_{category or 'unknown'}",
        "addressed_actor_id": None,
        "addressed_actor_source": None,
    }


def is_rules_or_engine_mechanics_question(text: str | None) -> bool:
    """True for roll/skill/procedure questions to the GM (including short parenthetical clauses)."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if re.search(r"\b(?:does|do)\s+that\s+require\b", low) and re.search(
        r"\b(?:sleight|hand|perception|stealth|roll|check|skill|difficulty)\b",
        low,
    ):
        return True
    if re.search(r"\b(?:skill\s+check|saving\s+throw|\bdc\b|difficulty\s+class)\b", low):
        return True
    if re.search(
        r"\b(?:sleight of hand|perception|stealth|sense motive|diplomacy|intimidate|bluff|thievery)\b",
        low,
    ) and re.search(r"\b(?:need|needed|require|required|roll|check)\b", low):
        return True
    if re.search(r"\bneed(?:ed)?\s+(?:a\s+)?roll\b", low) or re.search(
        r"\brequire(?:s|d)?\s+(?:a\s+)?(?:roll|check)\b",
        low,
    ):
        return True
    return False


def is_gm_or_system_facing_question(text: str | None) -> bool:
    """True for clear player-to-GM feasibility / state questions, not NPC-directed dialogue."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if re.search(r"\b(?:can|could|would)\s+(?:i|we)\b", low):
        return True
    if re.search(r"\b(?:is there|are there)\s+(?:enough|any)\b", low):
        return True
    if "read the" in low and "board" in low and "?" in low:
        return True
    if re.search(r"\bwould\s+\w+\s+know\s+(?:this|that|already)\b", low):
        return True
    if "?" in low and re.search(
        r"\b(?:reach|climb|jump)\s+(?:the\s+)?(?:roof|wall|ledge|balcony)\b",
        low,
    ):
        return True
    return False


def _looks_like_information_seeking_player_question(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    if "?" in low:
        return True
    if any(h in low for h in _DIALOGUE_INFO_HINTS):
        return True
    return bool(re.search(r"\b(who|what|where|when|why|how|which|tell me|do you know)\b", low))


def _line_marked_explicit_ooc(text: str) -> bool:
    """True for explicit player-to-GM / table-talk markers (mirrors api dialogue lock)."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    patterns = (
        r"\booc\b",
        r"\bout of character\b",
        r"\bas a player\b",
        r"^\s*\(\(",
    )
    return any(re.search(pattern, low) for pattern in patterns)


def _line_marked_mechanical_table_talk(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    return bool(re.match(r"^\s*mechanically\b", low) or re.match(r"^\s*rules[- ]?wise\b", low))


_SCENE_PRESENCE_OR_SCOPE_QUERY_RE = re.compile(
    r"\b(?:earshot|who\s+can\s+hear|in\s+range|is\s+anyone\s+else|who\s+is\s+here)\b",
    re.IGNORECASE,
)

# Narrow: scene-local perception / attention questions that should not enter the social pipeline
# when no NPC is explicitly addressed. Prefer false negatives.
_LOCAL_OBSERVATION_EXCLUDE_RE = re.compile(
    r"""
    \bwhat\s+(?:do|does)\s+the\s+(?:
        guard|gate\s+guard|town\s+crier|crier|merchant|captain|watchman|soldier|
        refugee|bartender|keeper|watch|footman|patrol|warden|herald|bouncer
    )\b|
    \bwhat\s+(?:do|does)\s+the\s+[^\n?.!]{1,52}\s+know\b|
    \bwhat\s+(?:do|does)\s+(?:people|folks|anyone|everyone|someone)\s+|
    \bknow\s+about\b|
    \bpeople\s+know\b|
    \bwho\s+(?:here\s+)?wants\b|
    \bwho\s+wants\s+to\s+speak\b|
    \bwhat\s+happened\s+(?:at|in|during|before)\b|
    \b(?:tell\s+me\s+)?what\s+.*\babout\s+the\s+(?:missing|old)\b
    """,
    re.VERBOSE | re.IGNORECASE,
)
_LOCAL_OBSERVATION_POSITIVE_RE = re.compile(
    r"""
    (?:
        \bwhat\s+(?:do|does)\s+(?:i|we|he|she|they)\s+(?:see|notice|spot|hear|make\s+out|observe|perceive)\b
        |
        \bwhat\s+stands\s+out\b
        |
        \bwhat(?:'s|\s+is)\s+(?:going\s+on|happening)(?:\s+here|\s+now|\s+around\s+(?:us|here))?\b
        |
        \bwhat\s+can\s+(?:i|we|he|she|they)\s+(?:see|make\s+out|discern|spot|notice)\b
        |
        \bfrom\s+(?:here|there|this\s+spot|the\s+[^\n,?.!]{1,40}),?\s+what\s+(?:can|do|does)\s+(?:i|we|he|she|they)\s+(?:see|make\s+out|notice|spot)\b
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _looks_like_local_observation_question(text: str) -> bool:
    """True when *text* asks for immediate scene perception, not an NPC knowledge exchange.

    Requires a question mark and a tight positive pattern; excludes explicit role/NPC address
    (e.g. 'the guard'), lore/knowledge phrasing, and open social solicitations.
    """
    raw = str(text or "").strip()
    if not raw or "?" not in raw:
        return False
    low = raw.lower()
    if _LOCAL_OBSERVATION_EXCLUDE_RE.search(low):
        return False
    return bool(_LOCAL_OBSERVATION_POSITIVE_RE.search(low))


_LOCAL_OBSERVATION_GOING_ON_HAPPENING_RE = re.compile(
    r"\bwhat(?:'s|\s+is)\s+(?:going\s+on|happening)(?:\s+here|\s+now|\s+around\s+(?:us|here))?\b",
    re.IGNORECASE,
)


def _looks_like_local_observation_going_on_happening_question(text: str) -> bool:
    """Narrow slice of :func:`_looks_like_local_observation_question` — 'what's going on' / 'what is happening'."""
    raw = str(text or "").strip()
    if not raw or "?" not in raw:
        return False
    low = raw.lower()
    if _LOCAL_OBSERVATION_EXCLUDE_RE.search(low):
        return False
    return bool(_LOCAL_OBSERVATION_GOING_ON_HAPPENING_RE.search(low))


_LOCAL_OBSERVATION_RECOVERY_STOPWORDS = frozenset(
    {
        "what",
        "that",
        "this",
        "with",
        "from",
        "into",
        "your",
        "have",
        "been",
        "were",
        "there",
        "here",
        "when",
        "where",
        "which",
        "about",
        "going",
        "happening",
        "does",
        "doing",
        "they",
        "them",
        "those",
        "some",
        "than",
        "then",
    }
)


def _significant_tokens_for_topic_overlap(text: str) -> Set[str]:
    low = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    return {
        w
        for w in low.split()
        if len(w) >= 4 and w not in _LOCAL_OBSERVATION_RECOVERY_STOPWORDS
    }


def _player_text_overlaps_surfaced_npc_anchor(player_text: str, anchor_text: str) -> bool:
    pt = _significant_tokens_for_topic_overlap(player_text)
    at = _significant_tokens_for_topic_overlap(anchor_text)
    if not pt or not at:
        return False
    return bool(pt & at)


def _should_recover_social_from_local_observation_followup(
    *,
    session: Dict[str, Any],
    scene: Dict[str, Any],
    world: Dict[str, Any],
    merged_player_text: str,
    segmented_turn: Dict[str, Any] | None,
) -> bool:
    """True when a local-observation-shaped line should stay in the social lane for the active NPC.

    Objective #21 — narrow recovery: interrogative 'what's going on / happening' follow-ups that
    match :func:`_looks_like_local_observation_question` but continue the same interlocutor's
    surfaced topic (topic_pressure last_answer), not genuine scene perception queries.
    """
    t = str(merged_player_text or "").strip()
    if not t or not _looks_like_local_observation_question(t):
        return False
    if not _looks_like_local_observation_going_on_happening_question(t):
        return False
    w = world if isinstance(world, dict) else {}
    scene_obj = scene.get("scene") if isinstance(scene, dict) else None
    scene_id = str(scene_obj.get("id") or "").strip() if isinstance(scene_obj, dict) else ""
    if not scene_id:
        return False
    ctx = inspect(session)
    active_id = str(ctx.get("active_interaction_target_id") or "").strip()
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
    social_mode = mode == "social" or kind == "social"
    if not active_id or not social_mode:
        return False
    if not assert_valid_speaker(active_id, session, scene_envelope=scene, world=w):
        return False
    if not is_actor_addressable_in_current_scene(session, scene, active_id, world=w):
        return False

    decl_sw = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=str(merged_player_text or ""),
    )
    decl_cue = bool(decl_sw.get("has_declared_switch"))
    decl_id = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
    decl_ok = bool(
        decl_id and is_actor_addressable_in_current_scene(session, scene, decl_id, world=w)
    )
    if decl_cue and decl_ok and decl_id and decl_id != active_id:
        return False

    voc_scan = _text_for_spoken_vocative_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        t,
    )
    voc_res = resolve_spoken_vocative_target(
        session=session,
        scene=scene,
        spoken_text=voc_scan,
    )
    voc_id = _clean_string(voc_res.get("target_actor_id")) if voc_res.get("has_spoken_vocative") else ""
    voc_ok = bool(voc_id and is_actor_addressable_in_current_scene(session, scene, voc_id, world=w))
    if voc_ok and voc_id and voc_id != active_id:
        return False

    rt = get_scene_runtime(session, scene_id)
    tcur = rt.get("topic_pressure_current") if isinstance(rt.get("topic_pressure_current"), dict) else {}
    speaker_key = str(tcur.get("speaker_key") or "").strip()
    if speaker_key != active_id:
        return False
    topic_key = str(rt.get("topic_pressure_last_topic_key") or "").strip()
    pressure = rt.get("topic_pressure") if isinstance(rt.get("topic_pressure"), dict) else {}
    entry = pressure.get(topic_key) if topic_key and isinstance(pressure, dict) else None
    last_answer = str(entry.get("last_answer") or "").strip() if isinstance(entry, dict) else ""
    if len(last_answer) < 8:
        return False
    return _player_text_overlaps_surfaced_npc_anchor(t, last_answer)


def should_emit_observe_for_local_observation_parse(
    text: str,
    scene_envelope: Optional[Dict[str, Any]],
    *,
    session: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
    segmented_turn: Optional[Dict[str, Any]] = None,
) -> bool:
    """True when freeform parsing should emit an ``observe`` action for local observation phrasing."""
    if not _looks_like_local_observation_question(str(text or "").strip()):
        return False
    if not isinstance(session, dict) or not isinstance(scene_envelope, dict):
        return True
    if _should_recover_social_from_local_observation_followup(
        session=session,
        scene=scene_envelope,
        world=world if isinstance(world, dict) else {},
        merged_player_text=str(text or "").strip(),
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    ):
        return False
    return True


def _text_for_declared_actor_switch_scan(
    segmented_turn: Dict[str, Any] | None,
    raw_text: str,
) -> str:
    """Prefer syntactic declared-action clause; else full raw (unsegmented turns)."""
    if isinstance(segmented_turn, dict):
        decl = _clean_string(segmented_turn.get("declared_action_text"))
        if decl:
            return decl
    return str(raw_text or "").strip()


# Declared-action actor switch: ``(pattern, strength)`` where ``weak`` matches are
# suppressed when the scan looks like observation-plus-escape / residual movement
# with only an incidental NPC mention (Block #2 — residual false-bind cleanup).
_DECLARED_SWITCH_TARGET_PATTERNS: tuple[tuple[re.Pattern[str], Literal["strong", "weak"]], ...] = (
    # turns to speak with a nearby refugee / turn to speak to the guard
    (
        re.compile(
            r"\bturns?\s+to\s+speak\s+(?:with|to)\s+(.+?)(?=\.|\"|\?|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # speak with Lord Aldric / speaks to the refugee
    (
        re.compile(
            r"\bspeaks?\s+(?:with|to)\s+(.+?)(?=\.|\"|\?|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # addresses the watcher
    (
        re.compile(
            r"\baddresses\s+(.+?)(?=\.|\"|\?|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # confronts the captain
    (
        re.compile(
            r"\bconfronts?\s+(.+?)(?=\.|\"|\?|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # asks the guard where / what / whether …
    (
        re.compile(
            r"\basks?\s+(?:the\s+|a\s+|an\s+)?(.+?)\s+(?:where|what|why|how|whether|if)\b",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # tell / show the guard …
    (
        re.compile(
            r"\b(?:tell|tells|show|shows)\s+the\s+(.+?)(?=\.|\"|\?|,|\s+about\b|\s+that\b|\s+what\b|\s+where\b|\s+how\b)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # gestures to / toward the guard
    (
        re.compile(
            r"\bgestures?\s+(?:to|toward|towards)\s+(.+?)(?=\.|\"|\?|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # grabs the guard's sleeve / grabs the guard by …
    (
        re.compile(
            r"\bgrabs?\s+(.+?)(?='s\s+|\s+and\s+|\s+while\s+|[\.,;!?]|\"|$)",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # turns to the guard and demands / asks / says …
    (
        re.compile(
            r"\bturns?\s+(?:to|toward|towards)\s+(?!speak\b)(.+?)\s+and\s+(?:demands?|asks?|says?|tells?|"
            r"shouts?|whispers?|press(?:es)?|calls?|hails?|questions?|barks?)\b",
            re.IGNORECASE,
        ),
        "strong",
    ),
    # approaches the guard — stop before escape / incidental tail (weak)
    (
        re.compile(
            r"\bapproaches?\s+(.+?)(?=\s+and\s+(?:ask|asks|tell|tells|say|says|speak|speaks|question|questions|whether|if)\b|"
            r"\s+then\b|\s+while\b|\s+and\s+then\b|\s+for\s+(?:a\s+)?(?:moment|instant)|\s+before\s+(?:bolting|running|fleeing|vanishing)|"
            r"\s*,\s*then\b|[\.,;!?]|\"|$)",
            re.IGNORECASE,
        ),
        "weak",
    ),
    # turns to the captain — not "turns to speak …"; narrow tail so movement survives (weak)
    (
        re.compile(
            r"\bturns?\s+(?:to|toward|towards)\s+(?!speak\b)(.+?)(?=\s+and\s+(?:demands?|asks?|says?|tells?|"
            r"shouts?|whispers?|press(?:es)?|calls?|hails?|questions?|barks?)\b|"
            r"\s+for\s+(?:a\s+)?(?:moment|instant)|\s+before\s+(?:bolting|running|fleeing|vanishing)|"
            r"\s+while\b|\s+then\b|\s*,\s*then\b|[\.,;!?]|\"|$)",
            re.IGNORECASE,
        ),
        "weak",
    ),
)

_OBSERVATION_BEFORE_WEAK_TURN_RE = re.compile(
    r"\b(?:gaze|glance|glances|watch(?:es|ing|ed)?|stare|stares|staring|eye|eyes)\b",
    re.IGNORECASE,
)

_RESIDUAL_WEAK_BIND_ESCAPE_TAIL_RE = re.compile(
    r"\b(?:then|,)\s*(?:run|runs|ran|running|flee|flees|fleeing|bolt|bolts|bolting|dash|dashes|escape|escapes|escaping|"
    r"disappear|disappears|disappearing|retreat|retreats|sprint|sprints|edge|edges|edging|slip|slips|slipping|"
    r"back(?:ing)?\s+away|melt|melts|melting)\b",
    re.IGNORECASE,
)


def _observation_subject_before_weak_turn(low: str, turn_match_start: int) -> bool:
    if turn_match_start <= 0:
        return False
    window_start = max(0, turn_match_start - 96)
    chunk = low[window_start:turn_match_start]
    return bool(_OBSERVATION_BEFORE_WEAK_TURN_RE.search(chunk))


def _residual_weak_bind_escape_tail(low: str, bind_match_end: int) -> bool:
    if bind_match_end >= len(low):
        return False
    tail = low[bind_match_end:]
    if _merged_text_has_world_action_movement_or_evade(tail):
        return True
    if _RESIDUAL_WEAK_BIND_ESCAPE_TAIL_RE.search(tail):
        return True
    if re.search(r"\bwhile\s+(?:edging|backing)\s+away\b", tail, re.IGNORECASE):
        return True
    if re.search(r"\bdisappear(?:s|ing)?\s+into\b", tail, re.IGNORECASE):
        return True
    return False


def _residual_weak_declared_actor_switch_suppressed(
    low: str,
    *,
    strength: Literal["strong", "weak"],
    match_start: int,
    match_end: int,
) -> bool:
    if strength != "weak":
        return False
    if _observation_subject_before_weak_turn(low, match_start):
        return True
    if _residual_weak_bind_escape_tail(low, match_end):
        return True
    return False


def _strip_leading_articles_and_proximity(low: str) -> str:
    s = str(low or "").strip().lower()
    s = re.sub(r"^(?:the|a|an)\s+", "", s)
    s = re.sub(r"^nearby\s+", "", s)
    return s.strip()


def _resolve_social_address_phrase_to_roster_id(
    phrase: str,
    roster: List[Dict[str, Any]],
    addr_ids: Set[str],
) -> str:
    """Map a declared noun phrase to at most one scene-addressable roster id."""
    raw = str(phrase or "").strip()
    if not raw:
        return ""
    low = raw.lower().strip()
    low = re.sub(r"[.,;:!?]+$", "", low).strip()
    if not low:
        return ""

    rest = _strip_leading_articles_and_proximity(low)
    if not rest:
        return ""

    syn_to = f"to the {rest}"
    gr = match_generic_role_address(syn_to, roster)
    if not gr.get("ambiguous"):
        nid = str(gr.get("npc_id") or "").strip()
        if nid and nid in addr_ids:
            return nid

    for probe in (syn_to, f"to {rest}", f"at {rest}", rest):
        lead = _explicit_addressed_npc_id_leading_or_directed(probe, roster)
        if lead and lead in addr_ids:
            return lead

    voc = npc_id_from_vocative_line(f"{raw}, tell me", roster)
    if voc and voc in addr_ids:
        return voc

    best_id = ""
    best_len = 0
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid or nid not in addr_ids:
            continue
        for ref in extract_npc_reference_tokens(npc):
            if len(ref) < 3:
                continue
            if re.search(rf"\b{re.escape(ref)}\b", low):
                if len(ref) > best_len:
                    best_len = len(ref)
                    best_id = nid
    return best_id


def resolve_declared_actor_switch(
    *,
    session: dict,
    scene: dict | None,
    segmented_turn: dict | None,
    raw_text: str,
) -> dict:
    """Detect a player-authored *declared* redirection to a new addressee (beats interlocutor continuity).

    Scans :func:`game.intent_parser.segment_mixed_player_turn` ``declared_action_text`` when present,
    else *raw_text*. Resolves against :func:`canonical_scene_addressable_roster` (roles, aliases, names).
    """
    out: Dict[str, Any] = {
        "has_declared_switch": False,
        "target_actor_id": None,
        "target_source": None,
        "reason": "",
    }
    scan = _text_for_declared_actor_switch_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(raw_text or ""),
    )
    if not scan.strip():
        out["reason"] = "empty_scan_text"
        return out

    if not isinstance(session, dict):
        out["reason"] = "no_session"
        return out

    env = scene if isinstance(scene, dict) else {}
    sc = env.get("scene")
    if not isinstance(sc, dict):
        out["reason"] = "no_scene_envelope"
        return out
    sid = _clean_string(sc.get("id"))
    if not sid:
        st = session.get("scene_state")
        if isinstance(st, dict):
            sid = _clean_string(st.get("active_scene_id")) or _clean_string(session.get("active_scene_id"))
    if not sid:
        out["reason"] = "empty_scene_id"
        return out

    from game.storage import load_world

    world = load_world()
    if not isinstance(world, dict):
        world = {}

    roster = canonical_scene_addressable_roster(
        world, sid, scene_envelope=env, session=session
    )
    universe = addressable_scene_npc_id_universe(session, env, world)
    addr_ids = universe | scene_addressable_actor_ids(world, sid, scene_envelope=env, session=session)

    low_scan = scan.lower()
    candidates: List[tuple[Literal["strong", "weak"], int, int, str]] = []
    for pat, strength in _DECLARED_SWITCH_TARGET_PATTERNS:
        for m in pat.finditer(low_scan):
            ph = _clean_string(m.group(1))
            if not ph:
                continue
            if _residual_weak_declared_actor_switch_suppressed(
                low_scan, strength=strength, match_start=m.start(), match_end=m.end()
            ):
                continue
            candidates.append((strength, m.start(), m.end(), ph))

    if not candidates:
        out["reason"] = "no_declared_motion_or_address_pattern"
        return out

    prefer_strong = any(c[0] == "strong" for c in candidates)
    filtered = [c for c in candidates if (not prefer_strong or c[0] == "strong")]
    _strength_rank: dict[str, int] = {"strong": 0, "weak": 1}
    best = min(filtered, key=lambda c: (_strength_rank[c[0]], -c[2], c[1]))
    best_phrase = best[3]

    nid = _resolve_social_address_phrase_to_roster_id(best_phrase, roster, addr_ids)
    if not nid:
        out["reason"] = "declared_phrase_did_not_resolve_to_addressable_actor"
        return out

    out["has_declared_switch"] = True
    out["target_actor_id"] = nid
    out["target_source"] = "declared_action"
    out["reason"] = "declared_action_phrase_resolved_to_scene_addressable_actor"
    return out


def merge_turn_segments_for_directed_social_entry(
    segmented_turn: Dict[str, Any] | None,
    raw_text: str,
) -> str:
    """Join declared/spoken/observation segments for addressing — excludes adjudication clauses."""
    if not isinstance(segmented_turn, dict):
        return str(raw_text or "").strip()
    ordered_keys = (
        "declared_action_text",
        "spoken_text",
        "observation_intent_text",
    )
    parts: List[str] = []
    seen: Set[str] = set()
    for key in ordered_keys:
        raw = segmented_turn.get(key)
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s or s in seen:
            continue
        parts.append(s)
        seen.add(s)
    return " ".join(parts) if parts else str(raw_text or "").strip()


# Phrases for interlocutor follow-up vs new addressee (mirrors api dialogue lock).
_AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES_IC: tuple[str, ...] = (
    "what should i do next",
    "what's the next step",
    "what is the next step",
    "where does this lead",
    "where does this go",
    "what now",
)

_DIALOGUE_SPEECH_MARKERS_IC: tuple[str, ...] = (
    "say ",
    "tell ",
    "ask ",
    "reply ",
    "answer ",
    "shout ",
    "whisper ",
    "mutter ",
    "call out",
    "speak ",
)


def _npc_id_from_directed_motion_or_ask_phrases(low: str, roster: List[Dict[str, Any]]) -> str:
    """Resolve ``approach|turn to|ask …`` style phrases to a roster NPC id (longest ref wins)."""
    if not low.strip() or not roster:
        return ""
    best_id = ""
    best_len = -1
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid:
            continue
        refs = sorted(extract_npc_reference_tokens(npc), key=len, reverse=True)
        for ref in refs:
            if len(ref) < 3:
                continue
            esc = re.escape(ref)
            patterns: tuple[tuple[str, Literal["strong", "weak"]], ...] = (
                (rf"\bapproach(?:es|ing)?\s+(?:the\s+|a\s+|an\s+)?(?:nearby\s+)?{esc}\b", "weak"),
                (rf"\bapproaching\s+(?:the\s+|a\s+|an\s+)?(?:nearby\s+)?{esc}\b", "weak"),
                (rf"\bturns?\s+to\s+(?:the\s+)?{esc}\b", "weak"),
                (rf"\bturns?\s+towards?\s+(?:the\s+)?{esc}\b", "weak"),
                (rf"\bask\s+(?:the\s+)?{esc}\b", "strong"),
                (rf"\bquestion\s+(?:the\s+)?{esc}\b", "strong"),
                (rf"\btalk\s+to\s+(?:the\s+)?{esc}\b", "strong"),
                (rf"\bspeak\s+(?:to|with)\s+(?:the\s+|a\s+|an\s+)?(?:nearby\s+)?{esc}\b", "strong"),
                (rf"\bgauge\s+(?:the\s+)?{esc}\b", "strong"),
            )
            for pat, strength in patterns:
                m = re.search(pat, low)
                if not m:
                    continue
                if strength == "weak" and (
                    _observation_subject_before_weak_turn(low, m.start())
                    or _residual_weak_bind_escape_tail(low, m.end())
                ):
                    continue
                if len(ref) > best_len:
                    best_len = len(ref)
                    best_id = nid
                break
    return best_id


def _explicit_address_or_role_cue_in_line(
    low: str,
    roster: List[Dict[str, Any]],
    *,
    merged_text: str | None = None,
) -> bool:
    """True when the line likely selects a *new* addressee (not a bare interlocutor follow-up)."""
    mt = merged_text if merged_text is not None else low
    if _merged_text_has_resolvable_spoken_vocative(mt, roster):
        return True
    if npc_id_from_vocative_line(low, roster):
        return True
    if _explicit_addressed_npc_id_leading_or_directed(low, roster):
        return True
    if _npc_id_from_directed_motion_or_ask_phrases(low, roster):
        return True
    gr = match_generic_role_address(low, roster)
    if gr.get("npc_id") and not gr.get("ambiguous"):
        return True
    role_spoken = _last_spoken_generic_role_slug(low)
    if role_spoken and (gr.get("ambiguous") or not gr.get("npc_id")):
        return True
    return False


def _merged_indicates_travel_not_social(merged: str, scene_envelope: Dict[str, Any]) -> bool:
    """True when freeform parse is clearly travel / scene transition (wins over interlocutor continuity)."""
    from game.intent_parser import parse_freeform_to_action

    m = str(merged or "").strip()
    if not m:
        return False
    act = parse_freeform_to_action(m, scene_envelope if isinstance(scene_envelope, dict) else None)
    if not isinstance(act, dict):
        return False
    t = str(act.get("type") or "").strip().lower()
    return t in ("travel", "scene_transition")


_OBSERVATIONAL_ENV_ONLY_RE = re.compile(
    r"^\s*(?:what\s+do\s+i\s+see|what'?s\s+here|where\s+am\s+i|look\s+around|scan\s+the\s+(?:room|area))\s*\??\s*$",
    re.IGNORECASE,
)

# Crowd / room open-call phrasing not covered by :data:`_BROAD_ADDRESS_LEXICAL` (e.g. "who wants to speak").
_BROADCAST_OPEN_CALL_LEXICAL: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwho\s+wants\b", re.IGNORECASE), "who_wants"),
    (re.compile(r"\bwhich\s+of\s+you\b", re.IGNORECASE), "which_of_you"),
    (re.compile(r"\bwho\s+will\s+(?:answer|speak|talk|step\s+(?:forward|up))\b", re.IGNORECASE), "who_will"),
    (re.compile(r"\bwho\s+here\s+will\b", re.IGNORECASE), "who_here_will"),
    (re.compile(r"\banyone\s+care\s+to\b", re.IGNORECASE), "anyone_care_to"),
    (re.compile(r"\banyone\s+willing\s+to\s+talk\b", re.IGNORECASE), "anyone_willing_talk"),
    (re.compile(r"\bwho\s+here\s+(?:knows|knew|saw|heard)\b", re.IGNORECASE), "who_here_witness"),
    (re.compile(r"\bwhich\s+of\s+you\s+(?:saw|heard|knows|knew)\b", re.IGNORECASE), "which_of_you_witness"),
)


def is_broadcast_social_open_call(
    merged_text: str,
    *,
    low: str | None = None,
    roster: List[Dict[str, Any]],
    segmented_turn: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Detect crowd-addressed open-call social lines without broad-address lexical cues.

    Excludes local perception / observation queries (handled upstream) and named vocatives.
    """
    t = str(merged_text or "").strip()
    lo = str(low if low is not None else t.lower()).strip().lower()
    out: Dict[str, Any] = {"is_broadcast_open_call": False, "phrase_matched": "", "reason": ""}
    if not t or not lo:
        out["reason"] = "empty_text"
        return out
    if _looks_like_local_observation_question(t):
        out["reason"] = "local_scene_observation_query"
        return out
    if is_gm_or_system_facing_question(t) or is_rules_or_engine_mechanics_question(t):
        out["reason"] = "gm_or_mechanics_query"
        return out
    if _OBSERVATIONAL_ENV_ONLY_RE.search(t.strip()):
        out["reason"] = "observational_environment_only"
        return out
    if scene_envelope and _merged_indicates_travel_not_social(t, scene_envelope):
        out["reason"] = "travel_or_scene_transition_intent"
        return out
    phrase = ""
    for pat, label in _BROADCAST_OPEN_CALL_LEXICAL:
        if pat.search(lo):
            phrase = label
            break
    if not phrase:
        out["reason"] = "no_broadcast_open_call_cue"
        return out
    if not _broad_address_has_social_or_question_framing(t, lo):
        out["reason"] = "no_social_or_question_framing"
        return out
    mt_for_voc = merged_text
    if isinstance(segmented_turn, dict):
        voc_scan = _text_for_spoken_vocative_scan(segmented_turn, t)
        if voc_scan:
            voc_res = resolve_spoken_vocative_target(
                session=session or {},
                scene=scene_envelope if isinstance(scene_envelope, dict) else None,
                spoken_text=voc_scan,
            )
            if voc_res.get("has_spoken_vocative"):
                out["reason"] = "spoken_vocative_present"
                return out
    if _explicit_address_or_role_cue_in_line(lo, roster, merged_text=mt_for_voc):
        out["reason"] = "explicit_address_or_role_cue"
        return out
    if session and world and isinstance(scene_envelope, dict):
        scene_obj = scene_envelope.get("scene")
        sid = str(scene_obj.get("id") or "").strip() if isinstance(scene_obj, dict) else ""
        if sid:
            lead = _npc_id_from_directed_motion_or_ask_phrases(lo, roster)
            if lead and is_actor_addressable_in_current_scene(
                session, scene_envelope, lead, world=world
            ):
                out["reason"] = "directed_motion_resolves_npc"
                return out
    w = world if isinstance(world, dict) else {}
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid or len(nid) < 2:
            continue
        for ref in sorted(extract_npc_reference_tokens(npc), key=len, reverse=True):
            if len(ref) < 3:
                continue
            esc = re.escape(ref)
            if re.search(rf",\s*{esc}\b", lo) or re.search(rf"^\s*{esc}\b[,?!]", lo):
                out["reason"] = "named_vocative_or_address_pattern"
                return out
    out["is_broadcast_open_call"] = True
    out["phrase_matched"] = phrase
    out["reason"] = "broadcast_open_call_ok"
    return out


# Backward / doc alias (same predicate).
_is_broadcast_social_open_call = is_broadcast_social_open_call


_BROAD_ADDRESS_LEXICAL: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\banyone\b", re.IGNORECASE), "anyone"),
    (re.compile(r"\banybody\b", re.IGNORECASE), "anybody"),
    (re.compile(r"\bsomebody\b", re.IGNORECASE), "somebody"),
    (re.compile(r"\bsomeone\b", re.IGNORECASE), "someone"),
    (re.compile(r"\bwho\s+here\b", re.IGNORECASE), "who_here"),
    (re.compile(r"\bwho\s+among\s+(?:you|us|them)\b", re.IGNORECASE), "who_among"),
    (re.compile(r"\bdoes\s+anyone\b", re.IGNORECASE), "does_anyone"),
    (re.compile(r"\bdo\s+any\s+of\s+you\b", re.IGNORECASE), "do_any_of_you"),
    (re.compile(r"\bis\s+anyone\b", re.IGNORECASE), "is_anyone"),
    (re.compile(r"\bcan\s+anyone\b", re.IGNORECASE), "can_anyone"),
    (re.compile(r"\bcould\s+anyone\b", re.IGNORECASE), "could_anyone"),
    (re.compile(r"\bwould\s+anyone\b", re.IGNORECASE), "would_anyone"),
    (re.compile(r"\bcan\s+somebody\b", re.IGNORECASE), "can_somebody"),
    (re.compile(r"\bcan\s+someone\b", re.IGNORECASE), "can_someone"),
    (re.compile(r"\bi\s+call\s+out\b", re.IGNORECASE), "i_call_out"),
    (re.compile(r"\bwe\s+call\s+out\b", re.IGNORECASE), "we_call_out"),
    (re.compile(r"\bi\s+shout\b", re.IGNORECASE), "i_shout"),
    (re.compile(r"\bwe\s+shout\b", re.IGNORECASE), "we_shout"),
    (re.compile(r"\bi\s+yell\b", re.IGNORECASE), "i_yell"),
    (re.compile(r"\bi\s+ask\s+the\s+crowd\b", re.IGNORECASE), "i_ask_the_crowd"),
    (re.compile(r"\bi\s+address\s+the\s+room\b", re.IGNORECASE), "i_address_the_room"),
    (re.compile(r"\bfor\s+anyone\b", re.IGNORECASE), "for_anyone"),
    (re.compile(r"\bvolunteer(?:s|ed)?\s+to\s+talk\b", re.IGNORECASE), "volunteer_to_talk"),
)


def _broad_address_has_social_or_question_framing(merged_text: str, low: str) -> bool:
    t = str(merged_text or "").strip()
    if not t:
        return False
    if "?" in t:
        return True
    if _looks_like_information_seeking_player_question(t):
        return True
    if '"' in t:
        return True
    if any(tok in low for tok in _DIALOGUE_SPEECH_MARKERS_IC):
        return True
    if re.search(r"\b(i|we)\s+(?:call\s+out|shout|yell)\b", low):
        return True
    if re.search(r"\bchat\b|\btalk\b|\bspeak\b|\bconversation\b", low):
        return True
    return False


def detect_broad_address_social_bid(
    merged_text: str,
    *,
    low: str | None = None,
    roster: List[Dict[str, Any]],
    segmented_turn: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Conservative lexical detect: crowd / open-address solicitation (not a named vocative).

    Returns dict keys: is_broad_address (bool), phrase_matched (str), reason (str).
    """
    t = str(merged_text or "").strip()
    lo = str(low if low is not None else t.lower()).strip().lower()
    out = {"is_broad_address": False, "phrase_matched": "", "reason": ""}
    if not t or not lo:
        out["reason"] = "empty_text"
        return out
    if is_gm_or_system_facing_question(t) or is_rules_or_engine_mechanics_question(t):
        out["reason"] = "gm_or_mechanics_query"
        return out
    if _OBSERVATIONAL_ENV_ONLY_RE.search(t.strip()):
        out["reason"] = "observational_environment_only"
        return out
    if (
        "?" in t
        and _SCENE_PRESENCE_OR_SCOPE_QUERY_RE.search(lo)
        and not any(pat.search(lo) for pat, _ in _BROAD_ADDRESS_LEXICAL)
    ):
        out["reason"] = "scene_presence_query_without_broad_cue"
        return out
    if scene_envelope and _merged_indicates_travel_not_social(t, scene_envelope):
        out["reason"] = "travel_or_scene_transition_intent"
        return out
    phrase = ""
    for pat, label in _BROAD_ADDRESS_LEXICAL:
        if pat.search(lo):
            phrase = label
            break
    if not phrase:
        out["reason"] = "no_broad_lexical_cue"
        return out
    if not _broad_address_has_social_or_question_framing(t, lo):
        out["reason"] = "no_social_or_question_framing"
        return out
    mt_for_voc = merged_text
    if isinstance(segmented_turn, dict):
        voc_scan = _text_for_spoken_vocative_scan(segmented_turn, t)
        if voc_scan:
            voc_res = resolve_spoken_vocative_target(
                session=session or {},
                scene=scene_envelope if isinstance(scene_envelope, dict) else None,
                spoken_text=voc_scan,
            )
            if voc_res.get("has_spoken_vocative"):
                out["reason"] = "spoken_vocative_present"
                return out
    if _explicit_address_or_role_cue_in_line(lo, roster, merged_text=mt_for_voc):
        out["reason"] = "explicit_address_or_role_cue"
        return out
    if session and world and isinstance(scene_envelope, dict):
        scene_obj = scene_envelope.get("scene")
        sid = str(scene_obj.get("id") or "").strip() if isinstance(scene_obj, dict) else ""
        if sid:
            lead = _npc_id_from_directed_motion_or_ask_phrases(lo, roster)
            if lead and is_actor_addressable_in_current_scene(
                session, scene_envelope, lead, world=world
            ):
                out["reason"] = "directed_motion_resolves_npc"
                return out
    w = world if isinstance(world, dict) else {}
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid or len(nid) < 2:
            continue
        for ref in sorted(extract_npc_reference_tokens(npc), key=len, reverse=True):
            if len(ref) < 3:
                continue
            esc = re.escape(ref)
            if re.search(rf",\s*{esc}\b", lo) or re.search(rf"^\s*{esc}\b[,?!]", lo):
                out["reason"] = "named_vocative_or_address_pattern"
                return out
    out["is_broad_address"] = True
    out["phrase_matched"] = phrase
    out["reason"] = "broad_lexical_and_framing_ok"
    return out


def _current_valid_social_interlocutor_id(
    session: Dict[str, Any] | None,
    scene_envelope: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> str:
    if not isinstance(session, dict) or not isinstance(scene_envelope, dict):
        return ""
    ctx = inspect(session)
    active_id = str(ctx.get("active_interaction_target_id") or "").strip()
    if not active_id:
        return ""
    w = world if isinstance(world, dict) else {}
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
    social_mode = mode == "social" or kind == "social"
    if not social_mode:
        return ""
    if not assert_valid_speaker(active_id, session, scene_envelope=scene_envelope, world=w):
        return ""
    if not is_actor_addressable_in_current_scene(session, scene_envelope, active_id, world=w):
        return ""
    return active_id


def _emergent_addressable_id_set(session: Dict[str, Any] | None, scene_id: str) -> Set[str]:
    sid = _clean_string(scene_id) or ""
    out: Set[str] = set()
    if not isinstance(session, dict) or not sid:
        return out
    st = session.get("scene_state")
    if not isinstance(st, dict):
        return out
    active_sid = str(st.get("active_scene_id") or "").strip()
    if active_sid and active_sid != sid:
        return out
    for row in st.get("emergent_addressables") or []:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id") or "").strip()
        rsid = _clean_string(row.get("scene_id"))
        if not eid or (rsid and rsid != sid):
            continue
        out.add(eid)
    return out


def rank_open_social_solicitation_candidates(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
) -> List[str]:
    """Ordered addressable ids for an open crowd solicitation (no speaker chosen).

    Tiers: active social interlocutor → direct scene NPCs → emergent addressables → promoted figures.
    Within a tier, lower ``address_priority`` wins, then lexicographic id.
    """
    sid = _clean_string(scene_id) or ""
    if not sid:
        return []
    env = scene_envelope if isinstance(scene_envelope, dict) else None
    if env is None and isinstance(session, dict):
        env = _scene_envelope_for_addressability(session, None)
    roster = canonical_scene_addressable_roster(
        world if isinstance(world, dict) else {},
        sid,
        scene_envelope=env,
        session=session if isinstance(session, dict) else None,
    )
    w = world if isinstance(world, dict) else {}
    emergent_ids = _emergent_addressable_id_set(session, sid)
    interlocutor = _current_valid_social_interlocutor_id(session, env, w) if env else ""

    rows: List[tuple[int, int, str]] = []
    seen: Set[str] = set()
    for row in roster:
        if not isinstance(row, dict):
            continue
        nid = str(row.get("id") or "").strip()
        if not nid or nid in seen:
            continue
        if not isinstance(session, dict) or env is None:
            continue
        if not is_actor_addressable_in_current_scene(session, env, nid, world=w):
            continue
        seen.add(nid)
        try:
            pri = int(row.get("address_priority", 999))
        except (TypeError, ValueError):
            pri = 999
        tier = 1
        if interlocutor and nid == interlocutor:
            tier = 0
        else:
            wnpc = npc_dict_by_id(w, nid)
            if isinstance(wnpc, dict) and str(wnpc.get("promoted_from_actor_id") or "").strip():
                tier = 3
            elif nid in emergent_ids or nid.startswith("emergent_"):
                tier = 2
        rows.append((tier, pri, nid))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    return [r[2] for r in rows]


_WORLD_ACTION_SOCIAL_BREAK_MOVEMENT_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:sprint|sprints|sprinted|sprinting)\b", re.IGNORECASE),
    re.compile(r"\bflee(?:s|ing|ed)?\b", re.IGNORECASE),
    re.compile(r"\bbolt(?:s|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bdash(?:es|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\b(?:retreat|retreats|retreating|withdraw|withdraws|withdrawing)\b", re.IGNORECASE),
    re.compile(r"\b(?:run|runs|ran)\b", re.IGNORECASE),
    re.compile(r"\bkee?p(?:s|ing)?\s+running\b", re.IGNORECASE),
    re.compile(r"\brunning\s+(?:down|along|toward|towards|to|until|through|into|away)\b", re.IGNORECASE),
    re.compile(r"\bslip(?:s|ped)?\s+(?:into|away|through|past)\b", re.IGNORECASE),
    re.compile(r"\b(?:melt|melts|melting)\s+into\b", re.IGNORECASE),
    re.compile(r"\baway\s+from\b", re.IGNORECASE),
    re.compile(r"\bturns?\s+and\s+(?:run|runs|walk|walks|head|heads|go|goes|sprint|flee)\b", re.IGNORECASE),
    re.compile(r"\b(?:escape|escapes|escaping|fled|fleeing)\b", re.IGNORECASE),
    re.compile(r"\b(?:leave|leaves|leaving|left)\s+(?:him|her|them|it)\s+behind\b", re.IGNORECASE),
    re.compile(r"\bout\s+of\s+(?:sight|earshot)\b", re.IGNORECASE),
)

_WORLD_ACTION_SOCIAL_BREAK_SELF_OUTCOME_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\bwhere\s+do\s+(?:i|we)\s+end\s+up\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhere\s+does\s+(?:he|she|they)\s+end\s+up\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+does\s+(?:he|she|they)\s+(?:see|notice|spot)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+do\s+(?:i|we)\s+(?:see|notice|spot)\b",
        re.IGNORECASE,
    ),
)

_WORLD_ACTION_SOCIAL_BREAK_SELF_OBSERVE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\bkee?p(?:s|ing)?\s+(?:a\s+)?close\s+eye\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bkee?p(?:s|ing)?\s+watch(?:ing)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:watch|watches|watching)\s+(?:the\s+)?(?:gate|gates|door|doors|street|streets|"
        r"road|roads|alley|alleys|crowd|crowds|quay|harbor|harbour|dock|docks|yard|yards)\b",
        re.IGNORECASE,
    ),
)


def _merged_text_has_world_action_movement_or_evade(low: str) -> bool:
    if not low.strip():
        return False
    if any(p.search(low) for p in _WORLD_ACTION_SOCIAL_BREAK_MOVEMENT_RES):
        return True
    if "out of breath" in low and re.search(
        r"\b(?:run|runs|ran|running|sprint|sprints|sprinting)\b",
        low,
    ):
        return True
    return False


def _merged_text_has_self_directed_world_outcome_question(low: str) -> bool:
    if not low.strip():
        return False
    return any(p.search(low) for p in _WORLD_ACTION_SOCIAL_BREAK_SELF_OUTCOME_RES)


def _merged_text_has_self_directed_sustained_observation(low: str) -> bool:
    if not low.strip():
        return False
    return any(p.search(low) for p in _WORLD_ACTION_SOCIAL_BREAK_SELF_OBSERVE_RES)


# Narrow deterministic signals: inspect / manipulate / observe the environment or props,
# including third-person narration ("Galinor inspects …"), not NPC-directed dialogue.
_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:i|we|you|he|she|they)\s+(?:inspect|examine|study|search|investigate)(?:s|d|ing)?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\w+\s+(?:inspects|examines|studies|searches|investigates)\b", re.IGNORECASE),
    re.compile(r"\b(?:look|looks|looking)\s+(?:at|around|over)\b", re.IGNORECASE),
    re.compile(r"\b(?:glance|glances|glancing)\s+around\b", re.IGNORECASE),
    re.compile(
        r"\b(?:scan|scans|scanning)\s+(?:the\s+)?(?:area|room|tavern|street|crowd|scene|surroundings|vicinity)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:search|searches|searching)\s+(?:the\s+)?(?:area|room|vicinity|nearby|surroundings)\b", re.IGNORECASE),
    re.compile(r"\b(?:pick|picks|picking)\s+up\b", re.IGNORECASE),
    re.compile(
        r"\b(?:open|opens|opening)\s+(?:the|a|an|this|that|it|his|her|their|my|our)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:unlock|unlocks|unlocking|unlocked)\s+(?:the|a|an|this|that|it)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:take|takes|taking|took)\s+the\s+(?!east\s+road|west\s+road|north\s+road|south\s+road|main\s+road|high\s+road\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:take|takes|taking|took)\s+(?:a|an|his|her|their|its|it|this|that)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:grab|grabs|grabbing|seize|seizes|seizing)\s+(?:the|a|an|his|her|their|its|it|this|that)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:move|moves|moving|step|steps|stepping)\s+(?:past|aside|away|toward|towards|through)\b",
        re.IGNORECASE,
    ),
    # Avoid matching inter-scene travel ("heads to the waste"); keep positional reorientation.
    re.compile(r"\bhead(?:s|ed|ing)?\s+(?:toward|towards)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:check|checks|checking)\s+(?:the|a|an|his|her|their|its|this|that|my|our)\b",
        re.IGNORECASE,
    ),
)

_DIALOGUE_ACT_BEFORE_ESCAPE_RE = re.compile(
    r"\b(?:i|we)\s+(?:ask|asks|asking|tell|tells|telling|say|says|saying|shout|whispers?|call\s+out)\b",
    re.IGNORECASE,
)


def _first_regex_match_start(patterns: tuple[re.Pattern[str], ...], text: str) -> int | None:
    best: int | None = None
    for p in patterns:
        m = p.search(text)
        if m:
            pos = m.start()
            if best is None or pos < best:
                best = pos
    return best


def detect_explicit_non_social_continuity_escape(
    low: str,
    *,
    merged_text: str,
    segmented_turn: Dict[str, Any] | None = None,
) -> bool:
    """True when the merged turn is clearly a concrete non-dialogue action / observation.

    Used to peel explicit inspect / manipulate / scan turns off active-interlocutor dialogue
    continuity without broadly weakening directed questions.
    """
    lane = str(merged_text or "").strip().lower()
    if not lane:
        return False
    if any(p.search(lane) for p in _EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES):
        return True
    if isinstance(segmented_turn, dict):
        obs = _clean_string(segmented_turn.get("observation_intent_text"))
        if obs and any(p.search(obs.lower()) for p in _EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES):
            return True
    return False


def dialogue_intent_blocks_explicit_non_social_continuity_escape(
    low: str,
    *,
    merged_text: str,
) -> bool:
    """When True, dialogue / speech-to-NPC intent should win over continuity escape."""
    lane = str(merged_text or "").strip().lower()
    if not lane:
        return False
    esc_pos = _first_regex_match_start(_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES, lane)
    speech_m = _DIALOGUE_ACT_BEFORE_ESCAPE_RE.search(lane)
    spos = speech_m.start() if speech_m else None
    if spos is not None and (esc_pos is None or spos < esc_pos):
        return True
    return False


def detect_non_social_continuity_escape(
    low: str,
    *,
    merged_text: str,
    segmented_turn: Dict[str, Any] | None = None,
) -> bool:
    """Public alias: explicit non-social signal and dialogue does not veto it."""
    if not detect_explicit_non_social_continuity_escape(low, merged_text=merged_text, segmented_turn=segmented_turn):
        return False
    if dialogue_intent_blocks_explicit_non_social_continuity_escape(low, merged_text=merged_text):
        return False
    return True


def _should_break_social_continuity_for_world_action(
    *,
    merged_text: str,
    low: str,
    roster: List[Dict[str, Any]],
    scene: Dict[str, Any],
    segmented_turn: Dict[str, Any] | None,
    session: Dict[str, Any],
    world: Dict[str, Any],
    decl_cue: bool,
    decl_ok: bool,
    voc_ok: bool,
    motion_ok: bool,
) -> bool:
    """True when this turn should drop active-interlocutor continuity in favor of world-action routing.

    Conservative: explicit addressee cues, declared switches, spoken vocatives, and
    directed motion/ask toward a roster NPC keep social continuity.
    """
    t = str(merged_text or "").strip()
    if not t or not low.strip():
        return False
    if _merged_indicates_travel_not_social(t, scene):
        return True
    if decl_ok or voc_ok:
        return False
    if motion_ok:
        return False
    if detect_non_social_continuity_escape(
        low, merged_text=merged_text, segmented_turn=segmented_turn
    ):
        return True
    if _explicit_address_or_role_cue_in_line(low, roster, merged_text=t):
        return False
    if decl_cue:
        return False
    if isinstance(segmented_turn, dict):
        obs = _clean_string(segmented_turn.get("observation_intent_text"))
        if obs and _merged_text_has_self_directed_sustained_observation(obs.lower()):
            return True
    if _merged_text_has_world_action_movement_or_evade(low):
        return True
    if _merged_text_has_self_directed_world_outcome_question(low):
        return True
    if _merged_text_has_self_directed_sustained_observation(low):
        return True
    return False


def apply_world_action_social_continuity_break(
    session: Dict[str, Any],
    *,
    merged_text: str,
    scene: Dict[str, Any],
) -> None:
    """Clear active social lock so exploration / action-outcome routing can own the turn."""
    if not isinstance(session, dict):
        return
    low = str(merged_text or "").strip().lower()
    kind = (
        "travel"
        if (
            _merged_text_has_world_action_movement_or_evade(low)
            or _merged_indicates_travel_not_social(str(merged_text or "").strip(), scene)
        )
        else "observe"
    )
    set_non_social_activity(session, kind)


def evaluate_world_action_social_continuity_break(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    segmented_turn: Dict[str, Any] | None,
    raw_text: str,
) -> bool:
    """Side-effect-free preview matching :func:`resolve_directed_social_entry` break semantics.

    For callers (e.g. dialogue routing) that have not yet run canonical social entry.
    """
    if not isinstance(session, dict) or not isinstance(scene, dict) or not isinstance(world, dict):
        return False
    scene_obj = scene.get("scene")
    if not isinstance(scene_obj, dict):
        return False
    scene_id = str(scene_obj.get("id") or "").strip()
    if not scene_id:
        return False
    merged = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(raw_text or ""),
    )
    t = merged.strip()
    if not t:
        return False
    low = t.lower()
    ctx = inspect(session)
    active_id = str(ctx.get("active_interaction_target_id") or "").strip()
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
    social_mode = mode == "social" or kind == "social"
    interlocutor_ok = bool(
        active_id
        and social_mode
        and assert_valid_speaker(active_id, session, scene_envelope=scene, world=world)
        and is_actor_addressable_in_current_scene(session, scene, active_id, world=world)
    )
    if not interlocutor_ok:
        return False

    roster = canonical_scene_addressable_roster(
        world, scene_id, scene_envelope=scene, session=session
    )
    decl_sw = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=str(raw_text or ""),
    )
    decl_id = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
    decl_ok = bool(
        decl_id and is_actor_addressable_in_current_scene(session, scene, decl_id, world=world)
    )
    decl_cue = bool(decl_sw.get("has_declared_switch"))
    voc_scan = _text_for_spoken_vocative_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        t,
    )
    voc_res = resolve_spoken_vocative_target(
        session=session,
        scene=scene,
        spoken_text=voc_scan,
    )
    voc_id = _clean_string(voc_res.get("target_actor_id")) if voc_res.get("has_spoken_vocative") else ""
    voc_ok = bool(voc_id and is_actor_addressable_in_current_scene(session, scene, voc_id, world=world))
    motion_id = _npc_id_from_directed_motion_or_ask_phrases(low, roster)
    motion_ok = False
    if motion_id:
        motion_ok = is_actor_addressable_in_current_scene(session, scene, motion_id, world=world)

    return _should_break_social_continuity_for_world_action(
        merged_text=t,
        low=low,
        roster=roster,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        session=session,
        world=world,
        decl_cue=decl_cue,
        decl_ok=decl_ok,
        voc_ok=voc_ok,
        motion_ok=motion_ok,
    )


def world_action_turn_suppresses_npc_answer_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    segmented_turn: Dict[str, Any] | None,
    raw_text: str,
) -> bool:
    """True when Block #1 ``_should_break_social_continuity_for_world_action`` signals this turn is world-action.

    Unlike :func:`evaluate_world_action_social_continuity_break`, this does **not** require an active
    social interlocutor in session. Retry and stale-resolution paths use it so deterministic
    NPC/social answer fallbacks do not hijack self-directed movement, arrival, or observe/result
    questions after continuity has already broken upstream.
    """
    if not isinstance(session, dict) or not isinstance(scene, dict) or not isinstance(world, dict):
        return False
    scene_obj = scene.get("scene")
    if not isinstance(scene_obj, dict):
        return False
    scene_id = str(scene_obj.get("id") or "").strip()
    if not scene_id:
        return False
    merged = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(raw_text or ""),
    )
    t = merged.strip()
    if not t:
        return False
    low = t.lower()
    roster = canonical_scene_addressable_roster(
        world, scene_id, scene_envelope=scene, session=session
    )
    decl_sw = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=str(raw_text or ""),
    )
    decl_id = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
    decl_ok = bool(
        decl_id and is_actor_addressable_in_current_scene(session, scene, decl_id, world=world)
    )
    decl_cue = bool(decl_sw.get("has_declared_switch"))
    voc_scan = _text_for_spoken_vocative_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        t,
    )
    voc_res = resolve_spoken_vocative_target(
        session=session,
        scene=scene,
        spoken_text=voc_scan,
    )
    voc_id = _clean_string(voc_res.get("target_actor_id")) if voc_res.get("has_spoken_vocative") else ""
    voc_ok = bool(voc_id and is_actor_addressable_in_current_scene(session, scene, voc_id, world=world))
    motion_id = _npc_id_from_directed_motion_or_ask_phrases(low, roster)
    motion_ok = False
    if motion_id:
        motion_ok = is_actor_addressable_in_current_scene(session, scene, motion_id, world=world)

    return _should_break_social_continuity_for_world_action(
        merged_text=t,
        low=low,
        roster=roster,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        session=session,
        world=world,
        decl_cue=decl_cue,
        decl_ok=decl_ok,
        voc_ok=voc_ok,
        motion_ok=motion_ok,
    )


def resolve_directed_social_entry(
    *,
    session: dict | None,
    scene: dict | None,
    world: dict | None,
    segmented_turn: dict | None,
    raw_text: str,
) -> dict:
    """Single pre-classification decision: should this turn enter the social pipeline first?

    Runs before adjudication / perception / feasibility classification. Uses
    :func:`is_actor_addressable_in_current_scene` as the only addressability check for the
    resolved target.

    Returns keys: should_route_social, target_actor_id, target_source, reason, spoken_text.
    """
    out: Dict[str, Any] = {
        "should_route_social": False,
        "target_actor_id": None,
        "target_source": None,
        "reason": "",
        "spoken_text": None,
    }
    spoken_raw = (
        segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None
    )
    if isinstance(spoken_raw, str) and spoken_raw.strip():
        out["spoken_text"] = spoken_raw.strip()

    merged = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(raw_text or ""),
    )
    t = merged.strip()
    if not t:
        out["reason"] = "empty_turn"
        return out
    if _line_marked_explicit_ooc(t):
        out["reason"] = "explicit_ooc"
        return out
    if _line_marked_mechanical_table_talk(t):
        out["reason"] = "mechanical_table_talk"
        return out

    if not isinstance(scene, dict):
        out["reason"] = "no_scene_envelope"
        return out
    scene_obj = scene.get("scene")
    if not isinstance(scene_obj, dict):
        out["reason"] = "no_scene_object"
        return out
    scene_id = str(scene_obj.get("id") or "").strip()
    if not scene_id:
        out["reason"] = "empty_scene_id"
        return out

    if _merged_indicates_travel_not_social(t, scene):
        out["reason"] = "travel_or_scene_transition_intent"
        return out

    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else {}
    if sess is None:
        out["reason"] = "no_session"
        return out

    prior_social_target_snapshot = prior_interlocutor_for_turn_metadata(sess) or str(
        inspect(sess).get("active_interaction_target_id") or ""
    ).strip()

    if _looks_like_local_observation_question(t):
        if not _should_recover_social_from_local_observation_followup(
            session=sess,
            scene=scene,
            world=w,
            merged_player_text=t,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        ):
            out["reason"] = "local_scene_observation_query"
            return out

    low = t.lower()
    roster = canonical_scene_addressable_roster(
        w, scene_id, scene_envelope=scene, session=sess
    )

    decl_sw = resolve_declared_actor_switch(
        session=sess,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=str(raw_text or ""),
    )
    decl_id = _clean_string(decl_sw.get("target_actor_id")) if decl_sw.get("has_declared_switch") else ""
    decl_ok = bool(
        decl_id and is_actor_addressable_in_current_scene(sess, scene, decl_id, world=w)
    )

    decl_cue = bool(decl_sw.get("has_declared_switch"))
    voc_scan = _text_for_spoken_vocative_scan(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        t,
    )
    voc_res = resolve_spoken_vocative_target(
        session=sess,
        scene=scene,
        spoken_text=voc_scan,
    )
    voc_id = _clean_string(voc_res.get("target_actor_id")) if voc_res.get("has_spoken_vocative") else ""
    voc_ok = bool(voc_id and is_actor_addressable_in_current_scene(sess, scene, voc_id, world=w))

    if _line_blocks_dialogue_addressing(low) and not _explicit_address_or_role_cue_in_line(
        low, roster, merged_text=t
    ) and not decl_cue:
        out["reason"] = "non_dialogue_world_action"
        return out

    if "?" in t and _SCENE_PRESENCE_OR_SCOPE_QUERY_RE.search(low):
        if (
            not _explicit_address_or_role_cue_in_line(low, roster, merged_text=t)
            and not _npc_id_from_directed_motion_or_ask_phrases(low, roster)
            and not decl_cue
        ):
            out["reason"] = "scene_presence_or_perception_query"
            return out

    motion_id = _npc_id_from_directed_motion_or_ask_phrases(low, roster)
    motion_ok = False
    if motion_id:
        motion_ok = is_actor_addressable_in_current_scene(sess, scene, motion_id, world=w)

    ctx_break = inspect(sess)
    active_break = str(ctx_break.get("active_interaction_target_id") or "").strip()
    mode_break = str(ctx_break.get("interaction_mode") or "").strip().lower()
    kind_break = str(ctx_break.get("active_interaction_kind") or "").strip().lower()
    social_break = mode_break == "social" or kind_break == "social"
    interlocutor_ok_break = bool(
        active_break
        and social_break
        and assert_valid_speaker(active_break, sess, scene_envelope=scene, world=w)
        and is_actor_addressable_in_current_scene(sess, scene, active_break, world=w)
    )
    if interlocutor_ok_break and _should_break_social_continuity_for_world_action(
        merged_text=t,
        low=low,
        roster=roster,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        session=sess,
        world=w,
        decl_cue=decl_cue,
        decl_ok=decl_ok,
        voc_ok=voc_ok,
        motion_ok=motion_ok,
    ):
        apply_world_action_social_continuity_break(sess, merged_text=t, scene=scene)

    broad_detect_cache: Optional[Dict[str, Any]] = None

    def _broad_detect() -> Dict[str, Any]:
        nonlocal broad_detect_cache
        if broad_detect_cache is None:
            broad_detect_cache = detect_broad_address_social_bid(
                t,
                low=low,
                roster=roster,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                session=sess,
                scene_envelope=scene,
                world=w,
            )
        return broad_detect_cache

    auth = resolve_authoritative_social_target(
        sess,
        w,
        scene_id,
        player_text=t,
        normalized_action=None,
        scene_envelope=scene,
        merged_player_prompt=t,
        allow_first_roster_fallback=False,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    )
    auth_id = str(auth.get("npc_id") or "").strip() if auth.get("target_resolved") else ""
    auth_ok = bool(
        auth_id
        and is_actor_addressable_in_current_scene(sess, scene, auth_id, world=w)
        and not auth.get("offscene_target")
    )
    if (
        auth_ok
        and str(auth.get("source") or "").strip() == "continuity"
        and _broad_detect().get("is_broad_address")
    ):
        auth_ok = False

    chosen_id = ""
    chosen_source = ""
    if decl_ok:
        chosen_id = decl_id
        chosen_source = "declared_action"
    elif voc_ok:
        chosen_id = voc_id
        chosen_source = "spoken_vocative"
    elif motion_ok:
        chosen_id = motion_id
        chosen_source = "directed_motion_or_ask"
    elif auth_ok:
        chosen_id = auth_id
        src = str(auth.get("source") or "")
        chosen_source = src or "authoritative_resolver"

    ctx = inspect(sess)
    active_id = str(ctx.get("active_interaction_target_id") or "").strip()
    prior_bind = prior_interlocutor_for_turn_metadata(sess) or active_id
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
    social_mode = mode == "social" or kind == "social"

    interlocutor_ok = bool(
        active_id
        and social_mode
        and assert_valid_speaker(active_id, sess, scene_envelope=scene, world=w)
        and is_actor_addressable_in_current_scene(sess, scene, active_id, world=w)
    )

    # Precedence: interlocutor follow-up only when no explicit addressee cue and no declared switch.
    if (
        not chosen_id
        and interlocutor_ok
        and not _explicit_address_or_role_cue_in_line(low, roster, merged_text=t)
        and not decl_cue
    ):
        if not _broad_detect().get("is_broad_address") and (
            _looks_like_information_seeking_player_question(t)
            or any(phrase in low for phrase in _AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES_IC)
        ):
            chosen_id = active_id
            chosen_source = "active_interlocutor"

    if not chosen_id:
        if not is_gm_or_system_facing_question(t) and not is_rules_or_engine_mechanics_question(t):
            fb = find_addressed_npc_id_for_turn(
                t, sess, w, scene if isinstance(scene, dict) else None
            )
            if fb and is_actor_addressable_in_current_scene(sess, scene, fb, world=w):
                chosen_id = fb
                chosen_source = "scene_address_resolution"

    blocked_open_recovery = (
        (decl_cue and not decl_ok)
        or (bool(voc_res.get("has_spoken_vocative")) and not voc_ok)
        or (bool(motion_id) and not motion_ok)
    )

    if not chosen_id:
        if blocked_open_recovery:
            if is_gm_or_system_facing_question(t):
                out["reason"] = "gm_feasibility"
                return out
            if is_rules_or_engine_mechanics_question(t):
                out["reason"] = "rules_or_mechanics_query"
                return out
            out["reason"] = "no_addressable_target"
            return out
        if is_gm_or_system_facing_question(t):
            out["reason"] = "gm_feasibility"
            return out
        if is_rules_or_engine_mechanics_question(t):
            out["reason"] = "rules_or_mechanics_query"
            return out
        broad = _broad_detect()
        if broad.get("is_broad_address"):
            open_reason = str(broad.get("reason") or "")
            open_phrase = str(broad.get("phrase_matched") or "")
            broadcast_flag = False
        else:
            broadcast_hit = is_broadcast_social_open_call(
                t,
                low=low,
                roster=roster,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                session=sess,
                scene_envelope=scene,
                world=w,
            )
            if not broadcast_hit.get("is_broadcast_open_call"):
                out["reason"] = "no_addressable_target"
                return out
            open_reason = str(broadcast_hit.get("reason") or "")
            open_phrase = str(broadcast_hit.get("phrase_matched") or "")
            broadcast_flag = True

        candidates = rank_open_social_solicitation_candidates(
            sess, w, scene_id, scene_envelope=scene
        )
        if candidates:
            out["should_route_social"] = True
            out["target_actor_id"] = None
            out["target_source"] = "scene_open_bid"
            out["reason"] = "open_social_solicitation"
            out["open_social_solicitation"] = True
            out["broad_address_bid"] = True
            out["broadcast_social_open_call"] = broadcast_flag
            out["candidate_addressable_ids"] = list(candidates)
            out["candidate_addressable_count"] = len(candidates)
            out["broad_address_reason"] = open_reason
            out["broad_address_phrase_matched"] = open_phrase
            out["declared_switch_detected"] = bool(decl_sw.get("has_declared_switch"))
            out["declared_switch_target_actor_id"] = (
                decl_sw.get("target_actor_id") if decl_sw.get("has_declared_switch") else None
            )
            out["continuity_overridden_by_declared_switch"] = False
            out["spoken_vocative_detected"] = bool(voc_res.get("has_spoken_vocative"))
            out["spoken_vocative_target_actor_id"] = (
                voc_res.get("target_actor_id") if voc_res.get("has_spoken_vocative") else None
            )
            out["continuity_overridden_by_spoken_vocative"] = False
            return out
        out["reason"] = "no_addressable_target"
        return out

    addr_ok = is_actor_addressable_in_current_scene(sess, scene, chosen_id, world=w)
    if not addr_ok:
        if is_gm_or_system_facing_question(t):
            out["reason"] = "gm_feasibility"
            return out
        if is_rules_or_engine_mechanics_question(t):
            out["reason"] = "rules_or_mechanics_query"
            return out
        out["reason"] = "target_not_addressable"
        return out

    if is_rules_or_engine_mechanics_question(t) and not (
        addr_ok
        and (
            _looks_like_information_seeking_player_question(t)
            or bool(chosen_source == "directed_motion_or_ask")
            or bool(chosen_source == "declared_action")
            or bool(chosen_source == "spoken_vocative")
            or bool(re.search(r"\b(whether|if)\b", low))
        )
    ):
        out["reason"] = "rules_or_mechanics_query"
        return out

    if detect_non_social_continuity_escape(low, merged_text=t, segmented_turn=segmented_turn):
        out["reason"] = "explicit_non_social_action_escapes_social_lock"
        if prior_social_target_snapshot:
            out["continuity_escape_prior_target_actor_id"] = prior_social_target_snapshot
        return out

    if not _turn_plausibly_addressed_spoken_npc_exchange(
        t, low, chosen_source=str(chosen_source or "")
    ):
        out["reason"] = "not_directed_spoken_interaction"
        return out

    out["should_route_social"] = True
    out["target_actor_id"] = chosen_id
    src_out = str(chosen_source or "")
    if src_out == "continuity":
        src_out = "active_interlocutor"
    out["target_source"] = src_out
    out["declared_switch_detected"] = bool(decl_sw.get("has_declared_switch"))
    out["declared_switch_target_actor_id"] = (
        decl_sw.get("target_actor_id") if decl_sw.get("has_declared_switch") else None
    )
    out["continuity_overridden_by_declared_switch"] = bool(
        decl_cue
        and prior_bind
        and chosen_id
        and prior_bind != chosen_id
        and src_out == "declared_action"
    )
    out["spoken_vocative_detected"] = bool(voc_res.get("has_spoken_vocative"))
    out["spoken_vocative_target_actor_id"] = (
        voc_res.get("target_actor_id") if voc_res.get("has_spoken_vocative") else None
    )
    out["continuity_overridden_by_spoken_vocative"] = bool(
        prior_bind
        and chosen_id
        and prior_bind != chosen_id
        and src_out == "spoken_vocative"
    )
    if src_out == "active_interlocutor":
        out["reason"] = "active_interlocutor_followup"
    elif src_out == "declared_action":
        out["reason"] = "declared_action_actor_switch"
    elif src_out == "spoken_vocative":
        out["reason"] = "spoken_vocative_address"
    elif src_out == "directed_motion_or_ask":
        out["reason"] = "directed_motion_or_ask"
    elif src_out == "generic_role":
        out["reason"] = "generic_role_address"
    elif src_out in ("vocative", "substring", "explicit_target", "scene_address_resolution"):
        out["reason"] = "directed_social_question"
    else:
        out["reason"] = "directed_social_question"
    return out


def _turn_plausibly_addressed_spoken_npc_exchange(text: str, low: str, *, chosen_source: str) -> bool:
    if _looks_like_information_seeking_player_question(text):
        return True
    if '"' in text:
        return True
    if any(token in low for token in _DIALOGUE_SPEECH_MARKERS_IC):
        return True
    if re.search(r"\b(i|we)\s+(?:say|tell|ask|call\s+out)\b", low):
        return True
    if re.search(r"\b(whether|if)\b", low):
        return True
    if chosen_source in (
        "directed_motion_or_ask",
        "declared_action",
        "spoken_vocative",
        "vocative",
        "generic_role",
        "substring",
        "explicit_target",
        "scene_address_resolution",
    ):
        return True
    if chosen_source in ("active_interlocutor", "continuity"):
        return True
    return False


def should_route_addressed_question_to_social(
    text: str | None,
    *,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_envelope: Dict[str, Any] | None,
) -> tuple[bool, Dict[str, Any]]:
    """Canonical gate: delegates to :func:`resolve_directed_social_entry` (single routing owner)."""
    meta: Dict[str, Any] = {
        "route_reason": None,
        "addressed_actor_id": None,
        "addressed_actor_source": None,
    }
    entry = resolve_directed_social_entry(
        session=session,
        scene=scene_envelope,
        world=world,
        segmented_turn=None,
        raw_text=str(text or ""),
    )
    if not entry.get("should_route_social"):
        r = str(entry.get("reason") or "")
        if r in (
            "gm_feasibility",
            "rules_or_mechanics_query",
            "empty_turn",
            "no_addressable_target",
            "target_not_addressable",
            "not_directed_spoken_interaction",
            "explicit_non_social_action_escapes_social_lock",
        ):
            meta["route_reason"] = r
        return False, meta

    meta["route_reason"] = entry.get("reason")
    meta["addressed_actor_id"] = entry.get("target_actor_id")
    meta["addressed_actor_source"] = entry.get("target_source")
    return True, meta


def establish_dialogue_interaction_from_input(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any] | None,
    player_text: str | None,
) -> Dict[str, Any]:
    """Set active social target when the player line addresses an NPC in the current scene."""
    if not isinstance(session, dict) or not isinstance(world, dict):
        return {"established": False, "target_id": None}
    low = str(player_text or "").strip().lower()
    if not low:
        return {"established": False, "target_id": None}
    if _line_blocks_dialogue_addressing(low):
        return {"established": False, "target_id": None}

    target_id = find_addressed_npc_id_for_turn(str(player_text or ""), session, world, scene)
    if not target_id:
        return {"established": False, "target_id": None}

    set_social_target(session, target_id)
    return {"established": True, "target_id": target_id}


from game.social_continuity_routing import (  # noqa: E402
    apply_explicit_non_social_commitment_break,
    should_break_social_commitment_for_input,
)
