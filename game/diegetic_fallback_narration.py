"""Diegetic fallback lines for retry / momentum / visibility paths.

Templates are written to avoid patterns flagged by ``player_facing_narration_purity``
(scaffold headers, coaching, UI labels, meta transition bridges). This module does not
validate or repair text — the final emission gate remains authoritative.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Set, Tuple


def _stable_u32(seed: str) -> int:
    acc = 2166136261
    for ch in str(seed or ""):
        acc = (acc ^ ord(ch)) * 16777619
        acc &= 0xFFFFFFFF
    return int(acc)


def _clean_detail(text: str, *, max_len: int = 140) -> str:
    detail = " ".join(str(text or "").strip().split()).rstrip(".")
    if len(detail) <= max_len:
        return detail
    return detail[: max_len - 3].rstrip(" ,;:") + "..."


def _inner_scene(scene_or_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_or_envelope, Mapping):
        return {}
    raw = scene_or_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_or_envelope)  # type: ignore[arg-type]


def _visible_fact_strings(scene: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(scene, Mapping):
        return []
    vf = scene.get("visible_facts")
    if not isinstance(vf, list):
        return []
    out: List[str] = []
    for item in vf:
        if isinstance(item, str) and item.strip():
            out.append(_clean_detail(item.strip()))
    return out


def _first_summary_sentence(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    summary = str(scene.get("summary") or "").strip()
    if not summary:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", summary)
    first = parts[0].strip() if parts else ""
    return _clean_detail(first, max_len=320) if first else ""


def _humanize_scene_slug(sid: str) -> str:
    s = str(sid or "").strip().replace("_", " ").replace("-", " ")
    return " ".join(s.split()).strip().lower()


def _looks_like_complete_sentence(fact: str) -> bool:
    s = str(fact or "").strip()
    return bool(s) and s[-1] in ".!?"


def _exit_thoroughfare_hint(ex: Mapping[str, Any] | None) -> str:
    if not isinstance(ex, Mapping):
        return ""
    tid = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
    if tid:
        return _humanize_scene_slug(tid)
    lab = str(ex.get("label") or "").strip()
    return _clean_detail(lab, max_len=80) if lab else ""


_INTENT_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "around", "as", "at", "by", "closer", "for", "from", "i",
    "in", "into", "it", "let", "me", "my", "near", "of", "on", "the", "to",
    "toward", "towards", "up", "we", "with",
})

_INTENT_FAMILY_ALIASES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("listen", ("listen", "listen in", "eavesdrop", "overhear", "hear", "catch what", "catch their words")),
    ("approach", ("approach", "move closer", "step closer", "edge closer", "draw closer", "close in")),
    ("scan", ("scan", "watch", "observe", "look around", "survey", "study", "keep an eye on")),
    ("inspect", ("inspect", "examine", "search", "investigate", "check", "track", "follow", "look for")),
    ("ask", ("ask", "question", "press", "interrogate", "quiz")),
)

_INTENT_FAMILY_FACT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "listen": (
        "whisper", "whispers", "whispering", "mutter", "murmur", "gossip", "rumor",
        "rumour", "voice", "voices", "patron", "patrons", "merchant", "merchants",
        "guard", "guards", "talk", "talking", "conversation", "crowd", "group",
        "huddle", "cluster", "missing patrol",
    ),
    "approach": (
        "patron", "patrons", "merchant", "merchants", "guard", "guards", "runner",
        "crowd", "group", "huddle", "cluster", "queue", "notice board", "checkpoint",
        "gate", "table", "stall",
    ),
    "scan": (
        "crowd", "queue", "patron", "patrons", "guard", "guards", "watcher",
        "watchers", "glance", "glances", "notice board", "checkpoint", "gate",
        "murmur", "whisper", "voices", "stall", "table",
    ),
    "inspect": (
        "footprint", "footprints", "track", "tracks", "trail", "crates", "crate",
        "drag", "dragged", "disturbed", "disturbance", "mud", "muddy", "scuff",
        "scuffs", "mark", "marks", "scrape", "scrapes", "blood", "ash", "lock",
        "hinge", "ledger", "seal", "paper", "papers",
    ),
    "ask": (
        "answer", "answers", "reply", "replies", "whisper", "whispers", "gossip",
        "rumor", "rumour", "patron", "patrons", "merchant", "merchants", "guard",
        "guards", "runner", "crowd", "group", "missing patrol",
    ),
}

_HUMAN_SCENE_FACT_KEYWORDS: Tuple[str, ...] = (
    "patron", "patrons", "merchant", "merchants", "guard", "guards", "runner",
    "watcher", "watchers", "crowd", "group", "huddle", "cluster", "queue",
    "voices", "voice", "whisper", "whispers", "mutter", "murmur", "gossip",
    "rumor", "rumour", "conversation",
)

_PHYSICAL_CLUE_FACT_KEYWORDS: Tuple[str, ...] = (
    "footprint", "footprints", "track", "tracks", "trail", "crate", "crates",
    "drag", "dragged", "disturbed", "mud", "muddy", "scuff", "scuffs", "mark",
    "marks", "scrape", "scrapes", "blood", "ash", "lock", "hinge", "ledger",
    "seal", "paper", "papers",
)


def _normalize_token_blob(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]+", " ", str(text or "").lower())


def _token_variants(token: str) -> Set[str]:
    base = str(token or "").strip().lower()
    if not base:
        return set()
    out = {base}
    if len(base) > 4 and base.endswith("ies"):
        out.add(base[:-3] + "y")
    if len(base) > 5 and base.endswith("ing"):
        out.add(base[:-3])
    if len(base) > 4 and base.endswith("ed"):
        out.add(base[:-2])
    if len(base) > 4 and base.endswith("es"):
        out.add(base[:-2])
    if len(base) > 3 and base.endswith("s"):
        out.add(base[:-1])
    return {tok for tok in out if tok}


def _content_tokens(text: str, *, include_stopwords: bool = False) -> Set[str]:
    norm = _normalize_token_blob(text)
    out: Set[str] = set()
    for raw in norm.split():
        if len(raw) < 3:
            continue
        if not include_stopwords and raw in _INTENT_STOPWORDS:
            continue
        out.update(_token_variants(raw))
    return out


def _infer_intent_families(player_text: str) -> List[str]:
    low = str(player_text or "").lower()
    found: List[str] = []
    for family, patterns in _INTENT_FAMILY_ALIASES:
        if any(pat in low for pat in patterns):
            found.append(family)
    return found


def _topic_tokens_from_player_text(player_text: str) -> Set[str]:
    family_words = {
        var
        for _family, patterns in _INTENT_FAMILY_ALIASES
        for pat in patterns
        for var in _content_tokens(pat, include_stopwords=True)
    }
    return {
        tok
        for tok in _content_tokens(player_text)
        if tok not in family_words and tok not in {"closer", "around", "nearby"}
    }


def _topic_phrases_from_player_text(player_text: str) -> Tuple[str, ...]:
    norm = _normalize_token_blob(player_text)
    family_words = {
        raw
        for _family, patterns in _INTENT_FAMILY_ALIASES
        for pat in patterns
        for raw in _normalize_token_blob(pat).split()
        if raw
    }
    words = [
        raw
        for raw in norm.split()
        if len(raw) >= 3 and raw not in _INTENT_STOPWORDS and raw not in family_words and raw != "closer"
    ]
    seen: Set[str] = set()
    phrases: List[str] = []
    for size in (3, 2):
        for idx in range(0, max(0, len(words) - size + 1)):
            phrase = " ".join(words[idx : idx + size]).strip()
            if len(phrase) < 7 or phrase in seen:
                continue
            seen.add(phrase)
            phrases.append(phrase)
    return tuple(phrases)


def _keyword_hit_count(text: str, keywords: Tuple[str, ...]) -> int:
    low = str(text or "").lower()
    return sum(1 for kw in keywords if kw in low)


def _score_visible_fact_for_intent(
    fact: str,
    *,
    player_text: str,
) -> Dict[str, Any]:
    low_fact = str(fact or "").lower()
    intent_families = _infer_intent_families(player_text)
    player_tokens = _content_tokens(player_text)
    topic_tokens = _topic_tokens_from_player_text(player_text)
    topic_phrases = _topic_phrases_from_player_text(player_text)
    fact_tokens = _content_tokens(low_fact)

    overlap = fact_tokens & player_tokens
    topic_overlap = fact_tokens & topic_tokens
    phrase_hits = [phrase for phrase in topic_phrases if phrase in low_fact]
    human_hits = _keyword_hit_count(low_fact, _HUMAN_SCENE_FACT_KEYWORDS)
    physical_hits = _keyword_hit_count(low_fact, _PHYSICAL_CLUE_FACT_KEYWORDS)

    score = len(overlap) * 4
    score += len(topic_overlap) * 3
    score += len(phrase_hits) * 11

    family_hits = 0
    for family in intent_families:
        hits = _keyword_hit_count(low_fact, _INTENT_FAMILY_FACT_KEYWORDS.get(family, ()))
        if hits:
            family_hits += hits
            score += 9 + max(0, hits - 1) * 2
        if family in {"listen", "approach", "scan", "ask"} and human_hits:
            score += 6
        if family == "listen" and _keyword_hit_count(low_fact, ("whisper", "mutter", "murmur", "gossip", "rumor", "rumour", "voice", "voices")):
            score += 6
        if family == "inspect" and physical_hits:
            score += 7

    return {
        "score": int(score),
        "overlap_count": len(overlap),
        "topic_overlap_count": len(topic_overlap),
        "phrase_hit_count": len(phrase_hits),
        "family_hit_count": int(family_hits),
        "human_hits": int(human_hits),
        "physical_hits": int(physical_hits),
    }


def _select_intent_aligned_visible_facts(
    scene: Mapping[str, Any] | None,
    *,
    player_text: str,
    seed_key: str,
    max_facts: int = 2,
) -> List[str]:
    facts = _visible_fact_strings(scene)
    if not facts or not str(player_text or "").strip():
        return []

    scored: List[Dict[str, Any]] = []
    for idx, fact in enumerate(facts):
        metrics = _score_visible_fact_for_intent(fact, player_text=player_text)
        scored.append(
            {
                "fact": fact,
                "index": idx,
                "tie_break": _stable_u32(f"intent|{seed_key}|{idx}|{fact}"),
                **metrics,
            }
        )

    best = max((int(rec.get("score") or 0) for rec in scored), default=0)
    if best < 9:
        return []

    scored.sort(
        key=lambda rec: (
            -int(rec.get("score") or 0),
            -int(rec.get("phrase_hit_count") or 0),
            -int(rec.get("family_hit_count") or 0),
            -int(rec.get("topic_overlap_count") or 0),
            -int(rec.get("overlap_count") or 0),
            int(rec.get("tie_break") or 0),
        )
    )

    strongest_overlap_exists = any(
        int(rec.get("score") or 0) >= best - 2
        and (
            int(rec.get("phrase_hit_count") or 0) > 0
            or int(rec.get("family_hit_count") or 0) > 0
            or int(rec.get("topic_overlap_count") or 0) > 0
        )
        for rec in scored
    )
    if not strongest_overlap_exists:
        return []

    chosen: List[str] = []
    primary = scored[0]
    if strongest_overlap_exists and (
        int(primary.get("phrase_hit_count") or 0) == 0
        and int(primary.get("family_hit_count") or 0) == 0
        and int(primary.get("topic_overlap_count") or 0) == 0
    ):
        return []
    chosen.append(str(primary.get("fact") or ""))

    second_floor = max(9, best - 5)
    for rec in scored[1:]:
        if len(chosen) >= max_facts:
            break
        if int(rec.get("score") or 0) < second_floor:
            continue
        if (
            int(rec.get("phrase_hit_count") or 0) == 0
            and int(rec.get("family_hit_count") or 0) == 0
            and int(rec.get("topic_overlap_count") or 0) == 0
        ):
            continue
        chosen.append(str(rec.get("fact") or ""))
    return [fact for fact in chosen if fact]


def _fact_clause(detail: str) -> str:
    s = str(detail or "").strip()
    if not s:
        return ""
    return s[0].lower() + s[1:] if len(s) > 1 else s.lower()


def _intent_aligned_observe_line(
    scene: Mapping[str, Any] | None,
    *,
    player_text: str,
    seed_key: str,
) -> str | None:
    chosen = _select_intent_aligned_visible_facts(scene, player_text=player_text, seed_key=seed_key, max_facts=2)
    if not chosen:
        return None

    families = _infer_intent_families(player_text)
    opener = "You notice"
    if "listen" in families:
        opener = "You edge closer and catch it clearer:"
    elif "ask" in families:
        opener = "The nearest reaction gives you something to work with:"
    elif "inspect" in families:
        opener = "On closer inspection,"
    elif "scan" in families:
        opener = "As you watch the scene,"
    elif "approach" in families:
        opener = "From a few steps nearer,"

    primary = _fact_clause(chosen[0])
    if opener.endswith(":"):
        line = f"{opener} {primary}"
    else:
        line = f"{opener} {primary}"

    if not _looks_like_complete_sentence(line):
        line = f"{line.rstrip(' ,;:')}."

    if len(chosen) >= 2:
        second = str(chosen[1] or "").strip()
        if second:
            if not _looks_like_complete_sentence(second):
                second = f"{second[0].upper() + second[1:] if len(second) > 1 else second.upper()}."
            line = f"{line} {second}"
    return line.strip()


def render_observe_perception_fallback_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
    player_text: str = "",
) -> str | None:
    """Concrete observation from visible facts (no coaching / menus)."""
    scene = _inner_scene(scene_or_envelope)
    intent_aligned = _intent_aligned_observe_line(scene, player_text=player_text, seed_key=seed_key)
    if intent_aligned:
        return intent_aligned
    facts = _visible_fact_strings(scene)
    if not facts:
        frag = _first_summary_sentence(scene)
        if not frag:
            return None
        idx = _stable_u32(f"obs|sum|{seed_key}") % 2
        if idx == 0:
            return f"You take in the scene: {frag}."
        return f"What surrounds you resolves into focus—{frag.lower()}."

    n = len(facts)
    i = _stable_u32(f"obs|{seed_key}") % n
    lead = facts[i]
    lead_cap = lead[0].upper() + lead[1:] if lead else lead
    mode = _stable_u32(f"obs|m|{seed_key}") % 3
    if n >= 2:
        j = (i + 1 + (_stable_u32(f"obs|j|{seed_key}") % (n - 1))) % n
        if j == i:
            j = (i + 1) % n
        second = facts[j]
        if _looks_like_complete_sentence(lead) and _looks_like_complete_sentence(second):
            if mode == 0:
                return f"You widen the sweep: {lead} {second}".strip()
            if mode == 1:
                return f"Two details keep trading priority: {lead} {second}".strip()
            return f"{lead} {second}".strip()
        if mode == 0:
            return f"{lead_cap} sharpens when you look again, and {second.lower()} still competes for notice."
        if mode == 1:
            return f"On a slower pass, {lead.lower()} reads clearer while {second.lower()} keeps pulling the eye."
        return f"{lead_cap} holds the eye, while {second.lower()} stays impossible to ignore."
    if _looks_like_complete_sentence(lead):
        if mode == 0:
            return f"You take another pass at the scene; {lead[0].lower()}{lead[1:]}"
        if mode == 1:
            return lead_cap if lead_cap.endswith((".", "!", "?")) else f"{lead_cap}."
        return f"The same impression returns, unchanged: {lead[0].lower()}{lead[1:]}"
    if mode == 0:
        return f"{lead_cap} stands out more sharply on a second pass."
    if mode == 1:
        return f"{lead_cap} reads a little finer when you let the noise thin."
    return f"Your attention settles again on {lead.lower()}."


def render_travel_arrival_fallback_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str | None:
    """Short arrival line from destination scene summary / facts (current envelope only)."""
    scene = _inner_scene(scene_or_envelope)
    summary = _first_summary_sentence(scene)
    facts = _visible_fact_strings(scene)
    loc = str(scene.get("location") or "").strip()

    idx = _stable_u32(f"arr|{seed_key}") % 3
    if summary:
        summ_low = summary[0].lower() + summary[1:] if len(summary) > 1 else summary.lower()
        if idx == 0:
            prefix = f"You arrive{f' in {loc}' if loc else ''} as "
            return f"{prefix}{summ_low}".strip()
        if idx == 1:
            return f"You step through{f' into {loc}' if loc else ''}, and {summ_low}".strip()
        return f"The new ground shows itself: {summ_low}".strip()

    if facts:
        f0 = facts[_stable_u32(f"arr|f|{seed_key}") % len(facts)]
        lead = f0[0].upper() + f0[1:] if f0 else f0
        if idx == 0:
            return f"You arrive{f' in {loc}' if loc else ''} where {f0.lower()}.".strip()
        return f"{lead} is the first thing that defines the space{f' here in {loc}' if loc else ''}.".strip()

    if loc:
        return f"You arrive in {loc}, the air and noise different enough to mark the change."

    return None


def render_scene_momentum_diegetic_append(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str:
    """One diegetic momentum beat: pressure without scaffold headers or option menus."""
    scene = _inner_scene(scene_or_envelope)
    loc = str(scene.get("location") or "").strip()
    facts = _visible_fact_strings(scene)
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_hints: List[str] = []
    for ex in exits:
        if isinstance(ex, dict):
            hint = _exit_thoroughfare_hint(ex)
            if hint and hint not in exit_hints:
                exit_hints.append(hint)
    loc_bit = f" in {loc}" if loc else ""

    low_blob = " ".join(f.lower() for f in facts)
    notice = "notice board" in low_blob or "noticeboard" in low_blob
    runner = "tavern runner" in low_blob or ("tavern" in low_blob and "runner" in low_blob)
    patrol = "missing patrol" in low_blob or "patrol" in low_blob

    seed = _stable_u32(f"mom|{seed_key}")

    if notice and patrol:
        opts = (
            f"Fresh worry tracks along the posted lines{loc_bit}; the missing patrol notice keeps drawing eyes.",
            f"Someone jabs at the board{loc_bit}, impatient with anyone who reads too long.",
        )
        return opts[seed % len(opts)]

    if notice:
        opts2 = (
            f"The notice board{loc_bit} collects another crowd—posted lines matter more than courtesy today.",
            f"Taxes and curfew lines{loc_bit} get read aloud by someone who wants witnesses.",
        )
        return opts2[seed % len(opts2)]

    if runner:
        opts3 = (
            f"The tavern runner's shout cuts through rain{loc_bit}, stew steam and rumor braided together.",
            f"A runner shouldering a cauldron{loc_bit} trades glances with the gate line—business and tension both.",
        )
        return opts3[seed % len(opts3)]

    if len(facts) >= 2:
        i = seed % len(facts)
        j = (i + 1 + (seed // 7) % (len(facts) - 1 or 1)) % len(facts)
        if j == i:
            j = (i + 1) % len(facts)
        a, b = facts[i], facts[j]
        if _looks_like_complete_sentence(a) and _looks_like_complete_sentence(b):
            return f"Tension keeps threading through the crowd{loc_bit}: {a} {b}".strip()
        a_cap = a[0].upper() + a[1:] if a else a
        return f"{a_cap} tightens{loc_bit}; {b.lower()} doesn't let the moment go slack."

    if facts:
        f0 = facts[seed % len(facts)]
        if _looks_like_complete_sentence(f0):
            return f"The moment won't idle{loc_bit}: {f0}".strip()
        lead = f0[0].upper() + f0[1:] if f0 else f0
        tail = (
            f"Pressure gathers{loc_bit} without anyone naming it.",
            f"The noise doesn't soften{loc_bit}; it searches for a fault line.",
            f"Someone nearer the press mutters{loc_bit}, and the mood answers.",
        )
        return f"{lead} {tail[seed % len(tail)]}"

    if exit_hints:
        dest = exit_hints[seed % len(exit_hints)]
        return f"Foot traffic still shoulders toward {dest}{loc_bit}, and the crowd won't pretend patience."

    if loc:
        return f"The press of bodies{loc_bit} finds another impatient rhythm—something is about to give."

    return "The crowd's tempo tightens; the next sound will carry weight."


def render_nonsocial_terminal_anchor_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
    player_text: str = "",
) -> str | None:
    """Generic nonsocial anchor: scene facts before abstract coaching."""
    obs = render_observe_perception_fallback_line(
        scene_or_envelope,
        seed_key=f"anchor|{seed_key}",
        player_text=player_text,
    )
    if obs:
        return obs
    scene = _inner_scene(scene_or_envelope)
    loc = str(scene.get("location") or "").strip()
    if loc:
        mode = _stable_u32(f"anc|{seed_key}") % 2
        if mode == 0:
            return f"Rain and voices tangle{_near_loc_phrase(loc)}—the scene keeps moving without waiting."
        return f"The crowd's rhythm shifts{_near_loc_phrase(loc)}; faces turn, then turn away."
    return None


def _near_loc_phrase(loc: str) -> str:
    s = str(loc or "").strip()
    return f" near {s}" if s else ""


def render_global_scene_anchor_fallback(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str = "",
    player_text: str = "",
) -> str | None:
    """Last-resort global stock replacement when visible facts or summary exist."""
    line = render_observe_perception_fallback_line(
        scene_or_envelope,
        seed_key=f"global|{seed_key}",
        player_text=player_text,
    )
    if line:
        return line
    scene = _inner_scene(scene_or_envelope)
    summary = _first_summary_sentence(scene)
    if summary:
        s0 = summary[0].lower() + summary[1:] if len(summary) > 1 else summary.lower()
        return f"The moment stays crowded with detail—{s0}."
    loc = str(scene.get("location") or "").strip()
    if loc:
        return f"Sound and motion keep trading places{_near_loc_phrase(loc)}."
    return None
