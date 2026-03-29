"""Structured clues that drive world progression.

Clues augment session state; narrative output is preserved via mark_clue_discovered.
Supports a knowledge-state layer: discovered, inferred, known_to_player.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

from game.storage import add_pending_lead, get_scene_runtime, is_known_scene_id, mark_clue_discovered
from game.utils import slugify


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


def record_discovered_clue(
    session: Dict[str, Any],
    scene_id: str,
    clue_id: str,
    clue_text: str | None = None,
    world: Dict[str, Any] | None = None,
    *,
    presentation_level: str = "explicit",
) -> Dict[str, Any]:
    """Record a structured clue discovery once per knowledge/runtime identity (idempotent).

    Discovery (knowledge + scene runtime list + discovery log + inference) runs only on first commit.
    Retries return ``duplicate_ignored`` without re-appending, re-logging, or re-running inference.
    Presentation may still be promoted on duplicate when strictly higher than the stored level
    (metadata only; not treated as rediscovery).

    Returns:
        ``{"status": "newly_recorded"|"duplicate_ignored", "clue_id": str}``
    """
    if not clue_id or not isinstance(clue_id, str):
        return {"status": "duplicate_ignored", "clue_id": str(clue_id or "").strip()}
    clue_id = clue_id.strip()
    if not clue_id:
        return {"status": "duplicate_ignored", "clue_id": ""}

    knowledge = _ensure_clue_knowledge(session)
    runtime = session.setdefault("scene_runtime", {})
    if not isinstance(runtime, dict):
        session["scene_runtime"] = {}
        runtime = session["scene_runtime"]
    scene_rt = runtime.setdefault(scene_id, {})
    if not isinstance(scene_rt, dict):
        runtime[scene_id] = {}
        scene_rt = runtime[scene_id]
    clue_ids: List[str] = scene_rt.setdefault("discovered_clue_ids", [])

    # --- A) membership (discovery identity) ---
    already_known = clue_id in knowledge
    already_in_scene_runtime = clue_id in clue_ids

    target_pres = _normalize_presentation(presentation_level, default="explicit")
    if already_known:
        entry = knowledge.get(clue_id)
        current_pres = (
            _normalize_presentation(entry.get("presentation"), default="implicit")
            if isinstance(entry, dict)
            else "implicit"
        )
    else:
        current_pres = "implicit"
    already_presented_same_way = _presentation_rank(target_pres) <= _presentation_rank(current_pres)

    already_discovered = already_known or already_in_scene_runtime

    # --- Duplicate: no knowledge/runtime discovery side effects, no inference, no discovery log ---
    if already_discovered:
        print("[CLUE DUPLICATE IGNORED]", clue_id)
        if already_known and not already_presented_same_way:
            set_clue_presentation(session, clue_id=clue_id, clue_text=clue_text, level=presentation_level)
        return {"status": "duplicate_ignored", "clue_id": clue_id}

    # --- B) first-time commit ---
    clue_ids.append(clue_id)
    add_clue_to_knowledge(session, clue_id, "discovered", clue_text=clue_text, source_scene=scene_id)
    set_clue_presentation(session, clue_id=clue_id, clue_text=clue_text, level=presentation_level)

    # --- C) one-shot side effects ---
    print("[CLUE DISCOVERED]", clue_id)
    if world and isinstance(world, dict):
        run_inference(session, world)

    return {"status": "newly_recorded", "clue_id": clue_id}


def reveal_clue(
    session: Dict[str, Any],
    scene_id: str,
    clue_id: str,
    clue_text: str | None = None,
    world: Dict[str, Any] | None = None,
) -> str:
    """Record that a structured clue was discovered. Augments scene_runtime and clue_knowledge.

    Backward compatible: delegates to :func:`record_discovered_clue`; returns ``clue_id`` string.

    When world is provided, runs inference only on first-time discovery for this clue identity.
    """
    result = record_discovered_clue(
        session,
        scene_id,
        clue_id,
        clue_text=clue_text,
        world=world,
        presentation_level="explicit",
    )
    return str(result.get("clue_id") or "")


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


def _stable_social_lead_id(scene_id: str, npc_id: str, topic_id: str) -> str:
    a, b, c = slugify(scene_id), slugify(npc_id), slugify(topic_id)
    if not c:
        c = "topic"
    return f"social_{a}_{b}_{c}"


def _stable_social_text_lead_id(scene_id: str, npc_id: str, primary_text: str) -> str:
    tail = slugify(primary_text)[:56] or "lead"
    if npc_id:
        return f"social_text_{slugify(scene_id)}_{slugify(npc_id)}_{tail}"
    return f"social_text_{slugify(scene_id)}_{tail}"


def _stable_extracted_lead_id(scene_id: str, *descriptor_parts: str) -> str:
    tail = "_".join(slugify(p) for p in descriptor_parts if p and str(p).strip())
    tail = (tail or "lead")[:96]
    return f"lead_{slugify(scene_id)}_{tail}"


def _effective_social_clue_context(
    resolution: Dict[str, Any],
    scene_id: str,
) -> Tuple[str | None, str | None, List[str], Dict[str, Any] | None, str, str]:
    """Return (effective_clue_id, primary_text, merged_texts, topic, npc_id, topic_tid) from a social resolution."""
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else None

    top_clue_id = str(resolution.get("clue_id") or "").strip() or None
    top_texts: List[str] = []
    for raw in resolution.get("discovered_clues") or []:
        if isinstance(raw, str) and raw.strip():
            t = raw.strip()
            if t not in top_texts:
                top_texts.append(t)

    topic_text = ""
    topic_clue_id: str | None = None
    topic_tid = ""
    if topic:
        topic_text = str(topic.get("clue_text") or topic.get("text") or "").strip()
        topic_clue_id = str(topic.get("clue_id") or topic.get("reveals_clue") or "").strip() or None
        topic_tid = str(topic.get("id") or "").strip()

    merged_texts: List[str] = []
    if topic_text:
        merged_texts.append(topic_text)
    for t in top_texts:
        if t not in merged_texts:
            merged_texts.append(t)
    primary_text = merged_texts[0] if merged_texts else None

    npc_id = str(social.get("npc_id") or "").strip()

    effective_clue_id = top_clue_id or topic_clue_id
    if not effective_clue_id and topic and npc_id and topic_tid:
        effective_clue_id = _stable_social_lead_id(scene_id, npc_id, topic_tid)
    if not effective_clue_id and primary_text:
        effective_clue_id = _stable_social_text_lead_id(scene_id, npc_id, primary_text)

    return effective_clue_id, primary_text, merged_texts, topic, npc_id, topic_tid


def _public_lead_dict(
    *,
    lead_id: str,
    kind: str,
    label: str,
    source_scene_id: str,
    source_npc_id: str | None,
    target_scene_id: str | None = None,
    target_npc_id: str | None = None,
    rumor_text: str | None = None,
    evidence_text: str | None = None,
    extraction_source: str | None = None,
) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "lead_id": lead_id,
        "kind": kind,
        "label": label,
        "source_scene_id": source_scene_id,
        "source_npc_id": source_npc_id,
        "target_scene_id": target_scene_id,
        "target_npc_id": target_npc_id,
        "rumor_text": rumor_text,
        "evidence_text": evidence_text,
    }
    if extraction_source:
        rec["extraction_source"] = extraction_source
    return rec


# Deterministic, conservative phrase → investigative lead signals (low false-positive rate).
_TEXT_LEAD_SPECS: tuple[tuple[re.Pattern[str], str, str, str | None, str | None], ...] = (
    (
        re.compile(r"\bold\s+trading\s+crossroads\b", re.IGNORECASE),
        "location",
        "Ask around the old trading crossroads",
        None,
        "old_trading_crossroads",
    ),
    (
        re.compile(r"\bold\s+milestone\b", re.IGNORECASE),
        "scene",
        "Investigate the old milestone",
        "old_milestone",
        "old_milestone",
    ),
    (
        re.compile(
            r"\b(?:speak|talk)\s+(?:with|to)\s+(?:the\s+)?guards?\b",
            re.IGNORECASE,
        ),
        "npc",
        "Speak with the guards",
        None,
        "guards",
    ),
    (
        re.compile(
            r"\b(?:find|seek|locate)\s+(?:the\s+)?(?:town\s+)?crier\b|\b(?:town\s+)?crier\s+(?:at|near|by)\b",
            re.IGNORECASE,
        ),
        "npc",
        "Find the town crier",
        None,
        "town_crier",
    ),
    (
        re.compile(
            r"\bshipments?\b.{0,48}\bout\s+of\s+(?:the\s+)?city\b|\bout\s+of\s+(?:the\s+)?city\b.{0,48}\bshipments?\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "operation",
        "Shipments moving out of the city",
        None,
        "shipments_city",
    ),
    (
        re.compile(
            r"\bhouse\s+verevin\b.{0,64}\b(?:stronghold|estate|outskirts)\b|\b(?:stronghold|estate|outskirts)\b.{0,64}\bhouse\s+verevin\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "location",
        "House Verevin stronghold at the outskirts",
        None,
        "house_verevin",
    ),
)


def _topic_hook_lead_id(
    scene_id: str,
    npc_id: str | None,
    topic: Dict[str, Any],
    primary_clue_id: str | None,
) -> str:
    """Stable id for topic-hook leads when the engine did not supply a clue_id."""
    if primary_clue_id and str(primary_clue_id).strip():
        return str(primary_clue_id).strip()
    tid = str(topic.get("id") or "").strip()
    if not tid:
        tid = slugify(str(topic.get("text") or topic.get("clue_text") or ""))[:40] or "topic"
    return _stable_social_lead_id(scene_id, str(npc_id or "").strip() or "_scene", tid)


def _structured_social_fact_leads(
    scene_id: str,
    npc_id: str | None,
    resolution: Dict[str, Any],
    topic: Dict[str, Any] | None,
    *,
    suppressed_scene_targets: Set[str],
) -> List[Dict[str, Any]]:
    """Tier B: leads from reconciled structured fields (scene ids as clue ids), no regex."""
    out: List[Dict[str, Any]] = []
    sid = str(scene_id or "").strip()
    if not sid:
        return out
    local_seen: Set[str] = set()

    def _emit_for_scene_target(target_sid: str, label_hint: str | None) -> None:
        ts = str(target_sid or "").strip()
        if not ts or not is_known_scene_id(ts):
            return
        if ts in suppressed_scene_targets:
            return
        lid = _stable_extracted_lead_id(sid, ts)
        if lid in local_seen:
            return
        local_seen.add(lid)
        lab = (label_hint or "").strip() or f"Investigate {ts.replace('_', ' ')}"
        out.append(
            _public_lead_dict(
                lead_id=lid,
                kind="scene",
                label=lab[:200],
                source_scene_id=sid,
                source_npc_id=npc_id,
                target_scene_id=ts,
                target_npc_id=None,
                rumor_text=None,
                evidence_text=None,
                extraction_source="structured_fact:scene_id",
            )
        )

    sources: List[Dict[str, Any]] = []
    if isinstance(resolution, dict):
        sources.append(resolution)
    if isinstance(topic, dict):
        sources.append(topic)

    for src in sources:
        for key in ("clue_id", "reveals_clue"):
            raw = src.get(key)
            if isinstance(raw, str) and raw.strip():
                hint = str(src.get("clue_text") or src.get("text") or "").strip() or None
                _emit_for_scene_target(raw.strip(), hint)

    return out


def _scan_text_for_actionable_leads(
    scene_id: str,
    source_npc_id: str | None,
    text: str,
    *,
    extraction_source_prefix: str,
) -> List[Dict[str, Any]]:
    if not text or not isinstance(text, str) or not text.strip():
        return []

    found: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    low = text.strip()
    for pattern, kind, label, target_scene, slug_tail in _TEXT_LEAD_SPECS:
        if not pattern.search(low):
            continue
        resolved_scene = target_scene
        if resolved_scene and not is_known_scene_id(resolved_scene):
            resolved_scene = None
        rumor: str | None = None
        if not resolved_scene and kind in ("location", "operation", "npc"):
            rumor = label
        lid = _stable_extracted_lead_id(scene_id, slug_tail)
        if lid in seen_ids:
            continue
        seen_ids.add(lid)
        found.append(
            _public_lead_dict(
                lead_id=lid,
                kind=kind,
                label=label,
                source_scene_id=scene_id,
                source_npc_id=source_npc_id,
                target_scene_id=resolved_scene,
                target_npc_id=None,
                rumor_text=rumor,
                evidence_text=text.strip()[:400] or None,
                extraction_source=f"{extraction_source_prefix}:{slug_tail}",
            )
        )
    return found


def extract_actionable_social_leads(
    *,
    scene_id: str,
    npc_id: str | None,
    topic_payload: dict | None,
    social_resolution: dict | None,
    player_facing_text: str | None,
    scene: dict | None,
    session: dict | None,
    primary_clue_id: str | None = None,
    extraction_pass: str = "full",
    narration_text_is_reconciled: bool = False,
) -> List[Dict[str, Any]]:
    """Derive normalized actionable leads from social topic hooks, structured facts, and text (deterministic).

    Precedence (within a pass): **A** explicit ``leads_to_*`` topic hooks → **B** structured facts (e.g. clue id
    that is a known scene id) → **C** regex hooks on reconciled topic/clue strings, then on narration text.

    ``player_facing_text`` for tier **C** narration scans should be the post–Block-3 reconciled/finalized string
    when ``narration_text_is_reconciled`` is True (callers after :func:`reconcile_final_text_with_structured_state`).

    extraction_pass:
        - ``topic``: A + B + C on topic / resolution strings only (no narration).
        - ``narration``: C on ``player_facing_text`` only.
        - ``full``: A + B + C (topic strings first, then narration); deduped by ``lead_id``.
    """
    _ = scene, session  # reserved for future scene-graph / known-NPC hints

    res = social_resolution if isinstance(social_resolution, dict) else {}
    topic = topic_payload if isinstance(topic_payload, dict) else None
    sid = str(scene_id or "").strip()
    if not sid:
        return []

    npc = str(npc_id or "").strip() or None
    pass_norm = str(extraction_pass or "full").strip().lower()
    if pass_norm not in ("full", "topic", "narration"):
        pass_norm = "full"

    leads: List[Dict[str, Any]] = []
    seen_lead_ids: Set[str] = set()
    suppressed_scene_targets: Set[str] = set()
    if topic:
        hook_skip = str(topic.get("leads_to_scene") or "").strip()
        if hook_skip:
            suppressed_scene_targets.add(hook_skip)

    def _add(lead: Dict[str, Any]) -> None:
        lid = str(lead.get("lead_id") or "").strip()
        if not lid or lid in seen_lead_ids:
            return
        seen_lead_ids.add(lid)
        leads.append(lead)

    # --- A: explicit topic hooks (leads_to_*) ---
    if pass_norm in ("full", "topic") and topic:
        hook_scene = str(topic.get("leads_to_scene") or "").strip() or None
        hook_npc = str(topic.get("leads_to_npc") or "").strip() or None
        hook_rumor = str(topic.get("leads_to_rumor") or "").strip() or None
        if hook_scene or hook_npc or hook_rumor:
            hook_lid = _topic_hook_lead_id(sid, npc, topic, primary_clue_id)
            primary_txt = str(topic.get("clue_text") or topic.get("text") or "").strip() or "Social lead"
            _add(
                _public_lead_dict(
                    lead_id=hook_lid,
                    kind="scene" if hook_scene else ("npc" if hook_npc else "rumor"),
                    label=primary_txt[:200],
                    source_scene_id=sid,
                    source_npc_id=npc,
                    target_scene_id=hook_scene,
                    target_npc_id=hook_npc,
                    rumor_text=hook_rumor,
                    evidence_text=None,
                    extraction_source="topic_hook",
                )
            )

    # --- B: reconciled structured social facts (no regex) ---
    if pass_norm in ("full", "topic"):
        for L in _structured_social_fact_leads(
            sid,
            npc,
            res,
            topic,
            suppressed_scene_targets=suppressed_scene_targets,
        ):
            _add(L)

    # --- C: deterministic text hooks on topic + resolution clue strings ---
    if pass_norm in ("full", "topic"):
        texts_c: List[str] = []
        if topic:
            for key in ("clue_text", "text"):
                v = topic.get(key)
                if isinstance(v, str) and v.strip():
                    texts_c.append(v.strip())
        for raw in res.get("discovered_clues") or []:
            if isinstance(raw, str) and raw.strip():
                texts_c.append(raw.strip())
        for chunk in texts_c:
            for L in _scan_text_for_actionable_leads(sid, npc, chunk, extraction_source_prefix="topic_text"):
                ts = str(L.get("target_scene_id") or "").strip()
                if ts and ts in suppressed_scene_targets:
                    continue
                _add(L)

    # --- C (narration slice): same pattern library, reconciled GM text only in this branch ---
    if pass_norm in ("full", "narration") and player_facing_text:
        narr_prefix = "narration_reconciled" if narration_text_is_reconciled else "narration"
        for L in _scan_text_for_actionable_leads(
            sid, npc, player_facing_text, extraction_source_prefix=narr_prefix
        ):
            ts = str(L.get("target_scene_id") or "").strip()
            if ts and ts in suppressed_scene_targets:
                continue
            _add(L)

    return leads


def _lead_has_pending_target(lead: Dict[str, Any]) -> bool:
    return bool(
        str(lead.get("target_scene_id") or "").strip()
        or str(lead.get("target_npc_id") or "").strip()
        or str(lead.get("rumor_text") or "").strip()
    )


def _apply_extracted_social_leads(
    session: Dict[str, Any],
    scene_id: str,
    world: Dict[str, Any],
    leads: List[Dict[str, Any]],
    *,
    actionable_lead_ids: List[str],
    lead_write_targets: List[str],
    primary_canonical_clue_id: str | None = None,
) -> List[str]:
    """Persist supplemental leads (clue knowledge, pending_leads, actionable presentation)."""
    added: List[str] = []
    touched_pending = False
    logged_ids = session.setdefault("social_lead_event_ids", [])
    if not isinstance(logged_ids, list):
        session["social_lead_event_ids"] = []
        logged_ids = session["social_lead_event_ids"]
    primary_skip = str(primary_canonical_clue_id or "").strip() or None

    for lead in leads:
        if not isinstance(lead, dict):
            continue
        cid = str(lead.get("lead_id") or "").strip()
        if not cid:
            continue
        label = str(lead.get("label") or "").strip() or cid
        reveal_clue(session, scene_id, cid, clue_text=label, world=world)
        if label and mark_clue_discovered(session, scene_id, label):
            added.append(label)

        if _lead_has_pending_target(lead):
            pend: Dict[str, Any] = {"clue_id": cid, "text": label}
            ts = str(lead.get("target_scene_id") or "").strip()
            tn = str(lead.get("target_npc_id") or "").strip()
            tr = str(lead.get("rumor_text") or "").strip()
            if ts:
                pend["leads_to_scene"] = ts
            if tn:
                pend["leads_to_npc"] = tn
            if tr:
                pend["leads_to_rumor"] = tr
            newly_pending = add_pending_lead(session, scene_id, pend)
            if newly_pending:
                touched_pending = True
                ext_src = str(lead.get("extraction_source") or "")
                if (
                    ext_src
                    and ext_src != "topic_hook"
                    and cid != primary_skip
                    and cid not in logged_ids
                ):
                    world.setdefault("event_log", []).append(
                        {
                            "type": "social_extracted_lead",
                            "clue_id": cid,
                            "scene_id": scene_id,
                            "source": ext_src,
                        }
                    )
                    logged_ids.append(cid)
                    if "event_log" not in lead_write_targets:
                        lead_write_targets.append("event_log")
            set_clue_presentation(session, clue_id=cid, clue_text=label, level="actionable")
            if cid not in actionable_lead_ids:
                actionable_lead_ids.append(cid)
    if touched_pending and "pending_leads" not in lead_write_targets:
        lead_write_targets.append("pending_leads")
    return added


def apply_social_narration_lead_supplements(
    session: Dict[str, Any],
    scene_id: str,
    world: Dict[str, Any],
    resolution: Dict[str, Any],
    player_facing_text: str,
    scene: Dict[str, Any] | None,
) -> List[str]:
    """Second-pass landing: narration-only patterns after GM text exists. Idempotent."""
    from game.social import SOCIAL_KINDS

    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in SOCIAL_KINDS:
        return []
    if resolution.get("success") is False:
        return []
    if resolution.get("requires_check"):
        return []
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if social.get("offscene_target"):
        return []
    if not social.get("target_resolved", True):
        return []

    eff_id, _primary, _merged, topic, npc_id, _tid = _effective_social_clue_context(resolution, scene_id)
    extra = extract_actionable_social_leads(
        scene_id=scene_id,
        npc_id=npc_id,
        topic_payload=topic,
        social_resolution=resolution,
        player_facing_text=player_facing_text,
        scene=scene,
        session=session,
        primary_clue_id=eff_id,
        extraction_pass="narration",
        narration_text_is_reconciled=True,
    )
    if not extra:
        return []

    actionable_ids: List[str] = []
    targets: List[str] = []
    added_texts = _apply_extracted_social_leads(
        session,
        scene_id,
        world,
        extra,
        actionable_lead_ids=actionable_ids,
        lead_write_targets=targets,
        primary_canonical_clue_id=eff_id,
    )

    meta = resolution.setdefault("metadata", {})
    if isinstance(meta, dict):
        ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}
        merged = dict(ll)
        prev_e = list(merged.get("extracted_lead_ids") or [])
        merged["extracted_lead_ids"] = list(
            dict.fromkeys(
                prev_e + [str(x.get("lead_id")) for x in extra if isinstance(x, dict) and x.get("lead_id")]
            )
        )
        prev_s = list(merged.get("extracted_lead_sources") or [])
        narr_keys = [
            str(x.get("extraction_source") or f"narration:{x.get('lead_id')}")
            for x in extra
            if isinstance(x, dict)
        ]
        merged["extracted_lead_sources"] = list(dict.fromkeys(prev_s + narr_keys))
        merged["extracted_from_text"] = bool(merged.get("extracted_from_text")) or True
        merged["extracted_from_reconciled_text"] = bool(merged.get("extracted_from_reconciled_text")) or True
        merged["actionable_lead_ids"] = list(
            dict.fromkeys(list(merged.get("actionable_lead_ids") or []) + actionable_ids)
        )
        merged["lead_write_targets"] = list(
            dict.fromkeys(list(merged.get("lead_write_targets") or []) + targets)
        )
        merged["narration_supplement_texts"] = added_texts
        meta["lead_landing"] = merged

    return added_texts


# Opening / social hubs where a successful information-bearing exchange must not end with zero actionable leads.
_MINIMUM_ACTIONABLE_LEAD_SCENE_IDS: frozenset[str] = frozenset({"frontier_gate"})
_SCENE_FLAG_MINIMUM_LEAD = "ensure_minimum_actionable_lead_after_social"

_INVESTIGATIVE_EXIT_LABEL_KEYWORDS: tuple[str, ...] = (
    "rumor",
    "patrol",
    "milestone",
    "crossroads",
    "follow",
    "investigate",
    "missing",
    "trail",
    "lead",
    "clue",
    "east",
    "outskirts",
)

# Slug tails aligned with _TEXT_LEAD_SPECS — scan discoverable_clues in this order before generic matches / exits.
_MINIMUM_LEAD_AUTHORED_HOOK_SLUG_PRIORITY: tuple[str, ...] = (
    "old_milestone",
    "old_trading_crossroads",
    "guards",
    "town_crier",
    "shipments_city",
    "house_verevin",
)


def _discoverable_clue_texts(scene_inner: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for raw in scene_inner.get("discoverable_clues") or []:
        if isinstance(raw, str) and raw.strip():
            out.append(raw.strip())
        elif isinstance(raw, dict):
            t = raw.get("text")
            if isinstance(t, str) and t.strip():
                out.append(t.strip())
    return out


def _pick_actionable_lead_from_discoverable_clues(scene_id: str, scene_inner: Dict[str, Any]) -> Dict[str, Any] | None:
    """Prefer milestone / crossroads / guards / crier hooks from authored discoverable strings; then any other match."""
    texts = _discoverable_clue_texts(scene_inner)
    if not texts:
        return None
    sid = str(scene_id or "").strip()
    if not sid:
        return None
    for slug in _MINIMUM_LEAD_AUTHORED_HOOK_SLUG_PRIORITY:
        want_suffix = f"discoverable_clue:{slug}"
        for chunk in texts:
            for L in _scan_text_for_actionable_leads(
                sid, None, chunk, extraction_source_prefix="discoverable_clue"
            ):
                if str(L.get("extraction_source") or "") == want_suffix:
                    return L
    for chunk in texts:
        found = _scan_text_for_actionable_leads(
            sid, None, chunk, extraction_source_prefix="discoverable_clue"
        )
        if found:
            return found[0]
    return None


def _scene_eligible_for_minimum_actionable_lead(scene_id: str, scene: dict | None) -> bool:
    if scene_id in _MINIMUM_ACTIONABLE_LEAD_SCENE_IDS:
        return True
    inner = scene.get("scene") if isinstance(scene, dict) and isinstance(scene.get("scene"), dict) else {}
    return bool(inner.get(_SCENE_FLAG_MINIMUM_LEAD))


def _session_has_actionable_pending_lead(session: Dict[str, Any], scene_id: str) -> bool:
    rt = get_scene_runtime(session, scene_id)
    for p in rt.get("pending_leads") or []:
        if not isinstance(p, dict):
            continue
        if str(p.get("leads_to_scene") or "").strip():
            return True
        if str(p.get("leads_to_npc") or "").strip():
            return True
        if str(p.get("leads_to_rumor") or "").strip():
            return True
    return False


def _social_resolution_carries_information(resolution: Dict[str, Any]) -> bool:
    """True when the social engine surfaced a topic, clue id, or clue strings (same gate as lead landing)."""
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if social.get("social_probe_engine_contract"):
        return True
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else None
    top_clue_id = str(resolution.get("clue_id") or "").strip()
    top_texts: List[str] = []
    for raw in resolution.get("discovered_clues") or []:
        if isinstance(raw, str) and raw.strip():
            t = raw.strip()
            if t not in top_texts:
                top_texts.append(t)
    return bool(topic or top_clue_id or top_texts)


def _score_exit_for_investigative_lead(ex: Dict[str, Any]) -> int:
    score = 0
    wu = ex.get("world_updates_on_transition")
    if isinstance(wu, dict) and wu:
        score += 10
    lab = str(ex.get("label") or "").strip().lower()
    for kw in _INVESTIGATIVE_EXIT_LABEL_KEYWORDS:
        if kw in lab:
            score += 2
    if lab.startswith("enter ") or lab.startswith("go to ") or lab.startswith("return to "):
        score -= 4
    return score


def _pick_best_investigative_exit(scene_inner: Dict[str, Any]) -> Dict[str, Any] | None:
    exits = scene_inner.get("exits") or []
    if not isinstance(exits, list):
        return None
    best: Dict[str, Any] | None = None
    best_score = 0
    for ex in exits:
        if not isinstance(ex, dict):
            continue
        tid = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not tid or not is_known_scene_id(tid):
            continue
        s = _score_exit_for_investigative_lead(ex)
        if s > best_score:
            best_score = s
            best = ex
    return best if best_score >= 3 else None


def ensure_scene_has_minimum_actionable_lead(
    *,
    scene_id: str,
    session: dict,
    scene: dict,
    resolution: dict | None,
    gm_output: dict | None,
    world: dict | None = None,
) -> dict | None:
    """Safety rail: after a successful, information-bearing social turn, ensure at least one actionable pending lead.

    Uses authored discoverable_clues (priority hooks: milestone, crossroads, guards, crier, …), then investigative
    exits, then full structured/text extraction. At most one lead per call.

    Debug: ``resolution["metadata"]["minimum_actionable_lead"]`` plus top-level
    ``minimum_actionable_lead_enforced``, ``enforced_lead_id``, ``enforced_lead_source`` on the same metadata dict.
    """
    from game.social import SOCIAL_KINDS

    sid = str(scene_id or "").strip()
    if not sid or not isinstance(session, dict):
        return None
    if not _scene_eligible_for_minimum_actionable_lead(sid, scene if isinstance(scene, dict) else None):
        return None
    if not isinstance(resolution, dict):
        return None

    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in SOCIAL_KINDS:
        return None
    if resolution.get("success") is False:
        return None
    if resolution.get("requires_check"):
        return None
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if social.get("offscene_target"):
        return None
    if not social.get("target_resolved", True):
        return None
    if not _social_resolution_carries_information(resolution):
        return None
    if _session_has_actionable_pending_lead(session, sid):
        meta = resolution.setdefault("metadata", {})
        if isinstance(meta, dict):
            meta["minimum_actionable_lead"] = {
                "minimum_actionable_lead_enforced": False,
                "enforced_lead_id": None,
                "enforced_lead_source": None,
            }
            meta["minimum_actionable_lead_enforced"] = False
            meta["enforced_lead_id"] = None
            meta["enforced_lead_source"] = None
        return meta.get("minimum_actionable_lead") if isinstance(meta, dict) else None

    scene_inner = scene.get("scene") if isinstance(scene, dict) and isinstance(scene.get("scene"), dict) else {}
    w = world if isinstance(world, dict) else {}

    meta = resolution.setdefault("metadata", {})
    if not isinstance(meta, dict):
        return None

    def _record(enforced: bool, lead_id: str | None, source: str | None) -> dict[str, Any]:
        block: Dict[str, Any] = {
            "minimum_actionable_lead_enforced": enforced,
            "enforced_lead_id": lead_id,
            "enforced_lead_source": source,
        }
        meta["minimum_actionable_lead"] = block
        meta["minimum_actionable_lead_enforced"] = enforced
        meta["enforced_lead_id"] = lead_id
        meta["enforced_lead_source"] = source
        return block

    def _apply_single_enforced_lead(lead: Dict[str, Any], *, primary_skip: str | None) -> str | None:
        _apply_extracted_social_leads(
            session,
            sid,
            w,
            [lead],
            actionable_lead_ids=[],
            lead_write_targets=[],
            primary_canonical_clue_id=primary_skip,
        )
        return str(lead.get("lead_id") or "").strip() or None

    # --- A: authored discoverable_clues (priority hooks, then any pattern match) ---
    disc_lead = _pick_actionable_lead_from_discoverable_clues(sid, scene_inner)
    if disc_lead is not None:
        lid = _apply_single_enforced_lead(disc_lead, primary_skip=None)
        return _record(True, lid, "discoverable_clue")

    # --- B: best investigative exit ---
    best_ex = _pick_best_investigative_exit(scene_inner)
    if best_ex is not None:
        target = str(best_ex.get("target_scene_id") or best_ex.get("targetSceneId") or "").strip()
        label = str(best_ex.get("label") or "").strip() or f"Investigate {target}"
        clue_id = f"minlead_exit_{slugify(sid)}_{slugify(target)}"
        lead = _public_lead_dict(
            lead_id=clue_id,
            kind="scene",
            label=label[:200],
            source_scene_id=sid,
            source_npc_id=None,
            target_scene_id=target,
            target_npc_id=None,
            rumor_text=None,
            evidence_text=None,
            extraction_source="author_exit",
        )
        _apply_single_enforced_lead(lead, primary_skip=None)
        return _record(True, clue_id, "exit")

    # --- C: extracted social (topic + resolution + narration) ---
    eff_id, _p, _m, topic, npc_id, _tid = _effective_social_clue_context(resolution, sid)
    ptext = ""
    if isinstance(gm_output, dict):
        pt = gm_output.get("player_facing_text")
        if isinstance(pt, str):
            ptext = pt.strip()
    extracted = extract_actionable_social_leads(
        scene_id=sid,
        npc_id=npc_id or None,
        topic_payload=topic,
        social_resolution=resolution,
        player_facing_text=ptext or None,
        scene=scene_inner if scene_inner else None,
        session=session,
        primary_clue_id=eff_id,
        extraction_pass="full",
        narration_text_is_reconciled=bool(ptext),
    )
    if extracted:
        L = extracted[0]
        lid = _apply_single_enforced_lead(L, primary_skip=eff_id)
        return _record(True, lid, "extracted_social")

    return _record(False, None, None)


def apply_socially_revealed_leads(
    session: Dict[str, Any],
    scene_id: str,
    world: Dict[str, Any],
    resolution: Dict[str, Any],
    *,
    player_facing_text: str | None = None,
    player_facing_text_is_reconciled: bool = False,
    scene: Dict[str, Any] | None = None,
) -> List[str]:
    """Canonical **first** landing for information revealed by the social engine (single entry point).

    Call from authoritative resolution mutation only for social ``kind`` values; avoid parallel
    clue writes from other layers for the same reveal.

    Normalizes clue/lead candidates from resolution + ``social.topic_revealed``,
    runs :func:`apply_authoritative_clue_discovery`, optionally adds ``pending_leads``,
    promotes presentation to ``actionable`` when a topic carries ``leads_to_*``,
    and appends a single idempotent ``event_log`` entry per stable ``clue_id``.

    Returns:
        Newly-added discovered clue texts (same contract as ``apply_authoritative_clue_discovery``).
    """
    from game.social import SOCIAL_KINDS

    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in SOCIAL_KINDS:
        return []

    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else None

    top_clue_id = str(resolution.get("clue_id") or "").strip() or None
    top_texts: List[str] = []
    for raw in resolution.get("discovered_clues") or []:
        if isinstance(raw, str) and raw.strip():
            t = raw.strip()
            if t not in top_texts:
                top_texts.append(t)

    has_payload = bool(topic or top_clue_id or top_texts)
    if not has_payload:
        meta = resolution.setdefault("metadata", {})
        if isinstance(meta, dict):
            meta["lead_landing"] = {
                "revealed_lead_ids": [],
                "already_known_lead_ids": [],
                "actionable_lead_ids": [],
                "lead_write_targets": [],
                "extracted_lead_ids": [],
                "extracted_lead_sources": [],
                "extracted_from_text": False,
                "extracted_from_reconciled_text": False,
            }
        return []

    effective_clue_id, primary_text, merged_texts, topic, npc_id, topic_tid = _effective_social_clue_context(
        resolution, scene_id
    )

    before_ids = get_all_known_clue_ids(session)
    was_id_known = bool(effective_clue_id and effective_clue_id in before_ids)

    added_texts = apply_authoritative_clue_discovery(
        session,
        scene_id,
        clue_id=effective_clue_id,
        clue_text=primary_text,
        discovered_clues=merged_texts if merged_texts else None,
        world=world,
    )

    ext_pass = (
        "full"
        if (player_facing_text and isinstance(player_facing_text, str) and player_facing_text.strip())
        else "topic"
    )
    extracted = extract_actionable_social_leads(
        scene_id=scene_id,
        npc_id=npc_id or None,
        topic_payload=topic,
        social_resolution=resolution,
        player_facing_text=player_facing_text,
        scene=scene,
        session=session,
        primary_clue_id=effective_clue_id,
        extraction_pass=ext_pass,
        narration_text_is_reconciled=bool(player_facing_text_is_reconciled),
    )

    lead_write_targets: List[str] = ["clue_knowledge", "scene_runtime.discovered_clue_ids"]
    revealed_lead_ids: List[str] = []
    already_known_lead_ids: List[str] = []
    actionable_lead_ids: List[str] = []

    if effective_clue_id:
        if was_id_known:
            already_known_lead_ids.append(effective_clue_id)
        elif effective_clue_id in get_all_known_clue_ids(session):
            revealed_lead_ids.append(effective_clue_id)

    sup_targets: List[str] = []
    supplemental_added = _apply_extracted_social_leads(
        session,
        scene_id,
        world,
        extracted,
        actionable_lead_ids=actionable_lead_ids,
        lead_write_targets=sup_targets,
        primary_canonical_clue_id=effective_clue_id,
    )
    for t in sup_targets:
        if t not in lead_write_targets:
            lead_write_targets.append(t)
    for txt in supplemental_added:
        if txt and txt not in added_texts:
            added_texts.append(txt)

    event_key = effective_clue_id or ""
    logged_ids = session.setdefault("social_lead_event_ids", [])
    if not isinstance(logged_ids, list):
        session["social_lead_event_ids"] = []
        logged_ids = session["social_lead_event_ids"]
    should_log_event = bool(
        event_key
        and event_key not in logged_ids
        and not was_id_known
        and (revealed_lead_ids or added_texts)
    )
    if should_log_event:
        world.setdefault("event_log", []).append(
            {
                "type": "social_lead_revealed",
                "clue_id": event_key,
                "scene_id": scene_id,
                "npc_id": npc_id or None,
                "topic_id": topic_tid or None,
            }
        )
        logged_ids.append(event_key)
        lead_write_targets.append("event_log")

    extracted_from_text_flag = any(
        str(x.get("extraction_source") or "").startswith("narration")
        for x in extracted
        if isinstance(x, dict)
    )
    extracted_from_reconciled_text_flag = bool(player_facing_text_is_reconciled) and any(
        str(x.get("extraction_source") or "").startswith("narration_reconciled")
        for x in extracted
        if isinstance(x, dict)
    )
    extracted_ids = [str(x["lead_id"]) for x in extracted if isinstance(x, dict) and x.get("lead_id")]
    extracted_sources = [
        str(x.get("extraction_source") or "")
        for x in extracted
        if isinstance(x, dict) and x.get("extraction_source")
    ]

    meta = resolution.setdefault("metadata", {})
    if isinstance(meta, dict):
        meta["lead_landing"] = {
            "revealed_lead_ids": revealed_lead_ids,
            "already_known_lead_ids": already_known_lead_ids,
            "actionable_lead_ids": list(dict.fromkeys(actionable_lead_ids)),
            "lead_write_targets": list(dict.fromkeys(lead_write_targets)),
            "extracted_lead_ids": extracted_ids,
            "extracted_lead_sources": list(dict.fromkeys(extracted_sources)),
            "extracted_from_text": extracted_from_text_flag,
            "extracted_from_reconciled_text": extracted_from_reconciled_text_flag,
        }

    return added_texts
