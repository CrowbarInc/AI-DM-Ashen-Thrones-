"""Engine-owned narration visibility contract (read-only).

Builds a conservative snapshot of what entities and scene-layer facts are in scope
for narration matching. Does not enforce, rewrite, or mutate runtime truth; the
contract is a **view** for matching and prompts, not a persistence root.
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
_SINGULAR_PERSON_PRONOUNS = {"he", "she", "him", "her", "his", "hers", "himself", "herself"}
_SINGULAR_THEY_PRONOUNS = {"they", "them", "their", "theirs", "themselves"}
_NEUTER_PRONOUNS = {"it", "its", "itself"}
_PERSON_LIKE_ENTITY_KINDS = {"npc", "scene_actor", "creature", "humanoid", "person"}
_DIALOGUE_SPAN_PATTERNS = (
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"‘[^’\n]*’"),
    re.compile(r"(?<!\w)'[^'\n]*'(?!\w)"),
)
_LOCAL_NONPERSON_OBJECT_RE = re.compile(
    r"(?<!\w)(?:"
    r"lift|lifts|lifting|unfold|unfolds|unfolding|set|sets|setting|hold|holds|holding|"
    r"carry|carries|carrying|take|takes|taking|place|places|placing|raise|raises|raising|"
    r"lower|lowers|lowering|tap|taps|tapping"
    r")\s+(?:the\s+|a\s+|an\s+|this\s+|that\s+)?([a-z][\w'-]*(?:\s+[a-z][\w'-]*){0,2})"
)
_LOCAL_NONPERSON_LINK_RE = re.compile(
    r"(?<!\w)(?:beside|against|into|onto|under)\s+"
    r"(?:the\s+|a\s+|an\s+|this\s+|that\s+)?([a-z][\w'-]*(?:\s+[a-z][\w'-]*){0,2})"
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


def _role_bucket_from_row(row: Dict[str, Any]) -> List[str]:
    bucket: List[str] = []
    raw_roles = row.get("address_roles")
    if isinstance(raw_roles, list):
        for role in raw_roles:
            if not isinstance(role, str):
                continue
            normalized = _normalize_visibility_text(role)
            if normalized and normalized not in bucket:
                bucket.append(normalized)
    role = row.get("role")
    if isinstance(role, str):
        normalized = _normalize_visibility_text(role)
        if normalized and normalized not in bucket:
            bucket.append(normalized)
    return bucket


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


def _collect_contract_entity_kind_map(
    roster: List[Dict[str, Any]],
    world: Dict[str, Any] | None,
) -> Dict[str, str]:
    by_id: Dict[str, str] = {}
    for row in roster:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id") or "").strip()
        if not eid:
            continue
        kind = str(row.get("kind") or "").strip().lower()
        if kind:
            by_id[eid] = kind

    for npc in _world_npc_rows_for_visibility(world):
        eid = str(npc.get("id") or "").strip()
        if eid and eid not in by_id:
            by_id[eid] = "npc"
    return by_id


def _collect_contract_entity_role_map(
    roster: List[Dict[str, Any]],
    world: Dict[str, Any] | None,
) -> Dict[str, List[str]]:
    by_id: Dict[str, List[str]] = {}
    for row in roster:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id") or "").strip()
        if not eid:
            continue
        bucket = _role_bucket_from_row(row)
        if bucket:
            by_id[eid] = bucket

    for npc in _world_npc_rows_for_visibility(world):
        eid = str(npc.get("id") or "").strip()
        if not eid:
            continue
        bucket = _role_bucket_from_row(npc)
        if not bucket:
            continue
        current = by_id.get(eid, [])
        merged = list(current)
        for role in bucket:
            if role not in merged:
                merged.append(role)
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


def _all_phrase_match_offsets(normalized_text: str, phrase: str) -> List[int]:
    if not normalized_text or not phrase:
        return []
    return [int(match.start()) for match in re.finditer(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_text)]


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


def _mask_dialogue_spans(text: str) -> str:
    if not text:
        return ""
    masked = list(text)
    for pattern in _DIALOGUE_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                masked[index] = " "
    return "".join(masked)


def _split_visibility_sentences(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    sentences: List[Dict[str, Any]] = []
    masked_text = _mask_dialogue_spans(text)
    cursor = 0
    sentence_index = 0
    for match in re.finditer(r"[.!?\n]+", masked_text):
        raw_segment = text[cursor:match.start()]
        stripped = raw_segment.strip()
        if stripped:
            lead_ws = len(raw_segment) - len(raw_segment.lstrip())
            trail_ws = len(raw_segment) - len(raw_segment.rstrip())
            sentences.append(
                {
                    "sentence_index": sentence_index,
                    "start": cursor + lead_ws,
                    "end": match.start() - trail_ws,
                    "text": stripped,
                }
            )
            sentence_index += 1
        cursor = match.end()
    tail = text[cursor:]
    stripped_tail = tail.strip()
    if stripped_tail:
        lead_ws = len(tail) - len(tail.lstrip())
        trail_ws = len(tail) - len(tail.rstrip())
        sentences.append(
            {
                "sentence_index": sentence_index,
                "start": cursor + lead_ws,
                "end": len(text) - trail_ws,
                "text": stripped_tail,
            }
        )
    return sentences


def _sentence_index_for_offset(sentences: List[Dict[str, Any]], offset: int) -> int:
    for sentence in sentences:
        start = int(sentence.get("start", 0))
        end = int(sentence.get("end", 0))
        if start <= offset <= end:
            return int(sentence.get("sentence_index", 0))
    return 0


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


def _entity_reference_class(entity_kind: str) -> str:
    clean = str(entity_kind or "").strip().lower()
    if not clean:
        return "unknown"
    if clean in _PERSON_LIKE_ENTITY_KINDS:
        return "person"
    return "nonperson"


def _referential_pronoun_class(token: str) -> str:
    lowered = str(token or "").strip().lower()
    if lowered in _SINGULAR_PERSON_PRONOUNS:
        return "singular_person"
    if lowered in _SINGULAR_THEY_PRONOUNS:
        return "singular_they"
    if lowered in _NEUTER_PRONOUNS:
        return "neuter"
    return ""


def _person_candidate_ids(
    candidate_ids: List[str],
    candidates_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    return _dedupe_preserve_order(
        [
            entity_id
            for entity_id in candidate_ids
            if _entity_reference_class(str((candidates_by_id.get(entity_id) or {}).get("entity_kind") or "")) == "person"
        ]
    )


def _player_character_coref_aliases(session: Dict[str, Any] | None) -> List[str]:
    if not isinstance(session, dict):
        return []
    raw = str(session.get("character_name") or "").strip()
    if not raw:
        return []
    nn = _normalize_visibility_text(raw)
    if not nn:
        return []
    aliases = [nn]
    parts = nn.split()
    if len(parts) > 1:
        first = parts[0]
        if first and first not in aliases:
            aliases.append(first)
    return _dedupe_preserve_order(aliases)


def _resolve_visible_player_entity_id(session: Dict[str, Any] | None, contract: Dict[str, Any]) -> str:
    """Visible roster entity id whose alias matches session character_name, else ''."""
    aliases = _player_character_coref_aliases(session)
    if not aliases:
        return ""
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    visible_ids = [
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    for eid in visible_ids:
        raw_list = alias_map.get(eid) if isinstance(alias_map.get(eid), list) else []
        for raw in raw_list:
            if not isinstance(raw, str):
                continue
            an = _normalize_visibility_text(raw)
            if an and an in aliases:
                return eid
    return ""


def _session_constrained_player_pronoun_tokens(session: Dict[str, Any] | None) -> Optional[Set[str]]:
    """Optional explicit allow-list of lowercase pronoun tokens for the PC; None = unconstrained."""
    if not isinstance(session, dict):
        return None
    raw = session.get("player_character_pronouns")
    if raw is None:
        raw = session.get("character_pronouns")
    if not isinstance(raw, str) or not raw.strip():
        return None
    low = raw.strip().lower()
    if low in {"he", "him", "his", "masculine", "m", "male", "man"}:
        return set(_SINGULAR_PERSON_PRONOUNS)
    if low in {"she", "her", "hers", "feminine", "f", "female", "woman"}:
        return {"she", "her", "hers", "herself"}
    if low in {"they", "them", "their", "nonbinary", "nb", "enby"}:
        return set(_SINGULAR_THEY_PRONOUNS)
    return None


def _pronoun_token_allowed_for_player_presentation(pronoun_token: str, session: Dict[str, Any] | None) -> bool:
    lowered = str(pronoun_token or "").strip().lower()
    allowed = _session_constrained_player_pronoun_tokens(session)
    if allowed is None:
        return lowered in _SINGULAR_PERSON_PRONOUNS or lowered in _SINGULAR_THEY_PRONOUNS
    return lowered in allowed


def _last_pc_alias_end_before_pronoun(
    *,
    normalized_text: str,
    window_start: int,
    pronoun_start: int,
    aliases: List[str],
) -> Optional[int]:
    best: Optional[int] = None
    for alias in aliases:
        if not alias:
            continue
        for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_text):
            start = int(match.start())
            end = int(match.end())
            if start < window_start or end > pronoun_start:
                continue
            if best is None or end > best:
                best = end
    return best


def _competing_person_mention_strictly_between(
    sentence_mentions: List[Dict[str, Any]],
    *,
    candidates_by_id: Dict[str, Dict[str, Any]],
    pc_alias_end: int,
    pronoun_start: int,
    player_entity_id: str,
) -> bool:
    """True if a person-like explicit mention starts after the PC alias span and before the pronoun."""
    for m in sentence_mentions:
        start = int(m.get("offset", -1))
        if start <= pc_alias_end or start >= pronoun_start:
            continue
        if m.get("is_ambiguous") is True:
            return True
        eid = str(m.get("entity_id") or "").strip()
        if player_entity_id and eid == player_entity_id:
            continue
        if _entity_reference_class(str((candidates_by_id.get(eid) or {}).get("entity_kind") or "")) == "person":
            return True
    return False


def _is_player_character_local_pronoun_reference(
    *,
    normalized_text: str,
    sentence_start: int,
    pronoun_start: int,
    pronoun_token: str,
    session: Dict[str, Any] | None,
    contract: Dict[str, Any],
    candidates_by_id: Dict[str, Dict[str, Any]],
    sentence_mentions: List[Dict[str, Any]],
) -> bool:
    """Narrow safe harbor: same-sentence PC name before pronoun, no competing person between, pronoun OK."""
    pclass = _referential_pronoun_class(pronoun_token)
    if pclass not in {"singular_person", "singular_they"}:
        return False
    if not _pronoun_token_allowed_for_player_presentation(pronoun_token, session):
        return False
    aliases = _player_character_coref_aliases(session)
    if not aliases:
        return False
    pc_end = _last_pc_alias_end_before_pronoun(
        normalized_text=normalized_text,
        window_start=sentence_start,
        pronoun_start=pronoun_start,
        aliases=aliases,
    )
    if pc_end is None:
        return False
    player_eid = _resolve_visible_player_entity_id(session, contract)
    if _competing_person_mention_strictly_between(
        sentence_mentions,
        candidates_by_id=candidates_by_id,
        pc_alias_end=pc_end,
        pronoun_start=pronoun_start,
        player_entity_id=player_eid,
    ):
        return False
    return True


def _candidate_display_labels(
    candidate_entity_ids: List[str],
    candidates_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    return [
        str((candidates_by_id.get(entity_id) or {}).get("display_label") or entity_id)
        for entity_id in candidate_entity_ids
        if entity_id
    ]


def _flatten_mention_candidate_ids(mentions: List[Dict[str, Any]]) -> List[str]:
    return _dedupe_preserve_order(
        [
            str(entity_id).strip()
            for mention in mentions
            for entity_id in (mention.get("candidate_entity_ids") or [])
            if isinstance(entity_id, str) and str(entity_id).strip()
        ]
    )


def _detect_local_nonperson_mentions(
    sentence_text: str,
    *,
    sentence_start: int,
    referential_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    masked_text = _mask_dialogue_spans(sentence_text)
    person_aliases: Set[str] = set()
    for candidate in referential_candidates:
        if _entity_reference_class(str(candidate.get("entity_kind") or "")) != "person":
            continue
        for alias in (candidate.get("aliases") or []):
            normalized = _normalize_visibility_text(alias)
            if normalized:
                person_aliases.add(normalized)

    mentions: List[Dict[str, Any]] = []
    seen_keys: Set[tuple[int, str]] = set()
    for pattern in (_LOCAL_NONPERSON_OBJECT_RE, _LOCAL_NONPERSON_LINK_RE):
        for match in pattern.finditer(masked_text):
            surface = _normalize_visibility_text(match.group(0))
            label = _normalize_visibility_text(match.group(1))
            if not label or surface in person_aliases or label in person_aliases:
                continue
            key = (int(match.start()), label)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            mentions.append(
                {
                    "label": label,
                    "offset": sentence_start + int(match.start()),
                    "end_offset": sentence_start + int(match.end()),
                }
            )
    mentions.sort(key=lambda item: (int(item.get("offset", 10**9)), str(item.get("label") or "")))
    return mentions


def _build_visible_referential_candidates(contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    visible_ids = [
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    name_list = contract.get("visible_entity_names") if isinstance(contract.get("visible_entity_names"), list) else []
    kind_map = contract.get("visible_entity_kinds") if isinstance(contract.get("visible_entity_kinds"), dict) else {}
    role_map = contract.get("visible_entity_roles") if isinstance(contract.get("visible_entity_roles"), dict) else {}
    out: List[Dict[str, Any]] = []
    for index, entity_id in enumerate(visible_ids):
        raw_aliases = alias_map.get(entity_id) if isinstance(alias_map.get(entity_id), list) else []
        aliases = _dedupe_preserve_order(
            [
                _normalize_visibility_text(alias)
                for alias in raw_aliases
                if isinstance(alias, str) and _normalize_visibility_text(alias)
            ]
        )
        raw_roles = role_map.get(entity_id) if isinstance(role_map.get(entity_id), list) else []
        for raw_role in raw_roles:
            role = _normalize_visibility_text(raw_role)
            if not role:
                continue
            for alias in (role, f"the {role}"):
                if alias not in aliases:
                    aliases.append(alias)
        display_label = aliases[0] if aliases else ""
        if not display_label and index < len(name_list) and isinstance(name_list[index], str):
            display_label = _normalize_visibility_text(name_list[index])
        if not display_label:
            display_label = _normalize_visibility_text(entity_id.replace("_", " ").replace("-", " "))
        out.append(
            {
                "entity_id": entity_id,
                "aliases": aliases or ([display_label] if display_label else []),
                "display_label": display_label or entity_id,
                "entity_kind": str(kind_map.get(entity_id) or "").strip().lower(),
            }
        )
    return out


def _detect_explicit_entity_mentions(
    normalized_text: str,
    referential_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    sentences = _split_visibility_sentences(normalized_text)
    masked_text = _mask_dialogue_spans(normalized_text)
    raw_mentions: List[Dict[str, Any]] = []
    for candidate in referential_candidates:
        entity_id = str(candidate.get("entity_id") or "").strip()
        aliases = candidate.get("aliases") if isinstance(candidate.get("aliases"), list) else []
        for raw_alias in aliases:
            alias = _normalize_visibility_text(raw_alias)
            if not entity_id or not alias:
                continue
            for offset in _all_phrase_match_offsets(masked_text, alias):
                raw_mentions.append(
                    {
                        "entity_id": entity_id,
                        "matched_alias": alias,
                        "offset": offset,
                        "end_offset": offset + len(alias),
                    }
                )

    grouped_mentions: List[Dict[str, Any]] = []
    grouped_by_span: Dict[tuple[int, int, str], Dict[str, Any]] = {}
    for mention in raw_mentions:
        key = (
            int(mention.get("offset", -1)),
            int(mention.get("end_offset", -1)),
            str(mention.get("matched_alias") or ""),
        )
        entry = grouped_by_span.get(key)
        if entry is None:
            entry = {
                "matched_alias": str(mention.get("matched_alias") or ""),
                "offset": int(mention.get("offset", -1)),
                "end_offset": int(mention.get("end_offset", -1)),
                "candidate_entity_ids": [],
            }
            grouped_by_span[key] = entry
            grouped_mentions.append(entry)
        entity_id = str(mention.get("entity_id") or "").strip()
        if entity_id and entity_id not in entry["candidate_entity_ids"]:
            entry["candidate_entity_ids"].append(entity_id)

    for mention in grouped_mentions:
        candidate_entity_ids = list(mention.get("candidate_entity_ids") or [])
        mention["entity_id"] = candidate_entity_ids[0] if len(candidate_entity_ids) == 1 else ""
        mention["is_ambiguous"] = len(candidate_entity_ids) > 1

    grouped_mentions.sort(
        key=lambda item: (
            int(item.get("offset", 10**9)),
            -(int(item.get("end_offset", 0)) - int(item.get("offset", 0))),
            str(item.get("matched_alias") or ""),
        )
    )

    selected: List[Dict[str, Any]] = []
    last_end = -1
    for mention in grouped_mentions:
        start = int(mention.get("offset", -1))
        end = int(mention.get("end_offset", -1))
        if start < 0 or end <= start:
            continue
        if start < last_end:
            continue
        selected.append(mention)
        last_end = end

    seen_entities: Set[str] = set()
    for mention in selected:
        offset = int(mention.get("offset", 0))
        sentence_index = _sentence_index_for_offset(sentences, offset)
        sentence = sentences[sentence_index] if 0 <= sentence_index < len(sentences) else {"start": 0, "end": len(normalized_text), "text": normalized_text}
        entity_id = str(mention.get("entity_id") or "").strip()
        mention["first_offset"] = offset
        mention["sentence_index"] = sentence_index
        mention["sentence_start"] = int(sentence.get("start", 0))
        mention["sentence_end"] = int(sentence.get("end", len(normalized_text)))
        mention["sentence_text"] = str(sentence.get("text") or "")
        mention["is_first_mention"] = entity_id not in seen_entities
        if entity_id:
            seen_entities.add(entity_id)
    return selected


def validate_player_facing_referential_clarity(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    normalized_text = _normalize_visibility_text(text)
    referential_candidates = _build_visible_referential_candidates(contract)
    candidates_by_id = {
        str(candidate.get("entity_id") or "").strip(): candidate
        for candidate in referential_candidates
        if isinstance(candidate, dict) and str(candidate.get("entity_id") or "").strip()
    }
    explicit_mentions = _detect_explicit_entity_mentions(normalized_text, referential_candidates)
    sentences = _split_visibility_sentences(normalized_text)
    mentions_by_sentence: Dict[int, List[Dict[str, Any]]] = {}
    for mention in explicit_mentions:
        sentence_index = int(mention.get("sentence_index", 0))
        mentions_by_sentence.setdefault(sentence_index, []).append(mention)

    checked_entities = [
        {
            "entity_id": str(candidate.get("entity_id") or ""),
            "display_label": str(candidate.get("display_label") or ""),
            "aliases": list(candidate.get("aliases") or []),
            "entity_kind": str(candidate.get("entity_kind") or ""),
        }
        for candidate in referential_candidates
    ]
    violations: List[Dict[str, Any]] = []
    player_coref_safe_harbor_tokens: List[str] = []
    previous_sentence_entity_ids: List[str] = []
    previous_sentence_nonperson_labels: List[str] = []
    previous_single_referent: Optional[str] = None
    pending_drift_pair: Optional[List[str]] = None

    for sentence in sentences:
        sentence_index = int(sentence.get("sentence_index", 0))
        sentence_text = str(sentence.get("text") or "")
        sentence_mentions = sorted(
            mentions_by_sentence.get(sentence_index, []),
            key=lambda item: int(item.get("offset", 10**9)),
        )
        sentence_entity_ids = _dedupe_preserve_order(
            [str(item.get("entity_id") or "").strip() for item in sentence_mentions if str(item.get("entity_id") or "").strip()]
        )
        sentence_nonperson_mentions = _detect_local_nonperson_mentions(
            sentence_text,
            sentence_start=int(sentence.get("start", 0)),
            referential_candidates=referential_candidates,
        )
        current_sentence_drift_pair: Optional[List[str]] = None
        current_sentence_drift_offset: Optional[int] = None
        if previous_single_referent and len(sentence_entity_ids) == 1:
            introduced_entity_id = sentence_entity_ids[0]
            previous_class = _entity_reference_class(
                str((candidates_by_id.get(previous_single_referent) or {}).get("entity_kind") or "")
            )
            introduced_class = _entity_reference_class(
                str((candidates_by_id.get(introduced_entity_id) or {}).get("entity_kind") or "")
            )
            if (
                introduced_entity_id != previous_single_referent
                and previous_class == introduced_class
                and previous_class == "person"
            ):
                current_sentence_drift_pair = [previous_single_referent, introduced_entity_id]
                current_sentence_drift_offset = int(sentence_mentions[0].get("offset", 0)) if sentence_mentions else None

        for mention in sentence_mentions:
            if mention.get("is_ambiguous") is not True:
                continue
            candidate_entity_ids = _flatten_mention_candidate_ids([mention])
            violations.append(
                {
                    "kind": "ambiguous_entity_reference",
                    "token": str(mention.get("matched_alias") or ""),
                    "candidate_entity_ids": candidate_entity_ids,
                    "candidate_aliases": _candidate_display_labels(candidate_entity_ids, candidates_by_id),
                    "sentence_text": sentence_text,
                    "offset": int(mention.get("offset", 0)),
                }
            )

        for pronoun_match in _THIRD_PERSON_PRONOUN_RE.finditer(sentence_text):
            token = pronoun_match.group(0).lower()
            pronoun_class = _referential_pronoun_class(token)
            pronoun_offset = int(sentence.get("start", 0)) + int(pronoun_match.start())
            masked_sentence_text = _mask_dialogue_spans(sentence_text)
            if masked_sentence_text[int(pronoun_match.start()) : int(pronoun_match.end())].strip().lower() != token:
                continue
            explicit_before_mentions = [
                item
                for item in sentence_mentions
                if int(item.get("offset", 10**9)) < pronoun_offset
            ]
            explicit_before = _flatten_mention_candidate_ids(explicit_before_mentions)
            explicit_nonperson_before = _dedupe_preserve_order(
                [
                    str(item.get("label") or "").strip()
                    for item in sentence_nonperson_mentions
                    if int(item.get("offset", 10**9)) < pronoun_offset and str(item.get("label") or "").strip()
                ]
            )
            if explicit_before:
                local_candidate_ids = explicit_before
            elif not sentence_entity_ids:
                local_candidate_ids = list(previous_sentence_entity_ids)
            else:
                local_candidate_ids = []
            if explicit_nonperson_before:
                local_nonperson_candidate_labels = explicit_nonperson_before
            else:
                local_nonperson_candidate_labels = list(previous_sentence_nonperson_labels)
            explicit_person_candidate_ids = _person_candidate_ids(explicit_before, candidates_by_id)
            local_person_candidate_ids = _person_candidate_ids(local_candidate_ids, candidates_by_id)

            violation_kind: Optional[str] = None
            candidate_entity_ids: List[str] = []
            candidate_aliases: List[str] = []
            if pronoun_class in {"singular_person", "singular_they"}:
                if (
                    current_sentence_drift_pair
                    and current_sentence_drift_offset is not None
                    and pronoun_offset > current_sentence_drift_offset
                    and len(explicit_person_candidate_ids) != 1
                ):
                    violation_kind = "referent_drift"
                    candidate_entity_ids = list(current_sentence_drift_pair)
                elif pending_drift_pair and not sentence_entity_ids:
                    violation_kind = "referent_drift"
                    candidate_entity_ids = list(pending_drift_pair)
                elif len(local_person_candidate_ids) > 1:
                    violation_kind = "ambiguous_entity_reference"
                    candidate_entity_ids = list(local_person_candidate_ids)
                elif len(local_person_candidate_ids) == 1:
                    candidate_entity_ids = list(local_person_candidate_ids)
                elif local_candidate_ids:
                    violation_kind = "ambiguous_entity_reference"
                    candidate_entity_ids = list(local_candidate_ids)
                else:
                    violation_kind = "ambiguous_entity_reference"
                if violation_kind == "ambiguous_entity_reference" and _is_player_character_local_pronoun_reference(
                    normalized_text=normalized_text,
                    sentence_start=int(sentence.get("start", 0)),
                    pronoun_start=pronoun_offset,
                    pronoun_token=token,
                    session=session,
                    contract=contract,
                    candidates_by_id=candidates_by_id,
                    sentence_mentions=sentence_mentions,
                ):
                    violation_kind = None
                    player_coref_safe_harbor_tokens.append(token)
            elif pronoun_class == "neuter":
                if len(local_nonperson_candidate_labels) > 1:
                    violation_kind = "ambiguous_entity_reference"
                    candidate_aliases = list(local_nonperson_candidate_labels)
                elif len(local_nonperson_candidate_labels) == 1:
                    candidate_aliases = list(local_nonperson_candidate_labels)
                elif local_candidate_ids:
                    violation_kind = "ambiguous_entity_reference"
                    candidate_entity_ids = list(local_candidate_ids)
                else:
                    violation_kind = "ambiguous_entity_reference"

            if not violation_kind:
                continue
            if not candidate_aliases:
                candidate_aliases = _candidate_display_labels(candidate_entity_ids, candidates_by_id)
            violations.append(
                {
                    "kind": violation_kind,
                    "token": token,
                    "candidate_entity_ids": candidate_entity_ids,
                    "candidate_aliases": candidate_aliases,
                    "sentence_text": sentence_text,
                    "offset": pronoun_offset,
                }
            )

        previous_sentence_entity_ids = list(sentence_entity_ids)
        previous_sentence_nonperson_labels = _dedupe_preserve_order(
            [str(item.get("label") or "").strip() for item in sentence_nonperson_mentions if str(item.get("label") or "").strip()]
        )
        previous_single_referent = sentence_entity_ids[0] if len(sentence_entity_ids) == 1 else None
        pending_drift_pair = list(current_sentence_drift_pair) if current_sentence_drift_pair else None

    return {
        "ok": not violations,
        "violations": violations,
        "checked_entities": checked_entities,
        "explicit_mentions": explicit_mentions,
        "referential_clarity_player_coref_safe_harbor_used": bool(player_coref_safe_harbor_tokens),
        "referential_clarity_player_coref_safe_harbor_tokens": list(player_coref_safe_harbor_tokens),
    }


def validate_player_facing_first_mentions(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    exempt_eid = str(grounded_speaker_first_mention_exemption_entity_id or "").strip()
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
        if not grounding_present and exempt_eid and entity_id == exempt_eid:
            grounding_present = True
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
    kind_map = _collect_contract_entity_kind_map(roster, w)
    role_map = _collect_contract_entity_role_map(roster, w)
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
        "visible_entity_kinds": {eid: str(kind_map.get(eid) or "") for eid in visible_entity_ids},
        "visible_entity_roles": {
            eid: list(role_map.get(eid) or [])
            for eid in visible_entity_ids
            if list(role_map.get(eid) or [])
        },
        "active_interlocutor_id": _resolve_active_interlocutor_id(session),
        "visible_fact_strings": _collect_scene_visible_fact_strings(env),
        "discoverable_fact_strings": _collect_scene_discoverable_fact_strings(env),
        "hidden_fact_strings": _collect_scene_hidden_fact_strings(env),
        "allowed_narration_sources": dict(_ALLOWED_NARRATION_SOURCES),
    }
