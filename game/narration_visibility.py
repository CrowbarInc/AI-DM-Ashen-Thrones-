"""Engine-owned narration visibility contract (read-only).

Builds a conservative snapshot of what entities and scene-layer facts are in scope
for narration matching. Does not enforce, rewrite, or mutate runtime state.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Optional, Set

from game.interaction_context import (
    addressable_scene_npc_id_universe,
    canonical_scene_addressable_roster,
    inspect,
    npc_dict_by_id,
)

_ALLOWED_NARRATION_SOURCES: Dict[str, str] = {
    "entity_reference": "visible_or_addressable_only",
    "fact_assertion": "visible_only",
}

_THIRD_PERSON_PRONOUNS = (
    "he",
    "she",
    "they",
    "him",
    "her",
    "them",
    "his",
    "hers",
    "their",
    "theirs",
    "himself",
    "herself",
    "themselves",
    "it",
    "its",
    "itself",
)
_THIRD_PERSON_PRONOUN_RE = re.compile(
    rf"(?<!\w)(?:{'|'.join(re.escape(token) for token in _THIRD_PERSON_PRONOUNS)})(?!\w)"
)
_FIRST_MENTION_FAMILIARITY_PHRASES = (
    "you recognize",
    "you remember",
    "you know",
    "you've seen before",
    "this is clearly",
)
_FIRST_MENTION_VISIBLE_ACTION_RE = re.compile(
    r"(?<!\w)(?:"
    r"stand|stands|standing|wait|waits|waiting|lean|leans|leaning|watch|watches|watching|"
    r"look|looks|looking|turn|turns|turning|step|steps|stepping|move|moves|moving|"
    r"sit|sits|sitting|kneel|kneels|kneeling|enter|enters|entering|cross|crosses|crossing|"
    r"raise|raises|raising|lower|lowers|lowering|speak|speaks|speaking|say|says|saying|"
    r"reply|replies|replying|gesture|gestures|gesturing|hold|holds|holding|carry|carries|carrying|"
    r"open|opens|opening|close|closes|closing|block|blocks|blocking|follow|follows|following|"
    r"approach|approaches|approaching|linger|lingers|lingering|nod|nods|nodding|shake|shakes|shaking|"
    r"smile|smiles|smiling|frown|frowns|frowning|glance|glances|glancing|study|studies|studying|"
    r"face|faces|facing|rest|rests|resting|pace|paces|pacing|shout|shouts|shouting|"
    r"call|calls|calling|scan|scans|scanning|signal|signals|signaling"
    r")(?!\w)"
)
_FIRST_MENTION_LOCATION_RE = re.compile(
    r"(?<!\w)(?:"
    r"in|at|near|by|under|beside|beyond|across|inside|outside|before|behind|among|around|on|"
    r"within|from|into|over|through|along|amid|beneath|above|below"
    r")\s+(?:the\s+|a\s+|an\s+|your\s+|this\s+|that\s+)?[a-z][\w'-]*(?:\s+[a-z][\w'-]*){0,4}"
)
_FIRST_MENTION_RELATIONAL_PATTERNS = (
    "next to",
    "across from",
    "in front of",
    "at your side",
    "before you",
    "behind you",
    "near you",
    "with you",
)
_FIRST_MENTION_SCENE_ADVERBIAL_OPENERS = (
    "nearby",
    "across the square",
    "at the gate",
    "by the board",
    "under the awning",
    "in the crowd",
    "near the tavern",
)


def _normalize_visibility_text(value: Any) -> str:
    """Lowercase, collapse whitespace, strip edge punctuation (conservative matching)."""
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split()).strip().lower()
    if not text:
        return ""
    punct = string.punctuation
    while text and text[0] in punct:
        text = text[1:].lstrip().lower()
        text = " ".join(text.split()).strip()
    while text and text[-1] in punct:
        text = text[:-1].rstrip().lower()
        text = " ".join(text.split()).strip()
    return text


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _inner_scene(scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(scene_envelope, dict):
        return {}
    inner = scene_envelope.get("scene")
    if isinstance(inner, dict):
        return inner
    return {}


def _coerce_scene_envelope(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    """Treat ``scene`` as a full envelope or wrap a bare inner scene dict."""
    if not isinstance(scene, dict):
        return {}
    if isinstance(scene.get("scene"), dict):
        return scene
    return {"scene": scene}


def _resolve_scene_id(scene_envelope: Dict[str, Any], session: Dict[str, Any] | None) -> str:
    sid = str(_inner_scene(scene_envelope).get("id") or "").strip()
    if sid:
        return sid
    if not isinstance(session, dict):
        return ""
    st = session.get("scene_state")
    if isinstance(st, dict):
        sid = str(st.get("active_scene_id") or "").strip()
    if not sid:
        sid = str(session.get("active_scene_id") or "").strip()
    return sid


def _collect_scene_visible_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        norm = _normalize_visibility_text(item)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _discoverable_entry_to_text(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("text") or "").strip()
    if isinstance(entry, str):
        return entry.strip()
    return ""


def _collect_scene_discoverable_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("discoverable_clues")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        text = _discoverable_entry_to_text(item)
        norm = _normalize_visibility_text(text)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _collect_scene_hidden_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("hidden_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        norm = _normalize_visibility_text(item)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _alias_bucket_from_row(row: Dict[str, Any], entity_id: str) -> List[str]:
    bucket: List[str] = []
    name = str(row.get("name") or "").strip()
    if name:
        nn = _normalize_visibility_text(name)
        if nn:
            bucket.append(nn)
    aliases_in = row.get("aliases")
    if isinstance(aliases_in, list):
        for a in aliases_in:
            if not isinstance(a, str):
                continue
            an = _normalize_visibility_text(a)
            if an and an not in bucket:
                bucket.append(an)
    if bucket:
        return bucket
    fallback = _normalize_visibility_text(entity_id.replace("_", " ").replace("-", " "))
    return [fallback] if fallback else []


def _world_npc_rows_for_visibility(world: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    w = world if isinstance(world, dict) else {}
    raw = w.get("npcs")
    if not isinstance(raw, list) or not raw:
        from game.defaults import default_world

        raw = default_world().get("npcs") or []
    if not isinstance(raw, list):
        return []
    return [npc for npc in raw if isinstance(npc, dict)]


def _collect_contract_entity_alias_map(
    roster: List[Dict[str, Any]],
    world: Dict[str, Any] | None,
) -> Dict[str, List[str]]:
    """Normalized alias strings per entity id for deterministic reference validation."""
    by_id: Dict[str, List[str]] = {}
    for row in roster:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id") or "").strip()
        if not eid:
            continue
        bucket = _alias_bucket_from_row(row, eid)
        if bucket:
            by_id[eid] = bucket

    for npc in _world_npc_rows_for_visibility(world):
        eid = str(npc.get("id") or "").strip()
        if not eid:
            continue
        bucket = _alias_bucket_from_row(npc, eid)
        if not bucket:
            continue
        current = by_id.get(eid, [])
        merged = list(current)
        for alias in bucket:
            if alias not in merged:
                merged.append(alias)
        if merged:
            by_id[eid] = merged
    return by_id


def _normalized_phrase_in_text(normalized_text: str, phrase: str) -> bool:
    if not normalized_text or not phrase:
        return False
    if normalized_text == phrase:
        return True
    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_text))


def _normalized_fact_match_kind(normalized_text: str, fact: str) -> Optional[str]:
    if not normalized_text or not fact:
        return None
    if normalized_text == fact:
        return "exact"
    if fact in normalized_text:
        return "substring"
    return None


def _fact_check_entry(kind: str, fact: str, match_kind: str) -> Dict[str, str]:
    return {
        "kind": kind,
        "fact": fact,
        "match_kind": match_kind,
    }


def _first_phrase_match_offset(normalized_text: str, phrase: str) -> Optional[int]:
    if not normalized_text or not phrase:
        return None
    match = re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_text)
    if not match:
        return None
    return int(match.start())


def _sentence_bounds_for_offset(text: str, offset: int) -> tuple[int, int]:
    if offset < 0:
        return 0, len(text)
    start = 0
    for match in re.finditer(r"[.!?\n]+", text):
        if match.end() <= offset:
            start = match.end()
            continue
        break
    end = len(text)
    for match in re.finditer(r"[.!?\n]+", text[offset:]):
        end = offset + match.start()
        break
    return start, end


def _sentence_text_for_offset(text: str, offset: int) -> str:
    start, end = _sentence_bounds_for_offset(text, offset)
    return text[start:end].strip()


def _sentence_starts_with_third_person_pronoun(sentence_text: str) -> bool:
    stripped = sentence_text.lstrip(string.whitespace + "\"'([{")
    if not stripped:
        return False
    return bool(re.match(rf"^(?:{'|'.join(re.escape(token) for token in _THIRD_PERSON_PRONOUNS)})(?!\w)", stripped))


def _has_first_mention_grounding(sentence_text: str) -> bool:
    if not sentence_text:
        return False
    lowered = sentence_text.lower()
    stripped = lowered.lstrip(string.whitespace + "\"'([{")
    if any(
        stripped == opener
        or stripped.startswith(f"{opener},")
        or stripped.startswith(f"{opener} ")
        for opener in _FIRST_MENTION_SCENE_ADVERBIAL_OPENERS
    ):
        return True
    if _FIRST_MENTION_VISIBLE_ACTION_RE.search(lowered):
        return True
    if _FIRST_MENTION_LOCATION_RE.search(lowered):
        return True
    return any(phrase in lowered for phrase in _FIRST_MENTION_RELATIONAL_PATTERNS)


def _first_mention_familiarity_phrase(sentence_text: str) -> Optional[str]:
    if not sentence_text:
        return None
    lowered = sentence_text.lower()
    for phrase in _FIRST_MENTION_FAMILIARITY_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def validate_player_facing_first_mentions(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    normalized_text = _normalize_visibility_text(text)
    visible_ids = {
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}

    matched_entities: List[Dict[str, Any]] = []
    for entity_id, raw_aliases in alias_map.items():
        if entity_id not in visible_ids or not isinstance(raw_aliases, list):
            continue
        best_alias = ""
        best_offset: Optional[int] = None
        for raw_alias in raw_aliases:
            if not isinstance(raw_alias, str):
                continue
            alias = _normalize_visibility_text(raw_alias)
            if not alias:
                continue
            offset = _first_phrase_match_offset(normalized_text, alias)
            if offset is None:
                continue
            if best_offset is None or offset < best_offset or (offset == best_offset and len(alias) > len(best_alias)):
                best_alias = alias
                best_offset = offset
        if best_offset is None or not best_alias:
            continue
        matched_entities.append(
            {
                "entity_id": entity_id,
                "matched_alias": best_alias,
                "first_offset": best_offset,
            }
        )

    matched_entities.sort(key=lambda item: (int(item.get("first_offset", 10**9)), -len(str(item.get("matched_alias") or ""))))
    violations: List[Dict[str, Any]] = []
    checked_entities: List[Dict[str, Any]] = []
    first_explicit_entity_offset: Optional[int] = None
    leading_pronoun_detected = False
    leading_pronoun_match: Optional[re.Match[str]] = None

    if matched_entities:
        first_match = matched_entities[0]
        first_explicit_entity_offset = int(first_match.get("first_offset"))
        pronoun_match = _THIRD_PERSON_PRONOUN_RE.search(normalized_text)
        if pronoun_match and pronoun_match.start() < first_explicit_entity_offset:
            leading_pronoun_detected = True
            leading_pronoun_match = pronoun_match
        sentence_start, sentence_end = _sentence_bounds_for_offset(normalized_text, first_explicit_entity_offset)
        first_sentence = normalized_text[sentence_start:sentence_end].strip()
        if not leading_pronoun_detected and _sentence_starts_with_third_person_pronoun(first_sentence):
            first_sentence_pronoun = _THIRD_PERSON_PRONOUN_RE.search(first_sentence.lower())
            if first_sentence_pronoun is not None and (sentence_start + first_sentence_pronoun.start()) < first_explicit_entity_offset:
                leading_pronoun_detected = True
                leading_pronoun_match = first_sentence_pronoun
        if leading_pronoun_detected:
            violations.append(
                {
                    "kind": "pronoun_before_first_explicit_entity",
                    "token": leading_pronoun_match.group(0) if leading_pronoun_match is not None else "",
                    "matched_entity_id": first_match.get("entity_id"),
                    "matched_fact": None,
                }
            )

    for entry in matched_entities:
        entity_id = str(entry.get("entity_id") or "").strip()
        matched_alias = str(entry.get("matched_alias") or "").strip()
        first_offset = int(entry.get("first_offset"))
        sentence_text = _sentence_text_for_offset(normalized_text, first_offset)
        grounding_present = _has_first_mention_grounding(sentence_text)
        familiarity_phrase = _first_mention_familiarity_phrase(sentence_text)
        entity_violation_kinds: List[str] = []
        if not grounding_present:
            entity_violation_kinds.append("first_mention_missing_grounding")
            violations.append(
                {
                    "kind": "first_mention_missing_grounding",
                    "token": matched_alias,
                    "matched_entity_id": entity_id,
                    "matched_fact": None,
                }
            )
        if familiarity_phrase:
            entity_violation_kinds.append("first_mention_unearned_familiarity")
            violations.append(
                {
                    "kind": "first_mention_unearned_familiarity",
                    "token": matched_alias,
                    "matched_entity_id": entity_id,
                    "matched_fact": None,
                    "trigger": familiarity_phrase,
                }
            )
        checked_entities.append(
            {
                "entity_id": entity_id,
                "matched_alias": matched_alias,
                "first_offset": first_offset,
                "grounding_present": grounding_present,
                "familiarity_phrase": familiarity_phrase,
                "violation_kinds": entity_violation_kinds,
            }
        )

    return {
        "ok": not violations,
        "violations": violations,
        "checked_entities": checked_entities,
        "leading_pronoun_detected": leading_pronoun_detected,
        "first_explicit_entity_offset": first_explicit_entity_offset,
    }


def validate_player_facing_visibility(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    normalized_text = _normalize_visibility_text(text)
    visible_ids = {
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    visible_facts = [
        str(raw).strip()
        for raw in (contract.get("visible_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    visible_fact_set = set(visible_facts)
    hidden_facts = [
        str(raw).strip()
        for raw in (contract.get("hidden_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    discoverable_facts = [
        str(raw).strip()
        for raw in (contract.get("discoverable_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]

    violations: List[Dict[str, Any]] = []
    checked_entities: List[Dict[str, Any]] = []
    checked_facts: List[Dict[str, Any]] = []

    for entity_id, raw_aliases in alias_map.items():
        if not isinstance(entity_id, str) or not entity_id.strip() or not isinstance(raw_aliases, list):
            continue
        matched_aliases: List[str] = []
        for raw_alias in raw_aliases:
            if not isinstance(raw_alias, str):
                continue
            alias = _normalize_visibility_text(raw_alias)
            if alias and _normalized_phrase_in_text(normalized_text, alias) and alias not in matched_aliases:
                matched_aliases.append(alias)
        if not matched_aliases:
            continue
        checked_entities.append(
            {
                "entity_id": entity_id,
                "matched_aliases": matched_aliases,
            }
        )
        if entity_id not in visible_ids:
            violations.append(
                {
                    "kind": "unseen_entity_reference",
                    "token": matched_aliases[0],
                    "matched_entity_id": entity_id,
                    "matched_fact": None,
                }
            )

    seen_fact_checks: Set[tuple[str, str]] = set()
    for fact_kind, facts, illegal in (
        ("hidden_fact_strings", hidden_facts, True),
        ("discoverable_fact_strings", discoverable_facts, True),
        ("visible_fact_strings", visible_facts, False),
    ):
        for fact in facts:
            match_kind = _normalized_fact_match_kind(normalized_text, fact)
            if not match_kind:
                continue
            key = (fact_kind, fact)
            if key not in seen_fact_checks:
                checked_facts.append(_fact_check_entry(fact_kind, fact, match_kind))
                seen_fact_checks.add(key)
            if illegal and fact not in visible_fact_set:
                violations.append(
                    {
                        "kind": "undiscovered_fact_assertion",
                        "token": fact,
                        "matched_entity_id": None,
                        "matched_fact": fact,
                    }
                )

    return {
        "ok": not violations,
        "violations": violations,
        "visibility_checked_entities": checked_entities,
        "visibility_checked_facts": checked_facts,
    }


def _resolve_active_interlocutor_id(session: Dict[str, Any] | None) -> Optional[str]:
    if not isinstance(session, dict):
        return None
    ctx = inspect(session)
    tid = str(ctx.get("active_interaction_target_id") or "").strip()
    if tid:
        return tid
    st = session.get("scene_state")
    if isinstance(st, dict):
        il = str(st.get("current_interlocutor") or "").strip()
        if il:
            return il
    return None


def build_narration_visibility_contract(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Return a read-only, conservative narration visibility snapshot (no mutations)."""
    env = _coerce_scene_envelope(scene)
    sid = _resolve_scene_id(env, session)
    w = world if isinstance(world, dict) else None

    visible_ids_set = addressable_scene_npc_id_universe(session, env, w)
    visible_entity_ids = sorted(visible_ids_set)

    inner_for_roster = env.get("scene")
    roster = canonical_scene_addressable_roster(
        w or {},
        sid,
        scene_envelope=env if isinstance(inner_for_roster, dict) else None,
        session=session if isinstance(session, dict) else None,
    )

    alias_map = _collect_contract_entity_alias_map(roster, w)
    visible_entity_names: List[str] = []
    for eid in visible_entity_ids:
        names = alias_map.get(eid)
        if names:
            visible_entity_names.append(names[0])
        else:
            fallback = _normalize_visibility_text(eid.replace("_", " "))
            visible_entity_names.append(fallback or eid.lower())

    return {
        "scene_id": sid or None,
        "visible_entity_ids": list(visible_entity_ids),
        "visible_entity_names": visible_entity_names,
        "visible_entity_aliases": dict(alias_map),
        "active_interlocutor_id": _resolve_active_interlocutor_id(session),
        "visible_fact_strings": _collect_scene_visible_fact_strings(env),
        "discoverable_fact_strings": _collect_scene_discoverable_fact_strings(env),
        "hidden_fact_strings": _collect_scene_hidden_fact_strings(env),
        "allowed_narration_sources": dict(_ALLOWED_NARRATION_SOURCES),
    }
