"""Canonical promoted-NPC shape, normalization, deterministic promotion IDs, and promotion API."""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from game.utils import slugify

# ---------------------------------------------------------------------------
# Canonical field contracts
# ---------------------------------------------------------------------------
VALID_STANCES_TOWARD_PLAYER = frozenset({"neutral", "wary", "favorable", "hostile"})
VALID_INFORMATION_RELIABILITY = frozenset({"truthful", "partial", "misleading"})
VALID_ORIGIN_KINDS = frozenset({"npc", "scene_actor", "crowd_actor"})

_STABLE_ACTOR_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,79}$")


def disposition_to_stance(disposition: Any) -> str:
    """Map legacy disposition to stance_toward_player (backward compatible)."""
    d = str(disposition or "").strip().lower()
    if d == "friendly":
        return "favorable"
    if d == "neutral":
        return "neutral"
    if d == "hostile":
        return "hostile"
    return "wary"


def _coerce_stance(raw: Any, disposition_fallback: str) -> str:
    s = str(raw or "").strip().lower()
    if s in VALID_STANCES_TOWARD_PLAYER:
        return s
    return disposition_to_stance(disposition_fallback)


def _coerce_reliability(raw: Any) -> str:
    r = str(raw or "").strip().lower()
    if r in VALID_INFORMATION_RELIABILITY:
        return r
    return "partial"


def _coerce_origin_kind(raw: Any) -> str:
    k = str(raw or "").strip().lower()
    if k in VALID_ORIGIN_KINDS:
        return k
    return "npc"


def _string_field(npc: Dict[str, Any], key: str, default: str = "") -> None:
    if key not in npc or npc[key] is None:
        npc[key] = default
        return
    npc[key] = str(npc[key]).strip()


def _ensure_str_list(npc: Dict[str, Any], key: str) -> None:
    raw = npc.get(key)
    if raw is None:
        npc[key] = []
        return
    if isinstance(raw, list):
        out: List[str] = []
        for x in raw:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
        npc[key] = out
        return
    if isinstance(raw, str) and raw.strip():
        npc[key] = [raw.strip()]
        return
    npc[key] = []


def _ensure_topics_list(npc: Dict[str, Any]) -> None:
    raw = npc.get("topics")
    if raw is None:
        npc["topics"] = []
        return
    if isinstance(raw, list):
        npc["topics"] = raw
        return
    npc["topics"] = []


def ensure_npc_social_fields(npc: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate *npc* with normalized long-term social fields; safe for legacy records."""
    if not isinstance(npc, dict):
        return npc
    _string_field(npc, "id")
    _string_field(npc, "name")
    _string_field(npc, "location")
    _string_field(npc, "role")
    _string_field(npc, "affiliation")
    _string_field(npc, "availability", "available")
    _string_field(npc, "current_agenda")
    if "disposition" not in npc or npc["disposition"] is None:
        npc["disposition"] = "neutral"
    else:
        npc["disposition"] = str(npc["disposition"]).strip() or "neutral"

    disp = npc["disposition"]
    stance_raw = npc.get("stance_toward_player")
    npc["stance_toward_player"] = _coerce_stance(stance_raw, disp)

    _ensure_str_list(npc, "knowledge_scope")
    npc["information_reliability"] = _coerce_reliability(npc.get("information_reliability"))

    npc["origin_kind"] = _coerce_origin_kind(npc.get("origin_kind"))
    if "origin_scene_id" not in npc or npc["origin_scene_id"] is None:
        loc = str(npc.get("location") or npc.get("scene_id") or "").strip()
        npc["origin_scene_id"] = loc
    else:
        npc["origin_scene_id"] = str(npc["origin_scene_id"]).strip()

    if "promoted_from_actor_id" in npc and npc["promoted_from_actor_id"] is not None:
        pfa = str(npc["promoted_from_actor_id"]).strip()
        npc["promoted_from_actor_id"] = pfa or None
    else:
        npc["promoted_from_actor_id"] = None

    if "promotion_reason" in npc and npc["promotion_reason"] is not None:
        npc["promotion_reason"] = str(npc["promotion_reason"]).strip() or None
    else:
        npc["promotion_reason"] = None

    pt = npc.get("promotion_turn")
    if pt is None or pt == "":
        npc["promotion_turn"] = None
    else:
        try:
            npc["promotion_turn"] = int(pt)
        except (TypeError, ValueError):
            npc["promotion_turn"] = None

    _ensure_str_list(npc, "tags")
    _ensure_topics_list(npc)
    return npc


def normalize_promoted_npc_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a full canonical NPC dict (copy); does not mutate *record*."""
    npc = copy.deepcopy(record) if isinstance(record, dict) else {}
    ensure_npc_social_fields(npc)
    return npc


def deterministic_promoted_npc_id(
    scene_id: str,
    name_or_label: str,
    *,
    source_actor_id: Optional[str] = None,
) -> str:
    """Stable id for a promoted actor: prefer advertised actor id, else scene + label slug."""
    if source_actor_id:
        aid = str(source_actor_id).strip()
        if aid and _STABLE_ACTOR_ID_RE.match(aid):
            return aid[:80]
    sid = slugify(str(scene_id or "")) or "scene"
    label = slugify(str(name_or_label or "")) or "actor"
    combined = f"{sid}__{label}"
    return combined[:80]


def promoted_npc_id_for_actor(
    session: Optional[Dict[str, Any]],
    world: Dict[str, Any],
    scene_id: str,
    actor_id: str,
) -> Optional[str]:
    """If *actor_id* is already represented in ``world[\"npcs\"]``, return that NPC id.

    Matches:
    - ``promoted_from_actor_id == actor_id`` (optional ``origin_scene_id`` must match *scene_id*
      when both sides are non-empty)
    - or an existing world NPC whose ``id`` equals *actor_id* (bootstrap / native NPC row)

    *session* is reserved for future indexes; unused.
    """
    _ = session
    if not isinstance(world, dict):
        return None
    aid = str(actor_id or "").strip()
    if not aid:
        return None
    sid = str(scene_id or "").strip()

    npcs = world.get("npcs")
    if not isinstance(npcs, list):
        return None

    promoted_match: Optional[str] = None
    for raw in npcs:
        if not isinstance(raw, dict):
            continue
        nid = str(raw.get("id") or "").strip()
        if not nid:
            continue
        if nid == aid:
            return nid
        pfa = raw.get("promoted_from_actor_id")
        if pfa is None:
            continue
        if str(pfa).strip() != aid:
            continue
        oscene = str(raw.get("origin_scene_id") or "").strip()
        if sid and oscene and oscene != sid:
            continue
        promoted_match = nid

    return promoted_match


# ---------------------------------------------------------------------------
# Scene actor -> world NPC promotion (deterministic)
# ---------------------------------------------------------------------------


def _clean_id(value: Any) -> str:
    return str(value).strip() if isinstance(value, str) else ""


def _find_roster_row(roster: List[Dict[str, Any]], actor_id: str) -> Optional[Dict[str, Any]]:
    aid = _clean_id(actor_id)
    if not aid:
        return None
    for r in roster:
        if isinstance(r, dict) and _clean_id(r.get("id")) == aid:
            return r
    return None


def _tone_to_stance(tone: Any) -> Optional[str]:
    t = str(tone or "").strip().lower()
    if not t:
        return None
    if t in ("friendly", "warm", "cordial", "helpful", "open", "welcoming"):
        return "favorable"
    if t in ("hostile", "aggressive", "menacing", "threatening", "cruel"):
        return "hostile"
    if t in ("neutral", "calm", "matter-of-fact", "professional", "flat"):
        return "neutral"
    if t in ("wary", "suspicious", "cautious", "guarded", "cold"):
        return "wary"
    return None


def _infer_knowledge_scope(row: Dict[str, Any], scene_id: str) -> List[str]:
    out: List[str] = []
    sid = _clean_id(scene_id)

    def add(s: str) -> None:
        x = s.strip()
        if x and x not in out:
            out.append(x)

    for t in row.get("tags") or []:
        if isinstance(t, str) and t.strip():
            add(t.strip().lower())
    for r in row.get("address_roles") or []:
        if isinstance(r, str) and r.strip():
            add(r.strip().lower())
    role = row.get("role")
    if isinstance(role, str) and role.strip():
        add(role.strip().lower())
    if sid:
        add(f"scene:{sid}")
    return out


def _explicit_reliability(data: Dict[str, Any]) -> Optional[str]:
    r = data.get("information_reliability")
    rs = str(r or "").strip().lower()
    if rs in VALID_INFORMATION_RELIABILITY:
        return rs
    if data.get("truthfulness") is True or data.get("is_truthful") is True:
        return "truthful"
    ts = str(data.get("truthfulness") or "").strip().lower()
    if ts in ("truthful", "true", "yes", "honest"):
        return "truthful"
    return None


def _reliability_for_promotion(row: Dict[str, Any], snap: Optional[Dict[str, Any]]) -> str:
    for src in (row, snap or {}):
        if not isinstance(src, dict):
            continue
        ex = _explicit_reliability(src)
        if ex:
            return ex
    return "partial"


def _resolved_promotion_kind(
    row: Dict[str, Any],
    actor_kind: Optional[str],
) -> Tuple[bool, str, str]:
    """Return (ok, effective_kind_for_origin, detail_kind_string)."""
    if actor_kind is not None and str(actor_kind).strip():
        k = str(actor_kind).strip().lower()
        if k in ("scene_actor", "crowd_actor"):
            return True, k, k
        return False, k, k
    k = str(row.get("kind") or "").strip().lower()
    if not k:
        return True, "scene_actor", ""
    if k in ("scene_actor", "crowd_actor"):
        return True, k, k
    return False, k, k


def _merge_actor_snapshot(row: Dict[str, Any], snap: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = dict(row) if isinstance(row, dict) else {}
    if isinstance(snap, dict):
        for key, val in snap.items():
            if val is not None:
                base[key] = val
    return base


def _apply_promotion_continuity(session: Dict[str, Any], actor_id: str, npc_id: str) -> None:
    from game.storage import get_interaction_context, get_scene_state

    aid = _clean_id(actor_id)
    nid = _clean_id(npc_id)
    if not aid or not nid:
        return
    state = get_scene_state(session)
    pmap = state.setdefault("promoted_actor_npc_map", {})
    if isinstance(pmap, dict):
        pmap[aid] = nid

    ctx = get_interaction_context(session)
    if _clean_id(ctx.get("active_interaction_target_id")) == aid:
        ctx["active_interaction_target_id"] = nid
    if _clean_id(state.get("current_interlocutor")) == aid:
        state["current_interlocutor"] = nid

    if aid == nid:
        return
    ae = state.get("active_entities")
    if isinstance(ae, list):
        new_ae: List[str] = []
        for x in ae:
            if not isinstance(x, str):
                continue
            xs = x.strip()
            if not xs:
                continue
            new_ae.append(nid if xs == aid else xs)
        seen: Set[str] = set()
        deduped: List[str] = []
        for x in new_ae:
            if x not in seen:
                seen.add(x)
                deduped.append(x)
        state["active_entities"] = deduped
    ep = state.get("entity_presence")
    if isinstance(ep, dict) and aid in ep:
        val = ep.pop(aid, None)
        if nid not in ep:
            ep[nid] = val if val is not None else "active"


def promote_scene_actor_to_npc(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    actor_id: str,
    *,
    actor_kind: Optional[str] = None,
    actor_snapshot: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    turn_counter: Optional[int] = None,
) -> Dict[str, Any]:
    """Promote a scene or crowd actor from the authoritative roster into ``world[\"npcs\"]``.

    Idempotent: the same *actor_id* resolves to the same *npc_id* via
    :func:`promoted_npc_id_for_actor` or :func:`deterministic_promoted_npc_id`.
    On success returns ``{\"ok\": True, \"npc_id\", \"npc\", \"already_promoted\"}``.
    On failure returns ``{\"ok\": False, \"error\", \"message\", \"scene_id\", \"actor_id\"}``.
    """
    from game.interaction_context import canonical_scene_addressable_roster
    from game.storage import load_scene, get_scene_state
    from game.world import get_world_npc_by_id, upsert_world_npc

    def _fail(code: str, message: str) -> Dict[str, Any]:
        return {
            "ok": False,
            "error": code,
            "message": message,
            "scene_id": sid,
            "actor_id": aid,
        }

    if not isinstance(session, dict) or not isinstance(world, dict):
        return {
            "ok": False,
            "error": "invalid_input",
            "message": "session and world must be dicts",
            "scene_id": "",
            "actor_id": "",
        }

    sid = _clean_id(scene_id)
    aid = _clean_id(actor_id)
    if not sid:
        return _fail("invalid_scene_id", "scene_id is empty")
    if not aid:
        return _fail("invalid_actor_id", "actor_id is empty")

    get_scene_state(session)

    env = load_scene(sid)
    roster = canonical_scene_addressable_roster(world, sid, scene_envelope=env, session=session)
    row = _find_roster_row(roster, aid)

    existing_npc_id = promoted_npc_id_for_actor(session, world, sid, aid)
    if existing_npc_id:
        cur = get_world_npc_by_id(world, existing_npc_id)
        if not isinstance(cur, dict):
            cur = {}
        patch: Dict[str, Any] = {"id": existing_npc_id}
        pfa = _clean_id(cur.get("promoted_from_actor_id"))
        native_same = not pfa and _clean_id(cur.get("id")) == aid
        merged_src = _merge_actor_snapshot(row or {"id": aid, "name": aid}, actor_snapshot)
        if pfa == aid or native_same:
            for key in ("name", "role", "affiliation", "current_agenda", "topics", "tags", "disposition"):
                if key in merged_src and merged_src[key] is not None and key not in patch:
                    if cur.get(key) in (None, "", []):
                        patch[key] = merged_src[key]
        if pfa == aid:
            if reason and not cur.get("promotion_reason"):
                patch["promotion_reason"] = str(reason).strip()
            if turn_counter is not None and cur.get("promotion_turn") is None:
                patch["promotion_turn"] = int(turn_counter)
            tone_s = _tone_to_stance(merged_src.get("tone"))
            if tone_s and not cur.get("stance_toward_player"):
                patch["stance_toward_player"] = tone_s
            ks = _infer_knowledge_scope(merged_src, sid)
            if ks and not cur.get("knowledge_scope"):
                patch["knowledge_scope"] = ks
            rel = _reliability_for_promotion(merged_src, actor_snapshot)
            if cur.get("information_reliability") in (None, "", "partial") and rel != "partial":
                patch["information_reliability"] = rel
        norm = upsert_world_npc(world, patch)
        _apply_promotion_continuity(session, aid, existing_npc_id)
        return {
            "ok": True,
            "npc_id": existing_npc_id,
            "npc": norm,
            "already_promoted": True,
        }

    if row is None:
        return _fail("actor_not_found", "actor_id not in authoritative roster for this scene")

    ok_kind, eff_kind, detail_k = _resolved_promotion_kind(row, actor_kind)
    if not ok_kind:
        return _fail(
            "not_promotable",
            f"actor kind must be scene_actor or crowd_actor (got {detail_k!r})",
        )

    merged = _merge_actor_snapshot(row, actor_snapshot)
    npc_id = deterministic_promoted_npc_id(
        sid,
        str(merged.get("name") or aid),
        source_actor_id=aid,
    )
    name = str(merged.get("name") or merged.get("display_name") or "").strip()
    if not name:
        name = aid.replace("_", " ").replace("-", " ").title()
    disp = merged.get("disposition")
    if disp is None or (isinstance(disp, str) and not disp.strip()):
        disp = "neutral"
    else:
        disp = str(disp).strip()
    tone_stance = _tone_to_stance(merged.get("tone"))
    record: Dict[str, Any] = {
        "id": npc_id,
        "name": name,
        "location": sid,
        "scene_id": sid,
        "role": str(merged.get("role") or "").strip(),
        "affiliation": str(merged.get("affiliation") or "").strip(),
        "availability": str(merged.get("availability") or "available").strip() or "available",
        "current_agenda": str(merged.get("current_agenda") or "").strip(),
        "disposition": disp,
        "origin_kind": eff_kind,
        "origin_scene_id": sid,
        "promoted_from_actor_id": aid,
        "promotion_reason": str(reason).strip() if reason else None,
        "promotion_turn": int(turn_counter) if turn_counter is not None else None,
        "knowledge_scope": _infer_knowledge_scope(merged, sid),
        "information_reliability": _reliability_for_promotion(merged, actor_snapshot),
        "tags": [],
        "topics": merged.get("topics") if isinstance(merged.get("topics"), list) else [],
    }
    if tone_stance:
        record["stance_toward_player"] = tone_stance
    tags_in = merged.get("tags")
    if isinstance(tags_in, list):
        record["tags"] = [str(t).strip() for t in tags_in if isinstance(t, str) and str(t).strip()]

    norm = upsert_world_npc(world, record)
    _apply_promotion_continuity(session, aid, npc_id)
    return {
        "ok": True,
        "npc_id": npc_id,
        "npc": norm,
        "already_promoted": False,
    }


def should_promote_scene_actor(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    actor_id: str,
) -> bool:
    """Return True if *actor_id* is a promotable roster actor not yet bound to a world NPC row."""
    from game.interaction_context import canonical_scene_addressable_roster
    from game.storage import load_scene, get_scene_state

    if not isinstance(session, dict) or not isinstance(world, dict):
        return False
    sid = _clean_id(scene_id)
    aid = _clean_id(actor_id)
    if not sid or not aid:
        return False
    get_scene_state(session)
    if promoted_npc_id_for_actor(session, world, sid, aid):
        return False
    env = load_scene(sid)
    roster = canonical_scene_addressable_roster(world, sid, scene_envelope=env, session=session)
    row = _find_roster_row(roster, aid)
    if row is None:
        return False
    ok_k, _, _ = _resolved_promotion_kind(row, None)
    return ok_k


def maybe_promote_active_social_target(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    *,
    actor_kind: Optional[str] = None,
    actor_snapshot: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    turn_counter: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """If the active interaction target should be promoted, run promotion; else return None."""
    from game.interaction_context import inspect

    if not isinstance(session, dict):
        return None
    tid = _clean_id((inspect(session).get("active_interaction_target_id")))
    if not tid:
        return None
    if not should_promote_scene_actor(session, world, scene_id, tid):
        return None
    return promote_scene_actor_to_npc(
        session,
        world,
        scene_id,
        tid,
        actor_kind=actor_kind,
        actor_snapshot=actor_snapshot,
        reason=reason,
        turn_counter=turn_counter,
    )
