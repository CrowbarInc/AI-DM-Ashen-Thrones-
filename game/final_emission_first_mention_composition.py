"""Scene-intro / first-mention prose composition for visibility fallback candidates.

Authors grounded composed scene intros, explicit entity intro fallback text, and
related fact/entity matching helpers. Does not own visibility enforcement
orchestration or final output emission.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_text import _normalize_text
from game.final_emission_visibility_fallback import (
    VisibilitySelectedFallback,
    default_first_mention_composition_layers as _default_first_mention_composition_layers,
    first_mention_composition_meta as _first_mention_composition_meta,
    visibility_selected_fallback_candidate as _visibility_selected_fallback_candidate,
)
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_visibility,
)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _lowercase_leading_alpha(text: str) -> str:
    if not text:
        return ""
    chars = list(text)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.lower()
            break
    return "".join(chars)


def _join_entity_clauses(first_clause: str, second_clause: str) -> str:
    first = _normalize_text(first_clause)
    second = _normalize_text(second_clause)
    if not first:
        return second
    if not second:
        return first

    # If first clause already contains "while", avoid stacking it
    if " while " in first.lower():
        return f"{first}, and {second}"
    return f"{first}, while {second}"

def _visible_entity_catalog(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = {
        str(item).strip()
        for item in (contract.get("visible_entity_ids") or [])
        if isinstance(item, str) and str(item).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    inner = _scene_inner(scene)
    addressables = inner.get("addressables") if isinstance(inner.get("addressables"), list) else []
    world_npcs = world.get("npcs") if isinstance(world, dict) and isinstance(world.get("npcs"), list) else []
    world_npc_map = {
        str(row.get("id") or "").strip(): row
        for row in world_npcs
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    ordered_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append_row(entity_id: str, row: Dict[str, Any] | None) -> None:
        if not entity_id or entity_id in seen or entity_id not in visible_ids:
            return
        seen.add(entity_id)
        base = row if isinstance(row, dict) else {}
        display_name = str(base.get("name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (base.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        normalized_aliases = alias_map.get(entity_id) if isinstance(alias_map.get(entity_id), list) else []
        ordered_aliases = _dedupe_preserve_order(
            [display_name]
            + aliases
            + [str(alias).strip() for alias in normalized_aliases if isinstance(alias, str) and str(alias).strip()]
        )
        if not display_name and ordered_aliases:
            display_name = ordered_aliases[0].title()
        role_hints = [
            str(role).strip()
            for role in (base.get("address_roles") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        world_row = world_npc_map.get(entity_id)
        if isinstance(world_row, dict):
            world_role = str(world_row.get("role") or "").strip()
            if world_role:
                role_hints.append(world_role)
        ordered_rows.append(
            {
                "entity_id": entity_id,
                "display_name": display_name or entity_id.replace("_", " ").title(),
                "aliases": ordered_aliases,
                "role_hints": _dedupe_preserve_order(role_hints),
            }
        )

    for row in addressables:
        if not isinstance(row, dict):
            continue
        _append_row(str(row.get("id") or "").strip(), row)

    for entity_id in sorted(visible_ids):
        _append_row(entity_id, world_npc_map.get(entity_id))

    return ordered_rows


def _rewrite_visible_fact_as_explicit_intro(display_name: str, fact_text: str, phrases: List[str]) -> str:
    fact = _output_sentence(fact_text)
    if not fact:
        return ""
    if fact.lower().startswith(display_name.lower()):
        return fact
    for phrase in phrases:
        clean_phrase = _normalize_text(phrase).lower()
        if not clean_phrase:
            continue
        for pattern in (
            rf"^(?:A|An|The)\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
            rf"^One\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
        ):
            match = re.match(pattern, fact, flags=re.IGNORECASE)
            if not match:
                continue
            remainder = (match.group(1) or "").strip()
            if not remainder:
                return _output_sentence(display_name)
            return _output_sentence(f"{display_name} {remainder}")
    return ""


def _scene_grounding_clause(visible_facts: List[str], blocked_phrases: List[str]) -> str:
    blocked = [phrase.lower() for phrase in blocked_phrases if phrase]
    for fact in visible_facts:
        if not fact:
            continue
        lowered = fact.lower()
        if any(phrase in lowered for phrase in blocked):
            continue
        return _lowercase_leading_alpha(fact.rstrip(".!?"))
    return ""


def _fact_matches_keywords(fact: str, keywords: tuple[str, ...]) -> bool:
    lowered = fact.lower()
    return any(keyword in lowered for keyword in keywords)


def _first_fact_matching_keywords(
    visible_facts: List[str],
    keywords: tuple[str, ...],
    *,
    excluded: set[str] | None = None,
) -> str:
    blocked = excluded or set()
    for fact in visible_facts:
        if not fact or fact in blocked:
            continue
        for segment in _fact_segments(fact):
            if segment in blocked:
                continue
            if _fact_matches_keywords(segment, keywords):
                return _output_sentence(segment)
        if _fact_matches_keywords(fact, keywords):
            return fact
    return ""


_ENTITY_COMPOSITION_PREDICATE_STARTS: tuple[tuple[str, str], ...] = (
    ("hangs back", "hangs back"),
    ("calls out", "calls"),
    ("is shouting", "shouts"),
    ("are shouting", "shouts"),
    ("is calling", "calls"),
    ("are calling", "calls"),
    ("is offering", "offers"),
    ("are offering", "offers"),
    ("is watching", "watches"),
    ("are watching", "watches"),
    ("is scanning", "scans"),
    ("are scanning", "scans"),
    ("is studying", "studies"),
    ("are studying", "studies"),
    ("is gesturing", "gestures"),
    ("are gesturing", "gestures"),
    ("is lingering", "lingers"),
    ("are lingering", "lingers"),
    ("is waiting", "waits"),
    ("are waiting", "waits"),
    ("is observing", "observes"),
    ("are observing", "observes"),
    ("is surveying", "surveys"),
    ("are surveying", "surveys"),
    ("is exchanging", "exchanges"),
    ("are exchanging", "exchanges"),
    ("holds", "holds"),
    ("hold", "holds"),
    ("watches", "watches"),
    ("watch", "watches"),
    ("scans", "scans"),
    ("scan", "scans"),
    ("studies", "studies"),
    ("study", "studies"),
    ("shouts", "shouts"),
    ("shout", "shouts"),
    ("calls", "calls"),
    ("call", "calls"),
    ("offers", "offers"),
    ("offer", "offers"),
    ("gestures", "gestures"),
    ("gesture", "gestures"),
    ("lingers", "lingers"),
    ("linger", "lingers"),
    ("waits", "waits"),
    ("wait", "waits"),
    ("observes", "observes"),
    ("observe", "observes"),
    ("surveys", "surveys"),
    ("survey", "surveys"),
    ("exchanges", "exchanges"),
    ("exchange", "exchanges"),
    ("stands", "stands"),
    ("stand", "stands"),
    ("keeps", "keeps"),
    ("keep", "keeps"),
    ("looks", "looks"),
    ("look", "looks"),
    ("glances", "glances"),
    ("glance", "glances"),
    ("murmurs", "murmurs"),
    ("murmur", "murmurs"),
    ("whispers", "whispers"),
    ("whisper", "whispers"),
)
_LOW_INFO_ENTITY_PREDICATE_RE = re.compile(
    r"^(stands|shouts|watches|lingers|waits|scans|gestures)(?:\s+(nearby|there|quietly|silently|still|alone))?$",
    flags=re.IGNORECASE,
)
_ENTITY_DESCRIPTOR_STOPWORDS = {
    "captain",
    "guard",
    "runner",
    "informant",
    "watcher",
    "stranger",
    "refugee",
    "figure",
    "nearby",
    "still",
}
_ENTITY_ROLE_DETAIL_PHRASE_MAP: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("choke", "gate"), "holds the choke at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("line", "gate"), "holds the line at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("crowd",), "scans the crowd at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("gate",), "watches the gate"),
    (("runner", "informant"), ("stew", "rumor"), "calls over the noise with offers of hot stew and rumor"),
    (("runner", "informant"), ("stew",), "calls over the noise with offers of hot stew"),
    (("runner", "informant"), ("crowd",), "calls over the crowd"),
    (("watcher",), ("crowd",), "lingers at the edge of the crowd"),
    (("stranger", "refugee"), ("refugee", "crowd"), "hangs back from the press of refugees"),
    (("stranger", "refugee"), ("crowd",), "hangs back from the crowd"),
)


def _phrase_present(text: str, phrase: str) -> bool:
    clean_text = _normalize_text(text).lower()
    clean_phrase = _normalize_text(phrase).lower()
    if not clean_text or not clean_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(clean_phrase)}(?!\w)", clean_text))


def _entity_descriptor_tokens(display_name: str, aliases: List[str]) -> List[str]:
    tokens: List[str] = []
    for raw in [display_name] + list(aliases):
        for token in re.findall(r"[a-zA-Z][a-zA-Z'-]+", raw.lower()):
            if len(token) < 5 or token in _ENTITY_DESCRIPTOR_STOPWORDS:
                continue
            tokens.append(token)
    return _dedupe_preserve_order(tokens)


def _role_forms(role: str) -> List[str]:
    clean = _normalize_text(role).lower()
    if not clean:
        return []
    forms = [clean]
    if clean.endswith("y") and len(clean) > 1:
        forms.append(f"{clean[:-1]}ies")
    elif clean.endswith(("s", "x", "z", "ch", "sh")):
        forms.append(f"{clean}es")
    else:
        forms.append(f"{clean}s")
    return _dedupe_preserve_order(forms)


def _fact_segments(fact_text: str) -> List[str]:
    clean = _output_sentence(fact_text).rstrip(".!?")
    if not clean:
        return []
    segments = re.split(r"[;:]|(?<=[.!?])\s+", clean)
    return [segment.strip(" ,") for segment in segments if segment.strip(" ,")]


def _extract_leading_subject_and_predicate(segment: str) -> tuple[str, str]:
    clean = _normalize_text(segment)
    if not clean:
        return "", ""
    lowered = clean.lower()
    for predicate_start, _canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        match = re.search(rf"\b{re.escape(predicate_start)}\b", lowered)
        if not match:
            continue
        subject = clean[: match.start()].strip(" ,")
        predicate = clean[match.start() :].strip(" ,")
        if not subject or not predicate:
            continue
        if len(subject.split()) > 9:
            continue
        return subject, predicate
    return "", ""


def _subject_matches_entity(
    subject: str,
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    descriptor_tokens: List[str],
) -> bool:
    lowered_subject = _normalize_text(subject).lower()
    if not lowered_subject:
        return False
    for phrase in _dedupe_preserve_order([display_name] + aliases):
        if _phrase_present(lowered_subject, phrase):
            return True
    for role in role_hints:
        for form in _role_forms(role):
            if _phrase_present(lowered_subject, form):
                return True
    return any(token in lowered_subject for token in descriptor_tokens)


def _singularize_entity_predicate(predicate: str) -> str:
    clean = _normalize_text(predicate)
    if not clean:
        return ""
    lowered = clean.lower()
    replacements = (
        ("are now ", "is now "),
        ("are ", "is "),
        ("hang back", "hangs back"),
        ("hold ", "holds "),
        ("watch ", "watches "),
        ("scan ", "scans "),
        ("study ", "studies "),
        ("shout ", "shouts "),
        ("call ", "calls "),
        ("offer ", "offers "),
        ("gesture ", "gestures "),
        ("linger ", "lingers "),
        ("wait ", "waits "),
        ("observe ", "observes "),
        ("survey ", "surveys "),
        ("exchange ", "exchanges "),
        ("stand ", "stands "),
        ("keep ", "keeps "),
        ("look ", "looks "),
        ("glance ", "glances "),
        ("murmur ", "murmurs "),
        ("whisper ", "whispers "),
    )
    for old, new in replacements:
        if lowered == old.strip():
            return new.strip()
        if lowered.startswith(old):
            return f"{new}{clean[len(old):]}".strip()
    return clean


def _predicate_after_display_name(display_name: str, sentence: str) -> str:
    clean = _output_sentence(sentence).rstrip(".!?")
    if not clean:
        return ""
    lowered_clean = clean.lower()
    lowered_name = display_name.lower()
    if not lowered_clean.startswith(lowered_name):
        return ""
    return clean[len(display_name) :].strip(" ,;:-")


def _entity_predicate_signature(predicate: str) -> tuple[str, bool]:
    clean = _normalize_text(predicate).lower()
    if not clean:
        return "", True
    for predicate_start, canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        if clean == predicate_start or clean.startswith(f"{predicate_start} "):
            return canonical, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))
    first_token = clean.split()[0]
    return first_token, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))


def _composition_candidate(
    *,
    display_name: str,
    predicate: str,
    source_rank: int,
    source_index: int,
    fact_backed: bool,
) -> Dict[str, Any] | None:
    clean_predicate = _normalize_text(predicate).rstrip(".!?")
    if not clean_predicate:
        return None
    verb_key, low_info = _entity_predicate_signature(clean_predicate)
    detail_bonus = 0 if low_info else min(len(clean_predicate.split()), 8)
    return {
        "clause": f"{display_name} {clean_predicate}",
        "verb_key": verb_key,
        "low_info": low_info,
        "fact_backed": fact_backed,
        "score": (source_rank * 100) + detail_bonus,
        "source_index": source_index,
    }


def _generic_entity_intro_predicate(
    *,
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> str:
    signal_text = " ".join(fact.lower() for fact in composition_facts if isinstance(fact, str))
    role_set = {role.lower() for role in role_hints if isinstance(role, str) and role}
    for required_roles, required_tokens, predicate in _ENTITY_ROLE_DETAIL_PHRASE_MAP:
        if role_set.isdisjoint(required_roles):
            continue
        if all(token in signal_text for token in required_tokens):
            return predicate
    if "crowd" in signal_text:
        return "watches the crowd" if slot_index == 0 else "lingers at the edge of the crowd"
    if "gate" in signal_text:
        return "stands at the gate"
    return "watches nearby" if slot_index == 0 else "lingers nearby"


def _entity_clause_candidates(
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> List[Dict[str, Any]]:
    explicit_phrases = _dedupe_preserve_order([display_name] + aliases + role_hints)
    descriptor_tokens = _entity_descriptor_tokens(display_name, aliases)
    candidates: List[Dict[str, Any]] = []
    seen_clauses: set[str] = set()

    for fact_index, fact in enumerate(composition_facts):
        explicit_sentence = ""
        if fact.lower().startswith(display_name.lower()):
            explicit_sentence = fact
        else:
            explicit_sentence = _rewrite_visible_fact_as_explicit_intro(display_name, fact, explicit_phrases)
        if explicit_sentence:
            predicate = _predicate_after_display_name(display_name, explicit_sentence)
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=predicate,
                source_rank=3,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)
        for segment in _fact_segments(fact):
            subject, predicate = _extract_leading_subject_and_predicate(segment)
            if not subject or not predicate:
                continue
            if not _subject_matches_entity(
                subject,
                display_name=display_name,
                aliases=aliases,
                role_hints=role_hints,
                descriptor_tokens=descriptor_tokens,
            ):
                continue
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=_singularize_entity_predicate(predicate),
                source_rank=2,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)

    generic_candidate = _composition_candidate(
        display_name=display_name,
        predicate=_generic_entity_intro_predicate(
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=slot_index,
        ),
        source_rank=1,
        source_index=len(composition_facts),
        fact_backed=False,
    )
    if generic_candidate and generic_candidate["clause"] not in seen_clauses:
        candidates.append(generic_candidate)

    candidates.sort(
        key=lambda item: (
            -int(item.get("score", 0)),
            int(item.get("source_index", 10**6)),
            len(str(item.get("clause") or "")),
        )
    )
    return candidates


def _visible_safe_scene_composition_facts(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[str]:
    inner = _scene_inner(scene)
    raw_candidates: List[str] = list(_scene_visible_facts(scene))
    summary = _output_sentence(str(inner.get("summary") or ""))
    if summary:
        raw_candidates.append(summary)
    raw_journal_seed_facts = inner.get("journal_seed_facts") if isinstance(inner.get("journal_seed_facts"), list) else []
    for item in raw_journal_seed_facts:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            raw_candidates.append(clean)

    visible_safe_facts: List[str] = []
    for candidate in _dedupe_preserve_order(raw_candidates):
        validation = validate_player_facing_visibility(
            candidate,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            visible_safe_facts.append(candidate)
    return visible_safe_facts


def _build_composed_scene_intro(
    narration_visibility: Dict[str, Any],
    visible_entities: List[str],
    composition_facts: List[str],
    scene_context: Dict[str, Any],
) -> str | None:
    scene_context["composition_layers"] = _default_first_mention_composition_layers()
    if not isinstance(narration_visibility, dict) or not composition_facts or not visible_entities:
        return None

    environment = _first_fact_matching_keywords(
        composition_facts,
        (
            "rain",
            "snow",
            "wind",
            "fog",
            "mist",
            "smoke",
            "ash",
            "mud",
            "muddy",
            "stone",
            "gate",
            "wall",
            "square",
            "yard",
            "district",
            "alley",
            "alleyway",
            "tavern",
            "banner",
            "banners",
            "ground",
            "earth",
            "puddle",
            "puddles",
            "crate",
            "crates",
            "path",
            "thicket",
            "milestone",
            "millstone",
            "underbrush",
            "breeze",
        ),
    )
    if not environment:
        return None

    motion = _first_fact_matching_keywords(
        composition_facts,
        (
            "crowd",
            "refugee",
            "refugees",
            "wagon",
            "wagons",
            "traffic",
            "patron",
            "patrons",
            "townsfolk",
            "onlookers",
            "voices",
            "whisper",
            "whispers",
            "murmur",
            "murmurs",
            "shout",
            "shouts",
            "queue",
            "presses",
            "press in",
            "pushes",
            "scan",
            "scans",
            "glance",
            "glances",
            "watch newcomers",
            "tension",
            "tense",
            "agitation",
            "unrest",
            "shift uneasily",
        ),
        excluded={environment},
    )

    entity_rows_by_display_name = (
        scene_context.get("entity_rows_by_display_name")
        if isinstance(scene_context.get("entity_rows_by_display_name"), dict)
        else {}
    )
    visible_entity_ids = {
        str(entity_id).strip()
        for entity_id in (narration_visibility.get("visible_entity_ids") or [])
        if isinstance(entity_id, str) and str(entity_id).strip()
    }
    selected_entity_names: List[str] = []
    for entity_name in visible_entities:
        clean_name = _normalize_text(entity_name)
        if not clean_name or clean_name in selected_entity_names:
            continue
        row = entity_rows_by_display_name.get(clean_name) if isinstance(entity_rows_by_display_name, dict) else None
        entity_id = str((row or {}).get("entity_id") or "").strip() if isinstance(row, dict) else ""
        if visible_entity_ids and entity_id and entity_id not in visible_entity_ids:
            continue
        selected_entity_names.append(clean_name)
    if not selected_entity_names:
        return None

    selected_entity_clauses: List[Dict[str, Any]] = []
    used_verb_keys: set[str] = set()
    for index, entity_name in enumerate(selected_entity_names):
        row = entity_rows_by_display_name.get(entity_name) if isinstance(entity_rows_by_display_name, dict) else {}
        aliases = [
            str(alias).strip()
            for alias in ((row or {}).get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in ((row or {}).get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        clause_candidates = _entity_clause_candidates(
            display_name=entity_name,
            aliases=aliases,
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=index,
        )
        chosen_candidate: Dict[str, Any] | None = None
        for candidate in clause_candidates:
            verb_key = str(candidate.get("verb_key") or "")
            if not selected_entity_clauses:
                chosen_candidate = candidate
                break
            if verb_key and verb_key in used_verb_keys and bool(candidate.get("low_info")):
                continue
            if len(selected_entity_clauses) >= 1 and not bool(candidate.get("fact_backed")):
                continue
            chosen_candidate = candidate
            break
        if not chosen_candidate:
            continue
        selected_entity_clauses.append(
            {
                "entity_name": entity_name,
                "clause": str(chosen_candidate.get("clause") or ""),
                "verb_key": str(chosen_candidate.get("verb_key") or ""),
                "fact_backed": bool(chosen_candidate.get("fact_backed")),
                "low_info": bool(chosen_candidate.get("low_info")),
            }
        )
        verb_key = str(chosen_candidate.get("verb_key") or "")
        if verb_key:
            used_verb_keys.add(verb_key)
        if len(selected_entity_clauses) >= 2:
            break
    if not selected_entity_clauses:
        return None

    entity_sentence = selected_entity_clauses[0]["clause"]
    if len(selected_entity_clauses) > 1:
        first_clause = selected_entity_clauses[0]
        second_clause = selected_entity_clauses[1]
        if (
            first_clause["verb_key"]
            and second_clause["verb_key"]
            and first_clause["verb_key"] != second_clause["verb_key"]
            and not second_clause["low_info"]
        ):
            entity_sentence = _join_entity_clauses(
                first_clause["clause"],
                second_clause["clause"],
            )

    scene_sentence = environment.rstrip(".!?")
    if motion:
        scene_sentence = f"{scene_sentence} while {_lowercase_leading_alpha(motion.rstrip('.!?'))}"

    scene_context["composition_layers"] = {
        "environment": environment,
        "motion": motion or None,
        "entities": [str(item.get("entity_name") or "") for item in selected_entity_clauses if str(item.get("entity_name") or "")],
    }
    return f"{_output_sentence(scene_sentence)} {_output_sentence(entity_sentence)}".strip()


def _grounded_scene_intro_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    active_interlocutor: str,
) -> List[VisibilitySelectedFallback]:
    visible_facts = _scene_visible_facts(scene)
    composition_facts = _visible_safe_scene_composition_facts(session=session, scene=scene, world=world)
    entity_rows = _visible_entity_catalog(session=session, scene=scene, world=world)
    if not entity_rows and not composition_facts and not visible_facts:
        return []

    narration_visibility = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    inner = _scene_inner(scene)
    scene_location = str(inner.get("location") or inner.get("id") or "").strip()
    prioritized_entities: List[Dict[str, Any]] = []
    if active_interlocutor:
        for row in entity_rows:
            if str(row.get("entity_id") or "").strip() == active_interlocutor:
                prioritized_entities.append(row)
                break
    for row in entity_rows:
        if row not in prioritized_entities:
            prioritized_entities.append(row)

    fallback_candidates: List[VisibilitySelectedFallback] = []
    composed_scene_context: Dict[str, Any] = {
        "scene_location": scene_location,
        "entity_rows_by_display_name": {
            str(row.get("display_name") or "").strip(): row
            for row in prioritized_entities
            if isinstance(row, dict) and str(row.get("display_name") or "").strip()
        },
    }
    composed_scene_intro = _build_composed_scene_intro(
        narration_visibility,
        [str(row.get("display_name") or "").strip() for row in prioritized_entities if str(row.get("display_name") or "").strip()],
        composition_facts,
        composed_scene_context,
    )
    composed_layers = composed_scene_context.get("composition_layers")
    if composed_scene_intro and isinstance(composed_layers, dict):
        fallback_candidates.append(
            _visibility_selected_fallback_candidate(
                composed_scene_intro,
                "visible_scene_composed_intro",
                "first_mention_composed_scene_intro",
                "composed_visible_scene_intro",
                "composed_visible_scene_intro",
                "visible_scene_composed_intro",
                _first_mention_composition_meta(
                    used=True,
                    environment=str(composed_layers.get("environment") or "") or None,
                    motion=str(composed_layers.get("motion") or "") or None,
                    entities=composed_layers.get("entities") if isinstance(composed_layers.get("entities"), list) else [],
                ),
            )
        )

    for row in prioritized_entities:
        entity_id = str(row.get("entity_id") or "").strip()
        display_name = str(row.get("display_name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (row.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in (row.get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        subject_phrases = _dedupe_preserve_order(aliases + role_hints)

        explicit_fact_intro = ""
        for fact in visible_facts:
            explicit_fact_intro = _rewrite_visible_fact_as_explicit_intro(display_name, fact, subject_phrases)
            if explicit_fact_intro:
                break
        if explicit_fact_intro:
            fallback_candidates.append(
                _visibility_selected_fallback_candidate(
                    explicit_fact_intro,
                    "visible_scene_explicit_intro",
                    "first_mention_explicit_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    f"visible_entity:{entity_id}",
                    _first_mention_composition_meta(),
                )
            )

        grounding_clause = _scene_grounding_clause(visible_facts, subject_phrases)
        if scene_location and grounding_clause:
            generic_intro = f"{display_name} stands in {scene_location} while {grounding_clause}."
        elif scene_location:
            generic_intro = f"{display_name} stands in {scene_location}."
        elif grounding_clause:
            generic_intro = f"{display_name} stands nearby while {grounding_clause}."
        else:
            generic_intro = f"{display_name} stands nearby."
        fallback_candidates.append(
            _visibility_selected_fallback_candidate(
                _output_sentence(generic_intro),
                "visible_scene_explicit_intro",
                "first_mention_explicit_scene_intro",
                "explicit_visible_entity_scene_intro",
                "explicit_visible_entity_scene_intro",
                f"visible_entity:{entity_id}",
                _first_mention_composition_meta(),
            )
        )

    for index, fact in enumerate(visible_facts):
        fallback_candidates.append(
            _visibility_selected_fallback_candidate(
                fact,
                "visible_scene_fact_intro",
                "first_mention_visible_fact_intro",
                "visible_fact_scene_intro",
                "visible_fact_scene_intro",
                f"visible_fact:{index}",
                _first_mention_composition_meta(),
            )
        )

    deduped_candidates: List[VisibilitySelectedFallback] = []
    seen_candidates = set()
    for candidate in fallback_candidates:
        candidate_key = (
            candidate.text,
            candidate.fallback_pool,
            candidate.fallback_kind,
            candidate.final_emitted_source,
            candidate.fallback_strategy,
            candidate.fallback_candidate_source,
        )
        if candidate_key in seen_candidates:
            continue
        seen_candidates.add(candidate_key)
        deduped_candidates.append(candidate)
    return deduped_candidates
